# Theme SCSS on Moodle 5.2

What is specific to Moodle 5.2 (the baseline). Everything here was read in the 5.2 source (5.2.2+); nothing was
compiled or run on 5.2.

## Where the libraries live

| Library | Version | Location |
|---|---|---|
| Bootstrap SCSS | 5.3.3 | `public/theme/boost/scss/bootstrap/` (wrapper `scss/bootstrap.scss` imports `bootstrap/bootstrap`) |
| Font Awesome | Free 6.7.2 | SCSS in `public/theme/boost/scss/fontawesome/`; webfonts in `public/lib/fonts/`. The wrapper's `$fa-version` still says 6.3.0: do not use it to decide which icons exist |
| Design system | `@moodlehq/design-system` 2.1.1 | `public/theme/boost/scss/design-system/tokens/scss/`: SCSS variables only, seven partials |
| Compiler | scssphp 1.12.1 | `public/lib/scssphp/` |

## Imports that resolve only on 5.2

`@import "bootstrap/<partial>";` (for example `bootstrap/functions`, `bootstrap/variables`, `bootstrap/mixins`),
`@import "fontawesome/<partial>";` and `@import "design-system/tokens/scss/...";`. They resolve because those
directories sit inside Boost's `scss/`. A theme that also supports a later version must not use them: use the wrapper
names (`bootstrap`, `fontawesome`, `design-system`, `moodle`) or import nothing after the preset.

Imports are accepted only from the theme directories. A path that leaves them is skipped with a debugging message
(`core_scss::is_valid_file()`).

## What does not exist on 5.2

| Missing | Effect if used |
|---|---|
| `--mds-*` custom properties (0 in the compiled Boost CSS) | `var(--mds-x)` is undefined; give a fallback such as `var(--mds-x, var(--bs-body-bg))` |
| Design system component CSS (`.mds-*` classes) | No such components are rendered |
| `scss/moodle/colour-mode.scss`: `@mixin dark-mode`, `dark-readable()`, `$dark-surface-*`, `$dark-min-contrast` | "Undefined mixin" / undefined function or variable: compile error, fallback to stock Boost |
| `scss/moodle/dark.scss`, `scss/design-system-tokens.scss`, `scss/moodle/fonts.scss`, `font-stack.scss`, `font-stack-lang.scss` | "file not found for @import" |
| Colour mode switcher, `data-bs-theme` on `<html>`, the `theme_boost_colourmode` preference | Dark rules are inert. Bootstrap's own `[data-bs-theme=dark]` block is in the compiled CSS, but nothing sets the attribute |
| Self-hosted fonts in Boost (`public/theme/boost/fonts/`) | The default typeface is Bootstrap's system font stack |
| Font subdirectories in `theme/font.php` | A font placeholder naming `dir/file.woff2` is answered 404; keep `fonts/` flat |
| `--colourmode` option of the Behat init script | Not available |
| 59 newer tokens (activity-icon, avatars, breakpoints, nav-pill, switch, `*-light` feedback fills, `-50` ramp steps and a few single ones) | Undefined `$mds-*` variable: compile error |

## What is different in Boost's SCSS

- `scss/preset/default.scss`: imports `design-system`, sets the Bootstrap variables, then `fontawesome`, `bootstrap`,
  `moodle`. No font-stack or fonts imports, no `$body-bg` (the page is Bootstrap's white), no `$card-bg` or
  `$card-border-color` overrides, and a `.navbar` box-shadow rule in the preset CSS.
- `scss/moodle/variables.scss`: the `$state-*-bg` / `$state-*-border`, `$dialogue-*`, `$filemanager-*`, `$atto-*`,
  `$popover-region-*`, `$question-*` and similar variables are colours (`$state-success-bg:
  shift-color($success, -80%)`, `$dialogue-base-bg: $white`), so colour functions on them compile. On 5.3 they hold
  `var(...)`: `darken()`, `lighten()` and `mix()` on them are a compile error, and `rgba()` emits a declaration
  that browsers drop (read, not run).
- Boost's partials use the SCSS colour variables (`$gray-100`, `$white`) directly, where 5.3 uses
  `var(--bs-gray-100)`. The `--bs-*` custom properties themselves are emitted by Bootstrap on 5.2 too, so theme rules
  written with them work on both.
- Design tokens are defined as literal values (`$mds-bg-interactive-primary-default: #0f6cbf !default;`). Several
  values differ from 5.3: `$mds-font-family-base` is `Roboto`; `$mds-border-radius-sm` / `-md` / `-lg` are
  `.25` / `.375` / `.5rem`; the `$mds-icons-*` sizes are one step smaller.
- `scss/editor.scss` is Bootstrap plus two rules: no fonts, no tokens, no dark palette.
- `scss/moodle/bs4-compat.scss` and `scss/moodle/deprecated.scss` are identical to 5.3. Bootstrap 4 class names work
  through them on both versions and are marked for removal in Moodle 6.0.

## Core's former Classic theme

5.2 is the last version that ships `public/theme/classic`. It is a useful reading example of a child of Boost that
shadows Boost's SCSS entry files (`scss/moodle.scss` importing `../../boost/scss/moodle` and then its own partial),
offers its own preset setting, and ships a precompiled stylesheet. It is not present on later versions, so a theme
cannot have it as a parent there.
