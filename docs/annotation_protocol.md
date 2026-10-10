# Annotation protocol (blind human rating)

Each image is shown with the two actions the prompt asks the person to perform (for example, "tucking her hair behind her ear with her right hand" and "holding a book against her chest with her left hand"). Raters choose one label per image:

| Button | Meaning |
|---|---|
| Extra hand or limb | A third hand, an extra arm or leg, or a limb that cannot belong to the person (commission). |
| A hand not doing a prompted action / object not held | All hands are drawn correctly, but one of the prompted actions is not performed, or the object floats without being held (omission). |
| No problem | Both actions are performed and no limb is wrong. |
| Other / unclear | Any other defect (finger count, proportions, wrong number of people) or an image the rater cannot judge. |

- Raters do not see the generator, the training arm, the seed, or the study hypothesis; images carry random codes and appear in a per-rater random order.
- Raters are adult volunteers who are not authors. Individual answers are kept private; only aggregate results are reported.
- Majority rule: with 4 raters, at least 3 agree; with 5, at least 3; with 6, at least 4.
- The sampling of each rating block (strata, sizes, random seeds) and every analysis rule were registered before any rater started; see `preregistration/PREREG.md` (revisions 3, 22, 27, 41, 42).
