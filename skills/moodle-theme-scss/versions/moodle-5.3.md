# Theme SCSS on Moodle 5.3

What is specific to Moodle 5.3 against the 5.2 baseline. Read in the 5.3.0 source unless marked **run 5.3.0**
(observed in a child theme of Boost on Moodle 5.3.0).

## The libraries moved out of Boost

| Library | Version | Location in 5.3 |
|---|---|---|
| Bootstrap SCSS | 5.3.8 | `lib/bundles/bootstrap/scss/` at the Moodle root, outside `public/` |
| Font Awesome | Free 6.7.2 | `lib/bundles/fontawesome/scss/` and `lib/bundles/fontawesome/webfonts/`; entry `lib/bundles/fontawesome.scss` |
| Design system | `@moodlehq/design-system` 5.3.0 | `lib/bundles/design-system/scss/tokens/` (tokens) and `lib/bundles/design-system/js/components/_index.legacy.scss` (component CSS) |
| Compiler | scssphp 1.12.1 (unchanged) | `public/lib/scssphp/` |

- The directories `scss/bootstrap/`, `scss/fontawesome/` and `scss/design-system/` are gone from Boost. The files
  `scss/bootstrap.scss`, `scss/fontawesome.scss` and `scss/design-system.scss` remain as wrappers that import from
  `../../../../lib/bundles/...`, so the wrapper names work as before.
- `@import "bootstrap/functions";` (or any other partial path) fails with "file not found for @import", and the theme
  falls back to stock Boost CSS (**run 5.3.0**).
- `core_scss::is_valid_file()` now also accepts imports whose real path is under `lib/bundles`
  (`public/lib/classes/scss.php`). That is the only change to the SCSS engine; `theme_config` differs from 5.2 only in
  where a core font is looked up.
- The bundles are managed by npm in core. A theme does not ship or edit them.

## New in Boost's SCSS

| File | What it adds |
|---|---|
| `scss/design-system.scss` | Now imports token variables, the `:root { --mds-*: ... }` custom properties (354) and the design system component CSS |
| `scss/design-system-tokens.scss` | Token variables only, for contexts such as the editor |
| `scss/moodle/font-stack.scss` | `$font-family-fallback`, `$font-family-sans-serif` (built from `$mds-font-family-base`), `$font-family-sans-serif-jp` |
| `scss/moodle/fonts.scss` | `@font-face` rules for self-hosted Noto Sans, using `[[font:theme\|noto-sans/...]]` |
| `scss/moodle/font-stack-lang.scss` | `:lang(ja)` rule applying the Japanese stack; imported after Bootstrap |
| `scss/moodle/colour-mode.scss` | `$dark-surface-raised`, `$dark-surface-page`, `$dark-surface-recessed`, `$dark-min-contrast`, `@mixin dark-mode`, `@function dark-readable()` |
| `scss/moodle/dark.scss` | The dark palette; the last import of `scss/moodle.scss` |

Also new: `@mixin collapsemenu-toggle`, `$stickyfooter-supplementary-height`, `$dialogue-exception-line-color`, and in
Bootstrap 5.3.8 `$btn-close-filter` and `$carousel-control-icon-filter`. Nothing a theme is likely to use was removed.
47 of the 52 partials under `scss/moodle/` that exist in both versions changed; the largest changes are in `course`,
`drawer`, `admin`, `core`, `modules`, `navbar`, `primarynavigation`, `layout`, `moremenu` and `variables`. A theme
that overrides selectors from those partials should re-check them.

## The default preset changed

`scss/preset/default.scss` on 5.3 additionally: imports `moodle/font-stack` after the design system; sets
`$body-bg: $gray-100` (a grey page instead of white); sets `$card-bg: var(--bs-white)` and
`$card-border-color: var(--bs-gray-200)` so cards follow the colour mode; imports `moodle/fonts` before Font Awesome
and `moodle/font-stack-lang` after Bootstrap; and no longer has the `.navbar` box-shadow rule.

Visible effect on a theme that changes nothing: grey page background, Noto Sans instead of the system font stack, no
navbar shadow. Set `$body-bg` and `$font-family-sans-serif` in pre-SCSS to keep the 5.2 look.

`scss/preset/plain.scss` did not change: it still imports only `fontawesome`, `bootstrap` and `moodle`. Because
`scss/moodle/course.scss` (19 uses) and `scss/moodle/question.scss` (6 uses) now use `$mds-*` variables that plain
never defines, plain should fail to compile on 5.3 and fall back to the precompiled default CSS, silently, since the
setting does not validate the two built-in names. This is from reading the source; it was not confirmed by a compile.

## Variables that became custom properties

These hold a colour on 5.2 and a `var(...)` string on 5.3 (`scss/moodle/variables.scss`, both versions compared).
Passing one to `darken()`, `lighten()`, `mix()`, `rgba()`, `tint-color()` or `shade-color()` compiles on 5.2 and is a
compile error on 5.3 (read, not run). Setting one to a literal in pre-SCSS stops that component following the mode.

| Variables | 5.3 default |
|---|---|
| `$state-success-bg`, `$state-success-border`, `$state-info-bg`, `$state-info-border`, `$state-warning-bg`, `$state-warning-border`, `$state-danger-bg`, `$state-danger-border` | `var(--bs-state-<name>-bg)` / `var(--bs-state-<name>-border)` |
| `$dialogue-base-bg`, `$dialogue-lightbox-bg`, `$dialogue-exception-pre-bg` | `var(--mds-bg-surface-default)` |
| `$dialogue-base-border-color`, `$dialogue-base-hd-border-color`, `$dialogue-exception-call-border-color`, `$dialogue-exception-label-border-color`, `$dialogue-exception-pre-border-color` | `var(--mds-border-default)` |
| `$dialogue-exception-call-color` | `var(--mds-text-default)` |
| `$dialogue-exception-file-color` | `var(--mds-text-feedback-primary)` |
| `$dialogue-exception-label-bg` | `var(--mds-bg-surface-strong)` |
| `$dialogue-exception-line-color` (new) | `var(--mds-text-feedback-warning)` |
| `$atto-content-wrap-bg`, `$atto-control-icon-bg`, `$atto-toolbar-button-gradient-inner`, `$atto-toolbar-group-bg` | `var(--bs-white)` |
| `$atto-toolbar-button-color` | `var(--bs-gray-700)` |
| `$filemanager-dnd-upload-over-bg`, `$filemanager-dnd-upload-target-bg`, `$filemanager-dnd-upload-target-shadow`, `$filemanager-filename-bg`, `$filemanager-panel-button-bg`, `$filemanager-picker-bg`, `$filemanager-picker-thumbnail-bg`, `$filemanager-thumbnail-border-color`, `$filemanager-thumbnail-over-bg`, `$filemanager-yui-table-cell-even-bg`, `$filemanager-yui-table-cell-even-border-color`, `$filemanager-yui-table-header-bg`, `$filemanager-yui-table-header-border-left-color` | `var(--bs-white)` |
| `$formlisting-bg`, `$forms-autocomplete-bg`, `$grade-table-td-bg`, `$hover-tooltip-bg`, `$hover-tooltip-border-top-color`, `$popover-region-container-bg`, `$popover-region-toggle-border-bottom-color`, `$question-choice-text-shadow`, `$question-gradient-start-color`, `$question-type-bg`, `$visually-hidden-active-bg` | `var(--bs-white)` |
| `$webservice-doc-td-border-color` | `var(--bs-black)` |
| In the preset: `$card-bg`, `$card-border-color` (Bootstrap's literals on 5.2) | `var(--bs-white)`, `var(--bs-gray-200)` |

`$input-border-color` is already `var(--bs-gray-500)` in the 5.2 preset, so it is not new, but the same two rules
apply to it.

Related change: Boost's own partials now read the greyscale and body colours as `var(--bs-gray-*)`, `var(--bs-white)`,
`var(--bs-black)`, `var(--bs-body-bg)` and `var(--bs-body-color)` instead of the SCSS variables. The light-mode values
are unchanged, and pre-SCSS values for `$gray-*` still feed those properties.

## Colour modes

- New settings on Boost's "Experimental settings" tab: `theme_boost | enablecolourmodes` (default off) and
  `theme_boost | defaultcolourmode` (default light). They are read from `theme_boost` for every theme that has `boost`
  among its parents; a child theme cannot opt out with a setting of its own.
- New user preference and cookie `theme_boost_colourmode` (`light`, `dark`, `auto`).
- `<html data-bs-theme="light|dark" data-colourmode="light|dark|auto">` on every page of a Boost-based theme once the
  feature is on.
- The dark CSS is compiled into every Boost-based stylesheet whether or not the feature is on.
- `@include dark-mode { ... }` compiles to a `[data-bs-theme="dark"]`-prefixed selector, and a rule scoped by that
  attribute changes computed styles when the attribute is `dark` (**run 5.3.0**).
- The Behat init script takes `--colourmode=<light|dark>`.
- The official guide says a later change will move the settings off the Experimental tab, turn colour modes on by
  default and make "System" the default mode (https://moodledev.io/docs/5.3/guides/colourmodes). Treat dark mode as
  something every 5.3 theme will meet.

## Design tokens

- 354 `$mds-*` variables, each also emitted as a `--mds-*` custom property on `:root`; semantic tokens now reference
  primitives instead of holding literals.
- Core renders design system components (`mds-nav-pill`, `mds-switch`, `mds-btn`, `mds-badge`) whose CSS reads the
  tokens. Their primary colours do not follow `$primary` in light mode unless the theme sets the `$mds-*-primary-*`
  tokens in pre-SCSS.
- The tokens are not defined in the editor content iframe.

## Fonts

- `public/theme/font.php` accepts subdirectories in font names (`[[font:theme|my-sans/regular.woff2]]`).
- Core's Font Awesome webfonts are served from `lib/bundles/fontawesome/webfonts/`; `public/lib/fonts/` no longer
  exists. `[[font:core|...]]` placeholders are unaffected; a hand-built path to `lib/fonts/` breaks.
- Boost ships Noto Sans and Noto Sans JP under `public/theme/boost/fonts/`.

## Navigation selectors

Primary and secondary navigation are rendered by React components on 5.3. Selectors such as
`.primary-navigation .nav-link.active`, `.moremenu .nav-link` and `.secondary-navigation .nav-tabs .nav-link` match
nothing in that markup; the styling hooks are `.primarynav-navbar`, `.secondarynav-tabbar`, `.mds-nav-pill` and
`.mds-nav-pill--selected` (`public/theme/boost/scss/moodle/primarynavigation.scss`, `secondarynavigation.scss`). A
theme that supports 5.2 and 5.3 needs both sets. What the templates render is covered in
`moodle-theme-layouts-templates`.
