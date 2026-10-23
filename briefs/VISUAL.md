# VISUAL stream brief: look at every rendered output and list visible defects

Report only: write `docs/status/VISUAL.md` and put screenshots under `notebook/v3/.work/visual/`
(ignored). Do not edit any other file. Do not commit.

Render every output cell of `notebook/v3/tritflow_ja_output.ipynb` and `tritflow_en_output.ipynb`
(build them first with `TRITFLOW_REF=$(git rev-parse HEAD) python3 submission/build_submission.py`
only if they are missing; otherwise use them) in headless Chrome at 1140 px and at 800 px width, the
way Colab shows them (HTML/JS outputs live, images as images). Look at each screenshot. Report only
visible defects: clipped or overlapping text, unreadable labels, wrong language in a ja/en output,
controls that do not respond, blank or broken figures, legends hiding data, horizontal scroll, mojibake.
For each: cell id/section, screenshot path, what is wrong, and the smallest fix (file/function).
No taste or style preferences; no suggestions to add content.
