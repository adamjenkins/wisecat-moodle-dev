# Moodle 5.3: what is specific for plugin authors

Read this when the plugin's `supported` range includes 503, when moving a 5.2 plugin to 5.3, or when a 5.3 CI row
fails where 5.2 passes.

Facts below were read in the 5.3.0 source (`UPGRADING.md` at the root and the files named), not run, unless a line
says otherwise. 5.3.0 is `$version = 2026100500.00`, branch `503` (`public/version.php`). The full upgrade
catalogue is `moodle-5-3-changes`; this file keeps what changes how a plugin is written.

## Writing one code line for 5.2 and 5.3

The rule is the same for every row below: use the name both branches have, or guard the new one.

```php
if (method_exists(\core\user::class, 'create_user')) {
    $userid = \core\user::create_user($user);
} else {
    require_once($CFG->dirroot . '/user/lib.php');
    $userid = user_create_user($user);
}
```

| 5.3 change | On 5.2 | What a 5.2 + 5.3 plugin does |
|---|---|---|
| `user/lib.php` functions deprecated for `\core\user::*` (`user_create_user()` to `\core\user::create_user()`, `user_update_user()`, `user_delete_user()`, `user_get_user_details()` and about 25 more), MDL-82650; the old functions now live in `public/lib/deprecatedlib.php` and emit a deprecation | Only the old functions exist | Guard as above; `--fail-on-warning` CI rejects the notice on the 5.3 row |
| Legacy global external classes (`\external_api`, `\external_value`, `\external_single_structure`, ...) deprecated | `\core_external\...` already exists (since 4.2) | Always `use core_external\...` |
| Admin setting classes get namespaced names (`\admin_setting_configtext` is now an alias of `\core_admin\setting\setting\configtext`, `\admin_settingpage` of `\core_admin\setting\settingpage\settingpage`); "existing classes are currently unaffected" | Only the global names exist | Keep the global names |
| `FEATURE_GROUPMEMBERSONLY` deprecated and no longer supported (MDL-83231) | Accepted | Remove the case from `<modname>_supports()` |
| `delete_course($course, $showfeedback, $asyncpreferred = true)` (`public/lib/moodlelib.php:4467`): when the site setting `moodlecourse/enablecourseasyncdeletion` is on (default off, `public/admin/settings/courses.php:90`), the call returns at once and cron deletes later, so the shortname stays taken | Two arguments, synchronous | A delete-then-recreate script passes `delete_course($course, false, false)`; PHP ignores the extra argument on 5.2, so no branch check is needed |
| `\core\task\manager::queue_adhoc_task($task, true)` returns the id of the new or the existing task (false only when the component is deprecated or on a DML error) | Returns false when an identical task already exists | Do not branch on the return value |
| `\core\session\manager::supports_cookies()` replaces reading `NO_MOODLE_COOKIES` (MDL-87174) | Read the constant | `method_exists()` guard, else `defined('NO_MOODLE_COOKIES') && NO_MOODLE_COOKIES` |
| `email_to_user()` dispatches the `before_email_to_user` hook (subscribers can change content, add headers, or block the mail) | No hook | Register the hook; nothing runs on 5.2 |
| `moodle_exception` accepts a `$previous` Throwable (MDL-88579) | No such argument | Do not pass it unless 503 is the lowest branch |

## Course formats

- `core_courseformat\base::get_return_section()` is deprecated for `get_page_section()` (MDL-86284).
- `\core_courseformat\base::uses_linear_navigation()` is new and returns false (MDL-87302). A format that returns
  true gets the activity prev/next footer switched on by default: `linearnavigationsettings` falls back to
  enabled when the format has no `format_<name>/enablelinearnav` setting
  (`public/course/format/classes/local/linearnavigationsettings.php`). Add that setting if the footer should be
  optional. `$PAGE->set_show_navigation_footer(false)` suppresses it on one page (MDL-87575).

## Forms, report builder, activity APIs

- The `duration` form element throws when `defaultunit` (default `MINSECS`) is not in the element's `units`
  (MDL-89434). Pass a `defaultunit` that is in `units` whenever you restrict `units`.
- Report builder: the `$tablealias` argument of `set_main_table()` is mandatory (MDL-88397); columns are sortable
  by default, so call `->set_is_sortable(false)` on columns that must not sort (MDL-87404).
- `mod_assign\event\marker_updated` is no longer triggered: observe `marker_added` and `marker_removed`
  (MDL-87709).
- Quiz report sub-plugins call `$this->print_action_bar(...)` to render the new navigation bar (MDL-81096).

## Styles

Boost has an experimental dark colour mode (`theme_boost | enablecolourmodes`, MDL-68037), so a plugin's
`styles.css` cannot assume a light page. Take colours from Bootstrap custom properties (`--bs-body-bg`,
`--bs-body-color`, `--bs-secondary-bg`, `--bs-border-color`, `--bs-link-color`) or utility classes (`bg-body`,
`text-body`), scope any mode-specific colour with `[data-bs-theme="dark"]`, and note that an SVG rendered through
`<img>` (any plugin's `pix/icon.svg`) keeps the colours baked into the file. Theme-side detail:
`moodle-theme-scss`.
