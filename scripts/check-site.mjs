import { createHash } from 'node:crypto'
import { readFile, stat } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DIST = path.join(ROOT, 'docs', '.vitepress', 'dist')
const GENERATED = path.join(ROOT, 'docs', 'public', 'generated')
const SITE_URL = 'https://sunwood-ai-labs.github.io/nikukyu-maru-font/'
const OG_IMAGE = `${SITE_URL}generated/comparison.png`

const sourcePath = (relativePath) => path.join(ROOT, relativePath)

async function readText(relativePath) {
  return readFile(sourcePath(relativePath), 'utf8')
}

async function readJson(relativePath) {
  return JSON.parse(await readText(relativePath))
}

async function exists(relativePath) {
  try {
    await stat(sourcePath(relativePath))
    return true
  } catch {
    return false
  }
}

async function bytes(relativePath) {
  return readFile(sourcePath(relativePath))
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex')
}

function stripFinalNewline(value) {
  return value.replace(/\r?\n$/, '')
}

function codepointCount(value) {
  return [...value].length
}

function fail(errors, message) {
  errors.push(message)
}

async function main() {
  const errors = []
  const design = await readJson('sources/design.json')
  const verification = await readJson('outputs/verification.json')
  const expectedCharacters = stripFinalNewline(await readText('outputs/characters.txt'))
  const expectedUnicodeCount = Number(verification.unicode_characters)
  const expectedGlyphCount = Number(verification.glyphs)

  if (codepointCount(expectedCharacters) !== expectedUnicodeCount) {
    fail(errors, 'outputs/characters.txt does not match outputs/verification.json')
  }

  const requiredGenerated = ['font.woff2', 'concept.png', 'comparison.png', 'meta.json', 'characters.json']
  for (const filename of requiredGenerated) {
    if (!(await exists(path.join('docs', 'public', 'generated', filename)))) {
      fail(errors, `missing staged asset docs/public/generated/${filename}; run npm run site:prepare`)
    }
  }
  if (!(await exists(path.join('docs', 'public', 'favicon.svg')))) {
    fail(errors, 'missing docs/public/favicon.svg used by the custom theme')
  }

  let meta
  let characterList
  if (errors.length === 0) {
    meta = await readJson('docs/public/generated/meta.json')
    const characterData = await readJson('docs/public/generated/characters.json')
    characterList = Array.isArray(characterData) ? characterData : characterData.characters
    if (!meta || typeof meta !== 'object') fail(errors, 'generated/meta.json is not an object')
    if (!Array.isArray(characterList)) fail(errors, 'generated/characters.json must contain a characters array')
  }

  if (meta) {
    if (meta.version !== design.version) fail(errors, 'generated/meta.json version differs from sources/design.json')
    if (typeof meta.characters !== 'string' && !Array.isArray(meta.characters)) {
      fail(errors, 'generated/meta.json characters must be the complete Unicode string or array')
    }
    const metaCharacters = typeof meta.characters === 'string' ? meta.characters : meta.characters.join('')
    if (metaCharacters !== expectedCharacters) fail(errors, 'generated/meta.json characters differ from outputs/characters.txt')
    if (meta.unicodeCount !== expectedUnicodeCount) fail(errors, 'generated/meta.json unicodeCount is stale')
    if (meta.glyphCount !== expectedGlyphCount) fail(errors, 'generated/meta.json glyphCount is stale')
    const font = await bytes('outputs/NikukyuMaru-Regular.woff2')
    if (meta.fontSha256 !== sha256(font)) fail(errors, 'generated/meta.json fontSha256 is stale')
  }

  if (Array.isArray(characterList)) {
    const listedCharacters = characterList.map((entry) => typeof entry === 'string' ? entry : entry.character)
    if (listedCharacters.join('') !== expectedCharacters) fail(errors, 'generated/characters.json list differs from outputs/characters.txt')
    if (listedCharacters.length !== expectedUnicodeCount) fail(errors, 'generated/characters.json count is stale')
    if (new Set(listedCharacters).size !== listedCharacters.length) fail(errors, 'generated/characters.json contains duplicate characters')
  }

  const sourceAssets = [
    ['outputs/NikukyuMaru-Regular.woff2', 'docs/public/generated/font.woff2'],
    ['references/04-latin-cat-concept.png', 'docs/public/generated/concept.png'],
    ['outputs/latin-concept-review/comparison.png', 'docs/public/generated/comparison.png'],
  ]
  for (const [source, staged] of sourceAssets) {
    if ((await exists(source)) && (await exists(staged))) {
      if (sha256(await bytes(source)) !== sha256(await bytes(staged))) fail(errors, `${staged} differs from ${source}`)
    }
  }

  const docsConfig = await readText('docs/.vitepress/config.mts')
  if (!docsConfig.includes("base: '/nikukyu-maru-font/'")) fail(errors, 'VitePress base is not /nikukyu-maru-font/')
  if (!docsConfig.includes("link: '/en/'") || !docsConfig.includes("link: '/'")) fail(errors, 'locale links are missing from VitePress config')
  const japaneseHome = await readText('docs/index.md')
  const englishHome = await readText('docs/en/index.md')
  if (!japaneseHome.includes('title: にくきゅう丸')) fail(errors, 'Japanese home title is missing')
  if (!englishHome.includes('title: Nikukyu Maru')) fail(errors, 'English home title is missing')

  const ignore = await readText('.gitignore')
  if (!ignore.includes('docs/public/generated/')) fail(errors, 'generated site assets are not ignored')
  if (!ignore.includes('docs/.vitepress/dist/')) fail(errors, 'VitePress build output is not ignored')

  for (const workflow of ['.github/workflows/ci.yml', '.github/workflows/pages.yml']) {
    const content = await readText(workflow)
    const uses = [...content.matchAll(/^\s*uses:\s*([^\s#]+)\s*(?:#.*)?$/gm)].map((match) => match[1])
    if (!uses.length) fail(errors, `${workflow} has no pinned actions`)
    for (const action of uses) {
      if (!/@[0-9a-f]{40}$/.test(action)) fail(errors, `${workflow} has an unpinned action: ${action}`)
    }
  }

  const requiredDist = [
    'index.html',
    'en/index.html',
    'favicon.svg',
    'generated/font.woff2',
    'generated/concept.png',
    'generated/comparison.png',
    'generated/meta.json',
    'generated/characters.json',
  ]
  for (const relativePath of requiredDist) {
    const fullPath = path.join(DIST, relativePath)
    try {
      const info = await stat(fullPath)
      if (!info.isFile() || info.size === 0) fail(errors, `empty or missing docs build output: ${relativePath}`)
    } catch {
      fail(errors, `missing docs build output: ${relativePath}; run npm run docs:build`)
    }
  }

  for (const page of ['docs/.vitepress/dist/index.html', 'docs/.vitepress/dist/en/index.html']) {
    if (await exists(page)) {
      const html = await readText(page)
      if (!html.includes('/nikukyu-maru-font/')) fail(errors, `${page} does not contain the configured base path`)
      if (!html.includes(`https://sunwood-ai-labs.github.io/nikukyu-maru-font/generated/comparison.png`)) {
        fail(errors, `${page} does not contain the configured social preview image`)
      }
    }
  }

  const rootHtmlPath = 'docs/.vitepress/dist/index.html'
  const englishHtmlPath = 'docs/.vitepress/dist/en/index.html'
  if (await exists(rootHtmlPath)) {
    const html = await readText(rootHtmlPath)
    if (!html.includes(`<link rel="canonical" href="${SITE_URL}">`)) fail(errors, 'Japanese page canonical URL is missing')
    if (!html.includes('<meta property="og:locale" content="ja_JP">')) fail(errors, 'Japanese Open Graph locale is missing')
    if (!html.includes(`<meta name="twitter:card" content="summary_large_image">`)) fail(errors, 'Twitter card metadata is missing')
    if (!html.includes(`<link rel="icon" href="${SITE_URL}favicon.svg"`)) fail(errors, 'absolute favicon URL is missing')
  }
  if (await exists(englishHtmlPath)) {
    const html = await readText(englishHtmlPath)
    if (!html.includes(`<link rel="canonical" href="${SITE_URL}en/">`)) fail(errors, 'English page canonical URL is missing')
    if (html.includes(`<link rel="canonical" href="${SITE_URL}">`)) fail(errors, 'English page retains the Japanese canonical URL')
    if (!html.includes('<html lang="en"')) fail(errors, 'English page lang attribute is missing')
    if (!html.includes('<meta property="og:locale" content="en_US">')) fail(errors, 'English Open Graph locale is missing')
    if (!html.includes('content="A Japanese display font with round shapes, little ears, and a curious tail."')) {
      fail(errors, 'English page description metadata is missing')
    }
  }

  const report = {
    pass: errors.length === 0,
    checked: {
      version: design.version,
      unicodeCount: expectedUnicodeCount,
      glyphCount: expectedGlyphCount,
      generatedAssets: requiredGenerated,
      pages: ['/', '/en/'],
      buildDirectory: 'docs/.vitepress/dist',
      publicUrl: SITE_URL,
      socialPreview: OG_IMAGE,
    },
    errors,
  }
  console.log(JSON.stringify(report, null, 2))
  if (errors.length) process.exitCode = 1
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exitCode = 1
})
