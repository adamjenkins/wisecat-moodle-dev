# Moodle 5.2: JavaScript specifics

What holds on 5.2 and not on 5.3. Read it when the plugin supports 5.2, or when code written for 5.3 must also run
on 5.2. Read in the 5.2 source (`MOODLE_502_STABLE`); not run.

## Core modules are all AMD

- `core/pending`, `core/config`, `core/log`, `core/url`, `core/localstorage`, `core/sessionstorage` and
  `core/storagewrapper` are ordinary AMD files in `public/lib/amd/src/`. Importing them works the same on both
  versions; only stack traces and source paths differ.
- The storage wipe lives in `public/lib/amd/src/storage_validation.js` (login change: `LocalStorage.clean()`) and
  `public/lib/amd/src/storagewrapper.js` (`jsrev` change). On 5.2 the login check clears `localStorage` only.
- Only three ES modules ship in core: `public/lib/js/esm/src/{mount,profiler,react_autoinit}.ts`.

## Loading ES modules and React

- No `core/import`, no `core/component`, no `html_writer::react_component()`. Mount a component from a template with
  `{{#react}}` (exists on 5.2), or print your own `<script type="module">`.
- `grunt react` builds `js/esm/src`; esbuild bundles npm packages into the output and leaves `react`, `react-dom`,
  `@moodlehq/design-system` and `@moodle/lms/*` external. One minified `.js` with a linked source map per source file.
- No Jest set-up (`package.json` has no `test` script).

## Bootstrap imports

- `import {Tooltip} from 'theme_boost/index'` is the form that works on 5.2 and 5.3; `import ... from 'bootstrap'`
  does not resolve on 5.2.
- Bootstrap's `dom` and `util` helpers load as `theme_boost/bootstrap/dom/event-handler` and the like.

## Build

- `grunt amd` is `ignorefiles, eslint:amd, rollup`; no `amdtypes`. `grunt js` runs `react`, not `esm`.

## Markup that JavaScript selects or builds

- The modal title is `<h5 class="modal-title text-truncate">` (`public/lib/templates/modal.mustache:49`). Select
  it with `[data-region="title"]`, which both versions have, not by tag.
- Primary and secondary navigation are Mustache (`core/moremenu`, `.nav-link`); there is no React navigation.
- `block_timeline` is AMD (`public/blocks/timeline/amd/src/`) with Mustache templates.

## Editor

- TinyMCE always uses the `oxide` skin (`public/lib/editor/tiny/amd/src/editor.js`); there is no dark colour mode.
