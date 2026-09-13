## Summary

Describe the user-visible result first. Link the issue or design record when one exists.

## Scope

- [ ] Font outlines or UFO source
- [ ] Build or tracing code
- [ ] Validation or evidence
- [ ] README, support, or documentation site

List the exact characters, code points, files, and release version affected.

## Validation

Record the commands you ran and their results. Identify whether each check is structural, raster, shaping, or browser visual review.

~~~powershell
uv run --active python -X utf8 build.py
uv run --active python -X utf8 verify_latin_concept.py
~~~

For a documentation change, also include the relevant Node checks:

~~~powershell
npm ci
npm run docs:build
npm run site:check
~~~

## Visual evidence

Link before/after screenshots or the current evidence report for visible glyph changes. Include the font hash and the target release when screenshots are involved.

## Provenance and licensing

- [ ] Upstream font notices and source records are preserved.
- [ ] New image or outline sources are documented.
- [ ] The font remains under SIL Open Font License 1.1.
- [ ] No private user data appears in the evidence.

## Release boundary

State whether this changes the current release, an unreleased build, or historical evidence. Keep generated archives, dependency directories, and temporary work files out of the pull request.
