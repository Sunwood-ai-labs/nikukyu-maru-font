# Font showcase verification — 2026-09-13

The repository and bilingual GitHub Pages showcase were completed using the released **0.105** font. The site uses real text rendered by its WOFF2, including the hero, live tester, character collection, and use examples.

## Published artifacts

- [Japanese showcase](https://sunwood-ai-labs.github.io/nikukyu-maru-font/)
- [English showcase](https://sunwood-ai-labs.github.io/nikukyu-maru-font/en/)
- [Pages workflow](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/actions/workflows/pages.yml) and [Site CI](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/actions/workflows/ci.yml)
- First successful deployment: [34752534712](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/actions/runs/34752534712), source `84549b2b9ae0baabeb65cf1d5d5738a8fe2aa8b6`; [CI](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/actions/runs/34752534766) also succeeded.
- [Public HTTP/asset evidence](site-showcase/public-http.json): both locales, WOFF2, metadata, reference, comparison, favicon, and all three release downloads returned HTTP 200.

## Screenshot review

Screenshots were inspected in the Windows in-app Chromium browser. Responsive checks used real pages inside explicitly sized iframe viewports, not scaled screenshots. These checks do not claim physical iOS/Android or Safari testing.

- [Published desktop](site-showcase/public-desktop.png): real Japanese lettering, Aa paw counter, ear shapes, g tail, header and CTA.
- [Published mobile](site-showcase/public-mobile.png): Japanese at 390px and English at 320px, including the repaired English heading and poster width.
- [Published playground](site-showcase/public-playground.png): editable text, vermilion ink, and visible keyboard focus.
- Local 768px tablet and desktop reviews also covered the character grid, three use examples, original generated reference, downloads, and expanded CSS instructions.
- Horizontal overflow was measured after the final responsive repair: the 320px frame had client/scroll widths **308/308**; the 390px frame had **378/378** (the browser reserves 12px for its scrollbar).

## Interactions and edge cases

| Check | Result |
| --- | --- |
| Japanese/English navigation | Correct localized heading, document title, language, and navigation labels |
| Published font loading | `document.fonts.check` true; served WOFF2 SHA-256 matches the release |
| Preset buttons and text input | Text changes and resets correctly; published input checked with `ねこ CAT & nap` |
| Size and spacing | Actual pointer clicks produced 110px and 0.11em; computed CSS was 110px and 12.1px |
| Ink and ss01 | Cocoa/vermilion/forest controls work; ss01 applies paw alternates to こ/る |
| Empty input | Native select-all/backspace gives empty text, `0 / 180`, and placeholder |
| Unicode input limit | Pasting 181 paw-print characters retains 180 code points and displays `180 / 180` |
| Unsupported character | 🐈 produces the fallback-font notice |
| Character categories | Latin 106, hiragana 92, katakana 157 (including 63 halfwidth), kanji 6716, other 445; total 7516 |
| All and more | All shows `60 / 7516`; Kanji increases from 60 to 120 |
| Search | U+0041 returns A; absent emoji returns zero; malformed U+004G returns zero |
| Unicode bounds review | U+110000, U+FFFFFF and U+D800 return zero; U+1F43E and 0xFF9E are valid |
| FAQ and CSS copy | Native details expand; Copy CSS reports Copied |
| Keyboard | Tab moves to the next ink button with a solid visible focus outline |
| 404 | Missing URL returns 404; the published 404 application renders its message and home link; header anchors also route back to the showcase |

The responsive review found and repaired the 320px English heading, poster min-content width, decorative paw overflow, and layout movement while the character metadata loads. An independent LUNA MAX review found the character-category gaps, code-point limit mismatch, invalid Unicode search handling, Japanese ARIA labels, and two low-contrast text colors. All findings were corrected and reviewed again. The corrected contrast ratios are approximately 5.20:1 and 5.16:1. IME composition is preserved in the input handler; native Japanese IME conversion was reviewed in code but not exercised with an OS IME.

## Build and repository checks

- `npm ci`, `npm run docs:build`, and `npm run site:check` succeeded. The dev server's Japanese/English routes and assets returned HTTP 200.
- CI validates base paths, generated files, exact font/image hashes, complete character metadata, locales, canonical/OG/Twitter tags, and the static build.
- Source/generated/dependency boundaries are explicit: `node_modules`, VitePress cache/dist, and staged public assets are ignored; the build stages the released assets reproducibly.
- English/Japanese README sections match; relative links resolve; issue forms parse as YAML. Contribution, support and PR guidance are included.
- `LICENSE` is byte-for-byte identical to `OFL.txt`, including its original whitespace. No new font release was created.
- GitHub description, homepage and topics are configured. Actions are pinned to commit SHAs and Pages uses the workflow deployment mode.
- The repository-polish staged-payload check ran before each GitHub-bound commit. No archive, dependency tree, duplicate font binary, or temporary test harness was staged.

## Remaining dependency limitation

`npm audit --omit=dev` reports **0** vulnerabilities. The full audit reports **3 development-dependency findings**: esbuild (moderate), Vite (high), and VitePress (moderate). npm reports `fixAvailable: false` for the pinned stable VitePress 1.6.4 dependency tree. No unverified major/alpha override was introduced. The preview/dev servers were bound to 127.0.0.1; GitHub Pages serves the static build, not those development servers.

## Font preservation

| File | SHA-256 before and after |
| --- | --- |
| TTF | `186c97f8b32790d35c7b6cdfedf23cddc3136abd7c7a49e5bcf6ea296794c80d` |
| WOFF2, including public delivery | `5723041efc183c7ad5be9d6b5350ffd5149d36335a11d5106ea6c97c8632db4f` |
