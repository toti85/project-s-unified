# SHAYANWATERS.COM — DESIGN KONCEPCÍÓ
**Dátum:** 2026-06-03  
**Készítette:** Cline (autonomous)  
**Státusz:** FÁZIS 2 — Várva Toti review-ra

---

## 1. VIZUÁLIS KONCEPCÍÓ

### 1.1 Mood & Brand Identity

**"A Kárpátok tiszta ereje"** — a víz útja a hegységtől a palackig.

A design a kárpátaljai természet erejét és tisztaságát tükrözi. Nem egy klasszikus "víz cég" weboldal, hanem egy élmény, amely átadja a Kárpátok hangulatát: friss, tiszta, erős, természetes.

**Kulcsszavak:** tiszta, természetes, prémium, friss, erős, hegyi

### 1.2 Color Palette

| Szín | Hex | Használat |
|------|-----|-----------|
| `Carpathian Deep Green` | `#1A3C34` | Elsődleges, header, footer, sötét háttérek |
| `Water Cyan` | `#00B4D8` | CTA gombok, linkek, accent |
| `Glacier Blue` | `#90E0EF` | Sekundér accent, hover állapotok |
| `Spring White` | `#F8F9FA` | Fő háttér |
| `Pure White` | `#FFFFFF` | Kártyák, szekciók |
| `Mountain Rock` | `#2B2D42` | Szöveg, sötét elemek |
| `Fog Gray` | `#6C757D` | Sekundér szöveg |
| `Gold Award` | `#D4A843` | Díjak, elismerések accent |

**Sötét téma paletta:**
| Szín | Hex | Használat |
|------|-----|-----------|
| `Midnight Mountain` | `#0D1B18` | Fő háttér |
| `Deep Forest` | `#1A3C34` | Kártyák, szekciók |
| `Water Cyan` | `#00B4D8` | Accent (megmarad) |
| `Glacier Blue` | `#90E0EF` | Sekundér accent |
| `Fog White` | `#E8E8E8` | Szöveg |

### 1.3 Typography

**Fő betűtípus:** `Inter` (Google Fonts)
- Modern, tiszta, jól olvasható ukrán karakterekkel
- Weightek: 300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold), 800 (extrabold)
- CDN-ről betöltve

**Címsor betűtípus:** `Playfair Display` (Google Fonts)
- Elegáns serif a hero és szekció címekhez
- Weightek: 400, 500, 600, 700
- A kárpátaljai prémium hangulatot adja

**Betűméretek (mobile-first):**
| Elem | Mobile | Desktop |
|------|--------|---------|
| H1 (Hero) | 2.5rem | 4.5rem |
| H2 (Szekció) | 1.75rem | 3rem |
| H3 (Alcím) | 1.25rem | 1.5rem |
| Body | 1rem | 1.125rem |
| Small | 0.875rem | 0.875rem |

---

## 2. LAYOUT JAVASLAT

### 2.1 Mobile-First Approach

A design **mobile-first** — először mobile layout tervezve, aztán breakpoint-okkal felfelé skálázva.

**Breakpoint-ek:**
- `sm`: 576px (nagy mobilek)
- `md`: 768px (tablet)
- `lg`: 992px (kis desktop)
- `xl`: 1200px (nagy desktop)
- `xxl`: 1400px (ultra-wide)

### 2.2 Hero Szekció — VIDEO BACKGROUND

```
┌─────────────────────────────────────────────────┐
│  [FULL-SCREEN VIDEO: main.mp4/webm]             │
│                                                  │
│  [Overlay: gradient dark → transparent]          │
│                                                  │
│  [Header: transparent → solid on scroll]         │
│  ┌──────────────────────────────────────────┐   │
│  │  LOGO    Főoldal  Termékek  Rólunk  Kontakt│ │
│  └──────────────────────────────────────────┘   │
│                                                  │
│                    [Darken]                       │
│           ТОВ ВАП "ШАЯНИ"                        │
│                                                  │
│    Провідне підприємство Закарпаття              │
│    з видобутку мінеральної води                  │
│                                                  │
│         [Замовити]  [Дізнатись більше]           │
│                                                  │
│                    [Scroll indicator ↓]          │
└─────────────────────────────────────────────────┘
```

**Video:** Az eredeti `main.mp4` / `main.webm` használata full-screen backgroundként.
- Autoplay, muted, loop
- Fallback kép ha video nem tölthető be
- Gradient overlay a szöveg olvashatósága érdekében
- Mobile-on: fallback kép (video data consumption)

### 2.3 Navigation

**Desktop:**
- Transparent header a hero felett
- Solid background (Deep Green) scroll után
- Logo balra, menü középen, CTA jobbra
- Smooth scroll anchor linkek

**Mobile:**
- Hamburger menu (jobb felső sarok)
- Full-screen overlay menu
- Logo balra, hamburger jobbra
- Menu animáció: slide from right

### 2.4 Oldalstruktúra (index.html)

```
1. HERO (video background)
2. TERMÉK MÁRKÁK (3 kártya — modern grid)
3. "A VÍZ ÚTA" (storytelling — parallax scroll)
4. ELŐNYÖK (3 oszlop — ikon + szöveg)
5. TERMÉK RÁKÖSZÖNTŐ (split layout)
6. SZOCIAL MEDIA GALÉRIA (masonry grid)
7. DOSTAVKA (térkép + szöveg)
8. FOOTER (5 oszlop)
```

### 2.5 Termék Oldal (products.html)

Modern **asymmetric grid** a klasszikus 3 oszlop helyett:

```
┌──────────────┬───────────────┬──────────────┐
│              │               │              │
│  Шаянська    │   Йодіс       │  Сила        │
│  (nagy)      │  Карпат       │  Карпат      │
│              │               │              │
│  [kép]       │  [kép]        │  [kép]       │
│              │               │              │
│  Gazovana    │  Jódos        │  5L családi  │
│  klasszikus  │  víz          │  formátum    │
│              │               │              │
│  [Részletek] │  [Részletek]  │  [Részletek] │
└──────────────┴───────────────┴──────────────┘
```

### 2.6 Termék Detail (shayanska.html stb.)

```
┌─────────────────────────────────────────────────┐
│  [Hero: termék kép — nagy, központi]            │
│                                                  │
│  Шаянська                                        │
│  Лікувально-столова мінеральна вода              │
│                                                  │
│  [TAB: Газована | Слабогазована | Негазована]   │
│                                                  │
│  ┌────────────┬──────────────────────────────┐  │
│  │            │  Mineral összetétel:          │  │
│  │ [termék    │  HCO3: 1000-2200 mg/l         │  │
│  │  kép]      │  SO4: < 120 mg/l              │  │
│  │            │  Cl: < 200 mg/l               │  │
│  │            │  ...                          │  │
│  └────────────┴──────────────────────────────┘  │
│                                                  │
│  Варіанти фасування:                             │
│  ┌──────┐  ┌──────┐  ┌──────┐                   │
│  │ 1,5л │  │ 0,5л │  │ 0,5л │                   │
│  │ [kép]│  │ [kép]│  │ скло │                   │
│  └──────┘  └──────┘  └──────┘                   │
│                                                  │
│  [Різаєtkes szöveg a víz hatásairól]             │
└─────────────────────────────────────────────────┘
```

### 2.7 "A VÍZ ÚTA" — Storytelling Szekció

Ez a legbátorabb elem. Parallax scroll-lal a víz útja a Kárpátoktól a palackig:

```
┌─────────────────────────────────────────────────┐
│                                                  │
│  [Parallax: Kárpátok hegység kép]               │
│  "З глибини 250 метрів"                         │
│                                                  │
│  ──── scroll ────                               │
│                                                  │
│  [Parallax: földrétegek, ásványok]              │
│  "Тисячі років очищення"                        │
│                                                  │
│  ──── scroll ────                               │
│                                                  │
│  [Parallax: gyár, technológia]                  │
│  "Сучасні технології розливу"                   │
│                                                  │
│  ──── scroll ────                               │
│                                                  │
│  [Parallax: palack, termék]                     │
│  "Від джерела до вашого столу"                  │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## 3. ANIMÁCIÓK / INTERAKCIÓK

### 3.1 Külső Library: AOS (Animate on Scroll)

- **CDN-ről:** `https://unpkg.com/aos@2.3.1/dist/aos.css`
- Lightweight (~14KB), modern, jól dokumentált
- WOW.js helyére (WOW.js elavult, már nem karbantartott)

### 3.2 Animációk Listája

| Szekció | Animáció | Trigger |
|---------|----------|---------|
| Hero szöveg | Fade up + delay | Page load |
| CTA gombok | Fade up + delay | Page load |
| Termék kártyák | Fade up + stagger | Scroll into view |
| "A víz útja" | Parallax + fade | Scroll position |
| Előnyök ikonok | Scale in + rotate | Scroll into view |
| Storytelling | Parallax layers | Scroll position |
| Footer | Fade up | Scroll into view |
| Dark mode toggle | Smooth transition | Click |

### 3.3 Interakciók

- **Smooth scroll:** Natív CSS `scroll-behavior: smooth`
- **Header:** Transparent → solid on scroll (JS)
- **Dark mode:** Toggle + `prefers-color-scheme` auto-detect
- **Tab switching:** Smooth fade between product variants
- **Image hover:** Scale + shadow on product cards
- **Mobile menu:** Slide from right with overlay

---

## 4. TECH STACK

### 4.1 Alap

| Komponens | Megoldás | Indok |
|-----------|----------|-------|
| HTML | Tiszta HTML5 | Statikus, gyors, egyszerű deploy |
| CSS | Custom CSS + CSS Variables | Nincs framework overhead |
| JS | Natív ES6+ JavaScript | jQuery NEM kell |
| Font | Google Fonts (Inter + Playfair Display) | CDN, gyors, jól támogatott |
| Ikonok | Lucide Icons CDN | Modern, lightweight, SVG-based |

### 4.2 Külső Library-k (CDN)

| Library | Cél | Méret |
|---------|-----|-------|
| AOS 2.3.1 | Scroll animációk | ~14KB |
| Lucide Icons | Modern ikonok | ~5KB (használt ikonok) |

**NEM használunk:**
- ❌ jQuery (natív JS)
- ❌ Bootstrap (custom CSS grid)
- ❌ Tailwind (overkill ehhez a projekthez)
- ❌ WOW.js (elavult)
- ❌ animate.css (AOS helyett)

### 4.3 CSS Variables (Design Tokens)

```css
:root {
  /* Colors */
  --color-primary: #1A3C34;
  --color-accent: #00B4D8;
  --color-accent-light: #90E0EF;
  --color-bg: #F8F9FA;
  --color-surface: #FFFFFF;
  --color-text: #2B2D42;
  --color-text-secondary: #6C757D;
  --color-gold: #D4A843;
  
  /* Typography */
  --font-body: 'Inter', sans-serif;
  --font-heading: 'Playfair Display', serif;
  
  /* Spacing */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 2rem;
  --space-xl: 4rem;
  --space-xxl: 8rem;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-xl: 2rem;
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 300ms ease;
  --transition-slow: 500ms ease;
}

/* Dark mode */
[data-theme="dark"] {
  --color-bg: #0D1B18;
  --color-surface: #1A3C34;
  --color-text: #E8E8E8;
  --color-text-secondary: #B0B0B0;
}
```

---

## 5. CONTACT FORM — JAVASLAT

### 5.1 Ajánlott: Formspree.io

| Kritérium | Formspree | PHP mail.php |
|-----------|-----------|--------------|
| Statikus hosting | ✅ Igen | ❌ Nem |
| HTTPS | ✅ Beépített | ❌ Függ a szervertől |
| Spam protection | ✅ Akismet integráció | ❌ Manuális |
| HTTPS | ✅ | ❌ Függ a szervertől |
| Kártya | ✅ Ingyenes: 50/hó | ✅ Ingyenes |
| Karbantartás | ✅ Nulla | ❌ PHP frissítések |
| GDPR | ✅ Beépített | ❌ Manuális |

**Indok:** A redesign statikus HTML/CSS/JS, így Formspree a legtermészetesebb választás. Nincs szükség PHP szervertre, és a GDPR compliance beépített.

**Alternatíva:** Ha Formspree ingyenes limitet túllépnének, akkor Getform.io vagy EmailJS.

---

## 6. NYELVKAPCSOLÓ — STRUKTÚRA

### 6.1 Jelenlegi: Csak Ukrán

```html
<!-- Minden szöveges elem data-i18n attribútummal -->
<h1 data-i18n="hero.title">ТОВ ВАП "ШАЯНИ"</h1>
<p data-i18n="hero.subtitle">Провідне підприємство Закарпаття</p>
```

### 6.2 Nyelvi kapcsoló

```
┌─────────────────┐
│  🇺🇦 Укр  │  🇬🇧 Eng [SOON]  │
└─────────────────┘
```

- "Уkr" aktív (klikkelhető, de most semmit nem csinál — active state)
- "Eng" szürke, "Coming soon" tooltip, nem klikkelhető
- Későbbi bővítés: `js/translations/uk.json`, `js/translations/en.json`

### 6.3 Későbbi multilingual struktúra

```
js/
  i18n.js              — Nyelvkezelő modul
  translations/
    uk.json            — Ukrán fordítások
    en.json            — Angol fordítások
```

---

## 7. MOCKUP SZEKCIÓK — SZÖVEGES LEÍRÁS

### 7.1 Hero Szekció

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  [FULL-SCREEN VIDEO BACKGROUND]                          │
│  (main.mp4 / main.webm, autoplay muted loop)             │
│                                                          │
│  [DARK GRADIENT OVERLAY: rgba(26,60,52,0.7)]             │
│                                                          │
│                    [Header — transparent]                 │
│  [LOGO]        Főoldal  Termékek  Rólunk  Kontakt        │
│                                                          │
│                                                          │
│         ТОВ ВАП "ШАЯНИ"                                  │
│         (Playfair Display, 4.5rem, white)                │
│                                                          │
│    Провідне підприємство Закарпаття                      │
│    з видобутку, розливу і дистрибуції                    │
│    природної мінеральної води                            │
│    (Inter, 1.25rem, white, opacity 0.9)                  │
│                                                          │
│    ТМ "Шаянська"  │  ТМ "Сила Карпат"  │  ТМ "Йодіс"    │
│    (Water Cyan, underline on hover)                      │
│                                                          │
│         [Замовити]        [Дізнатись більше]             │
│         (filled)          (outline)                      │
│                                                          │
│                                                          │
│                     [animated scroll indicator ↓]        │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 7.2 Termék Márkák Szekció

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                   Продукція                              │
│                   (Playfair Display, 3rem)               │
│                                                          │
│    Три унікальні мінеральні води                         │
│    з надр Карпат                                         │
│                                                          │
│    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│    │              │  │              │  │              │ │
│    │  [kép]       │  │  [kép]       │  │  [kép]       │ │
│    │  Шаянська    │  │  Йодіс       │  │  Сила        │ │
│    │              │  │  Карпат      │  │  Карпат      │ │
│    │              │  │              │  │              │ │
│    │  Лікувально- │  │  Йодована    │  │  Помірний    │ │
│    │  столова     │  │  мінеральна  │  │  мінеральний │ │
│    │              │  │              │  │              │ │
│    │  [Детальніше→]│  │  [Детальніше→]│  │  [Детальніше→]│ │
│    └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 7.3 "A VÍZ ÚTA" Storytelling Szekció

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  [PARALLAX LAYER 1: Kárpátok hegység]                   │
│                                                          │
│           З глибини 250 метрів                          │
│           (white, large, bold)                           │
│                                                          │
│  [PARALLAX LAYER 2: földrétegek, ásványok]              │
│                                                          │
│           Тисячі років очищення                          │
│                                                          │
│  [PARALLAX LAYER 3: gyár, technológia]                  │
│                                                          │
│           Сучасні технології розливу                     │
│                                                          │
│  [PARALLAX LAYER 4: palack, termék]                     │
│                                                          │
│           Від джерела до вашого столу                    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 8. SEO & META

### 8.1 Minden oldalon:
- ✅ `<html lang="uk">`
- ✅ `<meta name="description">` (frissített, 0.33L nélkül)
- ✅ `<meta name="keywords">`
- ✅ Open Graph (og:title, og:description, og:image, og:url, og:type)
- ✅ Twitter Card (summary_large_image)
- ✅ Canonical URL
- ✅ Schema.org structured data (Organization, Product, LocalBusiness)
- ✅ Robots meta tag

### 8.2 Performance
- ✅ Lazy loading képek (`loading="lazy"`)
- ✅ Modern képformátum (WebP fallback PNG-val)
- ✅ Preconnect Google Fonts-hoz
- ✅ Preload hero video
- ✅ Minimal JS (nincs jQuery)
- ✅ CSS critical path inlined

---

## 9. DARK MODE

### 9.1 Implementáció
- CSS variables-alapú (lásd 4.3)
- Toggle gomb a header-ben (🌙/☀️ ikon)
- Auto-detect: `prefers-color-scheme: dark`
- localStorage-ban mentve a választás
- Smooth transition (300ms) a váltáskor

### 9.2 Toggle pozíció
```
[LOGO]  [Menu...]  [🌙 Dark Mode]  [Уkr | Eng]
```

---

## 10. FÁJLSTRUKTÚRA (new/)

```
new/
├── index.html              — Főoldal
├── products.html           — Termékek áttekintés
├── product-shayanska.html  — Шаянська detail
├── product-yodis.html      — Йодіс Карпат detail
├── product-syla.html       — Сила Карпат detail
├── about.html              — Rólunk (egységes oldal)
├── contacts.html           — Kapcsolat
├── cookie.html             — Cookie politika
├── css/
│   ├── style.css           — Fő stylesheet (CSS variables)
│   └── animations.css      — AOS customizációk
├── js/
│   ├── main.js             — Navigation, dark mode, smooth scroll
│   └── i18n.js             — Nyelvkezelő (strukturálva)
├── img/                    — Megőrzött képek (0.33L KIVÉVE)
│   ├── shayanska.png
│   ├── syla-karpat.png
│   ├── yodis.png
│   ├── history.jpg
│   ├── vyrobnyctvo.jpg
│   ├── map.png
│   ├── test.svg
│   ├── happy.svg
│   ├── water.svg
│   ├── water/              — Termék képek (0.33L KIVÉVE)
│   ├── sertificate/        — Díjak, tanúsítványok
│   └── facebook/           — Social media képek
├── icons/
│   ├── logo.png
│   └── favicon.png
├── video/
│   ├── main.mp4
│   └── main.webm
├── AUDIT_20260603.md
├── DESIGN_CONCEPT_20260603.md
├── robots.txt
└── sitemap.xml
```

---

## ÖSSZEGZÉS

| Elem | Megoldás |
|------|----------|
| Vizuális irány | Bold, prémium, kárpátaljai természet |
| Color palette | Deep Green + Water Cyan + White |
| Typography | Inter (body) + Playfair Display (headings) |
| Layout | Mobile-first, asymmetric grids |
| Hero | Full-screen video background |
| Storytelling | Parallax scroll "A víz útja" |
| Animációk | AOS library, smooth transitions |
| Dark mode | CSS variables, toggle + auto-detect |
| Nyelv | Ukrán alap, strukturálva multilingual-re |
| Contact form | Formspree.io |
| jQuery | NEM — natív ES6+ JS |
| Bootstrap | NEM — custom CSS |
| Performance | Lighthouse 90+ cél |
| SEO | OG, Twitter, Schema.org, canonical |

---
*Vége a DESIGN KONCEPCÍÓ dokumentumnak. Várakozás Toti review-ra a FÁZIS 3 (Implementáció) elindításához.*