import { defineConfig } from 'vitepress'

const japaneseNav = [
  { text: 'ためす', link: '/#play' },
  { text: '文字見本', link: '/#characters' },
  { text: 'つかう', link: '/#download' },
  { text: 'English', link: '/en/' },
]

const englishNav = [
  { text: 'Try it', link: '/en/#play' },
  { text: 'Characters', link: '/en/#characters' },
  { text: 'Download', link: '/en/#download' },
  { text: '日本語', link: '/' },
]

const japaneseSidebar = [
  { text: 'トップ', link: '/' },
  { text: 'ためす', link: '/#play' },
  { text: '文字見本', link: '/#characters' },
  { text: 'ダウンロード', link: '/#download' },
]

const englishSidebar = [
  { text: 'Home', link: '/en/' },
  { text: 'Try it', link: '/en/#play' },
  { text: 'Characters', link: '/en/#characters' },
  { text: 'Download', link: '/en/#download' },
]

const siteUrl = 'https://sunwood-ai-labs.github.io/nikukyu-maru-font/'
const ogImage = `${siteUrl}generated/comparison.png`

export default defineConfig({
  base: '/nikukyu-maru-font/',
  title: 'にくきゅう丸',
  titleTemplate: false,
  description: '小さな猫耳とまあるい輪郭の、日本語対応ディスプレイフォント。',
  lang: 'ja',
  head: [
    ['link', { rel: 'icon', href: `${siteUrl}favicon.svg`, type: 'image/svg+xml' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:image', content: ogImage }],
    ['meta', { property: 'og:image:alt', content: 'にくきゅう丸の生成見本と実フォントの比較' }],
    ['meta', { name: 'twitter:card', content: 'summary_large_image' }],
    ['meta', { name: 'twitter:image', content: ogImage }],
  ],
  locales: {
    root: {
      label: '日本語',
      lang: 'ja',
      head: [
        ['link', { rel: 'canonical', href: siteUrl }],
        ['meta', { property: 'og:url', content: siteUrl }],
        ['meta', { property: 'og:title', content: 'にくきゅう丸 — Nikukyu Maru' }],
        ['meta', { property: 'og:description', content: '小さな猫耳とまあるい輪郭の、日本語対応ディスプレイフォント。' }],
        ['meta', { property: 'og:locale', content: 'ja_JP' }],
        ['meta', { name: 'twitter:title', content: 'にくきゅう丸 — Nikukyu Maru' }],
        ['meta', { name: 'twitter:description', content: '小さな猫耳とまあるい輪郭の、日本語対応ディスプレイフォント。' }],
      ],
    },
    en: {
      label: 'English',
      lang: 'en',
      title: 'Nikukyu Maru',
      titleTemplate: false,
      description: 'A Japanese display font with round shapes, little ears, and a curious tail.',
      head: [
        ['link', { rel: 'canonical', href: `${siteUrl}en/` }],
        ['meta', { property: 'og:url', content: `${siteUrl}en/` }],
        ['meta', { property: 'og:title', content: 'Nikukyu Maru — A little type. A lot of cat.' }],
        ['meta', { property: 'og:description', content: 'A Japanese display font with round shapes, little ears, and a curious tail.' }],
        ['meta', { property: 'og:locale', content: 'en_US' }],
        ['meta', { name: 'twitter:title', content: 'Nikukyu Maru — A little type. A lot of cat.' }],
        ['meta', { name: 'twitter:description', content: 'A Japanese display font with round shapes, little ears, and a curious tail.' }],
      ],
    },
  },
  themeConfig: {
    nav: japaneseNav,
    sidebar: japaneseSidebar,
    locales: {
      root: {
        label: '日本語',
        lang: 'ja',
        nav: japaneseNav,
        sidebar: japaneseSidebar,
      },
      en: {
        label: 'English',
        lang: 'en',
        nav: englishNav,
        sidebar: englishSidebar,
      },
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Sunwood-ai-labs/nikukyu-maru-font' },
    ],
  },
})
