# Boost child themes on Moodle 5.2

Read this when a Boost child has to run on Moodle 5.2, or when a 5.2 child is being moved forward and you need
to know what it relied on. Everything here is read in the 5.2 source (5.2.2); nothing was run on 5.2.

## What is the same as 5.3

The theme engine (`public/lib/classes/output/theme_config.php`) is the same code apart from where core fonts are
found, and Boost's `config.php` and every file in `public/theme/boost/layout/` are identical in 5.2 and 5.3.0.
So the recipe in `SKILL.md` (the keys to restate, the chained SCSS callbacks, the one settings object, the
layout cascade, presets) holds on 5.2 as written.

Boost's version in 5.2 is `2026042000`, the value used for `$plugin->dependencies` in the recipe.

## Things that exist only on 5.2

Using any of these makes the child a 5.2-only theme.

| Only on 5.2 | On 5.3 |
|---|---|
| Bootstrap, Font Awesome and design-system SCSS inside Boost: `public/theme/boost/scss/bootstrap/`, `scss/fontawesome/`, `scss/design-system/`; imports such as `@import "bootstrap/functions";` resolve | The directories are gone; only the wrapper names `bootstrap`, `fontawesome`, `design-system` resolve |
| The `drawerheadercontent` block of the `theme_boost/drawer` template | Replaced by `drawercontrols`. An unknown block is ignored without a message on either version, so a child can fill both |
| `core/moremenu` as the navigation partial in Boost's `drawers.mustache`, `columns2.mustache` and `navbar.mustache` | `core/secondarymoremenu` and `core/primarymoremenu`. The old template still ships in 5.3 |
| `theme_boost\output\core_renderer::render_login()` and Boost's override of `core/loginform` | Both removed; the template lives in core |
| The system font stack as Boost's default typeface | Self-hosted Noto Sans |
| The Classic theme in core, `public/theme/classic/`: the one worked example of a Boost child in core, with two block regions, `'theme' => 'boost'` layout borrowing and its own preset lookup | Removed from core |
| Core fonts under `public/lib/fonts/` | `lib/bundles/fontawesome/webfonts/` |

## Things 5.2 does not have

A child that supports 5.2 cannot rely on these.

| Missing on 5.2 | Effect on a dual-version child |
|---|---|
| Colour modes: no `theme_boost\colour_mode`, no `data-bs-theme` attribute on `<html>`, no `output.colour_mode_menu` | `[data-bs-theme="dark"]` rules are harmless and never match. A Mustache section on a renderer method that does not exist renders nothing, so the 5.3 switcher lines can stay in a shared navbar template |
| Boost's `dark-mode` mixin and `dark-readable()` function (`scss/moodle/colour-mode.scss`) | `@include dark-mode` is a compile error on 5.2. Write the selector `[data-bs-theme="dark"]` directly |
| `--mds-*` custom properties in the compiled CSS | `var(--mds-...)` without a fallback resolves to nothing. `--bs-*` properties are emitted on both versions |
| The templates `core/secondarymoremenu`, `core/primarymoremenu`, `theme_boost/colour_mode_menu` | A copy of Boost 5.3's `drawers.mustache` used on 5.2 throws "file not found" for the partial on every page with secondary navigation; this is an error, not a quiet degrade |
| `lib/bundles/` and SCSS imports that point into it | 5.2's SCSS import check accepts only files under the theme directories (`core_scss::is_valid_file()`, `public/lib/classes/scss.php`) |
| React component overrides for themes | The official page tags theme overrides "since 5.2", but the 5.2 import map has no theme handling; treat it as 5.3 and up |
| `\core\user::can_view_profile()` and the other `\core\user` replacements of `user/lib.php` functions | Renderer code shared by both versions must branch |
| Behat `--colourmode` option | 5.3 only. `--scss-deprecations` exists on both |

## The Classic theme as a reference

On 5.2, `public/theme/classic/` shows patterns this skill describes: a child with its own `pre.scss` and
`post.scss` around a preset, its own `preset` setting and file area (`theme_classic_get_main_scss_content()` in
`lib.php`), `'theme' => 'boost'` in a layout entry to borrow a parent's layout file, and a set of Behat step
overrides. Note that Classic repeats Boost's pre-SCSS logic in `theme_classic_get_pre_scss()`; do not copy that
part, because Boost's callback already runs for a child.
