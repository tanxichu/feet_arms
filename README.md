# Omission Is Free — public materials

Companion materials for the WVAQ @ WACV 2027 submission
"Omission Is Free: Hand-Artifact Detectors Miss Skipped Hand Actions, and Rewards Built on Them Can Learn to Skip Them" (Luckison Du).

## Contents

| Folder | What is in it |
|---|---|
| `preregistration/PREREG.md` | The preregistration log (in Chinese), revisions 1–47. Each revision states its predictions, thresholds and analysis rules, and was added before the experiment or rating it concerns. Later notes about deviations are marked as such. |
| `preregistration/HISTORY.md` | The commit time of every change to `PREREG.md` in the authors' working repository, with the revision numbers each commit touched. |
| `analysis/` | The statistics scripts that produce every number in the paper (`paper_numbers.py` writes the LaTeX macros). They read per-image judge labels and generated images that are not released (see below), so they document the computation rather than run as-is. Paths are replaced by `DATA/` (experiment data) and `PRIVATE_RATINGS/` (raw human ratings, not released). |
| `results/` | The aggregate outputs of those scripts: counts per arm, paired tests, permutation p-values, judge precision against raters, Krippendorff's alpha, and the cross-machine bit-identity check. |
| `data/klein_prompts.json` | The 1,227 FLUX.2 Klein prompts (person index, sex, action id, prompt text). Source-photo identifiers are replaced by indices. |
| `docs/annotation_protocol.md` | The blind rating protocol. |

## Not released

- Generated images, trained LoRA weights and detectors (available to reviewers on request).
- Raw human ratings and anything that identifies a rater; only aggregate results are reported.
- Source photographs and their Flickr identifiers (to be released with the camera-ready version).

## Code that is not here

The training and generation code depends on internal infrastructure and is available on request.
