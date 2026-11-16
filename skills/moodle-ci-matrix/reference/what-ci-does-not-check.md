# What a green moodle-plugin-ci run does not check

Read this when a plugin with green CI is about to be submitted to the Plugins directory, a reviewer raised something
CI did not catch, or you need to know exactly what one moodle-plugin-ci step checks.

Read in the moodle-plugin-ci 4.5.11 source (with moodle-cs 3.7.0 and local_moodlecheck 1.3.2) and against the
Moodle Plugins directory submission guidelines; not run for this file. The pre-submission walk itself is
`moodle-release-preflight`; building the release ZIP is `moodle-plugin-release`.

## What each step really checks

| Step | Checks | Does not check |
|---|---|---|
| `phplint` | PHP syntax of every `*.php` | anything else |
| `phpcs` | moodle-cs on `*.php` only: style, boilerplate, `@copyright` and `@license` tags present, lang file syntax and order, `require_login` after `config.php`, forbidden functions (`eval`, `extract`, `print_r`, `error_log`, ...) | `.mustache`, `.js`, `.scss`, `.css`, `.xml` headers; whose name is in `@copyright`; frankenstyle prefixes on global functions (only lower case is checked); `unserialize()` and `call_user_func()`; direct `$_GET`/`$_POST` use |
| `phpdoc` | five local_moodlecheck rules about inline phpdoc tags and function arguments | docblock presence (that moved to phpcs) |
| `phpmd` | prints mess findings | can never fail: exits 0 |
| `validate` | required files (`version.php`, the lang file, per type: `config.php` for a theme; `lib.php`, `mod_form.php`, `view.php`, `index.php`, `db/install.xml`, `db/access.php` for a module), the `pluginname` string (`filtername` for a filter), the `db/install.xml` table prefix, `xmldb_<component>_upgrade()`, `@<type>` and `@<component>` tags on every feature | a licence file, README, `thirdpartylibs.xml`, a privacy provider, backup and restore for a module, `choosereadme` for a theme, `cachedef_<area>` strings |
| `savepoints` | each `db/upgrade.php` step has its savepoint | the upgrade step's logic |
| `mustache` | each `*.mustache` outside `templates/mobileapp/`: syntax, `@template` docs and `Example context (json):`, HTML validation, ESLint on `{{#js}}` blocks; any warning fails | files not named `*.mustache` exactly; HTML validation of files matched by a `.mustachelintignore` next to them |
| `grunt` | eslint over `amd/src` (subdirectories included), stylelint over `styles.css` (a theme: its `scss/` tree), gherkinlint over `tests/behat/*.feature`, and that no `*.js`, `*.js.map` or `*.css` changed when rebuilt | a theme's `style/*.css` when the theme has `scss/`; a hand-run `npx grunt --force` downgrades failures to warnings, so it is not a substitute for this step |
| `phpunit` | the plugin's own tests | core's privacy compliance test (`public/privacy/tests/privacy/provider_test.php`), which covers every installed plugin but runs only in a full core suite |
| `behat` | the plugin's own features, tagged `@<component>`, with reruns | pages no scenario visits |

`thirdpartylibs.xml` locations are removed from phplint, phpcs, phpdoc, phpmd and mustache, so a vendored library
that is not declared there shows up as hundreds of phpcs errors, the only signal that the declaration is missing.

## Rules nothing in CI checks

The Plugins directory review applies the submission guidelines, and moodle-plugin-ci is only the automated part of
it. Every rule below is in the guidelines and none is checked by the standard workflow. The licence file
(by far the most frequent), ZIP root, missing strings, prefixes, capability, `PARAM_RAW` and `mkdir` rows are ones
reviewers have raised on plugins whose CI was green. The check on the right catches it before
submission.

| Rule | Check before submitting |
|---|---|
| The package includes a licence file in its root | `LICENSE` with the full GPL v3 text in the repository root, committed and pushed before the tag; then `unzip -Z1 plugin.zip \| grep -x 'example/LICENSE'` on the built ZIP |
| The ZIP's single root folder is the plugin name without its type (`example/` for `local_example`) | `unzip -Z1 plugin.zip \| cut -d/ -f1 \| sort -u` prints exactly one line; never upload a GitHub source archive (`moodle-local_example-1.0.0/`) |
| `.gitattributes` does not drop required files | `export-ignore` lines leave `LICENSE`, `version.php`, `lang/en` and `amd/build` in the archive; check the ZIP listing, not the repository |
| Every string the code or core asks for exists | for each `db/caches.php` definition, `cachedef_<area>`; `pluginname` for every type, a filter included; `choosereadme` for a theme; every literal `get_string('x', 'local_example')` and `{{#str}} x, local_example }}` key |
| Global functions, classes and constants carry the full frankenstyle prefix | `grep -rnE '^\s*function [a-z_0-9]+' --include=*.php .` outside `classes/` and `tests/`: every name starts with the component (or `xmldb_`), including helpers in page and CLI scripts |
| Each page and web service function checks a capability, not only `require_login()` | for each script with `require_login`, a `require_capability` or `has_capability`; sibling actions make the same checks as the main one |
| Input uses the narrowest `PARAM_*` type | `grep -rn 'PARAM_RAW' --include=*.php .`; each hit gets a narrower type or a one-line reason in a comment |
| Directories use core's helpers and permissions | `grep -rn 'mkdir(' --include=*.php .`; expect `make_temp_directory()`, `make_request_directory()` or `$CFG->directorypermissions` |
| A privacy provider exists and is complete | `classes/privacy/provider.php`; run core's privacy test once on a site with the plugin installed (`moodle-privacy-gdpr`) |
| An activity module implements backup and restore | `backup/moodle2/`; for course-scoped tables in other plugin types, decide and document why they are or are not backed up |
| The plugin works on PostgreSQL as well as MySQL | a blocking PostgreSQL row for every branch, and tests that reach the SQL |
| Bundled third-party code, fonts and media are declared | one `thirdpartylibs.xml` entry per library, font or icon set, with its licence |

## Traps

- **A licence file added after the tag, or committed and not pushed, is still missing from the reviewed ZIP.**
  Build the ZIP from the tag you submit and list it.
- **`validate` and the reviewer's tooling can disagree.** `validate` asks a filter for `filtername`; review asked
  for `pluginname` too. Satisfy both.
- **A reviewer's suggested fix is not always right.** A suggested `PARAM_*` type can strip characters valid input
  needs; check the suggestion against real input, and answer with the reason when you keep the original. A reasoned
  answer is accepted.
- **Reviewers often link 4.5 documentation pages.** Read the page for your branch; the rule is the same, the
  details may not be.
