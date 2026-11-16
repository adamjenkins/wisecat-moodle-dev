# Moodle 5.3: JavaScript specifics

What 5.3 adds or changes against the 5.2 baseline. Read it when the plugin supports 5.3, or when code that works on
5.2 misbehaves on 5.3. Read in the 5.3.0 source unless tagged; the full upgrade list is in `moodle-5-3-changes`.

## Core AMD names served from ES modules

`page_requirements_manager::get_requirejs_static_esm_map()` maps these AMD ids to ES modules through the
`core/esm!` RequireJS plugin (`public/lib/classes/output/requirements/page_requirements_manager.php`):

| AMD id | ES module |
|---|---|
| `core/config` | `@moodle/lms/core/config` (default export) |
| `core/deprecated` | `@moodle/lms/core/deprecated` |
| `core/fetch` | `@moodle/lms/core/fetch` |
| `core/log` | `@moodle/lms/core/log` |
| `core/localstorage`, `core/sessionstorage` | `@moodle/lms/core/Storage` (`localStore`, `sessionStore`) |
| `core/storagewrapper` | `@moodle/lms/core/Storage` (default) |
| `core/pending` | `@moodle/lms/core/pending` |
| `core/url`, `core/utils` | `@moodle/lms/core/url`, `@moodle/lms/core/utils` |
| `core/popper2` | `@popperjs/core` |

Imports by the AMD id keep working; `public/lib/amd/src/pending.js` and the others no longer exist, so code that
reads core's AMD sources (a build script, a copied file) must look in `public/lib/js/esm/src/`. The storage wipe is
`public/lib/js/esm/src/Storage.ts:98-120` and also clears `sessionStorage` on a login change.

## Bootstrap

- `import {Tooltip} from 'bootstrap'` is the 5.3 name. `theme_boost/index` and `theme_boost/bootstrap/*` are mapped
  to it by `theme_boost\hook_listener` and stay until 7.0, but `theme_boost/bootstrap/*` is deprecated
  (`public/theme/boost/UPGRADING.md`, MDL-88766). A plugin for 5.2 and 5.3 keeps `theme_boost/index`.
- `dom` and `util` helpers: `bootstrap/dom/event-handler` on 5.3, `theme_boost/bootstrap/dom/event-handler` on 5.2.
  They are not public Bootstrap API on either.

## ES modules and React

- New AMD helpers: `core/import` (native `import()` that Babel does not rewrite) and `core/component`
  (`appendToDom()`, `prependToDom()`).
- New PHP: `\core\output\html_writer::react_component($specifier, $props)`; pass props unencoded.
- `grunt esm` replaces `grunt react` (kept as an alias); `esm:dev` only warns. Each source file builds to a minified
  `.js` and a `.dev.js` with `.dev.js.map`; with JavaScript caching off the server serves `.dev.js`. Nothing is
  bundled.
- `npm test` runs Jest over the ESM tree.
- `grunt amd` also runs `amdtypes`, writing declarations to the Moodle root's `.types/`.

## Markup that changed under existing selectors

- Modal title: `<h2 class="modal-title fs-5 text-truncate">` (`public/lib/templates/modal.mustache:49`). Selectors on
  `h5.modal-title` match nothing; use `[data-region="title"]`. Body headings start at `<h3>` (`moodle-accessibility`).
- Primary and secondary navigation are React (`core/nav/PrimaryNav`, `core/nav/Nav`), with `a.mds-nav-pill` items
  and `.mds-nav-pill--selected`; `.moremenu` and `.nav-link` selectors match only the no-JavaScript fallback
  (`public/lib/UPGRADING.md`, MDL-87830, MDL-89294). Scripts that query the old navigation markup find nothing.
- `block_timeline` is an ES module (`public/blocks/timeline/js/`); its AMD modules and templates are gone, so a
  plugin or theme that imported or overrode them gets a load error or a dead file.

## New modules worth knowing

- `core/imagedetails/modal` `getImageDetails(file)` shows core's alt text, decorative and size controls in a modal
  and resolves with the choices, or `null` on cancel (`public/lib/amd/src/imagedetails/modal.js:61`). Use it in an
  upload UI that embeds images instead of building an alt-text form.

## Editor

- TinyMCE picks `oxide-dark` when the page has `data-bs-theme="dark"` at setup and keeps it until reload
  (`public/lib/editor/tiny/amd/src/editor.js:57,331`). Dialogs a Tiny plugin opens sit on the main page and use
  the theme's tokens; content CSS for the iframe is `moodle-theme-scss`.
