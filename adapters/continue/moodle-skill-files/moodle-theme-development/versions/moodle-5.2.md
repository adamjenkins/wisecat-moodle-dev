# Moodle 5.2: what is specific to the theme engine

Read this when the theme has to run on Moodle 5.2, or when moving a 5.2 theme forward and you need to know what
it was relying on.

Everything here was read in the 5.2 source (5.2.2). Nothing was run on 5.2.

## Version numbers

| Item | Value | Source |
|---|---|---|
| Branch | `502`, `MOODLE_502_STABLE` | `public/version.php` |
| `$plugin->requires` for 5.2.0 | `2026042000` | branching date in `public/version.php` |
| `theme_boost` version | `2026042000` | `public/theme/boost/version.php` |
| `theme_classic` version | `2026042000` | `public/theme/classic/version.php` |

## The engine is the same as on 5.3

`theme_config.php` differs from 5.3 in one hunk, the core font lookup below. The renderer factories, the Mustache
template finder, `outputlib.php`, `theme/styles.php`, `theme/styles_debug.php`, `resolve_theme()`, the theme
selector, `admin/cli/purge_caches.php`, `admin/cli/build_theme_css.php` and Boost's `config.php` are identical in
both versions. Every rule in the skill body applies to 5.2 unless it is tagged **5.3+**.

## What exists on 5.2 only

- **Classic is a core theme.** `public/theme/classic/` exists, with `$THEME->parents = ['boost']`. A theme with
  `$THEME->parents = ['classic', 'boost']` and `'theme_classic' => 2026042000` in its dependencies loads on a stock
  5.2 site and does not on a stock 5.3 site.
- **Bootstrap and Font Awesome SCSS live inside Boost**, in `public/theme/boost/scss/bootstrap/` and
  `public/theme/boost/scss/fontawesome/`. There is no `lib/bundles` directory at the Moodle root.
- **Core fonts are in `public/lib/fonts/`.** `[[font:core|fa-solid-900.woff2]]` resolves there. A theme that builds
  a file path to that directory by hand works on 5.2 and breaks on 5.3; the placeholder works on both.
- **SCSS imports are accepted only from theme directories.** `core_scss::is_valid_file()` on 5.2 checks the
  `theme/` directory under `$CFG->dirroot` and `$CFG->themedir`, nothing else.

## What does not exist on 5.2

| Missing on 5.2 | Effect on a theme written for 5.3 |
|---|---|
| Boost's colour modes: `\theme_boost\colour_mode`, the settings `theme_boost/enablecolourmodes` and `theme_boost/defaultcolourmode`, the `data-bs-theme` attribute, Boost's `scss/moodle/colour-mode.scss` | PHP that calls `\theme_boost\colour_mode` is a fatal error; SCSS that includes Boost's `dark-mode` mixin fails to compile, and the whole theme falls back to stock Boost CSS. `moodle-theme-scss` has the portable form |
| Theme overrides of React components: the import map has no theme lookup | A `js/esm/build/overrides/` directory is ignored |
| Hooks `\core\hook\output\before_requirejs_config` and `\core\hook\output\before_import_map_config` | Registering a callback for a hook class that does not exist is harmless: the entry is stored by name and never fires |
| `\core\user::update_user()` | Use `user_update_user()` from `public/user/lib.php` |
| Cohort cleanup on theme uninstall | `cohort.theme` keeps the name of an uninstalled theme; the cohort level then fails to load it and falls back |

## One codebase for 5.2 and 5.3

- `$plugin->requires = 2026042000; $plugin->supported = [502, 503];` and
  `$plugin->dependencies = ['theme_boost' => 2026042000];`.
- Keep to what is identical in both: the `$THEME` keys, SCSS on top of Boost's preset, settings, hooks that exist
  in both, renderer overrides of methods that exist in both.
- A layout template copied from 5.3 Boost is not portable: `drawers.mustache` from 5.3 includes a partial that 5.2
  does not have, which is a fatal render error on 5.2, not a cosmetic difference (read, not run). A theme that
  copies Boost's layout templates needs a branch per Moodle version; `moodle-theme-layouts-templates` covers the
  method.
