# Patterns to avoid as a child theme grows

Read this when the child is growing past SCSS and a few overrides: before adding a second way for settings to
reach the CSS, block regions that depend on settings, page HTML built in PHP, or a companion plugin; or when
reviewing a large theme.

These come from reading two large, long-lived public themes built on Boost. Each entry says what was done, what
it costs, and what to do instead. They are design observations from source reading, not test results.

## Structure

| Pattern | Cost | Instead |
|---|---|---|
| Building the page in PHP renderer methods that each echo part of the HTML, one opening `<body>` and a wrapper, a template closing them | No file shows the page structure; the Mustache linter cannot check it; improvements to Boost's layouts never arrive | Keep Boost's layout file and template. Copy one only when needed, with its `.upstream` twin, and add context keys from one small include per feature |
| One renderer class or helper class of several thousand lines that mixes settings access, SCSS building, import/export and layout helpers | Every change risks unrelated features; nothing can be tested alone | `lib.php` holds only what core calls; one class or include per feature |
| Core behaviour of the theme hidden behind a separate companion plugin, with `method_exists()` checks through the theme | The theme alone is incomplete and each call site has two code paths | Keep the theme whole. If an optional plugin integrates, isolate it behind one class |
| Hard-coding the theme's directory or name: `'/theme/example/'`, `theme_config::load('example')` in many places | Breaks under `$CFG->themedir`, in a renamed fork and for descendants | `__DIR__` for own files; the `$theme` argument or `$PAGE->theme` where the active theme is meant |
| Copying Boost's pre or extra SCSS logic into the child | The parent's callbacks also run, so the output is doubled | Add only the child's part; offer Boost's settings under the child's component |

## Settings and CSS

| Pattern | Cost | Instead |
|---|---|---|
| Three mechanisms side by side for getting a setting into the CSS (SCSS variables, a string-replacement table, SCSS built in PHP), with the default repeated in each | Defaults drift apart: the same setting falls back to different colours depending on the path taken | One mechanism: SCSS variables written by the pre-SCSS callback, with the default in one place (`pre.scss`, `!default`) |
| `[[setting:name]]` placeholders in SCSS files, replaced by the theme's own code | Core has no such replacement. The files are not valid SCSS until processed, so they cannot be linted or compiled alone, and a setting missing from the table is never substituted | SCSS variables |
| Reading settings in `config.php` to decide which block regions exist | Turning the setting off orphans the blocks placed in those regions; the theme then needs recovery code | Fixed regions. If regions must be optional, decide per layout through one function, default to `side-pre`, and plan what happens to blocks when a region goes away |
| A region declared under one name in `config.php` and rendered or labelled under another | The region can never show blocks and nothing reports it | One constant per region name, used in `config.php`, the layout and the `region-<name>` string |
| Hundreds of settings and `hide_if` rules on one admin page | A page too long to scan, with every rule evaluated in the browser. The "Too much data passed as arguments to js_call_amd" message sometimes given as the reason does not arise on 5.2 or 5.3: the rules reach the page in a data attribute (`public/admin/settings.php`, read) | Tabs or several settings pages (`moodle-theme-settings`) |
| Checkbox settings (`0`/`1`) feeding SCSS through an `empty()` test | A saved `0` is skipped like "not set" | Select settings with string values, or test against `false` and `''` |
| Printing admin-entered values on a settings page without escaping | Stored markup runs on the settings page | `s()` or `format_text()` on every value echoed back |
| Loading web fonts from a third-party host in the page head | Every visitor's browser contacts that host; a privacy and availability dependency | Ship the font files in the theme's `fonts/` directory and load them with the `[[font:theme\|file]]` placeholder (`moodle-theme-scss`) |

## Upgrade and release

| Pattern | Cost | Instead |
|---|---|---|
| `purge_all_caches()` at the end of every upgrade | Every minor update empties all caches on a production site; core already purges what an upgrade needs | Nothing. For a style change, `theme_reset_all_caches()` inside the step that changed it |
| Upgrade code that runs outside any `if ($oldversion < ...)` block | Runs on every upgrade, forever | Every action inside a version check with its own savepoint |
| An upgrade step that renames a setting by reading it, writing the same name and then unsetting that name | The value is deleted | Read old, write new, unset old; test the step with the old value present |
| `db/install.php` and `db/upgrade.php` recording different "migrated up to" markers | A fresh install replays old migrations on its first upgrade | Install writes the same marker the newest upgrade step writes |
| A "wrong Moodle version" notice inside the settings page, with the branch number hard-coded | Duplicates `$plugin->supported`, which already stops the install | `$plugin->supported` only |
| Hard-coded English text and contact details in PHP | Untranslatable, and a Plugins directory reviewer will ask for it to be changed | Lang strings |
| Empty Behat scenarios and unit tests that cover only option lists | CI is green without rendering a page | At least one test that compiles the theme and one scenario that loads a page with the theme's suite (`moodle-theme-testing-release`) |
| Templates and classes excluded from linting in CI because they do not pass | The excluded files are where the real defects sit (a malformed tag, invalid JavaScript in a template) | Fix the file; exclude only untouched upstream copies |

## PHP slips seen in theme code

Small, but each one shipped and none raised an error.

- `$classes .= ' ' . (isloggedin()) ? 'loggedin' : 'loggedout';` parses as `(' ' . isloggedin()) ? ... : ...`,
  so it always appends `loggedin` with no leading space. Parenthesise the whole ternary.
- A global class used without a leading backslash inside a namespaced file (`instanceof block_move_target`,
  `new coding_exception`). `instanceof` against a class that does not exist is quietly false; the `throw` then
  fails with "class not found". Import with `use`, or write `\coding_exception`.
- `$context = new stdClass(); ... if (!empty($context))` is always true: an object is never empty. Test the
  property you mean.
- A function whose signature was shortened while old call sites still pass the extra arguments. PHP ignores
  them, so the option those arguments carried silently stops working. Search for every caller when changing a
  signature.
- A user-preference web service declared `loginrequired => false` with `PARAM_RAW` names and values, guarded only
  by a list kept on the session. Use the `theme_<name>_user_preferences()` callback in `lib.php` instead: core's
  own preference service then validates the name, the type and who may write it.
- Keys in `config.php` that core does not read (`enable_dock`, `supportscssoptimisation`). They look like
  configuration and do nothing. Check a key against the `$configurable` list in the constructor of
  `public/lib/classes/output/theme_config.php` before relying on it.

## Patterns worth keeping from the same themes

So this file is not only a list of don'ts:

- An untouched `.upstream` copy beside every overridden template, layout or module, and a header comment listing
  the modifications.
- One include per feature that adds keys to the layout's template context.
- Settings read by `get_config()` with the theme's own component everywhere.
- Renderer overrides that call the widget's `export_for_template()`, change the data and render the original
  template, instead of copying the template.
- An upgrade checklist file naming the upstream files to re-diff at each Moodle release.
- Guards for `during_initial_install()` before `get_config()` in `config.php` when the theme reads settings there.
