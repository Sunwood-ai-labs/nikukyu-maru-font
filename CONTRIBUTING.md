# Contributing to Nikukyu Maru

Thank you for helping improve Nikukyu Maru. The project is a font, a reproducible build, and a set of visual checks. Please keep those three parts aligned when proposing a change.

## Start with the current release

Use the 0.105 evidence as the current baseline. The 0.103 Japanese audit and the 0.104 Latin pages are preserved as historical records and should not be presented as fresh 0.105 validation.

Before editing, read:

- [README.md](README.md) for coverage, usage, and the current release links.
- [SUPPORT.md](SUPPORT.md) for problem reports and reproducible examples.
- [sources/SUPPLEMENTAL-SOURCES.md](sources/SUPPLEMENTAL-SOURCES.md) for upstream font provenance.
- [sources/LATIN-DESIGN.md](sources/LATIN-DESIGN.md) for the 0.105 image-derived Latin design.

## Set up a local environment

The repository pins its Python dependencies in requirements files. [uv](https://docs.astral.sh/uv/) is recommended for a local virtual environment:

~~~powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
uv run --active python -X utf8 build.py
~~~

Install additional requirements only for the work you need:

~~~powershell
uv pip install -r requirements-trace.txt
uv pip install -r requirements-validation.txt
~~~

The trace file includes the base requirements; the validation file adds the browser-shaping dependency used by the checks.

## Make a font change

The editable source is sources/NikukyuMaru-Regular.ufo/. Build settings live in sources/design.json. Keep source edits deterministic and record the reason for a changed outline in the relevant source note.

For the 0.105 Latin concept workflow:

~~~powershell
uv run --active python -X utf8 trace_latin_concept.py
uv run --active python -X utf8 latin_cats.py
uv run --active python -X utf8 build.py
uv run --active python -X utf8 concept_latin_review.py
uv run --active python -X utf8 concept_latin_overview.py
~~~

The Latin masters are derived from references/04-latin-cat-concept.png. Keep the image, prompt, source boxes, scale, and baseline records together. An image-derived shape should be checked as an actual TTF/WOFF2 glyph before it is described as accepted.

build.py --regenerate can recreate the UFO and overwrite manual UFO edits. Work on a branch or a disposable copy when testing that path. Do not change the generated font or a release archive as a shortcut for changing the source.

## Run the checks

Run the checks that cover your change and report the exact command and result in the pull request:

~~~powershell
uv run --active python -X utf8 verify_latin_concept.py
uv run --active python -X utf8 japanese_validation.py
uv run --active python -X utf8 verify_latin_regression.py --baseline <previous.ttf> --current outputs/NikukyuMaru-Regular.ttf --include-ampersand
~~~

The regression check needs an explicit previous TTF because baseline fixtures under work/ are local evidence and are not part of a fresh checkout. For a 0.105 Latin change, inspect the generated HTML and screenshots in outputs/latin-concept-review/. A numerical contour comparison is useful evidence, but it does not replace visual review of counters, ear placement, tails, and small-size readability. If you update a user-facing screenshot or report, make sure its font hash and release label identify the current build.

For documentation site changes, use the repository's Node checks:

~~~powershell
npm ci
npm run docs:build
npm run site:check
~~~

Use npm run docs:dev for an interactive local preview and npm run docs:preview to serve the built site locally.

## Open a pull request

Describe the user-visible result first, then explain the source and validation. A useful pull request includes:

- the affected release or source area and the exact code points involved;
- before/after evidence for visible glyph changes;
- the commands run and whether the check was structural, raster, shaping, or browser visual review;
- links to the relevant provenance and license notices;
- any known limitation, especially horizontal-only layout or small-size detail loss.

Keep generated archives, dependency directories, temporary worktrees, and local virtual environments out of commits. The repository ignores work/, ZIP archives, .venv/, and Python cache files; do not force them into a pull request. Do not include private user data in screenshots or issue evidence.

Use a focused English commit title with an emoji when a commit is needed. Keep unrelated cleanup out of the change so reviewers can compare the font and its evidence.

## Font provenance and license

Mochiy Pop One and Zen Maru Gothic Black notices are retained under vendor/. The top-level LICENSE is the project copy of OFL.txt. Do not add a different license for the font software or remove an upstream notice. See [LICENSE](LICENSE) and [SUPPLEMENTAL-SOURCES.md](sources/SUPPLEMENTAL-SOURCES.md) before adding a new upstream outline.
