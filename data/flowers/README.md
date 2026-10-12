# Five Flowers102 examples

These JPEGs retain their original bytes. Each image was opened and visually
inspected by the Codex assistant on **12 October 2026**. The assistant then
authored **40 concept judgments and 35 approximate support rectangles** across
five photos. No classifier, object detector, or learned CBM was run.

| Image ID | Official class ID | Official category |
|---|---:|---|
| 05147 | 5 | english marigold |
| 06395 | 9 | monkshood |
| 03828 | 17 | purple coneflower |
| 06198 | 49 | oxeye daisy |
| 05399 | 54 | sunflower |

Class IDs are checked against the downloaded official `imagelabels.mat` using
the image ID. Names are independently resolved from the official category page:
its named thumbnail IDs are looked up in that same official label vector. The
mirror's folder labels are therefore not the sole evidence for these names.

**What the scores mean:** independent, subjective visual confidence estimates
in `[0,1]` that a concept is present. They are uncalibrated and are not trained
model probabilities or measured performance. They do not sum to one.

**What the boxes mean:** approximate image-pixel rectangles around visible
support for a concept. A petal box can also contain a flower centre and gaps;
these are neither segmentation masks nor tight ground-truth extents. Multiple
boxes illustrate support and do not guarantee every instance was counted.

`assessment` distinguishes `present`, `absent`, and `uncertain`. When
`observable=false`, `present=0` is only a storage placeholder, not a reliable
negative. Ambiguous background flower heads and an ambiguous possible insect
are deliberately left uncertain, with no asserted box.

Flowers102 already supplies category labels **and flower segmentation images**.
The segmentation images are not used here. The concept vocabulary, scores, and
boxes in this demo are newly authored by the assistant, not supplied by Oxford.

- `assistant-annotations.json`: the exact authored judgments and rectangles.
- `provenance.json`: source URLs pinned to a mirror revision, SHA-256 hashes,
  label verification, coordinate semantics, score meaning, and rights notes.
- `imagelabels.mat`, `categories.html`, `README.txt`, `setid.mat`: preserved
  official metadata used for traceability; the split file is retained but no
  split claim is made by the generator.
- `../../scripts/flowers.py`: offline generator and integrity checks; run
  `python scripts/flowers.py` from the repository root.

Original source: [Oxford Flowers102](https://www.robots.ox.ac.uk/~vgg/data/flowers/102/index.html).
Nilsback and Zisserman, *Automated flower classification over a large number of
classes*, ICVGIP 2008.

The inspected official homepage and README do not state an explicit image reuse
license. Original copyright remains with the image owners; no open image license
is inferred from the mirror. The embedded watermark in image 05147 is preserved.
