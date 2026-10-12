# Where is the concept?

A small, offline concept-grounding exercise: **10 real CUB-200-2011 photos, 18 controlled SVGs in three rendering styles, and 5 assistant-annotated Flowers102 photos**. Open [index.html](index.html) directly in a browser. All viewer images and data are embedded; no server or internet connection is required after preparation.

The viewer lets you select an attribute, see the associated location, inspect its coordinates and certainty, and export annotations. The SVG tab also lets you change the concept vector supplied to an explicit toy classification rule.

## What is ground truth here?

| Annotation | CUB photographs | Generated SVGs |
|---|---|---|
| Class | Original species label; no model inference | Authored rule: A iff yellow bill AND red crown, otherwise B |
| Concepts | Original 312 binary **image-level** attributes per image | Yellow bill, red crown patch, blue wing patch |
| Location | Original 15 part keypoints with visibility | Exact SVG primitive geometry |
| Whole-bird box | Original CUB box | Union of the authored bird's primitives |
| Concept box | **Unavailable.** Optional dashed squares are heuristic proxies | Exact tight axis-aligned box of each present colored primitive |
| Concept mask | Not supplied | White concept / black background SVG; all black for an absent concept |

**No trained classifier, learned CBM score, or measured classification result is claimed. Flower scores are subjective assistant visual estimates, not calibrated model probabilities.** Ground-truth concept annotations and model predictions are different objects. A model's attention or saliency map would be a further object to evaluate against these locations.

CUB supports part localization, but it does not supply bounding boxes for each attribute. Our authored attribute-to-part mapping connects, for example, `has_crown_color::red` to the native crown point. That correspondence is a useful supervision proxy; it does not identify the extent of red pixels or prove that the predictor attends to them. Bilateral attributes map to every visible corresponding part, without evidence that the attribute occurs on both sides. Global attributes such as overall size have no direct local mapping here.

## Files

- `index.html`: self-contained interactive viewer.
- `images/cub/`: 10 original JPEGs, unmodified.
- `images/svg/`: six original editable vector drawings.
- `images/svg/masks/`: 18 per-concept SVG masks, including four empty masks for absent concepts.
- `outputs/annotations.json`: all 33 examples, native labels/keypoints/boxes, exact SVG boxes, and explicitly typed CUB proxies.
- `outputs/concepts.csv`: 3,214 concept rows, convenient for inspection.
- `outputs/synthetic-concepts.coco.json`: 12 pure-vector images and 28 positive concept detections in COCO-style bounding-box format. Vector area is provided (analytic for primitives, sampled for Bezier paths); `mask_svg` is an extension, not COCO polygon/RLE segmentation. The file names reference SVGs; rasterize before passing to loaders requiring PNG/JPEG. No CUB proxy or assistant flower box appears in this exact-geometry export. Photo editing masks have a separate COCO-style file.
- `data/cub/raw/`: original metadata rows for the selected images, plus name dictionaries and the source README.
- `data/cub/provenance.json`: pinned mirror revision, original URLs, SHA-256 hashes, selection rule, and use terms.
- `outputs/validation.json`: data integrity and geometry check results.

## The six controlled examples

The concept order is **[yellow bill, red crown patch, blue wing patch]**. This is a designed toy task, not a bird taxonomy.

| SVG | Concepts | Class | Change relative to reference |
|---|---|---|---|
| `01-reference.svg` | [1, 1, 1] | A | None |
| `02-neutral-bill.svg` | [0, 1, 1] | B | Bill color only |
| `03-neutral-crown.svg` | [1, 0, 1] | B | Crown color only |
| `04-neutral-wing.svg` | [1, 1, 0] | A | Wing color only; class-irrelevant concept |
| `05-moved-bird.svg` | [1, 1, 1] | A | Entire bird translated by (+72, -22) pixels |
| `06-red-distractor.svg` | [1, 0, 1] | B | Neutral-crown bird plus a red background circle |

In the simple set, every target primitive is fully visible, filled without stroke, unrotated, and unclipped. The bill is a triangle; the crown and wing patches are ellipses. Boxes are **continuous vector bounds**, not raster-pixel extents; rasterization can change edge coverage by a pixel. The mask records the actual concept shape, whereas its box also includes surrounding pixels. Structural gray areas and the background circle are not positive instances of these three target concepts. The distractor has its own box in the JSON.

At the reference position, the exact boxes `[x, y, width, height]` are:

- Yellow bill: `[350, 141, 57, 34]`
- Red crown patch: `[278, 102, 62, 26]`
- Blue wing patch: `[168, 193, 140, 70]`

An absent color concept gets `ground_truth_concept_boxes: []`; the neutral anatomical part still has `part_geometry`. Unavailable CUB concept boxes use `null`. **Absent, unavailable, and unobservable are not interchangeable.**

The interactive concept switches edit the inputs to the class rule. They do not recolor the image or alter its ground-truth annotation. Use the six authored drawings to inspect actual image changes.

## Ten-minute exercise

1. On a CUB photo, select a local color attribute. Identify the original label, annotator certainty, and related part point. Turn on proxy boxes and identify the assumption used to create them.
2. Turn off “Present only” to inspect absent or unobservable attributes. Certainty 1 means “not visible”; it is not treated as a reliable negative. Other certainty levels are categorical judgments, not probabilities. Original raw bits are always retained.
3. Compare the reference SVG with its bill, crown, and wing edits. Predict the output of `A iff bill AND crown` before inspecting it. The first two edits change class; the wing edit does not.
4. Compare reference and moved SVGs. Their concept vectors and class agree, while their bounding boxes differ. A concept vector therefore cannot recover location on its own.
5. Compare the neutral-crown and red-distractor SVGs. A global “red exists” detector would respond to the distractor, but the semantic concept “red crown patch” stays absent.

These are inspectable fixtures for checking a proposed localization method. Six drawings are not a train/test benchmark. To evaluate a learned spatial CBM, generate many independent layouts and shapes, split by generation factors, predict concepts and locations, and separately report concept errors, class errors, box overlap / mask overlap, and controlled-change consistency. With CUB, score landmark agreement rather than claiming box IoU against nonexistent concept-box annotations. Localization agreement alone still does not establish causal model reliance.

## Rebuild and verify

Python 3.10+ standard library is enough for acquisition, rebuilding, and data checks:

```bash
cd /Users/nipun/git/cbm
python3 scripts/fetch_cub.py  # First fetch: about 75 MB metadata plus ten JPEGs.
python3 scripts/build.py     # Offline once selected raw files exist.
python3 scripts/validate.py
```

The full metadata download is cached under ignored `work/cub-source/`; only the selected image rows enter the durable dataset. No CUB class-average attributes are used.

Optional local web serving:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765`. The frontend has no third-party JavaScript, font, CSS, build, or runtime dependencies. This intentionally follows the request for a small, portable exercise.

## Selection and provenance

Two official-training images were selected for each of Cardinal, Northern Flicker, American Goldfinch, Blue Jay, and Common Yellowthroat. Within each species, order by number of visible bill/breast/crown/forehead/throat points, then wing visibility, then image ID. IDs: **898, 900, 1994, 2002, 2651, 2654, 4197, 4199, 11731, 11732**. This favors inspectable examples and is not representative evaluation sampling.

The optional CUB box is a square centered at a visible mapped part. Its side is `0.18 × max(native bird box width, native bird box height)`, clipped to the image. It is only produced for a present attribute with certainty greater than 1. It can include background and miss part of the intended concept. The parameter is an authored visualization choice, not an estimated anatomical extent.

Coordinates in the raw CUB metadata are preserved numerically, without inferred origin conversion, resizing, or cropping. The viewer uses the original image dimensions as its SVG viewBox. All exported boxes are `[x_min, y_min, width, height]`; normalized versions divide x/width by image width and y/height by image height.

- [Official CUB dataset description](https://www.vision.caltech.edu/datasets/cub_200_2011/)
- [Official CaltechDATA archive](https://data.caltech.edu/records/65de6-vp158)
- [Pinned lightweight-download mirror](https://huggingface.co/datasets/pawlo2013/CUB/tree/8a8486039c718e33d87b96ed42c0f457e6a7d939)

Source: Wah, Branson, Welinder, Perona, and Belongie, *The Caltech-UCSD Birds-200-2011 Dataset*, CNS-TR-2011-001, 2011. The source README has a “322” typo in its introductory directory description; the actual dictionary and per-image rows contain **312** attributes, matching the official website.

CUB image copyrights remain with their owners; the official dataset restricts image use to non-commercial research and education. The mirror's MIT label is not a replacement for the original image terms. The complete exercise is published as a static GitHub Pages site at https://nipunbatra.github.io/cbm-grounding/. No backend, inference server, account, or API key is required.


## More realistic SVG options

The **Realistic SVG** tab has a rendering selector:

- **Photo texture + exact edit masks** (`images/svg-photographic/`): embeds an original CUB photograph in each standalone SVG, desaturates it, and uses authored polygons to recolor the bill, crown, and wing patches. Feather texture comes from the photo. Mask boundaries and their bounding boxes are exact **designed editing regions**; their anatomical fit is approximate, hand-traced by the assistant. These must not be reported as independently validated anatomical segmentation. The moved example translates the entire photograph, not the bird alone. These edited images are constructed examples, not original CUB observations.
- **Pure-vector feathered illustration** (`images/svg-naturalistic/`): an invented bird with curved silhouette, gradients, layered feather detail, eye, feet, and perch. Filled concept silhouettes have exact Bezier bounds; decorative texture is clipped to those silhouettes. This remains an illustration, not a photograph or a real-species claim.

Both styles repeat the same six concept interventions as the simple set. The photo-derived set is exported separately to `outputs/photographic-edit-masks.coco.json` (six images, 14 positive color-edit regions). The pure-vector COCO export covers both simple and feathered styles. All three sets include per-concept SVG masks; absent concepts have black masks. The full-body box is supplied only for CUB and the simple drawings; realistic variants focus on the three concept regions.

## Verification of CUB's dots

The coordinates, visibility flags, and anatomical names are native CUB annotations, not placed by the assistant. **All 150 selected part records matched an independent copy** of `parts/part_locs.txt`. The report at `data/cub/point-verification.json` records its pinned URL and checksum. The site exposes the native rows and names from the inspector. For image 898, the native beak is `(134,83)` and crown is `(176,53)`.

The **attribute-to-part association** is authored: CUB has separate image attributes and part records. The optional **proxy extent** is also authored. The site distinguishes both from the original dots.

## Assistant annotations: Flowers102

The third image family has five real flowers (English marigold, monkshood, purple coneflower, oxeye daisy, sunflower), **40 concept-presence scores and 35 supporting boxes**. Every photo was visually inspected before annotation. Native class IDs were verified against Oxford's official `imagelabels.mat`; class names were checked through the official category thumbnail mapping.

The eight concepts are yellow petals, white petals, purple/pink petals, dark centre, yellow centre, recognizable green leaf, multiple heads, and visible insect. Definitions, scores, box coordinates, and per-judgment notes are exposed in `data/flowers/assistant-annotations.json` and the viewer. The scores are independent, subjective visual estimates in `[0,1]`: **uncalibrated, not trained-model probabilities, not performance measurements, and not required to sum to one**. A supporting petal box can enclose the centre and gaps. Multiple boxes do not imply exhaustive instance counting.

Oxford already supplies category labels and flower segmentation images. The concept vocabulary, scores, and boxes here are newly authored; native segmentation masks are not used. `assessment=uncertain` / `observable=false` is retained as uncertainty, even though its storage bit is zero. Human review would be needed before using these as gold labels. See `data/flowers/provenance.json` for exact sources, image SHA-256 hashes, annotation method, and rights notes; no blanket open image license is inferred.

## Static publication and downloadable copy

The published `index.html` includes every displayed image and all inspector data. Download buttons use browser-side Blob URLs; the ZIP and provenance links are ordinary static files. The complete ZIP also includes raw annotations, individual images/SVGs, masks, CSV/JSON exports, source, and regeneration scripts. There is no frontend/backend split.
