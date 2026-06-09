# BOLD VARIANT — INDEX.HTML RIPOORT
**Dátum:** 2026.06.03.
**Verzió:** new_bold/ (alternatív design a new/ mellett)

---

## 1. VÁLASZTOTT OPCIÓK

### Constraint 1 — HERO: C) OVERSIZED TYPOGRAPHY DOMINANCE
**Indok:** A "ШАЯНИ" szöveg a viewport ~70%-át elfoglalja Anton betűtípussal, tracking: -8px. Ez a legmerészebb opció, és leginkább illeszkedik a brutalista koncepcióhoz. A cégnevet nem "címnek" használjuk — a cégnevvel KÉPEZÜNK.

### Constraint 2 — TERMÉK SZEKCIÓ: Asymmetric Grid
Domináns Шаянська (grid: 1.2fr) + két kisebb termék (grid: 0.8fr, egymás alatt). NEM szimmetrikus 3-oszlopos.

### Constraint 3 — SZÍNEK: A) MÉLY SÖTÉT + ÉLES ACCENT
- Háttér: `#0A0F0E` (almost-black, zöldes árnyalat)
- Szöveg: `#F0F0F0` (tört fehér)
- Accent: `#00FFE5` (elektromos cián)
- Indok: A sötét háttér a 250 méteres mélységet reprezentálja. Az elektromos cián a mineralizált víz "fénye" a sötétségben.

### Constraint 4 — TYPOGRAPHIA: Anton
Egyetlen weight, extrabold condensed sans-serif. Tracking: -8px hero (nyomó hatás), +4px navigáció (ellentét). Nem "víz-font" — poszter-font.

### Constraint 5 — HERO VIDEO: Autoplay + JS fallback
Video fut desktop-on. Mobile-on JS detektálja (userAgent + navigator.saveData) → fallback kép. NEM CSS media query.

### Constraint 6 — HERO INTERAKCIÓ: Letter-by-letter + vízszint-vonal
- "ШАЯНИ" betűi egyenként jelennek meg (staggered animation, 120ms delay)
- SVG vízszint-vonal folyamatosan pulzál a hero alján
- Cursor glow effect (desktop-only, `pointer: fine` media query)

---

## 2. TECH STACK

| Komponens | new/ | new_bold/ |
|-----------|------|-----------|
| HTML5 | ✅ | ✅ |
| CSS Variables | ✅ | ✅ (sötét paletta) |
| Google Fonts | Inter + Playfair Display | Inter + **Anton** |
| AOS animációk | ✅ | ✅ (korlátozott, csak fade-up) |
| Custom animációk | ✅ | ✅ (letter reveal, water pulse, cursor glow) |
| JS | ES6+ | ES6+ (ugyanaz + letter split + parallax) |
| Video | ✅ | ✅ (JS fallback detektálás) |

---

## 3. HOGYAN TÉR EL A new/ VERZIÓTÓL

| Szempont | new/ | new_bold/ |
|----------|------|-----------|
| **Háttér** | Fehér (#FFFFFF) | Almost-black (#0A0F0E) VÉGIG |
| **Hero** | Középre rendezett, klasszikus stack | Oversized "ШАЯНИ" + meta info alul |
| **Tipográfia** | Playfair Display (serif) + Inter | Anton (display) + Inter |
| **Termék grid** | 3 egyforma kártya | 1 domináns + 2 kisebb (aszimmetrikus) |
| **Accent szín** | #00B4D8 (klasszikus víz-kék) | #00FFE5 (elektromos cián) |
| **Interakciók** | AOS fade-be-everywhere | Letter reveal + cursor glow + parallax |
| **Footer** | 5 oszlopos klasszikus | 4 oszlopos, minimal |
| **Hangulat** | "Friss és tiszta" | "Brutalista mélység" |

---

## 4. TUDATOS DESIGN-DÖNTÉSEK

### A "mélység" narratíva végigkísér
- Sötét háttér VÉGIG — nincs "sötét fent, világos lent" váltás
- Story szekcióban a "250м", "∞", "1979" számok cián színnel, Anton-ban
- Képek alacsony opacity-vel (0.12-0.25) — soha nem dominálnak a szöveg felett

### Aszimmetria legalább 3 szekcióban
1. **Hero:** "ШАЯНИ" balra, "250" jobbra alul
2. **Termékek:** 1.2fr / 0.8fr grid (NEM 1fr 1fr 1fr)
3. **Delivery:** 0.7fr / 1.3fr split (kép balra, szöveg jobbra)
4. **Social:** 1fr / 1.5fr (szöveg balra, grid jobbra)

### Accent kiszámítottan
- CIÁN: linkek hover, CTA gombok, kulcs számok (250, ∞, 1979)
- NEM cián: minden más gomb, szöveg, border

### NEM téttem meg
- ❌ Semmilyen középre rendezés (kivéve hero title)
- ❌ Pasztel színek bárhol
- ❌ Fade-be-everywhere AOS (csak fade-up, korlátozott)
- ❌ Klasszikus 5-oszlopos footer
- ❌ "Safe" termék kártyák

---

## 5. LIMITÁCIÓK

### Mi NEM működhet még
1. **Light mode** — a CSS-ben nincs `.light-mode` implementálva (a JS toggle-ol, de a CSS változatok hiányoznak). A bold variant dark-first design.
2. **Termék detail oldalak** — csak index.html kész. A product-*.html, about.html, contacts.html, cookie.html még hiányoznak.
3. **Hero fallback kép** — `img/hero-fallback.jpg` placeholder, az eredeti ZIP-ben nincs megfelelő kép.
4. **SVG vízszint-vonal** — egyszerű path, nem komplex animáció. Továbbfejleszthető.

### Ismert korlátok
- Video autoplay: egyes böngészők blokkolhatják (Chrome policy). A `muted` attribútum segíti, de nem garantált.
- Anton font: cirill támogatás korlátozott lehet (Google Fonts tesztelés szükséges).
- Cursor glow: csak desktop-on (`pointer: fine`), mobile-on nincs.

---

## 6. FÁJLSTRUKTÚRA

```
new_bold/
├── index.html          ← KÉSZ
├── css/
│   ├── style.css       ← KÉSZ (~10KB)
│   └── animations.css  ← KÉSZ (~3KB)
├── js/
│   └── main.js         ← KÉSZ (~5KB)
├── img/                ← másolva new/-ből (0.33L nélkül)
├── icons/              ← másolva new/-ből
└── video/              ← másolva new/-ből
```

---

## 7. ÖSSZEGZÉS

A bold variant egy radikálisan más vizuális irány, ami:
- ✅ Nem hasonlít semmilyen vízmárka weboldalra
- ✅ Brutalista + mélység narratíva végigkísér
- ✅ Aszimmetrikus layoutok (NEM szimmetrikus grid)
- ✅ Anton tipográfia mint vizuális elem
- ✅ Elektromos cián accent kiszámítottan
- ✅ Letter-by-letter + vízszint-vonal interakció
- ✅ 0.33L NINCS
- ✅ Ukrán nyelv
- ✅ Mobile responsive

**Következő lépés:** Toti review → zöld lámpa → termék detail oldalak + belső oldalak new_bold/ alatt.