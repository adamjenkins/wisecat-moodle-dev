---
name: moodle-upgrade-migration
description: Use when porting a Moodle plugin written for 3.x, 4.x, 5.0 or 5.1 up to 5.2, moving it to a newer PHP version, or needing the porting method for any version: raising $plugin->requires and $plugin->supported, one codebase or a branch per Moodle version, guarding an API that differs between supported branches, fixing deprecation debugging ("has been deprecated", "Call to undefined function print_error", "Undefined constant"), writing db/upgrade.php steps that must survive a failed upgrade, or porting old code (print_error, add_to_log, external_api without namespace, lib.php callbacks, Bootstrap 4 classes, /public directory). Skip when the question is what Moodle 5.3 removed, moved, deprecated or added (moodle-5-3-changes) or writing a plugin from scratch (moodle-plugin-development).
---

# Moodle Upgrade and Migration

## Overview

A plugin declares a range of Moodle versions it supports, and every core API it calls must exist and behave the
same across that range. Porting is three jobs: find what changed between the lowest and highest supported branch,
make the code work on all of them (feature tests, not version numbers), and move stored data forward with
`db/upgrade.php` steps that can be re-run. Per-release catalogues live elsewhere (`moodle-5-3-changes`); this skill
is the method and the cross-version rules.

## When to Use

- Raising `$plugin->requires`, adding a branch to `$plugin->supported`, or adding a branch to CI (when the branch
  is 5.3, the list of what to fix is `moodle-5-3-changes`)
- A deprecation `debugging()` notice, an "undefined function/constant/class" fatal, or a changed return value
  after a core upgrade
- Writing or reviewing `db/upgrade.php`
- Porting code written for Moodle 3.x or 4.x
- Moving to a newer PHP version
- **Skip when:** you want everything that changed in 5.3 (`moodle-5-3-changes`), are creating a plugin
  (`moodle-plugin-development`), or are preparing the release itself (`moodle-plugin-release`).

## The model: a plugin supports a range

```php
// version.php
$plugin->component = 'local_example';
$plugin->version   = 2026111600;
$plugin->requires  = 2026042000;      // 5.2.0: the lowest core version number you accept.
$plugin->supported = [502, 503];      // [lowest, highest] branch, both ends inclusive.
```

- `requires` is a core `$version` number; `supported` is a pair of branch numbers. `[502]` is malformed and core
  throws `coding_exception` (`public/lib/classes/plugininfo/base.php`, read in 5.2 and 5.3.0). Details:
  `moodle-field-lessons`.
- The local development site proves one row of the range. An API added, moved, deprecated or changed inside the
  range is a bug on the other rows until guarded, and only CI on every branch shows it.
- Core release values: 5.2.0 is `2026042000`, 5.3.0 is `2026100500` (`public/version.php` of each tree).
- Deprecation timeline (https://moodledev.io/general/development/policies/deprecation): an API deprecated in a
  non-LTS release X.Y is removed in (X+1).0; one deprecated in the LTS (the last release of a series, 5.3 for the
  5.x series) is removed in (X+2).0. So anything deprecated in 4.5 to 5.2 is due to go in 6.0, and anything
  deprecated in 5.3 in 7.0. Stages: initial deprecation (works, emits `debugging()`), final deprecation (the
  function is a stub that throws `coding_exception`), removal (undefined).

## Default recipe for a port

1. **List what changed**, for every branch inside the new range: read the root `UPGRADING.md` (sections `## 5.3`,
   `## 5.2`, ...; per-component `UPGRADING.md` files carry the same notes) of the highest branch, and for branches
   before 4.5 the `upgrade.txt` files. Grep it for every core symbol the plugin calls:

   ```bash
   # Function names the plugin calls, then the upgrade-note lines that mention any of them.
   grep -rhoE '\b[a-z][a-z0-9_]{3,}\(' --include=*.php . | tr -d '(' | sort -u > /tmp/calls.txt
   grep -nwFf /tmp/calls.txt /path/to/moodle/UPGRADING.md
   # Everything core marks deprecated, with the version and replacement:
   grep -rn -A1 '#\[\\core\\attribute\\deprecated' /path/to/moodle/public --include=*.php | grep -v /tests/
   ```

   Return values and argument defaults change too, not only names: on 5.3 `\core\task\manager::queue_adhoc_task($task,
   true)` returns the id of the existing task where 5.2 returned `false` (`public/lib/classes/task/manager.php`,
   both trees). A caller that treated a truthy result as "newly queued" breaks on 5.3 with no notice.
2. **Raise the floor** in `version.php` if you can; every branch you drop removes guards. Raise any dependency in
   `$plugin->dependencies` in the same commit that starts calling a symbol the dependency added.
3. **Replace or guard each changed API** (next section).
4. **Move data** with `db/upgrade.php` steps (rules below) and bump `$plugin->version`.
5. **Run the suite on every supported branch** with `DEBUG_DEVELOPER`. In PHPUnit an "Unexpected debugging() call
   detected" line in a passing run is a finding: it is a deprecation you have not fixed. Behat fails the step on it.
   CI matrix: `moodle-ci-matrix`.
6. **Write the change down** in the plugin's `CHANGES.md` and, if other code calls your APIs, in an upgrade notes
   file (`UPGRADING.md` or `upgrade.txt`; for plugins the format is free,
   https://moodledev.io/general/development/upgradenotes). Name the replacement, not only what went:

   ```markdown
   ## 2.0.0
   ### Deprecated
   - `local_example_get_items()` is deprecated; use `\local_example\api::get_items()`. Removal in 3.0.0.
   ### Changed
   - Requires Moodle 5.2; supports 5.2 and 5.3.
   ```

## Guarding an API that differs inside the range

Test for the feature, not the version. `$CFG->branch` is a stored config value that core writes only after the
core upgrade (`public/admin/index.php`, `admin/cli/upgrade.php`, 5.3.0), so it is stale while core upgrades, and
it says nothing about point-release backports.

```php
// A function or method added in the newer branch.
if (method_exists(\core_courseformat\base::class, 'get_page_section')) {
    $section = $format->get_page_section();          // 5.3+
} else {
    $section = $format->get_return_section();        // 5.2; deprecated on 5.3
}

// A method added to a class that may already exist on the older branch: test the method, not the class.
if (method_exists(\core_courseformat\local\cmactions::class, 'delete')) {
    \core_courseformat\formatactions::cm($course->id)->delete($cmid);
} else {
    course_delete_module($cmid);
}

// A constant removed in the newer branch (ASSIGN_ATTEMPT_REOPEN_METHOD_NONE is gone in 5.2): reference it
// only behind defined(); a bare use throws "Error: Undefined constant" when the line runs.
$noreopen = defined('ASSIGN_ATTEMPT_REOPEN_METHOD_NONE')
    && $assign->get_instance()->attemptreopenmethod === constant('ASSIGN_ATTEMPT_REOPEN_METHOD_NONE');
```

- Guard the call that differs, not the whole feature, and keep the newer path first so the guard is easy to delete
  when the floor rises.
- A new optional parameter on a user-land function can be passed on the older branch without a guard: PHP ignores
  surplus arguments to a function that does not declare them. `delete_course($course, false, false)` is valid on
  5.2 and forces synchronous deletion on 5.3.
- Hooks: one `db/hooks.php` can name a hook that exists only on the newer branch; the entry is simply never
  dispatched on the older one (`moodle-hooks-api`).
- When the code grows a guard per screen, branch the plugin per Moodle version instead (one `MOODLE_5xx_STABLE`
  branch each, `supported = [503, 503]`). Themes that copy Boost templates reach that point quickly
  (`moodle-theme-development`).

## db/upgrade.php rules

The skeleton and the XMLDB editor workflow are in `moodle-plugin-development`. The rules that matter when a site
upgrades across several versions:

- **Keep every historical step.** A site can jump from any old version to the newest; each `if ($oldversion <
  N)` block runs once, in order, and ends with `upgrade_plugin_savepoint(true, N, 'local', 'example')`
  (`upgrade_mod_savepoint()` for activities, `upgrade_block_savepoint()` for blocks).
- **Make each step safe to run twice.** DDL is not transactional on MySQL and MariaDB: when a step dies halfway,
  the changes before the failure stay, the savepoint is not reached, and the next upgrade attempt runs the step
  again from the top. A second `add_field()` then throws "Field already exists" and the site is stuck. Guard every
  DDL call (`field_exists()`, `index_exists()`, `table_exists()`, `key` changes inside the same guards) and write
  data changes so that repeating them changes nothing.
- **Do not call high-level APIs from an upgrade step**: grade, modinfo, course, completion, events, caches. They
  depend on the current schema of other components, which may not be upgraded yet, and they are slow per row.
  Queue an ad-hoc task and let cron do it on the finished site:

  ```php
  if ($oldversion < 2026111601) {
      // Recalculate cached grades for existing instances after the schema change above.
      $task = new \local_example\task\recalculate_after_upgrade();
      \core\task\manager::queue_adhoc_task($task, true);
      upgrade_plugin_savepoint(true, 2026111601, 'local', 'example');
  }
  ```

- **Iterate with recordsets and set fields directly** for data migration: `get_recordset_select()` plus
  `$DB->set_field()` or `update_record()` on the fields you change, closing the recordset.
- **Test the step on a site that has rows.** A fresh install never runs `upgrade.php`, and an empty table passes
  any data migration. Install the previous release, create data, then upgrade.
- An `install.xml` change without an upgrade step does nothing on existing sites; XMLDB keys are indexes and must
  be dropped around a NOT NULL change: both in `moodle-field-lessons`.
- Changing a default, a capability, or a setting definition also needs a version bump for existing sites (and for
  the PHPUnit `init.php`, which is a no-op until some version changes).

## Old code you will still find

| Old code | Status on 5.2 and 5.3 | Replacement |
|---|---|---|
| `print_error('key', 'component')` | Removed (undefined function) | `throw new \moodle_exception('key', 'component')` |
| `add_to_log(...)` | Removed | Trigger an event class (`\local_example\event\thing_viewed::create(...)->trigger()`) |
| `notify('text')` | Removed | `\core\notification::error('text')` or `echo $OUTPUT->notification('text', 'error')` |
| `external_api` and the other global `external_*` classes | 5.2: alias; 5.3: deprecated, notice on first use | `use core_external\external_api;` (since 4.2) |
| `external_format_text()` and the other `external_*()` functions | 5.2: work, no notice; 5.3: throw `coding_exception` | `\core_external\util::format_text()` etc. (exists on both) |
| `require_once($CFG->libdir . '/externallib.php')` | Not needed | autoloaded `\core_external\...` |
| `<component>_before_footer()` and other output callbacks | Deprecated: debugging notice | Hooks (`moodle-hooks-api`) |
| `core/modal_factory`, `core/modal_registry` (AMD) | Removed in 5.2 | `core/modal` subclasses with `ModalX.create()` |
| `.sr-only`, `.ml-*`, `.float-left`, `data-toggle` | Bootstrap 4 compat layer, removal in 6.0 | `.visually-hidden`, `.ms-*`, `.float-start`, `data-bs-toggle` |
| `course_delete_module()`, `duplicate_module()`, `moveto_module()` | Deprecated in 5.2 | `\core_courseformat\formatactions::cm($courseid)->delete()`, `duplicate()`, `move_before()`, `move_end_section()` |
| Theme or plugin files built from `$CFG->dirroot . '/lib/fonts/'` | Gone on 5.3 | `[[font:core\|fa-solid-900.woff2]]` in CSS |

The longer list (formslib, navigation, course formats, older PHP-era functions) is in
[reference/legacy-api-replacements.md](reference/legacy-api-replacements.md).

## Traps

- **Behat fails on a deprecation that PHPUnit tolerates.** A deprecated call such as `moveto_module()` on 5.2 makes
  every Behat step that reaches it fail with the debugging message, while PHPUnit reports only "Unexpected
  debugging() call" and passes. Fix the call, do not silence the output.
- **A docblock is not the code.** `qbank_helper::get_question_structure()` documents random slots with `qtype` set
  to `'random'`, but on 5.2 sets it to `null` and adds `->random = true`
  (`public/mod/quiz/classes/question/bank/qbank_helper.php`, 5.2). Compare slots by `->random`. Read the return
  statement of any core function whose result you branch on.
- **Classes moved into namespaces lose their old name eventually.** `\mod_assign\output\assign_header` moved in 4.0;
  write the namespaced name with `use`. Grep for bare names of renamed classes in each component's
  `db/renamedclasses.php` (`public/lib/db/renamedclasses.php` for core).
- **The 5.1 `/public` directory changed paths, not APIs.** From 5.1 the web root is `<moodle>/public`, and plugins
  live under it (`public/local/example`); `$CFG->dirroot` points at `public`, and `$CFG->root` at the directory
  above it, where Composer's `vendor/` and, on 5.3, `lib/bundles/` live. Code that builds paths from
  `$CFG->dirroot` keeps working; code that hard-coded `__DIR__ . '/../../lib/...'` across the boundary does not.
  CLI admin scripts are at the root: `php admin/cli/purge_caches.php`.
- **Raising the PHP floor is Moodle's call, not yours.** Use only PHP features of the lowest PHP that the lowest
  supported Moodle branch allows (8.3 for 5.2 and 5.3, `public/admin/environment.xml`). PHP changes:
  [reference/php-versions.md](reference/php-versions.md).
- **Do not bump `$plugin->release` to signal compatibility.** Compatibility is `requires` and `supported`;
  `release` is your own version string (`moodle-plugin-release`).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `$plugin->supported = [502]` | Core throws on plugin load | `[502, 503]` |
| Testing only on the dev site's branch | Fatal on another CI row | CI on every branch in `supported` |
| `if ($CFG->branch >= 503)` as the guard | Stale during the core upgrade; blind to backports | `method_exists()` / `class_exists()` |
| Treating `queue_adhoc_task($t, true)` truthy as "queued now" | Wrong on 5.3 (returns existing id) | Compare ids, or check `get_queued_adhoc_task_record()` |
| `add_field()` with no `field_exists()` guard | Second upgrade attempt dies, site stuck | Guard every DDL call |
| `rebuild_course_cache()` or grade API in `upgrade.php` | Errors or wrong data mid-upgrade | Queue an ad-hoc task |
| Deleting old upgrade steps | Sites skipping versions miss schema | Keep every step |
| Upgrade step tested only on a fresh install | Data migration never ran | Upgrade a site with rows |
| Referencing a removed constant bare | "Undefined constant" fatal | `defined()` guard or own value |
| Ignoring "Unexpected debugging() call" in a green run | Behat fails later; removal in the next major | Fix the deprecation now |

## Reference files

| File | Read it when |
|---|---|
| [reference/legacy-api-replacements.md](reference/legacy-api-replacements.md) | porting code written for Moodle 3.x or 4.x, or a deprecated function, class or template is not in the table above |
| [reference/php-versions.md](reference/php-versions.md) | moving code to a newer PHP version, or PHP itself (not Moodle) emits the deprecation |
| [reference/release-history.md](reference/release-history.md) | the plugin's current minimum is below 5.2 and you need what changed in 4.x, 5.0 and 5.1 |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](versions/moodle-5.2.md): requirements, and the 5.2 removals and deprecations a port from 5.1 hits |
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md): requirements, values for `requires`, and spanning 5.2 and 5.3 in one codebase |

## References

- https://moodledev.io/general/development/policies/deprecation
- https://moodledev.io/general/development/upgradenotes
- https://moodledev.io/docs/guides/upgrade
- https://moodledev.io/general/releases
- Root `UPGRADING.md` of the target Moodle tree
