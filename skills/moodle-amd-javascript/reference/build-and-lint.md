# Building and linting AMD modules

Read this when grunt or `moodle-plugin-ci grunt` fails, the built file looks stale, you vendor a third-party
library, or you split code into sub-folders of `amd/src`. Facts were read in `Gruntfile.js` and `.grunt/` of 5.2 and
5.3.0 and in moodle-plugin-ci's `GruntCommand.php`; nothing was run.

## What `grunt amd` does

| Step | 5.2 | 5.3 | Effect |
|---|---|---|---|
| `ignorefiles` | yes | yes | Writes `.eslintignore` and `.stylelintignore` at the Moodle root from every `thirdpartylibs.xml` |
| `eslint:amd` | yes | yes | Lints `amd/src` with the root `.eslintrc` |
| `rollup` | yes | yes | Babel (with `.grunt/babel-plugin-add-module-to-define.js` and `system-import-transformer`), then terser; writes `amd/build/<path>.min.js` and `.min.js.map` |
| `amdtypes` | no | yes | Writes `.d.ts` declarations under the Moodle root's `.types/`; nothing in the plugin |

Source: `.grunt/tasks/javascript.js:62` in both versions. `grunt js` is `amd, yui, react` on 5.2 and
`amd, yui, esm` on 5.3 (line 63).

The working directory decides the scope: grunt run inside a plugin directory builds and lints that component only
(`Gruntfile.js` `getCwd()`, `inComponent`). `--root=<path>` is resolved against the directory holding
`Gruntfile.js`, so on 5.1 and later it is `--root=public/local/example`; a path that does not exist is a fatal
"Setting root to ... failed - path does not exist".

```bash
cd /path/to/moodle && nvm use && npm ci       # Node from .nvmrc: lts/jod on 5.2 and 5.3
cd public/local/example && npx grunt amd      # one plugin
npx grunt watch                               # rebuild on save, from the plugin directory
```

The plugin must be inside a Moodle checkout, because the root `.eslintrc`, the Babel plugin and `node_modules` are
core's. Build against the lowest branch you support: the output is the same JavaScript, but the lint rules and
Babel targets come from that branch.

## What CI checks

`moodle-plugin-ci grunt` runs the tasks `amd`, `yui`, `gherkinlint` and `stylelint` by default, then compares every
`*.js`, `*.js.map` and `*.css` in the plugin with what it built. Any difference fails with the file named, so a
committed build that is not byte-identical to a fresh build is a failure, not a warning.

- Commit `amd/build/*.min.js` and `*.min.js.map` in the same commit as the `amd/src` change.
- Use the same Node major and the same Moodle branch as CI's lowest matrix row, or the minified output can differ.
- `--max-lint-warnings 0` turns every eslint warning into a failure; use it locally too:
  `moodle-plugin-ci grunt --max-lint-warnings 0`.
- `grunt --force` is not a build check. Under `--force` a failing eslint step is skipped while its banner still
  prints, and a failed write leaves the previous build in place with "Done, but with warnings". After any build,
  confirm the `amd/build` files are newer than their sources and the diff contains them (`moodle-definition-of-done`).

## Sub-folders and module names

- `amd/src/net/client.js` is the module `local_example/net/client`, built to `amd/build/net/client.min.js`.
- There is no index fallback: `local_example/net` loads `amd/build/net.min.js` and nothing else
  (`core_requirejs::find_one_amd_module()`, `public/lib/classes/requirejs.php`). To offer a short name, add a
  re-export module:

```javascript
// amd/src/net.js
export {fetchItems, saveItem} from 'local_example/net/client';
```

- Import your own modules by their full id (`'local_example/net/client'`), not by a relative path; the id is what
  RequireJS resolves at run time.

## Vendoring a third-party browser library

1. Put it under `amd/src/local/<lib>/` if it can be an AMD module (an ES module that grunt can build), or under
   `js/<lib>/` if it must stay as shipped.
2. List the directory in `thirdpartylibs.xml` so that `ignorefiles` excludes it from eslint and the Plugins
   directory sees the licence:

```xml
<?xml version="1.0"?>
<libraries>
    <library>
        <location>amd/src/local/chartlib</location>
        <name>chartlib</name>
        <version>4.2.1</version>
        <license>MIT</license>
        <licenseversion></licenseversion>
        <repository>https://github.com/example/chartlib</repository>
    </library>
</libraries>
```

3. Name browser-fetched ES module files `.js`. Many web servers have no `application/javascript` type for `.mjs` and
   send `application/octet-stream`, which browsers refuse for a module script.
4. Keep browser-fetched files out of any path segment named `vendor`, `node_modules`, `fixtures` or `behat`. Core's
   security check `core\check\environment\publicpaths` (`public/lib/classes/check/environment/publicpaths.php`, 5.2
   and 5.3) expects the web server to deny them, so a correctly configured production site returns 404 for those
   files while a permissive development server serves them.
5. Record the upstream version and any local change in a `readme_moodle.txt` next to it, as core does.

## Errors and what they mean

| Message | Cause | Fix |
|---|---|---|
| `No define call for local_example/x` (RequireJS, in the console) | The file served for the id is not an AMD module: an unbuilt file, a 404 page, or a vendored ES module loaded through RequireJS | Build it; check the id maps to an existing `amd/build/<path>.min.js` |
| `Script error for "local_example/x"` | The request for the built file failed | Check the path, the `jsrev` cache (purge caches) and the web server rules above |
| Named import is `undefined` at load | The module has `export default` as well as named exports | One export style per module (SKILL.md) |
| `Setting root to ... failed - path does not exist` | `--root` without `public/` on 5.1+ | Run inside the plugin, or add `public/` |
| `Too much data passed as arguments to js_call_amd` (developer debugging) | Third argument of `js_call_amd()` over 1024 characters as JSON | Pass ids; read the rest from `data-*` or a web service |
| CI's grunt step fails after building, naming files under `amd/build/` | Committed build differs from a fresh one | Rebuild with CI's Node and branch, commit both files |

## ESLint in practice

- Every exported function has a JSDoc block with `@param` for each argument and `@return` when it returns; the
  `@module` line in the file header must match the module id.
- `no-console` is on: use `core/log`.
- `promise/catch-or-return` and `promise/always-return` are warnings in core's config; with
  `--max-lint-warnings 0` they fail CI. End chains with `.catch(Notification.exception)`.
- An intentionally empty function needs a comment body: `() => { /* Intentionally empty. */ }`.
- Rules are applied by path from the root `.eslintrc`, so a copy of the plugin outside a Moodle tree lints with the
  wrong rules or none.
