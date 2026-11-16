# TypeScript, React and ES modules (`js/esm`)

Read this when writing TypeScript or React under `js/esm/src`, mounting a React component from PHP, Mustache or
AMD, loading an ES module from AMD code, or running Jest. Facts were read in the 5.2 and 5.3.0 source (`.grunt/`,
`.esbuild/`, `public/lib/classes/output/`, `public/lib/js/esm/`); no plugin ES module was built or loaded for this
file. Theme overrides of core React components are theme work: `moodle-theme-renderers-output`.

## The model

- Source: `<plugin>/js/esm/src/**/*.ts` or `*.tsx`. Nothing else is picked up: the build globs
  `**/js/esm/src/**/*.{ts,tsx}` (`.esbuild/plugin/plugincomponents.mjs`, 5.2 and 5.3), so a `.js`, `.jsx` or `.wasm`
  file there is ignored.
- Output: `<plugin>/js/esm/build/**/*.js`, one file per source file. Commit it with the source, as for `amd/build`.
- Specifier: `@moodle/lms/<component>/<path without extension>`, for example `@moodle/lms/local_example/viewer` for
  `local/example/js/esm/src/viewer.tsx`. Every page head carries an import map that resolves `@moodle/lms/` to a
  server route, which serves `<component dir>/js/esm/build/<path>.js` (`core\output\requirements\import_map`).
  Only `.js` and `.js.map` are served: any other path gets `.js` appended before the file is looked up
  (`import_map::add_import()` `$allowedsuffixes` and `resolve_candidate_path()`,
  `public/lib/classes/output/requirements/import_map.php`, read 5.3.0), so a WebAssembly file cannot be shipped
  this way.
- Mounting: `core/react_autoinit` is imported on every page; it finds each `[data-react-component]` element, imports
  the specifier in that attribute, and renders the module's default export with the JSON in `data-react-props`
  (`public/lib/js/esm/src/react_autoinit.ts`). A component module therefore default-exports a function component.
- Bare imports such as `react`, `react-dom`, `@moodlehq/design-system` and `@moodle/lms/...` are resolved by the import
  map, not bundled. **5.2 only:** esbuild runs with `bundle: true` and those names as externals, so another npm
  package you import is bundled into your output file. **5.3+:** nothing is bundled (`bundle: false`); every
  `import` line survives as written, so an npm package that is not in the import map fails in the browser.

## Mounting from PHP and Mustache

On 5.2 and 5.3, from a template, with the `{{#react}}` helper (`public/lib/classes/output/mustache_react_helper.php`):

```mustache
{{#react}}
{
    "component": "@moodle/lms/local_example/viewer",
    "props": {"itemid": {{itemid}}, "title": "{{#str}}viewer, local_example{{/str}}"},
    "id": "local-example-viewer"
}
<p>{{#str}}loading, core{{/str}}</p>
{{/react}}
```

The text after the JSON is the content shown until the component mounts (and without JavaScript). The helper
JSON-encodes `props` with `JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS` and escapes the component name.

**5.3+:** from PHP, `\core\output\html_writer::react_component('@moodle/lms/local_example/viewer', ['itemid' => 3])`
writes the same placeholder `<div>` (`public/lib/classes/output/html_writer.php:856`). Pass an array or object:
the method calls `json_encode()` itself, so a pre-encoded string is encoded twice and the component receives a
string.

## Loading an ES module from AMD

A literal `import()` in `amd/src` is rewritten by Babel into a RequireJS call, which cannot resolve an
`@moodle/lms/...` specifier.

- **5.3+:** `core/import` hides the call from Babel (`public/lib/amd/src/import.js`):

```javascript
import nativeImport from 'core/import';

const {formatTotal} = await nativeImport('@moodle/lms/local_example/totals');
```

- **5.3+:** `core/component` `appendToDom(specifier, props, parent)` and `prependToDom(...)` create the mount
  `<div>` from AMD; `react_autoinit` then mounts it (`public/lib/amd/src/component.js`).
- **5.2 only:** neither module exists. Render the mount point server-side with `{{#react}}`, or load the ES module
  from a `<script type="module">` that you print yourself.

## Build

| | 5.2 | 5.3 |
|---|---|---|
| Task | `npx grunt react` (`react:watch`) | `npx grunt esm` (`react` and `react:watch` are aliases) |
| `grunt js` includes it | yes (`react`) | yes (`esm`) |
| Output | Minified `.js` with a linked source map | Minified `.js` with no map, plus `.dev.js` and `.dev.js.map`; commit all three |
| Bundling | `bundle: true`, framework names external | `bundle: false` |
| Lint | Separate: `npx grunt eslint:react`, which runs with `fix: true` and so rewrites files | Same |
| Type check | None: esbuild strips types | None |

Sources: `.grunt/tasks/react.js` (5.2), `.grunt/tasks/esm.js` (5.3.0), `.grunt/tasks/eslint.js`,
`.esbuild/plugin/plugincomponents.mjs`.

- The build is whole-tree on both versions: it globs every `js/esm/src` under the Moodle root and rebuilds them
  all, whatever directory you run it from. **5.3+:** it also deletes each matching `js/esm/build` directory first. In
  a shared checkout expect changes in core and other plugins; commit only your plugin's files.
- **5.3+:** when JavaScript caching is off (`jsrev = -1`) the server prefers `<module>.dev.js` if it exists
  (`import_map.php:445-455`, read 5.3.0). Shipping
  an updated `.js` with a stale `.dev.js` makes developer sites run different code from production.
- New build files are served under the JS revision in the URL with long cache headers: purge caches after a build.
- moodle-plugin-ci's default grunt tasks (`amd`, `yui`, `gherkinlint`, `stylelint`) neither rebuild `js/esm` nor
  lint `.ts`/`.tsx`, so CI stays green with a stale ESM build. `moodle-plugin-ci grunt -t amd -t yui -t gherkinlint
  -t stylelint -t esm` should add it on 5.3 (derived from moodle-plugin-ci's `GruntCommand.php`, not run).

## Jest

**5.3+:** `npm test` at the Moodle root runs Jest (`package.json` `"test": "jest"`) over the ESM tree. 5.2 has no
Jest set-up and no `grunt jest` task exists on either version, so AMD modules have no unit-test runner: test them
through a JavaScript Behat scenario (`moodle-behat-testing`).

## Things that pass the build and fail in the browser

- A component module with only named exports: `react_autoinit` finds no default export and mounts nothing.
- Props that are not JSON-safe (functions, `Date`, class instances): they arrive as strings or are dropped.
- A component that reads `M.cfg` or other globals at module top level: read them inside the component when it
  renders (**5.3+:** or import `@moodle/lms/core/config`, which exists as `public/lib/js/esm/src/config.ts`; 5.2 ships
  only `mount`, `profiler` and `react_autoinit` as core ES modules).
- Accessibility still applies: a React widget needs the same keyboard and labelling behaviour as markup
  (`moodle-accessibility`).
