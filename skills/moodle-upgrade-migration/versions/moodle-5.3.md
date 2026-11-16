# Moodle 5.3: what a port has to know

Read this when adding 5.3 to a plugin's supported range, or when one codebase must run on both 5.2 and 5.3.

Read in the 5.3.0 source (`public/version.php`: `2026100500.00`, `5.3 (Build: 20261005)`), its
`public/admin/environment.xml` and root `UPGRADING.md`; not run unless stated. The catalogue of every 5.3 change,
with fixes, is the `moodle-5-3-changes` skill; this file covers only the migration mechanics.

## Release facts

| Item | Value |
|---|---|
| Branch | `503`, `MOODLE_503_STABLE`; the LTS of the 5.x series |
| 5.3.0 `$version` | `2026100500`, so `$plugin->requires = 2026100500;` for a 5.3-only release |

PHP and database minimums, the upgrade path and the Composer step are in the release facts table of
`moodle-5-3-changes`. Because 5.3 is the LTS, what it deprecates is removed in 7.0, not 6.0. What 4.5 to 5.2
deprecated (including the Bootstrap 4 compatibility layer) is due to go in 6.0.

## One codebase for 5.2 and 5.3, or a branch each

```php
// One codebase:                          // A branch per Moodle version:
$plugin->requires  = 2026042000; // 5.2   $plugin->requires  = 2026100500; // 5.3
$plugin->supported = [502, 503];          $plugin->supported = [503, 503];
```

- One codebase works when the plugin calls stable APIs and copies no core templates. Guard each 5.3-only call with
  `method_exists()` / `class_exists()` and keep the 5.2 call in the other branch, for example:

  ```php
  if (method_exists(\core\user::class, 'create_user')) {
      $userid = \core\user::create_user((object) $record);      // 5.3+
  } else {
      require_once($CFG->dirroot . '/user/lib.php');
      $userid = user_create_user((object) $record);             // 5.2; deprecated on 5.3
  }
  ```

  Useful feature tests: `class_exists(\core\output\react_component_renderable::class)` (React rendering API),
  `class_exists(\theme_boost\colour_mode::class)` (colour modes), `method_exists(\core_courseformat\base::class,
  'get_page_section')` (page section API).
- A branch per version is simpler once the plugin overrides core templates or styles markup that 5.3 rewrote
  (navigation, the course index drawer, the timeline block). Large themes do this; the theme skills explain why.
- `$CFG->branch` is written only after the core upgrade finishes (`admin/cli/upgrade.php` and
  `public/admin/index.php`, 5.3.0), so code that runs during the core part of a 5.2 to 5.3 upgrade still sees
  `502`. Plugin `db/upgrade.php` steps run afterwards and see `503`, but a feature test is still the safer guard.

## What usually breaks first

From the 5.3.0 notes, in the order a port meets them (fixes in `moodle-5-3-changes`):

1. Install or upgrade throws: `FEATURE_GROUPMEMBERSONLY` still returned true by `<mod>_supports()`.
2. A form throws: a `duration` element whose `units` leave out the default unit.
3. Web services throw: legacy `external_*()` functions are now stubs.
4. Report builder: `set_main_table()` needs an alias; columns are sortable unless you say otherwise.
5. Debugging floods: 25 `user/lib.php` functions, global `\external_*` class names, `get_return_section()`, the
   `sr` URL parameter on `course/modedit.php`, `course/mod.php` and `course/editsection.php`.
6. UI and Behat selectors: primary and secondary navigation rendered by React components, modal titles now `<h2>`.

## Data migration across the 5.2 to 5.3 core upgrade

Plugin upgrade steps run after the core upgrade, but during the same upgrade run, so core tables already have their
5.3 shape. Code in a plugin step that reads core tables moved in 5.3 (for example AI token counts, now in
`ai_action_register`) must use the 5.3 columns. The rules for writing steps are in `SKILL.md`.
