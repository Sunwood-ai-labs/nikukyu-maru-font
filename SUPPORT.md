# Nikukyu Maru support

Start with the [README](README.md) for downloads, web setup, coverage, and the Japanese and English showcases:

- [Japanese showcase](https://sunwood-ai-labs.github.io/nikukyu-maru-font/)
- [English showcase](https://sunwood-ai-labs.github.io/nikukyu-maru-font/en/)
- [v0.105 release](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/releases/tag/v0.105)

## Usage questions

For a web page, load Nikukyu Maru with an @font-face rule and use the WOFF2 asset. For desktop applications, install the TTF with the operating system's normal font installer. The font is designed for horizontal display text; vertical layout, kerning, and hinting are not implemented.

At small sizes, cat ears, paw pads, combining marks, and small counters become less distinct. If a detail matters, test the actual target size in the showcase or in the application where the font will be used.

The current inventory is [CHARACTERS.md](outputs/CHARACTERS.md). The current machine checks are in [verification.json](outputs/verification.json). Latin concept comparisons and screenshots are in [outputs/latin-concept-review](outputs/latin-concept-review/).

## Report a rendering problem

Please search [existing issues](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/issues) first, then use the [font rendering issue form](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/issues/new?template=bug-report.yml). Include:

- the exact font version, file format, and download source;
- the character or code point, including whether it is ASCII, fullwidth, halfwidth, or a combining sequence;
- the application, operating system, browser, and display size;
- the expected and actual result;
- a minimal string that reproduces the issue;
- a screenshot or a small reproducible example when it can be shared safely.

For shaping reports, say whether the text is NFC or NFD and include the surrounding characters. U+3099 and U+309A are intentional zero-width combining marks, and OpenType ccmp handles the documented voiced and semi-voiced combinations.

## Request a glyph or coverage change

Use the [glyph and coverage request form](https://github.com/Sunwood-ai-labs/nikukyu-maru-font/issues/new?template=glyph-request.yml). Give the Unicode code point, the text or language context, and the reason the character is needed. A request is not a promise that the next release will add the character.

## Documentation and showcase issues

For a broken link, misleading explanation, or problem on the VitePress showcase, open a regular issue and include the page URL, language path, browser, and a screenshot or console message if available. Documentation changes should follow [CONTRIBUTING.md](CONTRIBUTING.md).

## License and attribution

Nikukyu Maru is distributed under the SIL Open Font License 1.1. See [LICENSE](LICENSE) for the project notice and full text, and [SUPPLEMENTAL-SOURCES.md](sources/SUPPLEMENTAL-SOURCES.md) for the upstream source notices. Keep those notices with any redistributed font software.
