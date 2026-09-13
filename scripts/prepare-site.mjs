import { createHash } from 'node:crypto'
import { mkdir, readFile, writeFile, cp } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const GENERATED = path.join(ROOT, 'docs', 'public', 'generated')

const sourcePath = (relativePath) => path.join(ROOT, relativePath)

async function readJson(relativePath) {
  return JSON.parse(await readFile(sourcePath(relativePath), 'utf8'))
}

function withoutFinalNewline(value) {
  return value.replace(/\r?\n$/, '')
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex')
}

function codepointLabel(character) {
  const codepoint = character.codePointAt(0)
  return `U+${codepoint.toString(16).toUpperCase().padStart(4, '0')}`
}

async function main() {
  const design = await readJson('sources/design.json')
  const verification = await readJson('outputs/verification.json')
  const characterText = withoutFinalNewline(await readFile(sourcePath('outputs/characters.txt'), 'utf8'))
  const characters = [...characterText]
  const unicodeCount = Number(verification.unicode_characters)
  const glyphCount = Number(verification.glyphs)

  if (!design.version || !Number.isInteger(unicodeCount) || !Number.isInteger(glyphCount)) {
    throw new Error('design.json or verification.json is missing the site metadata fields')
  }
  if (characters.length !== unicodeCount) {
    throw new Error(`characters.txt has ${characters.length} Unicode characters; verification.json says ${unicodeCount}`)
  }

  await mkdir(GENERATED, { recursive: true })
  const copied = [
    ['outputs/NikukyuMaru-Regular.woff2', 'font.woff2'],
    ['references/04-latin-cat-concept.png', 'concept.png'],
    ['outputs/latin-concept-review/comparison.png', 'comparison.png'],
  ]
  for (const [source, destination] of copied) {
    await cp(sourcePath(source), path.join(GENERATED, destination), { force: true })
  }

  const glyphs = characters.map((character) => ({
    character,
    codepoint: codepointLabel(character),
    value: character.codePointAt(0),
  }))
  await writeFile(
    path.join(GENERATED, 'characters.json'),
    `${JSON.stringify({ version: design.version, unicodeCount, glyphCount, characters: glyphs }, null, 2)}\n`,
    'utf8',
  )

  const font = await readFile(sourcePath('outputs/NikukyuMaru-Regular.woff2'))
  const meta = {
    version: design.version,
    characters: characterText,
    unicodeCount,
    glyphCount,
    fontSha256: sha256(font),
  }
  await writeFile(path.join(GENERATED, 'meta.json'), `${JSON.stringify(meta, null, 2)}\n`, 'utf8')

  console.log(`Prepared site assets for Nikukyu Maru ${design.version}: ${unicodeCount} Unicode characters, ${glyphCount} glyphs`)
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error)
  process.exitCode = 1
})
