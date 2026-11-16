# Moodle 5.3: deprecations and renames

Read this when a 5.3 site prints a deprecation `debugging()` notice from your code, when you need the replacement
for an API deprecated in 5.3, or when you meet an unfamiliar `\core_admin\setting\...` class name.

Everything deprecated in 5.3 still works on 5.3 and is due for removal in 7.0 (5.3 is the LTS; deprecation policy,
https://moodledev.io/general/development/policies/deprecation), unless an entry names another version. Most
replacements do not exist on 5.2: while 5.2 is in your supported range, keep the old call behind a
`method_exists()` / `class_exists()` test for the new one. Sources: the `## 5.3` section of the 5.3.0 root
`UPGRADING.md` and the cited files, read, not run.

## `user/lib.php` functions moved to `\core\user` (MDL-82650)

The 25 functions are now wrappers in `public/lib/deprecatedlib.php` that emit a developer debugging notice and
delegate. `user/lib.php` keeps only the `USER_FILTER_*` constants, `user_page_type_list()` and
`core_user_inplace_editable()`.

| Old | New |
|---|---|
| `user_create_user()` | `\core\user::create_user()` |
| `user_update_user()` | `\core\user::update_user()` |
| `user_delete_user()` | `\core\user::delete_user()` |
| `user_get_users_by_id()` | `\core\user::get_users_by_id()` |
| `user_get_default_fields()` | `\core\user::get_default_fields()` |
| `user_get_user_details()` | `\core\user::get_user_details()` |
| `user_get_user_details_courses()` | `\core\user::get_user_details_courses()` |
| `can_view_user_details_cap()` | `\core\user::can_view_user_details_cap()` |
| `user_count_login_failures()` | `\core\user::count_login_failures()` |
| `user_convert_text_to_menu_items()` | `\core\user::convert_text_to_menu_items()` |
| `user_get_default_homepage_options()` | `\core\user::get_default_homepage_options()` |
| `user_get_user_navigation_info()` | `\core\user::get_user_navigation_info()` |
| `user_add_password_history()` | `\core\user::add_password_history()` |
| `user_is_previously_used_password()` | `\core\user::is_previously_used_password()` |
| `user_remove_user_device()` | `\core\user::remove_user_device()` |
| `user_list_view()` | `\core\user::list_view()` |
| `user_mygrades_url()` | `\core\user::mygrades_url()` |
| `user_can_view_profile()` | `\core\user::can_view_profile()` |
| `user_process_profile_callbacks()` | `\core\user::process_profile_callbacks()` |
| `user_get_tagged_users()` | `\core\user::get_tagged_users()` |
| `user_get_course_lastaccess_sql()` | `\core\user::get_course_lastaccess_sql()` |
| `user_get_user_lastaccess_sql()` | `\core\user::get_user_lastaccess_sql()` |
| `user_get_lastaccess_sql()` | `\core\user::get_lastaccess_sql()` |
| `user_edit_map_field_purpose()` | `\core\user::edit_map_field_purpose()` |
| `user_update_device_public_key()` | `\core_user\devicekey::update_device_public_key()` (a `\core\user` delegate also exists) |

The new methods are typed, for example `create_user(stdClass $user, bool $updatepassword = true, bool
$triggerevent = true): int` (`public/lib/classes/user.php`), so cast arrays: `(object) $record`.
`convert_text_to_menu_items(string $text): array` still returns `stdClass` items with `itemtype`, `title`, `url`
(read in 5.3.0; the notes describe typed items, the code does not return them). Renderer code copied from 5.2 core
that calls `user_can_view_profile()` or `user_get_user_navigation_info()` emits these notices on 5.3.

```php
if (method_exists(\core\user::class, 'create_user')) {
    $userid = \core\user::create_user((object) $record);   // 5.3+
} else {
    require_once($CFG->dirroot . '/user/lib.php');
    $userid = user_create_user((object) $record);          // 5.2
}
```

## Web service classes

The global names are no longer `class_alias`es in `public/lib/externallib.php`; they resolve through
`public/lib/db/renamedclasses.php`, which emits "Class ... has been renamed for the autoloader and is now
deprecated" on first use (MDL-81225). The namespaced classes exist on 5.2, so switch unconditionally.

| Old | New |
|---|---|
| `\external_api` | `\core_external\external_api` |
| `\restricted_context_exception` | `\core_external\restricted_context_exception` |
| `\external_description` | `\core_external\external_description` |
| `\external_value` | `\core_external\external_value` |
| `\external_format_value` | `\core_external\external_format_value` |
| `\external_single_structure` | `\core_external\external_single_structure` |
| `\external_multiple_structure` | `\core_external\external_multiple_structure` |
| `\external_function_parameters` | `\core_external\external_function_parameters` |
| `\external_util` | `\core_external\util` |
| `\external_files` | `\core_external\external_files` |
| `\external_warnings` | `\core_external\external_warnings` |
| `\external_settings` | `\core_external\external_settings` |

The `external_*()` functions are not deprecated but final: they throw (the Removed table in `SKILL.md`).

## Course formats and course pages

| Deprecated | Replacement | Notes |
|---|---|---|
| `\core_courseformat\base::get_return_section()` | `get_page_section(): ?section_info` (null on the course main page) | 5.3+ only; MDL-86284 |
| `get_view_url()` option `'sr'` (section number) | `'pagesectionid' => $section->id` | No notice from `get_view_url()`; `'sr'` still works when `pagesectionid` is absent; removal 7.0 (MDL-88498) |
| URL parameter `sr` on `course/modedit.php`, `course/mod.php`, `course/editsection.php` | `returnoptions[pagesectionid]=<sectionid>` | These three scripts do emit "The sr parameter has been deprecated" debugging (read in 5.3.0); 5.2's `modedit.php` knows only `sr`, so a link for both branches picks the parameter with `method_exists(\core_courseformat\base::class, 'get_page_section')` |
| Section collapse/expand-all toggle in `core_courseformat\output\local\content\section` and `local/content/section/content` | The toggle in `core_courseformat\output\local\content` and `core_courseformat/local/content` | Still exported for old overrides; MDL-89496 |
| `course_get_cm_move()` with a number or null second argument | An array of return options | Debugging notice (`public/course/lib.php`) |

```php
// A link to edit a module that returns to the right section on 5.2 and 5.3.
$params = ['update' => $cm->id];
if (method_exists(\core_courseformat\base::class, 'get_page_section')) {
    $params['returnoptions'] = ['pagesectionid' => $cm->section];      // 5.3+
} else {
    $params['sr'] = $cm->sectionnum;                                   // 5.2
}
$url = new \moodle_url('/course/modedit.php', $params);
```

## Users, menus, sessions

| Deprecated | Replacement | MDL |
|---|---|---|
| `\core_user\hook\extend_user_menu::add_navitem()`, `get_navitems()` | `add_menu_item()` with `\core_user\output\user_action_menu\{link,divider,header,text}`, `get_menu_items()` | MDL-88938 (dual-version callback: `moodle-hooks-api`) |
| Checking `defined('NO_MOODLE_COOKIES')` | `\core\session\manager::supports_cookies()` | MDL-87174 |
| `enrol_manual_plugin::enrol_cohort()` | none; enrol the members yourself or use `enrol_cohort` | MDL-89439 |

## Report builder, grades, tasks

| Deprecated | Replacement | MDL |
|---|---|---|
| `get_main_table()` on a report | `get_main_table_sql()` with `get_main_table_alias()` (the value includes `{braces}` or complex SQL; the old method strips outer braces) | MDL-88397 |
| `grade_item::update_deducted_mark()` | none; `\core_grades\penalty_manager` applies penalties through `grade_item::adjust_raw_grade()` | MDL-88407 |
| Templates `core_grades/general_action_bar`, `gradereport_grader/action_bar` | `core/navigation_action_bar`, `core/action_bar` (removal planned for 6.0) | MDL-81096 |
| `\core\task\manager::task_is_scheduled()` (protected) | `get_queued_adhoc_task_record($task, false)` | MDL-86422 |
| `\core\hub\registration::get_dataroot_size()` | `get_filepool_usage()` (estimates from the files table, deduplicated by content hash, cached; also on the 5.2 branch) | MDL-88805 |

## Activities

| Deprecated | Replacement | MDL |
|---|---|---|
| `assign::delete_override()`, `assign::delete_all_overrides()`, global `move_group_override()`, `reorder_group_overrides()` | `\mod_assign\override_manager`: `delete_overrides_by_id(array $ids, ...)` (there is no `delete_override()` on it), `delete_all_overrides()`, `move_group_override()`, `reorder_group_overrides()`; removal planned for 6.0 (MDL-87324) | MDL-86513 |
| `assign::get_allocated_markers()`, `update_allocated_markers()` | `get_marker_allocations(int $studentid, bool $includeplaceholders = true)`, `update_marker_allocations(int $studentid, array $modifiedallocations)`: the second argument has a different shape | MDL-87709 |
| `ASSIGN_MULTIMARKING_MAX_MARKERS` | `ASSIGN_MULTIMARKING_DEFAULT_MAX_MARKERS` (removal planned for 7.0) | MDL-87709, MDL-89401 |
| `mod_quiz` `override_manager::get_effective_open_close_times()` | `get_effective_times()`; the old name was restored as a deprecated wrapper returning only `timeopen`/`timeclose` | MDL-89711 |
| `mod_forum/forum_subscription_action` context `viewandmanageselect` | `viewandmanageselectmenu` (`core\output\select_menu` data) | MDL-89890 |
| Behat `I set portfolio instance "X" to "Y"` | `I set the portfolio instance "X" to "Y"` (in `behat_portfolio`; removal planned for 7.0) | MDL-89069 |

## Admin pages and renderer

| Deprecated | Replacement | MDL |
|---|---|---|
| `core_admin_renderer::admin_notifications_page()` | `notifications_page()`, same arguments minus `$showcampaigncontent`, `$showfeedbackencouragement`, `$showservicesandsupport` | MDL-89290 |
| Protected `campaign_content()`, `services_and_support_content()`, `userfeedback_encouragement()`, `marketplace_integration_notice()` | Customise `core_admin/notification_ctas` | MDL-89290 |
| Template `core/external_content_banner` | `core_admin/notification_ctas` (final deprecation planned for 6.0) | MDL-89290 |
| `$CFG->showcampaigncontent` | No effect; hide cards with `$CFG->disablenotificationctas = ['marketplace', 'moodlecloud', 'partners', 'feedback'];` | MDL-89290 |
| `core_admin_renderer::upgradekey_form_page()` | `upgradekey_form_page_with_validation(moodle_url $url, bool $upgradekeyerror)`, which exists on 5.2; the attribute says `since: '5.2'` though 5.2 does not emit it | MDL-87896 |

`$CFG->showservicesandsupportcontent` now controls only the "Services and support" link in the help popover.

## JavaScript: Bootstrap imports

`theme_boost/amd/src/bootstrap/` and `theme_boost/amd/src/index.js` are gone. The old module ids still resolve
through a RequireJS-to-ESM map that Boost registers with the new `before_requirejs_config` hook
(`public/theme/boost/classes/hook_listener.php`), marked for removal in 7.0. MDL-88766.

```js
// Works on 5.2 and 5.3 (until 7.0):
import {Tooltip} from 'theme_boost/index';
// 5.3 and later only:
import {Tooltip} from 'bootstrap';
// Private DOM helpers, 5.3 and later only (not public Bootstrap API):
import EventHandler from 'bootstrap/dom/event-handler';
```

Replace `theme_boost/bootstrap/<module>` imports and rebuild the AMD files with `grunt amd`.

## Renamed without notices: admin setting classes (MDL-81935)

About 110 classes from `adminlib.php` are autoloaded under new names in 5.3 (`public/admin/classes/setting/`). The
old global names keep working without any notice (each new file ends with `class_alias()`). Keep the old names
while you support 5.2, where the new names do not exist.

| Old name pattern | New name |
|---|---|
| `\admin_setting` | `\core_admin\setting` |
| `\admin_setting_<x>`, `\admin_settings_<x>` | `\core_admin\setting\setting\<x>` |
| `\admin_category`, `\admin_externalpage`, `\admin_root` | `\core_admin\setting\tree\category`, `externalpage`, `root` |
| `\admin_page_<x>` (`manageblocks`, `managefilters`, `managemessageoutputs`, `managemods`, `manageportfolios`, `manageqbehaviours`, `manageqtypes`, `managerepositories`, `pluginsoverview`) | `\core_admin\setting\page\<x>` |
| `\admin_settingpage` | `\core_admin\setting\settingpage\settingpage` |
| `\admin_settingdependency` | `\core_admin\setting\settingpage\dependency` |

`<x>` covers: `agedigitalconsentmap`, `bloglevel`, `check`, `configbackupfilenamemustachetemplate`,
`configcheckbox`, `configcheckbox_with_advanced`, `configcheckbox_with_lock`, `configcolourpicker`,
`configdirectory`, `configduration`, `configduration_with_advanced`, `configempty`, `configexecutable`,
`configfile`, `confightmleditor`, `configiplist`, `configmixedhostiplist`, `configmulticheckbox`,
`configmulticheckbox2`, `configmultiselect`, `configmultiselect_modules`, `configpasswordunmask`,
`configpasswordunmask_with_advanced`, `configportlist`, `configselect`, `configselect_autocomplete`,
`configselect_with_advanced`, `configselect_with_lock`, `configstoredfile`, `configtext`,
`configtext_with_advanced`, `configtext_with_maxlength`, `configtextarea`, `configthemepreset`, `configtime`,
`countrycodes`, `courselist_frontpage`, `description`, `emoticons`, `enablemobileservice`, `encryptedpassword`,
`filetypes`, `flag`, `forcetimezone`, `grade_profilereport`, `gradecat_combo`, `heading`, `langlist`,
`manage_fileconverter_plugins`, `manage_plugins`, `manageantiviruses`, `manageauths`,
`managecontentbankcontenttypes`, `managecustomfields`, `managedataformats`, `manageenrols`,
`manageexternalservices`, `manageformats`, `managemediaplayers`, `managerepository`, `managewebserviceprotocols`,
`my_grades_report`, `php_extension_enabled`, `pickfilters`, `pickroles`, `question_behaviour`,
`regradingcheckbox`, `requiredpasswordunmask`, `requiredtext`, `savebutton`, `scsscode`, `searchsetupinfo`,
`servertimezone`, `sitesetcheckbox`, `sitesetselect`, `sitesettext`, `special_adminseesall`,
`special_backup_auto_destination`, `special_backupdays`, `special_calendar_weekend`, `special_coursecontact`,
`special_debug`, `special_frontpagedesc`, `special_gradebookroles`, `special_gradeexport`,
`special_gradeexportdefault`, `special_gradelimiting`, `special_grademinmaxtouse`, `special_gradepointdefault`,
`special_gradepointmax`, `special_registerauth`, `special_selectsetup`, `users_with_capability`,
`webservicesoverview`; and from `admin_settings_`: `country_select`, `coursecat_select`, `h5plib_handler_select`,
`num_course_sections` (itself deprecated since 5.1 in favour of `admin_setting_configtext`),
`sitepolicy_handler_select`.

```php
// 5.3+ only. Use admin_setting_configtext while 5.2 is supported.
$settings->add(new \core_admin\setting\setting\configtext(
    'local_example/apikey',
    get_string('apikey', 'local_example'),
    '',
    '',
    PARAM_TEXT,
));
```
