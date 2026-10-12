#!/usr/bin/env python3
"""Package the complete offline exercise without acquisition caches or scratch files."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'index.html',ROOT/'README.md']
for directory in ['src','scripts','images','data']:
    files.extend(p for p in (ROOT/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name!='.DS_Store')
for name in ['annotations.json','concepts.csv','synthetic-concepts.coco.json','photographic-edit-masks.coco.json','validation.json','build-manifest.json']:
    files.append(ROOT/'outputs'/name)
archive=ROOT/'outputs/cbm-grounding.zip'
with ZipFile(archive,'w',ZIP_DEFLATED) as z:
    for path in sorted(files):z.write(path,'cbm-grounding/'+str(path.relative_to(ROOT)))
report={'archive':'outputs/cbm-grounding.zip','files':len(files),'bytes':archive.stat().st_size,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest()}
(ROOT/'outputs/package-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
