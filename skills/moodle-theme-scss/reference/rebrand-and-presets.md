# Re-branding and presets

Read this when changing the brand colour, typeface, radius or dark surfaces across a whole theme, when you need to
know which Bootstrap variables Boost's preset sets (and which a child can still override), or when offering or writing
a preset.

Evidence: the variable map and the preset mechanics were read in the 5.2 and 5.3.0 source. **The re-brand recipe was
assembled from that reading and has not been compiled or looked at in a browser.** Compile it and check a primary
button, a navigation pill, a link and a focus ring in both modes before relying on it.

## What Boost's default preset does, in order

`public/theme/boost/scss/preset/default.scss` (5.3.0). "Pre-SCSS" means the pre-SCSS callback or your `pre.scss`.

| What | Overridable in pre-SCSS? |
|---|---|
| `@import "design-system"`: tokens, and on 5.3 the `:root` custom properties and component CSS | Yes. Every `$mds-*` is `!default`; on 5.3 the value also lands in `--mds-*` |
| **5.3+:** `@import "moodle/font-stack"`: `$font-family-fallback`, `$font-family-sans-serif`, `$font-family-sans-serif-jp` | Yes |
| `$prefix: bs- !default` | Leave it. The dark palette and the official guide assume `--bs-` |
| `$white`, `$gray-100` to `$gray-900`, `$black`, ten hues, each `= $mds-color-* !default` | Yes |
| `$primary: $blue`, `$secondary: $gray-400`, `$success: $green`, `$info: $cyan`, `$warning: $yellow`, `$danger: $red`, `$light: $gray-100`, `$dark: $gray-900` | Yes. `$primary` is what the `brandcolor` setting writes |
| `$theme-colors` map-merge | Yes: define `$theme-colors` with extra entries |
| `$link-decoration`, `$link-hover-decoration`, `$border-radius: .5rem`, `$border-radius-lg: .6rem`, `$hr-opacity`, breadcrumb variables, `$table-striped-bg-factor` | Yes |
| `$card-group-margin: .25rem;` | **No**: assigned without `!default` |
| `$focus-ring-opacity`, `$input-border-color`, `$form-check-input-border`, `$form-switch-color` | Yes. **5.3+:** a literal `$input-border-color` stops inputs following the mode |
| `$dropdown-link-hover-color: $white;` `$dropdown-link-hover-bg: $primary;` | **No**: assigned without `!default` |
| `$popover-max-width` | Yes |
| **5.3+:** `$body-bg: $gray-100` | Yes |
| **5.3+:** `$card-bg: var(--bs-white)`, `$card-border-color: var(--bs-gray-200)` | Yes, but a literal stops cards following the mode |
| `$spacer`, `$spacers` | Yes |
| `$behatsite`, `$enable-transitions`, `$enable-smooth-scroll` | Yes |
| Imports: (**5.3+:** `moodle/fonts`,) `fontawesome`, `bootstrap`, (**5.3+:** `moodle/font-stack-lang`,) `moodle` | n/a |
| Preset CSS: font smoothing, round `.userpicture`, outline button fixes | Only by later CSS in `post.scss` |

Facts that decide what "takes effect":

- **Bootstrap's SCSS variables still work.** Bootstrap turns them into `--bs-*` on `:root, [data-bs-theme=light]`
  (`--bs-primary`, `--bs-body-bg`, `--bs-border-radius`, `--bs-font-sans-serif`), and Boost's partials read greys and
  body colours through those properties. A pre-SCSS `$gray-200` or `$body-bg` changes light mode.
- **Theme colours are baked in at compile time.** `.btn-primary` carries literals (`--bs-btn-bg: #0f6cbf`). That is why
  Boost's dark palette rewrites `.btn-secondary` by hand.
- **Bootstrap's `$enable-*` flags** can be set in pre-SCSS: `$enable-shadows` and `$enable-gradients` default false,
  `$enable-rounded` true, `$enable-dark-mode` true with `$color-mode-type: data` (in both versions). Boost sets only
  `$enable-transitions` and `$enable-smooth-scroll`.
- **Moodle-only variables** (`$navbar-height`, `$course-content-maxwidth`, `$activity-icon-<purpose>-bg`,
  `$dialogue-*`, `$filemanager-*` and so on) are in `public/theme/boost/scss/moodle/variables.scss`, all `!default`.
  On 5.3 about fifty of them default to a custom property; the rest are still light literals.
- **5.3+:** dark surfaces have two independent sets of variables that default to the same greys. Bootstrap's
  `$body-bg-dark`, `$body-secondary-bg-dark`, `$body-tertiary-bg-dark`, `$border-color-dark`, `$body-color-dark`
  (`lib/bundles/bootstrap/scss/_variables-dark.scss`) feed `--bs-body-bg` and friends. Boost's `$dark-surface-page`,
  `$dark-surface-raised`, `$dark-surface-recessed` and `$dark-min-contrast`
  (`public/theme/boost/scss/moodle/colour-mode.scss`) feed `--bs-white`, `--bs-gray-100`, `--bs-gray-200` and the
  `--mds-bg-surface-*` tokens. Changing one set leaves the body and the surfaces out of step.

## The gap a brand colour falls into (5.3)

`$primary` defaults to `$blue`, which defaults to `$mds-color-blue-500`. The reverse link does not exist: no token is
derived from `$primary` in light mode. The only place Boost points a primary token at the brand colour in light mode
is the edit-mode switch (`public/theme/boost/scss/moodle/primarynavigation.scss`, `.editmode-switch-form`). In dark
mode `dark.scss` does derive links, the focus ring and the primary borders from `$primary`.

Result with only `$primary` (or the `brandcolor` setting) changed: Bootstrap buttons and links take the brand colour;
`.mds-*` components (navigation pills and their selected dot, switches, `mds-btn`, `mds-badge`), anything using
`--mds-text-link-primary-*`, `--mds-border-interactive-primary-*` or `--mds-focus-default` stay Moodle blue in light
mode and follow the brand in dark mode.

## Re-brand recipe (not compiled)

Return this from the child's pre-SCSS callback, or put it in `pre.scss`. Pre-SCSS runs before Bootstrap's functions
exist, so it uses literals and Sass built-ins only.

```scss
// Brand colour. !default keeps an admin's "brandcolor" setting, which Boost's callback has already emitted.
$primary: #7a1f5c !default;

// Light mode: design system components do not read $primary, so point their primary tokens at it.
// text-link-primary-default/-hover, border-interactive-primary-default/-hover and focus-default follow the
// first two lines by themselves; the others are set here because they point at the blue ramp.
$mds-bg-interactive-primary-default: $primary;
$mds-bg-interactive-primary-hover: mix(#000, $primary, 20%);
$mds-bg-interactive-primary-active: mix(#000, $primary, 40%);
$mds-bg-interactive-primary-disabled: mix(#fff, $primary, 60%);
$mds-bg-interactive-primary-default-light: mix(#fff, $primary, 90%);
$mds-border-interactive-primary-active: mix(#000, $primary, 20%);
$mds-border-interactive-primary-disabled: mix(#fff, $primary, 40%);
$mds-text-link-primary-disabled: mix(#fff, $primary, 40%);

// Dark mode: dark.scss derives links, focus ring and primary borders from $primary. Only the surfaces need
// stating, and both families must agree.
$dark-surface-page: #14171a;
$body-bg-dark: #14171a;
$dark-surface-raised: #2b3035;
$body-secondary-bg-dark: #2b3035;
$dark-surface-recessed: #1f2327;
$body-tertiary-bg-dark: #1f2327;
```

Notes on the recipe:

- On 5.2 the `$mds-*` lines set variables nothing reads as custom properties, and the `$dark-*` lines are unused
  variables: harmless there.
- Not covered: the "feedback primary" tokens (`bg-feedback-primary-*`, `border-feedback-primary`,
  `text-feedback-primary`) still point at the blue ramp in light mode. Either set them the same way, or override the
  whole primitive ramp instead (`$mds-color-blue-50` to `$mds-color-blue-900`, ten values), which moves every token
  built on blue and also `$blue` and `--bs-blue`. Overriding only `$mds-color-blue-500` is the half-measure to avoid.
- Whether overriding these tokens has side effects on other components was not checked.
- The other theme colours (`$success`, `$info`, `$warning`, `$danger`) have the same split: Bootstrap follows the SCSS
  variable, the `--mds-*-feedback-*` tokens follow the ramps in light mode and the SCSS variables in dark mode.
- In dark mode core derives link colours from `$primary`, not from `$link-color`. A theme with a separate link
  colour setting has to re-point them itself in `post.scss` (5.3 only; uses Boost's helpers):

```scss
@include color-mode(dark) {
    --#{$prefix}link-color: #{dark-readable($link-color)};
    --mds-text-link-primary-default: #{dark-readable($link-color)};
}
```

## Typeface

```scss
// pre-SCSS. The first line is what 5.2 reads; 5.3 reads all three.
$font-family-sans-serif: "My Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
$mds-font-family-base: "My Sans";
$font-family-sans-serif-jp: "My Sans", "Noto Sans JP", system-ui, sans-serif;
```

- **5.3+:** `$font-family-sans-serif` defaults to `$mds-font-family-base` joined with a fallback list
  (`public/theme/boost/scss/moodle/font-stack.scss`). The design system component styles use
  `font-family: var(--mds-font-family-base)` directly (16 declarations in
  `lib/bundles/design-system/js/components/_index.legacy.scss`, 5.3.0), so changing only `$font-family-sans-serif`
  leaves those components in Noto Sans.
- **5.3+:** content in Japanese (`:lang(ja)`) takes `$font-family-sans-serif-jp`
  (`scss/moodle/font-stack-lang.scss`), which starts with `$mds-font-family-base` and then Noto Sans JP.
- Not compiled with a custom font for this file. Declaring the `@font-face` and shipping the files is a separate step.

## Patterns for rules in `post.scss`

```scss
// 5.3 only: a mode-specific value next to the rule it corrects.
.mytheme-hero {
    background-color: mix($primary, $white, 10%);

    @include dark-mode {
        background-color: mix($primary, $dark-surface-page, 20%);
    }
}

// Light-mode only custom property, without touching the dark palette (both versions).
:root:not([data-bs-theme="dark"]) .navbar.navbar-dark {
    --bs-navbar-color: #{$white};
}
```

A variable that must follow the mode is set to a custom property in pre-SCSS, as Boost does on 5.3:
`$card-bg: var(--bs-white);`. Such a variable can no longer go through a colour function: `darken()`, `lighten()`
and `mix()` stop the compile ("is not a color"), and `rgba()` emits a declaration that browsers drop (read in the
compiler, not run).

## Presets

A preset is the main SCSS text: the file that sets variables and imports Bootstrap and Moodle's partials.

- Boost ships `default.scss` and `plain.scss` in `public/theme/boost/scss/preset/`. The setting `theme_boost/preset`
  lists those two plus every file uploaded through `theme_boost/presetfiles` (file area `theme_boost`, `preset`; up to
  20 `.scss` files). `theme_boost_get_main_scss_content($theme)` returns the built-in file, the stored file, or the
  default as a fallback, using the `preset` setting of the theme it is given (`public/theme/boost/lib.php`). The
  stored file is always looked up in the `theme_boost` file area, whatever theme is passed. A child that passes its
  own config, with a `preset` setting naming a file uploaded under the child, silently gets the default preset.
- On save, an uploaded preset is compiled with the theme's pre and extra SCSS and rejected on a compile error. The
  check is skipped for the names `default.scss` and `plain.scss` and when the value did not change
  (`admin_setting_configthemepreset::validate()`, read 5.3.0).
- **`plain.scss` is not "default minus decoration".** It imports only `fontawesome`, `bootstrap` and `moodle`: no
  design system, no tokens, no Noto fonts, no Bootstrap variable overrides. **5.3+:** Boost's partials
  `scss/moodle/course.scss` and `scss/moodle/question.scss` use `$mds-*` variables, which plain never defines, so by
  reading the source plain cannot compile on 5.3 and the site silently gets the precompiled default CSS. Not confirmed
  by a compile. Do not build a theme on plain; a child whose SCSS uses `$mds-*` fails on it on either version.

Ways for a child theme to offer presets:

1. **Reuse Boost's choice** (the recipe in `SKILL.md`): call
   `theme_boost_get_main_scss_content(theme_config::load('boost'))` and wrap it in your `pre.scss` and `post.scss`. The
   preset chosen in Boost's settings applies to the child.
2. **Own setting** (read in the source, not run): declare a `preset` setting under the child's component with
   `new admin_setting_configthemepreset($name, $title, $description, 'default.scss', $choices, 'mytheme')` and a stored
   file setting for file area `preset`. The last argument names the theme whose `theme_mytheme` / `preset` file area
   and pre/extra SCSS are used for validation. Then read the stored file in your own main-SCSS function and fall back
   to Boost's default file from disk. Core's former Classic theme did this in 5.2
   (`public/theme/classic/lib.php`, 5.2).

A complete preset must itself import everything, in this order:

| 5.2 | 5.3 |
|---|---|
| `design-system`, variables, `fontawesome`, `bootstrap`, `moodle` | `design-system`, `moodle/font-stack`, variables, `moodle/fonts`, `fontawesome`, `bootstrap`, `moodle/font-stack-lang`, `moodle` |

So one preset file cannot serve both versions unchanged: `moodle/font-stack` does not exist on 5.2, and without it and
`moodle/fonts` a 5.3 site loses its typeface. This is the reason to read Boost's own preset from disk at compile time
instead of shipping a copy. A preset written for an earlier Moodle that imports `moodle` without `design-system`
fails to compile on 5.3 for the same reason as plain (read, not run).
