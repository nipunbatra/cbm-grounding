#!/usr/bin/env python3
"""Check provenance, missingness, geometry, and controlled concept changes."""
from pathlib import Path
import hashlib
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import PART_MAP
from geometry import path_bounds

data = json.loads((ROOT / 'outputs/annotations.json').read_text())
provenance = json.loads((ROOT / 'data/cub/provenance.json').read_text())
checks = []


def check(condition, message):
    assert condition, message
    checks.append(message)


def bounds(shape):
    tag = shape.tag.split('}')[-1]
    a = shape.attrib
    if tag == 'ellipse':
        x, y, rx, ry = (float(a[k]) for k in ['cx', 'cy', 'rx', 'ry'])
        return [x-rx, y-ry, 2*rx, 2*ry]
    if tag == 'polygon':
        points = [[float(v) for v in p.split(',')] for p in a['points'].split()]
        xs, ys = list(zip(*points))
        return [min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)]
    if tag == 'path':
        return path_bounds(a['d'])
    raise ValueError(tag)


check(len(data['cub']) == 10 and all(len(data[k])==6 for k in ['synthetic','naturalistic','photographic']) and len(data['assistant'])==5, '10 CUB + 18 controlled SVG + 5 flower images')
for source in provenance['files']:
    actual = hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest()
    check(actual == source.get('saved_sha256', source.get('sha256')), 'Source hash: '+source['path'])
part_names = dict((int(r.split()[0]), ' '.join(r.split()[1:])) for r in (ROOT/'data/cub/raw/parts/parts.txt').read_text().splitlines())
for name, ids in PART_MAP.items():
    expected = 'beak' if name == 'bill' else name
    check(all(expected in part_names[i] for i in ids), 'Semantic part IDs: '+name)
raw_attributes = {(int(r[0]), int(r[1])): tuple(map(int,r[2:4])) for line in (ROOT/'data/cub/raw/attributes/image_attribute_labels.txt').read_text().splitlines() if (r:=line.split())}
for item in data['cub']:
    check(len(item['parts'])==15, item['id']+' has 15 parts')
    check(len(item['concepts'])==312 and len({c['id'] for c in item['concepts']})==312, item['id']+' has 312 distinct attributes')
    for c in item['concepts']:
        check((c['present'],c['certainty_id'])==raw_attributes[(item['image_id'],c['id'])], item['id']+' original label '+str(c['id']))
        check(c['ground_truth_concept_boxes'] is None, 'No CUB concept box invented')
        check(c['observable']==(c['certainty_id']!=1), 'CUB not-visible is unknown')
        check(all(p['visible'] for p in c['support_keypoints']), 'Only visible CUB points become supports')
        if c['present']==0 or not c['observable']:
            check(not c['proxy_boxes'], 'Absent/unknown concept has no positive proxy')
        for b in c['proxy_boxes']:
            x,y,w,h=b['bbox_xywh']
            check(x>=0 and y>=0 and w>0 and h>0 and x+w<=item['width']+.002 and y+h<=item['height']+.002, 'Proxy clipped to image')
            check(b['kind']=='heuristic_proxy_not_ground_truth', 'Proxy provenance retained')

ns = {'s': 'http://www.w3.org/2000/svg'}
for item in data['synthetic']+data['naturalistic']:
    svg = ET.parse(ROOT/item['image_path']).getroot()
    check(item['class_label']==('A' if item['concept_vector'][0] and item['concept_vector'][1] else 'B'), item['id']+' rule label')
    for c in item['concepts']:
        part = svg.find(f".//s:g[@id='{c['id']}']",ns)
        box = bounds(list(part)[0])
        dx,dy=c['part_geometry']['translation']
        box[0]+=dx;box[1]+=dy
        check(all(abs(a-b)<1e-8 for a,b in zip(box,c['part_geometry']['bbox_xywh'])), item['id']+' independently derived '+c['id']+' box')
        mask = ET.parse(ROOT/c['mask_path']).getroot()
        whites = [x for x in mask.iter() if x.attrib.get('fill')=='white']
        check(bool(whites)==bool(c['present']), item['id']+' mask presence '+c['id'])
        check(len(c['ground_truth_concept_boxes'])==c['present'], item['id']+' positive box count '+c['id'])
        if whites:
            check(bounds(whites[0])==bounds(list(part)[0]), item['id']+' mask shape matches concept')

base,*rest=data['synthetic']
for i in range(3):
    changed=rest[i]
    check(sum(a!=b for a,b in zip(base['concept_vector'],changed['concept_vector']))==1, changed['id']+' one concept changed')
    check(all(a['part_geometry']['bbox_xywh']==b['part_geometry']['bbox_xywh'] for a,b in zip(base['concepts'],changed['concepts'])), changed['id']+' geometry held fixed')
moved=data['synthetic'][4]
check(base['concept_vector']==moved['concept_vector'], 'Translation preserves concepts')
for a,b in zip(base['concepts'],moved['concepts']):
    ab,bb=a['part_geometry']['bbox_xywh'],b['part_geometry']['bbox_xywh']
    check([bb[0]-ab[0],bb[1]-ab[1]]==[72,-22] and ab[2:]==bb[2:], 'Translation updates exact box')
check(data['synthetic'][5]['concept_vector']==data['synthetic'][2]['concept_vector'], 'Background distractor preserves no-red-crown concepts')
for item in data['photographic']:
    svg=ET.parse(ROOT/item['image_path']).getroot()
    for c in item['concepts']:
        clip=svg.find(f".//s:clipPath[@id='{c['id']}-clip']",ns)
        box=bounds(list(clip)[0]);dx,dy=c['part_geometry']['translation'];box[0]+=dx;box[1]+=dy
        check(box==c['part_geometry']['bbox_xywh'], item['id']+' exact recoloring clip bounds')
        mask=ET.parse(ROOT/c['mask_path']).getroot()
        whites=[x for x in mask.iter() if x.attrib.get('fill')=='white']
        check(bool(whites)==bool(c['present']), item['id']+' photo mask presence')
        check(c['localization_status']=='exact_edit_mask_approximate_anatomical_fit','Photo geometry never represented as native anatomy GT')
for item in data['assistant']:
    for c in item['concepts']:
        check(0<=c['score']<=1,'Assistant score in range')
        check(c['ground_truth_concept_boxes'] is None,'Assistant box not presented as ground truth')
        if not c['observable']:
            check(c['assessment']=='uncertain' and not c['annotation_boxes'],'Uncertain flower concept has no asserted box')
        for b in c['annotation_boxes']:
            x,y,w,h=b['bbox_xywh']
            check(x>=0 and y>=0 and x+w<=item['width'] and y+h<=item['height'],'Assistant box within image')
point_check=json.loads((ROOT/'data/cub/point-verification.json').read_text())
check(point_check['all_numeric_records_equal'] and point_check['matching_records']==150,'All 150 native CUB point records match independent mirror')
coco=json.loads((ROOT/'outputs/synthetic-concepts.coco.json').read_text())
check(len(coco['images'])==12 and len(coco['annotations'])==28, 'Pure-vector COCO: 12 images and 28 positive concepts')
photo=json.loads((ROOT/'outputs/photographic-edit-masks.coco.json').read_text())
check(len(photo['images'])==6 and len(photo['annotations'])==14, 'Separate photo-edit COCO: 6 images and 14 positive masks')
report={'status':'passed','checks':len(checks),'cub_images':10,'cub_attributes':3120,'pure_vector_images':12,'photographic_svg_images':6,'flower_images':5,'assistant_concept_scores':40,'exact_vector_positive_boxes':28,'exact_photo_edit_boxes':14,
        'limitations':['No CUB concept ground-truth boxes','Photo edit mask anatomy is approximate','Assistant flower annotations are subjective and uncalibrated','No trained classifier','Selected teaching subset; no performance estimate'],
        'checks_summary':['Pinned source SHA-256 integrity','Original per-image labels and certainty','Native part IDs checked against names','Unknown versus absent handling','Clipped and explicitly marked proxies','SVG boxes independently derived from XML primitives','Mask presence and geometry','Single-concept edits, translation and distractor pairs','Synthetic-only COCO export']}
(ROOT/'outputs/validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
