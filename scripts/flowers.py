#!/usr/bin/env python3
"""Five visually inspected Flowers102 photos with assistant-authored concepts.

No model inference is run by this script. The visual judgments were made by the
Codex assistant while viewing each photo on 2026-10-12. Scores are subjective and
uncalibrated, not classifier probabilities. Generation is local and offline.
"""
from pathlib import Path
import hashlib
import json
import re
import struct
import zlib


def _jpeg_size(path):
    with path.open('rb') as stream:
        assert stream.read(2) == b'\xff\xd8'
        while True:
            marker = stream.read(1)
            while marker == b'\xff':
                marker = stream.read(1)
            if not marker:
                raise ValueError(f'JPEG dimensions unavailable: {path}')
            size = struct.unpack('>H', stream.read(2))[0]
            if marker[0] in (0xC0, 0xC1, 0xC2):
                _, height, width = struct.unpack('>BHH', stream.read(5))
                return width, height
            stream.seek(size - 2, 1)


def _official_labels(path):
    """Read this official MATLAB v5 uint8 vector without a SciPy dependency."""
    raw = path.read_bytes()
    assert raw[126:128] == b'IM', 'Expected little-endian MATLAB v5 file'
    kind, length = struct.unpack_from('<II', raw, 128)
    assert kind == 15, 'Expected compressed MATLAB data element'
    matrix = zlib.decompress(raw[136:136 + length])
    assert struct.unpack_from('<I', matrix)[0] == 14
    offset, name, result = 8, None, None
    while offset < len(matrix):
        kind, length = struct.unpack_from('<II', matrix, offset)
        value = matrix[offset + 8:offset + 8 + length]
        if kind == 1:
            name = value.decode('ascii')
        elif kind == 2:
            result = list(value)
        offset += 8 + ((length + 7) // 8) * 8
    assert name == 'labels' and len(result) == 8189
    return result


def generate(root):
    """Return viewer records, verifying image hashes and official class labels."""
    root = Path(root)
    directory = root / 'data/flowers'
    manifest = json.loads((directory / 'provenance.json').read_text())
    authored = json.loads((directory / 'assistant-annotations.json').read_text())
    labels = _official_labels(directory / 'imagelabels.mat')
    category_html = (directory / 'categories.html').read_text()
    thumbnails = re.findall(r'thumbim_(\d+)\.jpg[^>]+alt="([^"]+)"', category_html)
    class_names = {labels[int(i) - 1]: name for i, name in thumbnails}
    vocabulary = {concept['id']: concept for concept in authored['vocabulary']}
    annotations = {item['image_id']: item for item in authored['images']}
    records = []
    for source in manifest['images']:
        image_id = source['image_id']
        path = root / source['local_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256']
        width, height = _jpeg_size(path)
        annotation = annotations[image_id]
        assert [width, height] == annotation['image_size']
        class_id = labels[image_id - 1]
        assert class_id == source['verified_official_class_id']
        class_name = class_names[class_id]
        assert class_name == source['verified_official_class_name']
        concepts = []
        for judgment in annotation['concepts']:
            spec = vocabulary[judgment['id']]
            boxes = []
            for box in judgment.get('boxes', []):
                x, y, box_width, box_height = box
                assert 0 <= x < width and 0 <= y < height
                assert box_width > 0 and box_height > 0
                assert x + box_width <= width and y + box_height <= height
                boxes.append({
                    'bbox_xywh': box,
                    'bbox_normalized_xywh': [round(x / width, 6), round(y / height, 6),
                                             round(box_width / width, 6), round(box_height / height, 6)],
                    'kind': 'assistant_visual_annotation_not_ground_truth',
                })
            score = judgment['score']
            assert 0 <= score <= 1
            concepts.append({
                'id': judgment['id'], 'name': spec['name'], 'label': spec['label'],
                'definition': spec['definition'], 'present': judgment['present'],
                'observable': judgment['observable'],
                'certainty': 'assistant visual estimate; uncalibrated',
                'score': score, 'score_source': 'assistant_subjective_visual_estimate',
                'score_definition': manifest['score_definition'],
                'assessment': judgment['assessment'], 'note': judgment['note'],
                'annotation_boxes': boxes, 'ground_truth_concept_boxes': None,
                'proxy_boxes': [], 'support_keypoints': [],
                'localization_status': 'assistant_annotated',
            })
        records.append({
            'id': f'flowers-{image_id:05d}', 'image_id': image_id, 'kind': 'assistant',
            'title': class_name.capitalize(), 'class_id': class_id,
            'class_label': f'{class_id:03d}. {class_name}',
            'class_label_source': 'Official Flowers102 imagelabels.mat, with category name verified through official category thumbnail IDs',
            'image_path': source['local_path'], 'width': width, 'height': height,
            'bird_bbox_xywh': None, 'parts': [], 'concepts': concepts,
            'note': annotation['note'],
            'evidence': 'ASSISTANT VISUAL ANNOTATION: approximate boxes and uncalibrated subjective scores; only the flower class is a native dataset label.',
            'source_url': source['original_url'],
            'dataset_url': manifest['official_homepage'],
            'annotation_provenance_path': 'data/flowers/provenance.json',
            'annotation_author': 'Codex assistant', 'visual_inspection_date': '2026-10-12',
        })
    return records


if __name__ == '__main__':
    examples = generate(Path(__file__).resolve().parents[1])
    print(json.dumps({'images': len(examples),
                      'concept_judgments': sum(len(x['concepts']) for x in examples),
                      'approximate_boxes': sum(len(c['annotation_boxes']) for x in examples for c in x['concepts']),
                      'classes': [x['class_label'] for x in examples]}, indent=2))
