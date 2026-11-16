---
name: moodle-theme-scss
description: Use when writing or debugging a Moodle theme's SCSS or CSS - `$THEME->scss`, `prescsscallback` / `extrascsscallback`, pre.scss and post.scss, `@import` paths that must work on 5.2 and 5.3, Bootstrap variables and `!default`, `--bs-*` / `--mds-*` custom properties and design tokens, dark mode (`data-bs-theme`), re-branding, presets, fonts, `[[pix:]]` / `[[font:]]`, RTL directives, editor SCSS, stylelint, or when a theme suddenly looks like plain Boost ("Error while compiling SCSS", "file not found for @import"). Skip when the task is theme structure, layouts, templates, renderers or the settings page (start at moodle-theme-development).
---

# Moodle Theme SCSS

## Overview

How a Boost-based theme's stylesheet is assembled and compiled on Moodle 5.2 and 5.3, the recipe that works when
copied, and the traps that make a theme silently fall back to stock Boost or break in dark mode, RTL or the editor.

Evidence tags used below: **run 5.3.0** means observed in a child theme of Boost on Moodle 5.3.0. **read** means read
in the source of the named version and not run. Nothing here was run on Moodle 5.2; every 5.2 statement is "read".

## When to Use

- Adding or changing SCSS in a theme: variables, rules, imports, presets, fonts, background images
- Making a theme follow the 5.3 colour modes, or re-branding it (brand colour, typeface, radius)
- The theme "does nothing": the page looks like plain Boost, or a variable override has no effect
- RTL, editor content or stylelint problems in a theme's styles
- **Skip when:** the question is which files a theme needs or how caches and purges work (`moodle-theme-development`),
  how a setting reaches SCSS (`moodle-theme-settings`), page structure or template markup
  (`moodle-theme-layouts-templates`), icon maps and `pix_core` overrides (`moodle-theme-renderers-output`), or proving
  the result with PHPUnit, Behat and CI (`moodle-theme-testing-release`). The minimal child theme around this SCSS is in
  `moodle-theme-boost-child`.

## How the stylesheet is built

One SCSS string is compiled per theme and direction. `theme_config::get_css_content_from_scss()` concatenates three
parts and compiles them with scssphp 1.12.1 (the same compiler version in 5.2 and 5.3;
`public/lib/classes/output/theme_config.php`, `public/lib/classes/scss.php`, read in both).

```
1. pre-SCSS callbacks    every parent's prescsscallback, base parent first, then the theme's own.
                         Boost's emits: $primary from the brandcolor setting, $behatsite, the scsspre setting.
2. main SCSS             the string returned by the $THEME->scss closure. In the recipe below:
                           your pre.scss      variables, each with !default
                           Boost's preset     tokens, variables (!default), Font Awesome, Bootstrap, Moodle partials
                           your post.scss     rules; every variable, mixin and function now exists
3. extra-SCSS callbacks  every parent's extrascsscallback, base first, then the theme's own.
                         Boost's emits: the raw SCSS setting (scss) and the background image rules.
then post_process():     [[pix:...]] and [[font:...]] become URLs, csspostprocess runs,
                         the all-rtl build is flipped, and the result is minified.
```

- Every callback receives the theme being compiled, so Boost's callbacks read the child's settings: a `brandcolor`
  saved under `theme_mytheme` turned `.btn-primary` that colour with no code in the child (**run 5.3.0**). Do not copy
  Boost's callbacks into the child; that emits everything twice.
- The served sheet is: every plugin's `styles.css`, then parent themes' `sheets`, then this compiled SCSS, then the
  theme's own `sheets` (`theme_config::get_css_files()`, read 5.3.0). Theme rules come after plugin rules, so at equal
  specificity the theme wins.
- A compile error is caught and reported only as a developer-level debugging message; the precompiled CSS of the
  parents is served instead. See "When the compile fails".

## The default recipe

Works on 5.2 and 5.3. Files live in `scss/mytheme/` so that no file name collides with one of Boost's (see mistakes).

```php
// config.php (GPL header) - only the keys that concern styles.
$THEME->parents = ['boost'];
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->scss = function ($theme) {
    return theme_mytheme_get_main_scss_content($theme);
};
$THEME->prescsscallback = 'theme_mytheme_get_pre_scss';
$THEME->extrascsscallback = 'theme_mytheme_get_extra_scss';
// Leave editor_scss, usefallback and precompiledcsscallback unset: Boost's are used.
```

```php
// lib.php (GPL header)
function theme_mytheme_get_main_scss_content($theme) {
    global $CFG;
    require_once($CFG->dirroot . '/theme/boost/lib.php');
    $pre = file_get_contents(__DIR__ . '/scss/mytheme/pre.scss');
    $post = file_get_contents(__DIR__ . '/scss/mytheme/post.scss');
    // Boost returns the preset chosen in the settings of the theme it is given. Pass Boost's config to follow
    // the preset the admin chose for Boost. The preset file differs between 5.2 and 5.3, so never ship a copy.
    $boost = theme_config::load('boost');
    return $pre . "\n" . theme_boost_get_main_scss_content($boost) . "\n" . $post;
}

function theme_mytheme_get_pre_scss($theme) {
    $scss = '';
    $accent = get_config('theme_mytheme', 'accentcolour');
    // Validate before interpolating: the value is compiled as SCSS.
    if (!empty($accent) && preg_match('/^#[0-9a-fA-F]{3,8}$/', $accent)) {
        $scss .= '$mytheme-accent: ' . $accent . ";\n";
    }
    return $scss;
}

function theme_mytheme_get_extra_scss($theme) {
    return '';
}
```

```scss
// scss/mytheme/pre.scss - runs after the pre-SCSS callbacks, before Boost's preset.
$mytheme-accent: #b8410c !default;   // !default, so a value from the settings callback wins.
$mytheme-radius: .75rem !default;

$border-radius: $mytheme-radius !default;        // Bootstrap variables: set them here, before the preset reads them.
$card-border-radius: $mytheme-radius !default;
```

```scss
// scss/mytheme/post.scss - rules, after everything in Boost.
.mytheme-banner {
    padding: .75rem 1rem;
    border-left: .5rem solid $mytheme-accent;    // Flipped to border-right in the RTL build.
    border-radius: $mytheme-radius;
    background-color: var(--bs-tertiary-bg);     // Custom properties follow the colour mode.
    color: var(--bs-body-color);
}

[data-bs-theme="dark"] {
    .mytheme-banner {
        border-left-color: lighten($mytheme-accent, 25%);
    }
}
```

This shape was compiled on 5.3.0: the setting reached the compiled CSS, `border-left` became `border-right` in the RTL
build, and the banner changed under `data-bs-theme="dark"` (**run 5.3.0**).

## What exists at each stage

| Stage | Can use | Cannot use | Put here |
|---|---|---|---|
| pre-SCSS callback, `pre.scss` | literals; Sass built-ins (`mix()`, `lighten()`, `rgba()`); your own variables | `$gray-*`, `$primary` unless you set it, `$mds-*`, Bootstrap functions (`tint-color()`, `shade-color()`), any mixin | variable values |
| `post.scss`, extra-SCSS callback | everything: Bootstrap and Boost variables, mixins, functions, `$mds-*` tokens | changing a variable for code that was already compiled | rules |

- A variable set in pre-SCSS wins because Boost and Bootstrap assign theirs with `!default`. Symptom when ignored: a
  variable assigned in `post.scss` changes nothing above it.
- Three preset variables are assigned without `!default` and ignore pre-SCSS: `$card-group-margin`,
  `$dropdown-link-hover-color`, `$dropdown-link-hover-bg` (`public/theme/boost/scss/preset/default.scss`, read 5.2 and
  5.3). Override the resulting CSS in `post.scss` instead.
- An undefined variable or function in pre-SCSS is a compile error, and so a silent fallback (read 5.3.0:
  scssphp throws; the engine catches).
- `mixin-exists()`, `function-exists()` and `variable-exists()` work in scssphp 1.12.1, but in pre-SCSS they are false
  for everything Boost defines, on every version. Test in `post.scss` only.
- Prefix your own variables, mixins and classes (`$mytheme-`, `.mytheme-`). Boost's compatibility layer defines global
  helpers named `hover()`, `hover-focus()`, `sr-only()`, `sr-only-focusable()`, `badge-variant()` and `color-yiq()`
  (`public/theme/boost/scss/moodle/bs4-compat.scss`, read 5.2 and 5.3); it is due for removal in Moodle 6.0, so do not
  call them either.

## Imports that work on both versions

5.3 moved Bootstrap, Font Awesome and the design system out of Boost into `lib/bundles/` at the Moodle root. Only the
wrapper names survive in `public/theme/boost/scss/`.

| Import | 5.2 | 5.3 |
|---|---|---|
| `@import "bootstrap";` `"fontawesome";` `"design-system";` `"moodle";` `"preset/default";` | yes | yes |
| `"moodle/<partial>"` for a partial that exists in both (`moodle/variables`, `moodle/core`, ...) | yes | yes |
| `"bootstrap/<anything>"`, `"fontawesome/<anything>"`, `"design-system/tokens/scss/..."` | yes | **no** |
| `"design-system-tokens"`, `"moodle/colour-mode"`, `"moodle/dark"`, `"moodle/fonts"`, `"moodle/font-stack"`, `"moodle/font-stack-lang"`, `"../../../../lib/bundles/..."` | **no** | yes |

- `@import "bootstrap/functions";` on 5.3 fails with "file not found for @import" and the whole theme falls back to
  stock Boost (**run 5.3.0**). With the recipe above you need no import at all: by `post.scss` everything is loaded.
- Import lookup order is the importing file's own directory, then the theme's `scss/`, then each parent's `scss/`
  (`theme_config::get_scss_property()`; `public/lib/scssphp/src/Compiler.php` `findImport()`, read 5.3.0). The preset
  text is compiled as a string with no directory, so its `@import "moodle"` finds `scss/moodle.scss` in the child
  first. A child file named `moodle.scss`, `bootstrap.scss`, `fontawesome.scss` or `design-system.scss` therefore
  replaces Boost's. Do that only on purpose, and then import Boost's file from inside it by relative path.
- An imported file must end in `.scss` and sit under a theme directory (**5.3+:** or under `lib/bundles`); anything
  else is skipped with a developer debugging message "Can't import scss file" (`core_scss::is_valid_file()`, read).

## Colours and dark mode

**5.3+:** Boost has light and dark colour modes, off by default (`theme_boost | enablecolourmodes`, Experimental
settings tab). The settings are read from `theme_boost`, not from the child, and apply to every theme with `boost` in
its parents (`public/theme/boost/classes/colour_mode.php`, read 5.3.0). A child theme cannot opt out: once the admin
enables the feature, the child's pages get `<html data-bs-theme="dark">`. Write for both modes even in a "5.2 theme".

1. **Scope dark rules by `[data-bs-theme="dark"]`, never `@media (prefers-color-scheme: dark)`.** The user's choice
   and the site default override the device, so a media query styles light pages dark and the reverse
   (https://moodledev.io/docs/5.3/guides/colourmodes). On 5.2 nothing sets the attribute, so the rules are inert.
2. **Take surfaces and text from custom properties**, not SCSS colour variables. An SCSS variable is resolved at
   compile time and cannot follow a per-request mode. Safe on 5.2 and 5.3 (Bootstrap 5.3 emits them in both):
   `--bs-body-bg`, `--bs-body-color`, `--bs-secondary-bg`, `--bs-tertiary-bg`, `--bs-border-color`,
   `--bs-emphasis-color`, `--bs-link-color`, `--bs-gray-100` to `--bs-gray-900`, `--bs-white`, `--bs-black`.
   **5.3+:** in dark mode Boost re-points the greys: `--bs-white` is the raised surface (cards), `--bs-gray-100` the
   page, `--bs-gray-200` a recessed area, and the high numbers become light text colours.
3. **A literal is a bug when it is half of a pair**: a fixed background behind mode-following text, or the reverse.
   Symptom: unreadable text in one mode. Brand accents that are legible on both surfaces may stay literal; check
   contrast in both modes.
4. **5.3+:** Boost's helpers for `post.scss`: `@include dark-mode { ... }` inside a rule (prefixes the enclosing
   selector, so it outranks the rule it corrects; compiled, **run 5.3.0**) and `dark-readable($color)`, which tints a
   colour until it reaches 4.6:1 on a dark raised surface (`public/theme/boost/scss/moodle/colour-mode.scss`). Neither
   exists on 5.2, where using them is a compile error. For a theme that supports both, write the selector yourself as
   in the recipe, or ship a prefixed copy of the mixin (same compiler on both versions; not run on 5.2):

```scss
@mixin mytheme-dark {
    @at-root #{selector-nest('[data-bs-theme="dark"]', &)} {
        @content;
    }
}
```

5. **Do not write a bare `:root { --bs-...: ...; }` or `:root { --mds-...: ...; }` in post or extra SCSS.** It has the
   same specificity as `[data-bs-theme=dark]`, both match `<html>`, and yours comes later, so it overrides the dark
   palette (cascade reasoning; not checked in a browser). Set the SCSS variable in pre-SCSS, or scope light values:
   `:root:not([data-bs-theme="dark"]) { ... }`.
6. **5.3+:** some variables that were colours in 5.2 are `var(...)` strings in 5.3 (`$state-*-bg`, `$state-*-border`,
   `$dialogue-*`, `$card-bg`, `$card-border-color` and about forty more). `darken($state-success-bg, 5%)` or
   `rgba($dialogue-base-bg, .9)` compiles on 5.2 and is a compile error on 5.3 (read; scssphp colour functions need a
   colour). Derive from `$success`, `$gray-*` or a literal instead. The list is in the 5.3 version notes.
7. **5.3+:** setting `$card-bg`, `$card-border-color`, `$state-*-bg` or `$input-border-color` to a literal stops that
   component following the mode. Set a colour the dark palette can re-point (a `var(--bs-...)`), as Boost does.
8. Icons drawn as Font Awesome glyphs follow the text colour. An `<img>` icon keeps its baked-in colours; Boost
   inverts only a fixed list of core paths in dark mode. Details in the dark mode reference.

## Custom properties: `--bs-*` and `--mds-*`

- `--bs-*` comes from Bootstrap 5.3 and exists on 5.2 and 5.3. `--mds-*` (Moodle Design System tokens, 354 of them)
  exists only on 5.3 and only on the main page: not on 5.2 (0 matches in 5.2's compiled Boost CSS) and not inside
  the editor content iframe.
- **An undefined custom property is silent.** `var(--x, #fff)` uses the fallback on every theme and mode, so the rule
  looks right only where the fallback happens to fit. Fix: check each name once on the target version,
  `getComputedStyle(document.documentElement).getPropertyValue('--mds-bg-surface-default')` (empty string means
  undefined), and for 5.2 plus 5.3 chain a property that exists on both:
  `color: var(--mds-text-default, var(--bs-body-color));`.
- The `$mds-*` SCSS variables exist on both versions (295 on 5.2, 354 on 5.3), but several values changed
  (`$mds-border-radius-md` is `.375rem` on 5.2 and `.5rem` on 5.3). Do not rely on a token for a size that must be
  identical on both.
- The two families are not parallel: `--mds-border-translucent` is fully transparent in light mode, unlike
  `--bs-border-color-translucent`. Check both values before swapping one for the other.

## Re-branding

- Brand colour: Boost's `brandcolor` setting (declared under the child's component) or `$primary` in pre-SCSS. Theme
  colours are baked into Bootstrap components at compile time (`.btn-primary` carries literals).
- **5.3+:** nothing links `$primary` to the design system's primary tokens in light mode, so with only `$primary`
  changed the `.mds-*` components core renders (navigation pills, switch, buttons, badges), token-based links and
  focus outlines stay Moodle blue in light mode, while dark mode derives them from `$primary` (read 5.3.0:
  `scss/moodle/dark.scss`; the only light-mode link is the edit switch in `scss/moodle/primarynavigation.scss`).
  The fix is to set the `$mds-*-primary-*` tokens in pre-SCSS too. The recipe is in the re-brand reference; it was
  built from the source and has not been compiled.
- Typeface: set `$font-family-sans-serif` in pre-SCSS. **5.3+:** also set `$mds-font-family-base`, or design system
  components and `:lang(ja)` content keep Noto Sans.
- **5.3 changed the default look without a theme changing a line:** page background `$gray-100` instead of white,
  self-hosted Noto Sans instead of the system font stack, and no navbar box-shadow in the preset. A theme tuned on 5.2
  should set `$body-bg` and `$font-family-sans-serif` explicitly if it wants the old look.

## Fonts, images, RTL and the editor in one paragraph each

- **Images and fonts in SCSS** are written as placeholders, never as paths: `url([[pix:theme|hero]])` for
  `pix/hero.svg|png` in the theme, `url([[pix:t/collapsed]])` for a core icon, and
  `url('[[font:theme|mysans.woff2]]')` for `fonts/mysans.woff2`. **5.3+:** fonts may sit in subfolders
  (`[[font:theme|my-sans/regular.woff2]]`); on 5.2 that URL is a 404, so a 5.2-compatible theme keeps `fonts/` flat.
  Core does not replace `[[setting:name]]`: only `[[pix:]]` and `[[font:]]` (`theme_config::post_process()`, read
  5.3.0). Pass settings as SCSS variables from the pre-SCSS callback.
- **RTL is automatic.** There is one source; the `all-rtl` build is the same CSS with left/right flipped
  (**run 5.3.0**). Write LTR, prefer logical properties in new code, and correct by hand what the flipper skips:
  `transform`, `box-shadow`, gradients, `inset`. A rule whose selector contains `.dir-rtl` is left untouched.
  Directives are CSS comments placed before a declaration: `/*rtl:ignore*/`, `/*rtl:remove*/`, `/*rtl:raw: ...*/`.
- **Editor content is a separate document.** TinyMCE loads only the editor sheet, built from `editor_scss` with no
  pre or extra callbacks, so theme settings and `post.scss` never reach it. A child that sets
  `$THEME->editor_scss = ['editor']` without shipping `scss/editor.scss` loses Boost's editor styles (read 5.3.0).
  Leave the key unset unless you ship the file.
- Theme SCSS also never enters H5P content: that iframe takes CSS only from the `core_h5p | h5pcustomcss` setting.

## When the compile fails

Symptom: the page looks like plain Boost, with none of the theme's rules and no error on screen (**run 5.3.0**).
`get_css_content()` substitutes the parents' precompiled CSS, and `public/theme/styles.php` defines `NO_DEBUG_DISPLAY`,
so in a browser the message goes only to the PHP error log.

To see the error, compile from the command line with developer debugging on (`$CFG->debug = E_ALL;` and
`$CFG->debugdisplay = 1;` in a development `config.php`); the message "Error while compiling SCSS: ..." names the
cause (**run 5.3.0** for the message; the command below reaches the same code, read):

```bash
php admin/cli/build_theme_css.php --themes=mytheme --direction=ltr
```

- That command also caches what it built. After fixing the SCSS, run it again or purge caches, or the fallback CSS
  stays cached.
- A PHPUnit test that calls `theme_config::load('mytheme')->get_css_content()` and asserts one of the theme's own
  selectors is in the result catches every case here, because the fallback contains none of them
  (`moodle-theme-testing-release` has the test).
- Usual causes: a 5.2-only import path on 5.3; a 5.3-only mixin or partial on 5.2; a colour function applied to a
  `var(...)` variable; an undefined variable in pre-SCSS; invalid SCSS typed into a raw SCSS setting.
- A different effect with the same look: with `usefallback` on (inherited from Boost), the first stylesheet request
  after a purge can be answered with the previous build while the new one compiles. Reload once before debugging.
  Cache behaviour is in `moodle-theme-development`.

## Cascade facts that decide whether a rule applies

- "The rule is in the served sheet" is not "the rule applies". Prove arrival by searching the stylesheet the page
  links (`/theme/styles.php/<theme>/<rev>/all`) for the selector, then prove effect with `getComputedStyle()` on the
  element, in the mode and direction that matter.
- Bootstrap components read their own custom properties. To restyle one, set those from a selector that outranks
  the component rule, rather than fighting declarations:

```scss
.btn.mytheme-share {
    --bs-btn-bg: var(--bs-primary);
    --bs-btn-color: var(--bs-white);
}
```

- Bootstrap utilities such as `.d-flex` and `.d-none` use `!important`, so the `hidden` attribute and ordinary rules
  lose to them. Toggle `.d-none` instead.
- `animation-fill-mode: both` or `forwards` pins the last keyframe above every later declaration for that property.
  Use `backwards` when the element must stay restylable after the animation.
- Bootstrap 4 class names (`.ml-2`, `.float-right`, `.font-weight-bold`, `.sr-only`, `.badge-primary`,
  `.custom-select`, `.media`) still work only through Boost's compatibility layer, removal planned for 6.0. Each use
  shows a red "Deprecated style in use" marker in theme designer mode and fails Behat runs started with
  `--scss-deprecations` (`public/theme/boost/scss/moodle/deprecated.scss`, `bs4-compat.scss`; read 5.2 and 5.3,
  identical). Write `.ms-2`, `.float-end`, `.fw-bold`, `.visually-hidden` in templates and in markup built by
  JavaScript.
- Boost's fixed navbar is `$navbar-height: 60px` (`scss/moodle/variables.scss`). Offsets for sticky or scrolled-to
  elements start below it, not at 0.

## Stylelint

`moodle-plugin-ci grunt` lints a theme's whole `scss/` tree with core's `.stylelintrc`, identical in 5.2 and 5.3
(read; moodle-plugin-ci 4.5.11). With an `scss/` directory present, the theme's `style/*.css` is not linted. Locally,
from the Moodle root with the Node dependencies installed: `npx stylelint "public/theme/mytheme/scss/**/*.scss"`
(**run 5.3.0**). What trips most often: `!important` without a disable comment, single-line rule blocks, indentation
other than four spaces, `data:` URLs, durations under 100 ms, upper-case or long hex colours (warnings, but CI allows
none), and syntax the validator does not know (`container-type`, `@container`). The rule list and the disable
comments are in the build and lint reference.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `@import "bootstrap/functions"` (or any Bootstrap, Font Awesome or token partial) | 5.3: "file not found for @import", whole theme falls back to stock Boost (**run 5.3.0**) | Import nothing in `post.scss`; elsewhere use only the wrapper names |
| Shipping a copy of Boost's `preset/default.scss` | A 5.3 copy fails on 5.2 (`moodle/font-stack` missing); a 5.2 copy on 5.3 loses fonts, grey body and mode-following cards (read) | Call `theme_boost_get_main_scss_content()` at compile time |
| Variable override placed in `post.scss` | No effect on Bootstrap or Boost output | Move it to `pre.scss` or the pre-SCSS callback |
| `$gray-200`, `tint-color()` or `@include` in pre-SCSS | Compile error, silent fallback | Literals and Sass built-ins only in pre-SCSS |
| Repeating Boost's pre or extra SCSS callback code in the child | Brand colour and raw SCSS emitted twice | Rely on the inherited callbacks; add only your own |
| `$THEME->scss = 'main';` (a file name) in a child | Only the child's `scss/` is an import path, so `@import "moodle"` is not found (read: `core_scss::set_file()`) | Use the closure form |
| No `$THEME->scss` in the child, but files in its `scss/` | Boost's closure is used and the child's `scss/` is not on the import path (read: `get_scss_property()`) | Set the closure in the child |
| Child file `scss/moodle.scss` or `scss/bootstrap.scss` created by accident | It replaces Boost's file of that name; most of the page loses its styles | Keep theme files in `scss/mytheme/` |
| `@media (prefers-color-scheme: dark)` | Dark rules on light pages and the reverse | `[data-bs-theme="dark"]` |
| `@include dark-mode` in a theme that supports 5.2 | Compile error on 5.2 (read) | Plain selector, or a prefixed copy of the mixin |
| `var(--mds-...)` with no fallback in a 5.2-5.3 theme, or in editor CSS | Property undefined there: the declaration has no effect | `var(--mds-x, var(--bs-y))` |
| `background: #fff` behind inherited text | White box with light text in dark mode | `var(--bs-body-bg)` or a utility class (`bg-body`) |
| `[[setting:brand]]` in SCSS | Printed literally; core has no such placeholder | SCSS variable from the pre-SCSS callback |
| Raw setting value interpolated into SCSS | A bad value breaks the compile for the whole site, or injects rules | Validate with a pattern before emitting |
| `$THEME->editor_scss = ['editor']` with no `scss/editor.scss` | Editor content loses Bootstrap, fonts and the dark palette (read 5.3.0) | Leave it unset, or ship the file |
| `/* rtl:ignore */` as the last thing in a rule, or written as `//` | Directive does nothing | Put a `/* */` directive directly before a declaration |
| Judging CSS on the first load after a purge | Old stylesheet can be served once | Reload, then check the computed style |

## Reference files

| File | Read it when |
|---|---|
| [reference/design-tokens.md](reference/design-tokens.md) | You need a `--mds-*` / `$mds-*` token name, its light or dark value, or which tokens are safe for mode-following CSS |
| [reference/rebrand-and-presets.md](reference/rebrand-and-presets.md) | Changing the brand colour, typeface, radius or dark surfaces across the whole theme; checking which Bootstrap variables Boost's preset sets; offering or writing a preset |
| [reference/dark-mode.md](reference/dark-mode.md) | A page, component or icon looks wrong in dark mode, or you need what Boost's dark palette re-points and how the mode reaches the page |
| [reference/rtl.md](reference/rtl.md) | The theme must look right in a right-to-left language, a rule must not be flipped, or you need an RTL build to inspect |
| [reference/fonts-and-images.md](reference/fonts-and-images.md) | Shipping a web font, replacing Boost's typeface, or using `[[font:]]` / `[[pix:]]` beyond the one-line form |
| [reference/editor-css.md](reference/editor-css.md) | Content inside the TinyMCE editor must be styled, or the editor lost its styles |
| [reference/build-and-lint.md](reference/build-and-lint.md) | Stylelint fails or must be silenced, CI lints the theme, or you are considering a precompiled fallback stylesheet |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](versions/moodle-5.2.md): where the libraries live, what only resolves on 5.2, what is absent |
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md): `lib/bundles`, new partials and helpers, variables that became `var()`, the plain preset |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme/styles
- https://moodledev.io/docs/5.3/guides/colourmodes
- https://moodledev.io/docs/5.3/guides/bs5migration
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/fonts (out of date on core font location, subfolders and
  `.woff2`; `public/theme/font.php` and `theme_config::resolve_font_location()` are the authority)
- https://moodledev.io/general/development/policies/codingstyle/css
- https://moodledev.io/general/designsystem/overview
