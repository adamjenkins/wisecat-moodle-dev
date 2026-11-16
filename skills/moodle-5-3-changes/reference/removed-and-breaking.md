# Moodle 5.3: removals and breaking changes

Read this when a plugin or theme throws, fails to install or upgrade, loses a feature, or changes behaviour on 5.3,
and the summary table in `SKILL.md` is not enough to fix it.

Each entry: what changed, how it shows, the fix, the source. Sources are the `## 5.3` section of the root
`UPGRADING.md` of the 5.3.0 tree and the cited files in that tree (`public/...`), read, not run, unless an entry
says otherwise. Tracker links are `https://tracker.moodle.org/browse/MDL-NNNNN`.

## Install, upgrade and fatal errors

### `FEATURE_GROUPMEMBERSONLY` is refused

- `plugin_supports($type, $name, FEATURE_GROUPMEMBERSONLY)` throws `coding_exception` "The FEATURE_GROUPMEMBERSONLY
  flag has been deprecated and is no longer supported" (`public/lib/moodlelib.php`). Installing or upgrading a
  module whose `<mod>_supports('groupmembersonly')` returns true throws `plugin_defective_exception`. The constant
  itself is still defined, so the code compiles.
- Fix: delete the `case FEATURE_GROUPMEMBERSONLY:` line. MDL-83231.

### Legacy `external_*()` functions are stubs that throw

- `external_generate_token()`, `external_create_service_token()`, `external_delete_descriptions()`,
  `external_validate_format()`, `external_format_string()`, `external_format_text()`,
  `external_generate_token_for_current_user()`, `external_log_token_request()` are final-deprecated in
  `public/lib/externallib.php`: each calls `\core\deprecation::emit_deprecation()`, which throws. On 5.2 the same
  functions still work silently, so a 5.2-green plugin fails at the first web-service call on 5.3.
- Fix (valid on 5.2 too):

| Old function | Replacement |
|---|---|
| `external_generate_token()`, `external_create_service_token()` | `\core_external\util::generate_token()` |
| `external_delete_descriptions()` | `\core_external\util::delete_service_descriptions()` |
| `external_validate_format()` | `\core_external\util::validate_format()` |
| `external_format_string()` | `\core_external\util::format_string()` |
| `external_format_text()` | `\core_external\util::format_text()` |
| `external_generate_token_for_current_user()` | `\core_external\util::generate_token_for_current_user()` |
| `external_log_token_request()` | `\core_external\util::log_token_request()` |

- MDL-81225, MDL-76583. The global class names (`\external_api` and friends) are only deprecated: they still
  resolve, with a debugging notice, through the rename map (`public/lib/db/renamedclasses.php`). Switch to
  `use core_external\external_api;` and the other `\core_external\` names, which exist on 5.2 too.

### `login/token.php` refuses credentials in the query string

- `username` or `password` in `$_GET` throws `coding_exception` "Username and password can only be sent via POST
  parameters" (`public/login/token.php`). The requested service is validated before the user is authenticated, so
  `servicenotavailable` comes first. The `appsitecheck` parameter is gone.
- Fix: clients POST credentials; do not probe a site with `appsitecheck=1`. MDL-87010.

### `duration` form elements validate their units

- When `units` is given, the effective `defaultunit` (yours, or `MINSECS` by default) must be one of them, or the
  element throws `coding_exception` when the form is built (`public/lib/form/duration.php`).
- Fix:

```php
$mform->addElement('duration', 'timelimit', get_string('timelimit', 'local_example'),
    ['units' => [HOURSECS, DAYSECS], 'defaultunit' => HOURSECS]);
```

- MDL-89434. Valid on 5.2.

### Report builder: alias required, columns sortable by default

- `set_main_table(string $tablename, string $tablealias)` has no default alias any more (it was `''` on 5.2) and
  delegates to the new `set_main_table_sql()` (`public/reportbuilder/classes/local/report/base.php`). A call
  without an alias is an `ArgumentCountError`. MDL-88397.
- Columns are sortable unless told otherwise (`column::$issortable = true`,
  `public/reportbuilder/classes/local/report/column.php`). A column whose SQL cannot be sorted (a concatenation, an
  aggregate over text) now produces a sort link that errors or sorts nonsense. Add `->set_is_sortable(false)`; drop
  redundant `->set_is_sortable(true)`. MDL-87404.

```php
$this->set_main_table('local_example_items', 'lei');
```

### AI token counts moved

- `prompttokens` and the completion token column moved from `ai_action_generate_text`, `ai_action_summarise_text`
  and `ai_action_explain_text` to `ai_action_register` (`prompttokens`, `completiontokens`;
  `public/lib/db/install.xml`). On 5.2 the child-table column was spelled `completiontoken`. Direct SQL against the
  old columns fails with an unknown-column error. MDL-89123.

### Classes removed without a stub

- `block_timeline\output\main` and `block_timeline\output\renderer` are gone; the block is an ESM and React
  component mounted with `html_writer::react_component()` (MDL-88287). A theme renderer
  `theme_x_block_timeline_renderer extends \block_timeline\output\renderer` is a fatal "Class not found" as soon as
  it is autoloaded. Delete the override; the React component is customised by a theme React override, not by
  Mustache (`moodle-theme-renderers-output`).
- `theme_boost\output\core_renderer::render_login()` is gone; core's version renders `core/loginform` without
  adding `logourl`, `sitename` or `hasauthinstructions` (`public/lib/classes/output/core_renderer.php`). A child
  renderer that calls `parent::render_login()` now gets core's context.

### Classic theme removed

- `theme_classic` is no longer shipped. At upgrade, if Classic is installed but its files are absent, core
  uninstalls it (`public/lib/db/upgrade.php`, step `2026080700.01`). Settings are migrated to Boost only when Classic
  was the site default theme (`upgrade_migrate_classic_theme_to_boost()` returns early otherwise), and only the
  customised values of `unaddableblocks` (merged with Boost's `navigation`, `settings`, `course_list`),
  `brandcolor`, `scsspre`, `scss`, `backgroundimage` and `loginbackgroundimage`. Presets and `navbardark` are not
  migrated, side-post block positions are not kept, and uninstalling resets course, category, cohort and user
  theme choices. A forced `$CFG->theme = 'classic'` in `config.php` must be changed by hand.
- A theme with `'classic'` in `$THEME->parents` or `theme_classic` in `$plugin->dependencies` cannot work on a stock
  5.3 site. Re-parent it on Boost (what Classic provided that the theme must now own: `moodle-theme-boost-child`),
  or install Classic from its separate repository before upgrading, which skips the migration. MDL-88351.

### Core font files moved

- `public/lib/fonts/` no longer exists; core fonts are in `lib/bundles/fontawesome/webfonts/` under `$CFG->root`
  (`public/lib/classes/output/theme_config.php`, font lookup). `[[font:core|fa-solid-900.woff2]]` keeps working;
  code that builds `$CFG->dirroot . '/lib/fonts/...'` by hand breaks.

## Behaviour that changed silently

### `queue_adhoc_task($task, true)` returns the existing task's id

- 5.2 returned `false` when an identical task was already queued; 5.3 returns `int|false`: the new id, or with
  `$checkforexisting` the id of the matching existing task (matched by a new identity hash; exhausted tasks are
  revived), or `false` for a deprecated component or a database error (`public/lib/classes/task/manager.php`).
- Symptom: code that read a truthy result as "newly queued" double-counts or skips its "already queued" branch, and
  tests asserting `false` fail.
- Fix: do not use the return value to mean "new". To ask whether a task is queued:
  `false !== \core\task\manager::get_queued_adhoc_task_record($task, false)` (public static on 5.2 and 5.3).
  MDL-86422.
- The general lesson: a return value is part of the API contract across your supported range. Before branching on
  what a core function returns, grep the target branch's `UPGRADING.md` for the function name, not only for
  "deprecated".

### `marker_updated` is no longer triggered

- `mod_assign\event\marker_updated` fires only from deprecated code. Observers must listen to
  `mod_assign\event\marker_added` and `mod_assign\event\marker_removed`. MDL-87709.

### Custom quiz reports lose the group selector

- `report_base::print_header_and_tabs()` no longer prints the group selector. Minimal fix, restoring the report and
  group selectors:

```php
// In display() of a \mod_quiz\local\reports\report_base subclass.
$this->print_action_bar('myreport', null, $cm, $reporturl);
```

- If the report calls `print_standard_header_and_messages()` but does not implement `setup_report_data()`, pass
  `null` as its fourth argument (`$options`), or the AJAX user search fails.
- Full adoption: override `setup_report_data(stdClass $quiz, cm_info $cm, stdClass $course, ?context $context =
  null): array` returning `[$options, $table, $allowedjoins]` (the new `mod_quiz_get_users_in_report` web service
  calls it), and move a custom capability check from `display()` into `has_permission(context $context): void`,
  which the web service also calls. Core examples: `quiz_statistics_report` (minimal), `quiz_overview_report` and
  `quiz_responses_report` (full), `quiz_grading_report` (`has_permission()`). MDL-81096.

```php
public function has_permission(context $context): void {
    require_capability('quiz/myreport:view', $context);
}
```

### Courses with penalised grades are frozen on upgrade

- Courses containing a grade with a deducted penalty are frozen so a regrade does not change them; a user with
  `moodle/grade:manage` chooses to keep the grades or apply the fix (which restores affected raw grades from the
  assignment and regrades). Plugins that apply grade penalties re-test grading on an upgraded site. MDL-89497,
  MDL-88407. The review screens were not traced.

### Exporters return numeric entities

- Formatted single-valued `PARAM_TEXT` exporter properties go through `clean_string()`, so `&` comes back as
  `&#38;` instead of `&amp;` (also `&#60;`, `&#62;`, `&#34;`, `&#39;`); `multiple` properties are not affected.
  Update PHPUnit and Behat assertions and JS string comparisons. Listed under `block_myoverview`, change in
  `\core\external\exporter`. Also on the 5.2 branch from 5.2.2. MDL-79755.

### Block uninstall deletes instances later

- `\core\plugininfo\block::uninstall_cleanup()` deletes the `block` record at once and queues
  `\core\task\delete_block_instances_task`, which deletes instances, contexts, positions, preferences and search
  entries in batches. `before_delete()` still runs synchronously, and an overridden `instance_delete()` is still
  called per instance while the code is present. Do not assume contexts are gone when uninstall returns; uninstall
  tests may need `$this->runAdhocTasks()`. MDL-89289.

### Linear navigation is on by default for opted-in formats

- `\core_courseformat\base::uses_linear_navigation()` (static, false by default) lets a format show previous/next
  activity links in the sticky footer. Whether it shows is read from the site setting `format_<name>/enablelinearnav`
  (`public/course/format/classes/local/linearnavigationsettings.php`); a format that returns true but defines no such
  setting is treated as enabled (`SETTING_ENABLE_LINEAR_NAV_DEFAULT = 1`). `format_topics` and `format_weeks` define
  it. Add the setting if your format needs an off switch:

```php
// course/format/myformat/settings.php, same shape as format_topics.
$settings->add(new admin_setting_configselect(
    'format_myformat/enablelinearnav',
    new lang_string('linearnavigationsettings', 'core_courseformat'),
    new lang_string('linearnavigationsettings_help', 'core_courseformat'),
    1,
    [1 => get_string('yes'), 0 => get_string('no')],
));
```

- Activity modules that print their own previous/next controls check
  `\core_courseformat\local\linearnavigationsettings::is_linear_navigation_enabled($course)`, or call
  `$PAGE->set_show_navigation_footer(false)`. MDL-87302, MDL-89406 (not in the 5.3.0 notes; read in source).

### TeX and Algebra images moved to file storage

- `filter_tex` and `filter_algebra` store rendered images in file storage (system context, component
  `filter_tex`/`filter_algebra`, filearea `rendered_images`, itemid 0), not in `$CFG->dataroot/filter/tex|algebra/`;
  an upgrade step migrates and deletes the old directories. Scripts that read or clean those directories must
  switch. MDL-87554.

### Custom field handler instances

- `\core_customfield\handler::create()` returns a new instance again by default. A handler that removed its own
  `create()` while 5.3 was in development and relies on caching declares `protected const CACHE_HANDLER_INSTANCES =
  true;`. MDL-89238.

### Hub registration

- `\core\hub\api::call_rest()` now throws `moodle_exception` on a non-200 status, an empty body or invalid JSON
  instead of treating it as success; `registration::confirm_registration()` returns a bool and queues
  `\core\task\complete_hub_registration_task` on failure; updates are signed. Only code that calls the hub API
  directly is affected. MDL-89464, MDL-89474, MDL-89512.

## Markup and template changes that break overrides

These break theme or plugin template overrides and CSS, JS or Behat selectors. `SKILL.md` lists the file with the
markup for each; listed here so a search for "breaking" finds them:

- Primary and secondary navigation rendered by React components (`.mds-nav-pill`, no `.moremenu`), MDL-89294,
  MDL-87830.
- Edit mode switch rendered by the design-system switch (`mds-switch*`), MDL-89814.
- `core/modal` title is `<h2 class="modal-title fs-5">`, MDL-75699.
- `theme_boost/drawer` block `drawerheadercontent` replaced by `drawercontrols`, MDL-89050.
- Course index subsection ARIA moved to the activity `treeitem`, MDL-88949.
- Section collapse/expand-all toggle moved to `core_courseformat/local/content` and lost its `collapsesections` id,
  MDL-89496.
- `core/loginform` moved from Boost to core with new markup, MDL-89196.
- `mod_forum/forum_subscription_action` uses `core/tertiary_navigation_selector`, MDL-89890.
