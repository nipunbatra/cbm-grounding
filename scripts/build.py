#!/usr/bin/env python3
"""Build six deterministic SVG birds, machine-readable annotations, and offline viewer.

Python standard library only. Does not run a model or estimate probabilities.
"""
from pathlib import Path
import base64
import csv
import hashlib
import io
import json
import struct
from naturalistic import generate as naturalistic_examples
from geometry import path_area
from photo_svg import generate as photographic_examples
from flowers import generate as flower_examples

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/cub/raw'
OUTPUT = ROOT / 'outputs'

# This semantic correspondence is authored, not part of the CUB release.
PART_MAP = {
    'bill': [2], 'wing': [9, 13], 'crown': [5], 'forehead': [6],
    'breast': [4], 'belly': [3], 'back': [1], 'tail': [14],
    'nape': [10], 'throat': [15], 'eye': [7, 11], 'leg': [8, 12],
}


def lines(name):
    return [r.split() for r in (RAW / name).read_text().splitlines() if r.strip()]


def names(name):
    return {int(r[0]): ' '.join(r[1:]) for r in lines(name)}


def jpeg_size(path):
    with path.open('rb') as f:
        assert f.read(2) == b'\xff\xd8', path
        while True:
            marker = f.read(1)
            while marker == b'\xff':
                marker = f.read(1)
            if not marker:
                raise ValueError('No JPEG size: ' + str(path))
            size = struct.unpack('>H', f.read(2))[0]
            if marker[0] in [0xC0, 0xC1, 0xC2]:
                _, h, w = struct.unpack('>BHH', f.read(5))
                return w, h
            f.seek(size - 2, 1)


def data_uri(path):
    kind = 'image/svg+xml' if path.suffix == '.svg' else 'image/jpeg'
    return f'data:{kind};base64,' + base64.b64encode(path.read_bytes()).decode()


def norm_box(box, w, h):
    x, y, bw, bh = box
    return [round(x / w, 6), round(y / h, 6), round(bw / w, 6), round(bh / h, 6)]


def cub_examples():
    ids = json.loads((ROOT / 'data/cub/provenance.json').read_text())['selected_image_ids']
    paths = names('images.txt')
    classes = names('classes.txt')
    class_ids = {int(r[0]): int(r[1]) for r in lines('image_class_labels.txt')}
    attrs = names('attributes.txt')
    part_names = names('parts/parts.txt')
    certainties = names('attributes/certainties.txt')
    boxes = {int(r[0]): list(map(float, r[1:5])) for r in lines('bounding_boxes.txt')}
    parts = {i: [] for i in ids}
    for r in lines('parts/part_locs.txt'):
        i, p = int(r[0]), int(r[1])
        parts[i].append({'id': p, 'name': part_names[p], 'x': float(r[2]), 'y': float(r[3]),
                         'visible': bool(int(r[4])), 'source': 'CUB native part keypoint'})
    image_attrs = {i: [] for i in ids}
    for r in lines('attributes/image_attribute_labels.txt'):
        i, a, present, certainty = map(int, r[:4])
        image_attrs[i].append({'id': a, 'name': attrs[a], 'present': present,
                              'certainty_id': certainty, 'certainty': certainties[certainty],
                              'observable': certainty != 1})
    result = []
    for i in ids:
        path = ROOT / 'images/cub' / paths[i]
        w, h = jpeg_size(path)
        concepts = []
        for attr in image_attrs[i]:
            part_family = attr['name'].split('::')[0].removeprefix('has_').split('_')[0]
            related = [p for p in parts[i] if p['id'] in PART_MAP.get(part_family, [])]
            visible = [p for p in related if p['visible']]
            proxy_boxes = []
            if attr['present'] == 1 and attr['observable']:
                # Same square heuristic for every part. Not an extent estimate.
                side = 0.18 * max(boxes[i][2:])
                for point in visible:
                    x0, y0 = max(0, point['x'] - side / 2), max(0, point['y'] - side / 2)
                    x1, y1 = min(w, point['x'] + side / 2), min(h, point['y'] + side / 2)
                    box = [round(v, 3) for v in [x0, y0, x1 - x0, y1 - y0]]
                    proxy_boxes.append({'part_id': point['id'], 'bbox_xywh': box,
                                        'bbox_normalized_xywh': norm_box(box, w, h),
                                        'kind': 'heuristic_proxy_not_ground_truth'})
            group, value = attr['name'].removeprefix('has_').split('::')
            label = group.replace('_', ' ') + ': ' + value.replace('_', ' ')
            concepts.append({**attr, 'label': label, 'part_ids': [p['id'] for p in related],
                             'support_keypoints': visible, 'proxy_boxes': proxy_boxes,
                             'ground_truth_concept_boxes': None,
                             'localization_status': 'part_keypoints_only' if related else 'no_direct_part_mapping'})
        # Local, present, sure concepts first; never replace instance labels by class averages.
        concepts.sort(key=lambda a: (not (a['present'] and a['observable'] and a['support_keypoints']),
                                     -a['certainty_id'], a['id']))
        result.append({'id': f'cub-{i:05}', 'image_id': i, 'kind': 'cub',
                       'title': classes[class_ids[i]].split('.', 1)[1].replace('_', ' '),
                       'class_id': class_ids[i], 'class_label': classes[class_ids[i]], 'split': 'train',
                       'image_path': str(path.relative_to(ROOT)), 'width': w, 'height': h,
                       'bird_bbox_xywh': boxes[i], 'parts': parts[i], 'concepts': concepts,
                       'evidence': 'OBSERVED DATA: CUB annotations; not model predictions'})
    return result


def svg_examples():
    image_dir = ROOT / 'images/svg'
    mask_dir = image_dir / 'masks'
    mask_dir.mkdir(parents=True, exist_ok=True)
    # Each pair is authored; the classification rule is deliberately arbitrary.
    configs = [
        ('01-reference', 'Reference bird', [1, 1, 1], 0, 0, False, 'All three concepts are present.'),
        ('02-neutral-bill', 'Change only the bill', [0, 1, 1], 0, 0, False, 'Yellow bill becomes gray; the authored class changes.'),
        ('03-neutral-crown', 'Change only the crown', [1, 0, 1], 0, 0, False, 'Red crown becomes gray; the authored class changes.'),
        ('04-neutral-wing', 'Change only the wing', [1, 1, 0], 0, 0, False, 'Blue wing becomes gray; the authored class stays the same.'),
        ('05-moved-bird', 'Move the same bird', [1, 1, 1], 72, -22, False, 'The concept vector is unchanged, while all three boxes move.'),
        ('06-red-distractor', 'Put red in the background', [1, 0, 1], 0, 0, True, 'A red circle is present, but the bird still has no red crown.'),
    ]
    # These three primitives are fully visible, unrotated, unstroked, and unclipped.
    shape_specs = [
        ('bill', 'yellow bill', 'yellow', [350, 141, 57, 34], '<polygon points="350,141 407,158 350,175" fill="{color}"/>', '#e6b84d'),
        ('crown', 'red crown patch', 'red', [278, 102, 62, 26], '<ellipse cx="309" cy="115" rx="31" ry="13" fill="{color}"/>', '#b8574c'),
        ('wing', 'blue wing patch', 'blue', [168, 193, 140, 70], '<ellipse cx="238" cy="228" rx="70" ry="35" fill="{color}"/>', '#507b99'),
    ]
    result = []
    for name, title, bits, dx, dy, distractor, note in configs:
        identifier = 'svg-' + name
        prefix = '<svg xmlns="http://www.w3.org/2000/svg" width="560" height="360" viewBox="0 0 560 360">'
        body = [prefix, f'<title>{title}</title>', '<rect width="560" height="360" fill="#f2f1e9"/>']
        if distractor:
            body.append('<circle cx="466" cy="74" r="30" fill="#b8574c"/>')
        body.extend([f'<g transform="translate({dx} {dy})">',
                     '<polygon points="148,230 72,227 97,274 165,263" fill="#929a91"/>',
                     '<rect x="231" y="291" width="7" height="31" fill="#757b71"/>',
                     '<rect x="271" y="291" width="7" height="31" fill="#757b71"/>',
                     '<ellipse cx="249" cy="235" rx="112" ry="72" fill="#c2c7ba"/>',
                     '<circle cx="310" cy="147" r="54" fill="#c2c7ba"/>',
                     '<circle cx="333" cy="144" r="5" fill="#303b35"/>'])
        concepts, parts = [], []
        for (part, label, color_name, bbox, primitive, positive_color), bit in zip(shape_specs, bits):
            color = positive_color if bit else '#8e978d'
            shape = primitive.format(color=color)
            body.append(f'<g id="{part}">{shape}</g>')
            box = [bbox[0] + dx, bbox[1] + dy, *bbox[2:]]
            geom = {'part': part, 'bbox_xywh': box, 'bbox_normalized_xywh': norm_box(box, 560, 360),
                    'kind': 'exact_svg_geometry', 'primitive_svg': primitive.format(color=color),
                    'translation': [dx, dy], 'fill': color,
                    'definition': 'Tight axis-aligned bounds of the fully visible filled primitive; no stroke or clipping.'}
            parts.append(geom)
            # A target concept mask is empty when its attribute is absent.
            mask = prefix + '<rect width="560" height="360" fill="black"/>'
            if bit:
                mask += f'<g transform="translate({dx} {dy})">' + primitive.format(color='white') + '</g>'
            mask += '</svg>'
            mask_path = mask_dir / f'{name}-{part}.svg'
            mask_path.write_text(mask)
            concepts.append({'id': part, 'name': label.replace(' ', '_'), 'label': label, 'present': bit,
                             'observable': True, 'certainty': 'known by construction',
                             'ground_truth_concept_boxes': [geom] if bit else [],
                             'part_geometry': geom, 'proxy_boxes': [], 'support_keypoints': [],
                             'mask_path': str(mask_path.relative_to(ROOT)),
                             'localization_status': 'exact_visible_svg_geometry' if bit else 'concept_absent'})
        body.append('</g></svg>')
        path = image_dir / (name + '.svg')
        path.write_text('\n'.join(body))
        result.append({'id': identifier, 'kind': 'svg', 'title': title, 'note': note,
                       'image_path': str(path.relative_to(ROOT)), 'width': 560, 'height': 360,
                       'class_label': 'A' if bits[0] and bits[1] else 'B',
                       'rule': 'A iff yellow bill AND red crown patch; otherwise B. Blue wing is irrelevant.',
                       'concept_vector': bits, 'concept_order': ['yellow_bill', 'red_crown_patch', 'blue_wing_patch'],
                       'parts': parts, 'concepts': concepts, 'bird_bbox_xywh': [72+dx, 93+dy, 335, 229],
                       'bird_bbox_kind': 'exact_union_of_authored_bird_primitives',
                       'distractors': [{'name': 'red background circle', 'bbox_xywh': [436, 44, 60, 60]}] if distractor else [],
                       'evidence': 'ILLUSTRATIVE: exact SVG geometry and authored class rule'})
    return result


def export_coco(examples):
    ids = {'bill': 1, 'crown': 2, 'wing': 3}
    coco = {'info': {'description': 'SVG positive concepts only; exact vector AABBs. Areas are true vector shape areas. No CUB proxies.'},
            'images': [], 'annotations': [],
            'categories': [{'id': i, 'name': n} for n, i in [('yellow_bill', 1), ('red_crown_patch', 2), ('blue_wing_patch', 3)]]}
    from math import pi
    for i, item in enumerate(examples, 1):
        coco['images'].append({'id': i, 'file_name': item['image_path'], 'width': item['width'], 'height': item['height']})
        for c in item['concepts']:
            if c['present']:
                b = c['ground_truth_concept_boxes'][0]['bbox_xywh']
                geometry=c['ground_truth_concept_boxes'][0]
                if 'polygon' in geometry:
                    points=geometry['polygon'];area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2
                else:
                    area = path_area(geometry['path_d']) if 'path_d' in geometry else b[2]*b[3]*(0.5 if c['id'] == 'bill' else pi/4)
                coco['annotations'].append({'id': len(coco['annotations'])+1, 'image_id': i,
                    'category_id': ids[c['id']], 'bbox': b, 'area': area, 'iscrowd': 0,
                    'geometry_source': geometry['kind'], 'mask_svg': c['mask_path'],
                    'area_method': 'Bezier sampling at 256 intervals per curve' if 'path_d' in geometry else 'analytic primitive or polygon area'})
    return coco


def main():
    OUTPUT.mkdir(exist_ok=True)
    cub, synthetic, naturalistic = cub_examples(), svg_examples(), naturalistic_examples(ROOT)
    photographic = photographic_examples(ROOT)
    assistant = flower_examples(ROOT)
    dataset = {'schema_version': '1.0', 'bbox_format': '[x_min,y_min,width,height] in original image pixels',
               'coordinate_note': 'CUB numeric coordinates are preserved exactly; SVG uses its viewBox coordinates. Browser overlays use these numbers without resizing the coordinate system.',
               'proxy_definition': 'Square centered on each visible mapped part; side = 0.18 × max(native bird box width,height); clip to image. This is a teaching heuristic, not an annotated part extent.',
               'missingness': 'CUB ground_truth_concept_boxes=null means unavailable; SVG [] means known absent. CUB certainty=1 is not visible, not a reliable negative.',
               'prediction_note': 'CUB labels are dataset observations. SVG values are authored. Flower scores are subjective assistant visual estimates, uncalibrated. There is no trained classifier or performance measurement.',
               'cub': cub, 'synthetic': synthetic, 'naturalistic': naturalistic, 'photographic': photographic, 'assistant':assistant}
    (OUTPUT / 'annotations.json').write_text(json.dumps(dataset, indent=2) + '\n')
    (OUTPUT / 'synthetic-concepts.coco.json').write_text(json.dumps(export_coco(synthetic+naturalistic), indent=2) + '\n')
    photo_coco=export_coco(photographic)
    photo_coco['info']['description']='Exact authored photo-recoloring mask boxes. Anatomical fit is approximate, not independently validated part segmentation.'
    (OUTPUT / 'photographic-edit-masks.coco.json').write_text(json.dumps(photo_coco,indent=2)+'\n')
    with (OUTPUT / 'concepts.csv').open('w') as f:
        writer = csv.writer(f)
        writer.writerow(['example_id', 'kind', 'concept_id', 'concept_name', 'raw_present', 'observable', 'certainty', 'localization_status', 'exact_boxes_xywh', 'proxy_boxes_xywh','assistant_boxes_xywh','assistant_score'])
        for item in cub + synthetic + naturalistic + photographic + assistant:
            for c in item['concepts']:
                exact = c['ground_truth_concept_boxes']
                writer.writerow([item['id'], item['kind'], c['id'], c['name'], c['present'], c['observable'], c['certainty'], c['localization_status'],
                                 json.dumps(None if exact is None else [b['bbox_xywh'] for b in exact]), json.dumps([b['bbox_xywh'] for b in c['proxy_boxes']]),json.dumps([b['bbox_xywh'] for b in c.get('annotation_boxes',[])]),c.get('score','')])
    viewer_data = json.loads(json.dumps(dataset))
    for item in viewer_data['cub'] + viewer_data['synthetic'] + viewer_data['naturalistic'] + viewer_data['photographic'] + viewer_data['assistant']:
        item['image_data'] = data_uri(ROOT / item['image_path'])
    template = (ROOT / 'src/viewer.html').read_text()
    (ROOT / 'index.html').write_text(template.replace('__DATA__', json.dumps(viewer_data, separators=(',', ':')).replace('</', '<\\/')))
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [OUTPUT/'annotations.json', OUTPUT/'concepts.csv', OUTPUT/'synthetic-concepts.coco.json', ROOT/'index.html']}
    (OUTPUT/'build-manifest.json').write_text(json.dumps(hashes, indent=2)+'\n')
    print(f'Built {len(cub)} CUB + {len(synthetic)+len(naturalistic)+len(photographic)} SVG + {len(assistant)} flower examples; {sum(len(e["concepts"]) for e in cub)} native CUB attributes and {sum(len(e["concepts"]) for e in assistant)} assistant scores.')


if __name__ == '__main__':
    main()
