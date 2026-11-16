# Design tokens: the `--mds-*` / `$mds-*` catalogue

Read this when you need a Moodle Design System token name, its light or dark value, or to decide which tokens are safe
for CSS that must follow the colour mode.

Everything here was read in the Moodle 5.3.0 source, not compiled for this file. Light values come from
`lib/bundles/design-system/scss/tokens/_light.scss` by following references; dark values are the ones in core's own
precompiled `public/theme/boost/style/moodle.css` (default preset, default brand colour). Names are written without
the `--mds-` (custom property) or `$mds-` (SCSS variable) prefix; both forms exist for every token on 5.3.

## Where tokens live and how they reach the page

| | 5.2 | 5.3 |
|---|---|---|
| Package | `@moodlehq/design-system` 2.1.1 | 5.3.0 |
| Files | `public/theme/boost/scss/design-system/tokens/scss/` (seven partials) | `lib/bundles/design-system/scss/tokens/` (`_light.scss`, `_index.legacy.scss`, `_index_css_vars.scss`, `_index.scss`) |
| `$mds-*` SCSS variables | 295, defined as literals | 354, semantic tokens reference primitives |
| `--mds-*` custom properties | none | all 354, on `:root` |
| Component CSS (`.mds-*`) | none | imported by `public/theme/boost/scss/design-system.scss` |
| Dark values | none | only in `public/theme/boost/scss/moodle/dark.scss`; the package ships no dark token file |

- Every `$mds-*` is `!default`, so a value set in pre-SCSS wins and, on 5.3, also lands in the `--mds-*` property.
- On 5.3 semantic tokens point at primitives (`$mds-text-default: $mds-color-gray-900`), and a few point at other
  semantic tokens (`text-link-primary-default` and `-hover`, `border-interactive-primary-default` and `-hover` follow
  `bg-interactive-primary-default` / `-hover`; `focus-default` follows `border-interactive-primary-default`).
  Overriding a primitive before the import moves every token built on it.
- `_index.scss` uses `@forward` and cannot be used with `@import`. Boost imports `_index.legacy.scss`. Do not import
  token files yourself: `@import "design-system";` (both versions) or Boost's preset already does it.
- All 5.2 names still exist on 5.3. Added in 5.3: activity-icon, avatars, breakpoints, nav-pill and switch groups, the
  `*-light` feedback fills, the `-50` ramp steps, `focus-danger`, `text-link-primary-disabled`, `text-danger-disabled`,
  `font-family-base-jp`, `border-radius-xs`, `icons-xxs`, `spacing-offset`, `line-height-paragraph-xs`.
- Nothing read states that token names or values are a stable API across Moodle versions. Values did change between
  5.2 and 5.3 (last section).

## Tokens the official guide names as following the mode

From https://moodledev.io/docs/5.3/guides/colourmodes. Order of preference there: set no colour; use a utility class
(`bg-body`, `bg-body-secondary`, `bg-body-tertiary`, `text-body`, `text-body-secondary`, `text-body-emphasis`,
`text-bg-*`, `border`); use one of these tokens; write a literal with a `[data-bs-theme="dark"]` correction only where
the colour carries meaning.

| Token | Light | Dark | Use for |
|---|---|---|---|
| `--bs-body-bg` | `#f8f9fa` | `#1d2125` | The page itself (no token means "the page") |
| `--mds-bg-surface-default` | `#ffffff` | `#343a40` | A raised surface: card, modal, table cell |
| `--mds-bg-surface-strong` | `#e9ecef` | `#292e33` | A recessed area |
| `--mds-bg-surface-subtle` | `#f8f9fa` | `#292e33` | A subtler recessed area, a striped row |
| `--mds-text-default` | `#1d2125` | `#dee2e6` | Body text |
| `--mds-text-subtle` | `#495057` | `#ced4da` | Secondary text |
| `--mds-text-muted` | `#6a737b` | `#ced4da` | Muted text |
| `--mds-text-emphasis` | `#000000` | `#f8f9fa` | Text needing more contrast than the body |
| `--mds-text-link-primary-default` | `#0f6cbf` | `#7baedc` | Links |
| `--mds-border-default` | `#dee2e6` | `#495057` | Borders and rules |
| `--mds-bg-feedback-*-light`, `-subtle` | pale tint | shaded tint | Status backgrounds |
| `--mds-text-feedback-*` | readable on light | readable on dark | Status text |

Replacing a literal: pick the token whose light value matches, so light mode does not change.

| Literal | Token |
|---|---|
| `#fff`, `white` | `bg-surface-default` |
| `#eee` | `bg-surface-strong` |
| `#f5f5f5`, `#f8f9fa` | `bg-surface-subtle` |
| `#ddd` as a border | `border-default` |
| `#555` | `text-subtle` |
| `#666` | `text-muted` |
| `#0f6cbf` | `text-link-primary-default` |

Limits to keep in mind:

- `--mds-*` is undefined on 5.2 and inside the editor content iframe. Give a fallback that exists there:
  `var(--mds-bg-surface-default, var(--bs-body-bg))`.
- The saturated fills (`bg-feedback-*-default`, `bg-interactive-primary-*`, `bg-interactive-danger-*`) keep their
  colour in both modes on purpose. Text drawn on them must be chosen against the fill, not the page.
- `border-translucent` is fully transparent in light mode. It is not Bootstrap's `--bs-border-color-translucent`.
- `focus-default` and the switch tokens are not re-pointed in dark mode. `dark.scss` lifts
  `border-interactive-primary-default` because Moodle blue reaches only 2.56:1 on a dark card, but `focus-default`
  keeps the same blue and is used for focus outlines by the design system components. A theme that cares can re-point
  it inside `[data-bs-theme="dark"]`.
- The guide is silent on spacing, radius, typography and size tokens; they are not colours and have no dark values.

## Semantic colour tokens

"same" means `dark.scss` does not touch the token, so it keeps its light value in dark mode.

**Surfaces and neutral backgrounds**

| Token | Light | Dark |
|---|---|---|
| `bg-surface-default` | `#ffffff` | `#343a40` |
| `bg-surface-subtle` | `#f8f9fa` | `#292e33` |
| `bg-surface-strong` | `#e9ecef` | `#292e33` |
| `bg-nav-pill-hover` / `-pressed` / `-selected` | `#e9ecef` / `#dee2e6` / `#e9ecef` | `#495057` / `#6a737b` / `#495057` |
| `bg-switch-track-default` / `-hover` / `-disabled` | `#dee2e6` / `#ced4da` / `#e9ecef` | same |
| `bg-switch-thumb-default` / `-hover` / `-disabled` | `#495057` / `#495057` / `#8f959e` | same |

**Text**

| Token | Light | Dark |
|---|---|---|
| `text-default` | `#1d2125` | `#dee2e6` |
| `text-emphasis` | `#000000` | `#f8f9fa` |
| `text-subtle` | `#495057` | `#ced4da` |
| `text-muted` | `#6a737b` | `#ced4da` |
| `text-inverse` | `#f8f9fa` | `#1d2125` |
| `text-danger` / `text-danger-disabled` | `#ca3120` / `#df8379` | `#e28e84` / `#d76558` |
| `text-link-primary-default` / `-hover` / `-disabled` | `#0f6cbf` / `#0c5699` / `#6fa7d9` | `#7baedc` / `#b7d3ec` / `#8f959e` |
| `text-feedback-primary` / `-secondary` | `#062b4c` / `#343a40` | `#7baedc` / `#dee2e6` |
| `text-feedback-success` / `-info` / `-warning` / `-danger` | `#153114` / `#00343c` / `#60451f` / `#51140d` | `#86af84` / `#66b3c0` / `#f0ad4e` / `#e28e84` |

**Borders and focus**

| Token | Light | Dark |
|---|---|---|
| `border-default` | `#dee2e6` | `#495057` |
| `border-subtle` | `#e9ecef` | `#292e33` |
| `border-translucent` | `rgba(0,0,0,0)` | `rgba(255,255,255,.15)` |
| `border-interactive-primary-default` / `-hover` / `-active` / `-disabled` | `#0f6cbf` / `#0f6cbf` / `#0c5699` / `#6fa7d9` | `#3f89cc` / `#3f89cc` / `#7baedc` / `#3a658d` |
| `border-interactive-secondary-default` / `-hover` / `-active` / `-disabled` | `#ced4da` / `#6a737b` / `#495057` / `#dee2e6` | `#6a737b` / `#8f959e` / `#8f959e` / `#495057` |
| `border-interactive-danger-default` / `-hover` / `-active` / `-disabled` | `#ca3120` / `#ca3120` / `#a2271a` / `#df8379` | same |
| `border-feedback-primary` / `-secondary` | `#9fc4e5` / `#e9ecef` | `#094173` / `#495057` |
| `border-feedback-success` / `-info` / `-warning` / `-danger` | `#aecaad` / `#99cdd5` / `#f9deb8` / `#eaada6` | `#20491e` / `#004d5a` / `#90682f` / `#791d13` |
| `focus-default` / `focus-danger` | `#0f6cbf` / `#eaada6` | same |

**Interactive fills**

| Token | Light | Dark |
|---|---|---|
| `bg-interactive-primary-default` / `-hover` / `-active` / `-disabled` | `#0f6cbf` / `#0c5699` / `#094173` / `#9fc4e5` | same (on purpose) |
| `bg-interactive-primary-default-light` | `#e7f0f9` | `#041b30` |
| `bg-interactive-danger-default` / `-hover` / `-active` / `-disabled` | `#ca3120` / `#a2271a` / `#791d13` / `#eaada6` | same |
| `bg-interactive-danger-default-light` | `#faeae9` | `#330c08` |
| `bg-interactive-secondary-default` / `-hover` / `-active` / `-disabled` | `#dee2e6` / `#ced4da` / `#dee2e6` / `#e9ecef` | `#495057` / `#6a737b` / `#6a737b` / `#292e33` |

**Status ("feedback") fills**

| Token | Light `-default` / `-subtle` / `-light` | Dark `-default` / `-subtle` / `-light` |
|---|---|---|
| `bg-feedback-primary-*` | `#0f6cbf` / `#cfe2f2` / `#e7f0f9` | same / `#062b4c` / `#041b30` |
| `bg-feedback-success-*` | `#357a32` / `#d7e4d6` / `#ebf2ea` | same / `#153114` / `#0d1f0d` |
| `bg-feedback-info-*` | `#006778` / `#cce6ea` / `#e5f2f4` | same / `#00343c` / `#002026` |
| `bg-feedback-warning-*` | `#f0ad4e` / `#fcefdc` / `#fdf7ed` | same / `#60451f` / `#3c2b14` |
| `bg-feedback-danger-*` | `#ca3120` / `#f4d6d2` / `#faeae9` | same / `#51140d` / `#330c08` |
| `bg-feedback-secondary-default` / `-subtle` / `-dark` | `#dee2e6` / `#f8f9fa` / `#343a40` | `#495057` / `#292e33` / same |

**Activity icon colours** (all "same" in dark): `activity-icon-<category>-bg` / `-icon` for assessment
`#f8d1e3` / `#db1a74`, collaboration `#e0cffc` / `#6610f2`, communication `#ffe3d1` / `#cc5e13`, file
`#cce6ea` / `#008196`, interactive `#f4d6d2` / `#791d13`, other `#dee2e6` / `#1d2125`, resource `#cce6ea` / `#008196`.
Boost's own activity icon colours are a separate mechanism: the SCSS variables `$activity-icon-<purpose>-bg` and the
`--activity<purpose>` properties, tinted 30% in dark mode (`public/theme/boost/scss/moodle/icons.scss`).

## Primitive colour ramps

`color-<hue>-<step>`. Never re-pointed in dark mode. Values without the leading `#`.

| Hue | 50 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 |
|---|---|---|---|---|---|---|---|---|---|---|
| gray (plus `gray-white` ffffff, `gray-black` 000000) | n/a | f8f9fa | e9ecef | dee2e6 | ced4da | 8f959e | 6a737b | 495057 | 343a40 | 1d2125 |
| blue | e7f0f9 | cfe2f2 | 9fc4e5 | 6fa7d9 | 3f89cc | 0f6cbf | 0c5699 | 094173 | 062b4c | 031626 |
| cyan | e5f2f4 | cce6ea | 99cdd5 | 66b3c0 | 339aab | 008196 | 006778 | 004d5a | 00343c | 001a1e |
| green | ebf2ea | d7e4d6 | aecaad | 86af84 | 5d955b | 357a32 | 2a6228 | 20491e | 153114 | 0b180a |
| yellow | fdf7ed | fcefdc | f9deb8 | f6ce95 | f3bd71 | f0ad4e | c08a3e | 90682f | 60451f | 302310 |
| red | faeae9 | f4d6d2 | eaada6 | df8379 | d55a4d | ca3120 | a2271a | 791d13 | 51140d | 280a06 |
| orange | n/a | ffe3d1 | ffc8a3 | ffac74 | ff9146 | ff7518 | cc5e13 | 99460e | 662f0a | 331705 |
| pink | n/a | f8d1e3 | f1a3c7 | e976ac | e24890 | db1a74 | af155d | 831046 | 580a2e | 2c0517 |
| purple | n/a | dfd8e5 | c0b1cb | a08bb0 | 816496 | 613d7c | 4e3163 | 3a254a | 271832 | 130c19 |
| indigo | n/a | e0cffc | c29ffa | a370f7 | 8540f5 | 6610f2 | 520dc2 | 3d0a91 | 290661 | 140330 |
| teal | n/a | d2f4ea | a6e9d5 | 79dfc1 | 4dd4ac | 20c997 | 1aa179 | 13795b | 0d503c | 06281e |

Boost's preset maps Bootstrap's palette onto these: `$white`, `$gray-100` to `$gray-900`, `$black` and the ten hues
(`$blue: $mds-color-blue-500`, and so on), each `!default`. So `$mds-color-blue-500` is also `$blue`, the default
`$primary` and `--bs-blue`. Overriding only that one step to re-brand moves those, and nothing on the 600 and 700
steps used for hover and active states.

## Size, space and shape

No dark values; none are colours.

| Group | Tokens and values |
|---|---|
| `scale-*` (primitive, rem) | 0 `0`, 50 `.125`, 100 `.25`, 200 `.375`, 300 `.5`, 400 `.75`, 500 `.875`, 600 `1`, 700 `1.25`, 800 `1.5`, 900 `1.75`, 1000 `2`, 1100 `2.5`, 1200 `3`, 1300 `3.5`, 1400 `4`, 1500 `4.5`, 1600 `5`, 1700 `6`, 1800 `50` |
| `spacing-*` | none `0`, xxs `.25rem`, xs `.5rem`, sm `.75rem`, md `1rem`, lg `1.25rem`, xl `2rem`, xxl `3rem`; `spacing-offset` `.0625rem` |
| `border-radius-*` | none `0`, xs `.25rem`, sm `.375rem`, md `.5rem`, lg `.75rem`, xl `1rem`, xxl `2rem`, pill `50rem` |
| `stroke-weight-*` | sm `.0625rem`, md `.125rem`, lg `.1875rem`, xl `.25rem`, xxl `.3125rem` |
| shadow parts | `color-sm` `rgba(0,0,0,.08)`, `color-md` `rgba(0,0,0,.15)`, `color-lg` `rgba(0,0,0,.17)` (the names carry no "shadow"); `offset-sm` / `-md` / `-lg` `.125` / `.5` / `1rem`; `blur-sm` / `-md` / `-lg` `.25` / `1` / `3rem`. There is no composed shadow token |
| `icons-*` | xxs `.5rem`, xs `.75rem`, sm `1rem`, md `1.25rem`, lg `1.5rem`, xl `2rem`, xxl `2.5rem`, xxxl `3rem` |
| `avatars-*` | xs `1rem`, sm `1.5rem`, md `2rem`, lg `3rem`, xl `4rem`, xxl `6rem` |
| `breakpoints-*` | sm `36rem`, md `48rem`, lg `62rem`, xl `75rem`, xxl `87.5rem` |
| `margin-bottom-*` | paragraph `1rem`, heading `.5rem`, display `0` |
| `switch-track-padding` | `.125rem` |

Typography primitives (`typography-font-size-*`, `typography-font-weight-*`, `typography-line-height-*`) also exist;
check their exact names in `_light.scss` before using one.

## Typography

| Group | Tokens and values |
|---|---|
| Families | `font-family-base` `Noto Sans`, `font-family-base-jp` `Noto Sans JP`, `font-family-code` `Menlo`. Bare names with no fallback stack: a rule using only `var(--mds-font-family-base)` has no fallback if the font fails to load |
| `font-size-paragraph-*` | lead `1.25rem`, default `1rem`, small `.875rem` |
| `font-size-headings-1` to `-6` | `2.5`, `2`, `1.75`, `1.5`, `1.25`, `1` rem |
| `font-size-displays-1` to `-6` | `5`, `4.5`, `4`, `3.5`, `3`, `2.5` rem |
| `line-height-paragraph-*` | lead `2.5rem`, default `1.5rem`, small `1.0875rem`, xs `.75rem` |
| `line-height-headings-1` to `-6` | `3`, `2.4`, `2.1`, `1.8`, `1.5`, `1.2` rem |
| `line-height-displays-1` to `-6` | `6`, `5.4`, `4.8`, `4.2`, `3.6`, `3` rem |
| `font-weight-*` | light 300, regular 400, medium 500, semibold 600, bold 700 |
| `letter-spacing-default` | `0rem` |

## What Boost's dark palette re-points in total (5.3)

One `[data-bs-theme=dark]` block in the compiled CSS carries 57 `--mds-*` declarations and 33 `--bs-*` declarations.
The `--bs-*` part: `--bs-white` `#343a40`; `--bs-gray-100` to `--bs-gray-900` as
`#1d2125 #292e33 #495057 #6a737b #afb5bc #ced4da #dee2e6 #e9ecef #f8f9fa`; `--bs-black` `#f8f9fa`; the link colours;
the five hued `--bs-*-text-emphasis`; `--bs-focus-ring-color`; `--bs-state-*-bg` and `-border`;
`--bs-collapse-list-item-hover-*`; `--bs-link-focus-bg` and `-underline`.

With a changed brand colour the derived values differ: links, the focus ring, the primary borders and the feedback
tints are computed from `$primary`, `$success`, `$info`, `$warning` and `$danger` at compile time.

## Values that differ on 5.2

On 5.2 tokens exist only as SCSS variables. A theme that uses one for a size or colour gets a different result on
each version:

| Token | 5.2 | 5.3 |
|---|---|---|
| `font-family-base` | `Roboto` | `Noto Sans` |
| `border-radius-sm` / `-md` / `-lg` | `.25` / `.375` / `.5rem` | `.375` / `.5` / `.75rem` |
| `icons-xs` to `-xxl` | each one step smaller | as in the table above |
| `bg-feedback-info-default` | `#008196` | `#006778` |
| `bg-interactive-primary-disabled` | `#6fa7d9` | `#9fc4e5` |
| `bg-interactive-danger-disabled` | `#df8379` | `#eaada6` |
| `bg-interactive-secondary-default` and `-active` / `-hover` | `#ced4da` / `#dee2e6` | `#dee2e6` / `#ced4da` |
| `border-interactive-secondary-default` / `-disabled` | `#6a737b` / `#8f959e` | `#ced4da` / `#dee2e6` |
| shadow colours sm / md / lg | `.1` / `.2` / `.2` alpha | `.08` / `.15` / `.17` alpha |
