<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useData, useRoute, withBase } from "vitepress";
import { copy } from "./copy";

const route = useRoute();
const { page } = useData();
const isEn = computed(() => route.path.includes("/en/"));
const t = computed(() => copy[isEn.value ? "en" : "ja"]);
const repo = "https://github.com/Sunwood-ai-labs/nikukyu-maru-font";
const version = ref("0.105");
const release = computed(() => `${repo}/releases/download/v${version.value}/`);
const sample = ref(t.value.samples[0]);
const size = ref(72);
const spacing = ref(0);
const ink = ref(0);
const alternates = ref(false);
const inks = ["#35271f", "#aa3527", "#36584b"];
const category = ref(0);
const query = ref("");
const shown = ref(60);
const characters = ref<string[]>([]);
const metadataError = ref(false);
const fontState = ref("loading");
const copyState = ref("");
const cssExample = `@font-face {
  font-family: "Nikukyu Maru";
  src: url("NikukyuMaru-Regular.woff2") format("woff2");
  font-weight: 800;
  font-display: swap;
}
.headline {
  font-family: "Nikukyu Maru", sans-serif;
  font-weight: 800;
  line-height: 1.55;
  /* Optional paw alternates for こ / る */
  font-feature-settings: "ss01" 1;
}`;
const missing = computed(() => {
  if (!characters.value.length) return [];
  const supported = new Set(characters.value);
  return [
    ...new Set(
      [...sample.value].filter((c) => !/\s/.test(c) && !supported.has(c)),
    ),
  ].slice(0, 12);
});
function characterCategory(c: string) {
  const value = c.codePointAt(0)!;
  if (/^[A-Za-z&Ａ-Ｚａ-ｚ＆]$/.test(c)) return 0;
  if (value >= 0x3041 && value <= 0x309f) return 1;
  if (
    (value >= 0x30a0 && value <= 0x30ff) ||
    (value >= 0xff61 && value <= 0xff9f)
  )
    return 2;
  if (
    (value >= 0x4e00 && value <= 0x9fff) ||
    (value >= 0xf900 && value <= 0xfaff)
  )
    return 3;
  return 4;
}
const filtered = computed(() => {
  const term = query.value.trim();
  if (term) {
    const hex = term.match(/^(?:U\+|0x)([\da-f]{4,6})$/i);
    if (/^(?:U\+|0x)/i.test(term) && !hex) return [];
    const value = hex ? parseInt(hex[1], 16) : null;
    if (
      value !== null &&
      (value > 0x10ffff || (value >= 0xd800 && value <= 0xdfff))
    )
      return [];
    const wanted = new Set(
      value === null ? [...term] : [String.fromCodePoint(value)],
    );
    return characters.value.filter((c) => wanted.has(c));
  }
  return characters.value.filter(
    (c) => category.value === 5 || characterCategory(c) === category.value,
  );
});
function onSampleInput(event: Event) {
  if ((event as InputEvent).isComposing) return;
  const field = event.target as HTMLTextAreaElement;
  const limited = [...field.value].slice(0, 180).join("");
  if (field.value !== limited) field.value = limited;
  sample.value = limited;
}
const visible = computed(() => filtered.value.slice(0, shown.value));
const specimenStyle = computed(() => ({
  fontSize: `${size.value}px`,
  letterSpacing: `${spacing.value / 100}em`,
  color: inks[ink.value],
  fontFeatureSettings: `"ss01" ${alternates.value ? 1 : 0}`,
}));
function reset() {
  sample.value = t.value.samples[0];
  size.value = 72;
  spacing.value = 0;
  ink.value = 0;
  alternates.value = false;
}
function cp(c: string) {
  return "U+" + c.codePointAt(0)!.toString(16).toUpperCase().padStart(4, "0");
}
function glyph(c: string) {
  return /[\u3099\u309a]/.test(c) ? "◌" + c : c;
}
async function copyCss() {
  try {
    await navigator.clipboard.writeText(cssExample);
    copyState.value = "done";
  } catch {
    copyState.value = "failed";
  }
}
watch(isEn, () => {
  reset();
  copyState.value = "";
});
watch([query, category], () => {
  shown.value = 60;
});
onMounted(async () => {
  document.fonts
    .load('800 48px "Nikukyu Maru"')
    .then((result) => {
      fontState.value = result.length ? "ready" : "failed";
    })
    .catch(() => {
      fontState.value = "failed";
    });
  try {
    const response = await fetch(withBase("/generated/meta.json"));
    if (!response.ok) throw new Error("metadata unavailable");
    const data = await response.json();
    characters.value =
      typeof data.characters === "string"
        ? [...data.characters].filter((c) => !/[\r\n]/.test(c))
        : data.characters;
    version.value = data.version;
  } catch {
    metadataError.value = true;
  }
});
</script>

<template>
  <a class="skip-link" href="#main">{{ t.skip }}</a>
  <header class="site-header" id="top">
    <a
      class="brand"
      :href="withBase(isEn ? '/en/' : '/')"
      :aria-label="isEn ? 'Nikukyu Maru home' : 'にくきゅう丸 トップ'"
      ><img
        :src="withBase('/favicon.svg')"
        alt=""
        width="38"
        height="38"
      /><span class="display">にくきゅう丸</span
      ><span class="brand-sub">NIKUKYU MARU</span></a
    >
    <nav :aria-label="isEn ? 'Main' : 'メインナビゲーション'">
      <a
        :href="
          page.isNotFound ? withBase(isEn ? '/en/#play' : '/#play') : '#play'
        "
        >{{ t.nav[0] }}</a
      ><a
        :href="
          page.isNotFound
            ? withBase(isEn ? '/en/#characters' : '/#characters')
            : '#characters'
        "
        >{{ t.nav[1] }}</a
      ><a
        class="nav-download"
        :href="
          page.isNotFound
            ? withBase(isEn ? '/en/#download' : '/#download')
            : '#download'
        "
        >{{ t.nav[2] }} <span aria-hidden="true">↗</span></a
      >
    </nav>
    <div class="languages" :aria-label="isEn ? 'Language' : '言語'">
      <a
        :href="withBase('/')"
        lang="ja"
        :aria-current="!isEn ? 'page' : undefined"
        >JP</a
      ><span>/</span
      ><a
        :href="withBase('/en/')"
        lang="en"
        :aria-current="isEn ? 'page' : undefined"
        >EN</a
      >
    </div>
  </header>

  <main id="main" v-if="!page.isNotFound">
    <section class="hero section-shell" :class="{ english: isEn }">
      <div class="hero-copy">
        <p class="eyebrow">
          <span class="small-paw" aria-hidden="true">&#xE000;</span> A
          CAT-INSPIRED DISPLAY FONT <span class="version">v{{ version }}</span>
        </p>
        <h1 class="display">
          <span v-for="line in t.hero" :key="line">{{ line }}</span>
        </h1>
        <p class="hero-intro">{{ t.intro }}</p>
        <a
          class="button button-red"
          :href="
            page.isNotFound ? withBase(isEn ? '/en/#play' : '/#play') : '#play'
          "
          >{{ t.try }} <span aria-hidden="true">↘</span></a
        >
        <p class="hero-footnote">
          SIL OPEN FONT LICENSE 1.1 <span>·</span> 7,516 CHARACTERS
        </p>
      </div>
      <div
        class="hero-art"
        :aria-label="
          isEn ? 'Aa, cat alphabet specimen' : '猫の英字 Aa の文字見本'
        "
      >
        <span class="art-kicker mono">TYPE SPECIMEN / No. 001</span>
        <div class="red-poster">
          <div class="poster-top">NIKUKYU<br />MARU</div>
          <span class="poster-aa display">Aa</span
          ><span class="poster-caption">まるい文字には、ねこがいる。</span>
          <div class="poster-bottom">
            <span>CAT TYPE<br />WITH A LITTLE PAW.</span
            ><span class="display">&#xE000;</span>
          </div>
        </div>
        <div class="seal">
          <span v-for="line in t.stamp" :key="line">{{ line }}</span
          ><small>OFL 1.1</small>
        </div>
        <div class="mini-tag">
          <span class="display">g</span><span>FOLLOW<br />THE TAIL.</span
          ><span aria-hidden="true">↗</span>
        </div>
      </div>
    </section>
    <div class="ribbon" aria-hidden="true">
      <span v-for="n in 3" :key="n"
        ><b v-for="word in t.ribbon" :key="word"
          >{{ word }} <i class="display">&#xE000;</i></b
        ></span
      >
    </div>

    <section id="play" class="play-section section-shell section-pad">
      <div class="section-heading">
        <div>
          <p class="eyebrow">01 / TYPE & PLAY</p>
          <h2 class="display">{{ t.playground }}</h2>
        </div>
        <p>{{ t.playDesc }}</p>
      </div>
      <div class="tester">
        <div class="tester-top">
          <div
            class="preset-group"
            :aria-label="isEn ? 'Text presets' : '文章の見本'"
          >
            <button
              v-for="(preset, i) in t.presets"
              :key="preset"
              @click="sample = t.samples[i]"
              :aria-pressed="sample === t.samples[i]"
            >
              {{ preset }}
            </button>
          </div>
          <span class="mono">{{ [...sample].length }} / 180</span>
        </div>
        <label class="sr-only" for="specimen">{{ t.input }}</label>
        <textarea
          id="specimen"
          :value="sample"
          @input="onSampleInput"
          @compositionend="onSampleInput"
          :placeholder="t.empty"
          :style="specimenStyle"
          spellcheck="false"
          :aria-describedby="missing.length ? 'missing-text' : 'private-note'"
        ></textarea>
        <p class="font-notice" role="status" v-if="fontState !== 'ready'">
          {{ fontState === "loading" ? t.loading : t.failed }}
        </p>
        <p
          id="missing-text"
          class="input-warning"
          v-if="missing.length"
          role="status"
        >
          {{ t.missing }} {{ missing.join(" ") }}
        </p>
        <div class="tester-controls">
          <label class="range-control" for="type-size"
            ><span
              >{{ t.size }} <output>{{ size }}px</output></span
            ><input
              id="type-size"
              v-model.number="size"
              type="range"
              min="32"
              max="120"
              step="1" /></label
          ><label class="range-control" for="letter-spacing"
            ><span
              >{{ t.spacing }}
              <output>{{ (spacing / 100).toFixed(2) }}em</output></span
            ><input
              id="letter-spacing"
              v-model.number="spacing"
              type="range"
              min="-3"
              max="15"
              step="1"
          /></label>
          <fieldset class="ink-control">
            <legend>{{ t.color }}</legend>
            <button
              v-for="(color, i) in inks"
              :key="color"
              :style="{ background: color }"
              :aria-label="t.colors[i]"
              :aria-pressed="ink === i"
              @click="ink = i"
            >
              <span v-if="ink === i" aria-hidden="true">✓</span>
            </button>
          </fieldset>
          <label class="alternate-control"
            ><input type="checkbox" v-model="alternates" /><span>{{
              t.alternates
            }}</span></label
          ><button class="reset-button" @click="reset">{{ t.reset }} ↺</button>
        </div>
      </div>
      <p id="private-note" class="fine-print">{{ t.privacy }}</p>
    </section>

    <section
      class="personality section-shell"
      :aria-label="isEn ? 'The details' : '文字のこだわり'"
    >
      <article v-for="(title, i) in t.features" :key="title">
        <div
          class="feature-glyph display"
          :class="'feature-' + i"
          aria-hidden="true"
        >
          {{ ["A", "g", "a"][i] }}
        </div>
        <span class="feature-number mono">0{{ i + 1 }}</span>
        <h3 class="display">{{ title }}</h3>
        <p>{{ t.featureDescriptions[i] }}</p>
      </article>
    </section>

    <section id="characters" class="glyph-section section-shell section-pad">
      <div class="section-heading">
        <div>
          <p class="eyebrow">02 / THE CHARACTER COLLECTION</p>
          <h2 class="display">{{ t.glyphTitle }}</h2>
        </div>
        <p>{{ t.glyphDesc }}</p>
      </div>
      <div class="glyph-toolbar">
        <div
          class="category-group"
          :aria-label="isEn ? 'Character category' : '文字の種類'"
        >
          <button
            v-for="(name, i) in t.categories"
            :key="name"
            :aria-pressed="category === i && !query"
            @click="
              category = i;
              query = '';
            "
          >
            {{ name }}
          </button>
        </div>
        <label class="glyph-search"
          ><span class="sr-only">{{ t.search }}</span
          ><span aria-hidden="true">⌕</span
          ><input
            v-model="query"
            type="search"
            :placeholder="t.searchPlaceholder"
        /></label>
      </div>
      <p role="status" v-if="metadataError" class="input-warning">
        {{ t.metadataFailed }}
      </p>
      <div
        class="glyph-grid"
        :class="{ 'is-loading': !characters.length && !metadataError }"
      >
        <div v-for="c in visible" :key="c" class="glyph-cell" :title="cp(c)">
          <span class="display">{{ glyph(c) }}</span
          ><small class="mono">{{ cp(c) }}</small>
        </div>
      </div>
      <p
        v-if="!visible.length && characters.length"
        role="status"
        class="empty-glyphs"
      >
        {{ t.noGlyph }}
      </p>
      <div class="glyph-bottom">
        <span class="mono" aria-live="polite"
          >{{ visible.length }} / {{ filtered.length }} {{ t.shown }}</span
        ><button
          v-if="filtered.length > shown"
          class="text-link"
          @click="shown += 60"
        >
          {{ t.more }} +</button
        ><a class="text-link" :href="repo + '/blob/main/outputs/CHARACTERS.md'"
          >{{ t.allChars }} ↗</a
        >
      </div>
    </section>

    <section id="in-use" class="use-section section-pad">
      <div class="section-shell">
        <div class="section-heading">
          <div>
            <p class="eyebrow">03 / OUT IN THE WORLD</p>
            <h2 class="display">{{ t.usesTitle }}</h2>
          </div>
          <p>{{ t.usesDesc }}</p>
        </div>
        <div class="use-grid">
          <article class="use-card menu-card">
            <p class="mono">{{ t.useLabels[0] }}</p>
            <div class="menu-paper">
              <div class="display menu-name">ねこの<br />喫茶室</div>
              <span class="menu-line"></span
              ><span class="display menu-coffee">Coffee<br />& cookies</span
              ><span class="mono">OPEN 11:00 — 18:00</span
              ><span class="display menu-paw" aria-hidden="true">&#xE000;</span>
            </div>
          </article>
          <article class="use-card package-card">
            <p class="mono">{{ t.useLabels[1] }}</p>
            <div class="package-wrap">
              <div class="package-label">
                <span class="mono">BAKED WITH LOVE</span
                ><span class="display">おやつの<br />じかん。</span
                ><span class="display package-a" aria-hidden="true">a</span
                ><small>BUTTER COOKIES / 6 PIECES</small>
              </div>
            </div>
          </article>
          <article class="use-card poster-card">
            <p class="mono">{{ t.useLabels[2] }}</p>
            <div class="event-paper">
              <span class="mono">A LITTLE WEEKEND MARKET</span>
              <div class="display">HELLO,<br />NEKO.</div>
              <span class="event-cat display" aria-hidden="true">&#xE001;</span
              ><span class="mono">SUN 10:00 — 16:00</span>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section id="story" class="story-section section-shell section-pad">
      <div class="story-image">
        <img
          :src="withBase('/generated/concept.png')"
          :alt="
            isEn
              ? 'The original image-generated cat alphabet concept'
              : '画像生成による猫アルファベットのコンセプト見本'
          "
          loading="lazy"
          width="1536"
          height="1024"
        /><span class="mono">FROM CONCEPT TO CURVES / 0.105</span>
      </div>
      <div class="story-copy">
        <p class="eyebrow">{{ t.storyLabel }}</p>
        <h2 class="display">{{ t.storyTitle }}</h2>
        <p>{{ t.story }}</p>
        <a class="text-link" :href="withBase('/generated/comparison.png')"
          >{{ t.storyLink }} ↗</a
        >
      </div>
    </section>

    <section id="download" class="download-section section-pad">
      <div class="section-shell">
        <div class="download-heading">
          <p class="eyebrow">04 / TAKE A LITTLE CAT HOME</p>
          <h2 class="display">{{ t.downloadTitle }}</h2>
          <p>{{ t.downloadDesc }}</p>
          <span class="download-paw display" aria-hidden="true">&#xE000;</span>
        </div>
        <div class="download-grid">
          <a
            v-for="(format, i) in ['TTF', 'WOFF2', 'SOURCE']"
            :key="format"
            :href="
              release +
              (i === 0
                ? 'NikukyuMaru-Regular.ttf'
                : i === 1
                  ? 'NikukyuMaru-Regular.woff2'
                  : `NikukyuMaru-${version}.zip`)
            "
            class="download-card"
            ><span class="mono">{{ t.formats[i] }}</span
            ><strong>{{ format }} <span aria-hidden="true">↗</span></strong>
            <p>{{ t.formatDesc[i] }}</p>
            <small class="mono"
              >v{{ version }} / {{ i === 2 ? "ZIP" : format }}</small
            ></a
          >
        </div>
      </div>
    </section>

    <section id="faq" class="usage-section section-shell section-pad">
      <div>
        <p class="eyebrow">GOOD TO KNOW</p>
        <h2 class="display">{{ t.howTitle }}</h2>
        <a class="text-link" :href="repo + '/blob/main/OFL.txt'"
          >{{ t.license }} ↗</a
        >
      </div>
      <div class="faq-list">
        <details v-for="(faq, i) in t.faqs" :key="faq[0]">
          <summary>{{ faq[0] }} <span aria-hidden="true">+</span></summary>
          <p>{{ faq[1] }}</p>
          <div v-if="i === 3" class="css-example">
            <pre><code>{{ cssExample }}</code></pre>
            <button @click="copyCss">
              {{ copyState === "done" ? t.copied : t.copyCss }}
            </button>
            <p v-if="copyState === 'failed'" role="status">{{ t.copyFail }}</p>
            <span class="sr-only" role="status">{{
              copyState === "done" ? t.copied : ""
            }}</span>
          </div>
        </details>
      </div>
    </section>
  </main>
  <main v-else id="main" class="not-found section-shell">
    <span class="display">&#xE001;</span>
    <h1 class="display">{{ t.unavailable }}</h1>
    <p>{{ t.errorText }}</p>
    <a class="button button-red" :href="withBase(isEn ? '/en/' : '/')">{{
      t.back
    }}</a>
  </main>
  <footer class="site-footer section-shell">
    <div>
      <a class="display footer-brand" :href="withBase(isEn ? '/en/' : '/')"
        >にくきゅう丸</a
      >
      <p>{{ t.footer }}</p>
    </div>
    <div class="footer-links">
      <a :href="repo">GitHub ↗</a
      ><a :href="repo + '/blob/main/OFL.txt'">SIL OFL 1.1 ↗</a
      ><a
        :href="
          repo + (isEn ? '/blob/main/README.md' : '/blob/main/README.ja.md')
        "
        >{{ t.source }} ↗</a
      ><span class="mono"
        >© 2026 NIKUKYU MARU PROJECT<br />BASED ON MOCHIY POP ONE & ZEN MARU
        GOTHIC</span
      >
    </div>
    <a class="back-top" href="#top" :aria-label="t.back">↑</a>
  </footer>
</template>
