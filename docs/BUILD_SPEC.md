# CSV Rescue — Complete Build Specification (for Cursor)

> **Audience:** Cursor Pro (Agent mode). **Goal:** build the full product from an empty folder to a deployed website, with every feature working end-to-end.
> **Read this entire file before writing code.** Where this file says MUST, it is a hard requirement. Where it says SHOULD, follow it unless it conflicts with a MUST.
> **Visual reference:** `docs/design-reference/dashboard-reference.png` (attach it in Cursor chat with `@dashboard-reference.png` at the start of every UI phase). The UI MUST look like that image — see Section 2.

---

## 0. How to use this file in Cursor

1. Create an empty repo folder `csv-rescue/`. Put this file at `docs/BUILD_SPEC.md` and the reference image at `docs/design-reference/dashboard-reference.png`.
2. Create `.cursor/rules/csv-rescue.mdc` with the content in **Appendix A**.
3. Open the folder in Cursor, start a new Agent chat and paste:
   > Read `@docs/BUILD_SPEC.md` fully and `@docs/design-reference/dashboard-reference.png`. Then execute **Phase 0** from Section 17. Do not start Phase 1 until Phase 0's acceptance criteria pass. After each phase: run the tests, fix failures, and commit.
4. Repeat for each phase, one phase per chat. Each phase in Section 17 has a ready-to-paste prompt, deliverables and acceptance criteria.
5. If something in this file is ambiguous, choose the simplest option that satisfies the acceptance criteria and write the decision in `docs/DECISIONS.md`.

**Non-negotiables (summary):**
- The core product is **100% deterministic** (Pandas/NumPy/RapidFuzz). It works with **no API key and no internet**.
- The LLM layer is **optional**. Provider order: **Groq → Ollama → built-in templates**. The app never breaks if both LLMs are down.
- The UI is a **soft 3D "clay" pastel-purple dashboard** matching the reference image. No default shadcn/Material/Bootstrap look.
- Nothing is changed silently. Every change is previewed, explained, reviewable, undoable, and re-verified.

---

## Table of contents

1. Product overview
2. Design system (UI must match the reference image)
3. Screens and behaviour
4. Architecture, tech stack, repo layout
5. Session, data model, and the undo engine
6. Detection engine (exact algorithms)
7. Cleaning proposals and actions
8. Rules engine (cross-column validation)
9. Verification, quality score, report, export
10. LLM layer (Groq → Ollama → templates)
11. REST API contract
12. Frontend implementation notes
13. Sample datasets and benchmark/evaluation
14. Testing strategy
15. Security, privacy, performance, limits
16. Deployment (Docker, Render/Railway/Fly, CI)
17. Build phases with Cursor prompts and acceptance criteria
18. Final Definition of Done
- Appendix A — Cursor rules file
- Appendix B — Environment variables
- Appendix C — Image-generation prompts for mascot and 3D assets
- Appendix D — Copy deck (microcopy)

---

## 1. Product overview

**Name:** CSV Rescue — an explainable, reversible CSV data-cleaning tool.

**One-line pitch:** Upload a messy CSV, see exactly what is wrong and why, review proposed fixes side by side, approve or reject each one, undo mistakes, verify the result, and export a clean file plus a quality report.

**Primary user:** a student or analyst with a messy spreadsheet (student marks, sales, customers). Comfortable with Excel, not with code.

**Core promise:** *The tool never silently changes data and never calls a dataset "clean" without re-checking it.*

### 1.1 Seven-step workflow (drives navigation and the "Next step" banner)

| # | Step | Where in UI |
|---|------|-------------|
| 1 | Upload CSV (handle parse errors) | Datasets page |
| 2 | Profile the dataset (baseline snapshot) | Profile page |
| 3 | Detect issues | Issues page |
| 4 | Review recommendations | Cleaning Studio |
| 5 | Preview and approve / reject / skip | Cleaning Studio (Change Explorer) |
| 6 | Verify and undo | History + Reports |
| 7 | Export cleaned CSV and report | Reports page |

### 1.2 Feature list (all MUST work)

**Module A — Upload & Profiling:** drag-and-drop/file picker, delimiter + encoding detection, BOM handling, ragged-row detection, row/column counts, inferred types, sample values, stats, missing counts and %, duplicate-row count, distinct counts, baseline snapshot saved before any change.

**Module B — Issue detection (8 types):** missing values, exact duplicate rows, inconsistent text, inconsistent formats, invalid numeric values, invalid values (range/rule), suspicious outliers, duplicate identifiers. Each issue shows: column/rows, reason, affected count, evidence, and proposed next step.

**Module C — Recommended cleaning actions:** deterministic, each with a plain-English explanation, risk level, and parameters the user can change.

**Module D — Before-and-After Change Explorer:** side-by-side original vs proposed, highlighted cells, per-change checkboxes, accept / reject / skip, risk warnings.

**Module E — Cross-column rules:** rule builder (compare, range, arithmetic, format, unique, not-null, allowed-values), violation table, rerun after cleaning, suggested rules, natural-language → rule (LLM, optional).

**Module F — Reversible cleaning + verification:** operation history, undo (and redo), re-run all checks, before/after counts, resolved vs dismissed vs remaining vs newly introduced, quality report, export cleaned CSV, report (HTML + JSON), history (JSON/CSV), one-click ZIP bundle.

**Extras that are IN scope:** sample datasets, synthetic error-injection benchmark (CLI + in-app page), local-only privacy mode, global search, notifications panel, settings page, responsive layout.

**Out of scope for v1:** user accounts/auth, multi-user collaboration, non-CSV formats (xlsx/json), dark mode.

---

## 2. Design system (UI must match the reference image)

> **This is the most important section for visual fidelity.** The reference image is a *soft-clay / "claymorphism" pastel-lavender dashboard*. Study it before coding. Do **not** produce a flat white SaaS template, 1px gray borders, default shadcn look, or generic Tailwind UI blocks. Everything should feel puffy, rounded, softly lit from the top-left, and slightly 3D.

### 2.1 What the reference image looks like (decompose it)

1. **Page background:** a diagonal lavender gradient (`#C9BCEE → #DDD2F5 → #CBBDF0`). The whole app sits inside one big **rounded cream shell** (radius ≈ 44px) with a soft purple drop shadow.
2. **Floating left sidebar:** a tall, puffy **periwinkle-purple panel** (gradient `#A38FE8 → #8B75D6`, radius ≈ 36px, inner top highlight, inner bottom shade). Top: large circular avatar with a thick cream ring, then "Hi, {name}! 👋" in white bold. Below: nav items with **chunky filled white icons** + white labels. The **active item is a cream pill** with a purple icon + purple label and an elevated shadow. Bottom: a **pink promo card** with a 3D gold crown, title, one line of text and a pink pill button.
3. **Header row:** page title "Dashboard" in deep indigo, very bold, ~36px. A **cream search pill** (embossed, magnifier icon). A round **bell button with a pink badge** (number). A round **purple avatar button**.
4. **Hero banner:** wide rounded purple gradient card with a 3D character that *overflows the top edge*, floating pink music notes, greeting headline, muted subline, a saturated purple **pill CTA with a white play icon**, and a 3D potted plant on the right. The banner has a slightly darker "ledge" at the bottom edge.
5. **Four stat cards:** each tinted a different pastel (lavender, pink-peach, butter-yellow, baby-blue); each has a glossy **rounded-square 3D icon badge** (purple note, red heart, yellow clock, blue flame) at the top-left, a small muted label, a **big bold number**, and a small **green** delta line.
6. **Two chart cards:** cream cards. Left: bar chart with **pill-shaped bars in different pastel colours** and a small "This Week ⌄" chip. Right: a **donut chart** with pastel segments and a legend (coloured dot, label, % right-aligned).
7. **Two list cards:** left "Recently Played" list (rounded thumbnails, title, muted subtitle, **round white play buttons**, hairline dividers). Right "Daily Mix" with a big rounded image, title/subtitle overlaid at the bottom-left, round white play button bottom-right. Both have a tiny "See All" chip top-right.
8. **Footer CTA banner:** purple gradient strip with a smiling **3D star mascot**, headline, one-line subtext, sparkles and a lighter translucent pill button ("Explore Now").
9. **Motifs:** very large corner radii, soft layered shadows with white inner highlights, pastel tints, rounded geometric sans-serif (Nunito-like), emoji accents (👋 ☀️), no sharp edges anywhere.

### 2.2 Tokens (copy exactly; put in `frontend/src/styles/tokens.css` and mirror in `tailwind.config.ts`)

```css
:root {
  /* Surfaces */
  --bg-page-1: #C9BCEE;
  --bg-page-2: #DDD2F5;
  --bg-page-3: #CBBDF0;
  --shell: #F8F3FA;
  --shell-2: #F3ECF8;
  --card: #FCF9FC;
  --card-edge: #FFFFFF;

  /* Brand purples */
  --purple-50:  #F1EBFC;
  --purple-100: #E7DDF7;
  --purple-200: #D3C4F3;
  --purple-300: #BDAEF0;   /* hero light */
  --purple-400: #A996E8;   /* hero dark */
  --purple-500: #9783E0;   /* sidebar mid */
  --purple-600: #7C63D9;   /* primary button */
  --purple-700: #6A50C8;
  --sidebar-top: #A38FE8;
  --sidebar-bottom: #8B75D6;

  /* Ink */
  --ink: #2B2766;          /* titles, big numbers */
  --ink-2: #4A4580;
  --muted: #6F6A9C;        /* labels */
  --muted-2: #8C87B3;      /* placeholders (use only on large text) */

  /* Pastel tints (stat cards, chips) */
  --tint-lavender: #E8DEF7;
  --tint-pink: #FADADB;
  --tint-yellow: #FBEFC6;
  --tint-blue: #DCE6F6;
  --tint-mint: #D9F0E3;
  --tint-peach: #FBE3CF;

  /* Icon badge gradients */
  --badge-purple: linear-gradient(145deg, #A98BFF 0%, #6E52D4 100%);
  --badge-coral:  linear-gradient(145deg, #FF8C9A 0%, #E8455F 100%);
  --badge-amber:  linear-gradient(145deg, #FFD966 0%, #F5A524 100%);
  --badge-blue:   linear-gradient(145deg, #7DB4FF 0%, #3F7BE6 100%);
  --badge-mint:   linear-gradient(145deg, #7FE0A8 0%, #2FB36D 100%);
  --badge-pink:   linear-gradient(145deg, #FF9CC2 0%, #E8508F 100%);

  /* Chart palette (bars + donut), in this order */
  --c1: #A48BE9; /* purple */
  --c2: #F5A9C4; /* pink */
  --c3: #F9AE57; /* orange */
  --c4: #F9D56E; /* yellow */
  --c5: #A4D27C; /* green */
  --c6: #86B6EE; /* blue */
  --c7: #B9A5F0; /* soft purple */
  --c8: #F4B6A6; /* salmon */

  /* Semantic */
  --success: #2A8F4F;
  --success-bg: #DDF3E6;
  --warning: #B7791F;
  --warning-bg: #FDF0C9;
  --danger: #D23B5B;
  --danger-bg: #FADADF;
  --info: #3F6FD1;
  --info-bg: #DCE6F6;

  /* Promo pink card */
  --promo-1: #F8CDD6;
  --promo-2: #F3B5C6;
  --promo-btn: #EC6A93;

  /* Diff highlights (Change Explorer) */
  --diff-before: #FDE3E6;     /* old value cell */
  --diff-before-ink: #9B2C45;
  --diff-after: #DDF3E6;      /* new value cell */
  --diff-after-ink: #1F6B3B;
  --diff-flag: #FDF0C9;       /* flagged / needs review */

  /* Radii */
  --r-shell: 44px;
  --r-sidebar: 36px;
  --r-card: 28px;
  --r-inner: 20px;
  --r-badge: 18px;
  --r-pill: 999px;

  /* Shadows (layered, lit from top-left, with inner highlights) */
  --sh-shell: 0 40px 90px rgba(98,70,170,.30), inset 0 3px 0 rgba(255,255,255,.85);
  --sh-sidebar: 0 26px 50px rgba(98,70,170,.38), inset 0 3px 0 rgba(255,255,255,.35), inset 0 -12px 26px rgba(70,45,150,.28);
  --sh-card: 0 14px 34px rgba(124,99,217,.14), inset 0 2px 0 rgba(255,255,255,.95), inset 0 -5px 12px rgba(124,99,217,.06);
  --sh-card-hover: 0 22px 46px rgba(124,99,217,.22), inset 0 2px 0 rgba(255,255,255,.95), inset 0 -5px 12px rgba(124,99,217,.08);
  --sh-tint: 0 12px 26px rgba(124,99,217,.14), inset 0 2px 0 rgba(255,255,255,.8), inset 0 -6px 14px rgba(124,99,217,.08);
  --sh-btn: 0 12px 22px rgba(98,70,190,.40), inset 0 2px 0 rgba(255,255,255,.35), inset 0 -5px 10px rgba(50,28,130,.28);
  --sh-btn-light: 0 10px 20px rgba(98,70,190,.20), inset 0 2px 0 rgba(255,255,255,.9);
  --sh-pill-active: 0 12px 24px rgba(60,38,140,.30), inset 0 2px 0 rgba(255,255,255,.95);
  --sh-badge: 0 10px 18px rgba(40,20,100,.20), inset 0 2px 0 rgba(255,255,255,.55), inset 0 -4px 8px rgba(0,0,0,.14);
  --sh-field: inset 0 3px 8px rgba(124,99,217,.14), 0 1px 0 #fff;

  /* Focus */
  --focus: 0 0 0 4px rgba(124,99,217,.45);
}
```

**Page background (body):**
```css
body {
  background:
    radial-gradient(1100px 600px at 8% -5%, #EDE5FB 0%, transparent 60%),
    linear-gradient(160deg, var(--bg-page-1) 0%, var(--bg-page-2) 52%, var(--bg-page-3) 100%);
  background-attachment: fixed;
  color: var(--ink);
}
```

### 2.3 Typography

- **Font:** `Nunito` (self-hosted via `@fontsource/nunito`, weights 500, 600, 700, 800, 900). Fallback: `ui-rounded, "SF Pro Rounded", system-ui, sans-serif`. Do **not** use Inter/Roboto/Poppins.
- **Scale (desktop):**

| Role | Size / weight | Colour |
|------|---------------|--------|
| Page title | 36px / 800, letter-spacing -0.01em | `--ink` |
| Hero headline | 26px / 800 | `--ink` |
| Card title | 18px / 800 | `--ink` |
| Stat number | 34px / 800 | `--ink` |
| Body | 15px / 600 | `--ink-2` |
| Label / subtitle | 14px / 600 | `--muted` |
| Chip / small | 12–13px / 700 | `--muted` or `--ink-2` |
| Button | 16px / 800 | white on purple |

- Sentence case everywhere. No ALL-CAPS labels, no tracked-out eyebrows, no "01 / 02" numbering except in the real 7-step workflow stepper.
- Tabular numbers (`font-variant-numeric: tabular-nums`) for stats and tables.

### 2.4 App shell and layout

```
┌──────────────────────────── page lavender gradient ───────────────────────────┐
│ ┌── cream shell (r=44, padding 20) ─────────────────────────────────────────┐ │
│ │ ┌─sidebar─┐  Dashboard                [ search pill ]   (🔔3)  (👤)       │ │
│ │ │ avatar  │ ┌── hero banner (full width) ───────────────────────────────┐ │ │
│ │ │ Hi, Mia │ └───────────────────────────────────────────────────────────┘ │ │
│ │ │ ▣ Dash  │ ┌─stat──┐ ┌─stat──┐ ┌─stat──┐ ┌─stat──┐                       │ │
│ │ │ ○ nav   │ └───────┘ └───────┘ └───────┘ └───────┘                       │ │
│ │ │ ○ nav   │ ┌── bar chart (7 cols) ───────┐ ┌── donut (5 cols) ─────────┐ │ │
│ │ │  ...    │ └─────────────────────────────┘ └───────────────────────────┘ │ │
│ │ │ ┌promo┐ │ ┌── list card (7 cols) ───────┐ ┌── feature card (5 cols) ──┐ │ │
│ │ │ └─────┘ │ └─────────────────────────────┘ └───────────────────────────┘ │ │
│ │ └─────────┘ ┌── footer CTA banner (full width) ─────────────────────────┐ │ │
│ │             └───────────────────────────────────────────────────────────┘ │ │
│ └───────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

- Shell max-width **1440px**, centered, outer page padding 24px (≥1280px), 12px (<768px).
- Sidebar: **width 220px**, margin 8px inside the shell, `border-radius: var(--r-sidebar)`, sticky, scrolls internally if viewport is short (nav item height 52px, gap 6px).
- Content area: padding 28px; CSS grid, 12 columns, **gap 24px**.
- Breakpoints:
  - `≥1280`: full layout above.
  - `1024–1279`: sidebar becomes an **icon rail (84px)**, labels hidden, promo card hidden, avatar 56px.
  - `768–1023`: icon rail + 2-column card grids (stat cards 2×2, charts stacked).
  - `<768`: sidebar becomes a **floating bottom tab bar** (cream pill, 5 main icons + "More" sheet), header collapses to title + bell + avatar (search opens as a full-width sheet), all grids single column, hero character shrinks and sits bottom-right.

### 2.5 Component recipes (build these as reusable components in `frontend/src/components/clay/`)

| Component | Spec |
|-----------|------|
| `ClayShell` | Rounded cream shell, `--sh-shell`, background `linear-gradient(180deg, var(--shell), var(--shell-2))`. |
| `Sidebar` | Gradient `--sidebar-top → --sidebar-bottom`, `--sh-sidebar`, 1px inner top highlight. Avatar 120px circle, 6px cream (`#F6EEF6`) ring + soft shadow. Greeting `Hi, {name}! 👋` white 22px/800. |
| `NavItem` | Height 52px, radius pill, icon (Phosphor, `weight="fill"`, 24px) + label 17px/700 white. **Active:** background `#FBF4FA`, text/icon `--purple-600`, `--sh-pill-active`. **Hover:** `rgba(255,255,255,.14)` background. Badges (e.g., open-issue count) are small cream pills with purple text on the right. |
| `PromoCard` | Pink gradient `--promo-1 → --promo-2`, radius 28, crown-like 3D icon, title 18/800 `--muted`-dark, text 14/600, button `--promo-btn` pill with white text and `--sh-btn`-style shadow tinted pink. |
| `SearchPill` | Height 52, radius pill, background `#FBF6FB`, `--sh-field`, magnifier left, placeholder `--muted-2`. Opens results popover (Section 3.10). |
| `RoundIconButton` | 52px circle, cream, `--sh-btn-light`; bell variant has a pink/red badge (18px circle, white 11px/800 number) at top-right. |
| `AvatarButton` | 52px circle, purple gradient, white user glyph, `--sh-btn`. |
| `ClayCard` | `background: var(--card)`, radius 28, `--sh-card`, padding 24, `border: 1px solid rgba(255,255,255,.7)`. Hover lift (only on interactive cards): `translateY(-3px)` + `--sh-card-hover`, 180ms ease-out. |
| `TintCard` / `StatCard` | Same as ClayCard but background is a pastel tint + `--sh-tint`. Layout: `IconBadge` top-left, label under it (14/600 muted), value (34/800 ink), delta line (13/700; `--success` for improvement, `--danger` for regression, `--muted` neutral). |
| `IconBadge` | 56×56, radius 18, gradient `--badge-*`, white Phosphor fill icon 28px with `drop-shadow(0 2px 2px rgba(0,0,0,.25))`, `--sh-badge`, plus a pseudo-element glossy highlight (top-left white→transparent ellipse at 35% opacity). |
| `PillButton` (primary) | Height 52, padding 0 28px, radius pill, background `linear-gradient(180deg, #8C74E6, #6F55CF)`, white 16/800, `--sh-btn`. Hover: brighten 4%; active: `scale(.97)` + reduced shadow; disabled: 45% opacity, no shadow. |
| `PillButton` (light) | Cream background, purple text, `--sh-btn-light`. |
| `PillButton` (translucent) | `rgba(255,255,255,.28)` on purple banners, white text, inner highlight (like "Explore Now"). |
| `PillButton` (danger) | Coral gradient, same shape. |
| `Chip` | Height 30, radius pill, padding 0 12, 13/700, cream with `--sh-btn-light`; selectable variant fills `--purple-100` with purple text. "This Week ⌄" style dropdown chip is a `Chip` that opens a small clay popover menu. |
| `SeverityBadge` | Pill: `safe` → mint (`--success-bg` / `--success`), `review` → yellow (`--warning-bg`/`--warning`), `destructive` → pink (`--danger-bg`/`--danger`), `info` → blue. Always icon + text (never colour alone). |
| `ListRow` | Left 56px rounded-14 thumbnail/tile, title 16/800 ink, subtitle 14/600 muted, right `RoundActionButton` (40px white circle, purple triangle/arrow/undo icon, `--sh-btn-light`). Hairline divider `rgba(124,99,217,.12)` inset 0 on left 72px. |
| `FeatureCard` | Full-bleed rounded-24 image/illustration, gradient overlay bottom (`transparent → rgba(43,39,102,.65)`), title 24/800 white + subtitle 15/700 white 85%, round white action button bottom-right. |
| `CtaBanner` | Purple gradient `#B7A4EE → #9A84E3`, radius 28, left 3D mascot (overflows top by ~16px), headline 24/800 white-ish ink (use `#FFFFFF`), subtext 15/600 `rgba(255,255,255,.85)`, sparkles (SVG stars, 2–3, gently twinkling), right translucent pill button. |
| `Toast` | Clay card bottom-center (mobile) / bottom-right (desktop), icon badge small, auto-dismiss 4s, includes "Undo" action when the toast reports an applied change. |
| `Modal` / `Drawer` | Cream clay card, radius 32, backdrop `rgba(43,39,102,.35)` + 6px blur. |
| `Skeleton` | Lavender shimmer (`--purple-100 → --purple-50`), radius matches the component. |
| `DataGrid` | See 2.7. |
| `Progress` | 14px tall pill track `--purple-100` with inset shadow; fill gradient purple; animated width. |
| `Stepper` | The 7-step workflow as a row of round numbered badges connected by a pill track; completed = mint badge with check, current = purple, upcoming = cream. (Numbering is legitimate here because it is a real sequence.) |

### 2.6 Charts (Recharts, styled to match)

- **Bar chart ("pill bars"):** `barSize=28`, `radius=[14,14,14,14]`, each bar a different colour from `--c1…--c8`, **no axes lines**, only light dotted horizontal gridlines (`strokeDasharray="2 6"`, `rgba(124,99,217,.18)`), axis tick text 12/700 `--muted`. Tooltip = small clay card with coloured dot, label, value. Bars animate up from 0 on first render (600ms ease-out). A "This Week ⌄"-style chip at the top right switches series (Detected / Remaining / Resolved).
- **Donut:** `innerRadius="62%"`, `outerRadius="100%"`, `stroke="var(--card)"` `strokeWidth=3`, `cornerRadius=4`, `startAngle=90`, `endAngle=-270`. Legend to the right: 10px coloured dot, label 14/700 ink, percentage right-aligned 14/700 `--ink-2`. Centre of donut is empty (like the reference) or optionally shows total.
- **Sparklines/histograms** (profile page): same pill-bar style, tiny (barSize 6).
- Colour is never the only encoding: also show labels/legend text.

### 2.7 Data grid style (tables must NOT look default)

- Container: `ClayCard` with inner scroll. Header row = a pill-shaped lavender strip (`--purple-50`, radius 16) with 13/800 `--muted` text. Rows: height 48px, no vertical gridlines, hairline horizontal dividers `rgba(124,99,217,.10)`, alternate rows with a 3% lavender tint. Hovered row: `--purple-50`.
- Row number gutter in muted pill style. Use `@tanstack/react-table` + `@tanstack/react-virtual` (virtualized — MUST handle 100k rows smoothly).
- **Cell states:** `issue` → background `--diff-flag` with a small dot; `before` → `--diff-before` + strikethrough text; `after` → `--diff-after` bold; `selected change` → 2px inset purple ring. Cells with leading/trailing whitespace render a visible `·` marker (so " Jaipur " is visibly different from "Jaipur").
- Sticky first column(s) optional; column header menus (sort, filter, "go to issues for this column").

### 2.8 Iconography, illustration and assets

- **Icons:** `@phosphor-icons/react`. Sidebar = `weight="fill"`. Elsewhere = `weight="bold"`. Never mix with Lucide.
- **3D assets** (transparent WebP in `frontend/public/art/`): `avatar-default.webp`, `hero-character.webp`, `plant.webp`, `star-mascot.webp`, `sparkle-badge.webp`, `feature-card-bg.webp`, `empty-upload.webp`, `empty-clean.webp`, `empty-search.webp`. Generate them with the prompts in **Appendix C**. 
- **Fallbacks (MUST implement):** every image has an inline-SVG/CSS fallback (a clay-style gradient circle with an emoji or Phosphor icon; the star mascot as an SVG with a smiling face) so the UI looks right even before assets exist. Create the fallbacks in Phase 1 and wire `<ClayImage src fallback>`.
- Mascot concept: **"Sparky" the smiling yellow star** (as in the reference footer banner) is the product mascot. The hero character is a friendly girl with a magnifying glass tidying a spreadsheet card; the plant stays. The avatar is user-configurable (initial-based fallback with pastel gradient).

### 2.9 Motion

- One orchestrated page-load moment on the Dashboard only: stat numbers count up (700ms), bars grow, donut sweeps. Everything else is *response to user action*: card hover-lift, button press, drawers/modals sliding, toasts, diff rows fading when applied, undo "rewind" shimmer.
- Use `framer-motion`. Respect `prefers-reduced-motion` (disable count-up/sweep/lift; keep instant state changes).
- Route transitions: 180ms fade + 8px translate. No scroll-triggered animations.

### 2.10 Accessibility (quality floor)

- Text contrast ≥ 4.5:1 (check `--muted` on tinted cards; darken to `#5B5690` if needed). Focus ring `--focus` on every interactive element. All icon-only buttons have `aria-label`. Charts have `aria-label` plus a visually hidden table. Dialogs trap focus and close on Esc. Full keyboard operation of the Change Explorer: `J/K` next/prev change, `Space` toggle, `A` accept, `R` reject, `S` skip, `Ctrl/Cmd+Z` undo.

### 2.11 Anti-patterns (reject your own output if it shows any)

- Flat white cards with `border: 1px solid #e5e7eb`. Square-ish radii (<16px) on cards. Default blue links. Gray `shadow-md`. Inter font. Lucide icons. A plain top navbar. Default HTML tables. Pure-black text. Purple-to-pink "AI gradient" blobs. Emoji overuse beyond the 👋 / ☀️-style accents already in the reference.

---

## 3. Screens and behaviour

**Routes** (React Router): `/` Dashboard · `/datasets` · `/profile` · `/issues` · `/studio` · `/rules` · `/history` · `/reports` · `/settings`. All routes except `/` and `/datasets` and `/settings` show the "no dataset loaded" empty state (with an upload button) when there is no active session.

**Sidebar nav (in order, Phosphor fill icons):** Dashboard (`House`) · Datasets (`Table`) · Profile (`ChartBar`) · Issues (`WarningCircle`, with open-issue count pill) · Cleaning Studio (`MagicWand`, with pending-proposal count pill) · Rules (`ListChecks`) · History (`ClockCounterClockwise`) · Reports (`FileText`) · Settings (`Gear`).

**Sidebar promo card (replaces "Go Premium"):** 3D sparkle/star icon · title "Need a sample?" · text "Load a messy student or sales file in one click." · pink pill button "Load sample" → opens a small modal with two sample cards (Students, Sales); choosing one calls `POST /sessions/sample` and routes to `/profile`.

**First-run:** a small clay modal asks "What should I call you?" (default "friend"). Saved to `localStorage` key `csvrescue.profile`. Greeting uses it: `Hi, {name}! 👋` (sidebar) and `Good Morning|Afternoon|Evening, {name}! ☀️|🌤️|🌙` (hero) from the browser's local time.

### 3.1 Header (every page)
- Left: page title (36/800).
- Centre/right: `SearchPill` ("Search columns, issues, rules, values…"), `RoundIconButton` bell with unread badge, `AvatarButton`.
- A thin **session pill** under the title (small chip) shows `students_messy.csv · 5,000 rows · 12 columns` and a "Switch" chip when a dataset is active.

### 3.2 Dashboard (`/`) — mirrors the reference image one-to-one

| Reference element | CSV Rescue element |
|---|---|
| Hero "Good Morning, Mia! — Let's enjoy some music today! [Play Something]" | "Good Morning, {name}! — Let's get your data squeaky clean today. **[Upload a CSV]**". If a dataset is active the button says **[Continue cleaning]** and the subline shows the filename. Character with headphones → character with magnifying glass; plant stays. Floating notes → floating pink sparkles/cell icons. |
| Stat 1 (lavender, purple music badge): Songs Played 1,248 | **Rows** (lavender, purple `Table` badge): current row count; delta `N removed` (neutral) or `{cols} columns` |
| Stat 2 (pink, red heart badge): Favorites 128 | **Open issues** (pink, coral `WarningCircle` badge): number of open issues; delta `↓ N resolved` (green) |
| Stat 3 (yellow, clock badge): Hours Listened 34.6 | **Quality score** (yellow, amber `Gauge` badge): row quality % (Section 9.1); delta `+N pts since upload` (green) |
| Stat 4 (blue, flame badge): Current Streak 7 days in a row | **Changes applied** (blue, blue `MagicWand` badge): count; sub-line `N undone · M rejected` |
| "Listening Overview" bar chart + "This Week ⌄" | **Issues by type** pill-bar chart (8 types). Chip menu: *Detected / Remaining / Resolved*. |
| "Top Genres" donut + legend | **Where issues live** donut: top 4 columns by open-issue count + "Other"; legend with % |
| "Recently Played" (3 rows, play buttons) + "See All" | **Recent activity**: last 3 history operations (tile icon, title like "Trim whitespace · City", subtitle "42 cells · 2 min ago"); right circle button = **Undo** (enabled only on the latest applied op, otherwise **View**). "See all" → `/history`. |
| "Daily Mix" feature card ("Chill Mibes · 80 songs") | **Quick wins** feature card: title "Quick wins", subtitle "{N} safe fixes ready"; round button opens the *Apply safe fixes* modal (lists each safe proposal with counts + preview; primary "Apply {N} safe fixes"). |
| Footer banner "Discover new music / Play songs we think you'll love / [Explore Now]" | **Next step banner** driven by `session.stage`: no data → "Start with a CSV" [Upload]; uploaded → "Review {N} suggestions" [Open Cleaning Studio]; reviewed → "Verify your results" [Run verification]; verified → "Ready to export" [Export now]. Sparky the star mascot stays. |

- **Empty state (no dataset):** stat cards show "—" with muted "Upload a CSV to begin"; charts show a friendly illustration + one-line prompt; list card shows "Nothing yet — your changes will appear here"; quick-wins card shows the sample-data CTA.
- **Data source:** `GET /sessions/{id}/dashboard` (single aggregate endpoint, Section 11) to avoid waterfalls.

### 3.3 Datasets (`/datasets`)
- **Dropzone card** (dashed 3px `--purple-200` border, radius 32, 3D cloud/mascot art): "Drop your CSV here" / "or browse files". Accepts `.csv .tsv .txt`, up to the server limit (default 25 MB). Drag-over state: purple glow + scale 1.01. Upload progress bar (real progress via `XMLHttpRequest`/axios `onUploadProgress`).
- **Parse options** (collapsed accordion "Having trouble? Adjust how the file is read"): delimiter (Auto, `,`, `;`, tab, `|`), encoding (Auto, UTF-8, UTF-8-BOM, Windows-1252, Latin-1, UTF-16), "First row is a header" toggle. Changing options re-parses via `POST /sessions/{id}/reparse`.
- **Parse report card** after upload: detected encoding + delimiter + confidence, rows/columns, renamed duplicate/blank headers, **malformed rows** (line number, expected vs actual field count, raw text preview up to 200 chars) with explanation of how each was handled (short rows padded with blanks; long rows keep the first N fields, extras preserved in the report so nothing is lost silently). Severity banner: green "Parsed cleanly" / yellow "Parsed with N warnings" / red "Could not parse" (with the exact reason and fix suggestion).
- **Data tab:** virtualized `DataGrid` of the *current* data with issue-highlighted cells. **Double-click a cell to edit** → `POST /sessions/{id}/cells` (creates a `manual_edit` history operation, undoable). Toggle "Original / Current". Column header menu: override type, sort, filter, "Show issues".
- **Recent datasets** (from `localStorage` session ids, validated via `GET /sessions/summary?ids=…`): cards with filename, rows, last-modified, **Open** and **Delete** (calls `DELETE /sessions/{id}`).

### 3.4 Profile (`/profile`)
- Toggle chip **Original (baseline) / Current**.
- **Summary tiles** (4 small tint cards): rows, columns, missing cells (count + %), exact duplicate rows.
- **Column cards grid** (auto-fill, min 320px). Each card: column name, **type chip** (click → menu to override: text, integer, decimal, date, boolean, email, category, id → triggers re-profile/re-detect), missing count + % as a `Progress` pill, distinct count (+ "unique" pill when 100%), up to 5 sample-value chips (whitespace made visible), type-specific stats:
  - numeric: min, max, mean, median, std, Q1, Q3, + pill-bar histogram (10 bins);
  - text/category: min/max length, top 5 values with counts (pill bars);
  - date: earliest, latest, detected formats with counts;
  - boolean: true/false counts.
  - A coloured dot-count on the card shows open issues for this column → click goes to `/issues?column=…`.
- **Table tab**: same information as a dense `DataGrid`.
- Parse problems from upload are repeated in a collapsible card at the top.

### 3.5 Issues (`/issues`)
- **Filter bar** (chips): All + the 8 issue types with counts; select for column; status chips (Open · Dismissed · Resolved); text filter.
- **Issue card** (ClayCard) contents, always all of these:
  1. `IconBadge` per type (colours consistent across the app), **title** ("Missing values in *Age*"), severity chip.
  2. **Where:** column(s) and "N rows affected (x.x%)".
  3. **Why flagged:** one sentence from the detector (e.g., "Value is blank", "Value is 100,000 — more than 3×IQR above the 75th percentile (Q3 = 18, IQR = 9)").
  4. **Evidence:** up to 5 example cells as chips `row 14 · "twenty"`.
  5. **Proposed next step:** one sentence ("Fill with the median (22) or remove rows — you choose").
  6. Buttons: **View rows** (right drawer with grid of only affected rows, affected cells highlighted, paginated), **Fix in studio** (deep-link to its proposal), **Explain** (sparkle button → LLM/template explanation with a small source badge `Groq` / `Ollama` / `Built-in`), **Dismiss as valid** (modal asks for optional reason; issue moves to *Dismissed*, can be reopened).
- Outlier cards MUST include the text "Suspicious, not necessarily wrong" and never offer a default delete action.
- Sorting: severity desc, then affected count desc. Persist filters in the URL query string.

### 3.6 Cleaning Studio (`/studio`) — the Before-and-After Change Explorer

**Layout (desktop):** left **queue** (340px) + right **explorer** (flex). Mobile: queue becomes a top sheet.

**Queue:** each item = `ListRow` with tile icon, title ("Trim whitespace in City"), subtitle ("42 cells"), `SeverityBadge`, status dot (pending / applied ✓ / rejected ✕ / skipped ⤼). Filter chips: Pending · Applied · Rejected · Skipped · All. Top actions: **Apply all safe fixes** (opens confirm modal listing proposals + counts; applies each as its own history entry grouped in one batch, undoable as a batch) and **Refresh suggestions**.

**Explorer** (top → bottom):
1. Title + `SeverityBadge` + status.
2. **Explanation card** (plain English, e.g., "Trim leading and trailing whitespace in 42 cells. This standardises text without changing the words themselves.").
3. **Risk panel** (yellow/pink clay alert) shown for `review` and `destructive`: e.g., "Removing 7 rows discards their values in all 12 columns. You can undo this."
4. **Parameter controls** (pill selects/segmented control) from the proposal's `param_schema`, e.g., fill strategy `Leave · Median · Mean · Mode · Fixed value`, keep `first/last`, date target format, `dayfirst`. Changing a parameter calls `PATCH …/proposals/{id}` and refreshes the preview.
5. **Summary line:** "42 cells in 1 column · 0 rows removed".
6. **Diff grid** (virtualized): `☑ | Row | Column | Original | Proposed | Why | Confidence`. Original cell uses `--diff-before` (strikethrough), Proposed uses `--diff-after` (bold). **Proposed values are editable** (click → inline input; stores an override, shown with a small ✎ badge). Uncertain changes (`confidence < 0.9` or `review`) have a yellow flag and are **unchecked by default**; safe changes are checked by default. Toggle "Show full row context" adds up to 4 neighbouring columns (ID/name-like columns first).
7. **Other ways to fix** dropdown listing alternative actions for the same issue (e.g., missing values: Leave unchanged / Remove rows / Fill median / mean / mode / fixed value).
8. **Sticky footer:** `Reject` (light) · `Skip` (light) · **`Accept (N)`** (primary). *Accept* applies immediately, creates one history operation and shows a toast with **Undo**. *Reject* marks the proposal rejected (issue stays open, labelled "fix rejected", can be reopened). *Skip* defers it to the end of the queue. Destructive proposals require ticking "I understand this removes data" before Accept is enabled.
9. Keyboard shortcuts from 2.10.
10. **Explain with AI** button (sparkle) on every proposal and on every low-confidence change; for fuzzy-category merges it calls `ai/review-cluster` and shows an advisory card "AI opinion (not applied automatically)".

**Applied state:** proposal shows a green "Applied" banner with the operation id, the grid switches to showing the final values, and an **Undo** button (if still the latest op).

### 3.7 Rules (`/rules`)
- Left: **rule list** (cards: name, plain-language summary, severity, enabled switch, result chip "Passes ✓" or "12 violations", last-run time, edit/delete menu). Top: **Run all rules** button.
- **Suggested rules** strip (from Section 8.4): each suggestion card has editable parameters and **Add rule**.
- Right (or drawer on mobile): **rule builder** — type tiles (*Compare columns*, *Range*, *Arithmetic*, *Format*, *Unique*, *Required*, *Allowed values*), then a form with pill selects for columns/operators. Live **Test rule** shows violation count + first 10 violations with reasons *before saving*.
- **Describe in words** input with sparkle button → `POST /rules/from-text` → pre-fills the form (never saves automatically). Shows source badge.
- **Violations drawer:** table `Row | Columns involved | Values | Reason` (e.g., "End_Date (2025-01-02) is earlier than Start_Date (2025-03-04)"). Unevaluable rows (non-parseable) are shown in a separate tab, never silently counted as passing.
- Rules re-run automatically after every apply/undo and on demand.

### 3.8 History (`/history`)
- Summary tiles: Applied · Rejected · Skipped · Undone.
- **Timeline** (vertical pill rail with clay dots). Each operation card: tile icon, title, parameter summary, timestamp, affected cells/rows, status chip (Applied / Undone), **expand** → table of up to 50 before→after samples + "download full diff (CSV)". Only the **latest applied** op shows **Undo**; the latest undone shows **Redo**. `Ctrl/Cmd+Z` / `Ctrl/Cmd+Shift+Z` work globally (outside text inputs).
- Buttons: Export history JSON / CSV.

### 3.9 Reports (`/reports`)
- Top: `Stepper` of the 7 workflow steps with current step highlighted.
- **Run verification** primary button → `POST /verify` → results:
  - Verdict banner: **"Verified clean"** (green; only if verification ran on the *current* version, there are zero open findings after dismissals, and all enabled rules pass), **"Improved — N issues remain"** (yellow), or **"Not verified yet / out of date"** (grey; any change after the last verification marks it stale).
  - KPI tiles: quality score before → after; open issues before → after; rules passing before → after.
  - Table per issue type: *Before · Resolved · Dismissed · Remaining · New*. Explainer tooltip: "Resolved = you changed the data and the check now passes. Dismissed = you reviewed it and decided it is valid. Detected ≠ corrected."
  - Rules table (pass/fail with counts) and **Unresolved issues** list with links to the studio.
  - Action counts: applied / rejected / skipped / undone.
  - Optional **AI summary** paragraph (sparkle; template fallback).
- **Export card:** Cleaned CSV (options: delimiter, UTF-8 BOM for Excel, line endings), Report (HTML, self-contained, printable → "Save as PDF" via browser print), Report JSON, History (JSON/CSV), **Download everything (ZIP)**. If verification is stale, a yellow note appears but exporting is still allowed.

### 3.10 Global search, notifications, avatar menu
- **Search** (`Ctrl/Cmd+K` focuses it): debounced 200ms; popover groups results: *Pages*, *Columns*, *Issues*, *Rules*, *History*, *Cell values* (server `GET /sessions/{id}/search?q=`, max 20 cells). Keyboard up/down/Enter. Selecting navigates and highlights the target (column card pulse, issue card scroll-into-view, grid row scroll-to with highlight).
- **Notifications** (bell popover, Zustand + `localStorage`): entries for upload result, parse warnings, detection summary, applied/undone operations, verification result, AI fallback events ("Groq was unavailable — used Ollama"), errors. Badge = unread count. "Mark all read", "Clear".
- **Avatar popover:** name, Settings, "Delete my data now", About/version.

### 3.11 Settings (`/settings`)
- **Profile:** name; avatar (choose from 6 pastel presets or upload ≤ 200 KB, stored locally).
- **Detection defaults** (per session; changing triggers re-detect): missing-value tokens (editable chips), default day-first dates (toggle, default **on**), date output format (ISO `YYYY-MM-DD` default, or `DD/MM/YYYY`), outlier sensitivity (Relaxed / Standard / Strict), similar-text threshold slider (75–95, default 85), minimum numeric values for outlier checks (default 20).
- **AI assistant:** provider mode (*Groq → Ollama → built-in* default · *Ollama only (local)* · *Built-in only (off)*), provider status cards with **Test connection**, model name, latency and last error; "Redact emails/phone numbers before sending to AI" (default ON); plain-English privacy note: "Only column names and a few example values are sent — never whole files."
- **Data:** "Delete this dataset now", auto-delete notice (24h), version info.

### 3.12 System states (MUST implement everywhere)
- **Loading:** skeletons matching final layout (no spinners except on buttons).
- **Empty:** illustration + one sentence + one primary action.
- **Error:** inline clay alert with *what happened* + *how to fix it*; never raw stack traces. API errors follow the envelope in Section 11.1.
- **Stale data:** after any apply/undo the frontend invalidates `dashboard`, `issues`, `proposals`, `rules`, `history`, `profile(current)` queries.
- **Offline/backend down:** top banner "Can't reach the server — retrying…" with exponential backoff.

---

## 4. Architecture, tech stack, repo layout

### 4.1 Stack (pin exact versions in lockfiles; use the latest stable compatible versions at build time)

| Layer | Choice | Notes |
|---|---|---|
| Frontend | **React 18 + TypeScript (strict) + Vite** | SPA, served as static files by FastAPI in production |
| Styling | **Tailwind CSS 3** + CSS variables from Section 2.2 | custom `clay` utilities in `@layer components`; no component library look |
| Icons / font | `@phosphor-icons/react`, `@fontsource/nunito` | self-hosted, no CDN |
| State/data | **TanStack Query v5** (server state), **Zustand** (UI state, persisted bits) | |
| Routing | `react-router-dom` v6 | |
| Tables | `@tanstack/react-table` + `@tanstack/react-virtual` | virtualized |
| Charts | **Recharts** | styled per 2.6 |
| Motion | `framer-motion` | |
| Forms | `react-hook-form` + `zod` | |
| API types | `openapi-typescript` generated from FastAPI's OpenAPI → `src/api/schema.d.ts` | run `npm run gen:api` |
| Uploads | `react-dropzone` + axios progress | |
| Backend | **Python 3.11+, FastAPI, Uvicorn** | |
| Data | **pandas ≥ 2.2, numpy, rapidfuzz, python-dateutil, charset-normalizer** | all-string DataFrame core |
| Models/config | `pydantic` v2, `pydantic-settings` | |
| Persistence | **SQLite** (stdlib `sqlite3` or SQLAlchemy 2) + files on disk | per-session folder |
| HTTP client | `httpx` (async) | LLM calls |
| Templates | `jinja2` | HTML report |
| Rate limit | `slowapi` | |
| Tests | `pytest`, `pytest-asyncio`, `hypothesis` · `vitest` + Testing Library · `playwright` | |
| Lint/format | `ruff` (+ `ruff format`) · `eslint` + `prettier` | |
| Packaging | Docker multi-stage, docker-compose (with Ollama profile) | |

**No API key is required** for any core feature. LLM keys are optional (Section 10).

### 4.2 Repository layout (create exactly this)

```
csv-rescue/
├─ README.md
├─ docs/
│  ├─ BUILD_SPEC.md                # this file
│  ├─ DECISIONS.md                 # ambiguity decisions made during the build
│  └─ design-reference/dashboard-reference.png
├─ .cursor/rules/csv-rescue.mdc
├─ .env.example
├─ .gitignore  .dockerignore
├─ Dockerfile  docker-compose.yml  render.yaml  Makefile
├─ .github/workflows/ci.yml
├─ backend/
│  ├─ pyproject.toml
│  ├─ app/
│  │  ├─ main.py  config.py  db.py  errors.py  deps.py
│  │  ├─ api/            sessions.py data.py issues.py proposals.py rules.py history.py
│  │  │                  verify.py export.py ai.py search.py dashboard.py health.py
│  │  ├─ core/           ingest.py session_store.py working_set.py ops.py locks.py schemas.py ids.py
│  │  ├─ profiling/      profiler.py type_infer.py dates.py numbers.py number_words.py
│  │  ├─ detection/      engine.py missing.py duplicates.py text.py formats.py numeric.py
│  │  │                  outliers.py identifiers.py rule_findings.py config.py models.py
│  │  ├─ cleaning/       registry.py base.py proposals.py actions/ (one file per action, Section 7)
│  │  ├─ rules/          models.py evaluator.py suggestions.py
│  │  ├─ verification/   verify.py scoring.py
│  │  ├─ reporting/      report.py exporter.py templates/report.html.j2
│  │  ├─ llm/            service.py client.py redaction.py prompts.py templates.py schemas.py
│  │  │                  providers/ groq.py ollama.py base.py
│  │  └─ samples/        generate_samples.py students_messy.csv sales_messy.csv
│  ├─ benchmarks/        inject_errors.py run_benchmark.py baseline.py results/
│  └─ tests/             unit/ api/ property/ fixtures/
├─ frontend/
│  ├─ package.json vite.config.ts tailwind.config.ts postcss.config.js tsconfig.json index.html
│  ├─ public/art/        (3D assets; see Appendix C)
│  └─ src/
│     ├─ main.tsx App.tsx routes.tsx
│     ├─ styles/         tokens.css globals.css
│     ├─ api/            client.ts schema.d.ts hooks/
│     ├─ store/          profile.ts notifications.ts ui.ts session.ts
│     ├─ components/     clay/ layout/ charts/ grid/ studio/ rules/ common/
│     ├─ pages/          Dashboard Datasets Profile Issues Studio Rules History Reports Settings
│     ├─ lib/            format.ts greeting.ts shortcuts.ts search.ts
│     └─ __tests__/
└─ e2e/                  playwright.config.ts specs/
```

### 4.3 Runtime model
- **One FastAPI process** serves `/api/v1/*` and, in production, the built frontend (`StaticFiles` + SPA fallback to `index.html`).
- Heavy pandas work runs in `run_in_threadpool`. Each session has a **per-session lock** (`threading.RLock` in a dict, created lazily) so mutating requests are serialized; reads take no lock but read from immutable snapshots.
- Start with `--workers 1` (small instances). Because all state is reconstructable from disk (Section 5), multi-worker would still be correct if a shared disk is used, but the in-memory cache is per-worker.

---

## 5. Session, data model, and the undo engine

### 5.1 Core principle: **everything is a string until proven otherwise**
Read the CSV so that **nothing is coerced**:
```python
pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False,
            encoding=enc, sep=delim, engine="python", quoting=csv.QUOTE_MINIMAL)
```
- Stored cells are exactly what was in the file (blank = `""`).
- Typed views (numeric/date) are derived on demand and cached; they never replace the stored strings. Only an *operation* may change a stored string.
- Row identity: the DataFrame **index is `rid`** = 0-based position in the original file (after the header). `rid` never changes, even after deletions. UI row numbers = `rid + 1` (so "Row 14" means `rid 13`). This MUST be consistent everywhere, and export preserves original order.

### 5.2 Ingestion (`core/ingest.py`)
1. Enforce limits (Section 15). Save raw bytes to `data/sessions/{sid}/original.csv` (as uploaded).
2. **Encoding:** BOM sniff (UTF-8-SIG, UTF-16 LE/BE) → else `charset_normalizer` → fallback `utf-8` then `cp1252` then `latin-1`. Record `encoding`, `confidence`.
3. **Delimiter:** `csv.Sniffer` on the first 64 KB with candidates `, ; \t |`; fallback to the delimiter with the most consistent field count across the first 50 lines.
4. **Header handling:** blank headers → `Unnamed: {i}`; duplicates → `name`, `name.1`, `name.2` (report each rename).
5. **Ragged rows:** parse with `csv.reader`; for each row compare field count to header count. Short rows → pad with `""`; long rows → keep first N fields, store the extras in `parse_report.malformed_rows[i].extra_fields`. **Every** malformed row is listed (line number, expected, actual, raw preview, handling). Fast path: if a quick `pd.read_csv(..., on_bad_lines="error")` succeeds, skip the slow path.
6. **Empty file / header-only / binary file** → friendly error codes `EMPTY_FILE`, `NO_DATA_ROWS`, `NOT_TEXT`.
7. Save `original.pkl` (pandas pickle, server-generated only — never unpickle user files) for fast reload, write `parse_report.json`.
8. Build the baseline: profile + detection run **before any change**; persist `baseline_profile.json` (never overwritten except by `reparse`). The "before" findings used by verification are recomputed from `original.pkl` with the current config and rules and cached (Section 9.2), so rules added later are still compared fairly.

### 5.3 SQLite schema (`app/db.py`) — one DB file `data/csvrescue.db`
```sql
CREATE TABLE sessions (
  id TEXT PRIMARY KEY, filename TEXT NOT NULL, created_at TEXT, updated_at TEXT, expires_at TEXT,
  stage TEXT NOT NULL DEFAULT 'uploaded',      -- uploaded|profiled|reviewing|reviewed|verified|exported
  head_seq INTEGER NOT NULL DEFAULT 0,         -- seq of latest *applied* op (0 = none)
  verified_seq INTEGER,                        -- head_seq at last verification
  verified_at TEXT,
  settings_json TEXT NOT NULL,                 -- DetectionConfig + type overrides + unique columns
  parse_report_json TEXT NOT NULL,
  n_rows_original INTEGER, n_cols INTEGER
);
CREATE TABLE operations (
  id TEXT PRIMARY KEY, session_id TEXT NOT NULL, seq INTEGER NOT NULL,
  batch_id TEXT, kind TEXT NOT NULL,           -- action type, 'manual_edit', 'batch'
  title TEXT NOT NULL, params_json TEXT NOT NULL,
  status TEXT NOT NULL,                        -- applied|undone|discarded
  proposal_id TEXT, created_at TEXT, undone_at TEXT,
  affected_cells INTEGER, affected_rows INTEGER, rows_deleted INTEGER,
  patch_path TEXT NOT NULL,                    -- ops/{id}.json.gz
  state_hash_after TEXT,                       -- integrity check
  UNIQUE(session_id, seq)
);
CREATE TABLE rules (id TEXT PRIMARY KEY, session_id TEXT, name TEXT, enabled INTEGER, json TEXT, created_at TEXT, updated_at TEXT);
CREATE TABLE decisions (session_id TEXT, proposal_key TEXT, status TEXT, reason TEXT, updated_at TEXT, PRIMARY KEY(session_id, proposal_key));
CREATE TABLE dismissals (session_id TEXT, issue_key TEXT, reason TEXT, rids_json TEXT NOT NULL, created_at TEXT, PRIMARY KEY(session_id, issue_key));
CREATE TABLE ai_cache (key TEXT PRIMARY KEY, response_json TEXT, source TEXT, created_at TEXT);
CREATE INDEX idx_ops_session ON operations(session_id, seq);
```
Use WAL mode and `PRAGMA foreign_keys=ON`.

### 5.4 Operations and patches
An **operation** is the only way data changes. Its patch file (`ops/{op_id}.json.gz`):
```json
{
  "cells": [ {"rid": 13, "col": "City", "old": " Jaipur ", "new": "Jaipur"} ],
  "deleted_rows": [ {"rid": 7, "values": {"ID": "S007", "City": "Jaipur", "...": "..."}} ],
  "meta": {"action": "trim_whitespace", "params": {"columns": ["City"]}}
}
```
- **Apply:** for each cell patch, assert current value == `old` (else raise `STATE_MISMATCH`, never overwrite blindly); set `new`. For deleted rows: drop from the DataFrame.
- **Undo (latest applied op only):** reverse: restore `old` values and re-insert deleted rows at their original `rid` position (re-sort index). Mark op `undone`; `head_seq` moves to the previous applied op.
- **Redo:** re-apply the latest `undone` op (only if no new op has been applied since). Applying a new op **discards** all undone ops (status `discarded`, patch files deleted).
- **Batch:** `apply-safe` creates a `batch` op with `batch_id`; child ops are individual rows with `batch_id` set. `undo` on a batch undoes all children (reverse order) atomically.
- **Atomicity:** write patch file → update DataFrame in memory → single SQLite transaction (insert op, update `head_seq`, `updated_at`). On any exception roll back the in-memory change by applying the inverse patch.
- **State hash:** after every apply/undo compute `hash(df)` = `pd.util.hash_pandas_object(df, index=True).sum()` (as hex) and store it; unit tests MUST prove `apply → undo` returns the identical hash.
- **Cold load / cache miss:** load `original.pkl`, then replay every `applied` op in `seq` order; compare the final hash to `state_hash_after` of the last op; on mismatch return `STATE_CORRUPT` and offer "Reset to original".
- **Working-set cache:** `WorkingSet` objects in an LRU (max 8 sessions or 512 MB). `WorkingSet` holds: `df`, `column_meta`, typed-view cache, detection cache keyed by `(head_seq, settings_hash, rules_hash)`.

### 5.5 Session lifecycle
- `session_id` = `secrets.token_urlsafe(16)` (unguessable; it is the only credential).
- TTL 24h from last activity (`SESSION_TTL_HOURS`), purge job at startup and hourly (delete rows + folder). `DELETE /sessions/{id}` purges immediately.
- Stage transitions: `uploaded → profiled` (baseline built) `→ reviewing` (first proposal decision/op) `→ reviewed` (no pending proposals of severity ≥ warning) `→ verified` (verify run at current `head_seq`; any later op resets to `reviewing`) `→ exported`.

### 5.6 Column metadata
```python
class ColumnMeta(BaseModel):
    name: str
    inferred_type: Literal["integer","decimal","boolean","date","email","text","category","id"]
    type_confidence: float          # share of non-blank values that parse as the inferred type
    override_type: str | None       # user override
    effective_type: str             # override or inferred
    date_formats: list[dict] | None # [{"format":"%d/%m/%Y","count":410}, ...]
    dayfirst_resolved: bool | None
    is_unique_declared: bool        # user/auto-declared unique
    unique_auto: bool
```

---

## 6. Detection engine (exact algorithms)

### 6.1 Data structures
```python
class IssueType(str, Enum):
    missing_value="missing_value"; duplicate_row="duplicate_row"; inconsistent_text="inconsistent_text"
    inconsistent_format="inconsistent_format"; invalid_numeric="invalid_numeric"; invalid_value="invalid_value"
    outlier="outlier"; duplicate_id="duplicate_id"

class IssueGroup(BaseModel):          # one card on the Issues page
    key: str            # stable: f"{type}:{subtype}:{column or '*'}" (+ ":"+rule_id for rule groups)
    type: IssueType
    subtype: str        # e.g. blank|disguised|whitespace|case_variant|similar_values|date_mixed|number_format|boolean_variant|range|rule:<id>...
    column: str | None
    columns: list[str]  # all involved columns (cross-column rules)
    severity: Literal["error","warning","info"]
    rids: list[int]     # affected rows (store as numpy int32 internally; list only in API slices)
    cells: int          # affected cell count
    reason: str         # human sentence (deterministic template)
    evidence: list[Evidence]   # up to 5 {rid, column, value, note}
    suggested_next_step: str
    stats: dict         # detector-specific numbers (q1,q3,iqr,median,threshold,similarity,...)
```
- Detection output = `list[IssueGroup]`. Group `key`s are **deterministic**, so the baseline and later runs can be diffed (Section 9).
- `DetectionConfig` (all user-tunable in Settings, with defaults):

| Key | Default |
|---|---|
| `missing_tokens` | `["na","n/a","nan","null","none","nil","-","--","?","missing","#n/a"]` (case-insensitive, exact match after trim) |
| `type_confidence` | 0.90 |
| `dayfirst_default` | true |
| `date_output_format` | `%Y-%m-%d` |
| `similar_threshold` | 85 (RapidFuzz `fuzz.ratio` on normalized strings) |
| `similar_max_distinct` | 200 |
| `outlier_min_values` | 20 |
| `outlier_sensitivity` | `standard` → IQR multiplier 1.5 / robust-z 3.5; `strict` → 1.5 / 3.0; `relaxed` → 3.0 / 4.5 |
| `unique_name_patterns` | regex `(^|_|\b)(id|uuid|guid|sku|code|email|roll_?no|reg(istration)?_?(no|number)|ref(erence)?)($|_|\b)` (case-insens.) |
| `unique_min_distinct_ratio` | 0.90 (non-blank values) |
| `duplicate_ignore_columns` | `[]` |

### 6.2 Type inference (`profiling/type_infer.py`)
For each column take non-blank, trimmed values (`n`). Test in this order and pick the first type whose parse-success ratio ≥ `type_confidence`:
1. **boolean:** values ⊂ `{true,false,yes,no,y,n,t,f,1,0}` (case-insens.) with ≥ 2 distinct values and not purely `1/0` unless the column name suggests boolean (`is_|has_|flag|active`).
2. **integer:** regex `^[+-]?\d+$` after removing thousands separators (pattern `^\d{1,3}(,\d{2,3})+$` incl. Indian grouping) / currency symbols (`₹ $ € £`) / trailing `%`; parentheses = negative.
3. **decimal:** `^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$` after the same cleanup.
4. **date:** matches ≥ 1 known date pattern (Section 6.6).
5. **email:** matches the email regex.
6. else **text**; if distinct ≤ min(50, 5% of rows) and avg length < 40 → **category**; if name matches `unique_name_patterns` and distinct ratio ≥ 0.9 → **id**.
Values that fail the chosen type are the *invalid-type* values (Section 6.5). A value that is number words ("twenty") in an integer/decimal column counts as invalid (and gets a proposal, Section 7).

### 6.3 Profiler outputs (`profiling/profiler.py`)
Dataset: rows, columns, memory estimate, total cells, missing cells (blank + disguised separately), exact duplicate row count, parse report. Column: type, confidence, missing (blank/disguised counts and %), distinct count, repeated non-blank value count (e.g., "12 repeated non-empty values"), top-5 values, 5 sample values, numeric stats (min,max,mean,median,std,q1,q3,sum), text stats (min/max/avg length), date stats (min, max, formats), histogram (10 bins) or top-values bars. All JSON-serialisable; numpy types converted.

### 6.4 Missing values (`detection/missing.py`)
- **blank:** `value.strip() == ""` → group `missing_value:blank:{col}`, severity `warning`.
- **disguised:** trimmed lower-case value ∈ `missing_tokens` → `missing_value:disguised:{col}`, severity `warning`. Reason: "'N/A' is a placeholder for a missing value." Mark proposals for this subtype as **review** (a token like "None" may be a real category).

### 6.5 Invalid numeric (`detection/numeric.py`)
For columns with effective type integer/decimal: every non-blank, non-missing-token value that fails numeric parsing (after the cleanup in 6.2) → group `invalid_numeric:parse:{col}`, severity `error`. Reason: `Age = "twenty" is not a number`. Evidence stores the value; `stats.parsable_as_words` lists values `words_to_number()` can convert (so Section 7 can propose `20` with `review` risk). Values that parse but carry formatting (currency symbols, thousands commas, %) are **not** invalid; they are reported under `inconsistent_format:number_format`.

### 6.6 Dates & formats (`profiling/dates.py`, `detection/formats.py`)
Recognised patterns (regex → `strptime` format): `YYYY-MM-DD`, `YYYY/MM/DD`, `DD/MM/YYYY`, `MM/DD/YYYY`, `DD-MM-YYYY`, `MM-DD-YYYY`, `DD.MM.YYYY`, `D Mon YYYY`, `DD Month YYYY`, `Mon D, YYYY`, `Month D, YYYY`, ISO datetime (`YYYY-MM-DDTHH:MM[:SS][Z]`, date part kept, time reported as a warning because trimming it loses information → **review** risk).
- Classify each value into a *pattern family* (`ymd-dash`, `slash-ambiguous`, …). Slash/dash/dot values with both numeric parts ≤ 12 are **ambiguous**.
- **Resolve day-first vs month-first per column:** if any value has first part > 12 → day-first; any second part > 12 → month-first; if both occur in the same column → mark **conflict** (flag, require user choice); if neither → use `dayfirst_default` and mark `dayfirst_resolved=false` (proposals become `review` and show a banner: "Dates like 03/04/2026 can mean 3 April or 4 March. We assumed day-first — change it here.").
- Two-digit years → treated as ambiguous (never auto-expanded); flagged `review`.
- Impossible dates (e.g., 31/02/2026, month 13) → `invalid_value:date` group (severity `error`); no auto-fix.
- **inconsistent_format:date_mixed:** ≥ 2 distinct pattern families among valid dates in one date column → one group; reason "Dates use 3 different formats: 410× DD/MM/YYYY, 88× YYYY-MM-DD, 5× D Mon YYYY".
- **number_format:** numeric column where values mix plain numbers with currency symbols/commas/percent/parentheses → group; proposal strips formatting.
- **boolean_variant:** boolean column with ≥ 2 representation families (`Yes/No`, `Y/N`, `true/false`, `1/0`) → group; canonical = most frequent family.

### 6.7 Exact duplicate rows (`detection/duplicates.py`)
`df.duplicated(subset=cols_without_ignored, keep="first")` on raw strings. Group `duplicate_row:exact:*`, severity `error`, `rids` = the *redundant* copies; evidence includes `first_rid` for each. Reason: "Row 22 is identical to row 4 in every column." (Rows that differ only by whitespace/case are **not** exact duplicates; they surface after normalisation — Section 9 labels these "revealed by cleaning".)

### 6.8 Inconsistent text (`detection/text.py`)
Applies to text/category columns (skip email/id/date/numeric; skip free text — avg length > 40 and distinct ratio > 0.5 — except whitespace checks).
1. **whitespace:** leading/trailing whitespace, internal runs of ≥ 2 spaces, non-breaking spaces (`\u00a0`), zero-width chars (`\u200b`) → `inconsistent_text:whitespace:{col}`, severity `info`. Evidence displays visible markers (`·`).
2. **case_variant:** group values by `norm(v) = collapse_spaces(strip(v)).casefold()`; groups with ≥ 2 distinct raw forms → `inconsistent_text:case_variant:{col}`, severity `warning`. Canonical form = most frequent raw form (after strip); ties → Title Case. Only forms that differ by case/spacing are grouped (this is the **safe** group).
3. **similar_values:** if distinct normalized values ≤ `similar_max_distinct`: compute pairwise `rapidfuzz.fuzz.ratio(a, b)` among *different* normalized values using `process.cdist`; link pairs with score ≥ threshold; cluster with union-find; canonical = most frequent. **Guards to reduce false positives (MUST):** skip pairs whose strings differ only in digits (`Room 101`/`Room 102`), skip pairs where either string is shorter than 4 chars, skip pairs that differ by a whole token of ≤ 2 chars (`Team A`/`Team B`), skip pairs that are both frequent (each ≥ 20% of the column — they are likely distinct categories), and never cluster across more than 6 members. Group `inconsistent_text:similar_values:{col}`, severity `info`, **always review risk**, stats keep `[(value, count, similarity)]`. Example: `Jaipur`, `jaipur`, `Japur` → case variants merge safely; `Japur` is a *possible* typo needing approval.

### 6.9 Outliers (`detection/outliers.py`)
Numeric columns only, with ≥ `outlier_min_values` valid numbers, skipping id-like/unique columns and columns where > 95% of values are identical.
1. Compute `Q1, Q3, IQR`. If `IQR == 0` → skip column (document as limitation in the card: "Not enough variation to judge outliers").
2. If the column is right-skewed (skewness > 2 and all values > 0) → run the test on `log1p(x)` and mention it in the reason.
3. Fences: `low = Q1 − k·IQR`, `high = Q3 + k·IQR` with `k` from sensitivity (standard 1.5).
4. Robust z: `0.6745·(x − median)/MAD` (if `MAD == 0` skip this condition).
5. **Flag only if outside the fences AND |robust z| > threshold** (both). This keeps precision high.
Group `outlier:iqr:{col}`, severity `info`. Reason: `Quantity = 100,000 is far above the usual range (most values are between 1 and 20; Q3 = 14, upper fence = 31).` Always include the sentence "Suspicious, not necessarily wrong." **No default delete.**

### 6.10 Duplicate identifiers (`detection/identifiers.py`)
Columns declared unique (settings or `unique` rule) **or** auto-detected (name matches `unique_name_patterns` and distinct ratio of non-blank values ≥ `unique_min_distinct_ratio`; show an "auto-detected" badge and a toggle to disable). Compare on trimmed + casefolded values; blanks ignored. Group `duplicate_id:repeat:{col}`, severity `error`, `rids` = **all rows** in conflicting groups; evidence = `{value, rids:[...]}`. Never auto-resolve.

### 6.11 Rule-based findings (`detection/rule_findings.py`)
Every enabled rule (Section 8) produces an `invalid_value` group with `subtype = "rule:<rule_id>"`, `severity` = rule severity, columns = involved columns, reason = rule's failure message template per row. Built-in sanity suggestions are *suggested* (not enforced) until the user accepts them (Section 8.4).

### 6.12 Engine orchestration (`detection/engine.py`)
```python
def run_detection(ws: WorkingSet, config: DetectionConfig, rules: list[Rule], dismissals: set[str]) -> DetectionResult:
    # order: missing → duplicates(row) → text → formats → numeric → outliers → identifiers → rules
    # returns groups sorted by (severity, -cells), plus per-row/cell issue masks for the grid highlights
```
- Deterministic and side-effect free. Target: 100k rows × 20 cols ≤ 10 s on 2 vCPU. Use vectorised string ops (`df[col].str.strip()` etc.), `numpy`, avoid Python loops over rows except for evidence generation (cap at 5).
- Cache by `(head_seq, config_hash, rules_hash)`.
- **Dismissals:** a dismissal stores the issue-group `key` plus the sorted list of `rid`s the user dismissed (add a `rids_json TEXT` column to the `dismissals` table). On later runs, findings whose `(key, rid)` is in that stored set are marked `dismissed` and excluded from open counts; any *other* rid in the same group stays open. Reopening an issue deletes its dismissal row.
- Per-cell issue mask for the grid: `dict[(rid, col)] -> list[group_key]` produced lazily for the visible window only (`GET /data/rows` annotates cells with `issue_keys`).

---

## 7. Cleaning proposals and actions

### 7.1 Concepts
```python
class Change(BaseModel):
    id: str                  # cell: f"{rid}:{column}"   row deletion: f"row:{rid}"
    kind: Literal["cell_update","row_delete"]
    rid: int; column: str | None
    before: str | None; after: str | None      # None for row_delete
    reason: str                                 # per-change explanation (short)
    confidence: float                           # 0–1
    selected: bool                              # default checkbox state
    override: str | None = None                 # user-edited 'after'

class Proposal(BaseModel):
    key: str                 # stable: f"{action}:{column or '*'}:{scope_hash}" – used for decisions
    action: str              # registry id
    title: str               # "Trim whitespace in City"
    explanation: str         # plain-English paragraph (deterministic template)
    column: str | None; columns: list[str]
    issue_keys: list[str]
    params: dict; param_schema: list[ParamSpec]  # UI controls (select|number|text|toggle)
    alternatives: list[AlternativeAction]        # "Other ways to fix"
    risk: Literal["safe","review","destructive"]
    warnings: list[str]                          # risk text shown in the yellow/pink alert
    cells_affected: int; rows_affected: int; rows_deleted: int
    status: Literal["pending","applied","rejected","skipped","partial"]
    priority: int            # ordering in the queue
    based_on_seq: int        # head_seq when the preview was computed
```
- **Preview is always computed server-side** by running the action's `build_changes(ws, params)` — a pure function that returns changes **without** mutating data. `GET …/proposals/{key}/changes?offset&limit&only_uncertain` pages through them.
- **Apply recomputes** the changes from current state, intersects with the user's selected `change_ids` (and applies `override` values), validates, writes one operation. If `based_on_seq != head_seq` and the recomputed selection differs → `409 PREVIEW_STALE` with the fresh preview (single apply) or silent recompute using default selection (batch apply).
- **Risk rules (MUST):** any proposal that deletes rows → `destructive` (requires the confirm checkbox). Anything where a correct value is a guess (fuzzy merge, assumed day-first dates, number words, fills, clip, recompute, swaps, converting placeholder tokens) → `review`. Pure formatting that cannot change meaning (whitespace, case-variant merge to the dominant form, unambiguous date reformat, boolean spelling, thousands separators) → `safe`.
- **Apply-all-safe** only applies `safe` proposals, in `priority` order, as one batch.
- **Decisions** (`decisions` table): `accepted` (applied), `rejected`, `skipped`. Rejected proposals stay in the queue (greyed) and can be reopened. A proposal whose changes are all gone (issue resolved) disappears; applied ones remain visible via History.

### 7.2 Action catalogue (`cleaning/actions/*.py`; register each in `registry.py` with `priority`)

| Priority | Action id | Triggered by | Default risk | What it changes | Params (UI) |
|---|---|---|---|---|---|
| 10 | `trim_whitespace` | `inconsistent_text:whitespace` | safe | strip ends, collapse internal runs of spaces to one, NBSP → space, drop zero-width chars | `collapse_internal` (toggle, default on) |
| 15 | `convert_disguised_missing` | `missing_value:disguised` | review | set placeholder tokens (`N/A`, `-`, …) to blank | `tokens` (multi-select) |
| 20 | `normalize_case_variants` | `inconsistent_text:case_variant` | safe | map variants to canonical form | `canonical` = `most_frequent`(default) / `title` / `upper` / `lower` |
| 25 | `normalize_numbers` | `inconsistent_format:number_format` | safe (review if `%` present or mixed currency symbols) | strip currency symbols, thousands separators, `(x)`→`-x`, `%` | `keep_percent_as` = `whole`(12) / `fraction`(0.12) |
| 26 | `normalize_booleans` | `inconsistent_format:boolean_variant` | safe | unify to one spelling family | `target` = `Yes/No` / `Y/N` / `true/false` / `1/0` (default = most frequent) |
| 30 | `standardize_dates` | `inconsistent_format:date_mixed` (+ any non-target-format date) | safe if unambiguous, else review | rewrite to `date_output_format` | `dayfirst` (toggle), `output_format`, `keep_time` |
| 40 | `remove_duplicate_rows` | `duplicate_row` | destructive | delete redundant copies | `keep` = `first`(default) / `last` |
| 45 | `fix_invalid_numeric` | `invalid_numeric` | review | number words → numbers (`twenty` → `20`); otherwise optionally set blank | `mode` = `convert_words`(default) / `set_blank` / `leave` |
| 50 | `fill_missing` | `missing_value:blank` | review (destructive if `drop_rows`) | fill or remove rows | `strategy` = `leave` / `median` / `mean` / `mode` / `constant` / `drop_rows`; `constant`; default strategy = median (numeric), mode (category/boolean), leave (text/id/date/email) |
| 55 | `merge_similar_values` | `inconsistent_text:similar_values` | review | map rare variants to the canonical value (one sub-group per cluster) | per-cluster `canonical` dropdown |
| 60 | `fix_out_of_range` | `invalid_value:rule:<range rule>` | review | per violation | `mode` = `set_blank`(default) / `clip_to_bound` / `abs_value` (only when negative and lower bound ≥ 0) / `delete_rows` / `leave` |
| 62 | `fix_rule_violation` | other rule groups | review | arithmetic: `recompute_target`; compare: `swap_values` (confidence 0.6); allowed-values: `nearest_allowed` (fuzzy ≥ 90); format(email): `trim_lowercase` (safe) | rule-specific |
| 70 | `handle_outliers` | `outlier` | review (destructive for `exclude_rows`) | **no change by default**. Modes: `keep` (= dismiss as valid), `set_blank`(default when user opens it), `exclude_rows`, `clip_to_fence`. All changes **unchecked** by default. | `mode` |
| 80 | `resolve_duplicate_ids` | `duplicate_id` | destructive | per conflict group: `keep_first` / `keep_last` / `keep_selected` (pick rid) / `keep_all` (= dismiss) — shows the conflicting rows side by side | per-group choice |
| — | `manual_edit` | user double-clicks a cell | review | single cell | — (not a proposal; creates an operation directly) |

Priority = recommended order (formatting first, then structure, then values), so duplicate rows revealed by trimming are found before dedupe, etc.

### 7.3 Action rules worth spelling out
- **Fill strategies:** `median/mean` only for numeric columns; format filled numbers with the column's max observed decimal places (median `22.0` → `22`, `22.5` → `22.5`); `mode` ties → alphabetically first; `constant` validated against the column type. Warning text: "Filling invents values. It keeps the row but can bias averages. You can also leave the blanks or remove the rows."
- **Words to numbers:** `words_to_number("twenty five") == 25` for 0–999,999 (hyphens, "and", case-insens.; no decimals). Anything unparseable stays flagged with `confidence=0` and no auto-change.
- **Dates:** parse with explicit formats only (never `dateutil`'s guessing for output decisions). Rewrite only values not already in the target format. If time portions are dropped, add a warning and mark `review`.
- **Similar values:** each cluster's canonical defaults to the most frequent member; per change `confidence = similarity/100`; changes unchecked by default; AI advisory available (Section 10).
- **Duplicate IDs:** conflict groups are rendered as a mini table (one row per record in the group, differing cells highlighted). If all non-ID columns are identical the group is labelled "Likely duplicate record" (and pre-suggests `keep_first`); otherwise "Different records share an ID — review".
- **Never** auto-change: IDs, emails (except trim/lowercase of format-only issues), free text content, or values in columns the user has locked (columns can be "locked" in Profile → excluded from all proposals; store in settings).
- Every `Change.reason` is a short deterministic string (e.g., "Extra spaces removed", "Capitalisation standardised", "Possible spelling variation (91% similar to 'Jaipur') — review required").

---

## 8. Rules engine (cross-column validation)

### 8.1 Rule model (`rules/models.py`, Pydantic v2 discriminated union on `type`)
```python
class BaseRule(BaseModel):
    id: str; name: str; severity: Literal["error","warning","info"] = "error"
    enabled: bool = True; origin: Literal["user","suggested","ai"] = "user"; description: str | None = None

class CompareRule(BaseRule):
    type: Literal["compare"]
    left: str                                   # column
    op: Literal["eq","ne","lt","lte","gt","gte","contains","not_contains","starts_with","ends_with"]
    right: ColumnRef | ValueRef                 # {"column":"End_Date"} or {"value":"0"}
    value_type: Literal["number","date","text"]
    skip_blank: bool = True

class RangeRule(BaseRule):
    type: Literal["range"]; column: str; min: float | None = None; max: float | None = None; inclusive: bool = True

class ArithmeticRule(BaseRule):
    type: Literal["arithmetic"]; target: str; left: str
    op: Literal["add","sub","mul","div"]; right: str | float   # column name or constant
    tolerance_abs: float = 0.01; tolerance_rel: float = 0.0

class FormatRule(BaseRule):
    type: Literal["format"]; column: str
    preset: Literal["email","phone_in","phone_intl","url","pincode_in","custom"]; pattern: str | None = None

class UniqueRule(BaseRule):      type: Literal["unique"]; columns: list[str]      # composite allowed
class NotNullRule(BaseRule):     type: Literal["not_null"]; columns: list[str]
class AllowedValuesRule(BaseRule): type: Literal["allowed_values"]; column: str; values: list[str]; case_sensitive: bool = False
```
Every rule has a deterministic **plain-English summary** generator (used in the list, violation reasons and reports), e.g. `Total_Price should equal Quantity × Unit_Price (±0.01)`.

### 8.2 Evaluation (`rules/evaluator.py`) — **no `eval`/`exec` anywhere**
- Vectorised pandas/numpy with the same numeric/date parsers as the profiler (so "₹1,200" and "01/02/2026" are understood consistently; dates use the column's resolved day-first setting).
- Result: `RuleResult{rule_id, evaluated, violations, unevaluable, rids, passed}`. **Unevaluable** = the value could not be parsed for the comparison (e.g., `Age="twenty"` in a range rule). These are reported separately and **never silently counted as passing** (the UI shows "3 values couldn't be checked").
- Blank values are skipped (`skip_blank=True`) except in `not_null`; missing handling stays in the missing-value detector.
- Per-violation reason strings are generated lazily for the visible page: `"Row 14: End_Date (2025-01-02) is earlier than Start_Date (2025-03-04)."`
- Arithmetic tolerance: violation if `abs(actual − expected) > max(tolerance_abs, tolerance_rel·|expected|)`; division by zero → unevaluable.
- `format` presets: email `^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$`; `phone_in` `^(\+91[\-\s]?|0)?[6-9]\d{9}$` after removing spaces/dashes/brackets; `pincode_in` `^[1-9]\d{5}$`; `url` `^https?://[^\s/$.?#][^\s]*$`; `custom` → user regex: max length 200, compile-checked, reject nested quantifiers (`(a+)+`), apply to values truncated at 500 chars; prefer the `regex` library with a timeout if available.
- `unique` with blanks ignored; `allowed_values` compares trimmed values.

### 8.3 Rule API behaviour
CRUD per session; `POST /rules/test` evaluates an unsaved rule and returns counts + first 10 violations (used by the builder's live preview); `POST /rules/run` evaluates all enabled rules; results cached by `(head_seq, rules_hash)` and refreshed after every apply/undo. Rules persist for the session and can be exported/imported as JSON (`GET/PUT /rules/export|import`) — this is the "custom rule templates" extra.

### 8.4 Suggested rules (`rules/suggestions.py`) — shown in the Rules page, never enforced until accepted
Heuristic on column *names* **and** effective types:

| Column name pattern | Suggested rule |
|---|---|
| `age` | range 0–120 |
| `qty|quantity|units|count|stock` | range min 0 |
| `price|amount|total|cost|salary|fee` | range min 0 |
| `percent|pct|percentage` | range 0–100 |
| `rating|stars|score_?out_?of` | range 1–5 (editable) |
| `marks?|score` | range 0–100 (editable) |
| `email` | format preset email |
| `phone|mobile|contact` | format preset phone_in |
| `pin(code)?|zip|postal` | format preset pincode_in |
| `(start|from|begin|open|issue|order)\w*date` with a matching `(end|to|close|expiry|due|delivery|ship)\w*date` | compare `start ≤ end` (value_type date) |
| `total|line_total|amount` + `qty|quantity` + `unit_?price|price|rate` | arithmetic `total = qty × price` |
| ID-like (Section 6.1 pattern) with distinct ratio ≥ 0.9 | unique |
Each suggestion includes a **dry-run count** ("would flag 14 rows") from evaluating it; suggestions with 0 evaluable rows are hidden.

---

## 9. Verification, quality score, report, export

### 9.1 Definitions (put these definitions in the UI tooltips and in the report)
- **Finding** = a pair `(issue group key, rid)`. Column-level groups: one finding per affected cell/row; row-level groups (duplicates, identifier conflicts, cross-column rules): one finding per affected row.
- **Open finding** = a finding that is not dismissed.
- **Row quality (headline "Quality score")** = `100 × rows with zero open findings ÷ current rows`. Rounded to 1 decimal; never shown as 100.0 while any open finding exists.
- **Cell quality** = `100 × (1 − distinct cells touched by open findings ÷ (current rows × columns))` (row-level findings touch every cell of the row).
- **Rows retained** = `current rows ÷ original rows` (shown next to the score so deleting bad rows cannot silently inflate quality).

### 9.2 Verification algorithm (`verification/verify.py`)
1. **Before** = run detection on `original_df` with the *current* config and rules (cached by `(config_hash, rules_hash)`).
2. **After** = run detection on the current `df` (same config and rules) + dismissals.
3. For each group key, compare finding sets (`before_rids` vs `after_rids`, numpy set ops):
   - `resolved` = in before, not in after (value fixed, or row removed), and not dismissed
   - `dismissed` = open-in-before but marked dismissed by the user ("reviewed and valid")
   - `remaining` = in before and still open in after
   - `new` = in after, not in before ("revealed by cleaning" when the group type is `duplicate_row`/`duplicate_id`/`similar_values` and a preceding operation touched that column; otherwise "introduced")
4. Counts by type, by group, plus rules table, action counters from `operations` + `decisions` (applied / rejected / skipped / undone), cells changed, rows removed.
5. Persist `verified_seq = head_seq`, `verified_at`; set `stage="verified"`.
6. **Verdict:** `clean` iff `verified_seq == head_seq` AND open findings == 0 AND all enabled rules pass; `improved` if after-open < before-open; `not_improved` otherwise; `stale` when `verified_seq != head_seq`.
7. The UI MUST call the data "clean" only for verdict `clean`. "Detected ≠ corrected": the table always shows both columns.

```jsonc
// POST /sessions/{id}/verify → VerificationResult (shape)
{
  "verified_at": "...", "head_seq": 7, "verdict": "improved",
  "before": {"rows":5000,"open_findings":412,"quality_score":71.2,"cell_quality":98.9,"rules_passing":2,"rules_total":5},
  "after":  {"rows":4968,"open_findings":23, "quality_score":97.8,"cell_quality":99.9,"rules_passing":5,"rules_total":5},
  "rows_removed": 32, "rows_retained_pct": 99.4,
  "by_type": [{"type":"missing_value","before":120,"resolved":115,"dismissed":0,"remaining":5,"new":0}, ...],
  "groups": [{"key":"outlier:iqr:Quantity","status":"remaining","before":4,"after":4}, ...],
  "rules": [{"id":"...","name":"...","violations_before":14,"violations_after":0,"unevaluable_after":0}],
  "actions": {"applied":7,"rejected":2,"skipped":1,"undone":1,"cells_changed":1480,"rows_deleted":32},
  "unresolved": [ ...issue group summaries with evidence... ]
}
```

### 9.3 Report (`reporting/report.py`)
- **HTML (self-contained, inline CSS using the pastel tokens, no external requests, print-friendly):** header (file, generated time, app version), verdict banner, KPIs (before → after), issues table (Detected / Corrected / Dismissed / Remaining / New), rules table, actions summary, **full operation log** (seq, time, title, params, counts, status), unresolved issues with up to 5 examples each, before/after column profile summary, **methodology** (all thresholds from `DetectionConfig`, date assumptions, outlier method) and the note "Outliers are suspicious values, not necessarily errors."
- **JSON:** the same data, machine-readable (`report_schema_version: 1`).
- Generated by Jinja2 from the `VerificationResult`; if verification is stale the report runs a fresh verification first and states its timestamp.

### 9.4 Export (`reporting/exporter.py`)
- **Cleaned CSV:** current `df` in original column order and original row order (deleted rows omitted), blanks stay blank, `csv.QUOTE_MINIMAL`, options `delimiter` (default = original), `encoding` (`utf-8` default / `utf-8-sig` for Excel), `line_ending` (`\n` default / `\r\n`), `escape_formulas` (default **off**; when on, prefix cells starting with `= + - @` with `'` and tell the user it changes those cells). Round-trip test: re-ingesting the export yields an identical DataFrame.
- **History JSON:** array of operations (seq, kind, title, params, status, timestamps, counts). Option `include_patches=true` adds cell diffs. **History CSV:** one row per cell change (`op_seq, op_kind, status, created_at, row_number, column, old_value, new_value`) + one row per deleted row.
- **Bundle ZIP:** `{stem}_cleaned.csv`, `{stem}_report.html`, `{stem}_report.json`, `{stem}_history.json`, `{stem}_history.csv`, `{stem}_rules.json`, `README.txt`. Streamed with `StreamingResponse`; header `Content-Disposition: attachment; filename*=UTF-8''…` (sanitise filenames).
- After a successful export set `stage="exported"`.

---

## 10. LLM layer (Groq primary → Ollama fallback → built-in templates)

### 10.1 Principles (MUST)
1. **The LLM never decides whether a value is correct and never changes data.** It explains, summarises, and *suggests*; all suggestions are shown as advisory cards and must be accepted by the user through the normal proposal flow.
2. **Every LLM feature has a deterministic fallback** (`source: "template"`). With no keys and no Ollama, the app is fully functional.
3. **Privacy:** only column names, aggregate stats and a handful of example values (≤ 20 per request) are sent; never whole files or rows. With "Redact emails/phone numbers" on (default), values matching email/phone patterns are replaced by `<email>` / `<phone>` before sending. "Ollama only" and "Built-in only" modes never contact Groq.
4. Keys live only in backend env vars. The frontend never sees them. Never log prompts' example values at INFO level.

### 10.2 Features that use the LLM
| Feature | Endpoint | Input sent | Output (validated) | Template fallback |
|---|---|---|---|---|
| Explain an issue | `POST /ai/explain` | issue type, column, counts, ≤ 5 redacted examples, stats | `{summary, why_it_matters, suggested_action}` (≤ 80 words total) | per-type template filled with the same numbers |
| Review a similar-value cluster | `POST /ai/review-cluster` | the cluster's values + counts, column name, ≤ 3 other column names | `{verdict: "likely_same"|"likely_different"|"unsure", confidence: 0–1, reasoning}` | "Spelling similarity is 91%. We can't tell if they are the same — please review." |
| Natural-language → rule | `POST /rules/from-text` | the sentence + list of column names with types | a `Rule` JSON object (validated against the Pydantic union; columns MUST exist) | deterministic parser for common patterns (`X must be between A and B`, `X should be greater than Y`, `X = Y * Z`, `X must be unique`, `X is required`); otherwise error "Couldn't understand — try the rule builder" |
| Report summary | `POST /ai/summarize` | verification numbers only (no cell values) | 3–5 sentence executive summary | templated paragraph from the numbers |

### 10.3 Provider chain (`llm/service.py`, `llm/client.py`)
```
LLM_ENABLED=true? → mode from request/session setting:
  "auto"        : try Groq → on failure try Ollama → on failure template
  "ollama_only" : try Ollama → template
  "off"         : template
```
- **Groq** (OpenAI-compatible): `POST {GROQ_BASE_URL}/chat/completions` with `Authorization: Bearer $GROQ_API_KEY`, base URL `https://api.groq.com/openai/v1`. Body: `model`, `messages`, `temperature: 0.1`, `max_tokens: 500`, `response_format: {"type":"json_object"}` (the prompt MUST also contain the word "JSON"). Default model **`llama-3.3-70b-versatile`**; cheap/fast alternative **`llama-3.1-8b-instant`** (both current Groq production models at time of writing — **do not hardcode; read from env** and expose `GET /ai/models` which proxies `GET {GROQ_BASE_URL}/models` so the Settings page can show what is currently available).
- **Ollama:** `POST {OLLAMA_BASE_URL}/api/chat` with `{"model": OLLAMA_MODEL, "messages": [...], "stream": false, "format": "json", "options": {"temperature": 0.1, "num_predict": 500}}`. Default `OLLAMA_BASE_URL=http://localhost:11434` (in docker-compose: `http://ollama:11434`), default model **`llama3.2:3b`** (small, runs on a laptop CPU; `qwen2.5:7b` is a stronger option if RAM allows). `GET {OLLAMA_BASE_URL}/api/tags` is used for availability/model-list checks.
- **Timeouts/retries:** connect 3s, total `LLM_TIMEOUT_SECONDS` (default 12). Retry **once** on `429`/`5xx`/timeout with jittered backoff (respect `Retry-After`, cap 2s). `401/403` → mark Groq `misconfigured` (don't retry, show clear Settings message).
- **Circuit breaker per provider:** after 3 consecutive failures, skip the provider for 60s (log + notification "Groq unavailable — used Ollama").
- **Response contract:** every AI endpoint returns `{ "source": "groq"|"ollama"|"template", "model": "...", "latency_ms": 412, "fallback_reason": null|"groq_timeout"|"groq_rate_limited"|..., "data": {...} }`. The UI shows a small source badge (`Groq`, `Ollama`, `Built-in`) next to every AI-generated text.
- **Validation:** parse JSON (strip ```json fences), validate with Pydantic; one repair retry (re-prompt "Return only valid JSON matching this schema"); on failure fall to the next provider/template. For rules: after validation, verify all referenced columns exist and regexes pass the safety checks (Section 8.2).
- **Cache:** `ai_cache` keyed by `sha256(prompt_kind + canonical_inputs + model)`; TTL 24h; prevents repeated calls and rate-limit issues.
- **Rate limit:** 20 AI requests/min/session (slowapi) so a free Groq key is not exhausted.

### 10.4 Prompts (`llm/prompts.py`) — system prompt skeleton
```
You are a careful data-quality assistant inside a CSV cleaning tool.
Rules: use ONLY the facts provided. Never invent values. Never claim a value is definitely wrong.
Outliers are "suspicious", not "errors". Answer in plain English for a non-programmer.
Return ONLY a JSON object matching this schema: {schema}. No markdown, no extra text.
```
User message = compact JSON of the redacted facts. Keep temperature low (0.1).

### 10.5 Status & test endpoints
`GET /ai/status` → `{ "mode": "auto", "groq": {"configured": true, "reachable": true, "model": "...", "latency_ms": 180, "last_error": null}, "ollama": {"reachable": false, "model": "llama3.2:3b", "model_installed": false, "last_error": "connection refused"}, "effective_chain": ["groq","template"] }`; `POST /ai/test {provider}` sends a 1-token ping and returns the result. Settings page renders both as status cards with a "Test connection" button and copy-paste help: *"Get a free Groq key at console.groq.com → API Keys"* and *"Install Ollama, then run `ollama pull llama3.2:3b`"*.

---

## 11. REST API contract

Base path `/api/v1`. JSON everywhere except uploads (multipart) and exports. All timestamps ISO-8601 UTC. FastAPI auto-generates OpenAPI at `/api/v1/openapi.json`; the frontend types are generated from it (`npm run gen:api`).

### 11.1 Error envelope (MUST be used for every non-2xx)
```json
{ "error": { "code": "PREVIEW_STALE", "message": "Your data changed since this preview was made.", "hint": "Review the refreshed preview and try again.", "details": {} } }
```
Codes: `FILE_TOO_LARGE`, `EMPTY_FILE`, `NO_DATA_ROWS`, `NOT_TEXT`, `PARSE_FAILED`, `SESSION_NOT_FOUND`, `SESSION_EXPIRED`, `COLUMN_NOT_FOUND`, `VALIDATION_ERROR`, `PREVIEW_STALE`, `STATE_MISMATCH`, `STATE_CORRUPT`, `NOTHING_TO_UNDO`, `NOTHING_TO_REDO`, `RULE_INVALID`, `RATE_LIMITED`, `AI_UNAVAILABLE` (never fatal; endpoints return `source:"template"` instead), `INTERNAL`. Map exceptions centrally in `errors.py`; never leak stack traces.

### 11.2 Endpoints

| Method & path | Purpose | Notes |
|---|---|---|
| `GET /health` | liveness | `{status:"ok", version}` — used by hosting health checks |
| `GET /version` | version + build info | |
| **Sessions** | | |
| `POST /sessions` | upload CSV (multipart `file`, optional `delimiter`, `encoding`, `has_header`) | returns `SessionCreated{session_id, filename, parse_report, dataset, profile_summary, issue_summary}`; runs profile + detection synchronously (≤ 10 s target); for large files return `202` + poll `GET /sessions/{id}/status` |
| `POST /sessions/sample` | `{sample:"students"|"sales"}` | same response |
| `GET /sessions/summary?ids=a,b` | cards for "recent datasets" | missing/expired ids omitted |
| `GET /sessions/{id}` | session meta (stage, head_seq, verified flags, counts) | |
| `GET /sessions/{id}/status` | processing status | `processing|ready|failed` |
| `POST /sessions/{id}/reparse` | re-read original with new parse options | resets ops (confirm in UI) |
| `PUT /sessions/{id}/settings` | detection config, type overrides, unique/locked columns | triggers re-detect |
| `DELETE /sessions/{id}` | purge | |
| `GET /sessions/{id}/dashboard` | aggregate for Dashboard (stats, issue-type counts, top columns, recent ops, quick-win count, next step) | |
| **Data & profile** | | |
| `GET /sessions/{id}/rows` | `view=current|original`, `offset`, `limit≤500`, `sort`, `dir`, `q`, `only_issues`, `column_filters` | returns rows with `rid`, cell values, per-cell `issue_keys` |
| `GET /sessions/{id}/profile` | `view=original|current` | dataset + per-column profile |
| `PUT /sessions/{id}/columns/{name}/type` | override type | |
| `POST /sessions/{id}/cells` | `{rid, column, value}` manual edit | creates op |
| `GET /sessions/{id}/search?q=` | cells/columns/issues/rules/history search | ≤ 20 per group |
| **Issues** | | |
| `GET /sessions/{id}/issues` | filters `type,column,status,severity,q` | list of `IssueGroup` (rids truncated; `cells`, `evidence`) |
| `GET /sessions/{id}/issues/{key}/rows` | paged affected rows | key URL-encoded |
| `POST /sessions/{id}/issues/{key}/dismiss` | `{reason?}` | stores rids |
| `POST /sessions/{id}/issues/{key}/reopen` | | |
| **Proposals** | | |
| `GET /sessions/{id}/proposals` | list (`status`, `risk`, `column`) | |
| `GET /sessions/{id}/proposals/{key}` | detail + params schema + alternatives | |
| `GET /sessions/{id}/proposals/{key}/changes` | paged `Change[]` (`offset,limit,only_uncertain`) | |
| `PATCH /sessions/{id}/proposals/{key}` | `{params}` → recomputed preview summary | |
| `PATCH /sessions/{id}/proposals/{key}/changes/{change_id}` | `{override}` edit proposed value | validated vs column type |
| `POST /sessions/{id}/proposals/{key}/apply` | `{change_ids?: string[]|null, overrides?: {}, confirm_destructive?: bool}` | `null` = all currently selected defaults; returns `OperationResult` + refreshed summary; `409 PREVIEW_STALE` if needed |
| `POST /sessions/{id}/proposals/{key}/reject` | `{reason?}` | |
| `POST /sessions/{id}/proposals/{key}/skip` | | |
| `POST /sessions/{id}/proposals/{key}/reopen` | | |
| `POST /sessions/{id}/proposals/apply-safe` | applies all `safe` proposals as one batch | returns list of op ids |
| **History** | | |
| `GET /sessions/{id}/history` | ops (+ counters applied/rejected/skipped/undone) | |
| `GET /sessions/{id}/history/{op_id}` | detail with paged cell diffs | |
| `POST /sessions/{id}/undo` / `POST /sessions/{id}/redo` | latest op / batch | `NOTHING_TO_UNDO` etc. |
| **Rules** | | |
| `GET/POST /sessions/{id}/rules` · `PUT/DELETE /sessions/{id}/rules/{rid}` | CRUD | validated by Pydantic union |
| `POST /sessions/{id}/rules/test` | evaluate unsaved rule | counts + first 10 |
| `POST /sessions/{id}/rules/run` | evaluate all enabled | `RuleResult[]` |
| `GET /sessions/{id}/rules/{rid}/violations` | paged violations with reasons + unevaluable tab | |
| `GET /sessions/{id}/rules/suggestions` | Section 8.4 | |
| `POST /sessions/{id}/rules/from-text` | NL → rule (AI/template) | |
| `GET /sessions/{id}/rules/export` · `PUT /sessions/{id}/rules/import` | JSON | |
| **Verification & export** | | |
| `POST /sessions/{id}/verify` | Section 9.2 | |
| `GET /sessions/{id}/verification` | latest result + `stale` flag | |
| `GET /sessions/{id}/report?format=html|json` | report | |
| `GET /sessions/{id}/export/csv` | `delimiter,encoding,line_ending,escape_formulas` | streamed |
| `GET /sessions/{id}/export/history?format=json|csv` | | |
| `GET /sessions/{id}/export/bundle` | ZIP | |
| **AI** | | |
| `GET /ai/status` · `GET /ai/models` · `POST /ai/test` | Section 10.5 | |
| `POST /sessions/{id}/ai/explain` · `/ai/review-cluster` · `/ai/summarize` | Section 10.2 | rate-limited |

### 11.3 Key response shapes (TypeScript view; derive from Pydantic)
```ts
type Risk = 'safe'|'review'|'destructive';
interface DashboardDTO {
  dataset: { filename: string; rows: number; rowsOriginal: number; columns: number };
  stats: { rows: number; openIssues: number; qualityScore: number; qualityDelta: number;
           changesApplied: number; changesUndone: number; proposalsRejected: number; resolvedIssues: number };
  issuesByType: { type: IssueType; detected: number; remaining: number; resolved: number }[];
  issuesByColumn: { column: string; open: number }[];          // top 4 + Other computed client-side
  recentOps: OperationSummary[];                               // last 3
  quickWins: { count: number; cells: number; proposals: { key: string; title: string; cells: number }[] };
  nextStep: { stage: Stage; headline: string; subline: string; cta: { label: string; route: string; action?: string } };
}
interface OperationResult { op: OperationSummary; session: SessionMeta; changed: { cells: number; rows: number; deleted: number } }
```

### 11.4 Cross-cutting API requirements
- Pagination everywhere (`offset/limit`, return `total`). Never return > 500 rows or 2,000 changes per call.
- Mutations return the updated `SessionMeta` (`head_seq`, `stage`, counts) so the client can invalidate precisely.
- `ETag`/`If-None-Match` on `GET /rows` and `GET /issues` keyed by `(head_seq, config_hash, rules_hash)`.
- CORS: allow `FRONTEND_ORIGIN` only (dev: `http://localhost:5173`).
- Request size limit enforced by reading the upload in chunks (stop at limit).

---

## 12. Frontend implementation notes

- **Data fetching:** one `api/client.ts` (axios or `fetch` wrapper) with envelope-aware errors → `ApiError{code,message,hint}`. Hooks per resource (`useDashboard`, `useIssues`, `useProposals`, `useProposalChanges`, `useHistory`, `useRules`, `useVerification`, …). Query keys always include `sessionId` and `headSeq` so stale data can't be shown after changes.
- **Mutations:** optimistic UI only for cheap toggles (rule enabled, selection checkboxes). Apply/undo wait for the server, then `invalidateQueries` for the list in Section 3.12. Show toast with **Undo** action after apply.
- **Active session:** Zustand `session` store (`sessionId`, `recentIds[]` persisted to `localStorage`). On boot, validate with `GET /sessions/summary`; if expired show "That dataset expired — upload again".
- **Selection state in the explorer:** held locally per proposal key (`Map<changeId, boolean>`), initialised from the server's `selected` defaults; sent as `change_ids` on apply. Overrides sent as `overrides`.
- **Virtualised tables:** rows fetched in pages of 200 via `useInfiniteQuery`; row height fixed 48px; placeholder skeleton rows while loading.
- **Charts:** wrapper components `PillBarChart`, `DonutChart` that take `{label,value,color}[]` and apply Section 2.6 styling; provide `aria-label` and an sr-only table.
- **Keyboard shortcuts:** central `useHotkeys` registry (Section 2.10 + `Ctrl/Cmd+K` search + `g d`/`g i`/`g s` navigation optional).
- **Forms:** `react-hook-form` + `zod`; rule builder forms are generated from rule type metadata (column pickers filtered by effective type).
- **Formatting helpers:** `formatNumber`, `formatPercent`, `relativeTime`, `visibleWhitespace(str)` (replaces leading/trailing/double spaces with `·`, tabs with `⇥`, NBSP with `⍽`) — used in every grid and evidence chip.
- **Greeting:** `lib/greeting.ts` returns `{text:"Good Morning", emoji:"☀️"}` (05–11:59), Afternoon `🌤️` (12–16:59), Evening `🌙` (17–04:59).
- **Performance budget:** initial JS ≤ 350 KB gzip (route-level code splitting with `React.lazy`; Recharts and the grid in separate chunks).
- **Environment:** `VITE_API_BASE` (default `/api/v1`; Vite dev proxy to `http://localhost:8000`).

---

## 13. Sample datasets and benchmark / evaluation

### 13.1 Bundled samples (`backend/app/samples/generate_samples.py`, deterministic with `random.Random(42)`)
The generator writes `students_messy.csv` (≈ 600 rows) and `sales_messy.csv` (≈ 1,200 rows) **and** a `*.truth.json` manifest listing every injected error `{id, type, rid, column, clean_value, dirty_value, correct_fix}`. Commit the generated CSVs (small) so the app works offline.

**Students columns:** `Student_ID, Name, Email, City, Age, Math, Science, English, Total_Marks, Enrollment_Date, Graduation_Date, Passed`
**Injected:** blank ages/marks; `"twenty"`, `"nineteen"` in `Age`; `N/A`/`-` placeholders; exact duplicate rows; repeated `Student_ID`s (some identical records, some different); `" Jaipur "`, `"jaipur"`, `"JAIPUR"`, `"Japur"`, `"Jaipur "`; mixed date formats (`25/10/2026`, `2026-10-25`, `25 Oct 2026`); marks `105` (limit 100); one age `212`; `Total_Marks ≠ Math+Science+English` for some rows; `Graduation_Date` before `Enrollment_Date`; invalid emails; one mark of `9999` (outlier); Yes/No/Y/true variants in `Passed`.

**Sales columns:** `Order_ID, Customer, Region, Product, Quantity, Unit_Price, Total_Price, Order_Date, Ship_Date, Status`
**Injected:** negative quantities; quantity `100000` (outlier); impossible dates (`31/02/2026`); `Total_Price ≠ Quantity × Unit_Price`; `Ship_Date` before `Order_Date`; prices like `"₹1,200"`, `"1200.00"`, `"1,200"`; `"Rahul Sharma"` vs `"Rahul Sharmaa"`; region case variants (`north`, `North`, `NORTH `); duplicate `Order_ID`s; blank `Status`.

### 13.2 Benchmark harness (`backend/benchmarks/`)
- `inject_errors.py`: takes a clean synthetic table and a spec `{type: count}` (default 100 total errors across types, seed fixed), returns `(dirty_df, manifest)`.
- `baseline.py`: **Baseline A — naive auto-clean** (no review): trim, `drop_duplicates`, fill numeric NaN with median, title-case text columns, `pd.to_datetime(errors="coerce")`, drop |z| > 3 rows. Applies everything automatically.
- `run_benchmark.py` runs three arms on the same dirty data:
  - **A. Naive baseline** (above).
  - **B. CSV Rescue, default selections, no human review** (accept every proposal's default-selected changes, including `review`).
  - **C. CSV Rescue + simulated reviewer** (accepts a change iff its `after` equals the manifest's `clean_value`; rejects the rest) — label this clearly as an *upper bound for a careful human*, not a real human result.
- **Metrics** (per issue type and macro-average), definitions MUST match the proposal:
  - *Detection precision* = flagged findings that match a manifest error ÷ flagged findings. *Recall* = manifest errors flagged ÷ manifest errors. Match on `(type, rid, column)` (row-level types on `rid`).
  - *Correction accuracy* = applied changes on injected-error cells whose final value equals `clean_value` ÷ applied changes on injected-error cells.
  - *False-correction rate* = cells that were originally **valid** (not in manifest) whose value changed ÷ all originally valid cells that were touched by any proposal/baseline step. Also report the count of *valid rows deleted*.
  - *Remaining violations* = manifest errors whose cell value still differs from `clean_value` (or whose row still exists, for duplicates) after cleaning.
  - *Processing time* = ms for ingest+profile, detection, and apply-all (per arm), on 10k and 100k-row synthetic tables.
- Outputs `benchmarks/results/benchmark_{timestamp}.json|md` and `latest.json`. The markdown table is pasted into the README.
- **In-app:** Reports page has a **Benchmark** tab: `GET /benchmark/latest` renders the table + a bar chart (pill style), and `POST /benchmark/run` (background task, ≤ 60 s, rate limited) re-runs it on the bundled synthetic sets. Add both endpoints to the API.
- Acceptance targets (tune if needed, but record real numbers honestly): detection recall ≥ 0.90 and precision ≥ 0.85 macro on the bundled manifests; false-correction rate for arm C = 0; arm B false-correction rate lower than arm A.

---

## 14. Testing strategy

| Level | Tooling | Must cover |
|---|---|---|
| Backend unit | `pytest` | ingest (encodings, delimiters, BOM, ragged rows, duplicate/blank headers, empty/binary file); type inference; dates (ambiguity, impossible dates, mixed formats); number parsing (₹, commas, %, parentheses); `words_to_number`; every detector with golden fixtures; every action's `build_changes`; rule evaluator for all 7 rule types; verification arithmetic; quality score; exporter; redaction; LLM provider chain with `httpx.MockTransport` (Groq 200, Groq 429 → Ollama 200, both down → template, malformed JSON → repair → fallback) |
| Property tests | `hypothesis` | (1) `apply(op)` then `undo` returns the **identical state hash** for random patches incl. row deletions; (2) `trim_whitespace` is idempotent; (3) export → re-ingest round-trips for random strings with commas/quotes/newlines/unicode; (4) detection is deterministic (same input → same group keys and rids); (5) no action ever changes cells outside its declared scope |
| API tests | FastAPI `TestClient` | full happy path; every error code in 11.1; `409 PREVIEW_STALE`; undo/redo/batch undo; dismissals; settings change re-detects; session expiry; upload limits |
| Frontend unit | `vitest` + Testing Library | `visibleWhitespace`, greeting, formatters, change-selection reducer, diff cell rendering, rule-builder validation, chart wrappers render with data/empty state |
| Component/visual | Playwright screenshot of `/__kit` and Dashboard at 1440×1000 and 390×844 | compare against the reference checklist (Phase 1) |
| E2E | Playwright | upload sample → profile → issues → studio → apply safe → accept a review proposal → reject one → undo → redo → add rule → verify → export CSV/report/ZIP → delete dataset. Also: AI disabled path, AI fallback path (mock Groq failing), parse-error file |
| Benchmark | `run_benchmark.py` in CI nightly | numbers recorded in artifacts |

**Golden examples that MUST pass (from the project brief):**
| Input | Expected |
|---|---|
| City column: `" Jaipur "`, `"Jaipur"` | whitespace group; proposal trim → `"Jaipur"` (safe) |
| `"jaipur"` vs `"Jaipur"` | case-variant group; canonical `"Jaipur"` (safe) |
| `"Japur"` among 90% `"Jaipur"` | similar-values group; change unchecked, review, confidence ≈ 0.91; **never in apply-all-safe** |
| `Age = "twenty"` in numeric column | `invalid_numeric` error; proposal `20`, review |
| `Rating = 8` with rule range 1–5 | `invalid_value` violation with reason text |
| Quantity `100000` with others 1–20 | outlier (info), card says "Suspicious, not necessarily wrong", no default delete |
| `25/10/2026` and `2026-10-25` in same column | `date_mixed` group; unambiguous (25 > 12 ⇒ day-first) → safe |
| `03/04/2026` only (no disambiguating value) | proposal is **review** with day-first assumption banner |
| `Start_Date > End_Date` rule | violation reason lists both values |
| `Total_Price ≠ Quantity × Unit_Price` (tolerance 0.01) | arithmetic violation; proposal `recompute_target` review |
| Same `Student_ID` in two rows | `duplicate_id` error, never auto-resolved |
| Two identical rows | `duplicate_row`; remove copies = destructive, requires confirm |

**Coverage gates in CI:** backend ≥ 85% line coverage on `detection/`, `cleaning/`, `core/ops.py`, `rules/`, `verification/`; frontend ≥ 70% on `lib/` and `components/studio/`.

---

## 15. Security, privacy, performance, limits

### 15.1 Limits (all configurable via env, Appendix B)
| Limit | Default |
|---|---|
| Upload size | 25 MB |
| Rows / columns | 250,000 / 200 |
| Max cell length | 32,768 chars (longer → truncated in preview, flagged in parse report) |
| Session TTL | 24 h since last activity |
| Max sessions held in memory | 8 |
| Changes per preview page | 2,000 |
| AI requests | 20 / min / session |
| API rate limit | 120 / min / IP (uploads 10 / min / IP) |

### 15.2 Security checklist (MUST)
- Validate uploads: extension in `.csv/.tsv/.txt`, reject files with NUL bytes unless UTF-16 detected, enforce size while streaming. Store under a server-generated name; never use the client filename in paths (sanitise for display and download names).
- Treat every cell as **untrusted text**: no `dangerouslySetInnerHTML`; Jinja2 **autoescape on** for the HTML report; escape values in evidence/tooltips.
- CSV formula injection: documented option `escape_formulas` on export (default off to avoid altering data) with a visible warning in the UI when a cell begins with `= + - @`.
- Custom regex safety (Section 8.2); no `eval`/`exec`; no unpickling of anything not server-generated.
- Security headers via middleware: `Content-Security-Policy: default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy` minimal. HTTPS is provided by the host (add HSTS in production).
- CORS restricted to `FRONTEND_ORIGIN`. Session id is a bearer secret — send in the URL path only over HTTPS; never log full ids at INFO (log first 6 chars).
- Secrets only in env; `.env` in `.gitignore`; `.env.example` committed. CI runs `pip-audit` and `npm audit --omit=dev` (warn, don't block).
- Logging: structured JSON, request id, no cell values at INFO.

### 15.3 Privacy
- Data stays on the server's disk for ≤ 24 h, deleted on request. LLM calls follow Section 10.1(3). Settings page and README explain this in plain language. "Local-only mode" (Ollama only or Built-in only) guarantees no data leaves the machine.

### 15.4 Performance targets (2 vCPU / 2 GB)
| Operation | Target |
|---|---|
| Upload + parse + profile + detect, 100k rows × 20 cols | ≤ 10 s |
| Re-detect after apply/undo (cached typed views) | ≤ 3 s |
| Preview page of 200 rows/changes | ≤ 300 ms |
| Apply a 50k-cell proposal | ≤ 2 s |
| Verification | ≤ 8 s (before-detection cached) |
| UI grid scroll | 60 fps on 100k rows (virtualised) |
Use vectorised pandas; categorical caching of per-column normalised strings; avoid `apply(axis=1)`; cap evidence generation.

---

## 16. Deployment (from local to production)

### 16.1 Local development
```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp ../.env.example ../.env          # add GROQ_API_KEY if you have one (optional)
uvicorn app.main:app --reload --port 8000
# frontend (new terminal)
cd frontend && npm ci && npm run dev    # http://localhost:5173 (proxy /api → :8000)
# optional local LLM fallback
ollama pull llama3.2:3b && ollama serve
```
`Makefile` targets: `make dev`, `make test`, `make lint`, `make build`, `make docker`, `make gen-api`, `make bench`, `make samples`, `make smoke`.

### 16.2 Dockerfile (single image: API + built frontend)
```dockerfile
# ---------- stage 1: build frontend ----------
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- stage 2: runtime ----------
FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /srv
RUN useradd -m -u 10001 appuser
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
COPY backend/app ./app
COPY --from=web /web/dist ./static
ENV STATIC_DIR=/srv/static DATA_DIR=/data
RUN mkdir -p /data && chown -R appuser:appuser /data
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD ["python","-m","app.healthcheck"]
CMD ["sh","-c","uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
```
`app/healthcheck.py` requests `http://127.0.0.1:$PORT/api/v1/health` and exits non-zero on failure. `main.py` mounts `StaticFiles(STATIC_DIR, html=True)` **after** the API routers and falls back to `index.html` for unknown non-`/api` paths (SPA routing).

### 16.3 docker-compose (local, optional Ollama)
```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    env_file: .env
    environment:
      OLLAMA_BASE_URL: http://ollama:11434
    volumes: ["csvrescue-data:/data"]
  ollama:
    image: ollama/ollama:latest
    profiles: ["ollama"]
    ports: ["11434:11434"]
    volumes: ["ollama-models:/root/.ollama"]
  ollama-pull:
    image: ollama/ollama:latest
    profiles: ["ollama"]
    depends_on: [ollama]
    environment: { OLLAMA_HOST: "http://ollama:11434" }
    entrypoint: ["ollama","pull","llama3.2:3b"]
volumes: { csvrescue-data: {}, ollama-models: {} }
```
Run: `docker compose up --build` (Groq/built-in) or `docker compose --profile ollama up --build` (adds local Ollama).

### 16.4 Production (recommended: Render, single Docker web service)
`render.yaml`:
```yaml
services:
  - type: web
    name: csv-rescue
    runtime: docker
    plan: free              # use "starter" + a persistent disk if you want sessions to survive restarts
    healthCheckPath: /api/v1/health
    autoDeploy: true
    envVars:
      - { key: GROQ_API_KEY, sync: false }
      - { key: GROQ_MODEL, value: llama-3.3-70b-versatile }
      - { key: LLM_PROVIDER_ORDER, value: "groq,ollama" }
      - { key: OLLAMA_BASE_URL, value: "" }          # empty = Ollama disabled in the cloud
      - { key: DATA_DIR, value: /tmp/csvrescue-data }
      - { key: FRONTEND_ORIGIN, value: "https://csv-rescue.onrender.com" }
      - { key: MAX_UPLOAD_MB, value: "25" }
      - { key: SESSION_TTL_HOURS, value: "24" }
```
**Steps:** push to GitHub → Render "New → Blueprint" → pick the repo → set `GROQ_API_KEY` in the dashboard (optional) → deploy → open the URL → run `scripts/smoke.sh https://<your-url>`.
**Notes:** free tier spins down when idle (first request is slow; the UI shows a friendly "waking up the server…" state when `/health` takes > 3 s) and has an ephemeral disk (sessions are lost on redeploy — fine because TTL is 24 h). Equivalent alternatives: **Railway** (detects the Dockerfile), **Fly.io** (`fly launch`, add a volume at `/data`), or a **split deploy** (frontend on Vercel/Netlify with `VITE_API_BASE=https://api…/api/v1`, backend on Render; set `FRONTEND_ORIGIN` accordingly).
**Ollama in production:** free PaaS tiers can't run it. If you want the fallback online, run Ollama on a small VPS (≥ 4 GB RAM), put it behind a private network/auth proxy, and set `OLLAMA_BASE_URL`. Otherwise leave it empty — the chain is Groq → built-in templates and everything still works.

### 16.5 CI/CD (`.github/workflows/ci.yml`)
Jobs on every PR and on `main`: (1) **backend**: setup Python 3.12, install, `ruff check`, `ruff format --check`, `pytest --cov`; (2) **frontend**: Node 20, `npm ci`, `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`; (3) **api-types**: `npm run gen:api` then `git diff --exit-code` (fails if generated types drifted); (4) **e2e**: build image, start container, run Playwright; (5) **audit** (non-blocking). Deploy: Render auto-deploys `main` after CI passes (use Render's "wait for CI" setting) — no secrets are stored in GitHub except optional `RENDER_DEPLOY_HOOK`.

### 16.6 Post-deploy smoke test (`scripts/smoke.sh`)
`GET /api/v1/health` → `POST /sessions/sample` (students) → `GET /issues` has ≥ 1 group → `POST /proposals/apply-safe` → `POST /verify` verdict ∈ {improved, clean} → `GET /export/csv` returns > 0 bytes → `DELETE /sessions/{id}` returns 204. Exit non-zero on any failure.

### 16.7 Release checklist
Version bump in `backend/app/__init__.py` and `frontend/package.json`; README updated (screenshots, benchmark table, how to get a Groq key, how to run Ollama); tag `v1.0.0`; confirm `.env` is not committed; confirm the live site passes the smoke test and the Phase-1 visual checklist.

---

## 17. Build phases (paste one prompt per Cursor chat)

> General instruction for every phase: *Read the cited sections of `@docs/BUILD_SPEC.md`. Implement only this phase. Write tests alongside the code. Run `make lint test` and fix everything. Update `docs/DECISIONS.md` for any ambiguity. Commit with message `phase N: …`. Stop and summarise what was done and what to check manually.*

### Phase 0 — Scaffolding and tooling
**Prompt:** "Execute Phase 0 of `@docs/BUILD_SPEC.md`: create the repo layout (4.2), FastAPI app with config (Appendix B), error envelope (11.1), SQLite init (5.3), `/api/v1/health`, static serving + SPA fallback, structured logging; Vite + React + TypeScript strict + Tailwind + Nunito + tokens (2.2) + router with placeholder pages; ESLint/Prettier/Ruff; Vitest + pytest smoke tests; Makefile; `.env.example`; `.gitignore`; GitHub Actions CI (16.5); Dockerfile + compose (16.2–16.3)."
**Acceptance:** `make dev` starts both servers; `GET /api/v1/health` → ok; `npm run build` and `docker build .` succeed; `make lint test` green; CI file passes `actionlint`-style review.

### Phase 1 — Design system, app shell, and the static Dashboard (visual fidelity phase)
**Prompt:** "Attach `@dashboard-reference.png`. Execute Phase 1: implement Section 2 completely — tokens, all clay components (2.5), chart wrappers (2.6), grid style (2.7), `ClayImage` with SVG/CSS fallbacks (2.8), motion (2.9), accessibility (2.10), the app shell (sidebar, header, routing, bottom-tab mobile nav), first-run name modal, and the Dashboard page built with **mock data** that mirrors the table in 3.2 one-to-one. Add a dev-only `/__kit` page showing every component in every state. Take Playwright screenshots at 1440×1000, 1024×800 and 390×844 and compare them with the reference."
**Visual acceptance checklist (every item MUST be true):**
1. Lavender gradient page background and a cream shell with ≈ 44px radius and soft purple shadow.
2. Floating periwinkle sidebar with large avatar ring, "Hi, {name}! 👋", filled white icons, **cream pill active item**, pink promo card at the bottom.
3. Header: bold indigo title, embossed cream search pill, round bell with badge, round purple avatar button.
4. Hero banner: purple gradient, character overflowing the top edge (or its fallback), headline, muted subline, saturated pill CTA with icon, plant on the right, darker bottom ledge.
5. Four tinted stat cards (lavender, pink, yellow, blue) each with a glossy rounded-square 3D icon badge, label, big number, green delta.
6. Pill-shaped multicolour bars with a dropdown chip; dotted light gridlines; no axis lines.
7. Donut with pastel segments + legend (dot, label, right-aligned %).
8. List card with rounded tiles, title/subtitle, round white action buttons and hairline dividers.
9. Feature card with large rounded image, bottom-left overlay text, round white button.
10. Purple footer banner with star mascot, sparkles and translucent pill button.
11. Font is Nunito; sentence case; no ALL-CAPS labels.
12. Radii/shadows are those in the tokens (no 1px gray borders, no flat shadows).
13. At 1024px the sidebar is an icon rail; at 390px a floating bottom tab bar; no horizontal scroll.
14. Hover/press/focus states exist; `prefers-reduced-motion` disables count-up and sweeps.
15. Lighthouse accessibility ≥ 95; no console errors.

### Phase 2 — Ingestion, sessions, profiling + Datasets and Profile pages
**Prompt:** "Execute Phase 2: Sections 5.1–5.3, 5.5–5.6, 6.2–6.3, the Sessions/Data/Profile endpoints in 11.2, the sample generator (13.1) and the Datasets and Profile pages (3.3, 3.4) wired to the real API (replace mocks on these pages only). Generate OpenAPI types."
**Acceptance:** upload of CSV/TSV/semicolon/UTF-16/Windows-1252/BOM/ragged files works with a correct parse report; empty/binary/oversize files show friendly errors; profile numbers match pandas ground truth in tests; sample datasets load; 100k-row file profiles within target (15.4); grid scrolls smoothly; session delete and TTL purge work.

### Phase 3 — Detection engine + Issues page
**Prompt:** "Execute Phase 3: Section 6.1, 6.4–6.12 and the Issues endpoints, plus the Issues page (3.5) with filters, issue cards, rows drawer, dismiss/reopen. Use the golden examples in Section 14 as tests."
**Acceptance:** all 8 issue types detected on the sample datasets (compare with truth manifests: recall ≥ 0.9, precision ≥ 0.85 at this stage); outlier cards never offer delete; dismissals persist and only dismiss the chosen rids; detection is deterministic and meets the 10 s target; grid highlights issue cells.

### Phase 4 — Operations/undo engine, safe actions, proposals API, Cleaning Studio
**Prompt:** "Execute Phase 4: Sections 5.4, 7.1, 7.2 (actions `trim_whitespace`, `normalize_case_variants`, `normalize_numbers`, `normalize_booleans`, `standardize_dates`, `convert_disguised_missing`), proposals/history endpoints, and the Cleaning Studio UI (3.6) including per-change checkboxes, inline override editing, accept/reject/skip, undo toast, apply-all-safe, keyboard shortcuts."
**Acceptance:** hypothesis test proves apply→undo restores the identical state hash; batch undo works; `409 PREVIEW_STALE` path tested; accepted changes appear in the grid and history; rejected/skipped states persist; apply-all-safe never touches `review`/`destructive` proposals; destructive confirm checkbox enforced server-side too.

### Phase 5 — Remaining actions, manual edits
**Prompt:** "Execute Phase 5: actions `remove_duplicate_rows`, `fill_missing`, `fix_invalid_numeric` (with `words_to_number`), `merge_similar_values`, `handle_outliers`, `resolve_duplicate_ids` (side-by-side conflict view), manual cell edit (3.3), redo, and the Quick-wins modal."
**Acceptance:** every alternative in the "Other ways to fix" menu works; fill strategies match pandas results; outliers default to no change; duplicate-ID groups can't be applied without an explicit choice; row deletion undo restores rows in original positions.

### Phase 6 — Rules engine + Rules page
**Prompt:** "Execute Phase 6: Section 8 and the Rules page (3.7): all 7 rule types, evaluator, live test, violations with reasons and unevaluable tab, suggestions with dry-run counts, rule export/import, `fix_rule_violation` proposals, re-run after every apply/undo. The deterministic NL parser fallback for `from-text` is included now; the LLM part comes in Phase 8."
**Acceptance:** all golden rule examples pass; custom regex safety tests pass (nested quantifier rejected); unevaluable values are reported, never counted as passing; rule results update automatically after changes.

### Phase 7 — Verification, History page, Reports, Export
**Prompt:** "Execute Phase 7: Section 9 fully, History page (3.8), Reports page (3.9) with verdict banner, KPI tiles, before/after table (Detected/Corrected/Dismissed/Remaining/New), unresolved list, export card, HTML + JSON report, history exports, ZIP bundle."
**Acceptance:** verdict is `clean` only when verified at the current `head_seq` with zero open findings and all rules passing; any change after verification marks it `stale`; CSV export round-trips (property test); report HTML opens offline and is XSS-safe (test with `<script>` in a cell); ZIP contains all 7 files.

### Phase 8 — LLM layer (Groq → Ollama → templates) + Settings
**Prompt:** "Execute Phase 8: Section 10 completely and the Settings page (3.11). Implement providers, circuit breaker, caching, redaction, validation/repair, status/test endpoints, source badges in the UI, AI buttons in Issues/Studio/Rules/Reports, notifications on fallback."
**Acceptance (all with `httpx.MockTransport` tests, plus manual check):** no keys + no Ollama → every AI button still returns a template answer; Groq failing → Ollama answers and a notification appears; both failing → template; malformed JSON is repaired or falls back; PII is redacted before sending (test); `GET /ai/status` accurately reflects reality; keys never reach the browser (grep the build output).

### Phase 9 — Dashboard wiring, global search, notifications, polish
**Prompt:** "Execute Phase 9: wire the Dashboard to `GET /dashboard` (3.2) with count-up/bar/donut motion, next-step banner logic, empty/loading/error states; global search (3.10); notifications; avatar menu; keyboard shortcuts; responsive QA at 390/768/1024/1440; accessibility pass (2.10)."
**Acceptance:** every control on every page does something real (no dead buttons — add a test that clicks every button on each page of the sample flow); the Phase-1 visual checklist still passes with real data; Lighthouse performance ≥ 85, accessibility ≥ 95.

### Phase 10 — Benchmark, hardening, end-to-end
**Prompt:** "Execute Phase 10: Section 13.2 benchmark (CLI + in-app tab), Section 14 test gaps, Playwright E2E for the full flow and failure paths, performance profiling against 15.4, security checklist 15.2."
**Acceptance:** benchmark report generated and rendered in-app; coverage gates met; E2E green in CI; performance targets met or documented deviations; security checklist ticked in `docs/SECURITY.md`.

### Phase 11 — Deployment and release
**Prompt:** "Execute Phase 11: finalize Dockerfile/compose/`render.yaml`, `scripts/smoke.sh`, README (screenshots, benchmark table, Groq key + Ollama instructions), release checklist 16.7, and deploy instructions verified end-to-end."
**Acceptance:** `docker compose up --build` works from a clean clone; Render blueprint deploys; smoke test passes against the live URL; site loads with the reference look; `.env` not in git history.

---

## 18. Final Definition of Done

**Core features (from the project checklist)**
- [ ] Upload CSV and display a preview (drag-and-drop + picker, parse report)
- [ ] Infer column types and calculate basic statistics
- [ ] Show missing-value and duplicate counts (and distinct counts)
- [ ] Detect missing values and exact duplicates
- [ ] Detect inconsistent text and date formats
- [ ] Validate numeric ranges and data types
- [ ] Flag suspicious outliers without auto-deleting them
- [ ] Apply selectable cleaning operations
- [ ] Preview original and proposed values (side by side, highlighted)
- [ ] Approve, reject, or skip proposed changes (and per-change selection)
- [ ] Run cross-column and user-defined rules
- [ ] Keep transformation history
- [ ] Undo (and redo) applied operations
- [ ] Recheck the dataset after cleaning (verification with Detected vs Corrected vs Dismissed)
- [ ] Export cleaned CSV and quality report (+ history JSON/CSV + ZIP)
- [ ] Summarize resolved and unresolved issues
- [ ] Test the system against a known set of errors (benchmark with precision, recall, correction accuracy, false-correction rate, remaining violations, time)

**Experience and quality**
- [ ] UI matches the reference image (Phase 1 checklist) on every page, not only the Dashboard
- [ ] Every button, chip, search, bell, avatar and menu does something real
- [ ] Works with no API key and no internet; Groq → Ollama → template chain proven by tests
- [ ] No silent data changes; every change is previewed, attributable and undoable
- [ ] Responsive (390 / 768 / 1024 / 1440), keyboard-accessible, reduced-motion safe
- [ ] Deployed, health-checked, smoke-tested, README complete

---

## Appendix A — `.cursor/rules/csv-rescue.mdc`
```
---
description: CSV Rescue project rules
alwaysApply: true
---
- Source of truth is docs/BUILD_SPEC.md. When unsure, re-read the relevant section; record decisions in docs/DECISIONS.md.
- Work one phase at a time. Do not build ahead. Always write tests with the feature. Run `make lint test` before finishing.
- Data integrity: DataFrames hold strings only (dtype=str, no NA coercion). Data may change ONLY through operations (core/ops.py). Every operation is undoable and hash-verified.
- Never use eval/exec, never unpickle user data, never execute user-provided regex without the safety checks in Section 8.2.
- Backend: Python 3.11+, type hints everywhere, Pydantic v2 models for every request/response, pure functions for detectors and actions, no business logic in routers. All errors use the envelope in Section 11.1.
- Frontend: TypeScript strict, no `any`, no inline hex colours (use CSS variables/Tailwind tokens from Section 2.2), Phosphor icons only, Nunito only, no default component-library look. Every image has a fallback. Every icon-only button has aria-label.
- The UI must match docs/design-reference/dashboard-reference.png: clay/pastel lavender, big radii, layered soft shadows, pill buttons, glossy icon badges. If a component looks like a generic SaaS template, redo it.
- LLM is optional: Groq → Ollama → templates. The LLM never changes data or decides correctness. Keys only on the backend. Redact PII before any LLM call.
- Do not add dependencies that are not in the spec without noting why in DECISIONS.md.
- Keep functions small, name things after the spec's vocabulary (IssueGroup, Proposal, Change, Operation, Finding).
- Never print or commit secrets. Never log cell values at INFO.
```

## Appendix B — Environment variables (`.env.example`)
```bash
# --- app ---
APP_ENV=development
PORT=8000
DATA_DIR=./data
STATIC_DIR=../frontend/dist
FRONTEND_ORIGIN=http://localhost:5173
LOG_LEVEL=INFO

# --- limits ---
MAX_UPLOAD_MB=25
MAX_ROWS=250000
MAX_COLUMNS=200
SESSION_TTL_HOURS=24
MAX_SESSIONS_IN_MEMORY=8
RATE_LIMIT_PER_MIN=120

# --- LLM (all optional) ---
LLM_ENABLED=true
LLM_PROVIDER_ORDER=groq,ollama        # then built-in templates automatically
LLM_TIMEOUT_SECONDS=12
LLM_REDACT_PII=true
GROQ_API_KEY=                          # get one free at https://console.groq.com → API Keys
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile     # alt: llama-3.1-8b-instant (check GET /ai/models for current list)
OLLAMA_BASE_URL=http://localhost:11434 # docker-compose overrides to http://ollama:11434; empty = disabled
OLLAMA_MODEL=llama3.2:3b               # alt: qwen2.5:7b

# --- frontend (frontend/.env) ---
# VITE_API_BASE=/api/v1
```

## Appendix C — Image-generation prompts for the 3D assets
Generate with any image model, then export **transparent WebP, 1024 px on the long side, quality 85** into `frontend/public/art/`. If the model can't output transparency, generate on a flat `#E8DEF7` background and remove it with a background-removal tool. Use original characters only (no existing franchises).

**Shared style block (append to every prompt):** *"soft 3D clay render, cute rounded forms, pastel lavender and cream palette with pink, butter-yellow and baby-blue accents, glossy subtle highlights, soft studio lighting from top-left, gentle contact shadow, smooth plasticine/vinyl toy finish, high detail, centered, no text, no watermark"*

| File | Prompt (before the style block) |
|---|---|
| `avatar-default.webp` | "Portrait bust of a friendly young person with a messy brown bun, big warm eyes, lavender hoodie, smiling, circular crop-friendly framing" |
| `hero-character.webp` | "Cheerful young person with a brown bun and lavender hoodie leaning on a ledge, holding a big magnifying glass over a small floating spreadsheet card with sparkles, one eye closed in a playful squint, torso only, wide composition" |
| `plant.webp` | "Leafy green houseplant in a round beige ceramic pot, tall glossy leaves" |
| `star-mascot.webp` | "Sparky, a smiling butter-yellow star mascot with rosy cheeks, tiny dot eyes and a small smile, slightly tilted, rounded points" |
| `sparkle-badge.webp` | "A glossy rounded golden sparkle/star trophy icon, simple silhouette" (used on the pink promo card instead of the crown) |
| `feature-card-bg.webp` | "Cozy desk scene in lavender and warm light: a tidy stack of paper sheets and a laptop showing a clean table, a small plant and a lamp, no people, 4:3" |
| `empty-upload.webp` | "A friendly fluffy cloud holding a small CSV document with a plus sign, soft sparkles" |
| `empty-clean.webp` | "A smiling sponge/bubble character holding a gold check mark, bubbles around" |
| `empty-search.webp` | "A tiny magnifying glass over a blank card with a question mark, cute, pastel" |
Provide SVG fallbacks for each so the app never shows a broken image.

## Appendix D — Copy deck (consistent verbs, sentence case)
| Where | Text |
|---|---|
| Hero (no data) | "Good Morning, {name}! Drop in a CSV and we'll find what needs fixing." — **Upload a CSV** |
| Hero (active) | "Good Morning, {name}! {filename} has {N} things to review." — **Continue cleaning** |
| Accept flow | Button **Accept (N)** → toast "Accepted — {n} cells updated" + **Undo** |
| Reject / Skip | **Reject** → "Rejected. The issue stays open." · **Skip** → "Skipped for now." |
| Undo / Redo | **Undo** → "Undone — {title}" · **Redo** → "Redone — {title}" |
| Apply safe | Modal title "Apply safe fixes?" — "These {N} fixes only change formatting, never meaning." — **Apply {N} fixes** → "Applied {N} fixes" |
| Destructive confirm | Checkbox "I understand this removes {n} rows. I can undo it." |
| Outlier card note | "Suspicious, not necessarily wrong." |
| Dismiss | **Mark as valid** → "Marked as valid. We won't count it as an open issue." |
| Verification | **Run verification** → "Verification finished — {verdict text}" |
| Verdicts | "Verified clean" · "Improved — {N} issues remain" · "Out of date — run verification again" |
| Empty issues | "No open issues. Run verification to confirm." |
| Upload error (not text) | "That file doesn't look like a CSV. Export it as CSV from Excel or Google Sheets and try again." |
| Upload error (too large) | "That file is {size}. The limit is {limit}. Split it or remove columns you don't need." |
| Server waking | "Waking up the server… this can take up to a minute on the free plan." |
| AI fallback notice | "Groq didn't respond, so Ollama wrote this." / "No AI available — showing a built-in explanation." |
| Session expired | "That dataset expired after 24 hours. Upload it again to continue." |

---
*End of specification. Build one phase at a time, keep the reference image attached for UI work, and verify with the Phase 1 checklist and the Definition of Done.*
