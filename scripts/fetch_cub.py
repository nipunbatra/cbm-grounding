#!/usr/bin/env python3
"""Fetch a pinned CUB mirror, retaining original annotations for ten images."""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
REVISION = '8a8486039c718e33d87b96ed42c0f457e6a7d939'
BASE = f'https://huggingface.co/datasets/pawlo2013/CUB/resolve/{REVISION}/'
CACHE = ROOT / 'work' / 'cub-source'
RAW = ROOT / 'data' / 'cub' / 'raw'
FILES = ['images.txt', 'classes.txt', 'image_class_labels.txt', 'train_test_split.txt',
         'bounding_boxes.txt', 'parts/parts.txt', 'parts/part_locs.txt',
         'attributes/certainties.txt', 'attributes/image_attribute_labels.txt', 'README']


def fetch(remote, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        print('Downloading', remote, flush=True)
        request = urllib.request.Request(BASE + remote, headers={'User-Agent': 'CBM-local-educational-exercise/1.0'})
        with urllib.request.urlopen(request, timeout=120) as response:
            temp = target.with_suffix(target.suffix + '.partial')
            with temp.open('wb') as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
            temp.replace(target)
    return target


def rows(name):
    return (line.split() for line in (CACHE / name).read_text().splitlines() if line.strip())


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        jobs = [pool.submit(fetch, 'CUB_200_2011/' + f, CACHE / f) for f in FILES]
        jobs.append(pool.submit(fetch, 'attributes.txt', CACHE / 'attributes.txt'))
        for job in jobs:
            job.result()
    classes = {int(r[0]): r[1] for r in rows('classes.txt')}
    labels = {int(r[0]): int(r[1]) for r in rows('image_class_labels.txt')}
    splits = {int(r[0]): int(r[1]) for r in rows('train_test_split.txt')}
    images = {int(r[0]): r[1] for r in rows('images.txt')}
    visibility = {}
    for r in rows('parts/part_locs.txt'):
        i, p, visible = int(r[0]), int(r[1]), int(r[4])
        visibility.setdefault(i, {})[p] = visible
    targets = ['Cardinal', 'Northern_Flicker', 'American_Goldfinch', 'Blue_Jay', 'Common_Yellowthroat']
    selected = []
    for species in targets:
        class_id = next(k for k, v in classes.items() if v.split('.', 1)[1] == species)
        candidates = [i for i, c in labels.items() if c == class_id and splits[i] == 1]
        # Predeclared teaching selection, not a random/representative evaluation sample.
        candidates.sort(key=lambda i: (-sum(visibility[i].get(p, 0) for p in [2, 4, 5, 6, 15]),
                                       -max(visibility[i].get(9, 0), visibility[i].get(13, 0)), i))
        selected.extend(candidates[:2])
    selected_set = set(selected)
    sources = []
    for name in FILES + ['attributes.txt']:
        src = CACHE / name
        dest = RAW / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        subset_files = {'images.txt', 'image_class_labels.txt', 'train_test_split.txt',
                        'bounding_boxes.txt', 'parts/part_locs.txt', 'attributes/image_attribute_labels.txt'}
        if name in subset_files:
            with src.open() as inp, dest.open('w') as out:
                for line in inp:
                    if int(line.split()[0]) in selected_set:
                        out.write(line)
        else:
            dest.write_bytes(src.read_bytes())
        remote = name if name == 'attributes.txt' else 'CUB_200_2011/' + name
        sources.append({'path': str(dest.relative_to(ROOT)), 'url': BASE + remote,
                        'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                        'saved_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
                        'subset_by_image_id': name in subset_files})
    for i in selected:
        remote = 'CUB_200_2011/images/' + images[i]
        target = ROOT / 'images' / 'cub' / images[i]
        fetch(remote, target)
        sources.append({'path': str(target.relative_to(ROOT)), 'url': BASE + remote,
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    manifest = {'dataset': 'CUB-200-2011', 'official_url': 'https://www.vision.caltech.edu/datasets/cub_200_2011/',
                'mirror': 'pawlo2013/CUB', 'mirror_revision': REVISION,
                'selection': 'Two official-training images per named species, sorted by visible bill/breast/crown/forehead/throat, then wing visibility, then image ID. Selected for teaching; not an evaluation sample.',
                'selected_image_ids': selected, 'retrieved_on': '2026-10-12', 'files': sources,
                'rights': 'CUB images: non-commercial research and educational use; copyrights remain with original owners. The mirror MIT tag does not override original image terms.'}
    (ROOT / 'data' / 'cub' / 'provenance.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Selected:', [(i, images[i]) for i in selected])


if __name__ == '__main__':
    main()
