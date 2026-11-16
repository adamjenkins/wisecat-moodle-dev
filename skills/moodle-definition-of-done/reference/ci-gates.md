# CI gates in detail

Read this when a `moodle-plugin-ci` step fails or prints nothing you can interpret, when you need the docblock
rules moodlecheck enforces, the lang-sorting check or the standalone moodlecheck CLI, or when you are writing a
local script that stands in for a CI step.

Facts about `moodle-plugin-ci` below were read in version 4.5.11 of its source (`src/Command/*.php`) with
moodle-cs 3.7.0 and local_moodlecheck 1.3.2, not observed in a run unless stated. Later versions may differ.

## What each step checks, and how it can mislead

| Step | Checks | Exit code | Trap |
|---|---|---|---|
| `phplint` | PHP syntax of every `*.php` | Real | None |
| `phpcs` | moodle-cs on `*.php` only | Real; `--max-warnings 0` makes warnings fail | Version-gated sniffs skip silently when the Moodle branch is unknown (below) |
| `phpdoc` | local_moodlecheck: five rules about docblock tags against the signature | Real; takes `--max-warnings` | Presence of docblocks is phpcs's job, not this one's |
| `phpmd` | Mess detector | Always 0 | Read the log |
| `phpcpd` | Copy-paste detector | Real | Deprecated since moodle-plugin-ci 4.4.0, to be removed in 5.0.0, no replacement planned |
| `validate` | Required files, `pluginname` string, `install.xml` table prefix, upgrade function name, `@<type>` and `@<component>` tags on every Behat feature | Real | Passes with no `LICENSE`, no README, no privacy provider |
| `savepoints` | `db/upgrade.php` savepoints | Real; skipped without `db/upgrade.php` | Any `WARN` line fails it |
| `mustache` | Template syntax, example context present, HTML validation, ESLint on inline JS | Real | Needs the plugin inside a Moodle tree; `templates/mobileapp/` skipped |
| `grunt` | `amd`, `yui`, `gherkinlint`, `stylelint`, then stale-build check | Real | Needs the plugin inside a Moodle tree with core's `node_modules` installed; `--max-lint-warnings`, not `--max-warnings` |
| `phpunit` | The plugin's tests | Real | No tests: passes |
| `behat` | The plugin's features | Real | No features: passes ("free pass") |

`moodle-plugin-ci install` writes `package.json` and `node_modules/` into the current directory; run it from a
work directory outside the plugin repository (`moodle-ci-matrix`).

## Reading output safely

```bash
moodle-plugin-ci phpcs --max-warnings 0 /path/to/plugin > phpcs.log 2>&1; code=$?
echo "phpcs exit: $code"; grep -c 'WARNING\|ERROR' phpcs.log; less phpcs.log
```

- A pipe returns the last command's exit code. `cmd | tee log` reports `tee`'s success; use `set -o pipefail`
  or `${PIPESTATUS[0]}`.
- phpcs prints each file's block of findings first and the summary last. `tail` keeps the summary and drops the
  finding.
- A background job's exit status is its last command's. `init.sh; phpunit` chained with `;` reports phpunit's
  status even when init failed and phpunit tested a stale site. Chain with `&&`.
- A grep that matches nothing exits 1, and a missing tool prints "command not found" to stderr; both read as
  "no findings" if only stdout is looked at.

## Proving a check can fail

Before trusting a clean result from a gate or a grep you wrote, run it once on input that must fail:

```bash
probe="$(mktemp -d)/myplugin" && cp -r /path/to/plugin "$probe"
printf '<?php\nfunction local_myplugin_probe($a) {\n    return $a;\n}\n' > "$probe/probe.php"
moodle-plugin-ci phpcs --max-warnings 0 "$probe"; echo "exit: $?"   # must be non-zero
```

Do this once per new gate or pattern, not on every run.

## phpcs and the Moodle branch

moodle-cs runs some version-gated sniffs, lang-file ordering among them (4.4 and later), only when it knows the
Moodle branch: from `--runtime-set moodleBranch 503`, or by finding a Moodle root (`public/version.php` or
`version.php`) above the file. A plugin checked in a standalone checkout skips them without saying so (moodle-cs 3.7,
`moodle/Util/MoodleUtil.php` `getMoodleBranch()`; `Sniffs/Files/LangFilesOrderingSniff.php`). Check a plugin
either inside a Moodle tree or with the runtime option:

```bash
phpcs --standard=moodle --runtime-set moodleBranch 503 /path/to/plugin
```

## Lang file checks

Sorted keys, as moodle-cs compares them (`strcmp`, within each comment-delimited section of the file):

```bash
php -r 'define("MOODLE_INTERNAL", 1); include "lang/en/local_myplugin.php";
  $k = array_keys($string); $s = $k; sort($s, SORT_STRING);
  if ($k === $s) { echo "sorted: ", count($k), " keys\n"; exit(0); }
  foreach ($k as $i => $key) { if ($key !== $s[$i]) { echo "out of order at: $key\n"; break; } } exit(1);'
```

The `define()` matters: without it the file's `defined('MOODLE_INTERNAL') || die();` ends PHP silently and the
command prints nothing. It must print a key count. If the file has sections (for example a deprecated block
under a comment), compare each section separately.

Syntax after any scripted edit:

```bash
php -l lang/en/local_myplugin.php
```

Lang files are data only: `$string['key'] = 'value';` lines. Concatenation, variables or function calls are
reported by phpcs ("Variable ... is not expected in a lang file") and are not supported by AMOS.

Every literal key used in code exists:

```bash
c=local_myplugin
grep -rhoE "get_string\('[a-z0-9_]+', *'$c'" --include=*.php . | sed -E "s/get_string\('([^']+)'.*/\1/" | sort -u > used.txt
grep -rhoE "\{\{#str\}\} *[a-z0-9_]+, *$c" templates | sed -E 's/.*\}\} *([^,]+),.*/\1/' | sort -u >> used.txt
php -r 'define("MOODLE_INTERNAL", 1); include "lang/en/'"$c"'.php"; echo implode("\n", array_keys($string)), "\n";' | sort -u > have.txt
sort -u used.txt | comm -23 - have.txt        # keys used but not defined: must print nothing
```

Also check the strings core asks for without a literal call: `pluginname`; `cachedef_<area>` for each
definition in `db/caches.php`; `messageprovider:<name>` for each provider in `db/messages.php`; one string per
capability in `db/access.php` (`myplugin:view` for `local/myplugin:view`); `privacy:metadata...` keys the
provider names; and, for a theme, `choosereadme`. Dynamic keys (`'status_' . $state`) are found only by rendering every state and looking
for `[[`.

## moodlecheck docblock rules

- A `@param` type containing a space (`array<string, mixed>`, `array{a: int}`) is read as type plus name, so it
  reports an incomplete parameter list. Keep `@param` types plain (`array`) and describe the shape in prose.
- `@return` is not name-matched, so a generic there is fine.
- Never write a literal `@param` inside docblock prose: it is parsed as a tag.
- The parameter list in the docblock must match the signature after every signature edit; this is the usual
  miss.
- Every function, test helpers included, needs a description sentence and complete `@param` and `@return` tags.
  A missing docblock is reported by phpcs; a docblock that disagrees with the signature by `phpdoc`.

The standalone `local_moodlecheck` CLI (`local/moodlecheck/cli/moodlecheck.php`) exits 0 even when it reports
errors, and its text output reads `Line 54: ...`. If you parse it, grep `Line [0-9]+:` and prove the pattern
matches known-bad output once. Prefer `moodle-plugin-ci phpdoc`, which has a real exit code.

## JavaScript and CSS

- Lint from inside a Moodle tree, at the plugin's real path: core's ESLint configuration scopes the AMD rules by
  path, so a copy elsewhere gets different rules.
- `grunt amd` builds `amd/build/` from `amd/src/`. Commit both. CI rebuilds into a copy and fails on any
  difference ("File is stale and needs to be rebuilt"), on a build file that should be deleted, and on a newly
  generated file that is not committed.
- stylelint runs over the plugin's `*.css` and `*.scss`. Moodle's configuration rejects single-line rule blocks
  (one declaration per line) and `!important` without a disable comment. The full rule set for themes is in
  `moodle-theme-scss`.

## Behat feature files (gherkinlint)

Core's `.gherkin-lintrc` (5.2 and 5.3.0) turns on: indentation (Feature 0, Background and Scenario 2, steps 4, Examples
4, example rows 6), no duplicate feature names, no empty file, no file without scenarios, no multiple empty
lines, no partially commented tag lines, no trailing spaces, no unnamed features or scenarios, no Scenario
Outline without Examples, and a newline at end of file. A blank line after the last step fails as "Multiple
empty lines are not allowed", because the linter counts the blank line and the final newline as two empty lines
(gherkin-lint 4.2.2, read in its source, not run). `validate` separately requires the `@<type>` and
`@<component>` tags (for example `@local @local_myplugin`) on every feature.
