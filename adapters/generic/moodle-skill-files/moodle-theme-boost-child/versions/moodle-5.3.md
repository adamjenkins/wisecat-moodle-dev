# Boost child themes on Moodle 5.3

Read this when a Boost child targets Moodle 5.3, when a child written on 5.2 is moved to 5.3, or when checking
what is announced for removal after 5.3. Read from the 5.3.0 source and
`public/theme/boost/UPGRADING.md`; items marked "run" were seen in a Boost child on 5.3.0.

## version.php for a 5.3-only theme

```php
$plugin->requires  = 2026100500;                        // Moodle 5.3.0.
$plugin->supported = [503, 503];
$plugin->dependencies = ['theme_boost' => 2026100500];  // Boost as shipped with 5.3.0.
```

## What a child gets from Boost 5.3 without doing anything

| New in Boost 5.3 | What it means for a child |
|---|---|
| Colour modes (experimental, off by default). Settings `theme_boost/enablecolourmodes` and `theme_boost/defaultcolourmode`; classes `theme_boost\colour_mode`, `theme_boost\hook_listener`; `db/hooks.php` | Once an admin turns it on in Boost's settings, every theme with `boost` in its parents gets `data-bs-theme="light\|dark"` and `data-colourmode` on `<html>` (`colour_mode::is_boost_theme()`). The child has no setting to opt out. A child's hard-coded light surface then sits under light text |
| `core_renderer::colour_mode_menu()` and `core_renderer::search_box()` in Boost's renderer | Available to a child whose renderer extends `\theme_boost\output\core_renderer`. Boost's `navbar.mustache` prints the switcher; a child with its own navbar template has to print it too |
| User preference and cookie `theme_boost_colourmode` | Declared and exported by `theme_boost`. The child's privacy provider does not mention them |
| Default typeface is self-hosted Noto Sans (`public/theme/boost/fonts/`), Noto Sans JP under `:lang(ja)` | A child that relied on the system font stack now renders in Noto Sans. Set `$font-family-sans-serif` in `pre.scss` to keep another face |
| Bootstrap 5.3.8, Font Awesome and the design system moved to `lib/bundles/` at the repository root, outside `public/`; Boost's `scss/bootstrap.scss`, `scss/fontawesome.scss`, `scss/design-system.scss` are now one-line wrappers | `@import "bootstrap";` still works. Any import of a path inside Bootstrap fails (run: "file not found", then plain Boost) |
| `--mds-*` custom properties are emitted | Usable in a 5.3-only child. In a 5.2-5.3 child write a fallback: `var(--mds-text-default, var(--bs-body-color))` |
| Primary and secondary navigation and the edit switch are rendered by React components | Selectors such as `.primary-navigation .nav-link.active` match nothing when JavaScript is on; the new hooks are `.mds-nav-pill` and `.mds-nav-pill--selected` (`moodle-theme-layouts-templates`) |
| The Classic theme is no longer in core | Core 5.3 has no worked example of a Boost child. A theme with `classic` in `parents` or in `dependencies` cannot be installed on a stock 5.3 site |

## A child written on 5.2: what to re-check on 5.3

| In the child | What changed in 5.3 | Symptom | Fix |
|---|---|---|---|
| SCSS colour functions on Boost variables: `darken($state-success-bg, 5%)`, `rgba($dialogue-base-bg, .9)`, `mix($formlisting-bg, ...)` | about fifty variables in Boost's `scss/moodle/variables.scss` now hold `var(...)`, among them the eight `$state-*-bg` and `$state-*-border` and twelve `$dialogue-*`; none did on 5.2. In the default preset so do `$card-bg` and `$card-border-color` | Compile error (a colour function given a `var()` string), so the site shows plain Boost | Compute from a literal colour of your own, set in `pre.scss` |
| A white page assumed | `$body-bg` is `$gray-100` in the default preset; the navbar lost its preset box-shadow | Panels that were invisible on white now show as white boxes on grey | Use `var(--bs-body-bg)`, or set `$body-bg` in `pre.scss` |
| Copy of `templates/drawers.mustache` or `columns2.mustache` | `core/moremenu` became `core/secondarymoremenu`; the `drawerheadercontent` block of `theme_boost/drawer` was removed and `drawercontrols` added | The 5.2 copy still renders, with the legacy menu and without the course index expand/collapse control | Re-diff against the 5.3 file (`moodle-theme-layouts-templates`) |
| Copy of `templates/navbar.mustache` | `core/moremenu` became `core/primarymoremenu`; a colour mode menu block was added | No switcher: where the site default is dark, a logged-in user cannot change it | Add `{{# output.colour_mode_menu }}{{{ . }}}{{/ output.colour_mode_menu }}`; it renders nothing on 5.2 |
| Override at `templates/core/loginform.mustache` | The template moved from Boost to core with new markup | The override still wins but shows the old markup | Re-diff against `public/lib/templates/loginform.mustache` |
| Renderer that overrides or calls `render_login()` from Boost | Boost's method was removed; core's no longer adds `logourl`, `sitename`, `hasauthinstructions` to the context | `parent::render_login()` now reaches core's version with a different context | Build the context yourself, or drop the override |
| Renderer code copied from Boost 5.2 that calls `user_can_view_profile()` and other `user/lib.php` functions | Moved to `\core\user`; the old functions emit a debugging notice | Notices, and Behat failures, on 5.3 | `\core\user::can_view_profile()` on 5.3; it does not exist on 5.2, so branch on `method_exists()` or split the branches |
| Renderer override of `block_timeline\output\renderer` | The class was removed with no stub | Fatal error when the override is autoloaded | Delete the override |
| Copy of `templates/courseindexdrawercontrols.mustache` | The dropdown became one toggle button handled by changed JavaScript | Buttons that do nothing | Re-copy |
| AMD code importing `theme_boost/bootstrap/tooltip` and similar | Deprecated; the names still resolve through a compatibility map | Works, with removal announced | `import {Tooltip} from 'theme_boost/index';` works on 5.2 and 5.3; `from 'bootstrap'` is 5.3 only |
| A file path built by hand to `lib/fonts/` | Core fonts moved to `lib/bundles/fontawesome/webfonts/` | File not found | Use the `[[font:core\|name]]` placeholder, which works on both |

Run on 5.3.0: the failed import of a Bootstrap path, and that any SCSS error ends in plain Boost. Everything else
in this table is read from a diff of the 5.2 and 5.3.0 trees; in particular the colour-function error was
predicted from the changed variables, not reproduced.

## Testing for 5.3 features in PHP

```php
$hascolourmodes = class_exists(\theme_boost\colour_mode::class);
$hasreactnav = class_exists(\core\output\react_component_renderable::class);
```

Prefer these to `$CFG->branch`, which still holds the old branch while the core upgrade is running. In SCSS,
`mixin-exists(dark-mode)` is false in pre SCSS even on 5.3, because Boost's partials have not been imported yet;
it can only be true in post SCSS. A dual-version child is simpler with the plain selector
`[data-bs-theme="dark"]`.

## Build time on 5.3.0

The Boost SCSS build is several times slower on 5.3.0 than on 5.2 and is fixed in 5.3.1 according to the tracker
(MDL-90109); not measured here. If a child's first page load after a purge times out on 5.3.0, check the core
version before blaming the child's SCSS.

## Removals already announced

Core's deprecation policy removes things deprecated in 4.5 to 5.2 in 6.0, and things deprecated in 5.3 (the
long-term support release) in 7.0
(https://moodledev.io/general/development/policies/deprecation). A child written today should already avoid:

| Item | Announced removal | Source |
|---|---|---|
| Bootstrap 4 compatibility SCSS: `.media`, `.badge-*`, `.ml-*`, `.sr-only`, `.form-inline`, `.custom-*`, and the mixins `hover()`, `hover-focus()`, function `color-yiq()` | 6.0 | `public/theme/boost/scss/moodle/bs4-compat.scss`, line 1 |
| `theme_boost/bs4-compat` JavaScript, which rewrites `data-toggle` to `data-bs-toggle`; it raises a deprecation message when loaded on 5.3 | 6.0 | `public/theme/boost/amd/src/bs4-compat.js` |
| `window.jQuery` kept for Bootstrap's jQuery interface, `$(el).tooltip()` | 6.0 | `public/lib/amd/src/first.js` |
| `core_renderer::sr_text()` (use `visually_hidden_text()`), `core_renderer::render_context_header()` | 6.0 | `public/lib/classes/output/core_renderer.php` |
| `dataattributes` in the `core/toggle` template (use `extraattributes`) | 6.0 | `public/lib/templates/toggle.mustache` |
| AMD names `theme_boost/index` and `theme_boost/bootstrap/*` | 7.0 | `public/theme/boost/UPGRADING.md`; `public/theme/boost/classes/hook_listener.php` |
| `user_*` functions of `user/lib.php` | 7.0 by the policy | root `UPGRADING.md`, 5.3 section |

This table records only what 5.3.0 announces. What a later version really removed belongs in that version's
notes.
