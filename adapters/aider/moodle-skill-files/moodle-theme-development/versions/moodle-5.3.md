# Moodle 5.3: what is specific to the theme engine

Read this when the theme targets Moodle 5.3, when a 5.2 theme is being moved to 5.3, or when planning for the
versions after 5.3.

Read in the 5.3.0 source unless a line says "run on 5.3.0". The upgrade itself, with every changed template,
selector and API, is the subject of `moodle-5-3-changes`.

## Version numbers

| Item | Value | Source |
|---|---|---|
| Branch | `503`, `MOODLE_503_STABLE` | `public/version.php` |
| `$plugin->requires` for 5.3.0 | `2026100500` | `public/version.php` |
| `theme_boost` version | `2026100500` | `public/theme/boost/version.php` |

A 5.3-only theme: `$plugin->requires = 2026100500; $plugin->supported = [503, 503];` and
`$plugin->dependencies = ['theme_boost' => 2026100500];`.

## What changed in the engine

| Change | What a theme has to do |
|---|---|
| Bootstrap, Font Awesome and the design-system tokens moved out of Boost into `lib/bundles/` at the Moodle root, outside `public/`. Boost's `scss/bootstrap.scss`, `scss/fontawesome.scss` and `scss/design-system.scss` are wrappers that import them | Import through Boost's wrapper names, never a path into `scss/bootstrap/`. An import of a file that is not there fails the whole compile, and the site shows stock Boost (run on 5.3.0). `moodle-theme-scss` has the portable imports |
| `core_scss` also accepts imports whose real path is under `lib/bundles` | Nothing; this is what makes the wrappers work |
| The core font lookup moved from `public/lib/fonts/` to `lib/bundles/fontawesome/webfonts/` | Use `[[font:core\|name.ext]]`; do not build the path by hand |
| `\core\output\renderer_base::render_react_component()` and `html_writer::react_component()` exist; the primary and secondary navigation are rendered by React components | Template overrides no longer reach those parts. `moodle-theme-layouts-templates` and `moodle-theme-renderers-output` cover what can still be changed |
| React component overrides are looked up in the active theme's `js/esm/build/overrides/` only | A parent theme's override is not inherited by its children |
| On theme uninstall, `cohort.theme` is now blanked along with course, category and user | Nothing |

Everything else in `theme_config`, the renderer factories, the template finder, the revision functions, the
stylesheet scripts, theme selection and the two CLI scripts is unchanged from 5.2.

## Classic is no longer in core

- `public/theme/classic/` does not exist. A theme with `'classic'` in `$THEME->parents` cannot be initialised on a
  stock 5.3 site: every page falls back to the site theme or Boost with a debugging notice, and a
  `'theme_classic'` entry in `$plugin->dependencies` blocks installation.
- The core upgrade handles a site that used Classic only when Classic's code is absent: compatible settings are
  copied to Boost and Classic is uninstalled, which resets every course, category, cohort and user theme that
  named it. Presets, the dark navbar setting and block positions in the second block column are not carried over;
  blocks from regions Boost does not have are shown at the end of the default region.
- `$CFG->theme = 'classic';` forced in the site's `config.php` is not changed by the upgrade and has to be edited
  by hand.
- The upgrade note says Classic can be installed separately before upgrading, which skips the migration. A theme
  built on Classic then depends on that separately installed plugin, and owns the things Classic provided: a
  two-column layout with `side-pre` and `side-post` regions, its navbar template and its SCSS.

Source: `public/theme/UPGRADING.md`, 5.3 section.

## Colour modes reach every Boost child

- Boost can render light and dark modes, written to the `data-bs-theme` attribute of `<html>`. The feature is
  experimental and off until the site enables `theme_boost/enablecolourmodes`.
- The switch and the default mode are read from the `theme_boost` component, not from the active theme, and they
  apply to any theme that is Boost or has `boost` in `parents`. A child theme cannot opt out with a setting of its
  own. Once the site turns the feature on, a child with hard-coded light colours shows unreadable combinations in
  dark mode.
- So on 5.3 every Boost child has to be checked in dark mode, whether or not it was designed for it.
  `moodle-theme-scss` owns the SCSS side; `moodle-theme-testing-release` owns the checks.

Source: `public/theme/boost/classes/colour_mode.php`, `public/theme/boost/UPGRADING.md` 5.3. Dark-mode custom
properties in a child were run on 5.3.0.

## Build time on 5.3.0

The Boost CSS build is noticeably slower on 5.3.0 than on 5.2 because of a contrast loop in the dark-mode SCSS; the
tracker issue MDL-90109 records a fix in 5.3.1. Not measured here. Allow for it in `build_theme_css.php` runs, in
PHPUnit tests that compile the theme, and in the first page load after a purge.

## Planning past 5.3

- 5.3 is a long-term support release. Under the deprecation policy, what was deprecated in 4.5, 5.0, 5.1 or 5.2
  is due for removal in 6.0, and what was deprecated in 5.3 is due for removal in 7.0
  (https://moodledev.io/general/development/policies/deprecation).
- For the theme engine itself nothing is announced: the `$THEME` keys, the parent rules, the selection order and
  the caches described in the skill body are the same from 5.2 to 5.3, and the official theme pages for the next
  version have no differences from 5.3.
- What is announced for 6.0 is in other layers: the Bootstrap 4 compatibility SCSS and JavaScript, and several
  deprecated renderer methods and templates. `moodle-theme-scss` and `moodle-theme-renderers-output` list them.
- Keep each copy of a core or Boost file next to an untouched copy of its upstream. The next port is then a
  comparison of the old upstream with the new one. `moodle-theme-layouts-templates` describes the method.
