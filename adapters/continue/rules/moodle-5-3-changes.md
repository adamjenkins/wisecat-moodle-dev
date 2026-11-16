---
name: moodle-5-3-changes
description: Use when porting a plugin or theme to Moodle 5.3 (branch 503, MOODLE_503_STABLE, $version 2026100500), adding 5.3 to $plugin->supported or CI, or fixing what 5.3 broke or deprecated — user/lib.php functions moved to \core\user, external_* functions that now throw, FEATURE_GROUPMEMBERSONLY, set_main_table() alias, duration units, queue_adhoc_task returning an id, the sr parameter, Classic theme removal, React primary/secondary navigation, dark colour mode, theme_boost/bootstrap imports, block_timeline renderer removal, quiz report action bar, assign overrides and marker events, enablemyhome on fresh sites, delete_course async. Skip when the plugin supports only 5.2 or the port starts from a version before 5.2, or when the question is the porting method (version guards, db/upgrade.php steps, PHP versions) rather than the 5.3 list (moodle-upgrade-migration), or the task is a theme recipe rather than what changed (moodle-theme-development).
---

# Moodle 5.3 Changes

## Overview

What Moodle 5.3 removed, moved, deprecated, changed and added, and how to find each in a plugin. Based on the
`## 5.3` section of the root `UPGRADING.md` of the 5.3.0 release (`$version = 2026100500.00`, `5.3 (Build:
20261005)`) and checked against the 5.3.0 and 5.2 source by reading; where the notes and the code disagree, this
skill follows the code and says so. Nothing here was run unless an entry says "run on 5.3.0".

## When to Use

- Adding `MOODLE_503_STABLE` to CI or `503` to `$plugin->supported`
- A 5.3 site shows debugging notices, `coding_exception`s, fatal errors or install failures from plugin code
- CSS, templates, JavaScript or Behat selectors stopped matching on 5.3
- Choosing whether a 5.3-only API is usable given the plugin's supported range
- **Skip when:** the plugin supports only 5.2 or earlier, or you need the general porting method rather than the
  5.3 list (`moodle-upgrade-migration`); building or fixing a theme beyond what changed (`moodle-theme-development`).

## Release facts

| Item | 5.3 | Source |
|---|---|---|
| Branch | `503`, `MOODLE_503_STABLE`; the LTS of the 5.x series | `public/version.php` |
| `$version` of 5.3.0 | `2026100500.00`: `$plugin->requires = 2026100500;` | `public/version.php` |
| PHP | 8.3.0 minimum; 8.4 supported | `public/admin/environment.xml`; https://moodledev.io/general/releases/5.3 |
| Databases | PostgreSQL 17, MariaDB 11.4, MySQL 8.4, SQL Server 2019 (15.0) (5.2: PostgreSQL 16, MariaDB 10.11) | `environment.xml` |
| Upgrade from | 4.4 or later | `environment.xml` |
| Composer | run `composer install` at the Moodle root; 5.3 adds `league/oauth2-server` for the OAuth2 server | MDL-88457, MDL-88576 |
| Removal schedule | deprecated in 5.3 means removed in 7.0 (LTS rule); deprecated in 4.5-5.2 means removed in 6.0 | https://moodledev.io/general/development/policies/deprecation |

## How to find what 5.3 changes in a plugin

Run these from the plugin root. Each hit is a row in the tables below.

```bash
# Removed or now fatal
grep -rn "FEATURE_GROUPMEMBERSONLY" .
grep -rnE "\bexternal_(generate_token|create_service_token|delete_descriptions|validate_format|format_string|format_text|generate_token_for_current_user|log_token_request)\(" .
grep -rn "block_timeline\\\\output\|block_timeline_renderer\|render_login" classes/ renderers.php 2>/dev/null
grep -rnE "'duration'.*units|set_main_table\(\s*'[a-z_]+'\s*\)" .
grep -rnE "prompttokens|completiontoken\b" .
grep -rnE "'classic'|theme_classic" config.php version.php
# Deprecated (notices on 5.3)
grep -rnE "\b(user_[a-z_]+|can_view_user_details_cap)\(" --include=*.php . | grep -v "function user_"
grep -rnE "extends\s+\\\\?external_api\b|new\s+\\\\?external_(value|single_structure|multiple_structure|function_parameters|warnings|files|format_value)\(" .
grep -rnE "get_return_section\(|'sr'\s*=>|[?&]sr=|add_navitem\(|get_main_table\(\)|NO_MOODLE_COOKIES" .
grep -rn "theme_boost/bootstrap/" amd/src
# Behaviour that changed silently
grep -rn "queue_adhoc_task(.*true)" .
grep -rn "marker_updated" db/events.php classes/
grep -rnE "delete_course\(" --include=*.php .
# Markup and selectors
grep -rnE "\.moremenu|primary-navigation .*\.nav-link|h5\.modal-title|drawerheadercontent|collapsesections|form-switch" --include=*.{css,scss,mustache,js,feature} .
```

Then run the plugin's PHPUnit and Behat suites on 5.3 with `DEBUG_DEVELOPER`, and read the notes for every core
function the plugin calls: a return value or default can change with no deprecation (the `queue_adhoc_task()` row
below). The method is `moodle-upgrade-migration`.

## Removed, or now fatal

| Change | Symptom | Fix | MDL |
|---|---|---|---|
| `FEATURE_GROUPMEMBERSONLY` supported by a module | `plugin_supports()` throws; install/upgrade throws `plugin_defective_exception` | Delete the `case FEATURE_GROUPMEMBERSONLY:` | MDL-83231 |
| `external_format_text()`, `external_format_string()`, `external_validate_format()`, `external_generate_token()` and four more | Throw `coding_exception` (5.2: worked silently) | `\core_external\util::format_text()` etc. (exist on 5.2) | MDL-81225, MDL-76583 |
| `login/token.php` credentials in the query string; `appsitecheck` | Throws; parameter gone | POST credentials | MDL-87010 |
| `duration` element whose `units` exclude the effective `defaultunit` | `coding_exception` building the form | `'defaultunit' => HOURSECS` from your `units` | MDL-89434 |
| `set_main_table('table')` without alias | `ArgumentCountError` | `set_main_table('table', 't')` | MDL-88397 |
| AI token columns on `ai_action_*` child tables | Unknown column in direct SQL | Read `ai_action_register.prompttokens`, `completiontokens` | MDL-89123 |
| `block_timeline\output\main`, `\renderer` | Fatal in a theme renderer that extends it | Delete the override | MDL-88287 |
| `theme_boost\output\core_renderer::render_login()` | `parent::render_login()` gets core's context | Re-diff against core's `core/loginform` | MDL-89196 |
| Classic theme | Themes with `classic` as a parent cannot work; settings migrate to Boost only when Classic was the site default | Re-parent on Boost (`moodle-theme-boost-child`) or install Classic before upgrading | MDL-88351 |
| `public/lib/fonts/` | Hand-built paths to core fonts 404 | `[[font:core\|fa-solid-900.woff2]]` in CSS | `theme_config.php` |

Details, including the quiz report and Classic migration rules: [reference/removed-and-breaking.md](../moodle-skill-files/moodle-5-3-changes/reference/removed-and-breaking.md).

## Moved and renamed

| Old | New | Old name still works? |
|---|---|---|
| 25 `user/lib.php` functions (`user_create_user()`, `user_get_user_details()`, `user_can_view_profile()` ...) | `\core\user::create_user()` etc. (drop the `user_` prefix); `user_update_device_public_key()` to `\core_user\devicekey` | Yes, with a notice |
| `\external_api`, `\external_value`, `\external_single_structure` and nine more global names | `\core_external\...` | Yes, notice on first use |
| About 110 `admin_setting_*` and admin tree classes | `\core_admin\setting\...` | Yes, no notice; new names 5.3 only |
| `theme_boost/bootstrap/*`, `theme_boost/index` AMD modules | `bootstrap` ESM package | Yes until 7.0 (RequireJS-to-ESM map) |
| `core/loginform` in Boost | core `public/lib/templates/loginform.mustache` | Child overrides still win |
| Section collapse toggle in `content\section` | `core_courseformat\output\local\content` and `local/content` | Still exported |
| Default font system-ui | self-hosted Noto Sans | n/a |

## Deprecated (works, emits a notice)

| Deprecated | Replacement | MDL |
|---|---|---|
| The 25 `user/lib.php` functions | `\core\user::*` (typed: cast arrays with `(object)`) | MDL-82650 |
| `get_return_section()` | `get_page_section()` | MDL-86284 |
| `sr` URL parameter on `course/modedit.php`, `course/mod.php`, `course/editsection.php` | `returnoptions[pagesectionid]` (5.2 knows only `sr`) | MDL-86284 |
| `get_view_url()` option `'sr'` | `'pagesectionid' => $section->id` (no notice here) | MDL-86284 |
| `extend_user_menu::add_navitem()`, `get_navitems()` | `add_menu_item()` with `\core_user\output\user_action_menu\link` etc. | MDL-88938 |
| `get_main_table()` | `get_main_table_sql()` | MDL-88397 |
| `NO_MOODLE_COOKIES` checks | `\core\session\manager::supports_cookies()` | MDL-87174 |
| `assign::delete_override()`, `delete_all_overrides()`, `get_allocated_markers()`, `update_allocated_markers()` | `\mod_assign\override_manager`, `get_marker_allocations()`, `update_marker_allocations()` | MDL-86513, MDL-87709 |
| `core_admin_renderer::admin_notifications_page()` and the banner methods; `core/external_content_banner` | `notifications_page()`; `core_admin/notification_ctas` | MDL-89290 |
| `theme_boost/bootstrap/*` imports | `theme_boost/index` (5.2 and 5.3) or `bootstrap` (5.3+) | MDL-88766 |
| `grade_item::update_deducted_mark()`, `get_dataroot_size()`, `enrol_cohort()`, `task_is_scheduled()` | `penalty_manager`, `get_filepool_usage()`, none, `get_queued_adhoc_task_record()` | MDL-88407, MDL-88805, MDL-89439, MDL-86422 |

Full list, with the admin setting rename map: [reference/deprecations.md](../moodle-skill-files/moodle-5-3-changes/reference/deprecations.md).

## Changed behaviour (no notice)

| Change | Symptom | Fix | MDL |
|---|---|---|---|
| `queue_adhoc_task($task, true)` returns the existing task's id, not `false` | "Already queued" branch never taken; tests asserting `false` fail | Do not read the result as "new"; compare ids | MDL-86422 |
| Report builder columns sortable by default | Sort links on columns that cannot sort | `->set_is_sortable(false)` | MDL-87404 |
| `mod_assign\event\marker_updated` not triggered | Observer never runs | Observe `marker_added`, `marker_removed` | MDL-87709 |
| Custom quiz reports: no group selector from `print_header_and_tabs()` | Group selector missing | `$this->print_action_bar('myreport', null, $cm, $reporturl);` | MDL-81096 |
| Exporter text uses numeric entities (`&#38;`) | String assertions fail | Update expectations | MDL-79755 |
| Block uninstall deletes instances in an ad-hoc task | Contexts still present after uninstall | Keep cleanup in `instance_delete()`; run ad-hoc tasks in tests | MDL-89289 |
| Linear navigation footer on by default for formats that opt in | Unexpected previous/next footer | `format_<name>/enablelinearnav` setting, or `$PAGE->set_show_navigation_footer(false)` | MDL-89406 |
| Courses with penalised grades frozen on upgrade | Grades held until a manager decides | Warn admins; re-test penalty code | MDL-89497 |
| `delete_course()` gains `$asyncpreferred = true`; asynchronous when `moodlecourse/enablecourseasyncdeletion` is on | Shortname still taken right after delete | `delete_course($course, false, false)` (safe on 5.2) | `public/lib/moodlelib.php` |

## Site and UI changes a port meets

- **Dark colour mode** (experimental `theme_boost/enablecolourmodes`) applies to every Boost-based theme when on;
  literal colours in plugin CSS lose contrast. Use `var(--bs-body-bg)`, `var(--bs-body-color)`,
  `var(--bs-border-color)`, `var(--bs-tertiary-bg)` and `bg-body*` / `text-body*` utilities; `--mds-*` tokens
  exist only on 5.3. Font Awesome icons follow the text colour; a plugin's `pix/icon.svg` rendered as `<img>` does
  not. MDL-68037.
- **Navigation is React**: primary (`core/primarymoremenu`) and secondary (`core/secondarymoremenu`) navigation
  render `a.mds-nav-pill` without `.moremenu`; the edit switch uses `mds-switch*`. Retarget CSS, JS and Behat.
  MDL-89294, MDL-87830, MDL-89814.
- **Modal titles are `<h2 class="modal-title fs-5">`**; headings in modal bodies start at `<h3>`. MDL-75699.
- **Course index and drawer templates**: `drawercontrols` replaces `drawerheadercontent`; subsection ARIA moved to
  the activity `treeitem`; the collapse-all toggle lost its `collapsesections` id (`[data-toggle="toggleall"]`).
  MDL-89050, MDL-88949, MDL-89496.
- **Fresh installs have `enablemyhome = 0`** (also on a fresh 5.2 install): `/` and Behat "I am on site homepage"
  land on the user's start page. Set `enablemyhome = 1` and `defaulthomepage = 0` where a test needs the site home.
- **A wide table on a `report` layout page inside an activity** sat under the course index on 5.3; use `incourse`
  (`moodle-theme-layouts-templates`).
- **Stylelint** rejects `container-type`, `@container` and `clamp()` in `font-size` through `csstree/validator`.
  Not new in 5.3 (`.stylelintrc` is identical in the 5.2 and 5.3.0 trees), but a port often meets it while
  restyling for dark mode; rule and workaround in `moodle-theme-scss`.

Markup, selectors and editor detail: [reference/ui-and-templates.md](../moodle-skill-files/moodle-5-3-changes/reference/ui-and-templates.md). Theme work for
5.3 starts at `moodle-theme-development`.

## Added (5.3 only unless noted)

| Area | Addition | MDL |
|---|---|---|
| React | `html_writer::react_component()`, `react_component_renderable`, AMD `core/import`, `core/component`, `scripts/swizzle.mjs` | MDL-89296, MDL-88505, MDL-88509 |
| Page | `set_show_navigation_footer()`, `set_has_sticky_footer()`, `set_supplementary_content()` | MDL-87575, MDL-87302, MDL-88601 |
| Hooks | `\core\hook\email\before_email_to_user`; `before_import_map_config`, `before_requirejs_config` | MDL-69724 |
| DI and auth | `#[\DI\Attribute\Inject]`; `\core\authentication`, `\core\authentication\password`, `\core_auth\validate_user`, `\core\composer` | MDL-89528, MDL-88580, MDL-88576 |
| REST API | Personal access tokens (`\core\api\token_manager`, `moodle/api:createtoken`), OAuth2 server clients, route scopes | MDL-87706, MDL-89181, MDL-89089 |
| Web services | `'allowcorsrequests' => true` for no-login functions; assign override, forum read state, quiz report user functions | MDL-87150, MDL-86513, MDL-87887, MDL-81096 |
| Exceptions | `new moodle_exception(..., previous: $e)` | MDL-88579 |
| Tasks | `set_soft_retry_delay()` (also 5.2.2+); `set_scheduled_task_nextruntime()` returns bool | MDL-79763, MDL-89200 |
| Course formats | `uses_linear_navigation()`, `inline_help`, disabled chooser items | MDL-87302, MDL-88669, MDL-87373 |
| Report builder | `week`/`month`/`year` aggregations, `set_main_table_sql()`, `prepend_joins()`, `add_fields(array)` | MDL-84635, MDL-88397, MDL-87405, MDL-89004 |
| Testing | Behat `--colourmode`, `I set the focus on`; PHPUnit `util.php --snapshot`, `--restore`, `--upgrade` | MDL-68037, MDL-84065, MDL-88495 |

The 5.3 OAuth2 server is an authorization server for Moodle's REST API, not an OpenID Connect provider (no
`id_token`, userinfo, discovery or JWKS in `public/lib/classes/oauth2/server/`, read in 5.3.0): it does not replace an
OIDC provider plugin for single sign-on. Signatures and samples:
[reference/new-apis.md](../moodle-skill-files/moodle-5-3-changes/reference/new-apis.md).

## Supporting 5.2 and 5.3 from one codebase

- Keep the 5.2 call and add the 5.3 one behind a feature test; never the reverse:

```php
if (method_exists(\core\user::class, 'create_user')) {
    $userid = \core\user::create_user((object) $record);      // 5.3+
} else {
    require_once($CFG->dirroot . '/user/lib.php');
    $userid = user_create_user((object) $record);             // 5.2
}
```

- Feature tests: `class_exists(\theme_boost\colour_mode::class)`, `class_exists(\core\output\react_component_renderable::class)`,
  `method_exists(\core_courseformat\base::class, 'get_page_section')`, `method_exists($hook, 'add_menu_item')`.
- `db/hooks.php` may name a 5.3-only hook; it is never dispatched on 5.2 (`moodle-hooks-api`).
- What breaks on removals (external functions, `FEATURE_GROUPMEMBERSONLY`, `set_main_table()` alias, `duration`
  units) has a fix that is valid on 5.2 too: apply it unconditionally.
- Plugins that override core templates or style navigation usually need a branch per version; theme skills explain.

## Upgrade checklist

1. Run the greps above; fix every removal first, unconditionally.
2. Replace `external_*()` functions and global `\external_*` class names; drop `require_once($CFG->libdir .
   '/externallib.php')`.
3. Migrate or guard the `user/lib.php` calls, `get_return_section()`, `sr`, `add_navitem()`.
4. Report builder: alias in `set_main_table()`; audit sortability; replace `get_main_table()`.
5. Quiz report subplugins: `print_action_bar()`; implement `has_permission()`.
6. Event observers on `marker_updated`; callers of `queue_adhoc_task($task, true)` that test the result.
7. AMD: replace `theme_boost/bootstrap/` imports; rebuild with `grunt amd`.
8. Styles: replace literal colours, `bg-white`, `text-dark`; run Behat once with `--colourmode=dark`.
9. Templates and selectors: `.moremenu`, `.nav-link`, `h5.modal-title`, `drawerheadercontent`, `collapsesections`,
   courseindex and `local/content` overrides, `core/loginform`.
10. qbank plugins with bulk actions: override `get_action_icon()` (the base returns `i/empty`).
11. Course formats with linear navigation: add `format_<name>/enablelinearnav` if an off switch is needed.
12. CI: add `MOODLE_503_STABLE` with PHP 8.3+, PostgreSQL 17 or MariaDB 11.4 ([reference/testing-and-ci.md](../moodle-skill-files/moodle-5-3-changes/reference/testing-and-ci.md)).
13. Run PHPUnit and Behat on 5.3 with `DEBUG_DEVELOPER`; treat every "Unexpected debugging() call" as a failure.
14. Set `$plugin->supported` to include `503` only after the suites pass on 5.3.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `\core\user::create_user($array)` | `TypeError`: the method takes `stdClass` | `(object) $array` |
| Raising `$plugin->requires` to 5.3 just to use `\core\user::` or `bootstrap` imports while claiming 5.2 | 5.2 sites cannot install | Feature-test, or `theme_boost/index` |
| Treating `set_columnheadersattributes()`, `add_header_attributes()`, soft retry delay as 5.3-only | Unneeded guards | They are also on the 5.2 branch (5.2.2 and later builds); guard only for older 5.2 releases |
| `\core\router\attributes\route` (from the notes) | Class not found | `\core\router\route` (`cookies:` option) |
| `\core\authentication::get_plugin()` statically | Error: non-static method | `\core\di::get(\core\authentication::class)->get_plugin($auth)` |
| `json_encode()`-ing props for `html_writer::react_component()` | Props double-encoded | Pass the array or object |
| `ai_action_register.courseid` treated as always a course | Wrong reports | `0` = not backfilled, `-1` = not in a course |
| Assuming a route without `#[scopeset]` is rejected | Open route | Declare scopes; test with `assert_route_is_scoped()` |
| `'allowcorsrequests' => true` on a login-required function | No effect, false sense of access | Only for `loginrequired => false` functions safe cross-origin |
| `override_manager::delete_override()` | Undefined method | `delete_overrides_by_id([$id])` |
| Expecting `user_convert_text_to_menu_items()` to return typed items | Code written for objects that are not there | It still returns `stdClass` with `itemtype` (read in 5.3.0) |
| Counting on `delete_course()` being synchronous in a setup script | Shortname collision on sites with async deletion | `delete_course($course, false, false)` |
| Using the 5.3 OAuth2 server as an SSO identity provider | No `id_token`; relying party fails | An OIDC provider plugin |
| Fixing only PHPUnit failures | Behat fails on deprecation debugging | Fix every notice |

## Reference files

| File | Read it when |
|---|---|
| [reference/removed-and-breaking.md](../moodle-skill-files/moodle-5-3-changes/reference/removed-and-breaking.md) | something throws, fails to install, disappears or behaves differently on 5.3 and the tables above are not enough to fix it (quiz reports, Classic migration, linear navigation, block uninstall, hub registration) |
| [reference/deprecations.md](../moodle-skill-files/moodle-5-3-changes/reference/deprecations.md) | a 5.3 deprecation notice names your code, you need the full `user/lib.php` or `external_*` mapping, or you meet a `\core_admin\setting\...` class |
| [reference/ui-and-templates.md](../moodle-skill-files/moodle-5-3-changes/reference/ui-and-templates.md) | CSS, a template override, JS or Behat selectors stopped matching, or the plugin must look right in dark mode |
| [reference/new-apis.md](../moodle-skill-files/moodle-5-3-changes/reference/new-apis.md) | you want to use a 5.3 API (React rendering, DI attributes, auth services, tokens, OAuth2 server, route scopes, email hook, soft retries, report builder or format additions) and need its signature |
| [reference/testing-and-ci.md](../moodle-skill-files/moodle-5-3-changes/reference/testing-and-ci.md) | adding `MOODLE_503_STABLE` to CI, or PHPUnit, Behat or a setup script fails only on 5.3 |

## References

- Root `UPGRADING.md` of the 5.3.0 tree, section `## 5.3`; `public/theme/boost/UPGRADING.md`
- https://moodledev.io/general/releases/5.3
- https://moodledev.io/docs/5.3/devupdate
- https://moodledev.io/general/development/policies/deprecation
- https://tracker.moodle.org/browse/MDL-82650 (user/lib.php to `\core\user`)
- https://tracker.moodle.org/browse/MDL-81225 (legacy external classes)
- https://tracker.moodle.org/browse/MDL-68037 (colour modes)
- https://tracker.moodle.org/browse/MDL-88351 (Classic removal)
- https://tracker.moodle.org/browse/MDL-88766 (Bootstrap imports)
