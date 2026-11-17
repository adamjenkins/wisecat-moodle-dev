# Moodle Development Prompts (agent-agnostic)

Drop these into any LLM coding assistant. Links to `moodle-skill-files/` are files beside this one:
open one only when the skill says its condition applies.

## Skills (load on relevant tasks)

### moodle-5-3-changes

> Use when porting a plugin or theme to Moodle 5.3 (branch 503, MOODLE_503_STABLE, $version 2026100500), adding 5.3 to $plugin->supported or CI, or fixing what 5.3 broke or deprecated — user/lib.php functions moved to \core\user, external_* functions that now throw, FEATURE_GROUPMEMBERSONLY, set_main_table() alias, duration units, queue_adhoc_task returning an id, the sr parameter, Classic theme removal, React primary/secondary navigation, dark colour mode, theme_boost/bootstrap imports, block_timeline renderer removal, quiz report action bar, assign overrides and marker events, enablemyhome on fresh sites, delete_course async. Skip when the plugin supports only 5.2 or the port starts from a version before 5.2, or when the question is the porting method (version guards, db/upgrade.php steps, PHP versions) rather than the 5.3 list (moodle-upgrade-migration), or the task is a theme recipe rather than what changed (moodle-theme-development).

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

Details, including the quiz report and Classic migration rules: [reference/removed-and-breaking.md](moodle-skill-files/moodle-5-3-changes/reference/removed-and-breaking.md).

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

Full list, with the admin setting rename map: [reference/deprecations.md](moodle-skill-files/moodle-5-3-changes/reference/deprecations.md).

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

Markup, selectors and editor detail: [reference/ui-and-templates.md](moodle-skill-files/moodle-5-3-changes/reference/ui-and-templates.md). Theme work for
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
[reference/new-apis.md](moodle-skill-files/moodle-5-3-changes/reference/new-apis.md).

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
12. CI: add `MOODLE_503_STABLE` with PHP 8.3+, PostgreSQL 17 or MariaDB 11.4 ([reference/testing-and-ci.md](moodle-skill-files/moodle-5-3-changes/reference/testing-and-ci.md)).
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
| [reference/removed-and-breaking.md](moodle-skill-files/moodle-5-3-changes/reference/removed-and-breaking.md) | something throws, fails to install, disappears or behaves differently on 5.3 and the tables above are not enough to fix it (quiz reports, Classic migration, linear navigation, block uninstall, hub registration) |
| [reference/deprecations.md](moodle-skill-files/moodle-5-3-changes/reference/deprecations.md) | a 5.3 deprecation notice names your code, you need the full `user/lib.php` or `external_*` mapping, or you meet a `\core_admin\setting\...` class |
| [reference/ui-and-templates.md](moodle-skill-files/moodle-5-3-changes/reference/ui-and-templates.md) | CSS, a template override, JS or Behat selectors stopped matching, or the plugin must look right in dark mode |
| [reference/new-apis.md](moodle-skill-files/moodle-5-3-changes/reference/new-apis.md) | you want to use a 5.3 API (React rendering, DI attributes, auth services, tokens, OAuth2 server, route scopes, email hook, soft retries, report builder or format additions) and need its signature |
| [reference/testing-and-ci.md](moodle-skill-files/moodle-5-3-changes/reference/testing-and-ci.md) | adding `MOODLE_503_STABLE` to CI, or PHPUnit, Behat or a setup script fails only on 5.3 |

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


---

### moodle-accessibility

> Use when building or reviewing Moodle plugin UI for WCAG 2.2 AA - semantic Mustache markup, headings and landmarks, formslib labels, {{#pix}} icon alt text and aria-hidden, accessible names for buttons, row checkboxes and icon links, ARIA only where HTML has no equivalent, live regions and core/toast, focus in core/modal and core/local/aria/focuslock, keyboard support, colour contrast in light and dark colour modes (data-bs-theme, --mds-* tokens), page titles, and the Behat axe steps ("the page should meet accessibility standards", @accessibility, --colourmode=dark, "No data"). Skip when styling a whole theme (moodle-theme-scss) or writing JavaScript mechanics (moodle-amd-javascript).

# Moodle Accessibility (WCAG 2.2 AA)

## Overview

Moodle's accessibility policy targets WCAG 2.2 AA, and core's Behat accessibility step checks WCAG 2.0, 2.1 and 2.2
A and AA by default (`public/lib/tests/behat/behat_accessibility.php`, 5.2 and 5.3). Boost, Bootstrap 5, formslib
and the core output components do most of the work when they are used as intended. This skill gives the markup
recipe, the places where plugins usually break it, and how to prove the result.

Evidence tags: **read** means read in the named version's source or moodledev.io, not run; **run 5.3.0** means
observed on 5.3.0.

## When to Use

- Writing a Mustache template, a renderer, a form, a modal, or any markup built in JavaScript
- Choosing colours in a plugin's `styles.css`, or checking a page in Boost's dark colour mode
- Reviewing a pull request or a Plugins directory submission for accessibility
- Adding `@accessibility` Behat scenarios, or making them pass
- **Skip when:** setting a whole theme's palette, tokens or dark-mode SCSS (`moodle-theme-scss`), testing a theme
  (`moodle-theme-testing-release`), wiring modals, TinyMCE or autocomplete in JavaScript (`moodle-amd-javascript`),
  or writing Behat steps in general (`moodle-behat-testing`).

## The model

1. **Native HTML first, ARIA second.** A `<button>`, `<a href>`, `<label for>`, `<table>` with `<th scope>` and a
   heading hierarchy give screen readers everything. ARIA is for widgets HTML does not have (tabs, tree, combobox),
   and wrong ARIA is worse than none (moodledev.io accessibility policy).
2. **Every interactive element has an accessible name** that a screen reader announces and a voice-control user can
   say: visible text, a `<label for>`, or `aria-label` when there is no room for text. Behat locates fields by id,
   name, `<label>` or placeholder, not by `aria-label`, so a visible or visually hidden `<label>` serves both.
3. **Keyboard is the baseline**: reachable with Tab in reading order, operable with Enter and Space, visible focus,
   and no trap except a modal that Escape closes.
4. **Colour carries no meaning alone**, and text meets 4.5:1 (3:1 for large text), components and focus indicators
   3:1, against whatever surface they end up on in either colour mode. **5.3+:** Boost has a dark colour mode, so a
   literal colour that passes on white can fail on `#1d2125`.
5. **Prove it twice**: axe through Behat catches roughly a third to a half of issues (moodledev.io accessibility
   testing page); keyboard and screen-reader passes catch the rest.

## Default recipe: markup

```mustache
{{!
    @template local_example/attendance

    Example context (json):
    {
        "headingid": "att-h", "sessionname": "Week 1",
        "rows": [{"userid": 3, "fullname": "Ana Lee", "present": true, "checkboxid": "att-3"}]
    }
}}
<section aria-labelledby="{{headingid}}">
    <h3 id="{{headingid}}">{{#str}}attendancefor, local_example, {{sessionname}}{{/str}}</h3>
    <table class="table">
        <caption class="visually-hidden">{{#str}}attendancetable, local_example{{/str}}</caption>
        <thead>
            <tr>
                <th scope="col">{{#str}}fullnameuser, core{{/str}}</th>
                <th scope="col">{{#str}}present, local_example{{/str}}</th>
            </tr>
        </thead>
        <tbody>
            {{#rows}}
            <tr>
                <th scope="row">{{fullname}}</th>
                <td>
                    <input type="checkbox" id="{{checkboxid}}" name="present[{{userid}}]" value="1"
                        {{#present}}checked{{/present}}>
                    <label for="{{checkboxid}}" class="visually-hidden">
                        {{#str}}markpresent, local_example, {{fullname}}{{/str}}
                    </label>
                </td>
            </tr>
            {{/rows}}
        </tbody>
    </table>
    <button type="submit" class="btn btn-primary">{{#str}}savechanges, core{{/str}}</button>
</section>
```

Why each piece is there: the section is named by its heading; the heading level follows the page (an activity
page's content usually starts at `<h3>` under the page's `<h2>`); every row checkbox has its own label naming the
person, so "Mark Ana Lee present" is announced instead of twelve unnamed checkboxes, and Behat's
`I set the field "Mark Ana Lee present" to "1"` finds it; `{{#str}}` keeps every word translatable.

- `visually-hidden` and `visually-hidden-focusable` are the Bootstrap 5 classes. `sr-only` is Bootstrap 4: Boost keeps
  it only in `scss/moodle/bs4-compat.scss` with the `deprecated-styles()` mixin, which outlines it in red on Behat
  sites and in theme designer mode, and a Behat run initialised with `--scss-deprecations` fails every JavaScript
  step on a page that uses it (read in 5.2 and 5.3, not run). `accesshide` still exists in core SCSS.
- A partial is one self-contained element. A template whose root is a bare `<li>` fails CI's HTML validation of the
  example context; put the `<ul>` and its items in the same template, or render the list in the parent. A role
  such as `role="log"` goes on a `<div>` wrapper, not on an `<ol>`, which already has the list role.
- Template structure, example contexts and comment syntax belong to `moodle-theme-layouts-templates`.

## Buttons and links

| Element | Use for |
|---|---|
| `<button type="button">` | An action handled by JavaScript |
| `<button type="submit">` | Submitting a form |
| `<a href="...">` | Going to a URL |

Never `<a href="#">` with a click handler, and never `<div role="button">` unless it also has `tabindex="0"`,
Enter and Space handlers and a focus style; a `<button>` gives all of that for free. Link text says where it goes
("Edit Ana Lee's attendance"), not "click here". Icon-only links and buttons need a name; targets in a row of icons
should be at least 44 by 44 CSS pixels (moodledev.io accessibility policy, Icons).

## Icons

```mustache
{{! An icon on its own: the third argument is the accessible name. }}
<a href="{{editurl}}">{{#pix}}t/edit, core, {{#str}}edituser, local_example, {{fullname}}{{/str}}{{/pix}}</a>

{{! An icon next to text that says the same thing: no third argument, so it is hidden. }}
<button type="button" class="btn btn-secondary">{{#pix}}t/edit, core{{/pix}} {{#str}}edit, core{{/str}}</button>
```

With the Font Awesome icon system (Boost's default) a mapped icon renders as `<i class="icon fa ..." role="img"
aria-label="...">` when it has alt text, and with `aria-hidden="true"` when it has none
(`public/lib/templates/pix_icon_fontawesome.mustache`; `public/lib/classes/output/pix_icon.php:93-95`, read 5.2 and
5.3). Only an icon with no Font Awesome mapping renders as `<img alt>`. So: pass alt text when the icon is the only
content, pass none when text beside it says the same. `{{#pix}}` is sized for icons; use `<img>` with real `alt` for
pictures.

## Forms

- formslib gives every element a `<label for>`, marks required fields with `aria-required="true"`, and points an
  invalid field at its error with `aria-describedby` (`public/lib/form/templates/element-text.mustache:12-17`, read
  5.2 and 5.3). Do not rebuild these by hand; add elements with a label string.
- `placeholder` is not a label. A search box with only a placeholder has no stable accessible name.
- Custom JavaScript form widgets must set `aria-invalid="true"` on an invalid field and associate the message with
  `aria-describedby` (policy page, Forms). Boost's `theme_boost/form-display-errors` does this for formslib.
- `core/form-autocomplete` is keyboard-accessible as shipped; keep its label (`$mform->addElement('autocomplete',
  'x', get_string('label', ...))`) and do not hide its input. Its AJAX handler is in `moodle-amd-javascript`.
- Checkboxes outside an mform can join it with `form="<formid>"`; give each its own label.

## ARIA, live regions and dynamic content

- Prefer a native element or a Bootstrap component that already carries roles (tabs, collapse, dropdown); Boost's
  `theme_boost/aria` adds the missing keyboard support to Bootstrap menus. Patterns for building your own widget
  are in [reference/widget-patterns.md](moodle-skill-files/moodle-accessibility/reference/widget-patterns.md).
- Status messages after an AJAX action: `core/toast` `add()` writes into a `role="status" aria-live="polite"`
  region (`public/lib/templates/local/toast/wrapper.mustache`). `core/notification` `addNotification()` shows an
  alert in the page. Use `aria-live="assertive"` only for errors that block the user.
- Content that JavaScript replaces (`Templates.replaceNode()`) loses focus if the focused element was inside it.
  Move focus to the new content's heading or the control that replaced the old one.
- `aria-hidden="true"` on anything focusable hides it from screen readers while Tab still reaches it. Remove it from
  the tab order too, or do not hide it.
- `aria-label` on a `<div>` or `<span>` with no role is ignored by most screen readers; give it a role or use text.
- The `hidden` attribute loses to Bootstrap's `d-*` utilities (`!important`): an element with `hidden` and `d-flex`
  stays visible and announced. Toggle `d-none` instead (`moodle-amd-javascript`).

## Modals and overlays

- Use `core/modal` or a subclass. It sets `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing at the
  title (`public/lib/templates/modal.mustache:43`), traps focus while open, closes on Escape, and returns focus to
  `returnElement` or to the element that had focus when it opened.
- The title is a heading: **5.2 only:** `<h5>`; **5.3+:** `<h2 class="modal-title fs-5">`. Headings inside the body
  start at `<h3>` so the outline holds on 5.3 and is harmless on 5.2.
- Always give a modal a title, even a short one: it is the dialog's accessible name.
- Your own overlay (not `core/modal`) uses `core/local/aria/focuslock`:

```javascript
import {trapFocus, untrapFocus} from 'core/local/aria/focuslock';

trapFocus(panel);     // returns nothing; focuses the first focusable element in panel
// ... on close, including Escape:
untrapFocus();        // releases the most recent trap
opener.focus();
```

Traps stack, so every `trapFocus()` needs its `untrapFocus()` on every close path
(`public/lib/amd/src/local/aria/focuslock.js:328,363`, read 5.2 and 5.3). There is no `focusmanager` module and no
release function returned by `trapFocus()`.

## Colour, contrast and colour modes

- A plugin's `styles.css` takes colours from the theme: utility classes (`text-body`, `text-body-secondary`,
  `bg-body`, `bg-body-tertiary`, `border`, `text-bg-*`) or custom properties (`--mds-text-default`,
  `--mds-bg-surface-default`, `--mds-border-default`, `--bs-body-bg`, `--bs-body-color`). These follow the colour
  mode; `bg-white`, `bg-light`, `text-dark` and `#fff` do not (moodledev.io Colour modes guide; `public/lib/UPGRADING.md`
  5.3).
- **5.3+:** where a colour must differ in dark mode, scope it with `[data-bs-theme="dark"] .local-example-x { ... }`,
  never with `@media (prefers-color-scheme: dark)`: the user's or the site's choice overrides the device, so the
  media query applies on the wrong pages. On 5.2 the attribute selector simply never matches, so the same CSS is
  safe on both.
- A colour that carries meaning (status tint, diff highlight) keeps its hue and gets a darker shade for dark mode;
  status shown by colour also gets an icon or text.
- An SVG shown through `<img>` cannot inherit `currentColor` and stays black on a dark page. Render icons with
  `{{#pix}}` or `$OUTPUT->pix_icon()` so a mapped Font Awesome glyph follows the text colour; for your own image,
  choose a mid-tone that has contrast on white and on `#1d2125`, or ship a second file.
- Before checking contrast, confirm the custom property exists: an undefined `var(--x, #fallback)` silently uses the
  fallback on every theme (`getComputedStyle(el).getPropertyValue('--x')` returns `""`).
- SCSS variables (`$primary`, `$danger`) belong to the theme and must be set in pre-SCSS, before Bootstrap compiles;
  setting them in a theme's post-SCSS changes nothing already emitted. Palette and dark-mode SCSS are owned by
  `moodle-theme-scss`.

## Page titles and landmarks

- `$PAGE->set_title()` takes the most specific part first, joined with `moodle_page::TITLE_SEPARATOR`
  (`' | '`, `public/lib/pagelib.php:130`); core appends the site name, so do not add it.

```php
$PAGE->set_title(format_string($cm->name) . ': ' . get_string('report', 'local_example') .
    moodle_page::TITLE_SEPARATOR . format_string($course->fullname));
```

- Landmarks come from the theme's layout. Do not add `<main>` or `role="main"` in plugin output: the page already
  has one, and two fail axe's `landmark-no-duplicate-main`. A plugin `<nav>` or `role="search"` needs a unique
  `aria-label`. `core/search_input_auto` exposes a `{{$searchrole}}` block to drop its `role="search"` when it sits
  inside another search landmark (`public/lib/templates/search_input_auto.mustache:40`; read in 5.3.0 and 5.2.2,
  absent from 5.2.0 and 5.2.1, where the block is ignored and the role stays).

## Testing

```gherkin
@local_example @javascript @accessibility
Scenario: The attendance page meets accessibility standards
  # "local_example > Attendance" is a page type resolved by behat_local_example::resolve_page_instance_url().
  Given I am on the "C1" "local_example > Attendance" page logged in as "teacher1"
  Then the page should meet accessibility standards with "best-practice" extra tests
  And the "region-main" "region" should meet accessibility standards
```

- The step throws a DriverException unless the scenario or feature has `@accessibility`, needs `@javascript`, and
  does nothing at all on a run initialised with `--no-axe` (`behat_accessibility.php:101-111`, read 5.2 and 5.3).
- It loads `/lib/behat/axe/axe.min.js` from the site. A web server rule that denies paths containing `/behat/` makes
  every such step fail with "No data" locally while CI passes; allow `/lib/behat/axe/` on the test vhost.
- **5.3+:** run the suite twice, once plain and once after `php public/admin/tool/behat/cli/init.php --colourmode=dark`;
  do not pin a mode in accessibility scenarios.
- axe does not enter iframes and does not test most non-text contrast (borders, focus rings, icons). Those, keyboard
  operation and screen-reader output are manual checks: [reference/testing.md](moodle-skill-files/moodle-accessibility/reference/testing.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `<div onclick>` or `<a href="#">` for an action | Not focusable or announced as a link | `<button type="button">` |
| `{{#pix}}` with no alt as the only content of a link | Link has no accessible name; axe `link-name` | Pass the alt as the third argument |
| `{{#pix}}` with alt next to the same text | Name read twice | Drop the alt |
| Row checkboxes with only `aria-label` | Behat cannot set them by name; voice users cannot say them | `id` plus a `visually-hidden` `<label for>` |
| `sr-only` in new markup | Red deprecation outline on Behat sites; `--scss-deprecations` runs fail | `visually-hidden` |
| Heading levels skipped | Broken outline; axe best-practice `heading-order` | Follow the page's level; modal body starts at `<h3>` |
| `placeholder` as the only label | No stable name | `<label for>` |
| `outline: 0` with no replacement | Focus invisible | Keep Boost's focus style |
| `aria-hidden="true"` on a focusable element | Silent tab stop | Remove from tab order or unhide |
| Literal `#fff` or `bg-white` in plugin CSS | **5.3+:** light island or unreadable text in dark mode | `--mds-*` tokens or `bg-body*` utilities |
| `@media (prefers-color-scheme: dark)` | Applies on the wrong pages | `[data-bs-theme="dark"]` |
| SCSS colour variables set in post-SCSS | No effect | Pre-SCSS, in the theme (`moodle-theme-scss`) |
| Own overlay without `trapFocus()`/`untrapFocus()` | Focus escapes behind it, or stays trapped after close | `core/modal`, or `focuslock` on every close path |
| `import {trapFocus} from 'core/local/aria/focusmanager'` | Module not found | `core/local/aria/focuslock` |
| `@accessibility` steps pass on a `--no-axe` site | Nothing was checked | Check the init options of the run |
| A second `<main>` in plugin output | axe `landmark-no-duplicate-main` | Use `<section>` with a heading |

## Reference files

| File | Read it when |
|---|---|
| [reference/widget-patterns.md](moodle-skill-files/moodle-accessibility/reference/widget-patterns.md) | Building a custom interactive widget (tabs, disclosure, menu, listbox, tree, drag and drop), a live region, or managing focus after JavaScript replaces content |
| [reference/testing.md](moodle-skill-files/moodle-accessibility/reference/testing.md) | Writing or debugging `@accessibility` Behat scenarios, running axe outside Behat, or doing the manual keyboard, screen-reader, zoom and colour-mode checks before a release |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-accessibility/versions/moodle-5.3.md) |

## References

- Accessibility policy: https://moodledev.io/general/development/policies/accessibility
- Accessibility testing: https://moodledev.io/general/development/policies/accessibility/testing
- Colour modes (5.3): https://moodledev.io/docs/5.3/guides/colourmodes
- Templates: https://moodledev.io/docs/guides/templates
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
- Related skills: `moodle-amd-javascript`, `moodle-behat-testing`, `moodle-theme-scss`, `moodle-theme-testing-release`


---

### moodle-amd-javascript

> Use when writing or debugging JavaScript for a Moodle plugin - amd/src ES modules and the amd/build output, `grunt amd`, `js_call_amd()`, core/ajax, core/str, core/templates, core/modal and ModalEvents, core/notification and core/toast, core/pending for Behat, core/fragment, core/form-autocomplete ajax handlers, TinyMCE (editor_tiny) plugins, localStorage, Bootstrap imports, 5.3 core/import and React mounting, or errors such as "No define call for", "is not a function" on `.finally`, a named import that is undefined, "Too much data passed as arguments to js_call_amd", "The theme has already been set up". Skip when the work is server-side only (moodle-web-services for external functions) or theme-wide styling (moodle-theme-scss).

# Moodle AMD JavaScript

## Overview

Plugin JavaScript is written as ES modules in `amd/src/`, transpiled by Moodle's `grunt amd` into AMD modules in
`amd/build/*.min.js`, and loaded by RequireJS. This skill gives the build model, a module recipe that works on 5.2 and
5.3, and the traps that pass every linter and still break the page.

Evidence tags: **read** means read in the source of the named version, not run; **run 5.3.0** means observed on 5.3.0.

## When to Use

- Adding or changing a module in `amd/src/`, or calling one from PHP with `js_call_amd()`
- Calling an external function from the browser, rendering a Mustache template client-side, showing a modal or toast
- Building, linting or committing `amd/build/`, or reading a CI failure from `moodle-plugin-ci grunt`
- Writing a TinyMCE plugin, an autocomplete AJAX handler, a fragment callback, or anything that stores browser state
- **Skip when:** declaring the external function itself (`moodle-web-services`), making the UI accessible
  (`moodle-accessibility`, which owns ARIA, focus and contrast rules), styling a theme (`moodle-theme-scss`), or
  writing the Behat scenario (`moodle-behat-testing`).

## The model in five facts

1. **Module id = component + path under `amd/src`, no extension.** `local/example/amd/src/marker.js` is
   `local_example/marker`; `amd/src/net/client.js` is `local_example/net/client`. The loader fetches exactly
   `amd/build/<path>.min.js`; there is no `index` fallback (`core_requirejs::find_one_amd_module()`,
   `public/lib/classes/requirejs.php`, read 5.3.0).
2. **The build is Babel plus a Moodle plugin**: `.grunt/babel-plugin-add-module-to-define.js` names the module and,
   when the file has `export default`, makes the module return only that value (line 92, read 5.2 and 5.3).
3. **Core's AJAX layer still speaks jQuery Deferred.** `core/ajax` `call()` returns one jQuery promise per request
   (`public/lib/amd/src/ajax.js:69,95`, read 5.3.0); `core/str` `get_string()` is jQuery, `getString()` is native;
   `core/templates` `render()` is jQuery, `renderForPromise()` resolves `{html, js}`.
4. **`js_call_amd()` JSON-encodes its third argument** and calls `init(...args)`. Over 1024 characters of arguments
   raises a developer debugging message (`page_requirements_manager.php`, `$toomanyparamslimit`, read 5.2 and 5.3):
   pass ids and read the rest from `data-*` attributes or a web service.
5. **5.3+:** several core AMD names (`core/pending`, `core/config`, `core/log`, `core/url`, `core/localstorage`,
   `core/sessionstorage`, `core/storagewrapper`, `bootstrap/*`) are served from ES modules through a RequireJS map,
   so imports keep working although `public/lib/amd/src/pending.js` and friends no longer exist
   (`get_requirejs_static_esm_map()` in `page_requirements_manager.php`, read 5.3.0). Details in
   [versions/moodle-5.3.md](moodle-skill-files/moodle-amd-javascript/versions/moodle-5.3.md).

## Default recipe

```javascript
// amd/src/marker.js (GPL header)
/**
 * Mark attendance from the session page.
 *
 * @module     local_example/marker
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
import Ajax from 'core/ajax';
import Notification from 'core/notification';
import Pending from 'core/pending';
import Templates from 'core/templates';
import {getString} from 'core/str';
import {add as addToast} from 'core/toast';

const SELECTORS = {
    BUTTON: '[data-action="local_example/mark-present"]',
    ROW: '[data-region="local_example/attendance-row"]',
};

let initialised = false;

const markPresent = (sessionid, userid) => Promise.resolve(Ajax.call([{
    methodname: 'local_example_mark_present',
    args: {sessionid, userid},
}])[0]);

/**
 * Bind one delegated click handler for the page.
 *
 * @param {number} sessionid The session id
 */
export const init = (sessionid) => {
    if (initialised) {
        return;
    }
    initialised = true;
    document.addEventListener('click', async(e) => {
        const button = e.target.closest(SELECTORS.BUTTON);
        if (!button) {
            return;
        }
        e.preventDefault();
        const pending = new Pending('local_example/marker:mark');
        button.disabled = true;
        try {
            const row = await markPresent(sessionid, Number(button.dataset.userid));
            const {html, js} = await Templates.renderForPromise('local_example/row', row);
            Templates.replaceNode(button.closest(SELECTORS.ROW), html, js);
            addToast(await getString('marked', 'local_example'));
        } catch (error) {
            Notification.exception(error);
        } finally {
            button.disabled = false;
            pending.resolve();
        }
    });
};
```

```php
$PAGE->requires->js_call_amd('local_example/marker', 'init', [$session->id]);
```

Why each piece is there: `Promise.resolve()` turns the jQuery promise into a native one so `finally` exists;
`Pending` makes Behat wait for the request and the render; `renderForPromise()` returns the template's `{{#js}}` so
`replaceNode()` can run it; the `initialised` guard stops a second `js_call_amd()` on the same page from binding twice;
a `data-action` namespaced with the component cannot collide with core's selectors. The web service must be
declared with `'ajax' => true` in `db/services.php` (`moodle-web-services`); `core/ajax` adds the sesskey itself.

## Build, lint and commit

Run grunt from a Moodle checkout of the lowest branch you support, with Node from the checkout's `.nvmrc`
(`lts/jod` in 5.2 and 5.3), with the plugin installed in it:

```bash
cd /path/to/moodle && nvm use && npm ci
cd public/local/example && npx grunt amd     # inside the plugin: builds and lints only this component
npx grunt amd --root=public/local/example     # same, from the Moodle root
```

- Since 5.1 plugins live under `public/`; `--root=local/example` is fatal ("Setting root to ... failed - path does
  not exist", `Gruntfile.js` `getCwd()`, read 5.3.0).
- `grunt amd` is `ignorefiles, eslint:amd, rollup` (**5.3+:** plus `amdtypes`, which writes `.d.ts` files under the
  Moodle root's `.types/`, not into the plugin) (`.grunt/tasks/javascript.js:62`, read 5.2 and 5.3).
- Commit `amd/build/*.min.js` and `*.min.js.map` with the source. `moodle-plugin-ci grunt` rebuilds and fails when a
  committed `.js`, `.js.map` or `.css` differs, so a stale build is a CI failure, not a warning.
- Lint the way CI does: `moodle-plugin-ci grunt --max-lint-warnings 0`. A warning fails it.
- `grunt --force` skips failures it was meant to report: under `--force` eslint lints nothing while still printing its
  banner, and a failed write leaves the old build behind "Done, but with warnings". Never judge a build or a lint
  from a `--force` run; check the `amd/build` files are newer than `amd/src` (`moodle-definition-of-done`).

Reference: [reference/build-and-lint.md](moodle-skill-files/moodle-amd-javascript/reference/build-and-lint.md).

## Traps that pass every gate

Each is silent in eslint, grunt and PHPUnit; only a page load or a JavaScript Behat run shows it.

**`.finally()` on a `core/ajax` promise throws while the chain is built.** jQuery Deferred has no `finally`, so the
`.then` already attached runs once and the button stays disabled ("works exactly once"; console
`TypeError: ....finally is not a function`). Wrap: `Promise.resolve(Ajax.call([...])[0])`. Find them:
`grep -rn '\.finally(' amd/src/`.

**`export default` plus named exports loses the named ones.** The build returns `_exports.default` only, so
`import {thing} from 'local_example/util'` is `undefined` and the page dies at load. One style per module:
`grep -l '^export default' -r amd/src` and check those files export nothing else.

**A dynamic `import()` in `amd/src` is rewritten** into a RequireJS call by `system-import-transformer`
(`.grunt/tasks/javascript.js`, read 5.3.0), which fails for a bare ES module URL. **5.3+:** use
`import nativeImport from 'core/import'` and `await nativeImport('@moodle/lms/local_example/viewer')`. On 5.2, load
the ES module from a plain `.js` file outside `amd/` with `<script type="module">`.

**Vendored browser files: `.js`, not `.mjs`, and never under `vendor/`, `node_modules/`, `fixtures/` or `behat/`.**
Web servers often serve `.mjs` as `application/octet-stream`, which the browser refuses for a module. Core's own
security check `core\check\environment\publicpaths` expects the web server to deny those four path segments
(`public/lib/classes/check/environment/publicpaths.php`, read 5.2 and 5.3), so a correctly configured site 404s them.
Put third-party code in `amd/src/local/<lib>/` or `js/<lib>/` and list it in `thirdpartylibs.xml`.

**`localStorage` is wiped for the whole site** on every new login and every `jsrev` change (every cache purge).
5.2: `core/storage_validation` calls `LocalStorage.clean()` (`public/lib/amd/src/storage_validation.js`) and
`storagewrapper.js` clears on a `jsrev` change. 5.3: both checks live in `public/lib/js/esm/src/Storage.ts:98-120`,
and the login check also clears `sessionStorage`. Both call the browser's `Storage.clear()`, so keys a plugin wrote
directly are lost too. Durable state goes in a user preference (declare it in the privacy provider) or a cookie;
`core_user_set_user_preferences` cannot unset a value, so store `0` to mean "forget".

**An awaited browser promise with no timeout can hang for ever.** An ES module that throws while running fires no
`error` event on its `<script>`; `AudioContext.resume()` and `speechSynthesis` can stay pending in Firefox. Race
each one with a timeout and show a message, and check every screen in Firefox and a Chromium browser:

```javascript
const withTimeout = (promise, ms) => Promise.race([
    promise,
    new Promise((resolve, reject) => setTimeout(() => reject(new Error('Timed out')), ms)),
]);
```

**`core/templates` overwrites a context key named `uniqid`** with its own counter
(`public/lib/amd/src/local/templates/renderer.js:522`, read 5.3.0). Rename it. Template authoring rules (example
context, comments, partial roots) are in `moodle-theme-layouts-templates`.

**User text in a modal title, toast or `Notification` string is HTML.** `setTitle()` uses jQuery `.html()`
(`public/lib/amd/src/modal.js:495-505`, read 5.3.0). Pass lang strings, and put user data in through `textContent`
or escape it server-side; the full sink list is in `moodle-release-preflight`.

**An `output_fragment_*` callback must not call `require_login()`** or anything that sets `$PAGE->course`:
`core_external::get_fragment()` has already run `validate_context()` and printed the header
(`public/lib/external/externallib.php:404-415`, read 5.3.0), so the call throws "The theme has already been set up".
Check capabilities only, and test through `core/fragment` `loadFragment()` in a JavaScript Behat step; calling the
callback directly from PHPUnit passes.

## Modals

`core/modal` and its subclasses (`core/modal_save_cancel`, `core/modal_delete_cancel`, `core/modal_cancel`) exist on
5.2 and 5.3; `core/modal_factory` is gone (no `public/lib/amd/src/modal_factory.js` in either).

```javascript
import ModalSaveCancel from 'core/modal_save_cancel';
import ModalEvents from 'core/modal_events';
import Notification from 'core/notification';
import Templates from 'core/templates';
import {getString} from 'core/str';

const modal = await ModalSaveCancel.create({
    title: getString('confirmtitle', 'local_example'),
    body: Templates.render('local_example/confirm', {name: 'A'}),
    removeOnClose: true,
    show: true,
});
modal.getRoot().on(ModalEvents.save, (e) => {
    e.preventDefault();
    save().then(() => modal.destroy()).catch(Notification.exception);
});
```

- `removeOnClose` defaults to `false` (`configure()` in `modal.js`, read 5.2 and 5.3): without it every open adds
  another hidden modal to the DOM.
- **Cleanup must cover every close path.** Cancel, Escape and a backdrop click never run the save handler.
  `ModalEvents.destroyed` bound on `modal.getRoot()` never fires: `destroy()` calls `this.root.remove()` (which unbinds
  jQuery handlers) and then triggers the event (`modal.js:1011-1012`, read 5.2 and 5.3). Test
  `modal.getRoot()[0].isConnected` where code must know the modal is gone. `ModalEvents.hidden` is triggered by
  `hide()`, which `destroy()` calls before removing the root, so it covers every close path of a modal that has been
  shown. `hide()` triggers it from the backdrop promise's callback, so on a modal destroyed before its first `show()`
  finished the event can come after the root is removed and is lost (`modal.js:963-1013`, read 5.2 and 5.3, not
  run).
- `core/modal` traps focus and returns it to the opener (`returnElement`, else the active element at `show()`); the
  heading level and labelling rules are in `moodle-accessibility`.
- A form in a modal: `core_form/modalform` with a `\core_form\dynamic_form` class. A dynamic form must
  `require_once` any library that is not autoloaded and request its AMD from `render()`, not `definition()`
  (`moodle-field-lessons`).

Reference: [reference/modals-forms-editors.md](moodle-skill-files/moodle-amd-javascript/reference/modals-forms-editors.md).

## TinyMCE (editor_tiny) and form JavaScript

- **A Tiny plugin button appears only through `configuration.js`.** `addButton()` / `addMenuItem()` in `commands.js`
  only make it referenceable; `plugin.js` must resolve `[`${component}/plugin`, Configuration]` and
  `configuration.js` must export `configure()` returning the toolbar and menu with the button added
  (`public/lib/editor/tiny/plugins/h5p/amd/src/{plugin,configuration}.js`, read 5.3.0). This holds with zero
  settings.
- **TinyMCE writes back to its textarea on blur and on the form's submit event** (`editor_tiny/editor`
  `setupForTarget()`, read 5.3.0). Code that serialises the form itself (`new FormData(form)`, `$(form).serialize()`)
  without a submit gets the old `name[text]`. Before reading: `getInstanceForElement(textarea)?.save()` from
  `editor_tiny/editor`, then `notifyFormSubmittedByJavascript(form)` from `core_form/events`, as core's modal forms
  do, so the autosave plugin drops its draft.
- Behat: generator-created rich text needs an HTML format (`contentformat` / `introformat` `1`), or the field is a
  plain textarea and no `tox-tinymce` element exists (`moodle-behat-testing`).
- `core/form-autocomplete` with `ajax` or `tags` does not check submitted values against the options, so validate
  them in the form's `validation()` and in the web service. The AJAX handler module exports `transport()` and
  `processResults()`; template in [reference/modals-forms-editors.md](moodle-skill-files/moodle-amd-javascript/reference/modals-forms-editors.md).
- Read a dropped or pasted `File` inside the event handler; the `DataTransfer` is emptied after it returns.

## Bootstrap and markup built in JavaScript

- Import Bootstrap components as `import {Tooltip} from 'theme_boost/index'` on 5.2 and 5.3. **5.3+:**
  `import {Tooltip} from 'bootstrap'` is the new name and `theme_boost/bootstrap/*` is deprecated
  (`public/theme/boost/UPGRADING.md`, MDL-88766; old names are mapped in `theme_boost\hook_listener`, read 5.3.0).
- Markup built in JavaScript uses Bootstrap 5 classes (`visually-hidden`, `me-2`, `fw-bold`): a Bootstrap 4 name
  fails every JavaScript step of a Behat run initialised with `--scss-deprecations`, on 5.2 and 5.3 (read in
  `public/lib/behat/classes/behat_session_trait.php` `look_for_deprecated_styles()`, not run).
- The `hidden` attribute loses to `d-flex` and other `d-*` utilities (they are `!important`): toggle `d-none`.
- Code that scrolls an element into view on a phone treats the bottom of Boost's fixed navbar (`$navbar-height: 60px`,
  `public/theme/boost/scss/moodle/variables.scss:28`, read 5.3.0) as the top of the visible area.

## ESLint

Moodle's root `.eslintrc` applies; rules are scoped by path, so lint inside a Moodle checkout, not a copy elsewhere.
JSDoc on every exported function, `const`/`let`, no `console.log` (use `core/log`), Moodle-style `async(e) =>` with
no space. A deliberate no-op satisfies `no-empty-function` with a comment as its body:
`const noop = () => { /* Intentionally empty. */ };`.

## Testing

AMD modules have no unit-test runner on 5.2 or 5.3: no `grunt jest` task exists, and **5.3+:** `npm test` runs Jest
over the `js/esm` tree only (`package.json`). Test AMD behaviour with an `@javascript` Behat scenario
(`moodle-behat-testing`), which is also the only gate that catches the traps above; keep logic that needs unit
tests in PHP or in a `js/esm` module.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Editing `amd/build/*.min.js` | Overwritten at next build; CI's stale-build check fails | Edit `amd/src`, run `npx grunt amd` |
| Committing `amd/src` without `amd/build` | Sites load the old code; CI fails | Rebuild, commit both |
| `--root=local/example` on 5.1+ | Grunt fatal: path does not exist | `--root=public/local/example`, or run inside the plugin |
| `.finally()` on `Ajax.call()[0]` | Works once, then throws | `Promise.resolve(...)` first |
| `export default` and named exports in one file | Named import is `undefined` at load | One export style per module |
| `import()` in `amd/src` | Rewritten to RequireJS; fails | **5.3+:** `core/import`; 5.2: plain `.js` outside `amd/` |
| No `Pending` around async work | Flaky Behat | `new Pending(key)`, `resolve()` in `finally` |
| `import ModalFactory from 'core/modal_factory'` | Module not found on 5.2 and 5.3 | `core/modal` or a subclass's `create()` |
| Teardown on `ModalEvents.destroyed` bound on the root | Never runs | `ModalEvents.hidden`, or check `isConnected` |
| User text into `setTitle()` / toast | Stored XSS | Lang strings; user data via `textContent` |
| Big arrays in `js_call_amd()` args | Debugging notice, slow page | Ids only; fetch the rest |
| State in `localStorage` | Lost at next login or purge | User preference or cookie |
| Vendored file under `vendor/` or as `.mjs` | 404 or refused MIME type on production | `.js` under `amd/src/local/` or `js/` |
| `require_login()` in a fragment callback | "The theme has already been set up" | Capability checks only |
| `FormData` from a form with TinyMCE, no submit | Stale editor text saved | `editor.save()` first |
| Context key `uniqid` in a JS-rendered template | Value replaced by a counter | Rename the key |

## Reference files

| File | Read it when |
|---|---|
| [reference/core-modules.md](moodle-skill-files/moodle-amd-javascript/reference/core-modules.md) | You need the exact API of a core module (`core/ajax`, `core/str`, `core/templates`, `core/notification`, `core/toast`, `core/pending`, `core/fragment`, `core/url`, `core/config`, `core/storagewrapper`, `core/local/aria/focuslock`) or whether it returns a jQuery or a native promise |
| [reference/modals-forms-editors.md](moodle-skill-files/moodle-amd-javascript/reference/modals-forms-editors.md) | Writing a modal subclass, a modal or dynamic form, a TinyMCE plugin, or a `core/form-autocomplete` AJAX handler |
| [reference/build-and-lint.md](moodle-skill-files/moodle-amd-javascript/reference/build-and-lint.md) | Grunt or `moodle-plugin-ci grunt` fails, the build looks stale, you vendor a third-party library, or you split code into sub-folders of `amd/src` |
| [reference/esm-react.md](moodle-skill-files/moodle-amd-javascript/reference/esm-react.md) | Writing TypeScript or React in `js/esm/src`, mounting a React component from PHP or Mustache, loading an ES module from AMD, or running Jest |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-amd-javascript/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-amd-javascript/versions/moodle-5.3.md) |

## References

- JavaScript modules: https://moodledev.io/docs/guides/javascript/modules
- JavaScript guide: https://moodledev.io/docs/guides/javascript
- Templates from JavaScript: https://moodledev.io/docs/guides/templates
- Modal dialogues: https://moodledev.io/docs/guides/javascript/modal
- TinyMCE plugins: https://moodledev.io/docs/apis/plugintypes/tiny
- React in Moodle (5.3): https://moodledev.io/docs/5.3/guides/javascript/react
- JavaScript coding style: https://moodledev.io/general/development/policies/codingstyle/javascript
- Related skills: `moodle-web-services`, `moodle-accessibility`, `moodle-behat-testing`, `moodle-field-lessons`


---

### moodle-behat-testing

> Use when writing, running or debugging Behat acceptance tests for a Moodle plugin - tests/behat/*.feature, behat_<component>.php step definitions, tests/generator/behat_<component>_generator.php and the "the following ... exist" step, public/admin/tool/behat/cli/init.php and run.php, @javascript scenarios, --scss-deprecations, "Deprecated style in use", "Deprecated styles found", gherkinlint failures in moodle-plugin-ci grunt, "I set the field" matching the wrong field, "I should not see" passing for the wrong reason, a new feature or step not being picked up, faildumps, or user tours blocking clicks. Covers the Behat site's mental model, the default feature and step recipe, and locator and assertion traps. Skip when testing business logic without a browser (moodle-phpunit-testing), building the CI workflow (moodle-ci-matrix), writing or fixing the axe accessibility steps (moodle-accessibility), or running a theme's own suite (moodle-theme-testing-release).

# Moodle Behat testing

## Overview

Behat drives a browser, or the BrowserKit driver for scenarios without `@javascript`, against a second Moodle site
built for testing. Features live in `<plugin>/tests/behat/*.feature`; custom steps in
`tests/behat/behat_<component>.php`. Most failures that waste time are not in the scenario: the run used a stale copy,
a locator matched another field, or a negative step passed because the text was never going to be on the page.

How sure each statement is: rules marked "seen in practice" were observed on real plugins and themes; everything
else was read in the 5.2 and 5.3.0 source (paths relative to the Moodle root) and not run for this skill.

## When to Use

- Writing a feature for a plugin's UI, forms, JavaScript, permissions or navigation
- Adding a Behat data generator or custom step
- A scenario passes locally and fails in CI, or the other way round
- A step matches the wrong element, a negative step passes vacuously, or a change is not picked up
- **Skip when:** testing logic without a browser (`moodle-phpunit-testing`), building the CI workflow
  (`moodle-ci-matrix`), or testing a theme's own suite, overrides and `blacklist.json`
  (`moodle-theme-testing-release`).

## Mental model

1. **A separate site.** `$CFG->behat_wwwroot`, `$CFG->behat_prefix` and `$CFG->behat_dataroot` in `config.php` define
   it (`config-dist.php`). `init.php` installs it and writes the Behat config (`behat.yml`) listing every feature
   and context class found in the Moodle tree. Never edit `behat.yml`; it is regenerated.
2. **The run reads the Moodle tree, not your repository.** Behat executes the copy of the plugin installed under the
   Moodle root. A new `.feature` file, a new `behat_*.php` context, or a new generator entity is unknown until
   `init.php` (or `util.php --enable`) runs again. Behat also caches each parsed feature and reuses the parse while
   the cache entry is newer than the feature file (`FileCache::isFresh()` in `vendor/behat/gherkin`), so a copy that
   keeps old timestamps can run the old scenario; `touch` the copied features. Seen in practice.
3. **Run options are fixed at init.** `init.php --scss-deprecations`, `--no-axe`, `--no-icon-deprecations` and
   (**5.3+:**) `--colourmode=dark` are stored for the site; `run.php` has no such options. The run header prints them
   under "Run optional tests:" (`public/lib/behat/classes/util.php`, 5.2 and 5.3). Read that banner before trusting
   a run.
4. **Suites follow themes.** The default theme's suite is `default`; every other installed theme gets a suite named
   after it holding only that theme's features (`public/lib/behat/classes/behat_config_util.php`). A plugin's
   features run in `default`.
5. **Each scenario starts from a fresh site.** Data comes from `Background` generator steps, not from earlier
   scenarios. Theme CSS is prebuilt at init and restored per scenario, so a changed SCSS or `styles.css` needs a
   re-init too.

## Setup and running

From the Moodle root (5.1 and later keep `admin/tool/behat` under `public/`):

```bash
php public/admin/tool/behat/cli/init.php --scss-deprecations          # as CI runs it
php public/admin/tool/behat/cli/run.php --tags=@local_example          # the plugin's features
php public/admin/tool/behat/cli/run.php --tags=@local_example --name="Teacher marks a student present"
php public/admin/tool/behat/cli/init.php --parallel=3 && php public/admin/tool/behat/cli/run.php --tags=@local_example
```

- `@javascript` scenarios need a WebDriver server (Selenium, or chromedriver/geckodriver) at the address in
  `$CFG->behat_profiles` or the default `localhost:4444`.
- **Run local Behat with `--scss-deprecations`, as `moodle-plugin-ci behat --scss-deprecations` does in the standard
  workflow.** With it, every step of a JavaScript scenario fails when any element on the page shows a Bootstrap 4
  compatibility class such as `.sr-only`, `.mr-2`, `.ml-auto` or `.font-weight-bold` ("Deprecated style in use",
  `look_for_deprecated_styles()` in `public/lib/behat/classes/behat_session_trait.php`; the class list is
  `public/theme/boost/scss/moodle/bs4-compat.scss`, 5.2 and 5.3), including markup your JavaScript builds and core
  steps that only visit your page. Fix: Bootstrap 5 names (`visually-hidden`, `me-2`, `ms-auto`, `fw-bold`). Seen
  in practice on 5.2 and 5.3. `run.php` hands options it does not know to Behat, so `--scss-deprecations` given
  to `run.php` fails with "option does not exist".
- **Compare the scenario count with the repository.** Before reading a result, check the summary's scenario count
  against `grep -c '^ *Scenario' tests/behat/*.feature`. A lower count means a stale or missing copy. Seen in
  practice.

## The default feature

```gherkin
@local @local_example
Feature: Mark attendance
  In order to track presence
  As a teacher
  I need to mark students present

  Background:
    Given the following "courses" exist:
      | fullname | shortname |
      | Maths    | M101      |
    And the following "users" exist:
      | username | firstname | lastname |
      | teacher1 | Tina      | Teach    |
      | student1 | Sam       | Student  |
    And the following "course enrolments" exist:
      | user     | course | role           |
      | teacher1 | M101   | editingteacher |
      | student1 | M101   | student        |

  @javascript
  Scenario: Teacher marks a student present
    Given I am on the "M101" "Course" page logged in as "teacher1"
    When I click on "Mark present" "button" in the "Sam Student" "table_row"
    Then I should see "1 present" in the "Today" "region"
    And I should not see "0 present" in the "Today" "region"
```

- **Tags.** `moodle-plugin-ci validate` requires both `@<plugintype>` and `@<component>` on every feature
  (`@local @local_example`; `@mod @mod_example`; `@theme @theme_example`). `@javascript` selects a real browser.
  `@_file_upload`, `@_switch_window` and `@_alert` mark scenarios that need those browser features.
- **Shape that gherkinlint enforces** (core `.gherkin-lintrc`, run by `moodle-plugin-ci grunt`): Feature at column
  0, Background and Scenario at 2, steps at 4, `Examples` at 4, example rows at 6; no trailing spaces; no two empty
  lines in a row; a newline at the end of the file; no duplicate feature names; no file without scenarios. A blank
  line after the last step fails as "Multiple empty lines are not allowed": the linter splits on newlines, so the
  blank line and the final newline count as two empty lines (`no-multiple-empty-lines` in gherkin-lint 4.2.2, read
  in its source, not run).
- **One scenario, one claim, proved in both directions** (see the rules below). Prefer `I am on the "<identifier>"
  "<type>" page logged in as "<user>"` to clicking through navigation.

## Data generators and custom steps

Plugin entities for `the following "local_example > items" exist:` come from a Behat generator next to the PHPUnit
one, `tests/generator/behat_local_example_generator.php`, which reuses the PHPUnit generator's `create_item()`:

```php
class behat_local_example_generator extends behat_generator_base {
    #[\Override]
    protected function get_creatable_entities(): array {
        return [
            'items' => [
                'singular' => 'item',
                'datagenerator' => 'item',
                'required' => ['name'],
                'switchids' => ['course' => 'courseid', 'user' => 'userid'],
            ],
        ];
    }
}
```

`switchids` turns a `course` column (shortname) and a `user` column (username) into ids through `get_course_id()`
and `get_user_id()` of `behat_generator_base` (`public/lib/behat/classes/behat_generator_base.php`). Custom steps go
in `tests/behat/behat_local_example.php`, class `behat_local_example extends behat_base`. The full step template,
page resolvers and named selectors are in [reference/generators-and-steps.md](moodle-skill-files/moodle-behat-testing/reference/generators-and-steps.md).

## Rules for locating and asserting

Each was seen in practice on shipped plugins.

- **`I set the field "X"` matches any field whose label contains X.** "Name" also matches "Short name" and "Name
  display". Fix: use the element id, `I set the field "id_name" to "Maths"`, or a scoped form
  `I set the field "Name" in the "General" "fieldset" to "Maths"`.
- **Field locators match id, name, `<label>` text and placeholder, not `aria-label`.** A row checkbox with only an
  `aria-label` cannot be set. Fix in the template: give it an id and an `accesshide` label:
  `<input type="checkbox" id="item-{{id}}" name="items[]" value="{{id}}"><label for="item-{{id}}" class="accesshide">{{name}}</label>`.
- **A page-wide "I should not see" also reads the course index, block drawer and navigation.** An activity name
  that you expect to be gone from the table is still in the course index, so the step fails; text that never renders
  anywhere makes it pass for nothing. Fix: scope it to the container that would hold the text,
  `I should not see "Quiz 2" in the "Student One" "table_row"` or `... in the "region-main" "region"`, and pair it
  with a positive step in the same container so the container is known to exist.
- **Submit buttons are never unique on a Moodle page.** The page header, a block or a modal can hold another
  "Save changes". Fix: `I press "Save changes"` only when it is the single one; otherwise scope it,
  `I click on "Save changes" "button" in the "Edit item" "dialogue"`.
- **Every "I should see" for a mode needs "I should not see" for the other modes.** A setting with three modes
  gets, per mode, positive steps for that mode's fields and negative steps for the other two. Without them a form
  that shows every field in every mode passes.
- **Assert what only the success state shows.** A heading or message that also appears on the failure page, or a URL
  change that differs only by `#fragment` (which does not reload), proves nothing. Fix: assert a marker unique to the
  destination, such as the saved value in the table or a success notification.
- **Restriction and availability texts differ per condition.** A date condition in the past says "Available until
  <date>", not "Not available unless". Fix: copy the expected text from the condition's lang string or the page,
  never from memory.
- **Generator-created rich text needs an HTML format.** An activity created with `intro` and no format, or a text
  field with `FORMAT_MOODLE`, can stop TinyMCE attaching in JavaScript scenarios. Fix: pass the format column,
  for example `| introformat | 1 |`.
- **TinyMCE writes to the hidden `name[text]` textarea only on submit.** A step or script that reads the textarea
  before submitting reads the old value; code that submits a form from JavaScript must call
  `notifyFormSubmittedByJavascript()` from `core_form/events` first (`moodle-amd-javascript`).
- **formslib puts a radio's class on its label, and `:checked` does not see JavaScript-set state.** Select the radio
  by its id, assert with `the field "id_mode_2" matches value "1"`, not a CSS `:checked` selector. A drop or paste
  scenario that passes while real users get an empty file usually means the code read the `File` after the event
  handler returned, when the browser has already emptied the `DataTransfer`; read it inside the handler
  (`moodle-amd-javascript`).
- **`I navigate to "A > B" in site administration` does not fail on an ambiguous path.** Two plugins with a "General
  settings" page collide and the step opens the other one. Fix: navigate to your category, then follow your page.
- **Read the failure dump first.** Set `$CFG->behat_faildump_path`; the HTML and screenshot of the failing step
  usually show the cause (a debugging() message, a modal, the wrong page) faster than re-running.

## Environment facts that break scenarios

- **Site home is off on new installs.** `enablemyhome` defaults to 0 on 5.2 and 5.3
  (`public/admin/settings/appearance.php`), so `I am on site homepage` lands on the dashboard and logged-out users go
  to the login page (`public/index.php`). A feature that needs site home sets it in the Background, as core
  features do (`public/lib/tests/behat/switch_editing_mode.feature`, 5.3.0); add `defaulthomepage` 0 too when users
  must land on it after login:

  ```gherkin
    Background:
      Given the following config values are set as admin:
        | enablemyhome    | 1 |
        | defaulthomepage | 0 |
  ```

  Upgraded sites keep site home (an upgrade step sets `enablemyhome` to 1, `public/lib/db/upgrade.php`).
- **User tours cover the page on a user's first visit.** A tour's backdrop blocks clicks and screenshots. On a
  Behat site the shipped tours are installed disabled (`public/admin/tool/usertours/classes/manager.php`); in other
  browser automation, mark the tours complete for the test users first. Seen in practice.
- **Accessibility steps load axe from `/lib/behat/axe/axe.min.js`.** A web-server rule that denies paths containing
  `/behat/` (some hardened configurations do) makes every `the page should meet accessibility standards` step fail
  with "No data". Steps also need `@accessibility` and `@javascript`, and pass without checking anything when the
  site was initialised with `--no-axe`. Seen in practice. Accessibility rules: `moodle-accessibility`.
- **Boost puts the block drawer outside `#page`.** Selectors that scope to `#page` do not see blocks; use the
  `"block"` selector with the block title (`moodle-theme-layouts-templates` for page structure).
- **Add activities with core's step**, `I add an "assign" activity to course "M101" section "1"` (or `... and I
  fill the form with:`), rather than clicking the chooser. The first argument is the module name, not its display
  name; the step opens `course/modedit.php?add=assign` directly, and the course may be named by idnumber, short
  name or full name (`public/course/tests/behat/behat_course.php`, `behat_session_trait::get_course_id()`, 5.2 and
  5.3). A hand-written click path breaks: "Add an activity or resource" is a plain button in some places and an
  item inside the "Add content" dropdown in others (`hasactionlinks` in
  `public/course/format/templates/local/content/activitychooserbutton.mustache`), and that dropdown's button shows
  only an icon on 5.2 and an icon with the text on 5.3.
- **A debugging() message fails the step that showed it.** A deprecated API called by your page (for example
  `moveto_module()` on 5.2) fails Behat even though PHPUnit passed; fix the call (`moodle-upgrade-migration`).
- **A deprecated core step fails the scenario.** It throws "Deprecated step, rather than using this step you can:"
  unless `$CFG->behat_usedeprecated` is set (`public/lib/behat/behat_deprecated_base.php`, 5.2 and 5.3). Use the
  replacement it names; when the replacement does not exist on your lowest branch, write the step in your own
  context.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| New feature, step or generator entity, no re-init | "Undefined step", or the old scenario runs | `init.php` again; compare the scenario count |
| Local run without `--scss-deprecations` | Green locally, red in CI on Bootstrap 4 classes | `init.php --scss-deprecations`; read the banner |
| Missing `@<plugintype>` tag | `moodle-plugin-ci validate` fails | `@local @local_example` on every feature |
| Trailing blank line, trailing spaces or tab indentation in a feature | gherkinlint fails the `grunt` step | End the file with one newline right after the last step; indent with spaces |
| `I set the field "Name"` | Sets "Short name" or the wrong form | `id_<element>` or a scoped step |
| Page-wide `I should not see` | Fails on the course index, or passes for nothing | Scope to the container |
| Only positive steps for a mode switch | Every field shown in every mode passes | Negative steps for the other modes |
| `I wait "5" seconds` | Slow and still flaky | `I wait until the page is ready`, or a step that waits for an element |
| AJAX UI scenario without `@javascript` | BrowserKit cannot run the JavaScript | Tag `@javascript` |
| Generator entity defined in `behat_<component>.php` | "the following ... exist" does not know it | `tests/generator/behat_<component>_generator.php` |
| `get_string()` text copied by memory | Expected text never matches | Copy from the lang file or the page |
| Editing `behat.yml` | Lost on the next init | Change `config.php` or init options |
| `I press "Save changes"` with two such buttons on the page | Presses the wrong one, or the step is ambiguous | Scope it to the form, region or dialogue |
| `I am on site homepage` on a fresh 5.2 or 5.3 site | Lands on the dashboard or login page | Set `enablemyhome` 1 in the Background |
| Accessibility step without `@accessibility` | The step throws | Tag the scenario `@accessibility @javascript` |

## Reference files

| File | Read it when |
|---|---|
| [reference/generators-and-steps.md](moodle-skill-files/moodle-behat-testing/reference/generators-and-steps.md) | You add a Behat data generator entity, a custom step definition or a named selector, or need to know which built-in steps and selectors exist |
| [reference/debugging-and-runs.md](moodle-skill-files/moodle-behat-testing/reference/debugging-and-runs.md) | A run gives a result you do not trust: scenarios missing, a change not picked up, a failure only in CI, parallel runs, faildumps, or you drive Moodle with Playwright or a similar tool outside Behat |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-behat-testing/versions/moodle-5.3.md) |

## References

- https://moodledev.io/general/development/tools/behat
- https://moodledev.io/general/development/tools/behat/writing
- https://moodledev.io/general/development/tools/behat/running
- https://moodledev.io/docs/apis/subsystems/testing/generators (Behat generators)
- `public/lib/behat/classes/behat_generator_base.php`, `public/lib/tests/behat/behat_general.php`,
  `public/lib/tests/behat/behat_forms.php` (5.2 and 5.3): the step and generator source
- Theme suites and overrides: `moodle-theme-testing-release`. CI workflow: `moodle-ci-matrix`.


---

### moodle-ci-matrix

> Use when adding or updating a GitHub Actions workflow that runs moodle-plugin-ci for a Moodle plugin (.github/workflows/ci.yml from gha.dist.yml), choosing its Moodle branch x PHP x database matrix, or when CI fails at "Initialize containers", at moodle-plugin-ci install, with "requires at least PHP", an empty DB in a job, an artifact-name error, "No PHPUnit tests to run, free pass!", or green while the Plugins directory still rejects the plugin. Covers the upstream template and its steps, reading each branch's environment.xml and core push.yml, service image pins and health checks, include/exclude pitfalls, non-blocking rows for main, running the pipeline locally as written, secrets in logs, optional PHP extensions, and what a green run does not check. Skip when running PHPUnit or Behat locally with no workflow involved (moodle-phpunit-testing, moodle-behat-testing) or for theme-specific CI (moodle-theme-testing-release).

# Moodle plugin CI matrix (moodle-plugin-ci on GitHub Actions)

## Overview

`moodlehq/moodle-plugin-ci` runs Moodle's plugin checks (phplint, phpcs, phpdoc, validate, savepoints, mustache,
grunt, PHPUnit, Behat) against a real Moodle checkout, usually from GitHub Actions. The workflow is short; most
breakage comes from the matrix, a Moodle branch paired with a PHP or database version that branch does not support,
and from believing a green run proves more than it does. Verify every combination against a source.

How sure each statement is: the moodle-plugin-ci statements were read in the 4.5.11 source; branch requirements were
read in the 5.2 and 5.3.0 trees (`public/admin/environment.xml`, `.github/workflows/push.yml`); the template's
steps and images are as published with moodle-plugin-ci 4.5.11, so compare them with the file you fetch; the
workflow below was written for a plugin supporting 5.2 and 5.3 and has not been run for this skill. "Seen in
practice" marks failures observed on real plugin workflows.

## When to Use

- Adding `.github/workflows/ci.yml` (or `moodle-ci.yml`) to a plugin repository
- Adding or dropping a Moodle branch, PHP version or database in an existing matrix
- CI fails at "Initialize containers", at `moodle-plugin-ci install`, or with a requirement error such as
  "Moodle 5.2 or later requires at least PHP 8.3.0" (`public/lib/phpminimumversionlib.php`)
- Adding a non-blocking row for Moodle `main` (the next release, in development)
- Deciding whether a green run is enough before a Plugins directory submission
- **Skip when:** running PHPUnit or Behat locally with no workflow involved (`moodle-phpunit-testing`,
  `moodle-behat-testing`); a theme's own suite, stylelint over `scss/` and Mustache lint of overridden templates
  (`moodle-theme-testing-release`); tagging and the release workflow (`moodle-plugin-release`).

## Mental model

1. **The workflow is the upstream template plus a matrix.** Each job checks the plugin out into `plugin/`, installs
   moodle-plugin-ci into `ci/`, runs `moodle-plugin-ci install`, which clones Moodle at `MOODLE_BRANCH`, copies the
   plugin in, installs it on database `DB` and initialises PHPUnit and Behat, then runs one step per check.
2. **Each branch declares its own requirements.** The minimum PHP and database versions are in that branch's
   `environment.xml`; the highest PHP is visible only in core's own CI on that branch. Neighbouring branches differ.
3. **CI tests the checkout, not the ZIP, and only the code the tests reach.** Steps with no input pass: "No PHPUnit
   tests to run, free pass!" and "No Behat features to run, free pass!" (`src/Command/PHPUnitCommand.php`,
   `BehatCommand.php`, moodle-plugin-ci 4.5.11). Licence file, ZIP root, privacy compliance and most security rules
   are checked by nothing in it (reference file below).

## 1. Start from the upstream template

Do not write the workflow from memory, and do not copy an older sibling repository's workflow. Fetch the current
template:

```
https://raw.githubusercontent.com/moodlehq/moodle-plugin-ci/main/gha.dist.yml
```

Keep its job structure and check steps. Change only the matrix, service images, plugin path and triggers. The
template installs the tool with `composer create-project ... moodlehq/moodle-plugin-ci ci ^4`, which is
moodle-plugin-ci 4.x; check its documentation if you pin another major. The steps and the flags that make them strict:

| Step | Command in the template | Fails on |
|---|---|---|
| PHP lint | `moodle-plugin-ci phplint` | PHP syntax errors |
| Mess detector | `moodle-plugin-ci phpmd` with `continue-on-error: true` | Nothing: the command always exits 0, so read its output |
| Code checker | `moodle-plugin-ci phpcs --max-warnings 0` | moodle-cs errors and warnings, PHP files only |
| PHPDoc checker | `moodle-plugin-ci phpdoc --max-warnings 0` | the few inline-tag and argument rules local_moodlecheck still owns |
| Validate | `moodle-plugin-ci validate` | missing required files and strings, table prefixes, Behat tags |
| Savepoints | `moodle-plugin-ci savepoints` | upgrade steps without matching savepoints |
| Mustache | `moodle-plugin-ci mustache` | missing example context, HTML validator and ESLint warnings in templates |
| Grunt | `moodle-plugin-ci grunt --max-lint-warnings 0` | eslint, stylelint, gherkinlint, and any rebuilt `amd/build` file that differs from the committed one |
| PHPUnit | `moodle-plugin-ci phpunit --fail-on-warning` | failures and warnings |
| Behat | `moodle-plugin-ci behat --profile chrome --scss-deprecations` | failures, debugging() output, Bootstrap 4 classes on the page |

Run the same flags locally (`moodle-behat-testing` for `--scss-deprecations`; `moodle-phpunit-testing` for
warnings).

## 2. Decide the Moodle branches

- Test the branches the plugin claims to support: `$plugin->requires` and `$plugin->supported` in `version.php`, or
  the branches the user names. If the user asks for a narrower matrix, a wider `supported` range can stay in
  `version.php`, but say which branches CI covers. `requires` must not sit below the lowest `supported` branch
  (`moodle-plugin-development`).
- A plugin that depends on another plugin needs `moodle-plugin-ci add-plugin owner/repo` (optionally
  `--branch X`) before `install`.

## 3. Verify PHP and database per branch

For each branch, get the requirements from the branch itself:

1. **Minimum PHP and database versions:** that branch's `public/admin/environment.xml` (5.1 and later;
   `admin/environment.xml` on 5.0 and earlier).

   ```bash
   git clone --bare --filter=blob:none https://github.com/moodle/moodle.git moodle.git
   git --git-dir moodle.git show MOODLE_503_STABLE:public/admin/environment.xml \
     | awk '/<MOODLE version="5.3"/{s=1} s && /VENDOR name="(mariadb|mysql|postgres)"|PHP version=/{print} /<\/MOODLE>/{s=0}'
   ```

   The file holds one `<MOODLE version="X.Y">` block per release, including newer ones used for upgrade checks (the
   5.2 tree already has a 5.3 block). Read the block whose version matches the branch, not the last one.
2. **Maximum PHP:** not in `environment.xml`. Read core's `.github/workflows/push.yml` on the same branch: its
   comments mark the "lowest PHP supported" (MySQL job) and "highest PHP supported" (PostgreSQL job). Cross-check
   with the moodledev.io PHP page.
3. If you cannot verify a combination, leave it out and say so. Never infer one branch's requirements from the
   branches next to it.

The values read for each supported branch are in the version files below; branches before 5.2 are in
[reference/older-branches.md](moodle-skill-files/moodle-ci-matrix/reference/older-branches.md).

## 4. Build the matrix only from verified pairs

The default for a plugin supporting 5.2 and 5.3: each branch's lowest and highest PHP, the databases alternated,
and each row given the database images its branch needs.

```yaml
    services:
      postgres:
        image: ${{ matrix.database == 'pgsql' && (matrix.pgsql-image || 'postgres:16') || '' }}
        env:
          POSTGRES_USER: 'postgres'
          POSTGRES_HOST_AUTH_METHOD: 'trust'
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 3
      mariadb:
        image: ${{ matrix.database == 'mariadb' && (matrix.mariadb-image || 'mariadb:10.11') || '' }}
        env:
          MARIADB_ALLOW_EMPTY_ROOT_PASSWORD: '1'
          MYSQL_CHARACTER_SET_SERVER: "utf8mb4"
          MYSQL_COLLATION_SERVER: "utf8mb4_unicode_ci"
        ports:
          - 3306:3306
        options: --health-cmd="healthcheck.sh --connect --innodb_initialized" --health-interval 10s --health-timeout 5s --health-retries 3

    strategy:
      fail-fast: false
      matrix:
        include:
          # 5.2: PHP 8.3-8.4, PostgreSQL >= 16, MariaDB >= 10.11 (environment.xml, push.yml on MOODLE_502_STABLE).
          - {moodle-branch: MOODLE_502_STABLE, php: '8.3', database: mariadb}
          - {moodle-branch: MOODLE_502_STABLE, php: '8.4', database: pgsql}
          # 5.3: PHP 8.3-8.4, PostgreSQL >= 17, MariaDB >= 11.4 (same files on MOODLE_503_STABLE).
          - {moodle-branch: MOODLE_503_STABLE, php: '8.3', database: mariadb, mariadb-image: 'mariadb:11.4'}
          - {moodle-branch: MOODLE_503_STABLE, php: '8.4', database: pgsql, pgsql-image: 'postgres:17'}
```

**Several branches with different PHP ranges and a full database cross.** Use an object axis, so each branch keeps
its own PHP list and is still crossed with every database:

```yaml
      matrix:
        moodle:
          - {branch: MOODLE_502_STABLE, php: '8.3'}
          - {branch: MOODLE_502_STABLE, php: '8.4'}
          - {branch: MOODLE_503_STABLE, php: '8.3'}
          - {branch: MOODLE_503_STABLE, php: '8.4'}
        database: [pgsql, mariadb]
```

Then read `matrix.moodle.branch` and `matrix.moodle.php` in `setup-php` and in the `install` step's env. If you
cross flat `php:` and `moodle-branch:` axes instead, prune with `exclude:` and give each entry a comment naming the
source.

**`include:` trap.** GitHub first tries to merge an `include` entry into existing combinations. If it cannot merge
without overwriting an original value, it adds the entry as a new job with only the keys it lists. A
`{moodle-branch: X, php: Y}` entry added to a matrix that also has `database` becomes a job with an empty `DB`, and
`install` fails. With no original axes, as above, every `include` entry is its own job. Expand the matrix before
you push: parse the YAML and apply GitHub's documented rules with a short script. Seen in practice.

## 5. Service images

- Pin each database to the lowest version its branch supports. An image that is too new hides breakage at the
  minimum version, and one that is too old fails the newer branch. When one image must serve every row, pin the
  lowest version that satisfies every branch; when branches differ (5.2 and 5.3 do), make the image a matrix value
  with a default, as above.
- The upstream template's `postgres:17` and floating `mariadb:11` images (as published with 4.5.11) are newer
  than the minimum for 5.2. Pin them explicitly.
- **Health check:** MariaDB 11.x images do not ship `mysqladmin`, so `--health-cmd="mysqladmin ping"` never reports
  healthy and the job dies at "Initialize containers". Use `healthcheck.sh --connect --innodb_initialized` (as
  above) or `mariadb-admin ping`. Seen in practice on 11.x; that `mariadb:10.11` ships the same script was not
  re-checked for this skill, so watch the first 5.2 MariaDB row.
- Before changing any matrix key, grep the workflow for every `matrix.` consumer: the service images, `setup-php`,
  the install env and artifact names all read it.

## 6. Non-blocking row for `main`

Add the next Moodle release as an `include:` row that cannot fail the build:

```yaml
jobs:
  test:
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - {moodle-branch: MOODLE_503_STABLE, php: '8.4', database: pgsql, pgsql-image: 'postgres:17'}
          - {moodle-branch: main, php: '8.4', database: pgsql, pgsql-image: 'postgres:17', experimental: true}
```

- Read `main`'s requirements from the `<MOODLE>` block for the version `main` is building, at the commit you test;
  they change during development and can rise above the newest stable branch's.
- Keep the Grunt step, and any "committed `amd/build` is stale" check, on one stable branch:
  `if: ${{ !cancelled() && matrix.moodle-branch == 'MOODLE_502_STABLE' }}`. Each branch's toolchain can minify and
  lint differently, so a build committed from one branch shows as stale on another.
- **Artifact names:** the template's `Behat Faildump (${{ join(matrix.*, ', ') }})` joins every matrix value, so an
  image value like `postgres:17` puts a `:` in the artifact name, which `actions/upload-artifact` rejects. Name the
  fields: `Behat Faildump (${{ matrix.moodle-branch }}, PHP ${{ matrix.php }}, ${{ matrix.database }})`. Seen in
  practice.

## 7. Propose the matrix before writing it

Show the user a table (branch x PHP x database) with one line on how each axis was checked. Then write the file. A
workflow on the default branch runs on every push, so a wrong matrix is visible at once.

## 8. Make the plugin pass on the first run

CI that fails on its first run teaches everyone to ignore it. Before you finish, run each step locally the way the
workflow runs it; the commands, the work-directory rule and the `.env` checks are in
[reference/running-the-pipeline-locally.md](moodle-skill-files/moodle-ci-matrix/reference/running-the-pipeline-locally.md). The failures that keep
coming back:

- Every Mustache template in `templates/` needs an `Example context (json):` block in its docblock; a
  `.mustachelintignore` next to the template skips only HTML validation, not the rest.
- Lang strings sorted by key, and no PHP other than `$string['id'] = 'value';` in the lang file (phpcs
  `moodle.Files.LangFilesOrdering`).
- A blank line after the last step, trailing spaces or wrong indentation in a `.feature` file fails gherkinlint in
  the Grunt step (`moodle-behat-testing` has the shape core's `.gherkin-lintrc` enforces).
- Bootstrap 4 class names (`mr-2`, `sr-only`, `font-weight-bold`) in templates or in markup built by JavaScript fail
  every JavaScript Behat step under `--scss-deprecations` on 5.2 and 5.3. Seen in practice.
- `amd/build` rebuilt with the Node version and grunt of the branch the Grunt step runs on (Node `>=22.11.0 <23`
  in `package.json` on 5.2 and 5.3.0).

## 9. Traps outside the matrix

- **Run the pipeline as written.** A flag that looks equivalent tests a different pipeline: an explicit `install
  --extra-plugins <dir>` in place of the workflow's `add-plugin` step overrides the path that `add-plugin` wrote to
  moodle-plugin-ci's `.env` (`EXTRA_PLUGINS_DIR`), and it can fail on the runner with `Failed to run realpath(...)`.
  Keep `add-plugin`, and do not add `--extra-plugins`. Seen in practice.
- **No secret in a URL or an echoed argument.** GitHub masks a secret only where it appears verbatim; a token put
  into a URL, base64-encoded or split, is printed in clear. Pass secrets through `env:` and mask derived values
  before printing anything that contains them:

  ```yaml
      - name: Fetch private dependency
        env:
          TOKEN: ${{ secrets.DEPENDENCY_TOKEN }}
        run: |
          AUTH="$(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)"
          echo "::add-mask::$AUTH"
          git -c http.extraHeader="Authorization: Basic $AUTH" clone https://github.com/owner/dependency.git
  ```

- **A code path behind an optional PHP extension runs only where the extension is loaded.** A runner's PHP can load
  extensions a local site lacks (Imagick, for example), so an `extension_loaded('imagick')` branch that a GD-only
  local site skips runs on CI and fails there first. Seen in practice; which extensions a runner loads by default
  depends on the `setup-php` version and was not checked for this skill. Name the extensions you rely on in
  `setup-php`'s `extensions:` input so every row is explicit, test both paths deliberately (or load the extension
  locally, `moodle-phpunit-testing`), and expect CI-only failures when the local site lacks one.
- **The PostgreSQL rows are the only place PostgreSQL-sensitive tests run.** PHPUnit wraps each test in a
  transaction there and not on MariaDB, so observer, message and log-store tests can pass on one family and fail on
  the other (`moodle-phpunit-testing`). Keep at least one blocking PostgreSQL row per branch.
- **Reruns hide flakes.** `moodle-plugin-ci behat` reruns failed scenarios twice by default (`--auto-rerun`,
  `BehatCommand.php`). A scenario that needs a rerun is flaky; fix it, do not rely on the rerun.
- **Theme plugins:** `behat` picks the theme's own suite by default since moodle-plugin-ci 4.5.11 (older versions ran
  `default` and found no theme features, a green job with zero scenarios); every feature carries `@theme
  @theme_<name>`; stylelint lints the theme's whole `scss/` tree. The rest is in `moodle-theme-testing-release`.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Crossing all requested branches with "current" PHP | Unsupported pair; install fails the environment check | Check each branch's `environment.xml` and core `push.yml` |
| Reading the last `<MOODLE>` block in `environment.xml` | Picks up a newer release's minimums | Select `version="X.Y"` for the branch |
| Looking for `admin/environment.xml` on 5.1+ | File not found | `public/admin/environment.xml` |
| `include` entry missing the `database` key | Extra job with an empty `DB` | Use an object axis, or list every key |
| `mysqladmin ping` health check on MariaDB 11 | Containers never become healthy | `healthcheck.sh --connect --innodb_initialized` |
| One floating image (`postgres:17`, `mariadb:11`) for 5.2 rows | Hides breakage at 5.2's minimum | Per-row image values with the branch minimum as default |
| `join(matrix.*)` in the artifact name with image values in the matrix | upload-artifact rejects the name | Name the fields explicitly |
| `main` row without `continue-on-error` | Upstream churn breaks the build | `experimental: true` plus job-level `continue-on-error` |
| Grunt step on every branch | "File is stale and needs to be rebuilt" on the branches you did not build with | Run Grunt on one stable branch |
| Replacing `add-plugin` with `--extra-plugins` | Install fails at `realpath` on the runner | Keep the upstream step order |
| Running `moodle-plugin-ci install` inside the plugin repository | `package.json` and `node_modules/` written into the repository | Run it from a separate work directory |
| No tests, or no features | "free pass!", green job | Add tests; read the step log, not the tick |
| Trusting `phpmd`'s green tick | It always exits 0 | Read its output |
| Token in a clone URL | Secret printed in the log | `env:` plus `::add-mask::` for derived values |
| Treating green CI as Plugins directory ready | Rejected for licence file, ZIP root, strings or prefixes | Walk [reference/what-ci-does-not-check.md](moodle-skill-files/moodle-ci-matrix/reference/what-ci-does-not-check.md) |

## Reference files

| File | Read it when |
|---|---|
| [reference/running-the-pipeline-locally.md](moodle-skill-files/moodle-ci-matrix/reference/running-the-pipeline-locally.md) | You reproduce a CI failure locally, run moodle-plugin-ci outside GitHub Actions, or need to know which directory `install` writes to and what `.env` holds |
| [reference/what-ci-does-not-check.md](moodle-skill-files/moodle-ci-matrix/reference/what-ci-does-not-check.md) | A plugin with green CI is about to be submitted to the Plugins directory, a reviewer raised something CI did not, or you need to know exactly what one moodle-plugin-ci step checks |
| [reference/older-branches.md](moodle-skill-files/moodle-ci-matrix/reference/older-branches.md) | The matrix includes Moodle 5.1 or earlier, or you need the requirement values for a branch before 5.2 |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-ci-matrix/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-ci-matrix/versions/moodle-5.3.md) |

## References

- https://moodlehq.github.io/moodle-plugin-ci/ (moodle-plugin-ci documentation)
- https://github.com/moodlehq/moodle-plugin-ci/blob/main/gha.dist.yml (upstream GitHub Actions template)
- https://moodledev.io/general/development/tools/phpunit (PHPUnit in plugins)
- https://moodledev.io/general/releases (release dates and per-version requirements)
- https://moodledev.io/general/development/policies/php (PHP version support policy)
- https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow
  (matrix `include` and `exclude` rules)
- https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#masking-a-value-in-a-log
  (`::add-mask::`)
- When a new Moodle version is supported, add `versions/moodle-X.Y.md` with the values read from that branch and
  extend the default matrix in section 4.


---

### moodle-definition-of-done

> Use when about to report a Moodle plugin or theme task complete, open a pull request, or hand work over for review. A definition-of-done checklist covering the moodle-plugin-ci gates (phplint, phpcs, phpdoc/moodlecheck, validate, savepoints, mustache, grunt with eslint, stylelint and gherkinlint), reading gate output instead of piping it through tail, PHPUnit and Behat counts, install.xml and upgrade path, course lifecycle (backup, restore, reset, uninstall and user preferences), privacy provider coverage, lang strings, renames, installing on a real site with upgrade and cache purge, browser checks in Firefox and Chromium as each role, CSS evidence, and proving each check can fail. Skip when exploring or prototyping with no intent to ship, when the next step is a tag or a Plugins directory submission (moodle-release-preflight, then moodle-plugin-release), or for theme-only checks such as SCSS compile, dark mode and RTL (moodle-theme-testing-release).

# Moodle Definition of Done

## Overview

A checklist to walk before claiming any Moodle plugin or theme change is finished. Every item is reported as
**pass**, **fail**, or **not applicable, because ...**. Evidence comes before assertions: run the command,
read its output, and state what you saw. A gate you did not run is not a pass, and a gate that could not have
failed is not a pass either.

## When to Use

- Before saying "done" on a plugin or theme feature, fix, or refactor
- Before opening a pull request or requesting a review
- Before handing a change to a release (then `moodle-plugin-release`, and `moodle-release-preflight` for a
  submission or a changed security surface)
- **Skip when:** spiking or prototyping code that will not be merged. Theme-only checks (SCSS compile, dark
  mode, RTL, visual baselines) are in `moodle-theme-testing-release`.

## Four rules that govern every item

1. **A check that printed nothing has proven nothing.** Before trusting "0 findings", feed the gate one
   known-bad input (a missing docblock, an unsorted lang key, a deliberately failing test) and confirm it
   complains. A grep pattern that can never match, an empty test suite and a linter pointed at the wrong path
   all look exactly like "clean". A check run where its signal cannot appear proves nothing either.
2. **Verify the effect, not the exit code.** A script that did not throw has not necessarily worked. Read the
   DB row, the rendered page, the file on disk, or the log line that proves the change happened.
3. **Name the change the claim predicts, and assert that change.** "Saved on leaving" is checked by editing,
   leaving without pressing Save, and reopening. Two exports that are byte-identical prove nothing unless both
   were expected to change. A browser check passes only on a marker that the success state alone renders.
4. **A count or a "verified" names the run it came from.** Write "PHPUnit: 42 tests, 0 failures, run on
   5.3.0 after the last edit", taken from that run's output. A reading-only review of the code is a design
   check, not evidence of behaviour: the first real run of a change is still ahead of you.

## 1. The CI gates, run as CI runs them

Run the steps in the plugin's own workflow, with the same flags, using `moodle-plugin-ci` itself (it has real
exit codes for most steps). Redirect each to a log, record `$?` directly, then read the log:

```bash
for s in phplint "phpcs --max-warnings 0" "phpdoc --max-warnings 0" validate savepoints phpmd; do
    moodle-plugin-ci $s /path/to/plugin > "ci_${s%% *}.log" 2>&1
    echo "$s exit: $?"
done
```

- **Never judge a gate through a pipe or `tail`.** `cmd | tail -3` returns `tail`'s exit code, and phpcs prints
  its FILE/WARNING block above the summary footer, so the tail shows a clean-looking footer while a warning
  sits above it. Read the whole log, or use `set -o pipefail` and `${PIPESTATUS[0]}` if you must pipe.
- `phpmd` always exits 0 (moodle-plugin-ci 4.5, `src/Command/MessDetectorCommand.php`): read its log.
- `--max-warnings` exists only on `phpcs` and `phpdoc`; on another command it aborts with "option does not
  exist", which looks like findings. `grunt` takes `--max-lint-warnings` instead.
- `mustache` and `grunt` need the plugin installed inside a Moodle checkout, at its real path, as in CI;
  `mustache` on a path outside the tree exits 1 with "not within basename".
- **The `grunt` step is three linters plus a build check**: eslint over all of `amd/src` (subfolders too),
  stylelint over the plugin's CSS and SCSS, gherkinlint over `tests/behat/*.feature`, then it fails on any
  `*.js`, `*.js.map` or `*.css` the build changed ("File is stale and needs to be rebuilt")
  (`src/Command/GruntCommand.php`, moodle-plugin-ci 4.5). A local lint of `amd/src/*.js` only, or no
  gherkinlint, is a narrower gate that reads as the same one. Run:

  ```bash
  moodle-plugin-ci grunt -m /path/to/moodle --max-lint-warnings 0 /path/to/moodle/public/local/myplugin
  echo "grunt exit: $?"
  ```

- **Never trust `grunt ... --force`**: it downgrades every later failure to a warning and prints "Done, but
  with warnings". `grunt amd --force` builds and lints nothing. After a build, check that `amd/build` is newer
  than `amd/src`.
- Gherkinlint uses core's `.gherkin-lintrc` (5.2 and 5.3.0). The usual failures are indentation, trailing
  spaces and a blank line after the last step ("Multiple empty lines are not allowed"). The shape it enforces
  is owned by `moodle-behat-testing`.
- The full gate list, docblock rules moodlecheck enforces, and the standalone-tool traps are in
  [reference/ci-gates.md](moodle-skill-files/moodle-definition-of-done/reference/ci-gates.md).

## 2. Recurring review gates

- Every Mustache template has an `Example context (json):` block in its docblock.
- `$string[...]` keys in `lang/en/<component>.php` are sorted. Assert it with a script over the whole file
  after any insertion rather than choosing the insertion point by eye (recipe in the reference file).
- **A lang file edited by a script gets `php -l`.** One unescaped `'` breaks every page that loads the
  component's strings, and no other gate reads the file as PHP before phpcs runs.
- **Every string key the code uses exists.** Missing strings pass every gate. Grep static keys against the lang
  file, and load the pages that build keys dynamically (`get_string('status_' . $state, ...)`) checking that
  no `[[` placeholder appears. A template's `{{#str}}` keys are checked by rendering it in a PHPUnit test
  (`moodle-phpunit-testing`).
- `defined('MOODLE_INTERNAL') || die();` only in files with side effects (`lib.php`, `db/*.php`,
  `settings.php`, `version.php`); moodle-cs flags it in plain class files as `MoodleInternalNotNeeded`.
- No scaffolding placeholders left in file headers (`@copyright`, author, package).
- `version.php` `$plugin->requires` is not below the lowest branch in `$plugin->supported`.
- A multi-line array inside `foreach` follows phpcs's layout:

  ```php
  foreach (
      [
          'first' => 1,
          'second' => 2,
      ] as $key => $value
  ) {
  ```

## 3. Tests

- The plugin's PHPUnit tests pass; Behat features pass if the change touches UI or user-visible behaviour.
- **Confirm the plugin's tests exist and ran.** `moodle-plugin-ci phpunit` over an empty `tests/` passes, and
  PHPUnit run on a bare directory prints "No tests executed!" and exits 0. Read `Tests: N` with N above zero.
  Invocation details are owned by `moodle-phpunit-testing`.
- **"Passes with warnings" is a failing run.** Core's `phpunit.xml.dist` sets `failOnWarning="true"` and
  `failOnDeprecation="true"` (5.2 and 5.3.0), and CI adds `--fail-on-warning`. An "Unexpected debugging()
  call" in the output is a finding.
- Run Behat with `--scss-deprecations`, as the CI template does (`moodle-behat-testing`).
- Every "I should see" for one mode of a form or page has an "I should not see" for the other modes' fields
  (`moodle-behat-testing`).
- **PHPUnit green is not production.** A PHPUnit process has already loaded libraries a web request has not,
  so a missing `require_once` passes tests and dies in the browser with "Call to undefined function"
  (`moodle-phpunit-testing` has the list). Routed POST bodies, hook dispatch, draft file areas and browser
  widgets (file picker, editor, date selector) need one real request each.
- **Renames and re-scopes reach past the class.** After renaming or splitting a state key, or turning a
  constant into a setting, grep the old key or literal in `tests/` (helpers that write `$SESSION` or config
  directly) and in `amd/src` (a hard-coded limit), then drive the browser down the changed path, not just to
  its first screen.

## 4. Schema and upgrade path

- A `db/install.xml` change is paired with a `db/upgrade.php` step and a savepoint
  (`upgrade_plugin_savepoint()`, or `upgrade_mod_savepoint()` for activities), and `$plugin->version` is
  raised. An `install.xml` correction without an upgrade step is a no-op for every existing site.
- **Load the changed `install.xml` on a fresh install with developer debugging**, or run
  `moodle-plugin-ci install`, and check the output for `XMLDB has detected` and `Debugging:`. XMLDB reports a
  CHAR NOT NULL column with an empty-string default, or a TEXT column with a default, through `debugging()`
  on install (`xmldb_field::setDefault()`, `public/lib/xmldb/xmldb_field.php`, 5.2 and 5.3.0); the PHPUnit and
  Behat init output has been seen not to show it (seen in practice, cause not traced in the source). While
  writing a table, `grep -n 'DEFAULT=""' db/install.xml` must print nothing: an optional CHAR is
  `NOTNULL="false"` with no default.
- Test both paths: a fresh install and an upgrade from the previous release, on a site that has rows in the
  changed tables. Both must give the same schema.
- `moodle-plugin-ci savepoints` passes.

## 5. Course lifecycle

If the plugin stores course- or activity-linked data, check each of these, or state why it does not apply:

- **Backup and restore**: `backup/moodle2/backup_<mod>_activity_task.class.php`, `backup_<mod>_stepslib.php`
  and the restore counterparts cover every table holding course data, and a restored course behaves like the
  original. For a non-activity plugin with course-keyed tables, decide per table whether it belongs in a
  backup and write the reason in the README; a reviewer will ask.
- **Restore cleans its input.** A crafted `.mbz` is untrusted: apply the same `clean_param()` or allowlist
  logic the forms apply.
- **Course reset needs all three callbacks** for an activity module:

  ```php
  function myplugin_reset_course_form_definition(&$mform) {
      $mform->addElement('header', 'mypluginheader', get_string('modulenameplural', 'mod_myplugin'));
      $mform->addElement('advcheckbox', 'reset_myplugin_attempts', get_string('removeattempts', 'mod_myplugin'));
  }

  function myplugin_reset_course_form_defaults($course) {
      return ['reset_myplugin_attempts' => 1];
  }

  function myplugin_reset_userdata($data) {
      // Delete user data when $data->reset_myplugin_attempts is set, reset
      // gradebook entries, and return a status array for the reset report.
  }
  ```

  Core looks these up as `<modname>_reset_...`, without the `mod_` prefix (`public/course/reset_form.php`,
  5.2 and 5.3.0; `forum_reset_userdata()` in `public/mod/forum/lib.php`). With no form definition, the module is
  listed as unsupported or its option never appears, and grades stay stale.
- **Uninstall**: core's `uninstall_plugin()` deletes the plugin's tables, config, capabilities, calendar
  events, tasks, web service functions, message providers and files, but not its user preferences
  (`public/lib/adminlib.php`, `uninstall_plugin()`, 5.2 and 5.3.0). Add `db/uninstall.php` when the plugin
  stores preferences or writes outside its own tables (grade items, config of other components):

  ```php
  function xmldb_local_myplugin_uninstall() {
      global $DB;
      $like = $DB->sql_like('name', ':prefix');
      $DB->delete_records_select('user_preferences', $like,
          ['prefix' => $DB->sql_like_escape('local_myplugin_') . '%']);
      return true;
  }
  ```

- **Privacy**: every table, preference and external location declared in `get_metadata()` is handled by export
  and by all three delete paths, and a `provider_test` exercises contexts, users, export and delete on
  generated data. A declared table that is never serviced is a compliance defect; a stale table name after a
  rename throws. See `moodle-privacy-gdpr`.

## 6. Security self-review of changed sinks

For every changed entry point (form handler, external function, AJAX call, `pluginfile` callback):

- `require_login()` and `require_capability()` in the right context; the capability re-checked at
  asynchronous sinks (scheduled or adhoc tasks, deferred grade pushes), not only at request time.
- Ids and values from the client are re-validated server-side, never trusted from hidden fields.
- Any client-side limit (size, duration, count) is also enforced server-side.
- Output is escaped at the sink (`s()`, `format_string()`, `format_text()`), especially anything that reaches
  `innerHTML`.
- User-uploaded files are served with `$forcedownload = true` unless their MIME type is validated.

Before a release, run `moodle-release-preflight` for the defect classes reviews have caught, and
`moodle-security-audit` for the broad checklist.

## 7. Installed and observed on a real site

Green tests are not the finish line. Install the change on a running Moodle and observe it.

- **Installing is four steps**: copy the code into the Moodle tree (`public/local/myplugin`), run
  `php admin/cli/upgrade.php --non-interactive` and `php admin/cli/purge_caches.php` from the Moodle root (the
  CLI scripts sit beside `public/`, not inside it, in 5.2 and 5.3.0), and make the files readable by the web
  server user. Skipping the purge is the usual failure: core caches the class map in
  `$CFG->cachedir/core_component.php` (`core_component::init()`, `public/lib/classes/component.php`, 5.2 and
  5.3.0), so a new class file gives a fatal "class not found" on the site while PHPUnit is green.
- Read the stored record, the rendered notice, or what the screenshot actually shows, not the fact that the
  command returned. Look at every screenshot you save.
- Check every page you changed **in Firefox and in Chromium**. Engine differences (secure-context-only APIs,
  media and audio APIs, a promise that never settles) are invisible in one engine.
- Check role-dependent UI **as each role that sees it, admin included**. A site admin passes every
  `has_capability()` check (`public/lib/accesslib.php`, `has_capability()` with `$doanything`), so admin-only
  testing hides capability bugs, and student-only testing hides admin layout bugs.
- Check a new setting on data that already exists (an activity with its own per-item values, a second
  attempt, a course already in use), and read the values the settings form shows, not only that it saves.
- Watch values set before a bulk write (restore, import, `update_record()`) that can silently overwrite them.
- Check the web server log for PHP warnings and `Debugging:` output from the pages you touched, with developer
  debugging on.
- A form-decorating or page-altering plugin is also checked on a Moodle with only standard plugins; another
  installed plugin can supply what yours forgot.
- Do not check filter or `format_text()` output while "logged in as" another user: core forces cleaning for the
  whole session (`$CFG->forceclean`, set in `require_login()`, `public/lib/moodlelib.php`, 5.3.0). See
  `moodle-field-lessons`.
- **CSS has two levels of evidence.** Finding the rule in the served stylesheet proves it arrived; only a
  screenshot or `getComputedStyle()` proves it applies, because the theme's and Bootstrap's rules can win. The
  first stylesheet request after a purge is answered with the previous CSS while the new one is built
  (`public/theme/styles.php`, themes with `$THEME->usefallback`, which Boost sets): reload before judging.
  Commands in [reference/site-verification.md](moodle-skill-files/moodle-definition-of-done/reference/site-verification.md).

## 8. Release notes and docs

- `README.md` still describes current behaviour, settings and requirements.
- The changelog records user-visible changes in the format the plugin already uses.
- Any user manual or help page naming a changed, renamed or removed setting, field or page is updated. A
  removal is the dangerous case: the doc becomes actively wrong rather than incomplete.
- Documentation and READMEs never contain literal course or module ids (`course/view.php?id=42`): they differ on
  every site. Say how to find the page instead.
- `$plugin->release` is changed only as part of a deliberate release (`moodle-plugin-release`), and
  `composer.json` (if present) is still valid.

## 9. Clean working state

- Every background process you started (Behat, a PHP built-in server, chromedriver, watchers) is stopped and
  its port is free. Stop processes by exact PID after reading their command line; `pkill -f <pattern>` also
  matches the shell running it.
- The diff contains only intended files: no build output, logs, `node_modules/`, or hand edits to `amd/build/`
  or `thirdparty/` code.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Reporting "clean" from a gate that printed nothing | Real errors ship; CI fails later | Prove the gate fires on a known-bad input |
| `phpcs ... \| tail -3` | Footer looks clean; the warning above it is unseen | Log to a file, read it all, check `$?` directly |
| Linting `amd/src/*.js` locally, no gherkinlint | CI's `grunt` fails on subfolders or a `.feature` file | `moodle-plugin-ci grunt --max-lint-warnings 0` |
| `grunt --force` treated as success | Lint errors hidden as warnings | Run `moodle-plugin-ci grunt` and read its exit code |
| Empty `tests/` or a bare-directory PHPUnit run | "No tests executed!", exit 0 | Read `Tests: N` with N > 0 |
| "Passes with warnings" | CI fails: `failOnWarning` | Fix the warning |
| Lang file edited by script, not linted | Every page of the component breaks | `php -l` the file |
| `install.xml` changed without an upgrade step | Upgraded sites differ from fresh installs | `upgrade.php` step plus savepoint |
| `DEFAULT=""` on a CHAR column | `debugging()` on fresh install; `moodle-plugin-ci install` can abort | `NOTNULL="false"`, no default |
| Only `*_reset_userdata` implemented | Reset option never shown; grades stale | All three reset callbacks |
| No `db/uninstall.php` for stored preferences | Preferences left behind after uninstall | Delete them in `xmldb_<component>_uninstall()` |
| New class deployed without a purge | "Class not found" on the site, tests green | `purge_caches.php` after every install |
| Checked only as admin, only in one browser | Capability and engine bugs reach users | Each role; Firefox and Chromium |
| CSS rule found in the served sheet, called done | Rule loses to the theme; nothing changes | Screenshot or `getComputedStyle()` |
| "The script didn't throw" treated as success | Setting not saved, record not deleted | Read back the effect |
| A count quoted from memory | Report contradicts the run | Quote the run's own output |

## Reference files

| File | Read it when |
|---|---|
| [reference/ci-gates.md](moodle-skill-files/moodle-definition-of-done/reference/ci-gates.md) | A `moodle-plugin-ci` step fails or prints nothing you can interpret, you need the moodlecheck docblock rules, the lang-sorting check, or the standalone moodlecheck CLI, or you are writing a local script that stands in for a CI step |
| [reference/site-verification.md](moodle-skill-files/moodle-definition-of-done/reference/site-verification.md) | You are about to verify a change on a running site: install steps, browser checks across engines and roles, success markers, `#fragment` navigation, or proving a CSS change arrived and applies |

## References

- https://moodledev.io/general/development/tools/phpcs
- https://moodledev.io/general/development/policies/codingstyle
- https://moodledev.io/general/development/tools/behat
- https://moodledev.io/general/development/tools/phpunit
- https://moodledev.io/docs/guides/upgrade
- https://moodledev.io/docs/apis/subsystems/backup
- https://moodledev.io/docs/apis/subsystems/privacy
- https://moodledev.io/docs/apis/plugintypes/mod
- https://moodlehq.github.io/moodle-plugin-ci/


---

### moodle-field-lessons

> Use when scanning a Moodle plugin change across topics for the non-obvious pitfalls that pass phpcs, PHPUnit and CI but break on a real site, or when a symptom fits no single topic skill - a short-rule index by topic: supported ranges and cross-branch guards, functions or classes missing outside PHPUnit, client-supplied ids, html_writer and format_string escaping, noclean under "Log in as", DB and XMLDB small print, backup/restore/reset date shifts across DST, privacy drift, lang placeholders and [[key]], moodleform/dynamic_form/file picker traps, admin settings defaults, the question engine outside mod_quiz, availability conditions, core AI calls, modal and TinyMCE gotchas, navigation and course-page content, and CI false greens. Skip when the task sits inside one topic and you need its recipe, checklist or error message explained (that topic's skill, such as moodle-plugin-development or moodle-security-audit), before a release (moodle-release-preflight), or for a theme (the moodle-theme-* skills).

# Moodle field lessons

## Overview

Rules distilled from defects that shipped, or nearly shipped, in real Moodle plugins despite green phpcs, PHPUnit
and CI. This file is the index: the expensive mistakes, the cross-cutting rules, and one headline per topic with
the reference file that holds the rest. Every rule holds on Moodle 5.2 and 5.3 unless it is tagged.

## When to Use

- Writing or changing `version.php`, `db/*.php`, `install.xml`, external functions, restore steps, forms or settings
- Reviewing a diff for what linters and unit tests cannot see
- Designing tests, especially security regression tests and date or timezone assertions
- Supporting several Moodle branches from one code line
- **Skip when:** you need the full recipe or checklist for one topic: `moodle-plugin-development` (plugin
  structure), `moodle-security-audit` (security review), `moodle-release-preflight` (before a release or an external
  review), `moodle-definition-of-done` (before calling a task finished), `moodle-phpunit-testing`,
  `moodle-behat-testing`, `moodle-ci-matrix`, `moodle-5-3-changes`, and the `moodle-theme-*` skills for themes

## The most expensive mistakes

1. **Trusting the green suite.** PHPUnit cannot see services or tasks that never registered, free functions its
   bootstrap preloads, routed POST bodies, hook dispatch on module pages, backup element collisions, or real form
   POSTs. Every such change needs one real HTTP request.
2. **Calling an API that changed inside the supported range.** Your local site is one row of the CI matrix. Guard
   the call or use the name every branch has.
3. **Changing `db/services.php` or `db/tasks.php` without a version bump.** The upgrade prints "No upgrade needed";
   nothing is registered.
4. **Authorising against a client-supplied id**, or checking capability at request time and not at the async sink.
5. **Two actors writing the same state value** to one column, so the lower-privileged one can undo the
   higher-privileged one's decision.
6. **Unescaped `html_writer::tag()` contents** and unclean restore or import input.
7. **A security test never seen failing.** It passes against vulnerable code when the fixture misses the column the
   renderer reads.
8. **DDL or payloads from a standalone CLI script**: a script that requires `config.php` writes to the live
   database.
9. **Fixed-seconds date shifts across DST** in restore and reset for wall-clock data.
10. **Hand-computed expected timestamps** in tests, then "fixing" correct code to match them.

## Versioning and cross-branch support

- **`$plugin->supported` is an inclusive `[low, high]` pair**, even for one branch: `[502, 502]`, never `[502]`. A
  malformed value makes core throw `coding_exception('Incorrect syntax in plugin supported declaration')` whenever
  it loads plugin information (`public/lib/classes/plugininfo/base.php:311-320`, 5.2 and 5.3); some third-party
  tooling silently falls back to `requires` instead. Keep `requires` at or above the lowest branch.

  ```php
  $plugin->requires = 2026042000; // 5.2.
  $plugin->supported = [502, 503];
  ```

- **Guard every core API that changed inside your range** with `method_exists()` or `class_exists()`. An old API
  emits a deprecation notice that `--fail-on-warning` CI rejects on the newer branch; a new one fatals ("Call to
  undefined method") on the older one. Grep each branch's source for the symbol and its `#[\core\attribute\deprecated]`
  attribute, and read the newer branch's `UPGRADING.md`.

  ```php
  if (method_exists(\core\user::class, 'create_user')) {
      $userid = \core\user::create_user($user);       // 5.3+.
  } else {
      require_once($CFG->dirroot . '/user/lib.php');
      $userid = user_create_user($user);              // 5.2; deprecated on 5.3.
  }
  ```

- **A return value is part of the contract too.** Before branching on what a core call returns, check it on the
  lowest and highest branch. **5.3+:** `\core\task\manager::queue_adhoc_task($task, true)` returns the id of the
  existing task where 5.2 returned false (`UPGRADING.md` at the 5.3.0 root), so a "was it queued?" check inverts.
- **Use the replacement API the lowest branch already has.** On 5.2 `course_delete_module()`,
  `duplicate_module()` and `moveto_module()` are deprecated for `\core_courseformat\local\cmactions`
  (`delete()`, `duplicate()`, `move_before()`, `move_end_section()`), which exists on 5.2 and 5.3
  (`public/course/format/classes/local/cmactions.php`), so no guard is needed; Behat fails on the old calls'
  debugging.
- **When core namespaces a global class** and keeps a `class_alias`, keep using the name the lowest supported branch
  has. A `use` of a name that only the newer branch defines breaks every page on the older one.
- **Raise `$plugin->dependencies`** from `ANY_VERSION` to the dependency's `$plugin->version` in the same commit that
  starts calling a newer symbol from it. `ANY_VERSION` proves only that the plugin is installed.
- **Keep `version` and `release` separate.** Schema, services, tasks, capabilities, caches and messages changes
  bump the numeric `version`; the semantic `release` changes only in a deliberate release with notes and a tag
  (`moodle-plugin-release`).
- **The `public/` layout (5.1+, so 5.2 and 5.3):** core admin CLI stays at `<root>/admin/cli/`; plugin code,
  including `admin/tool/phpunit` and `admin/tool/behat`, is under `<root>/public/`. Do not add `public/` to core CLI
  paths by analogy, and grep `public/lib/`, not `lib/`, for core library code.

## Registration that only happens on upgrade

- **`db/services.php`, `db/tasks.php`, `db/access.php`, `db/messages.php` and `db/caches.php` are re-read only when
  the plugin's numeric version changed** (`upgrade_component_updated()`, and `cache_helper::update_definitions()`
  for caches, both in `public/lib/upgradelib.php`, read in 5.3.0).
  Without a bump `admin/cli/upgrade.php` says "No upgrade needed", AJAX calls fail (`invalidrecordunknown`) or the
  task never exists, and unit tests calling the class directly stay green. Verify the effect, not the upgrade
  output:

  ```php
  $info = \core_external\external_api::external_function_info('local_myplugin_do_thing', IGNORE_MISSING);
  ```

  ```bash
  php admin/cli/scheduled_task.php --list | grep local_myplugin
  ```

- **PHPUnit init is a no-op** while the site-wide versions hash is unchanged: a table added to `install.xml` or a
  changed setting default without a version bump never reaches the test database. Rebuild with
  `php public/admin/tool/phpunit/cli/util.php --drop` then `init.php`. "Initialised for different version" means
  some component changed on disk, not that yours is broken.
- **New admin settings are stored with their defaults only by an upgrade**: added without a bump, `get_config()`
  returns false and the settings form shows the first choice of a select beside "Default: ...".
- **`$CFG->routerconfigured = true`** must be set in `config.php` above the `require_once` of `lib/setup.php`;
  setup normalises it early (`public/lib/setup.php:201`, 5.3.0).

## Web services and routed controllers

The first three rules are owned by `moodle-web-services`, which has the samples and sources.

- **`'loginrequired' => false` functions must not call `self::validate_context()`**: it ends in `require_login()`
  and refuses anonymous callers; call `$PAGE->set_context()` instead.
- **Match the gate of the page the function backs**: a course context check enforces enrolment, so an unenrolled
  owner gets `requireloginerror`.
- **`validate_parameters()` rejects free text that `PARAM_TEXT` cleaning would change**: declare it `PARAM_RAW` and
  escape at the sink.
- **Routing Engine controllers without a `requestbody` schema** get `$request->getParsedBody() === []` on a
  site: the request validator clears the body (`public/lib/classes/router/request_validator.php`,
  `validate_request_body()`, 5.2 and 5.3). Declare the schema, or read POST data with `optional_param()` plus
  `require_sesskey()`. A page route added to `route_testcase` with the group path `''` gets no validation
  middleware (`\core\router::configure_routes()` attaches it by group name, `public/lib/classes/router.php`,
  5.3.0), so the test sees the posted body; verify with a real HTTP POST.

## Authorisation and state

- **Never authorise against a client-supplied id.** Derive course, context and instance from the URL or context;
  re-validate each submitted id against the set you offered; re-check capability at async sinks (tasks, grade
  pushes); enforce size and duration limits server-side; do not ship answer or grading metadata to the browser.

  ```php
  $accountid = required_param('accountid', PARAM_INT);
  if (!array_key_exists($accountid, $offeredaccounts)) {
      throw new \moodle_exception('invalidaccount', 'mod_myplugin');
  }
  ```

- **One permission helper guarding several actions** is a smell: check that each action wants that gate. Test actor,
  control, resulting state, and assert that a lower-privileged subject cannot reverse a state a higher one set.
- **Grep every writer of a status column**, not only its readers, before reusing a value. Never let two actors of
  different privilege write the same value; give each a distinct state or record the actor on the row.
- **Enumerate all entry points mechanically before an access audit** (every top-level and `admin/**` PHP file, every
  external function): `grep -rlE 'require_login|require_course_login' --include='*.php' .` Sibling controllers gated
  only by `require_login()` are where exports leak (`moodle-security-audit`).
- **Serve uploads with force-download** unless the MIME type is validated audio or video; allowlist type and
  extension on upload; escape at output.
- **`db/access.php`: `clonepermissionsfrom` overrides `archetypes`** and copies the source capability's real grants.
  Fixing `access.php` later does not re-derive grants on existing sites; check `{role_capabilities}`.
- **Account-linking and token callbacks need a session-bound, single-use `state`** issued before the redirect, or
  they allow login CSRF.
- **Test system-context gates with a separate account or "Log in as"**, never "Switch role to", which works in course
  contexts only.
- **Inspect uploaded plugin ZIPs with core** (`\core\update\validator`, `\core\update\code_manager::unzip_plugin_file()`);
  never `include` an untrusted `version.php`: tokenise it with `token_get_all()` for the fields core's parser skips
  (`supported`, `dependencies`).
- **Probe a suspected traversal or XXE before filing it.** Core's zip extractor strips `../`; a flag-less
  `simplexml_load_file()` is XXE-safe on PHP 8 with libxml 2.9 or later unless `LIBXML_NOENT` or `LIBXML_DTDLOAD` is
  passed.

## Output escaping essentials

- **`html_writer::tag()`, `link()` and `select()` escape attributes, not contents**: `s()` at the sink. formslib
  labels and select option texts are printed unescaped too.
- **`format_string()` strips tags where `s()` escapes them**, and its behaviour depends on a site setting, so it is
  not an XSS argument on its own. `fullname()` and `get_string()` escape nothing.
- **Content written into core tables is rendered by core, often `noclean`**: clean every imported field and clamp
  `FORMAT_MARKDOWN`.
- **"Log in as" sets `$CFG->forceclean`** for the session (MDL-63786), so `noclean` is ignored and `data-*`
  attributes are stripped before filters run.
- **In block classes use `$this->page`, never `global $PAGE`** (moodle-cs `moodle.PHP.ForbiddenGlobalUse.BadGlobal`
  fails CI).

Modal and notification sinks, JSON in attributes, plain-text sinks, multilang and every lang string rule:
[reference/output-and-lang-strings.md](moodle-skill-files/moodle-field-lessons/reference/output-and-lang-strings.md).

## The other topics, one headline each

**DB and stored data** ([reference/db-and-data.md](moodle-skill-files/moodle-field-lessons/reference/db-and-data.md)): `update_record()` writes every
property (use `set_field()` near counters); `get_records()` keys by the first field and ignores a seventh argument;
never `CHAR NOTNULL="true" DEFAULT=""`; on PostgreSQL nothing may touch the database between a failed query and the
rollback; order same-request rows by `id`.

**Course lifecycle** ([reference/course-lifecycle.md](moodle-skill-files/moodle-field-lessons/reference/course-lifecycle.md)): plan backup, the reset triad
and `db/uninstall.php` for every data-storing plugin; restore input is attacker input; restore and reset shift dates
by fixed seconds across DST; `add_related_files(..., 'user')` restores nothing for a user-keyed file area.

**Activities, grades, questions, availability**
([reference/activities-and-questions.md](moodle-skill-files/moodle-field-lessons/reference/activities-and-questions.md)): use `$data->coursemodule` in
`add_instance()`; `create_module()` needs `introeditor`; `process_all_actions()` without `slots` grades every slot the
client names; `get_gradable_users()` throws while a regrade is pending; single availability conditions need an
`info` subclass.

**Forms and settings** ([reference/forms-and-settings.md](moodle-skill-files/moodle-field-lessons/reference/forms-and-settings.md)): read submit buttons with
`PARAM_RAW`; `hideIf()` also disables, so hidden fields are not posted; `confirm_sesskey()` with no argument throws;
`validation()` must not call `get_file_content()`; `admin_setting_filetypes` needs a `lang_string` label.

**JavaScript and UI** ([reference/javascript-and-ui.md](moodle-skill-files/moodle-field-lessons/reference/javascript-and-ui.md)): no `.finally()` on
`core/ajax` promises; `export default` drops named exports in the AMD build; `ModalEvents.destroyed` on the root never
fires; Bootstrap 5 names only; a module page's secondary navigation is extended through `extend_settings_navigation`.

**Testing and CI** ([reference/testing-blind-spots.md](moodle-skill-files/moodle-field-lessons/reference/testing-blind-spots.md)): `assign_capability()`
does not overwrite; `CLI_SCRIPT` is true under PHPUnit; a security test counts only after it was seen failing;
`I navigate to ... in site administration` does not fail on an ambiguous path; empty `tests/` passes CI.

**Core API and core AI** ([reference/core-api-small-print.md](moodle-skill-files/moodle-field-lessons/reference/core-api-small-print.md)):
`user_create_user($u, false)` stores the password verbatim; `empty($PAGE->cm)` is always true; `end()` throws on a
`readonly` array; `process_action()` can throw `\InvalidArgumentException`.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `$plugin->supported = [502];` | Core throws `coding_exception`; some tooling falls back to `requires` | `[502, 502]` |
| `db/services.php` edit, no version bump | Function never registered; "No upgrade needed" | Bump `version`, check `external_function_info()` |
| Branching on `queue_adhoc_task()`'s return across 5.2 and 5.3 | Logic inverts on one branch | Do not depend on the return value |
| `validate_context()` in a `loginrequired => false` function | Anonymous callers refused | `$PAGE->set_context()` |
| `html_writer::tag('td', $name)` | Stored XSS | `s($name)` |
| `get_coursemodule_from_instance()` in `add_instance()` | "Can't find data record", creation rolled back | `$data->coursemodule` |
| Shared "hidden" state for author and moderator | Moderation bypass | Distinct states, or record the actor |
| `.finally()` on a `core/ajax` promise | Works once, then the control stays disabled | `Promise.resolve(...)` wrapper |
| `PARAM_INT` on a submit button | Action silently does nothing | `PARAM_RAW`, test `!== ''` |
| `empty($PAGE->cm)` | Always true, even in an activity | Read into a variable first |
| `$format === 1` | Always false (`FORMAT_*` are strings) | Compare with `FORMAT_HTML` |
| `get_string('x', 'y', null, 'fr')` | Fourth argument is `$lazyload`; language ignored | `get_string_manager()->get_string(..., 'fr')` |
| `admin_setting_filetypes` with a `get_string()` label | Settings page fatal: `out()` on string | `new lang_string(...)` |
| `process_all_actions()` with client post data | Every named slot is graded | Filter to the slot's prefix, pass `slots` |
| `tar -czf` for a tampered `.mbz` | Negative test passes for the wrong reason | Core's backup packer |
| Restore date offset applied as seconds to wall-clock data | 09:00 becomes 08:00 after a DST change | Round to days, shift in the timezone |
| Expected timestamps computed by hand | Correct code "fixed" to match a wrong test | Derive with an independent tool |
| `catch (\moodle_exception)` around `process_action()` | `\InvalidArgumentException` escapes | `catch (\Exception)` |

## Reference files

| File | Read it when |
|---|---|
| [reference/output-and-lang-strings.md](moodle-skill-files/moodle-field-lessons/reference/output-and-lang-strings.md) | choosing how to escape a value at a sink, showing imported or stored HTML, a filter or `noclean` behaves differently for some users, or a lang string renders wrongly (`{$a->x}` in the text, `[[key]]`, wrong language) |
| [reference/db-and-data.md](moodle-skill-files/moodle-field-lessons/reference/db-and-data.md) | writing `$DB` queries, changing `install.xml` or `upgrade.php`, adding a column beside an existing value, writing a CLI script that touches the database, or a query fails only on PostgreSQL |
| [reference/course-lifecycle.md](moodle-skill-files/moodle-field-lessons/reference/course-lifecycle.md) | writing or reviewing backup, restore, course reset, uninstall or the privacy provider, or stored dates move after a restore or reset |
| [reference/activities-and-questions.md](moodle-skill-files/moodle-field-lessons/reference/activities-and-questions.md) | writing an activity module's callbacks or completion rules, creating modules or grades from code, using the question engine outside `mod_quiz`, or writing an availability condition |
| [reference/forms-and-settings.md](moodle-skill-files/moodle-field-lessons/reference/forms-and-settings.md) | writing a moodleform, `dynamic_form`, file or filemanager element, a form posted or built from code, or an admin setting whose stored or shown value is wrong |
| [reference/javascript-and-ui.md](moodle-skill-files/moodle-field-lessons/reference/javascript-and-ui.md) | plugin JS works once then stops, a modal or TinyMCE button misbehaves, plugin CSS does not apply, or you add to navigation, the course page, a block region or a Moodle app site plugin |
| [reference/testing-blind-spots.md](moodle-skill-files/moodle-field-lessons/reference/testing-blind-spots.md) | a test passes but the site fails, writing a security regression test or a DST assertion, driving Moodle with Behat or a browser automation tool, or a green CI run may have checked nothing |
| [reference/core-api-small-print.md](moodle-skill-files/moodle-field-lessons/reference/core-api-small-print.md) | a core function surprises you (users, tokens, enrolment, tables, page properties), PHP behaves oddly inside Moodle code, or the plugin calls core AI |

## References

- Moodle developer docs: [version.php](https://moodledev.io/docs/apis/commonfiles/version.php),
  [web services](https://moodledev.io/docs/apis/subsystems/external), [routing](https://moodledev.io/docs/apis/subsystems/routing),
  [output](https://moodledev.io/docs/apis/subsystems/output), [DML](https://moodledev.io/docs/apis/core/dml),
  [backup](https://moodledev.io/docs/apis/subsystems/backup), [privacy](https://moodledev.io/docs/apis/subsystems/privacy),
  [access](https://moodledev.io/docs/apis/subsystems/access), [forms](https://moodledev.io/docs/apis/subsystems/form),
  [AI](https://moodledev.io/docs/apis/subsystems/ai)
- Upgrade notes for each branch: `UPGRADING.md` at the root of the Moodle tree


---

### moodle-hooks-api

> Use when a plugin listens to or dispatches a Moodle hook — db/hooks.php, \core\hook\manager, \core\di, hook classes under classes/hook/, replacing lib.php callbacks such as before_http_headers, before_footer, before_standard_html_head, before_standard_top_of_body_html, add_htmlattributes, after_config or bulk_user_actions, the debugging message "Callback ... should be migrated to new hook callback", extend_user_menu, primary_extend, secondary_extend, or testing hook callbacks with phpunit_get_instance. Skip when reacting to a logged fact with \core\event observers (moodle-plugin-development), or when choosing where a theme puts page markup (moodle-theme-renderers-output).

# Moodle Hooks API

## Overview

A hook is a plain PHP object that core (or a plugin) creates, hands to `\core\hook\manager::dispatch()`, and then
reads back. Callbacks registered in each component's `db/hooks.php` receive that object and change it: add HTML,
add attributes, add a menu item, stop propagation. The API is PSR-14 underneath and is the same on Moodle 5.2 and
5.3 apart from the hooks listed in the version notes (`public/lib/classes/hook/manager.php` is byte-identical in
both, read in the 5.2 and 5.3.0 source).

## When to Use

- A plugin must add something to every page (head HTML, top of body, footer, `<html>` attributes, HTTP headers)
- Replacing a `lib.php` callback that core now reports as "should be migrated to new hook callback"
- Reacting to a core action that has a hook (course created or deleted, user enrolled, group changed, file
  created, quiz structure changed) and needing to change the outcome, not only log it
- Writing a hook in your own plugin so other plugins can extend it
- Testing a hook callback in PHPUnit
- **Skip when:** you only need to react to something that already happened and was logged (an event observer in
  `db/events.php`, see `moodle-plugin-development`), or you are choosing which hook a theme uses for page output
  (`moodle-theme-renderers-output`).

Hooks versus events: an event is a record of a fact, delivered after the transaction, and an observer cannot change
the outcome. A hook runs inline, and the dispatcher reads what callbacks put into it.

## How a dispatch works

1. Core builds the hook object, for example `new before_footer_html_generation($renderer)`.
2. For hooks that replace a legacy callback, core calls `$hook->process_legacy_callbacks()` first, which calls the
   old `lib.php` functions of plugins that have not registered the hook.
3. `\core\di::get(\core\hook\manager::class)->dispatch($hook)` calls each registered callback in priority order
   (highest first, default 100). If the hook implements `\Psr\EventDispatcher\StoppableEventInterface`, the
   manager checks `isPropagationStopped()` before each callback.
4. Core reads the result (`$hook->get_output()`, `get_attributes()` and so on).

Source: `public/lib/classes/output/core_renderer.php` (`htmlattributes()`, `standard_head_html()`) and
`public/lib/classes/hook/manager.php` (`dispatch()`, `prioritise_callbacks()`), 5.3.0.

## Listening to a core hook (the default recipe)

`db/hooks.php`:

```php
<?php
// (GPL header)
defined('MOODLE_INTERNAL') || die();

$callbacks = [
    [
        'hook' => \core\hook\output\before_footer_html_generation::class,
        'callback' => [\local_example\hook_callbacks::class, 'before_footer'],
        'priority' => 100,
    ],
];
```

`classes/hook_callbacks.php`:

```php
<?php
// (GPL header)
namespace local_example;

use core\hook\output\before_footer_html_generation;

/**
 * Hook callbacks for local_example.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
final class hook_callbacks {
    /**
     * Add the help banner to the footer.
     *
     * @param before_footer_html_generation $hook
     */
    public static function before_footer(before_footer_html_generation $hook): void {
        if (during_initial_install() || !isloggedin() || isguestuser()) {
            return;
        }
        $hook->add_html($hook->renderer->render_from_template('local_example/banner', []));
    }
}
```

Then purge caches (`php admin/cli/purge_caches.php` from the Moodle root) or bump `$plugin->version`; the upgrade
purges too.

Rules the manager enforces (`manager.php` `normalise_callback()`, `is_callback_valid()`, 5.3.0):

- **The callback must be a static method.** A non-static method is skipped with the debugging message "Callback
  method not a static method", so the hook silently does nothing on a site without developer debugging. Write
  `public static function`.
- `callback` is either `[Class::class, 'method']` or the string `'\local_example\hook_callbacks::method'`. A
  closure or a plain function name is rejected with debugging and ignored.
- `hook` is the class name as a string. A class that does not exist is not an error: the entry is stored under that
  name and never dispatched (`add_component_callbacks()`). This is what lets one `db/hooks.php` register a 5.3-only
  hook and still install on 5.2.
- `priority` is an integer; higher runs first; equal priorities have no guaranteed order.

## Migrating a lib.php callback

Core marks a legacy callback as replaced with `#[\core\attribute\hook\replaces_callbacks('before_footer')]` on the
hook class (or the older `deprecated_callback_replacement` interface). Two behaviours follow, both in
`public/lib/moodlelib.php` (`get_plugins_with_function()`, `component_callback()`), 5.2 and 5.3.0:

- A plugin that still has only the old function gets it called, plus the developer debugging "Callback
  before_footer in local_example component should be migrated to new hook callback for ...". Behat fails the step
  that reaches it. PHPUnit prints "Unexpected debugging() call detected" as a notice and the run still passes
  (core's `phpunit.xml.dist` fails on warnings and deprecations, not on notices; read in 5.2 and 5.3.0, not run), so
  read the output of a green run (`moodle-phpunit-testing`).
- A plugin that has both the old function and a `db/hooks.php` entry for the replacing hook gets only the hook
  called. So keeping the old function costs nothing while you still support a branch without the hook.

| Legacy `lib.php` callback | Hook (all exist on 5.2 and 5.3) |
|---|---|
| `<component>_before_http_headers()` | `\core\hook\output\before_http_headers` |
| `<component>_before_standard_html_head()` | `\core\hook\output\before_standard_head_html_generation` |
| `<component>_before_standard_top_of_body_html()` | `\core\hook\output\before_standard_top_of_body_html_generation` |
| `<component>_add_htmlattributes()` | `\core\hook\output\before_html_attributes` |
| `<component>_before_footer()` | `\core\hook\output\before_footer_html_generation` |
| `<component>_standard_footer_html()` | `\core\hook\output\before_standard_footer_html_generation` |
| `<component>_standard_after_main_region_html()` | `\core\hook\output\after_standard_main_region_html_generation` |
| `<component>_after_config()` | `\core\hook\after_config` |
| `<component>_bulk_user_actions()` | `\core_user\hook\extend_bulk_user_actions` |
| `<component>_before_file_created()`, `_after_file_created()` | `\core_files\hook\before_file_created`, `after_file_created` |
| `quiz_structure_modified` / `quiz_attempt_deleted` callback classes | `\mod_quiz\hook\structure_modified`, `attempt_state_changed` |

Source: `replaces_callbacks` attributes under `public/lib/classes/hook/`, `public/files/classes/hook/`,
`public/mod/quiz/classes/hook/` and `get_deprecated_plugin_callbacks()` in
`public/user/classes/hook/extend_bulk_user_actions.php`, read in 5.2 and 5.3.0.

These are still ordinary `lib.php` callbacks with no hook on 5.2 or 5.3, so do not look for one:
`extend_navigation()`, `extend_navigation_course()`, `extend_navigation_user()`, `extend_navigation_frontpage()`,
`extend_settings_navigation()`, `extend_navigation_user_settings()`, `extend_navigation_category_settings()`,
`myprofile_navigation()`, `after_require_login()`, `before_session_start()`, `pre_course_delete()`,
`pre_user_delete()`, `coursemodule_standard_elements()`, `coursemodule_edit_post_actions()`,
`control_view_profile()`, `render_navbar_output()`, `pluginfile()`, `output_fragment_*()`, `get_fontawesome_icon_map()`
(from the `get_plugins_with_function()` and `component_callback()` calls in the 5.3.0 source).
`\core\hook\navigation\primary_extend` and `secondary_extend` exist but replace nothing: they give
`get_primaryview()` / `get_secondaryview()` for adding nodes to those views.

Migration steps:

1. `grep -nE "function [a-z]+_[a-z0-9]+_(before_http_headers|before_standard_html_head|before_standard_top_of_body_html|add_htmlattributes|before_footer|standard_footer_html|standard_after_main_region_html|after_config|bulk_user_actions|before_file_created|after_file_created)\(" lib.php`
2. Move each body into a static method of `classes/hook_callbacks.php`; a legacy callback that returned a string
   now calls `$hook->add_html($html)`; `add_htmlattributes()` that returned an array calls
   `$hook->add_attribute($name, $value)` per pair.
3. Register each in `db/hooks.php`.
4. Delete the old function once every branch you support has the hook (all of the table above exist on 5.2), or
   keep it as the fallback for older branches; core will not call both.
5. Purge caches and run with `DEBUG_DEVELOPER`; the "should be migrated" message must be gone.

## Writing your own hook

Put the class in your component's `hook` namespace (`classes/hook/`), which is how the Hooks overview page and
`\core\hooks::discover_hooks()` find it (`public/lib/classes/hooks.php`, 5.3.0):

```php
<?php
// (GPL header)
namespace local_example\hook;

/**
 * Lets other plugins add actions to the widget toolbar or stop it rendering.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
#[\core\attribute\label('Allows plugins to add actions to the widget toolbar')]
#[\core\attribute\tags('widget', 'output')]
final class before_widget_toolbar implements \Psr\EventDispatcher\StoppableEventInterface {
    use \core\hook\stoppable_trait;

    /** @var array<string, string> action name => HTML */
    private array $actions = [];

    /**
     * Constructor.
     *
     * @param \context $context The widget context.
     * @param int $widgetid The widget id.
     */
    public function __construct(
        /** @var \context The widget context */
        public readonly \context $context,
        /** @var int The widget id */
        public readonly int $widgetid,
    ) {
    }

    /**
     * Add an action.
     *
     * @param string $name
     * @param string $html
     */
    public function add_action(string $name, string $html): void {
        $this->actions[$name] = $html;
    }

    /**
     * Get the actions added by callbacks.
     *
     * @return array<string, string>
     */
    public function get_actions(): array {
        return $this->actions;
    }
}
```

Dispatch it and read it back:

```php
$hook = new \local_example\hook\before_widget_toolbar($context, $widget->id);
\core\di::get(\core\hook\manager::class)->dispatch($hook);
if ($hook->isPropagationStopped()) {
    return '';
}
$actions = $hook->get_actions();
```

- Description: either the two attributes above or `implements \core\hook\described_hook` with static
  `get_hook_description()` and `get_hook_tags()`. Both feed Site administration > Development > Hooks overview
  (`/admin/hooks.php`).
- Stopping: `stoppable_trait` gives `stop_propagation()` and `isPropagationStopped()`. There is no
  `\core\hook\stoppable_event_interface`; implement the PSR interface. Only make a hook stoppable when a veto means
  something.
- Keep inputs `readonly` and give callbacks narrow methods (`add_action()`), so a callback cannot rewrite what
  other callbacks added. Once released, the hook class, its constructor and its methods are a public API under the
  deprecation policy (https://moodledev.io/general/development/policies/deprecation).
- If your hook replaces a callback of your own, add `#[\core\attribute\hook\replaces_callbacks('mycallback')]` and a
  `process_legacy_callbacks()` method that calls `get_plugins_with_function(function: 'mycallback',
  migratedtohook: true)`, and call it before `dispatch()`, as the core output hooks do.
- `dispatch()` before `setup.php` has finished only logs "Hooks cannot be dispatched yet" and returns the hook
  unchanged.

## Testing hook callbacks

Hook callbacks are not cached in PHPUnit (`should_cache()` returns false), so a callback in `db/hooks.php` runs in
tests exactly as on the site. Two ways to test:

```php
// 1. Call the callback directly with a real hook object: tests the callback alone.
$page = new \moodle_page();
$renderer = $page->get_renderer('core');
$hook = new \core\hook\output\before_footer_html_generation($renderer);
\local_example\hook_callbacks::before_footer($hook);
$this->assertStringContainsString('local_example-banner', $hook->get_output());

// 2. Dispatch through the real manager: also proves db/hooks.php is right.
\core\di::get(\core\hook\manager::class)->dispatch($hook);
```

To test code that dispatches your own hook with a known set of callbacks, replace the manager:

```php
\core\di::set(
    \core\hook\manager::class,
    \core\hook\manager::phpunit_get_instance([
        'local_example' => __DIR__ . '/fixtures/hooks.php',
    ]),
);
```

or redirect one hook to a closure with
`\core\di::get(\core\hook\manager::class)->phpunit_redirect_hook(hookclass::class, fn($hook) => ...)` and undo it
with `phpunit_stop_redirections()` (`manager.php`; core example `public/lib/tests/core_renderer_test.php`, 5.3.0).
Cover both branches: the callback acts, and the callback returns early (guest, wrong page, feature off).

## Traps

- **An exception thrown from an `after_config` callback never reaches the browser with your status code.** The
  page is answered `500 Internal Server Error` by the bootstrap renderer, or `404 Not Found` by
  `core_renderer::fatal_error()` when output has not started, whatever `http_response_code()` you set first
  (`public/lib/classes/output/bootstrap_renderer.php` `early_error()`, `core_renderer.php` `fatal_error()`, read in
  5.3.0, not run). The same holds for an `after_require_login()` callback. To refuse with a real 403, send it and stop:

  ```php
  public static function after_config(\core\hook\after_config $hook): void {
      if (during_initial_install() || CLI_SCRIPT || !self::must_refuse()) {
          return;
      }
      if (PHPUNIT_TEST) {
          throw new \moodle_exception('accessdenied', 'admin');
      }
      http_response_code(403);
      echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>403</title></head><body><p>' .
          s(get_string('accessdenied', 'admin')) . '</p></body></html>';
      exit;
  }
  ```

- **`after_config` runs on every request**, including CLI scripts, cron, web services and the upgrade itself.
  Return early unless the request is one you mean to change; database reads there cost on every hit.
- **A hook callback in a plugin runs site-wide**, including on pages of other plugins and, for a theme's callbacks,
  under other themes. Gate on the page (`$PAGE->url`, a capability, `$PAGE->theme->name`), not on the assumption
  that you are only called where you wanted. Theme-specific gating: `moodle-theme-renderers-output`.
- **`$PAGE->pagetype` is not a safe gate for course pages**: `course-view-<format>` is also set on backup, report
  and grade pages. Content injected onto course pages from a non-activity plugin has more traps (anchoring,
  reactive reloads, subsection order): `moodle-field-lessons`.
- **Editing `db/hooks.php` without purging** leaves the old list in the callback cache (`$CFG->cachedir` and
  `$CFG->localcachedir`, file `hookcallbacks.php`); the new callback does not run and nothing reports it.
- **Site admins can re-prioritise or disable a callback** in `config.php` with `$CFG->hooks_callback_overrides`
  (`['\core\hook\output\before_footer_html_generation' => ['local_example\hook_callbacks::before_footer' =>
  ['disabled' => true]]]`). When a callback "does not run" on one site only, look there.
- **Order between plugins is not a contract.** If your callback must see what another added, give it a lower
  priority and still handle the case where the other plugin is absent.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Instance method as callback | Skipped; only a developer debugging line says why | `public static function` |
| `'callback' => function ($hook) {...}` | Rejected at load, hook never runs | `[Class::class, 'method']` |
| Implementing `\core\hook\stoppable_event_interface` | Fatal: interface does not exist | `\Psr\EventDispatcher\StoppableEventInterface` + `\core\hook\stoppable_trait` |
| Calling `stop()` on a core stoppable hook | Fatal: no such method | `$hook->stop_propagation()` |
| `get_primary_view()` on `primary_extend` | Fatal: undefined method | `$hook->get_primaryview()` |
| `new before_standard_top_of_body_html_generation()` in a test | ArgumentCountError: the renderer is required | Pass `$PAGE->get_renderer('core')` |
| Looking for a hook that replaces `extend_navigation()` | None exists on 5.2 or 5.3 | Keep the `lib.php` callback |
| Removing the legacy function while a supported branch lacks the hook | That branch loses the feature | Keep both; core skips the old one when the hook is registered |
| Throwing from `after_config` to deny access | Browser gets 500 or 404 | Send 403, print a minimal page, `exit` |
| `php admin/cli/hooks_list.php` | No such script | Site administration > Development > Hooks overview (`/admin/hooks.php`) |
| Treating the "should be migrated" debugging as noise | Behat steps fail on it; PHPUnit shows it only as a notice in a passing run | Register the hook |

## Reference files

| File | Read it when |
|---|---|
| [reference/core-hook-catalogue.md](moodle-skill-files/moodle-hooks-api/reference/core-hook-catalogue.md) | you need to know whether core has a hook for an action (course, enrolment, group, user, file, AI, backup, quiz, output) and its class name, constructor and methods |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-hooks-api/versions/moodle-5.3.md): hooks added in 5.3 (email, import map, RequireJS map) and the `extend_user_menu` change |

## References

- https://moodledev.io/docs/apis/core/hooks
- https://moodledev.io/docs/apis/core/di
- https://moodledev.io/general/development/policies/deprecation
- `public/lib/classes/hook/manager.php` (5.2 and 5.3.0)


---

### moodle-language-pack

> Use when asked to translate a Moodle plugin's strings into another language, "add a language pack" (es, ja, pt_br, zh_tw ...), update an existing translation after lang/en changed, or try a translation on a test site. Covers the file name per plugin type (lang/<code>/<component>.php, an activity's <modname>.php), Moodle's language codes, keeping every key and only the keys of lang/en, placeholders ({$a}, {$a->name}) and HTML kept intact, _help strings, PHP quoting, checking a pack with php -l and a key and placeholder diff, keeping packs outside the plugin repository (the package ships lang/en only), installing a pack as a local customisation (<code>_local under $CFG->langlocalroot) to view it with ?lang=, and contributing it through AMOS. Skip when adding or renaming English strings (moodle-plugin-development) or finding hard-coded English (the /moodle-string-check command).

# Moodle Language Pack

## Overview

A translation of a plugin's strings into one language, as a file that Moodle can load. It is kept outside the
plugin repository, because a plugin's package ships only `lang/en/` and other languages reach sites through the
Moodle language packs (AMOS). Keeping the file lets you view it on a test site and contribute it.

## When to Use

- "Add a language pack for ja", `/add-language-pack es`, "translate the plugin into Portuguese (Brazil)"
- `lang/en` changed and the existing packs need the new and changed strings
- Viewing a translation on a test site, or preparing it for AMOS
- **Skip when:** adding or changing English strings (`moodle-plugin-development`) or finding hard-coded English
  (`/moodle-string-check`)

## Where the files go

In the project's notes directory, never inside the plugin repository: the Plugins directory review expects only
`lang/en/` in the package, and a non-English file in `lang/` ships with every release. Use the notes directory the
project's instructions name; otherwise ask once.

```
<notes>/<plugin>/lang-<code>/<file>.php
```

`<file>` is the same file name as in `lang/en/`: `<type>_<name>.php` (`local_forumcare.php`), except an activity
module, whose file is `<name>.php` without `mod_` (`public/lib/classes/string_manager_standard.php`, 5.3.0). Several
plugins of one project each get their own `lang-<code>/` under their own notes folder.

## Language codes

Moodle's codes are lower case with an underscore: `es`, `ja`, `de`, `pt_br`, `zh_cn`, `zh_tw`, `es_mx`, `fr_ca`.
`es` is international Spanish and `es_mx` a child of it; a child pack holds only what differs. The list of codes is
at https://download.moodle.org/langpack/5.3/. If the user's code is not one of them (`pt-BR`, `zh`), map it to the
Moodle code and say which was used, or ask when two fit (`zh`: `zh_cn` or `zh_tw`).

## The recipe

1. **Read the English file** `lang/en/<file>.php` from the repository at its current commit. Count the keys.
2. **If the pack exists**, read it: keep every translation whose English text is unchanged, translate new keys,
   retranslate keys whose English changed (compare with `git log -p lang/en/<file>.php` since the pack's date), and
   drop keys no longer in English.
3. **Translate each string.**
   - Keep the placeholders exactly: `{$a}`, `{$a->name}`, and the same set in each string. Their order in the
     sentence may change.
   - Keep HTML tags and Markdown in `_help` strings; translate only the text.
   - Keep the meaning of the UI: a button label stays short; a menu item matches how core translates the same word
     in that language. Read core's pack for the language where one is installed
     (`$CFG->dataroot/lang/<code>/moodle.php`) and reuse its terms ("course", "activity", "grade").
   - Product and plugin names stay as they are unless the plugin's own English string translates them.
   - Quote with single quotes and escape `'` as `\'`. Keep the file's sort order.
4. **Write the file** with the plugin's licence header, a docblock naming the language
   (`Japanese strings for local_forumcare.`) and the copyright holder of the translation, then the strings:

   ```php
   <?php
   // This file is part of Moodle - http://moodle.org/
   // ... the GPL header as in lang/en ...

   /**
    * Japanese strings for local_forumcare.
    *
    * @package    local_forumcare
    * @copyright  2026 <translation's copyright holder>
    * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
    */

   defined('MOODLE_INTERNAL') || die();

   $string['pluginname'] = 'フォーラムケア';
   $string['reportpost'] = 'この投稿を報告';
   ```

5. **Check it** (below), then add a line to the plugin's notes: language, key count, date, the commit of
   `lang/en` it matches, and who translated it ("machine translation, not reviewed by a native speaker" when that
   is the case).

## Checking a pack

```bash
php -l <notes>/<plugin>/lang-ja/local_forumcare.php
php -r '
  define("MOODLE_INTERNAL", 1);
  $string = []; include $argv[1]; $en = $string;
  $string = []; include $argv[2]; $xx = $string;
  echo "missing: ", implode(", ", array_keys(array_diff_key($en, $xx))) ?: "none", "\n";
  echo "extra: ", implode(", ", array_keys(array_diff_key($xx, $en))) ?: "none", "\n";
  foreach ($en as $k => $v) {
      if (!isset($xx[$k])) { continue; }
      preg_match_all("/\{\\\$a(->\w+)?\}/", $v, $a); preg_match_all("/\{\\\$a(->\w+)?\}/", $xx[$k], $b);
      sort($a[0]); sort($b[0]);
      if ($a[0] !== $b[0]) { echo "placeholders differ: $k\n"; }
  }' -- lang/en/local_forumcare.php <notes>/<plugin>/lang-ja/local_forumcare.php
```

Pass: `php -l` clean, missing and extra both `none`, no "placeholders differ" line. Then read the translated file
once for strings left in English.

## Viewing it on a test site

Moodle loads a plugin's strings in a language from the plugin's `lang/<code>/`, then
`$CFG->langotherroot/<code>/`, then local customisations in `$CFG->langlocalroot/<code>_local/` (both default to
`$CFG->dataroot/lang`; `public/lib/classes/string_manager_standard.php`, 5.3.0). To view a pack without touching
the plugin or the installed language pack:

1. The language itself must be installed on the site (Site administration > Language > Language packs).
2. Copy the file to `$CFG->dataroot/lang/<code>_local/<file>.php`, readable by the web server user.
3. Purge caches (`php admin/cli/purge_caches.php`), then open a page with `?lang=<code>`.

The `_local` copy overrides the official translation on that site. Remove it when done, and say in the notes if it
is left in place.

## Contributing it

Once the plugin is in the Plugins directory, its English strings are imported into AMOS (https://lang.moodle.org),
and translations reach sites through the language packs. Contribute the pack there: log in, import the file into
your AMOS stage, and submit the staged strings to the language pack maintainers (described in the AMOS
documentation, not run here). A plugin not yet in the directory has nothing in AMOS to translate.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| The pack put in the plugin's `lang/<code>/` | It ships in the release; reviewers ask for `lang/en` only | Keep it in the notes directory |
| `mod_<name>.php` for an activity | The file is never loaded | `<name>.php` |
| A placeholder translated or dropped | `{$a}` shows literally, or a value is missing from the sentence | Keep the same placeholder set; check with the diff |
| An apostrophe not escaped | Parse error: every string of the plugin fails in that language | `\'`, and `php -l` |
| Keys missing after `lang/en` grew | Those strings fall back to English | Re-run the key diff on every update |
| A code that is not Moodle's (`pt-BR`) | The directory name matches no language | `pt_br` |
| Copying into `<code>/` instead of `<code>_local/` | The next language pack update overwrites it | `<code>_local/` |
| A machine translation presented as reviewed | Users trust wording no speaker checked | Say who translated it |

## References

- https://moodledev.io/docs/5.3/apis/core/string
- https://docs.moodle.org/en/AMOS
- https://download.moodle.org/langpack/5.3/


---

### moodle-marketplace-package

> Use when asked to prepare a Moodle Plugins directory (Marketplace) submission or listing update - "make the Marketplace package", "publishing docs", listing text, screenshots for the plugin page. Produces one folder per release with listing.txt (every form field ready to paste: name, type, component, short description, full description as HTML, source control URL, bug tracker URL, documentation URL, supported versions, maturity, release notes, screenshot captions), listing.md (where each claim and screenshot came from), the numbered screenshots and the release ZIP. Covers reading the field values from version.php, the git remote and the README, checking the issue tracker is enabled, writing descriptions that make only checked claims, and taking listing screenshots. Skip when building the ZIP, tagging or answering a reviewer (moodle-plugin-release), auditing the code before release (moodle-release-preflight), or making an internal walkthrough report (moodle-walkthrough).

# Moodle Marketplace Package

## Overview

Everything needed to submit a plugin, or a new version, to the Moodle Plugins directory, gathered in one folder so
that submitting is copy, paste and upload. The rules the listing must meet (required tracker, licence, service
disclosure) are owned by `moodle-plugin-release`; this skill produces the files.

## When to Use

- "Make the Marketplace package", "prepare the publishing docs", "write the listing" for a plugin or theme
- A first submission, a new version upload, or a change to the listing text or screenshots
- **Skip when:** building the ZIP itself, tagging or replying to a reviewer (`moodle-plugin-release`), auditing the
  code for review findings (`moodle-release-preflight`), or an internal walkthrough (`moodle-walkthrough`)

## Where the files go

Outside the plugin repository, in the project's notes directory (the project's instructions name it; otherwise
ask once). One folder per release, never overwritten:

```
<notes>/<plugin>/marketplace-<release>/
    listing.txt            every field, ready to paste; open in any text editor
    listing.md             provenance: commit, screenshot site, demo data, how each claim was checked
    01-<what>.png ...      screenshots, in upload order
    <name>-<release>.zip   the release ZIP (built with moodle-plugin-release)
```

For a new version of a plugin already listed, copy the previous folder's text and screenshots forward, change
what the release changed, and say in `listing.md` what was carried over and why it still holds.

## listing.txt

A plain text file (`.txt`, so it opens in any editor) with one labelled block per form field, in the form's order.
The short description is plain text. The full description is HTML, because the directory's description field
takes formatted text; keep to simple tags (`<p>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`,
`<code>`), no styles, classes or scripts.

```text
PLUGIN NAME
Scribbles

PLUGIN TYPE
Local plugins

COMPONENT
local_scribbles

SHORT DESCRIPTION
Draw on any Moodle page with pen, highlighter, text, box and ellipse tools, then save the annotations or a screenshot.

FULL DESCRIPTION (HTML)
<p>Scribbles lets teachers draw on any Moodle page. ...</p>
<h3>Who it is for</h3>
<p>...</p>
<h3>Features</h3>
<ul>
<li>...</li>
</ul>
<h3>Requirements</h3>
<ul>
<li>Moodle 5.2 or 5.3.</li>
</ul>
<h3>Privacy</h3>
<p>...</p>

SOURCE CONTROL URL
https://github.com/<owner>/moodle-local_scribbles

BUG TRACKER URL
https://github.com/<owner>/moodle-local_scribbles/issues

DOCUMENTATION URL
https://github.com/<owner>/moodle-local_scribbles#readme

SUPPORTED MOODLE VERSIONS
5.2, 5.3

MATURITY
Beta

RELEASE NAME
0.1.1

VERSION
2026110404

RELEASE NOTES
- ...

LICENCE
GNU GPL v3 or later

SCREENSHOTS (upload in this order)
01-annotate-course-page.png
A course page annotated with the pen, highlighter, box and text tools.
02-...
```

Where each value comes from (never from memory):

| Field | Source |
|---|---|
| Plugin name | `pluginname` in `lang/en/<component>.php` (`modulename` for an activity) |
| Type and component | `$plugin->component` in `version.php`; the type is its prefix, named as the directory names it ("Activities", "Blocks", "Local plugins") |
| Supported versions | `$plugin->supported`, checked against `$plugin->requires` and the CI matrix |
| Maturity, release, version | `$plugin->maturity`, `$plugin->release`, `$plugin->version` at the release tag |
| Source control URL | `git remote get-url origin`, written as the `https://` web URL |
| Bug tracker URL | the repository's issues page; check issues are enabled (`gh api repos/<owner>/<repo> --jq .has_issues` is `true`): a tracker is required for approval |
| Documentation URL | the README on the forge (`...#readme`), or the plugin's documentation page if one exists |
| Release notes | this release's section of `CHANGES.md` (or the changelog the repository keeps) |
| Licence | the `LICENSE` file and the file headers |

If the plugin needs an external service, the full description says so, what depends on it, what happens without
it and how to get credentials, and `listing.txt` has a block of demo credentials for the reviewer
(`moodle-plugin-release`, reference `plugins-directory-submission.md`).

## Writing the descriptions

- **Short description:** one or two sentences: what it does and for whom. It shows in search results.
- **Full description:** what it does, who it is for, the features, what administrators set up, limits,
  requirements (Moodle and PHP versions, databases tested, other plugins, services), privacy (what personal
  data it stores and where it is sent). Same facts as the README.
- Every claim is one you checked: a feature you saw on the site, a version CI ran, a capability in
  `db/access.php`. Record the check in `listing.md`. "Works in all browsers" without testing them is not a claim
  to make; say which were tested.
- State limits plainly. A reviewer or an admin finding an unstated limit costs more than the sentence.
- Name settings and labels exactly as they appear in the UI, with the settings path
  (`Site administration > Plugins > Local plugins > Scribbles`).
- No marketing superlatives, no comparisons with other plugins, no Moodle trademark misuse.

## Screenshots

Take them with the `moodle-walkthrough` recipe (demo data, Playwright, read each image), with these listing rules:

- The current release's code, on a stock Boost site, light mode, at least 1280 x 800 (a 1.5x device scale gives
  sharper images). Crop to the plugin's UI where the rest of the page adds nothing.
- Every visible name is demo data chosen for the listing: course, users, site name. Read every proper noun in
  each image. No test leftovers, no other plugins' buttons, no offensive or placeholder text.
- 4 to 10 images, in the order a new user meets the plugin; the first one shows it doing its main job.
- Each has a one-sentence caption in `listing.txt`.

## listing.md

The record a later release, or a reviewer's question, needs:

- the commit and tag the package was made from, and whether CI passed on it;
- the site, Moodle version and theme the screenshots were taken on, and that the deployed code matched the commit;
- the demo data and whether it is still on the site;
- a table of screenshots with captions;
- "How the claims were checked": one line per claim that needed checking.

## The ZIP

Build and inspect it with `moodle-plugin-release`: its root folder is the plugin directory name, `LICENSE` is in
it, `lang/` holds only `en/`. Put the ZIP in the folder so the upload is from the same place.

## Hand it over

Give the folder path and say what to do: on a first submission, create the plugin in the directory and fill each
field from `listing.txt`; on a version, upload the ZIP with the release notes. Submitting is the maintainer's
action: prepare it, do not submit.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Full description as plain text | Paragraphs and lists run together on the plugin page | HTML in `listing.txt`, simple tags only |
| Values typed from memory | The listing's versions or maturity disagree with `version.php` | Read each from the source in the table |
| Issues disabled on the repository | Approval is blocked: the reviewer has nowhere to file | Check `has_issues`, enable it |
| Claims nobody checked | A reviewer or admin finds the plugin does not do what the page says | Record each check in `listing.md` |
| Screenshots from an old build or with test names | The page shows the wrong UI or someone's real data | Current code, demo data, read every image |
| Package folder inside the repository | Screenshots and the ZIP end up in the next release | The notes directory |
| A new version overwrites the last folder | The record of what was submitted is lost | One folder per release |

## References

- https://moodledev.io/general/community/plugincontribution/checklist
- https://moodle.org/plugins


---

### moodle-mobile-app

> Use when adding Moodle app (mobile) support to a plugin - db/mobile.php handlers and delegates (CoreMainMenuDelegate, CoreCourseModuleDelegate, CoreCourseOptionsDelegate, CoreBlockDelegate, CoreQuestionDelegate), classes/output/mobile.php methods called through tool_mobile_get_content, templates/mobileapp Mustache with {{=<% %>=}} and Ionic markup, otherdata and CONTENT_OTHERDATA, core-site-plugins-call-ws and other site-plugin directives, handler JavaScript (this.CoreSitesProvider, updateContent caching, detectChanges), offlinefunctions and prefetch, app CSS (--ion-*-color-step-N, :root.dark), push notifications, and errors such as "Scalar type expected, array or object received", "Access control exception", "serverconnectionajax" or a plugin that silently does nothing in the app. Skip when the plugin has no app UI and only needs web services (moodle-web-services).

# Moodle App Integration (site plugins)

## Overview

The Moodle app (Ionic and Angular) has no plugin code of its own for third-party plugins. It asks the site which
plugins support it, then asks each plugin's PHP for Angular templates, data and JavaScript, and compiles them at run
time. A plugin adds app support with PHP and templates only; no app build is involved. This skill gives the request
flow, a recipe that works, and the failures that show up only inside the app.

Evidence tags: **read** means read in the Moodle 5.2 or 5.3.0 source, the Moodle app 5.3.0 source or the app
developer docs, not run; **seen** means observed in a running app against a site.

## When to Use

- Writing `db/mobile.php` or `classes/output/mobile.php`, or templates under `templates/mobileapp/`
- An activity, block, course tab, main-menu page, question type or profile field must work in the app
- Calling web services from an app template, or making a view available offline
- The plugin works in the browser but shows nothing, an error, or stale content in the app
- **Skip when:** declaring the web service functions themselves (`moodle-web-services`); checking client-supplied
  arguments for SQL and access bugs before a release (`moodle-release-preflight`); styling the web site
  (`moodle-theme-scss`).

## How a request flows

1. On login the app calls `tool_mobile_get_plugins_supporting_mobile`. Core `require`s every plugin's
   `db/mobile.php`, reads `$addons`, and returns each handler JSON-encoded together with the `lang` strings in every
   installed language (`public/admin/tool/mobile/classes/api.php:160-230`, read 5.3.0). The result is cached in the
   `tool_mobile/plugininfo` MUC cache: after editing `db/mobile.php`, purge caches and log in again in the app.
2. When the user opens a handler, the app calls `tool_mobile_get_content(component, method, args)`. Core calls
   `\<component>\output\mobile::<method>(array $args)` directly (`external::get_content()` in
   `public/admin/tool/mobile/classes/external.php`, read 5.2 and 5.3). The method is not a web service: do not declare it in `db/services.php`.
3. The method returns `templates`, `javascript`, `otherdata`, `files`, and for `init` methods `restrict` and
   `disabled`. The app renders the first template, runs the JavaScript in the component's scope, and exposes
   `otherdata` as `CONTENT_OTHERDATA` (`INIT_OTHERDATA` for `init`).
4. Buttons in the template call your real web services (declared with `MOODLE_OFFICIAL_MOBILE_SERVICE` in
   `services`) through directives such as `core-site-plugins-call-ws`, or open more content with
   `core-site-plugins-new-content`.

`tool_mobile_get_content` validates nothing about your arguments and checks no capability: the method is a page
script and does what `view.php` does (`require_login`, `require_capability`). Every value in `$args` comes from the
client as a string.

## Default recipe: an activity view

```php
// db/mobile.php (GPL header)
defined('MOODLE_INTERNAL') || die();

$addons = [
    'mod_example' => [
        'handlers' => [
            'view' => [
                'delegate' => 'CoreCourseModuleDelegate',
                'method' => 'mobile_course_view',
                'displaydata' => [
                    'icon' => $CFG->wwwroot . '/mod/example/pix/monologo.svg',
                    'class' => '',
                ],
                'offlinefunctions' => [
                    'mobile_course_view' => [],
                ],
                'styles' => [
                    'url' => $CFG->wwwroot . '/mod/example/mobileapp/styles.css',
                    'version' => '1',
                ],
            ],
        ],
        'lang' => [
            ['pluginname', 'mod_example'],
            ['markdone', 'mod_example'],
            ['done', 'mod_example'],
        ],
    ],
];
```

```php
// classes/output/mobile.php (GPL header)
namespace mod_example\output;

use context_module;

/**
 * App content for mod_example.
 *
 * @package    mod_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class mobile {
    /**
     * The activity page in the app.
     *
     * @param array $args cmid, courseid, userid and app details, all sent by the app as strings
     * @return array
     */
    public static function mobile_course_view(array $args): array {
        global $DB, $OUTPUT, $USER;

        $cmid = clean_param($args['cmid'], PARAM_INT);
        $cm = get_coursemodule_from_id('example', $cmid, 0, false, MUST_EXIST);
        require_login($cm->course, false, $cm, true, true);
        $context = context_module::instance($cm->id);
        require_capability('mod/example:view', $context);

        $instance = $DB->get_record('example', ['id' => $cm->instance], '*', MUST_EXIST);
        $items = array_values($DB->get_records('example_items', ['exampleid' => $instance->id], 'sortorder', 'id, name'));
        foreach ($items as $item) {
            $item->name = format_string($item->name, true, ['context' => $context]);
        }

        return [
            'templates' => [[
                'id' => 'main',
                'html' => $OUTPUT->render_from_template('mod_example/mobileapp/view', [
                    'cmid' => $cm->id,
                    'name' => format_string($instance->name, true, ['context' => $context]),
                ]),
            ]],
            'javascript' => '',
            'otherdata' => [
                'items' => json_encode($items),
                'userid' => $USER->id,
            ],
            'files' => [],
        ];
    }
}
```

```handlebars
{{! templates/mobileapp/view.mustache: Mustache runs on the server with <% %>, Angular in the app with {{ }}. }}
{{=<% %>=}}
<ion-list>
    <ion-list-header><h2><% name %></h2></ion-list-header>
    <ion-item *ngFor="let item of CONTENT_OTHERDATA.items">
        <ion-label>{{ item.name }}</ion-label>
        <ion-button slot="end" core-site-plugins-call-ws name="mod_example_mark_done"
                [params]="{cmid: <% cmid %>, itemid: item.id}" [preSets]="{getFromCache: 0, saveToCache: 0}"
                successMessage="{{ 'plugin.mod_example.done' | translate }}" refreshOnSuccess="true">
            {{ 'plugin.mod_example.markdone' | translate }}
        </ion-button>
    </ion-item>
</ion-list>
```

Why each piece is there: the method checks access like a page; `json_encode` because each `otherdata` value must
be a scalar (an array fails the whole call with "Scalar type expected, array or object received"), and the app
parses any value starting with `{` or `[` back into an object before your JavaScript runs
(`src/core/features/siteplugins/services/siteplugins.ts:232`, app 5.3.0); `{{=<% %>=}}` stops server Mustache from
eating Angular's `{{ }}`; `getFromCache: 0` stops a write call from being answered from the app's cache; strings are
listed in `lang` and used as `plugin.<component>.<id>`. `mod_example_mark_done` is an ordinary external function
with `'services' => [MOODLE_OFFICIAL_MOBILE_SERVICE]` that checks access itself (`moodle-web-services`).

Handlers for other plugin types (main menu, course option, block, user profile, question type, format, settings)
differ only in the delegate and its options: [reference/handlers.md](moodle-skill-files/moodle-mobile-app/reference/handlers.md).

## Traps that only show in the app

**The app's content cache repeats the first answer.** Content is fetched with a cached read keyed on component,
method and args. A "next item" flow that calls `this.updateContent(args)` works once and then shows the same item.
Pass presets that bypass the cache, or invalidate first, and walk every loop to its end in testing, since the first
iteration is the cold-cache case:

```javascript
this.updateContent({cmid: this.cmid, page: next}, undefined, undefined, undefined,
    {getFromCache: false, saveToCache: false, emergencyCache: false});
```

**Parsing `otherdata` again throws.** `JSON.parse(this.CONTENT_OTHERDATA.items)` on a value the app has already
parsed throws; inside a `try` the view just stays empty with nothing in the console.

**Handler JavaScript gets `this.componentContainer`, not an `ElementRef`.** Looking for your form with
`document.querySelector('form')` finds the first form in the whole app; scope DOM lookups to
`this.componentContainer` (`src/core/features/compile/components/compile-html/compile-html.ts:263-264`, app 5.3.0).

**Assignments after an `await` do not re-render.** They run outside the change detection the tap started. Call
`this.ChangeDetectorRef.detectChanges()` after updating properties in an async handler.

**`core-question` reads its question once.** Giving it a new question object does nothing; hide it with `*ngIf`,
let it be destroyed, and show it again on the next tick.

**JavaScript can run before the template is in the DOM** (API reference, Content responses): put DOM work in a
`setTimeout`, or better, drive everything from Angular bindings.

**Handler CSS applies to the whole app.** Scope every rule under your own class. The app has no
`--ion-color-step-*` variables: use `--ion-text-color-step-N` and `--ion-background-color-step-N`
(`src/theme/theme.light.scss`, app 5.3.0), and scope dark rules to `:root.dark`, the class the app toggles. Bump
`styles.version` on every change or devices keep the old file. An undefined `var(--x, fallback)` silently uses the
fallback, so check each name exists.

**Static templates are fetched once at login.** Question types, profile fields and other delegates marked "static"
in the API reference get no context in `$args` and are cached on the device until the next login.

**Offline covers reading only.** `offlinefunctions` (course-module handlers) and the `files` list make a view and
its files available after prefetch. A write made offline is not queued for you: the call fails, and the directive
shows the error. Design writes to fail visibly offline, or implement your own sync in handler JavaScript.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Declaring `mobile_course_view` in `db/services.php` | An external function that is not one (no `_parameters()`/`_returns()`), which the app never calls | The method is called by `tool_mobile_get_content`; declare only real web services |
| Class not at `\<component>\output\mobile` | `coding_exception`: "Missing method in ..." | `classes/output/mobile.php`, namespace `<component>\output` |
| No `require_login()` / capability check in the method | Any app user can read the content | Check access as `view.php` does |
| An array in `otherdata` | "Scalar type expected, array or object received"; the page fails | `json_encode()` the value |
| `JSON.parse()` of `otherdata` in JavaScript | Exception; empty view, nothing logged | Use the value as is |
| Server Mustache without `{{=<% %>=}}` | Angular expressions vanish on the server | Switch delimiters at the top of the template |
| String used in a template but not listed in `lang` | Raw `plugin.mod_example.x` shown | Add `[id, component]` to `lang`, purge, log in again |
| Write call without `getFromCache: 0` | Second tap returns the first response | Presets on writes; presets on `updateContent()` |
| Web service without `MOODLE_OFFICIAL_MOBILE_SERVICE` | "Access control exception" from the app | Add the service, upgrade |
| `offlinefunctions` on a main-menu or block handler | Ignored | Only `CoreCourseModuleDelegate` takes it; use a prefetch handler otherwise |
| Editing `db/mobile.php` and reloading the app | No change | Purge caches, then log out and in (handlers are cached in `tool_mobile/plugininfo`) |
| Styles changed, `version` not | Old CSS on devices | Bump `styles.version` |
| `--ion-color-step-*` or `prefers-color-scheme` in app CSS | Fallback colours; wrong in dark mode | `--ion-text-color-step-N`, `:root.dark` |
| `this.CoreDomUtilsProvider.showToast()` copied from an old example | Deprecated since app 4.5 (the whole class since 5.0); still present in app 5.3.0, will stop working when it is removed | `this.CoreToastsService.show({message, translateMessage: true})`, or `successMessage` on the directive |
| Testing only in PHPUnit | Green tests, broken app (the web service permission layer is never entered) | Call `tool_mobile_get_content` over REST: [reference/testing-and-debugging.md](moodle-skill-files/moodle-mobile-app/reference/testing-and-debugging.md) |

## Reference files

| File | Read it when |
|---|---|
| [reference/handlers.md](moodle-skill-files/moodle-mobile-app/reference/handlers.md) | Choosing a delegate for a plugin type other than an activity, or setting handler options (`displaydata`, `priority`, `restrict*`, `init`, `coursepagemethod`, `updatesnames`, `supportedfeatures`) |
| [reference/templates-and-javascript.md](moodle-skill-files/moodle-mobile-app/reference/templates-and-javascript.md) | Writing template markup beyond the recipe: site-plugin directives, Moodle components (`core-format-text`, `core-file`, `core-rich-text-editor`), `ion-icon` names, forms, handler JavaScript scope, `init` methods and JavaScript overrides, lifecycle hooks |
| [reference/testing-and-debugging.md](moodle-skill-files/moodle-mobile-app/reference/testing-and-debugging.md) | The plugin does nothing or errors in the app, you need the site settings the app requires, you want to call `tool_mobile_get_content` with curl, run the app in a browser, or send push notifications |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-mobile-app/versions/moodle-5.3.md) |

App versions move separately from Moodle LMS. The app documentation marks app-version requirements (for example
`displayinusermenu` needs app 5.1, `CoreEnrolDelegate` app 4.3); check the app version your users run as well as the
site version.

## References

- Plugins development guide: https://moodledev.io/general/app/development/plugins-development-guide
- API reference (handlers, directives, components): https://moodledev.io/general/app/development/plugins-development-guide/api-reference
- Troubleshooting: https://moodledev.io/general/app/development/plugins-development-guide/troubleshooting
- Examples (course modules, forms, question types, prefetch): https://moodledev.io/general/app/development/plugins-development-guide/examples
- Running the app in a browser: https://moodledev.io/general/app/development/setup/app-in-browser
- App source: https://github.com/moodlehq/moodleapp
- Related skills: `moodle-web-services`, `moodle-release-preflight`, `moodle-accessibility`


---

### moodle-performance

> Use when a Moodle page, web service, filter or task is slow, runs too many queries, or runs out of memory, or when adding caching or background work - db/caches.php and \core_cache\cache::make (MUC application, session and request caches, cachedef_ strings, invalidation events), per-context or per-call repeated queries, N+1 loops, get_recordset vs get_records, batching large tables, $DB->perf_get_queries() budgets, ad-hoc and scheduled tasks (db/tasks.php, queue_adhoc_task, locks, retries), session locks, perfdebug, profiling and server tuning. Skip when the slowness is theme CSS compilation (moodle-theme-scss) or the task is a schema change (moodle-plugin-development).

# Moodle Performance

## Overview

A slow Moodle request is almost always one of three things: a query repeated once per item (per course module, per
context, per user), a large result loaded into memory at once, or work done on the request that belongs in a task.
Measure the query count first, fix the shape of the code, then cache what is still repeated.

## When to Use

- A page, filter, block or web service gets slower as a course gets bigger
- The performance footer shows hundreds of queries, or memory grows with the data
- A POST handler or upgrade step does long work (mail, grading, recalculation, external calls)
- Adding `db/caches.php`, `db/tasks.php`, an ad-hoc task or a lock
- **Skip when:** the cost is theme CSS or SCSS compilation (`moodle-theme-scss`), designing tables and indexes
  (`moodle-plugin-development`), or a heavy upgrade step (`moodle-upgrade-migration`, which says to queue an ad-hoc
  task instead).

## Measure first

Turn on the performance footer on a development site: Site administration > Development > Debugging >
"Performance info" (`perfdebug`, stored as 15 when on; `public/admin/settings/development.php`, 5.3.0). The footer
shows DB reads and writes, time, memory, and cache hits and misses per definition. In `config.php`:

```php
$CFG->debug = DEBUG_DEVELOPER;
$CFG->debugdisplay = 1;
$CFG->perfdebug = 15;
```

Count queries around the code path, in a script or a PHPUnit test, with the DML counters
(`public/lib/dml/moodle_database.php`, 5.2 and 5.3):

```php
$before = $DB->perf_get_queries();      // Also perf_get_reads(), perf_get_writes().
// ... the hot path ...
$used = $DB->perf_get_queries() - $before;
```

**A query budget test keeps a fix fixed.** Render the hot path for many items and assert a ceiling that does not grow
with the number of items:

```php
public function test_render_cost_does_not_grow_with_activities(): void {
    global $DB;
    $this->resetAfterTest();
    $course = $this->getDataGenerator()->create_course(['summary' => '']);
    for ($i = 0; $i < 30; $i++) {
        $this->getDataGenerator()->create_module('page', ['course' => $course->id]);
    }
    $contexts = [];
    foreach (get_fast_modinfo($course)->get_cms() as $cm) {
        $contexts[] = $cm->context;
    }

    $before = $DB->perf_get_queries();
    foreach ($contexts as $context) {
        format_text('Plain text', FORMAT_HTML, ['context' => $context]);
    }
    $this->assertLessThanOrEqual(10, $DB->perf_get_queries() - $before);
}
```

**Assert read counts only as "zero" or "at most N".** `perf_get_reads()` depends on the driver: on PostgreSQL an
unlimited `get_recordset_select()` is a cursor (`DECLARE`, then one `FETCH` per buffer, then `CLOSE`), so one
recordset counts as three or more reads, while MySQL and MariaDB count one. An exact-count assertion passes on one
database and fails on the other. Assert zero reads for a cache hit, use `get_records_*` for small sets in tested
code, and treat a non-zero exact count as unverified until the PostgreSQL CI row has run
(`public/lib/dml/pgsql_native_moodle_database.php`, cursor handling, 5.3.0).

Slow-query logging, EXPLAIN, profiling with `?PROFILEME` and server settings:
[reference/diagnosis-and-server.md](moodle-skill-files/moodle-performance/reference/diagnosis-and-server.md).

## Queries

### One query per item is the usual bug

```php
// Slow: one query per course.
foreach ($courses as $course) {
    $teacher = $DB->get_record('user', ['id' => $course->teacherid]);
}

// One query.
[$insql, $params] = $DB->get_in_or_equal(array_column($courses, 'teacherid'), SQL_PARAMS_NAMED);
$teachers = $DB->get_records_select('user', "id $insql", $params, '', 'id, firstname, lastname');
```

`get_in_or_equal()` throws on an empty array unless its fifth argument (`$onemptyitems`) is given; check for empty
input first. The same applies to capabilities: one `get_users_by_capability($context, 'mod/quiz:attempt',
'u.id, u.firstname, u.lastname')` instead of `has_capability()` for each user.

### Resolve per-context values once per request

Code that runs once per `format_text()`, `format_string()`, block or course module (filters above all) must not
query once per call. Core calls a filter's `setup()` for every `format_text()` and `format_string()`; on a course page
each activity has its own context, so a lookup that walks the parent contexts runs one query per ancestor per
activity, even when the text does not need the filter. Symptom: the footer's query count grows by several queries
for every activity added, and Plugins directory reviewers flag it. Fix: resolve each context once per request,
reuse the parent levels, and reuse what core already loaded (a filter has its own context's settings in
`$this->localconfig`; `public/filter/classes/text_filter.php`, 5.3.0):

```php
// db/caches.php
$definitions = [
    'contextconfig' => [
        'mode' => cache_store::MODE_REQUEST,
        'simplekeys' => true,
    ],
];
```

```php
public static function for_context(\core\context $context): \stdClass {
    $cache = \core_cache\cache::make('filter_example', 'contextconfig');
    if (($config = $cache->get($context->id)) !== false) {
        return $config;
    }
    $parent = $context->get_parent_context();
    $config = $parent ? clone(self::for_context($parent)) : get_config('filter_example');
    foreach (filter_get_local_config('example', $context->id) as $name => $value) {
        $config->$name = $value;
    }
    $cache->set($context->id, $config);
    return $config;
}
```

A request cache is purged between PHPUnit tests (`public/lib/classes/test/testing_util.php`, `reset_dataroot()`
calls `\core_cache\helper::purge_all()`, 5.3.0). A plain `static` array is not, so state from one test leaks into the
next unless you add a reset method and call it.

### Large result sets: recordsets, and batch by rows

`get_records*()` loads every row into a PHP array. For a table that grows with the site, iterate a recordset and
close it:

```php
$rs = $DB->get_recordset('local_example_log', ['courseid' => $courseid], 'id', 'id, userid, timecreated');
foreach ($rs as $row) {
    // ...
}
$rs->close();
```

An unclosed recordset keeps a cursor or result buffer open until the request ends. Keep per-row queries out of the
loop body, or the recordset only moves the N+1 problem.

**Batch on the ids you read, never on id arithmetic.** Ids are sparse (deleted rows, other plugins sharing the
sequence, and PHPUnit starting every table's sequence at a different high value: `public/lib/classes/test/testing_util.php`,
`reset_all_database_sequences()`, 5.2 and 5.3), so a loop over `lastid + 500` skips or repeats rows. Walk the key:

```php
$lastid = 0;
do {
    $rows = $DB->get_records_select('local_example_log', 'id > :lastid', ['lastid' => $lastid],
        'id ASC', 'id, userid', 0, 500);
    foreach ($rows as $row) {
        // ...
    }
    $lastid = $rows ? array_key_last($rows) : $lastid;
} while (count($rows) === 500);
```

To find the boundary of the next batch without loading it, read one row at the offset:
`get_records_select(..., 'id ASC', 'id', 499, 1)` returns the 500th id.

### Writes

`update_record()` writes every column it is given, and the object usually came from an earlier read; near a counter
or a status column that another request can change, use `set_field()` for the one column, or an SQL
`UPDATE ... SET n = n + 1` through `$DB->execute()` (rule owned by `moodle-field-lessons`).

## Caching with MUC

Recipe for a definition: [reference/muc-caching.md](moodle-skill-files/moodle-performance/reference/muc-caching.md) holds the option table, data sources,
invalidation, versioned data and testing. The rules that bite most often:

- **Every definition needs a `cachedef_<name>` string** in the plugin's `lang/en` file. The cache admin page and the
  performance footer call `get_string('cachedef_' . $area, $component)` (`public/cache/classes/definition.php`,
  `get_name()`, 5.3.0). Symptom: a missing-string finding from a Plugins directory reviewer, and
  `[[cachedef_x]]` on the admin page. No CI check catches it.
- **A `db/caches.php` change needs a version bump.** Definitions are read into the cache configuration on upgrade.
  A definition used before that is found on first use, but with a "Cache definitions reparsed causing cache
  reset" `debugging()` notice and a reset of the cache configuration (`public/cache/classes/factory.php`, 5.3.0).
- **`get()` returns `false` for a miss.** Never cache a bare `false`; wrap it (`['value' => false]`) or cache `0`.
- **Pick the mode by who shares the value:** `MODE_APPLICATION` for every user on every server, `MODE_SESSION` for
  one user, `MODE_REQUEST` for this request only.
- **Prefer event invalidation to `ttl`.** The definition class says so (`public/cache/classes/definition.php`,
  5.3.0): not every store supports a TTL natively, and where it does not, every item is wrapped and checked.
- **Class names:** `\core_cache\cache`, `\core_cache\store`, `\core_cache\helper` have existed since 4.5; the old
  `\cache`, `\cache_store`, `\cache_helper` are class aliases with no notice on 5.2 or 5.3
  (`public/cache/classes/cache.php`, `class_alias()`, 5.3.0). Core's own `db/caches.php` still writes
  `cache_store::MODE_*`.

## Work off the request: tasks

Recipe for an ad-hoc task:

```php
namespace local_example\task;

class send_report extends \core\task\adhoc_task {
    public function execute(): void {
        $data = $this->get_custom_data();
        // ... build and send the report for $data->reportid ...
    }
}
```

```php
$task = new \local_example\task\send_report();
$task->set_custom_data(['reportid' => $report->id]);
$task->set_userid($USER->id);                       // Runs as this user; must be an active user.
\core\task\manager::queue_adhoc_task($task, true);  // true: do not queue a duplicate.
```

- **`set_userid()` makes queueing check the user.** `queue_adhoc_task()` calls `\core_user::require_active_user()`,
  so a suspended or deleted user throws at queue time (`public/lib/classes/task/manager.php`, 5.2 and 5.3).
- **Duplicate detection compares class, component, custom data and user.** Keep timestamps out of the custom data if
  duplicates should collapse.
- **Do not rely on the return value of `queue_adhoc_task($task, true)`.** **5.3+:** a duplicate returns the existing
  task's id where 5.2 returned `false`; see [versions/moodle-5.3.md](moodle-skill-files/moodle-performance/versions/moodle-5.3.md).
- **Re-check permissions in `execute()`.** The user's capabilities may have changed between queueing and running.
- **Throwing from `execute()` marks the task failed** and cron retries it with a growing delay. To wait for something
  without counting a failure, call `$this->set_soft_retry_delay()` and return (present from 5.2.2 and on 5.3; guard
  with `method_exists()` if `requires` is 5.2.0).

Scheduled tasks, `db/tasks.php`, locks, concurrency limits, retries and running tasks from the CLI:
[reference/tasks.md](moodle-skill-files/moodle-performance/reference/tasks.md).

## Sessions and output

- **Release the session lock early** in a long request that only reads the session:
  `\core\session\manager::write_close();`. Parallel AJAX calls from one user otherwise queue behind each other. For
  external functions, `'readonlysession' => true` does the same (`moodle-web-services`).
- **Load heavy JavaScript on demand.** AMD source supports dynamic import, as core does in
  `public/lib/amd/src/notification.js` (5.3.0):

  ```javascript
  const onClick = async() => {
      const {init} = await import('local_example/heavy');
      init();
  };
  ```

- **Production caches stay on:** `cachejs`, `cachetemplates` and theme designer mode off. `config-dist.php` marks
  the changed value of each as not for production servers.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| A lookup per context in a filter or block | Query count grows with the number of activities | Request cache keyed by context id; reuse parent levels |
| `get_records()` on a table that grows with the site | Memory exhaustion on large sites | `get_recordset()` and `close()` |
| Batching with `lastid + 500` | Rows skipped or processed twice | `id > :lastid ORDER BY id` with `limitnum` |
| Exact `perf_get_reads()` assertion | Passes on MySQL, fails on PostgreSQL | Assert zero, or a ceiling |
| `has_capability()` per user in a list | One access check per user | `get_users_by_capability()` |
| Definition without `cachedef_<name>` | Reviewer finding; `[[cachedef_x]]` on the admin page | Add the string |
| `db/caches.php` or `db/tasks.php` edited without a bump | Definition or task never appears | Bump `$plugin->version`, upgrade |
| Caching `false` | Every read is a miss | Wrap the value |
| `ttl` instead of invalidation | Stale data until expiry, wrapper cost | `invalidationevents` and `\core_cache\helper::invalidate_by_event()` |
| Mail or external calls on POST | Slow page, timeouts, duplicate sends on retry | Ad-hoc task |
| Lock released outside `finally` | Lock held until it expires after an exception | `try { ... } finally { $lock->release(); }` |
| Truthiness test on `queue_adhoc_task($t, true)` | "Already queued" never detected on 5.3 | Ask the queue first with `get_queued_adhoc_task_record($t, false)` (5.3 version notes) |
| Grade, modinfo or course APIs in `db/upgrade.php` | Upgrade slow or broken on large sites | Queue an ad-hoc task (`moodle-upgrade-migration`) |

## Reference files

| File | Read it when |
|---|---|
| [reference/muc-caching.md](moodle-skill-files/moodle-performance/reference/muc-caching.md) | Writing or changing a `db/caches.php` definition, choosing options (`simplekeys`, `staticacceleration`, identifiers, data source), invalidating, or testing cached code |
| [reference/tasks.md](moodle-skill-files/moodle-performance/reference/tasks.md) | Writing `db/tasks.php`, a scheduled task, a lock, a concurrency limit or retry handling, or running and debugging tasks from the CLI |
| [reference/diagnosis-and-server.md](moodle-skill-files/moodle-performance/reference/diagnosis-and-server.md) | Finding which query or function is slow (slow-query log, EXPLAIN, profiling), or tuning OPcache, sessions and cache stores on a server |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-performance/versions/moodle-5.3.md) |

## References

- Caching (MUC): https://moodledev.io/docs/apis/subsystems/muc
- Task API: https://moodledev.io/docs/apis/subsystems/task (ad-hoc: `/adhoc`, scheduled: `/scheduled`)
- Lock API: https://moodledev.io/docs/apis/core/lock
- Data manipulation API (recordsets): https://moodledev.io/docs/apis/core/dml
- Profiling: https://moodledev.io/docs/guides/profiling
- Related skills: `moodle-web-services` (`readonlysession`), `moodle-upgrade-migration`, `moodle-field-lessons`,
  `moodle-release-preflight` (Plugins directory review checks), `moodle-phpunit-testing`


---

### moodle-phpunit-testing

> Use when writing, running or debugging PHPUnit tests for a Moodle plugin or core - tests/*_test.php, advanced_testcase, resetAfterTest, data generators (tests/generator/lib.php), public/admin/tool/phpunit/cli/init.php and util.php, vendor/bin/phpunit --testsuite, "No tests executed!", "Unexpected debugging() call detected", "unexpected database modification", tests that pass on MySQL or MariaDB and fail on PostgreSQL, preventResetByRollback, redirectEvents/redirectMessages/redirectEmails, external functions with clean_returnvalue, route_testcase, privacy provider tests, mock_clock_with_frozen and get_mocked_http_client. Covers the test framework's mental model, the default test recipe, invocation traps, fixture and database traps from shipped plugins, and pointers to generators, special test cases and PostgreSQL isolation. Skip when writing Behat acceptance tests (moodle-behat-testing) or building a CI workflow (moodle-ci-matrix).

# Moodle PHPUnit testing

## Overview

Moodle runs PHPUnit 11.5 (5.2 and 5.3, `vendor/phpunit/phpunit`) against a separate test database and dataroot,
resets state after each test, and gives every component a test suite. A green run proves less than it seems: the
bootstrap preloads libraries a web request does not, PostgreSQL wraps each test in a transaction MySQL cannot, and a
wrong invocation runs zero tests and exits 0. This skill gives the model, the recipe and the traps.

How sure each statement is: rules marked "seen in practice" were observed on real plugins; everything else was read in
the 5.2 and 5.3.0 source (paths below are relative to the Moodle root) and not run for this skill.

## When to Use

- Writing tests for a plugin's classes, events, tasks, external functions, privacy provider, templates or settings
- A test fails only on CI, only on PostgreSQL, only when run alone, or only in a particular order
- `init.php` output, "No tests executed!", warnings, or "Unexpected debugging() call detected"
- Adding a data generator or a shared test base class
- **Skip when:** writing Behat features (`moodle-behat-testing`), setting up the GitHub Actions workflow and matrix
  (`moodle-ci-matrix`), or doing the pre-release walk (`moodle-definition-of-done`).

## Mental model

1. **Separate site.** `$CFG->phpunit_prefix` and `$CFG->phpunit_dataroot` in `config.php` name a second database
   prefix and dataroot (`config-dist.php`). `init.php` installs every plugin on disk into them and writes
   `phpunit.xml` from `phpunit.xml.dist`, with one `<testsuite name="<component>_testsuite">` per component and
   `suffix="_test.php"` directories. Never edit `phpunit.xml`; it is regenerated.
2. **Init is keyed on versions.** Init reinstalls only when the hash of all component versions changes. A table added
   to `install.xml`, or a changed settings default, without a version bump never reaches the test site; any bump
   anywhere makes every run demand a re-init.
3. **Reset per test.** `advanced_testcase` restores `$CFG`, `$DB`, `$USER`, caches and the database after each test
   (`public/lib/phpunit/classes/advanced_testcase.php`, 5.2 and 5.3). With `$this->resetAfterTest()` the reset is
   silent; without it, a test that wrote anything fails with "Warning: unexpected database modification, resetting
   DB state".
4. **PostgreSQL is different.** On PostgreSQL (and SQL Server) each test runs inside a delegated transaction that is
   rolled back (`setup_test_environment()`, same file). MySQL and MariaDB cannot roll back DDL, so they reset by
   truncation. Code that depends on transaction state behaves differently on the two families.
5. **Not a web request.** `CLI_SCRIPT` is true, the bootstrap has already loaded libraries such as
   `course/lib.php` and `lib/filelib.php`, `$OUTPUT` is not a page renderer, and no form was posted. A missing
   `require_once` or a broken routed POST passes here and fails on the first real page load.
6. **Strict by default.** `phpunit.xml.dist` sets `failOnWarning="true"` and `failOnDeprecation="true"` and
   `beStrictAboutOutputDuringTests="true"` (5.2 and 5.3). A debugging() call left at teardown is raised as
   "Unexpected debugging() call detected." (`teardown_test_environment()`).

## Setup and running

From the Moodle root (5.1 and later keep plugin CLI scripts under `public/`; `vendor/` stays at the root):

```bash
php public/admin/tool/phpunit/cli/init.php                     # install test site, write phpunit.xml
vendor/bin/phpunit --testsuite local_example_testsuite          # one component
vendor/bin/phpunit public/local/example/tests/manager_test.php  # one file
vendor/bin/phpunit --filter test_create_item public/local/example/tests/manager_test.php
php public/admin/tool/phpunit/cli/util.php --drop && php public/admin/tool/phpunit/cli/init.php  # forced rebuild
```

- **Run by `--testsuite` or by an explicit `*_test.php` file, never by a bare directory.** PHPUnit's default suffix
  for a directory argument is `Test.php`, which matches none of Moodle's `*_test.php` files. Symptom: "No tests
  executed!" and exit code 0, which reads as a pass. Fix: the commands above, then read the summary line and require
  `Tests: N` with N greater than 0. Seen in practice.
- **"OK, but there were issues" is a failing run in CI.** Core's own `phpunit.xml.dist` already fails on warnings
  and deprecations, and `moodle-plugin-ci phpunit --fail-on-warning` does the same. Fix the warning; do not add a
  flag to hide it.
- **"Moodle PHPUnit environment was initialised for different version" means some component on disk changed**
  (`public/lib/phpunit/bootstraplib.php`, 5.2 and 5.3), not that yours is broken. Re-run `init.php`. When your own
  schema change is not picked up, bump the plugin's `$plugin->version` or use `util.php --drop` then `init.php`.
- **Run each new test file alone once**, and the whole suite in reverse order once
  (`vendor/bin/phpunit --testsuite local_example_testsuite --order-by=reverse`). Alone catches a missing
  `require_once` that another file happened to load; reverse order catches tests that depend on each other.
  Seen in practice.

## The default test

```php
<?php
// (GPL header)

namespace local_example;

/**
 * Tests for the item manager.
 *
 * @package    local_example
 * @category   test
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
#[\PHPUnit\Framework\Attributes\CoversClass(manager::class)]
final class manager_test extends \advanced_testcase {
    #[\Override]
    protected function setUp(): void {
        parent::setUp();
        $this->resetAfterTest();
    }

    public function test_create_item_stores_name(): void {
        global $DB;
        $course = $this->getDataGenerator()->create_course();
        $user = $this->getDataGenerator()->create_user();

        $id = (new manager())->create_item($course->id, $user->id, 'hello');

        $row = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
        $this->assertSame('hello', $row->name);
        $this->assertEquals($course->id, $row->courseid);
    }
}
```

What moodle-cs enforces on test files (moodle-cs 3.7, `moodle/Sniffs/PHPUnit/`):

- File `tests/<name>_test.php`, class `<name>_test`, namespace of the component (a file in `tests/local/` uses
  `local_example\local`). The class is `final` (warning `UnitTestClassesFinal`).
- Coverage: a `#[CoversClass]`, `#[CoversTrait]`, `#[CoversFunction]`, `#[CoversMethod]` or `#[CoversNothing]`
  attribute on the class (on a method the sniff accepts only `#[CoversNothing]`), or an `@covers` docblock tag at
  class or method level. A test with none gets the warning "is missing any coverage information, own or at class
  level". The attributes are ignored only when phpcs knows the branch is below 5.0 (`TestCaseCoversSniff`,
  `AbstractTestCaseSniff::shouldCheckTestCaseAttributes()`); with an unknown branch, or 5.0 and later, they count.
  Tell phpcs the lowest branch you support with `--runtime-set moodleBranch 502`.
- `setUp()`, `tearDown()`, `setUpBeforeClass()` and `tearDownAfterClass()` call their parent exactly once
  (`ParentSetUpTearDownSniff`; "must call to parent::setUp() only once"). Calling the parent does not reset the
  database; `resetAfterTest()` does.
- No `defined('MOODLE_INTERNAL') || die();` in a file that only declares a class. Test helpers need full docblocks.
- Test methods are `public function test_...(): void`. `getDataGenerator()`, `setUser()` and `setAdminUser()` are
  static, so `self::` and `$this->` both work.

## Common patterns

```php
// Events: assert class, context and objectid, not only the count.
$sink = $this->redirectEvents();
$manager->do_thing();
$events = $sink->get_events();
$sink->close();
$this->assertInstanceOf(\local_example\event\thing_done::class, $events[0]);

// Notifications and email: assert the rendered text, which catches {$a} placeholder mistakes.
$sink = $this->redirectMessages();
$manager->notify($user);
$this->assertStringNotContainsString('{$a', $sink->get_messages()[0]->fullmessage);

// External function: always clean the return value against its declared structure.
$this->setUser($user);
$result = \local_example\external\get_items::execute($course->id);
$result = \core_external\external_api::clean_returnvalue(\local_example\external\get_items::execute_returns(), $result);

// Ad-hoc task: queue it (or let the code under test queue it), then run the queue.
\core\task\manager::queue_adhoc_task(new \local_example\task\send_report());
$this->runAdhocTasks(\local_example\task\send_report::class);

// Scheduled task: call execute() and assert its side effects.
(new \local_example\task\cleanup())->execute();

// Email: the sink captures before any mail is sent.
$sink = $this->redirectEmails();
$manager->notify($user);
$this->assertSame($user->email, $sink->get_messages()[0]->to);

// Users: setUser($user), setAdminUser(), setGuestUser(); each replaces $USER.

// Time: freeze the clock that code reads through \core\di::get(\core\clock::class).
$clock = $this->mock_clock_with_frozen(1893456000);   // 2030-01-01 00:00 UTC.
```

Code that calls `time()` directly does not see the mocked clock; read the time through `\core\clock` in new code.
`redirectHook()`, `assertDebuggingCalled()`, `get_mocked_http_client()` and `get_mocked_string_manager()` are on the
same class. The helper classes behind them have namespaced, autoloaded names on 5.2 and 5.3
(`\core\test\phpunit\phpunit_util`, `\core\test\phpunit\event_sink`, `message_sink`, `phpmailer_sink`,
`\core\test\testing_util`); the old global names (`\phpunit_util`, `\phpunit_event_sink`) keep working without
debugging until 6.0 (MDL-87716, `public/lib/UPGRADING.md` under 5.2). Generators, special test cases and
PostgreSQL detail are in the reference files below.

- **Prefer the real test database to a mocked `$DB`.** The reset makes real rows cheap, and a mocked
  `moodle_database` tests your expectations of the DML API rather than the SQL. When a collaborator must be faked,
  inject it: obtain it in production code through `\core\di::get()` and replace it in the test with
  `\core\di::set(\local_example\remote\api::class, $mock)`. Never assign to the global `$DB`.
- **Coverage:** `vendor/bin/phpunit --coverage-text --testsuite local_example_testsuite` needs pcov or Xdebug loaded.
  `--group <name>` selects tests tagged `#[\PHPUnit\Framework\Attributes\Group('<name>')]` (PHPUnit 11 behaviour,
  not run for this skill); `--testsuite` is the selector that `init.php` builds for every component.
- **A code path behind an optional PHP extension runs only where the extension is loaded.** An `if
  (extension_loaded('imagick'))` branch is skipped on a site with GD only and runs on every CI row, so it fails
  there first. Load the extension locally (`php -d extension=imagick.so vendor/bin/phpunit ...`) or treat that branch
  as untested; the CI side is in `moodle-ci-matrix`.

## Rules that green suites hide

Each was seen in practice on shipped plugins.

- **A debugging() message in a green run is a finding.** Symptom: "Unexpected debugging() call detected" as a notice,
  or a deprecation that `failOnDeprecation` fails on the newest branch only. Fix: call the replacement API, guarded
  with `method_exists()` when the old branch lacks it; use `assertDebuggingCalled()` only when the debugging is the
  behaviour under test.
- **Every template gets a test that renders it.** A `{{#str}}` key missing from the lang file, or a wrong context
  key, passes every lint and unit test and breaks the live page. Fix:

  ```php
  global $PAGE;
  $html = $PAGE->get_renderer('core')->render_from_template('local_example/card', $context);
  $this->assertStringNotContainsString('[[', $html);   // A missing string renders as [[key]].
  $this->assertStringContainsString('>' . s($name) . '<', $html);
  ```

  Use `$PAGE->get_renderer()` in tests, not `$OUTPUT`, which is not a page renderer outside a real request.
- **A test process has loaded libraries a page has not.** The data generator requires `course/lib.php`
  (`public/lib/testing/generator/data_generator.php`), `get_file_storage()` requires `lib/filelib.php`, and every
  earlier test in the same run leaves its own `require_once` files loaded. Symptom: free functions from those
  files work in PHPUnit and the page dies with "Call to undefined function". Fix: add the `require_once` in the
  file that calls them, and make one real web request to every new entry point before calling the work done.
- **`CLI_SCRIPT` is true under PHPUnit.** A `if (CLI_SCRIPT) { return; }` guard short-circuits every positive test,
  and a suite that only asserts `false` then passes against broken code. Fix: inject the condition, and give every
  negative test a positive twin that must pass.
- **Negative tests assert the specific reason.** "It threw" proves nothing when it threw for an unrelated reason.
  Fix: `expectExceptionMessage()` or assert the error code; a security regression test counts only after it was
  seen failing with the fix reverted, at the exact output position.
- **`assign_capability()` defaults to `$overwrite = false`** and does nothing when a row exists, for example the
  archetype's allow. Fix: pass `true`, clear caches, and assert the gate flipped before testing it:

  ```php
  assign_capability('local/example:view', CAP_PROHIBIT, $roleid, $context->id, true);
  accesslib_clear_all_caches_for_unit_testing();
  $this->assertFalse(has_capability('local/example:view', $context, $user));
  ```

- **Ids from the database are strings.** `$cm->id`, record ids and `contextlist::get_contextids()` hold numeric
  strings, so `assertSame(5, $cm->id)` and `assertContains($context->id, $contextids)` fail. Fix: `assertEquals()`,
  or cast both sides with `intval`/`array_map('intval', ...)`.
- **Read core return shapes before asserting on them.** Many core `export_for_template()` results are stdClass
  objects, not arrays (`action_link` exports `$x->attributes`). Fix: open the method's `return` statement.
  Since 5.2.2, `block_myoverview` returns fields such as the course full name with numeric entities (`&#60;`) and
  unencoded quotes where earlier builds returned named ones (`&lt;`) (MDL-79755, `UPGRADING.md` of 5.2.2 and
  5.3.0). Symptom: an exact-string assertion on such a field passes on 5.2.0 and 5.2.1 and fails from 5.2.2.
  Fix: compare decoded text, `html_entity_decode($value, ENT_QUOTES | ENT_HTML5)`.
- **`isset($PAGE->cm)` is always false and `empty($PAGE->cm)` always true.** `moodle_page` has `__get()` but no
  `__isset()` (`public/lib/pagelib.php`, 5.2 and 5.3), so a guard written that way skips the branch in tests and on
  the site. Fix: read it first, `$cm = $PAGE->cm; if ($cm) { ... }`.
- **Expected timestamps come from an independent tool.** Near DST or a window boundary, a hand-computed value is
  wrong as often as the code. Paste the command in a comment; when a new test fails, decide which side is wrong
  before changing code:

  ```php
  // python3 -c "from datetime import datetime; from zoneinfo import ZoneInfo;
  //   print(int(datetime(2030, 3, 31, 9, tzinfo=ZoneInfo('Europe/London')).timestamp()))"
  ```

- **A fixture date that must be in the future is far-future or computed.** A literal that was "next year" when
  written turns the suite red with no code change. Fix: a date in 2030 or later with the same DST shape, or
  `time() + DAYSECS`, or a frozen clock.
- **Multilang in tests:** set `$SESSION->forcelang` after `setUser()`, which clears it; `force_current_language()`
  does nothing without an installed language pack.
- **Your own observers run in your tests.** A `course_deleted` observer of the plugin can delete fixtures a test
  built; an observer with `'internal' => false` runs only after commit (see the PostgreSQL reference).
- **A probe that writes attacker-shaped data is a `resetAfterTest()` test**, never a CLI script: any script that
  requires `config.php` writes to the live database.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `vendor/bin/phpunit public/local/example/tests` | "No tests executed!", exit 0 | `--testsuite local_example_testsuite` or a file path; require `Tests: N > 0` |
| Treating "OK, but there were issues" as green | CI fails on the same warning | Fix the warning or deprecation |
| No `resetAfterTest()` in a test that writes | "Warning: unexpected database modification" | Call it in `setUp()` or the test |
| `setUp()` without `parent::setUp()` | phpcs error from moodle-cs | Call the parent once, first |
| Schema change, no version bump | New table missing in tests, init says nothing | Bump `version`, or `util.php --drop` then `init.php` |
| Hand-editing `phpunit.xml` | Lost on the next init | Re-run `init.php`; pass per-run options on the command line |
| `assertSame()` on an id or context id | Fails on string versus int | `assertEquals()` or cast |
| `assign_capability()` without `$overwrite` | Prohibit silently not applied; test checks nothing | Pass `true`, clear caches, assert the flip |
| Skipping `clean_returnvalue()` | Return-structure bugs reach the web service | Always clean the external result |
| Asserting with `time()` | Flaky at second boundaries | `mock_clock_with_frozen()` or `assertTimeCurrent()` |
| Template tested through its context only | Missing `{{#str}}` key breaks the live page | Render it and assert no `[[` |
| Test passes locally on MariaDB | Fails on the PostgreSQL CI row | Read the PostgreSQL reference; treat it as unverified until that row runs |
| Test passes only in the full suite | Missing `require_once` or order dependence | Run the file alone, and the suite with `--order-by=reverse` |
| `if (empty($PAGE->cm))` | Always true: the branch never runs | Copy to a variable first |
| Mocking `$DB` or replacing the global | Tests the mock, breaks isolation | Real test rows; fake collaborators through `\core\di::set()` |
| Testing a log-store or observer effect on MariaDB only | Red on the PostgreSQL row | `preventResetByRollback()`, or assert through `redirectEvents()` |

## Reference files

| File | Read it when |
|---|---|
| [reference/generators-and-fixtures.md](moodle-skill-files/moodle-phpunit-testing/reference/generators-and-fixtures.md) | You write a plugin data generator, create activities, quiz attempts, grades, enrolments or users for a test, instantiate a block class, change module order, or back up and restore a course inside a test |
| [reference/special-testcases.md](moodle-skill-files/moodle-phpunit-testing/reference/special-testcases.md) | You test an external function, a routed controller (`route_testcase`), a privacy provider, admin settings pages, a moodleform or dynamic form, an HTTP client call, a hook listener, or core AI actions |
| [reference/postgresql-and-isolation.md](moodle-skill-files/moodle-phpunit-testing/reference/postgresql-and-isolation.md) | A test touches transactions, event observers, message processors, the log store or `perf_get_reads()`, or passes on MySQL/MariaDB and fails on PostgreSQL |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-phpunit-testing/versions/moodle-5.3.md) |

## References

- https://moodledev.io/general/development/tools/phpunit
- https://moodledev.io/docs/apis/subsystems/testing/generators (data generators)
- https://moodledev.io/general/development/policies/codingstyle (test naming and docblocks)
- `public/lib/phpunit/classes/advanced_testcase.php` (5.2 and 5.3): every helper named above
- `public/admin/tool/phpunit/cli/init.php` and `util.php` (5.2 and 5.3)
- Upgrade-specific changes: `moodle-5-3-changes`. Pre-release walk: `moodle-definition-of-done`.


---

### moodle-plugin-development

> Use when creating, modifying or reviewing any Moodle plugin (local, mod, block, format, auth, enrol, report, tool, qtype, filter, repository, tiny, availability, sub-plugins) - version.php ($plugin->version, requires, supported), db/install.xml and db/upgrade.php, db/access.php capabilities, db/services.php, db/tasks.php, db/caches.php, lang/en strings, classes/ autoloading and frankenstyle names, lib.php callbacks versus hooks, settings.php, page scripts (require_login, require_capability, sesskey, PARAM types), privacy provider, the LICENSE file, "No upgrade needed" after a db/ change, "Incorrect syntax in plugin supported declaration". Skip when the plugin is a theme (moodle-theme-development), the task is porting to another Moodle version (moodle-upgrade-migration, moodle-5-3-changes) or releasing (moodle-plugin-release), or you want the cross-topic pitfall index (moodle-field-lessons).

# Moodle plugin development

## Overview

A plugin is a directory that core maps to a frankenstyle component (`<type>_<name>`) and installs from its
`version.php`. This skill gives the mental model, a skeleton that installs and passes review, and the rules for
each `db/` file. Supported versions: Moodle 5.2 (baseline) and 5.3.

## When to Use

- Creating a plugin, or adding a table, capability, web service, task, cache, setting or page to one
- Reviewing a plugin for structure, naming, registration and coding-standard problems
- Deciding between a `lib.php` callback and a hook, or which files a plugin type needs
- **Skip when:** the plugin is a theme (`moodle-theme-development` and its siblings); you need the long list of
  non-obvious traps by topic (`moodle-field-lessons`); moving a plugin across Moodle versions
  (`moodle-upgrade-migration`, `moodle-5-3-changes`); preparing a release or a Plugins directory submission
  (`moodle-plugin-release`, `moodle-release-preflight`)

## The mental model

1. **The component name is the address.** `local_example` lives in `public/local/example/` (5.1+ layout: every
   plugin type directory is under `public/`). The type-to-directory map is `lib/plugins.json` at the Moodle root
   (5.3.0). Every global name the plugin defines (function, class, constant, table, setting, CSS class) starts
   with the component, because they all share one PHP process and one database.
2. **The numeric `$plugin->version` drives installation.** When it is higher than the value stored in
   `config_plugins`, the upgrade runs `db/upgrade.php` (or `db/install.xml` on a fresh install), then re-reads
   `db/access.php`, `db/log.php`, `db/services.php`, `db/tasks.php`, `db/messages.php` and `db/tag.php` into the
   database (`upgrade_component_updated()`) and `db/caches.php` into the cache configuration
   (`cache_helper::update_definitions()`; both in `public/lib/upgradelib.php`, 5.2 and 5.3).
   Edit one of those files without a bump and the upgrade prints "No upgrade needed"; nothing changes.
   `db/events.php` and `db/hooks.php` are read into the cache instead, so a cache purge picks them up.
3. **`classes/` is autoloaded by namespace.** `\local_example\task\cleanup` is
   `classes/task/cleanup.php`. Files outside `classes/` (`lib.php`, `locallib.php`, page scripts) are loaded
   only when something includes them.
4. **Every entry point authorises itself.** A page script, an external function and a `pluginfile` callback
   each establish login, context and capability. `require_login()` alone admits every account on the site.

## Default recipe: a skeleton that installs and survives review

```
local/example/
  LICENSE                      # full GPL v3 text; the Plugins directory blocks approval without it
  README.md                    # what it does, settings, dependencies, post-install steps
  version.php
  lang/en/local_example.php    # 'pluginname' at minimum
  classes/privacy/provider.php # null_provider if no personal data is stored
  db/                          # only the files you need: install.xml, upgrade.php, access.php, ...
  settings.php  lib.php  templates/  amd/src/  amd/build/  tests/
```

```php
<?php
// (GPL header)

/**
 * Version information.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'local_example';
$plugin->version   = 2026111600;       // YYYYMMDDXX.
$plugin->requires  = 2026042000;       // Moodle 5.2.
$plugin->supported = [502, 503];
$plugin->release   = '1.0.0';
$plugin->maturity  = MATURITY_STABLE;
```

- **`requires` is a core version number; `supported` is an inclusive pair of branch numbers.** 5.2 starts at
  `2026042000` (5.2.2+ is `2026042002.01`) and 5.3.0 is `2026100500` (`public/version.php` of each). A
  one-branch plugin says `[502, 502]`: `[502]` makes core throw `coding_exception('Incorrect syntax in plugin
  supported declaration')` whenever it loads plugin information (`public/lib/classes/plugininfo/base.php:311-320`,
  5.2 and 5.3). Keep `requires` at or above the lowest branch in `supported`.
- **`version` and `release` move separately.** Every `db/` change from mental model point 2 bumps `version`;
  `release` changes only when you cut a release (`moodle-plugin-release`).
- **`$plugin->dependencies`** takes the other plugin's `version` number, not `ANY_VERSION`, once your code
  calls something that plugin added: `['mod_quiz' => 2026042000]`.
- **`LICENSE` sits in the plugin root from the first commit.** `moodle-plugin-ci validate` does not check it and
  the Plugins directory blocks approval without it. How the ZIP is built and checked (one root folder named
  `example/`, the licence file inside it) is owned by `moodle-plugin-release`.

## db/install.xml and db/upgrade.php

- Generate `install.xml` with the XMLDB editor (Site administration > Development > XMLDB editor) and keep
  the `PREVIOUS`/`NEXT` chain intact if you edit it by hand. Table names start with the full component
  (`local_example_items`); only a `mod` may use the bare module name (`example_attempts`).
  `moodle-plugin-ci validate` checks the prefix.
- **Never write `CHAR ... NOTNULL="true" DEFAULT=""`.** XMLDB turns it into NOT NULL with no default and reports
  it only through `debugging()` on a fresh install, which aborts `moodle-plugin-ci install` while your upgraded
  site stays quiet. An optional CHAR is `NOTNULL="false"` with no default. Check while writing:
  `grep -n 'DEFAULT=""' db/install.xml` must print nothing.
- **Check each new column and table name against the reserved-word lists** in
  `public/lib/ddl/mysql_sql_generator.php`, `postgres_sql_generator.php` and `mssql_sql_generator.php`
  (`connection` is reserved on MySQL, read in 5.3.0). Renaming later touches every query.
- **Every `install.xml` change needs a matching `upgrade.php` step and a version bump.** `install.xml` runs only
  on fresh installs, so a correction without a step leaves existing sites unchanged while upgrade reports
  success. PHPUnit's `init.php` is also a no-op until some version changes.

```php
function xmldb_local_example_upgrade($oldversion) {
    global $DB;
    $dbman = $DB->get_manager();

    if ($oldversion < 2026111600) {
        $table = new xmldb_table('local_example_items');
        $field = new xmldb_field('status', XMLDB_TYPE_INTEGER, '4', null, XMLDB_NOTNULL, null, '0', 'name');
        if (!$dbman->field_exists($table, $field)) {
            $dbman->add_field($table, $field);
        }
        upgrade_plugin_savepoint(true, 2026111600, 'local', 'example');
    }
    return true;
}
```

- Write each step so it can run twice: DDL is not transactional on MySQL and MariaDB, so a step that dies
  halfway leaves the first changes in place (guard with `field_exists()`, `index_exists()`, `table_exists()`).
- Do not call grade, modinfo or course APIs from `upgrade.php`; queue an ad-hoc task instead. Details:
  `moodle-upgrade-migration`.
- XMLDB foreign keys are only indexes. Changing NULL-ability of a keyed field: `drop_key()`,
  `change_field_notnull()`, `add_key()`, or the upgrade throws `ddldependencyerror`.

## db/access.php

```php
$capabilities = [
    'local/example:manage' => [
        'riskbitmask'  => RISK_XSS | RISK_CONFIG,
        'captype'      => 'write',
        'contextlevel' => CONTEXT_SYSTEM,
        'archetypes'   => ['manager' => CAP_ALLOW],
    ],
];
```

- Each capability needs a lang string `$string['example:manage']`; a `mod` needs `mod/<name>:addinstance` (and
  its string) or `moodle-plugin-ci validate` fails.
- Set `riskbitmask` honestly: a capability that lets a user author HTML other users see carries `RISK_XSS`.
- `clonepermissionsfrom` replaces `archetypes`: the new capability copies every role's real grants of the source
  capability. A grant shipped by mistake is not re-derived when you fix `access.php`; existing sites keep it.

Full templates for every `db/` file (services, tasks, events, caches, messages, uninstall):
[reference/db-files.md](moodle-skill-files/moodle-plugin-development/reference/db-files.md).

## Names: frankenstyle everywhere

- Global functions, global classes and `define()` constants take the full component prefix, including helpers
  in page scripts and `cli/` scripts: `local_example_render_table()`, not `example_render_table()`. For `mod`
  the prefix is the bare module name (`example_add_instance()`). `phpcs` checks only the case of function names,
  and the Plugins directory treats a missing prefix as an approval blocker. Better: put helpers in a class under
  `classes/`.
- Settings are stored in `config_plugins`: name them `local_example/settingname` in `settings.php`, read with
  `get_config('local_example', 'settingname')`, write with `set_config('settingname', $v, 'local_example')`.
- CSS selectors in `styles.css` are scoped to the plugin (`.local_example-panel`, `.path-mod-example ...`): all
  plugins' `styles.css` files are served as one sheet on every page.

## Page scripts

```php
require_once(__DIR__ . '/../../config.php');

$id = required_param('id', PARAM_INT);
$course = get_course($id);
$context = \core\context\course::instance($course->id);

require_login($course);
require_capability('local/example:manage', $context);

$PAGE->set_url(new moodle_url('/local/example/manage.php', ['id' => $id]));
$PAGE->set_context($context);
$PAGE->set_title(get_string('pluginname', 'local_example'));

if (optional_param('delete', 0, PARAM_INT) && confirm_sesskey()) {
    // State change here, then redirect.
}

echo $OUTPUT->header();
echo $OUTPUT->footer();
```

- Read input only through `required_param()` / `optional_param()` with the narrowest type that fits
  (`PARAM_INT`, `PARAM_ALPHANUMEXT`, `PARAM_COMPONENT`, `PARAM_NOTAGS`). A `PARAM_RAW` or `PARAM_RAW_TRIMMED`
  needs a comment saying why and where the value is escaped; reviewers flag every unexplained one.
- `require_login()` is not authorisation: name the capability each page and each sibling action needs, and give
  sibling actions (edit, delete, react, pin) the same checks as the main one.
- `confirm_sesskey()` with no argument reads `required_param('sesskey')` and throws `missingparam` when the request
  has none (`public/lib/sessionlib.php`, 5.3.0); call it only on requests that carry one.
- Temporary directories come from `make_temp_directory('local_example/x')` or `make_request_directory()`; a
  literal `mkdir($dir, 0777, true)` ignores `$CFG->directorypermissions` and is flagged in review.
- Outbound HTTP goes through core's `\curl` class so the site proxy and `curlsecurityblockedhosts` apply; if you
  must use raw cURL, say in the setting's description that the proxy is not used.

Settings pages (`settings.php` for each plugin type, external pages behind a custom capability) and more page
patterns: [reference/settings-and-pages.md](moodle-skill-files/moodle-plugin-development/reference/settings-and-pages.md).

## Lang strings

- `lang/en/<component>.php` is data only: `$string['key'] = 'Value';` lines, sorted by key (phpcs
  `moodle.Files.LangFilesOrdering`). Only `lang/en` ships; translations go through AMOS.
- Strings core asks for by convention: `pluginname` (every plugin; filters also `filtername`), one
  `cachedef_<name>` per `db/caches.php` definition, one `<type>/<name>:<cap>` per capability,
  `privacy:metadata...` for the privacy provider, `messageprovider:<name>` per `db/messages.php` entry, and
  `modulename`/`modulenameplural`/`pluginadministration` for a `mod`. A missing one passes every automated gate
  and shows as `[[key]]` on the page.
- `{$a}` versus `{$a->name}` must match what the caller passes; nothing checks it. Placeholder rules, multilang
  and spelling: `moodle-field-lessons` (its output and lang strings reference).

## lib.php callbacks and hooks

- On 5.2 and 5.3 most output and navigation extension points are hooks (`db/hooks.php`, `\core\hook\...`). A
  legacy callback that a hook replaces is still called but emits a deprecation `debugging()`, which fails a
  `--fail-on-warning` CI run ("Callback ... should be migrated to new hook callback", `public/lib/moodlelib.php`,
  5.3.0). When the same plugin also registers the replacing hook, core skips the old callback
  (`\core\hook\manager::is_deprecating_hook_present()`), so both can coexist for older branches. See
  `moodle-hooks-api` for the list and the migration.
- Callbacks with no hook replacement are still normal `lib.php` functions: `<component>_pluginfile()`,
  `local_<name>_extend_navigation(global_navigation $nav)`, `<component>_extend_settings_navigation()`,
  `<modname>_supports()`, `<modname>_add_instance()` and the reset and grading callbacks.
- `core\hook\navigation\secondary_extend` is dispatched only when the course secondary navigation is built
  (`public/lib/classes/navigation/views/secondary.php`, 5.3.0). To add to an activity page's More menu from a
  non-activity plugin, use `<component>_extend_settings_navigation()` and the `modulesettings` node.

## Output, blocks and privacy

- HTML comes from templates (`$OUTPUT->render_from_template('local_example/panel', $data)`) or a renderer in
  `classes/output/renderer.php` extending `plugin_renderer_base`. User text is escaped at the sink: `s()` for
  plain text, `format_string()` for names, `format_text()` for rich text. `html_writer::tag()` escapes attributes,
  not contents.
- In a block class use `$this->page`, never `global $PAGE`; the moodle-cs sniff for blocks rejects the global.
- Every plugin declares privacy. With no personal data:

```php
namespace local_example\privacy;

class provider implements \core_privacy\local\metadata\null_provider {
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

  With personal data, implement the metadata, request and userlist providers (`moodle-privacy-gdpr`).

## Course lifecycle and module essentials

- A plugin that stores course- or user-scoped rows plans backup and restore (`backup/moodle2/`), course reset
  (the `_reset_course_form_definition()`, `_reset_course_form_defaults()` and `_reset_userdata()` triad), and
  `db/uninstall.php` for data outside its own tables (user preferences are not removed by core). If a table
  deliberately stays out of backups, say why in the README; reviewers accept a reasoned answer.
- Activity modules must implement backup and restore to be approved in the Plugins directory.
- Inside `<modname>_add_instance()` use `$data->coursemodule`; the `course_modules` row still has `instance = 0`,
  so any lookup by instance fails and rolls back the creation.
- Creating a module from code with core's `create_module()` (outside the test generator) needs
  `$data->introeditor = ['text' => ..., 'format' => FORMAT_HTML, 'itemid' => 0]` for any module that supports
  `FEATURE_MOD_INTRO`; without it the call throws `createmodulemissingattribut`, and `add_moduleinfo()` copies
  that array into `intro`/`introformat` (`public/course/lib.php` `create_module()`, `public/course/modlib.php`,
  read in 5.3.0).

Per-type required files, base classes and what `moodle-plugin-ci validate` demands, plus sub-plugins:
[reference/plugin-types.md](moodle-skill-files/moodle-plugin-development/reference/plugin-types.md).

## Coding standard essentials

- Every PHP file starts with `<?php` and the GPL boilerplate, has a file docblock with `@package`,
  `@copyright` and `@license`, and no closing `?>`. Non-PHP files (templates, SCSS, JS) carry the boilerplate too;
  phpcs only checks PHP.
- `defined('MOODLE_INTERNAL') || die();` belongs only in files that run code when included (`version.php`,
  `lib.php`, `db/*.php`, `settings.php`); class files under `classes/` do not have it. phpcs decides: run
  `vendor/bin/phpcs --standard=moodle path/to/plugin` and fix what it reports, including in files copied from
  another plugin.
- Code adapted from another author keeps that author's `@copyright` line above yours.
- After installing a change on a site: run the upgrade, then purge caches. A new class file returns 500 on the
  site until the class map cache is rebuilt, even though PHPUnit is green.

```bash
php admin/cli/upgrade.php --non-interactive
php admin/cli/purge_caches.php
php public/admin/tool/phpunit/cli/init.php
vendor/bin/phpunit --testsuite local_example_testsuite
```

Core CLI stays in `admin/cli/` at the Moodle root; the PHPUnit and Behat tools are under `public/admin/tool/`
(5.2 and 5.3).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `db/services.php` or `db/tasks.php` edited, no version bump | "No upgrade needed"; function or task never registered | Bump `version`; check `external_function_info($name, IGNORE_MISSING)` |
| `$plugin->supported = [502];` | `coding_exception` on every plugin list | `[502, 502]` |
| `CHAR NOTNULL="true" DEFAULT=""` | `debugging()` on fresh install only; CI install aborts | `NOTNULL="false"`, no default |
| `install.xml` fixed, no upgrade step | Existing sites keep the old schema | Pair every schema change with a step |
| No `LICENSE` in the root, or ZIP root `moodle-local_x-1.0.0/` | Plugins directory blocker; `rootdirinvalid` on install | `LICENSE` in root; build the ZIP as `moodle-plugin-release` says |
| Helper `function render_x()` in a page script | Namespace collision blocker in review | Component prefix or a class |
| Page with `require_login()` only | Any account can use it | `require_capability()` per page and action |
| `PARAM_RAW` on a name or id | Review finding; unvalidated input | Narrowest `PARAM_*`, or a comment with the reason |
| `mkdir($d, 0777, true)` | Ignores site permissions | `make_temp_directory()` |
| Capability without a lang string, cache without `cachedef_` | `[[key]]` on admin pages | Add the string |
| `global $PAGE` in a block | moodle-cs error | `$this->page` |
| Lookup by instance in `add_instance()` | Creation rolled back | `$data->coursemodule` |
| Legacy callback that a hook replaced | Deprecation notice fails CI | Register the hook |

## Reference files

| File | Read it when |
|---|---|
| [reference/db-files.md](moodle-skill-files/moodle-plugin-development/reference/db-files.md) | writing or reviewing `db/services.php`, `db/tasks.php`, `db/events.php`, `db/caches.php`, `db/messages.php`, `db/uninstall.php` or an external function class |
| [reference/settings-and-pages.md](moodle-skill-files/moodle-plugin-development/reference/settings-and-pages.md) | writing `settings.php` for any plugin type, an admin external page behind a custom capability, or a page that handles a form POST |
| [reference/plugin-types.md](moodle-skill-files/moodle-plugin-development/reference/plugin-types.md) | creating a plugin of a type other than `local`, checking which files and base classes a type needs, or declaring sub-plugins |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-plugin-development/versions/moodle-5.3.md) |

## References

- Plugin types: https://moodledev.io/docs/apis/plugintypes
- Common files: https://moodledev.io/docs/apis/commonfiles and https://moodledev.io/docs/apis/commonfiles/version.php
- Frankenstyle: https://moodledev.io/general/development/policies/codingstyle/frankenstyle
- Coding style: https://moodledev.io/general/development/policies/codingstyle
- XMLDB and DDL: https://moodledev.io/docs/apis/core/dml/ddl
- Access API: https://moodledev.io/docs/apis/subsystems/access
- Privacy API: https://moodledev.io/docs/apis/subsystems/privacy
- Hooks API: https://moodledev.io/docs/apis/core/hooks
- Security guidelines: https://moodledev.io/general/development/policies/security


---

### moodle-plugin-release

> Use when releasing a Moodle plugin or theme, or submitting it to the Moodle Plugins directory (Marketplace): bumping $plugin->version vs $plugin->release, CHANGES.md and changelog entries, the LICENSE file and ZIP root folder a reviewer checks, building and listing the ZIP before upload (rootdirinvalid, "Missing plugin license file", "Use the plugin folder name as the root folder of the ZIP"), staging and tagging an annotated vX.Y.Z, pushing the branch before the tag, the moodle-release.yml workflow, replying to a Plugins directory reviewer's issue, and confirming the version landed. Skip when only bumping version for a schema change (the /moodle-bump-version command) finishing the change itself (moodle-definition-of-done), or auditing the code for what reviewers catch (moodle-release-preflight).

# Moodle Plugin Release

## Overview

A release produces three things that are checked by different people: the tagged commit (checked by CI),
the ZIP (checked by the Plugins directory reviewer and by every admin who installs it), and the listing
(read by users). CI installs the plugin from the git checkout and never sees the ZIP, so a green CI run says
nothing about the two package problems reviewers raise most: a missing licence file and a wrong ZIP root
folder. With a tag-triggered release workflow, pushing the tag publishes it, so every step before the push
is read back, not assumed.

## When to Use

- A release has been decided on and the version bump approved
- A first submission to the Moodle Plugins directory, or a resubmission after review
- Setting up tag-triggered publishing, or checking whether a pushed tag actually arrived
- A Plugins directory reviewer opened an issue and you are writing the reply (the code fix itself is
  `moodle-release-preflight`)
- **Skip when:** the change only needs a `$plugin->version` bump for a schema change (`/moodle-bump-version`),
  or QA is still open (walk `moodle-definition-of-done`, and `moodle-release-preflight` for the security and
  approval-blocker classes, first). Theme-specific release checks are in `moodle-theme-testing-release`.

## 0. Preconditions: stop if any fails

- **The bump was asked for.** A release is a decision, not a side effect of other work. Default to a patch
  (`z`) increment; a minor or major bump needs a stated reason.
- **QA is done**: `moodle-definition-of-done` walked for everything going into the release;
  `moodle-release-preflight` walked when the plugin is being submitted or its security surface changed.
- **Every step of the plugin's own CI workflow has been run locally, as written, with its flags**, and each
  exit code and output read. A look-alike local gate is a different gate: phpcs does not run the `phpdoc`
  (moodlecheck) rules, a local `grunt` with other options skips stylelint or gherkinlint, and a missing
  `@param` found by Actions after tagging costs a new release. Read the workflow first:

  ```bash
  grep -n 'moodle-plugin-ci' .github/workflows/*.yml
  ```

  The command-by-command recipe and each command's exit-code traps (`phpmd` always returns 0, which commands
  take `--max-warnings`) are owned by `moodle-definition-of-done`.
- **A gate that runs only after the tag is pushed cannot fix that tag.** Anything that validates the release
  itself (a listing or metadata check, a packaging script, a release preview) runs before tagging.

## 1. `version.php`: two different numbers

```php
$plugin->component = 'local_myplugin';
$plugin->version   = 2026111600;          // YYYYMMDDXX build number: must strictly increase.
$plugin->release   = '1.4.2';             // Human release name: bumped deliberately.
$plugin->requires  = 2026042000;          // Lowest Moodle build: here 5.2.0.
$plugin->supported = [502, 503];          // Range [low, high] of Moodle branches.
$plugin->maturity  = MATURITY_STABLE;
```

| Number | When it changes | Rule |
|---|---|---|
| `version` | Any schema, upgrade, capability, cache-definition or service change must bump it; every release bumps it | Strictly greater than every shipped value |
| `release` | Only when cutting a release | Does not ride along with a schema bump; patch by default |

- `supported` must be a two-integer range, low first. `[502]` throws `coding_exception` "Incorrect syntax in
  plugin supported declaration" when the plugin is loaded; write `[502, 502]` for one branch
  (`\core\plugininfo\base::load_disk_version()`, `public/lib/classes/plugininfo/base.php`, 5.2 and 5.3.0).
- `requires` is not below the lowest branch in `supported`, or the plugin claims a branch it refuses to
  install on. 5.2.0 is build `2026042000` and 5.3.0 is `2026100500` (`$version` in `public/version.php` at the
  `v5.2.0` and `v5.3.0` tags). Use the `x.y.0` build, not the value of the tree you develop on: a 5.2.2 tree
  says `2026042002.01`, which locks out 5.2.0 and 5.2.1 sites.
- The directory reads the release name, maturity and supported versions from the uploaded ZIP; they can be
  overridden per version but default to what `version.php` says
  (https://moodledev.io/general/community/plugincontribution/pluginsdirectory/api, which documents the older
  moodle.org web service).

## 2. Release notes and docs: one consistent story

- `CHANGES.md` (if the plugin uses it): this version's notes only, replacing the previous body. The release
  workflow of section 6 submits the whole file as the version's release notes: it takes, in order, its
  `release_notes` input, the body of the GitHub Release for the tag, then the first of `CHANGES.md`,
  `CHANGES.txt`, `CHANGES.html`, `CHANGES`, `CHANGELOG.md` (and the same variants) or `UPGRADING.md` in the
  repository root (`moodlehq/moodle-plugin-release`, workflow revision 2026091801, read, not run). When neither
  the input nor a GitHub Release supplies the notes, a cumulative changelog with no `CHANGES.md` beside it is
  published in full on every version.
- `changelog.md` / `CHANGELOG.md`: prepend `## [x.y.z] - YYYY-MM-DD` with `### Added / Changed / Fixed /
  Security` (Keep a Changelog). Keep the file name the repository already uses.
- `README.md`: supported Moodle versions match `$plugin->supported`; requirements, settings and
  post-install steps match the code.
- **Write the notes against the previous release, not the previous commit.** A list built from the last
  commit misses everything merged since the last tag. Generate the raw list from the tag:

  ```bash
  prev=$(git describe --tags --abbrev=0 HEAD^)
  git log --oneline "$prev"..HEAD
  git diff --stat "$prev"..HEAD
  ```

- **A note claims only checks that were run**, on this commit, by name ("PHPUnit 42 tests on 5.3.0"), never
  "fully tested".
- **Manuals and translations are release artifacts.** A user manual or help page that names a renamed or
  removed setting, field or page is updated in the same release; a removal is the dangerous case, because the
  doc becomes wrong rather than incomplete. A translation kept outside the release (for AMOS) is diffed against
  `lang/en` at each release; recipe in [reference/zip-package.md](moodle-skill-files/moodle-plugin-release/reference/zip-package.md).

## 3. The package: what the reviewer checks first

Most review findings on Plugins directory submissions are about the ZIP, not the code, and no CI step can
see them. Build the ZIP, list it, and fix the repository before tagging.

- **A licence file in the plugin root.** The submission guidelines require the package to include a licence
  file; its absence is an approval blocker ("Missing plugin license file", priority blocker). `moodle-plugin-ci
  validate` requires only `version.php`, the lang file and, for a theme, `config.php`, so CI stays green
  without it. Fix: commit the full licence text as `LICENSE` in the repository root (GPL v3 text for a plugin
  that adapts Moodle code, which a Boost child theme does), make sure `.gitattributes` does not
  `export-ignore` it, and push it before the tag. A licence file added after the tag, or committed but not
  pushed, is still missing from the reviewed ZIP.
- **One root folder, named after the plugin without its type.** `local_myplugin` ships as `myplugin/`,
  `mod_forum` as `forum/`, `theme_mytheme` as `mytheme/`. A GitHub source archive has the root
  `moodle-local_myplugin-1.4.2/`. Core's validator requires a single root directory whose name survives
  `clean_param(..., PARAM_PLUGIN)` ("rootdirinvalid" otherwise) and equals the name part of
  `$plugin->component` ("componentmismatchname") (`\core\update\validator::validate_files_layout()` and
  `validate_version_php()`, `public/lib/classes/update/validator.php`, 5.3.0, identical in 5.2). Core's own
  help string names GitHub archives as the usual cause (`public/lang/en/plugin.php`,
  `validationmsg_rootdirinvalid_help`). The admin upload page can rename the
  root while extracting when it detects the component from `version.php`, so a wrong root sometimes installs
  through the UI; it still fails for an admin who unzips into `local/` by hand, and reviewers flag it every
  time.
- **Build it with `git archive` from the tag, then list it**:

  ```bash
  name=myplugin                                   # component local_myplugin
  git archive --format=zip --prefix="$name/" -o "../$name.zip" v1.4.2
  unzip -Z1 "../$name.zip" | cut -d/ -f1 | sort -u                       # prints only: myplugin
  unzip -Z1 "../$name.zip" | grep -xE "$name/(LICENSE|version\.php)"     # prints both
  unzip -Z1 "../$name.zip" | grep -E '(^|/)(node_modules|\.git|\.github)/' # prints nothing
  ```

  Then read the whole listing once: `lang/` holds only `en/`, `amd/build/` is present and current when
  `amd/src/` exists, no build output, logs or editor files. `.gitattributes` `export-ignore` lines decide what
  `git archive` leaves out; full checklist in [reference/zip-package.md](moodle-skill-files/moodle-plugin-release/reference/zip-package.md).
- **Only `lang/en/` ships.** Other languages reach sites through AMOS after approval, and an installed AMOS
  language pack overrides a plugin's bundled `lang/xx` strings key by key, so a bundled translation is both
  against the guidelines and silently shadowed. The repository-level check is in `moodle-release-preflight`.
- **Bundled third-party code, fonts and icons are declared in `thirdpartylibs.xml`.** The guidelines require
  it; it also takes those paths out of `moodle-plugin-ci`'s analysis commands. Format in
  [reference/zip-package.md](moodle-skill-files/moodle-plugin-release/reference/zip-package.md).
- **The ZIP works out of the box.** Admins must not need Composer, npm or a build step: compiled `amd/build`
  files are committed, `vendor/` code the plugin needs is shipped and declared.

## 4. Stage by path, commit, read back, tag

Other work may be sitting in the tree. Stage named paths, never `git add -A`, and re-read
`git status --porcelain` just before staging; investigate any file you did not expect rather than sweeping it
in or deleting it. "Everything is new" on a first commit is not an exception, and `.gitignore` is not a
substitute for reading the list.

```bash
git add version.php CHANGES.md CHANGELOG.md README.md
git commit -m "Release 1.4.2: <one-line summary>"
git show --stat HEAD                       # the file list must match the release notes
git tag -a v1.4.2 -m "1.4.2: <one-line summary>"
git describe --tags --exact-match HEAD     # the tag is on the commit you just read
```

If the read-back surprises you before anything is pushed, delete the local tag and fix the commit. Once a
tag or a commit may be on the remote, the rules change: see section 5.

## 5. Push: the branch first, the tag after its CI run is green

1. Push the branch only: `git push origin main`.
2. Wait for that commit's CI run and read its result. A local pass on a development site with extra plugins
   is not the same run: the CI site has only standard plugins, other databases and other PHP versions.
3. Push the one tag: `git push origin v1.4.2`.

- **Tag only a commit whose CI run is green.** If the commit is already pushed and red, fix it in a new
  commit and tag that one.
- **Never move or re-create a tag that may be published.** A tag the release workflow saw has already been
  sent to the Plugins directory, and other clones have it. Read the remote first, over the network, not from
  memory or an old note:

  ```bash
  git ls-remote origin 'refs/tags/v1.4.2*'     # any output: the tag is published
  git fetch origin && git branch -r --contains HEAD   # any output: the commit is pushed, never amend it
  ```

  New work goes into the next version. A failed remote read (authentication, network) is not evidence that the
  tag is absent. Detail in [reference/fixing-a-release.md](moodle-skill-files/moodle-plugin-release/reference/fixing-a-release.md).
- **Push at most three tags per `git push`.** GitHub creates no push event when one push updates more than
  three tags, so no tag-triggered workflow runs and nothing is published
  (GitHub's "Events that trigger workflows" page, `push` event:
  https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#push).
  Never `git push --tags` for a batch; one tag per push is the safe habit.
- **When someone else runs the push, say what it does**: "pushing tag v1.4.2 publishes it to the Moodle
  Plugins directory". They can then hold the tag back if they meant to push only the branch.

## 6. Publishing with GitHub Actions

Moodle HQ's reusable workflow publishes a release when a `v*` tag is pushed:

```yaml
# .github/workflows/moodle-release.yml
name: Release Plugin version to Moodle Marketplace
on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag to be released (e.g. v1.4.0)'
        required: true
jobs:
  release-to-marketplace:
    uses: moodlehq/moodle-plugin-release/.github/workflows/moodle-release.yml@main
    with:
      tag: ${{ inputs.tag }}
    secrets:
      MOODLE_MARKETPLACE_TOKEN: ${{ secrets.MOODLE_MARKETPLACE_TOKEN }}
```

- The plugin must already be approved in the directory. **The first submission is always a hand-built ZIP**
  (section 3), because the workflow can only add versions to an existing plugin.
- **The workflow builds the same ZIP as section 3.** It checks out the tag, reads `$plugin->component` from
  `version.php`, and runs `git archive --format=zip --prefix="<name>/" HEAD` with the type prefix removed
  (workflow revision 2026091801, read, not run). So `.gitattributes` `export-ignore` lines and uncommitted
  files affect the published ZIP exactly as they affect a hand-built one, and a wrong `component` line stops
  the run.
- The token is created on the Moodle Marketplace under "Account Settings > Security"
  (https://marketplace.moodle.com/account/security), shown once, and stored as the repository secret
  `MOODLE_MARKETPLACE_TOKEN` (the workflow's README). The moodledev.io Plugins directory API page still
  describes the older moodle.org "Plugins > API access" token, which this workflow does not use. Never put a
  token in a URL or an echoed argument in a workflow; mask a computed secret with `echo "::add-mask::$value"`
  before using it.
- A red run usually means a missing or expired token secret. Fix the secret, then re-run with
  `workflow_dispatch` and the tag; do not re-tag.
- The tag-push run uses the workflow file in the tagged tree. If that file was broken, fix it on the default
  branch and dispatch the run there with the tag as input; never move the tag. (Reasoned from GitHub's
  documented event behaviour, not run.)

## 7. A pushed tag is not a published release

Confirm ingestion downstream. These are anonymous HTTPS reads; a successful read is evidence, a failed one is
not a "no".

- **Plugins directory**: the release workflow run went green, then the version is in the public plugin list.
  The plugin page fills version numbers in by script, so grepping its HTML finds nothing:

  ```bash
  curl -fsSL https://download.moodle.org/api/1.3/pluglist.php | python3 -c '
  import json, sys
  p = [x for x in json.load(sys.stdin)["plugins"] if x["component"] == "local_myplugin"][0]
  print(sorted((v["version"], v["release"]) for v in p["versions"])[-3:])'
  ```

  The endpoint a site itself asks when it installs or updates the plugin is `pluginfo.php`, which answers 404
  for a version it does not know (`\core\update\api::get_plugin_info()` and `call_pluginfo_service()`,
  `public/lib/classes/update/api.php`, 5.2 and 5.3.0; read, not run for this skill):

  ```bash
  curl -s -o /dev/null -w '%{http_code}\n' \
    'https://download.moodle.org/api/1.3/pluginfo.php?plugin=local_myplugin@2026111600&format=json'   # 200
  ```

- **Packagist** (if the plugin has `composer.json`): the newest version Composer clients will see. Until this
  prints the new tag, no client-side cache clearing helps. Packagist offers only `dev-main` until a tag
  exists whose tree contains `composer.json`.

  ```bash
  curl -s https://repo.packagist.org/p2/<vendor>/<package>.json \
    | python3 -c "import json,sys;d=json.load(sys.stdin);k=list(d['packages'])[0];print(d['packages'][k][0]['version'])"
  ```

- `moodle/composer-installer` places a package by its `type` (`moodle-local`, `moodle-mod`, ...) and knows only
  the plugin types in its own data, so a sub-plugin of a third-party parent stops with "Unable to install
  package of type ..., unknown plugin type ..." until the installer adds that type (read in its
  `src/Composer/MoodleInstaller.php` and `DataProviders/ContribData.php`, not run). Say so in the README.

Record the release as "committed and tagged, push pending" until the push is confirmed, never as pushed.

## 8. The first submission and the listing

The listing is reviewed with the ZIP. What the submission guidelines require, and what nothing automated
checks, is in [reference/plugins-directory-submission.md](moodle-skill-files/moodle-plugin-release/reference/plugins-directory-submission.md): a public
issue tracker (required for approval), a short and a full description, screenshots, documentation URL, the
licence named on the page, dependencies and post-install steps stated in both the description and the
README, and demo credentials for any external service.

- **Publication material is checked like code.** Every tool or command the text recommends is current;
  every claim about users or sites is one you can support; every screenshot is read for its proper nouns
  (course, user and site names), which must be demo data you chose, not test leftovers.
- **Put a README caveat where admins read it too.** A limitation stated only in the README (for example that a
  feature does not use the site proxy) still gets raised in review; repeat it in the setting's description
  string.

## 9. Answering a Plugins directory reviewer

Reviewers file each finding as an issue on the plugin's tracker, with a priority and sometimes an
"Approval blocker" label. Answer on the issue:

- Name the release and commit that fixes it, say what changed, and say what you found when you looked for the
  same defect elsewhere in the plugin (reviewers report one instance; a second one in a CLI script or a sibling
  action is common).
- **A reasoned no is accepted.** When a suggestion does not fit, say exactly why. Two kinds of refusal have been
  approved without a code change: a narrower `PARAM_*` type that would corrupt valid input (`PARAM_USERNAME`
  strips `+`, `PARAM_ALPHANUMEXT` strips the dot in `5.2`), and course-scoped operational records deliberately
  left out of backup and restore, with the reason written in the README.
- **Verify a suggested fix before applying it.** Test the suggested type or API against real values first.
  Documentation links in reviews often point at an older Moodle version's page; read the page for your
  supported branch.
- Code-level findings (frankenstyle prefixes, `PARAM_RAW`, capabilities, directory permissions, caching) are
  `moodle-release-preflight`'s checks; run them before submitting.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No `LICENSE` in the repository root, or export-ignored | Approval blocked: "Missing plugin license file"; CI green | Commit the full text as `LICENSE`; list the ZIP |
| ZIP from GitHub's "Source code" download | Root `moodle-local_x-1.0.0/`: `rootdirinvalid`, reviewer finding | `git archive --prefix=<name>/` from the tag |
| Licence added after the tag | The reviewed ZIP still lacks it | Push it before tagging; release a new version |
| `release` bumped with every schema change | Release names drift from real releases | Bump `version` for schema; `release` only when releasing |
| Tagging after phpcs alone | CI fails `phpdoc` or stylelint after the tag is public | Run every step of the plugin's CI workflow first |
| `git add -A` for the release commit | Unrelated files shipped and tagged | Stage named paths; read `git show --stat` |
| Tag pushed with the branch | Published before CI ran; a red tag cannot be unpublished | Branch, green CI, then the tag |
| Moving a published tag to add a fix | Clones and the directory disagree on what the version is | New commit, new version |
| `git push --tags` with 4+ new tags | No workflow runs, nothing published | At most three tags per push; one is safer |
| `$plugin->supported = [502]` | `coding_exception` on load | `[502, 502]` |
| Notes written from the last commit | Changes since the previous tag missing | `git log <prevtag>..HEAD` |
| Treating a pushed tag as released | Users cannot see the version; time lost on caches | Workflow run, plugin list API, Packagist p2 JSON |
| Applying a reviewer's suggested type unchecked | Valid input corrupted | Test it; answer with a reasoned no if it does not fit |

## Reference files

| File | Read it when |
|---|---|
| [reference/zip-package.md](moodle-skill-files/moodle-plugin-release/reference/zip-package.md) | Building the ZIP by hand (first submission), writing `.gitattributes`, declaring bundled libraries or fonts in `thirdpartylibs.xml`, diffing a translation against `lang/en`, or debugging a "rootdirinvalid" or "componentmismatchname" install error |
| [reference/plugins-directory-submission.md](moodle-skill-files/moodle-plugin-release/reference/plugins-directory-submission.md) | Submitting a new plugin, filling in or changing the listing, preparing screenshots, or deciding what a reviewer will raise that CI does not check |
| [reference/fixing-a-release.md](moodle-skill-files/moodle-plugin-release/reference/fixing-a-release.md) | A tag already exists and something in that release is wrong, a release workflow run failed, or you are unsure whether a commit or tag is on the remote |

## References

- Version file: https://moodledev.io/docs/apis/commonfiles/version.php
- Third-party libraries: https://moodledev.io/docs/apis/commonfiles/thirdpartylibs.xml
- Plugins directory web service (the older moodle.org API): https://moodledev.io/general/community/plugincontribution/pluginsdirectory/api
- Marketplace API, as linked from the release workflow's README: https://moodledev.io/general/community/plugincontribution/moodlemarketplaceapi
- Release workflow: https://github.com/moodlehq/moodle-plugin-release
- Moodle Marketplace plugin submission guidelines: https://moodle.atlassian.net/wiki/external/ODRhYjAyNTY4NDVmNGJlNjljN2ViMzkwYzdmYmIwMGI
- moodle-plugin-ci: https://moodlehq.github.io/moodle-plugin-ci/
- See also: `moodle-definition-of-done`, `moodle-release-preflight`, `moodle-ci-matrix`, `moodle-theme-testing-release`


---

### moodle-privacy-gdpr

> Use when writing, reviewing or testing a Moodle plugin's privacy provider (classes/privacy/provider.php), adding a table, user preference, file area or external API call that holds personal data, or when the Plugin privacy registry says "Requires attention" or "Userlist provider missing". Covers null_provider vs metadata provider plus request\plugin\provider, get_metadata (add_database_table, add_subsystem_link, add_external_location_link, add_user_preference), get_contexts_for_userid, get_users_in_context, export_user_data, delete_data_for_all_users_in_context, delete_data_for_user, delete_data_for_users, core_userlist_provider, user_preference_provider, exporting and deleting files, comments, ratings and tags through core's helpers, activity and subplugin providers, and provider_testcase tests. Skip when auditing request handling for security (moodle-security-audit), running the whole pre-release audit (moodle-release-preflight), or declaring a theme's user preferences (moodle-theme-settings).

# Moodle Privacy / GDPR

## Overview

Every plugin ships `classes/privacy/provider.php`. The provider declares what personal data the plugin holds and
implements export and erasure for it, so that the privacy tool (`tool_dataprivacy`) can answer a data request and
apply retention. The privacy API is the same on 5.2 and 5.3 (`public/privacy/` is identical apart from
`phpunit.xml`, read in the source).

## When to Use

- Creating a plugin (every plugin needs a provider, even one that stores nothing)
- Adding or renaming a table, a user preference, a file area, or a call that sends user data to another system
- Reviewing a provider before a release or a Plugins directory submission
- The Plugin privacy registry (Site administration > Users > Privacy and policies) flags the plugin
- **Skip when:** auditing pages, web services and output for security (`moodle-security-audit`); running the full
  pre-release defect audit (`moodle-release-preflight`, whose class 4 points back here)

## How the privacy API works

- **`\core_privacy\manager` drives everything.** It finds `\<component>\privacy\provider` for every installed
  component and calls the interface methods. Nothing else in core calls your provider.
- **Compliant means one of two things** (`manager::component_is_compliant()`, `public/privacy/classes/manager.php`,
  5.3.0): the class implements `\core_privacy\local\metadata\null_provider`, or it implements
  `\core_privacy\local\metadata\provider` **and** a `\core_privacy\local\request\data_provider` (in practice
  `request\plugin\provider`, `request\user_preference_provider`, or a subplugin interface). A metadata provider
  alone is not compliant. The registry shows a non-compliant plugin as "Requires attention."
  (`public/admin/tool/dataprivacy/lang/en/tool_dataprivacy.php`, 5.3.0).
- **`request\plugin\provider` needs `request\core_userlist_provider` too.** Core's
  `test_userdata_provider_implements_userlist` fails without it, and the registry says "Userlist provider
  missing". `user_preference_provider` alone does not need it.
- **Export:** the user's contexts come from `get_contexts_for_userid()`; the admin approves them; the manager
  passes an `approved_contextlist` (one user, one component, those contexts) to `export_user_data()`.
- **Erasure has three entry points**, all of which must remove the same data:
  - `delete_data_for_user(approved_contextlist)`: one user, several contexts (a deletion request).
  - `delete_data_for_users(approved_userlist)`: several users, one context (retention expiry per user). The users
    come from `get_users_in_context()`.
  - `delete_data_for_all_users_in_context(\context)`: everything in a context (retention expiry of the context).
    The manager calls it **for every component** on that context (`manager::delete_data_for_all_users_in_context()`),
    so a context that is not yours arrives here too.
- **After your method, core removes what it owns for you:** the activity completion data of module contexts,
  and nothing else (`request\helper::delete_data_for_user()`, `public/privacy/classes/local/request/helper.php`,
  5.3.0).
  Your own tables, files, comments, ratings and tags are yours to remove.

## Choose the interfaces

| The plugin stores | Implement |
|---|---|
| No personal data at all (only events, which log stores cover) | `metadata\null_provider` with `get_reason()` |
| Only site-wide user preferences | `metadata\provider` + `request\user_preference_provider` |
| Rows in its own tables, files, comments, ratings or tags keyed to users | `metadata\provider` + `request\plugin\provider` + `request\core_userlist_provider` |
| Context-specific preferences | All three above, plus `user_preference_provider` for any site-wide ones; the per-context ones are exported and deleted as context data |
| Data it only sends elsewhere (an API, an AI service) | `metadata\provider` with `add_external_location_link()` + `request\plugin\provider` + `core_userlist_provider` with empty methods |
| Data inside a parent plugin (an `assignsubmission_` plugin) | `metadata\provider` + the parent's subplugin interface: [reference/activities-and-subplugins.md](moodle-skill-files/moodle-privacy-gdpr/reference/activities-and-subplugins.md) |

The devdocs FAQ suggests a metadata provider alone for data sent only to another subsystem; by
`component_is_compliant()` that is not compliant, and core's `test_all_providers_compliant` asserts exactly that
method (read in the 5.3.0 source, not run on such a plugin). Use `null_provider` when the only trace is in the
logs.

## Null provider

```php
// (GPL header)
namespace local_example\privacy;

class provider implements \core_privacy\local\metadata\null_provider {
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

`$string['privacy:metadata'] = 'The Example plugin does not store any personal data.';` Core's
`test_null_provider` calls `get_string()` on the reason.

A null provider is wrong when the plugin has any table with a `userid` column or a foreign key to `user.id`:
core's `test_table_coverage` lists every such table in `db/install.xml` that no metadata provider declares
(`public/privacy/tests/privacy/provider_test.php`, 5.3.0). Columns such as `usermodified` with no key are not
detected by that test, and still count as personal data.

## Default recipe: a plugin with its own table and a file area

```php
// (GPL header)
namespace local_example\privacy;

use core_privacy\local\metadata\collection;
use core_privacy\local\request\approved_contextlist;
use core_privacy\local\request\approved_userlist;
use core_privacy\local\request\contextlist;
use core_privacy\local\request\transform;
use core_privacy\local\request\userlist;
use core_privacy\local\request\writer;

class provider implements
    \core_privacy\local\metadata\provider,
    \core_privacy\local\request\plugin\provider,
    \core_privacy\local\request\core_userlist_provider {

    public static function get_metadata(collection $collection): collection {
        $collection->add_database_table('local_example_items', [
            'userid' => 'privacy:metadata:items:userid',
            'content' => 'privacy:metadata:items:content',
            'timecreated' => 'privacy:metadata:items:timecreated',
        ], 'privacy:metadata:items');
        $collection->add_subsystem_link('core_files', [], 'privacy:metadata:core_files');
        return $collection;
    }

    public static function get_contexts_for_userid(int $userid): contextlist {
        $sql = "SELECT ctx.id
                  FROM {local_example_items} i
                  JOIN {context} ctx ON ctx.instanceid = i.courseid AND ctx.contextlevel = :courselevel
                 WHERE i.userid = :userid";
        $contextlist = new contextlist();
        $contextlist->add_from_sql($sql, ['courselevel' => CONTEXT_COURSE, 'userid' => $userid]);
        return $contextlist;
    }

    public static function get_users_in_context(userlist $userlist): void {
        $context = $userlist->get_context();
        if (!$context instanceof \core\context\course) {
            return;
        }
        $userlist->add_from_sql('userid', 'SELECT userid FROM {local_example_items} WHERE courseid = :courseid',
            ['courseid' => $context->instanceid]);
    }

    public static function export_user_data(approved_contextlist $contextlist): void {
        global $DB;
        $userid = $contextlist->get_user()->id;
        foreach ($contextlist->get_contexts() as $context) {
            if (!$context instanceof \core\context\course) {
                continue;
            }
            $rows = $DB->get_records('local_example_items', ['courseid' => $context->instanceid, 'userid' => $userid]);
            foreach ($rows as $row) {
                $subcontext = [get_string('pluginname', 'local_example'), $row->id];
                writer::with_context($context)
                    ->export_data($subcontext, (object) [
                        'content' => writer::with_context($context)->rewrite_pluginfile_urls(
                            $subcontext, 'local_example', 'attachment', $row->id, $row->content),
                        'timecreated' => transform::datetime($row->timecreated),
                    ])
                    ->export_area_files($subcontext, 'local_example', 'attachment', $row->id);
            }
        }
    }

    public static function delete_data_for_all_users_in_context(\context $context): void {
        global $DB;
        if (!$context instanceof \core\context\course) {
            return;
        }
        get_file_storage()->delete_area_files($context->id, 'local_example', 'attachment');
        $DB->delete_records('local_example_items', ['courseid' => $context->instanceid]);
    }

    public static function delete_data_for_user(approved_contextlist $contextlist): void {
        $userid = (int) $contextlist->get_user()->id;
        foreach ($contextlist->get_contexts() as $context) {
            if ($context instanceof \core\context\course) {
                self::delete_items($context, [$userid]);
            }
        }
    }

    public static function delete_data_for_users(approved_userlist $userlist): void {
        $context = $userlist->get_context();
        if ($context instanceof \core\context\course) {
            self::delete_items($context, $userlist->get_userids());
        }
    }

    /** One delete path, so the three entry points cannot drift apart. */
    private static function delete_items(\context $context, array $userids): void {
        global $DB;
        if (!$userids) {
            return;
        }
        [$insql, $params] = $DB->get_in_or_equal($userids, SQL_PARAMS_NAMED);
        $params['courseid'] = $context->instanceid;
        $select = "courseid = :courseid AND userid $insql";
        $ids = $DB->get_fieldset_select('local_example_items', 'id', $select, $params);
        $fs = get_file_storage();
        foreach ($ids as $id) {
            $fs->delete_area_files($context->id, 'local_example', 'attachment', $id);
        }
        $DB->delete_records_select('local_example_items', $select, $params);
    }
}
```

Strings: one per summary and one per field identifier you pass (`privacy:metadata:items`,
`privacy:metadata:items:userid`, ..., `privacy:metadata:core_files`). Core's `test_metadata_provider` calls
`get_string()` on each and checks that each declared table exists.

## Rules

### What you declare must be what you export and delete

**Fact:** every table, field, preference, file area and external location in `get_metadata()` has an export path
and a path in all three delete methods. Nothing checks this except your own tests: core's tests check that the
declared table exists and has strings, not that the request methods touch it. **Symptom:** a declared field that
is never exported or erased is a compliance defect a reviewer finds by reading; a provider whose request
methods still query a table's old name after a rename throws `dml_exception` on the first export or erasure,
while `get_metadata()` (already updated) passes. **Fix:** route the three deletes through one helper, as in the
recipe; after any table rename, `grep -rn '<oldname>' classes/privacy`; write a provider test on generated rows
that covers all six methods. Source: `public/privacy/tests/privacy/provider_test.php` (5.3.0).

### A subsystem link declares; it does not export or delete

**Fact:** `add_subsystem_link('core_files', ...)` tells the registry that the plugin stores files. It does not
export or delete them: `\core_files\privacy\provider` handles only private-key data in the user context
(`public/files/classes/privacy/provider.php`, 5.3.0). **Symptom:** the export has no attachments, and erasure
leaves the user's files in `{files}`. **Fix:** export with `writer::with_context($ctx)->export_area_files()` (and
`rewrite_pluginfile_urls()` for text that embeds them); delete with `get_file_storage()->delete_area_files()`.
Comments, ratings and tags have their own helper calls: [reference/core-subsystems.md](moodle-skill-files/moodle-privacy-gdpr/reference/core-subsystems.md).
Only link a real subsystem: core's test asserts `core_component::is_core_subsystem()`, and there is no
`core_log` subsystem (`lib/components.json`, 5.3.0).

### Every context passed in may not be yours

**Fact:** `delete_data_for_all_users_in_context()` runs for every component on every expiring context, and
approved lists can carry context levels your plugin never uses. **Symptom:** an unguarded method deletes by the
wrong key (a module plugin deleting rows for whatever `instanceid` a course or another module's context has).
**Fix:** check the class (`instanceof \core\context\course`, `\core\context\module`) and, for a module, that the
cm is yours: `get_coursemodule_from_id('example', $context->instanceid)` returns false for another module's cm
(`public/mod/choice/classes/privacy/provider.php`, 5.3.0).

### Erasing one user touches only that user

**Fact:** `delete_data_for_user()` and `delete_data_for_users()` remove the named users' rows and files, nothing
else. **Symptom:** one erasure request deletes every user's files in a shared area (a file area keyed by
activity, not by row), or deletes the activity instance itself. **Fix:** key file areas by the row id that
belongs to one user, delete by that item id, and keep shared content (the activity, other users' replies).
Where content written by several users cannot be split, delete the personal part and keep the shared text, as
core's forum does by blanking authored fields.

### Ids come back as strings

**Fact:** `contextlist::get_contextids()` after `add_from_sql()` returns the values as the database driver gave
them, uncast (`public/privacy/classes/local/request/contextlist.php`, 5.3.0), which is a string on the MySQL,
MariaDB and PostgreSQL drivers, and `$context->instanceid` is not cast either, while `$context->id` is an int
(`public/lib/classes/context.php`, 5.3.0). Read in the source, not run. **Symptom:**
`$this->assertContains($context->id, $list->get_contextids())` fails (PHPUnit's `assertContains` is strict) and
`===` comparisons in provider code are silently false. **Fix:**
`array_map('intval', ...)` before comparing, or `assertEqualsCanonicalizing()`. `userlist::get_userids()` is
built from array keys and is int.

### User preferences

**Fact:** `add_user_preference($name, $stringid)` declares one preference; there is no wildcard, so numbered
preferences are declared one by one. `export_user_preferences(int $userid)` reads each with
`get_user_preferences($name, null, $userid)` and writes it with
`writer::export_user_preference('local_example', $name, $value, get_string(...))`, skipping a null value: the
writer's `$value` is typed `string`, so an unset preference passed through is a `TypeError`. Site-wide preferences
need no delete method. **Symptom:** a preference that is set but not declared is undeclared personal data; core's
uninstall does not remove a plugin's preferences (`uninstall_plugin()`, `public/lib/adminlib.php`, 5.3.0; the uninstall
recipe is in `moodle-definition-of-done`). **Fix:** declare and export each; a child theme declares only the
preferences it adds, not its parent's. Source: `public/theme/boost/classes/privacy/provider.php` (5.2 and 5.3).

**5.3+:** Boost also stores the colour mode as preference `theme_boost_colourmode` and declares it in its own
provider; dark mode itself is in `moodle-theme-scss`, and a theme's own preferences in `moodle-theme-settings`.

### Data sent to another system

**Fact:** a plugin that sends personal data out (an external API, an AI provider, analytics) declares it with
`add_external_location_link('<name>', ['<field>' => '<stringid>'], '<summarystringid>')` and still implements the
request interfaces, with empty methods when the data cannot be retrieved back. **Symptom:** a `null_provider` on a
plugin that posts names, emails or user text to a service is undeclared egress, and the Plugins directory
guidelines make a compliant privacy API an approval blocker for any plugin that processes personal data or
integrates with an external system. **Fix:** one external location per destination, the fields actually sent,
and the same statement in the plugin description. Source:
https://moodledev.io/docs/apis/subsystems/privacy/faq.

### Exports are readable

Use `transform::datetime()` for Unix timestamps (`transform::date()` for dates, `transform::yesno()`,
`transform::percentage()`), export language-independent ids only where they mean something to the user, put
each item in its own subcontext (`[get_string('pluginname', ...), $row->id]`), and use
`export_related_data()` for data about the item rather than its own content. Source:
`public/privacy/classes/local/request/transform.php`, `content_writer.php` (5.3.0).

## Testing

Extend `\core_privacy\tests\provider_testcase` in `tests/privacy/provider_test.php`, generate rows for two users,
and cover all six methods. Its helpers are `get_contexts_for_userid($userid, $component)`,
`export_all_data_for_user($userid, $component)` and `export_context_data_for_user($userid, $context, $component)`;
it has no delete helper (`public/privacy/classes/tests/provider_testcase.php`, 5.3.0). Assertions read the test
writer: `writer::with_context($context)->get_data([...])`, `has_any_data()`, `get_files()`. Full test and how to
run core's compliance checks for one plugin: [reference/testing.md](moodle-skill-files/moodle-privacy-gdpr/reference/testing.md).

Core's compliance tests (group `plugin_checks`) are not part of a plugin's `moodle-plugin-ci phpunit` run, which
runs only the plugin's own suite, so a missing or broken provider passes CI.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No `classes/privacy/provider.php` | Registry: "Requires attention."; core's compliance test fails | At least a `null_provider` |
| `null_provider` while a table has `userid` | `test_table_coverage` fails; data never exported or erased | Full provider |
| `metadata\provider` with no request interface | Not compliant | Add `plugin\provider` (or `user_preference_provider`) |
| `plugin\provider` without `core_userlist_provider` | "Userlist provider missing"; core test fails | Implement `get_users_in_context()` and `delete_data_for_users()` |
| A declared table or field missing from export or a delete | Compliance defect; erasure leaves data | One delete helper; a test per method |
| Provider still names a table's old name | `dml_exception` on export or erasure | Grep `classes/privacy` after every rename |
| Relying on `add_subsystem_link('core_files')` to delete files | Files survive erasure and are missing from the export | `export_area_files()`, `delete_area_files()` |
| `add_subsystem_link('core_log')` | Core test fails: no such subsystem | Nothing to declare for events |
| No context-class check in `delete_data_for_all_users_in_context()` | Deletes another component's data by a coincident id | `instanceof` check and, for a module, `get_coursemodule_from_id()` |
| One user's erasure deletes a shared file area | Other users lose their files | Key areas by the user's row id |
| Strict comparison of context ids | Test or check silently fails | `intval` them first |
| Missing `privacy:metadata:*` strings | `test_metadata_provider` fails; registry shows `[[key]]` | One string per summary and field |
| `transform::datetime()` on a non-timestamp | Nonsense dates in the export | Only for Unix timestamps |
| Expecting `provider_testcase` to delete for you | Method does not exist | Call the provider's delete methods directly |

## Reference files

| File | Read it when |
|---|---|
| [reference/core-subsystems.md](moodle-skill-files/moodle-privacy-gdpr/reference/core-subsystems.md) | The plugin stores files, comments, ratings, tags, favourites, question attempts or plagiarism data through core, and you are writing their export and delete calls |
| [reference/activities-and-subplugins.md](moodle-skill-files/moodle-privacy-gdpr/reference/activities-and-subplugins.md) | The plugin is an activity module (data in module contexts), defines subplugin types, or is a subplugin of another plugin |
| [reference/testing.md](moodle-skill-files/moodle-privacy-gdpr/reference/testing.md) | You are writing `tests/privacy/provider_test.php`, or need to run core's compliance checks against the plugin before a release |

## References

- https://moodledev.io/docs/apis/subsystems/privacy
- https://moodledev.io/docs/apis/subsystems/privacy/faq
- https://moodledev.io/docs/apis/subsystems/privacy/utils
- See also: `moodle-release-preflight` (class 4, lifecycle), `moodle-definition-of-done` (uninstall and user
  preferences), `moodle-field-lessons`


---

### moodle-release-preflight

> Use when about to tag a Moodle plugin release, submit it to the Moodle Plugins directory, fix a code finding a Plugins directory reviewer raised, or send the plugin for an external security review. A pre-release audit of the defect classes reviews caught in shipped plugins despite green CI: client-trusted ids and limits, require_login() without a capability, sibling actions that skip a rule, frozen form fields, unescaped output sinks, inline-served uploads, unclean restore and imports, settings read by name, privacy drift, reset and uninstall gaps, vacuous tests, missing frankenstyle prefixes, missing lang strings, PARAM_RAW, mkdir 0777, raw cURL, and an extended checklist (unserialize, IDOR, CSRF, noclean, SSRF, group leaks). Skip when writing new feature code (moodle-plugin-development), reviewing code for security with no release at stake (moodle-security-audit), finishing an ordinary task (moodle-definition-of-done), or building the ZIP, tagging and replying to the reviewer (moodle-plugin-release).

# Moodle Release Preflight

## Overview

A pre-release self-audit of the defect classes that Plugins directory reviewers and external security reviews
have repeatedly found in shipped Moodle plugins after `moodle-plugin-ci` passed. The goal is to find the next
instance before a reviewer does. It is narrower than `moodle-security-audit` and empirical: each class was seen
in a review, and each comes with a check and a fix. Run both before a release; they overlap at the sinks.

## When to Use

- Before tagging a release or uploading a version to the Moodle Plugins directory
- Before sending a plugin to an external security or code review
- When a Plugins directory reviewer has opened an issue and you are fixing the code and looking for the same
  defect elsewhere (how to reply is in `moodle-plugin-release`)
- Checking a change that touches request handling, uploads, output, restore, privacy or course reset before it
  goes into a release
- **Skip when:** writing new feature code (`moodle-plugin-development`), doing a broad security review
  (`moodle-security-audit`), or building, tagging and uploading the release itself (`moodle-plugin-release`)

## What green CI does not prove

`moodle-plugin-ci` tests the git checkout with the plugin's own tests. None of these is caught by it (read in
the moodle-plugin-ci 4.5 and moodle-cs 3.7 source, not run):

- **The ZIP.** CI installs from the checkout. The licence file and the ZIP's root folder, the two most common
  review findings, are never seen. Check the built ZIP with `moodle-plugin-release`.
- **Most required strings.** `validate` asks for `pluginname` (a filter: `filtername` only; an activity:
  `modulename` or `pluginname`, plus `<name>:addinstance`). `cachedef_*`, other capability strings and message
  provider strings are not checked.
- **Frankenstyle prefixes.** `validate` checks table names; `phpcs` checks global function names for lower case
  only. A missing prefix is an approval blocker.
- **Authorisation and parameter types.** `phpcs` checks that a login call follows `config.php`, not that a
  capability is required; no sniff flags `$_GET`, `$_REQUEST` or `PARAM_RAW`.
- **Privacy compliance.** Core's `test_all_providers_compliant` is not part of the plugin's PHPUnit run, so a
  missing provider passes CI (`moodle-privacy-gdpr`).
- **Empty tests.** `phpunit` and `behat` over an empty `tests/` pass. `phpmd` always exits 0.

## How to run it

Scope to the changed files, or the whole plugin for a release. The audit has seven classes, and every check in
them has its own ID (`1a` to `7j`), listed in order under **Report format**. For each check: run it, report pass,
fail or N/A with a reason, and cite evidence (file:line, grep output, a test name). "Looks fine" is not a pass.
The deliverable is the report; do not fix unless asked.

**Triage by plugin shape first,** from the file tree, not the prefix:

- **Editor (`tiny_`, `atto_`), filter, block, theme**: usually no request handlers, uploads, restore or stored
  data. Classes 1 and 3 are typically N/A, and so are 2b, 4b, 4c and 4d; focus on 2a, 4a, 5a and class 6. Prove
  N/A with a grep; do not assume.
- **`mod_`, `assignsubmission_`, `assignfeedback_`, anything with an upload endpoint, external functions or its
  own tables**: run classes 1 to 6, then 7.
- **`local_`, `tool_`, `report_`**: a `local_` with an AJAX endpoint and a table is activity-shaped (run all); a
  passive one is editor-shaped. A tool whose admins author content or import files that other users see runs 3b.

```bash
grep -rlnE "required_param|optional_param|send_(stored_)?file" --include='*.php' . ; ls backup db/install.xml 2>/dev/null
```

The positive model for classes 1 and 2b: one shared helper per plugin that loads the instance from the URL id,
calls `require_login()` and `require_capability()` (or `validate_context()` in a web service), and re-scopes every
client-supplied id to that instance.

## 1. Trust boundary: never trust what the client sends

### 1a. Submitted ids and values are re-validated

**Seen in reviews:** a report plugin took the target course from a hidden form field, and its async grade-push
task never re-checked the capability: a cross-course gradebook write. An activity trusted a client-sent "type".
Another left one id in a `<select>` un-revalidated against the menu that built it.

Check:
- Grep for request values that drive authorisation, storage or a privileged action: `required_param`,
  `optional_param`, `addElement('hidden'`, `$data->` fields from a form, external-function parameters.
- Is authorisation derived from the URL or context id, not the submitted one?
- Is every submitted id re-validated against the allowed set: the records that built the select, or an
  instance-scoped query?
- Is the capability re-checked at the async sink (scheduled or adhoc task, service call)? A tampered stored
  value executes later.

```php
$cm = get_coursemodule_from_id('myplugin', $cmid, 0, false, MUST_EXIST);
$context = context_module::instance($cm->id);
require_login($cm->course, false, $cm);
require_capability('mod/myplugin:grade', $context);

$options = $DB->get_records_menu('myplugin_accounts', ['instanceid' => $cm->instance], '', 'id, name');
if (!array_key_exists($data->accountid, $options)) {
    throw new moodle_exception('invalidaccount', 'mod_myplugin');
}
```

### 1b. `require_login()` is not authorisation

**Seen in reviews:** share and upload pages, and the web service behind them, called only `require_login()`, so
any account could upload files that a task then parsed. Each page and web service function that does more than
show users their own data names the capability it requires, with a `riskbitmask`, and the UI hides the link
without it. Command and fix: [reference/directory-review-checks.md](moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md)
section 1b.

### 1c. Sibling actions make the same checks as the main action

**Seen in reviews:** sending a message applied blocking and contacts-only privacy; reacting to and pinning a
message on the same conversation checked only membership. A blocked user could still react, and the other user
saw it with their name. No grep finds this: for each write action, list the checks its siblings make on the same
object and compare. Where the main action calls a shared check, every sibling calls it, and a PHPUnit test per
action covers the denied case.

### 1d. Client-side-only limits are advisory

**Seen in reviews:** maximum duration and size enforced only in the browser; a direct POST ignored both. For
each limit (size, duration, count, rate) grep the server endpoint for a matching guard. If the only enforcement
is in `amd/src/*.js`, it is bypassable. Enforce it on the server: `get_user_max_upload_file_size()`, a duration
probe, a `$DB->count_records()` gate.

### 1e. Two roles writing the same state value into one column

**Seen in reviews:** an owner-facing visibility toggle reused the status value moderators used for a takedown,
so authors could silently undo moderation. The readers of the column had been checked; the writers had not.

For every status, enum or flag column the change starts writing, grep every other writer:
`grep -rnE "set_field\(.*'status'|update_record|'status' *=>" --include='*.php' .`. If two privilege levels can
put a row into the same state, give each actor a distinct value (`hidden_by_moderator`, which the author setter
refuses to touch) or store the actor on the row, and confirm the privileged action is still reversible in the UI.

### 1f. Building a core form's data in code skips its freezes

**Seen in reviews:** a plugin read a core form's defaults, overlaid its own values and saved without posting the
form. Core had `hardFreeze()`d capability-gated fields for that user (`course_edit_form` freezes `visible` and
`downloadcontent`, `public/course/edit_form.php`, 5.3.0), and the overlay set them anyway; `create_course()` checks
no capability of its own. Wherever code fills a core form's data itself, skip every element where
`$mform->getElement($name)->isFrozen()` and take the pinned value from `_constantValues`. Test with a user who
lacks the gating capability.

### 1g. The question engine processes every slot the post names

`$quba->process_all_actions($timenow, $postdata)` processes the slots named in `$postdata['slots']`, or every
slot in the usage if that key is absent (`public/question/engine/questionusage.php`, 5.3.0), so a client-shaped
`$postdata` can grade every question in one request. Filter `$postdata` to the allowed slots'
`$quba->get_field_prefix($slot)` keys and set `$postdata['slots']` yourself. A regression test must include
`:sequencecheck` plus a hostile `-submit`, or it passes vacuously.

## 2. Output: escape at the sink, force-download uploads

### 2a. Escape at the output sink

**Seen in reviews:** a label built with `html_writer::tag('span', $label)` (tag content is not escaped), then
assigned through `innerHTML`: stored XSS.

Check:
- `grep -rnE "html_writer::(tag|div|span|link|select)\(" --include='*.php' .`: is the content argument a stored
  or user value without `s()`, `format_string()` or `format_text()`? Attributes are escaped; content is not.
  `html_writer::select()` option labels go into tag content too (`select_option()`,
  `public/lib/classes/output/html_writer.php`, 5.3.0). Assert on the `>label</option>` position in a test, not on
  a page substring.
- **Formslib prints labels as HTML:** element labels, `select` option texts and `advcheckbox` texts reach core's
  form templates as `{{{label}}}`, `{{{text}}}` and `{{{.}}}` (`public/lib/form/templates/`, 5.3.0). Stored or
  authored text passed to any of them needs `s()`.
- **Messages are HTML:** `core/modal` titles (`setTitle()` uses `.html()`, `public/lib/amd/src/modal.js`), toasts,
  `core/notification` strings, and `redirect($url, $message)`, whose message is rendered by
  `notification_base.mustache` as `{{{ message }}}` (5.3.0). Pass lang strings; put user data through `s()` on the
  server or `textContent` in JS.
- `grep -rnE "innerHTML|insertAdjacentHTML|outerHTML|dom\.create\(|setContent\(" amd/src`, then trace what feeds
  the sink. HTML from `Templates.renderForPromise()` of a template using `{{ }}` is a pass; string-concatenated
  HTML is a fail. In TinyMCE plugins `editor.dom.create('div', {}, html)` is a sink.
- `fullname()`, `get_string()` and `html_writer` escape at no layer: wrap a user's name in `s()`.
- **JSON in a data attribute:** `s()` keeps numeric entities (`public/lib/weblib.php`), so encode with
  `json_encode($data, JSON_HEX_AMP | JSON_HEX_QUOT | JSON_HEX_APOS | JSON_HEX_TAG)` before `s()`.

Fix: escape at the point of output (`s($label)`), which neutralises the payload however it entered the DB.

**Probing a sink:** names are often tag-stripped on save, so a `<script>` payload proves nothing. Store an entity
payload such as `Theo &amp; <b>` and assert the escaped form appears. Write the attacker-shaped data inside a
PHPUnit test with `$this->resetAfterTest()`: a CLI script that includes `config.php` writes to the live database.

**Content written into core tables is rendered by core, sometimes `noclean`.** Question text and
question-category info render without cleaning, and `clean_text()` skips HTMLPurifier when
`is_purify_html_necessary()` finds no `<`, `>` or `&` (or only simple tags), so a `FORMAT_MARKDOWN` link like
`[x](javascript:...)` survives as a live `javascript:` href (`public/lib/weblib.php`, 5.3.0). For imported or
untrusted fields, clean every field yourself and convert or clamp `FORMAT_MARKDOWN`. Prove "no sink" by grepping
core's output code, not just the plugin.

### 2b. Uploaded files: force-download unless proven media

**Seen in reviews:** student files served inline with no content-type validation: stored XSS in the grader's
session. Another plugin with the same gap was protected only because it forced download.

Check:
- `grep -rnE "send_(stored_)?file\(" --include='*.php' .`: both serve inline unless told otherwise. The 4th
  argument of `send_stored_file()` is `$forcedownload`; for student files it is true unless the MIME type is a
  validated audio or video type.
- The upload endpoint validates type or extension against an allowlist before storing, not just `PARAM_FILE` on
  the name. The `pluginfile` callback allowlists `$filearea`.
- **Validating one draft file does not validate what is stored.** `file_save_draft_area_files()` with
  `subdirs => 0` skips files outside `/` (`public/lib/filelib.php`, 5.3.0), so a valid image in `/sub/` can vouch
  for a root-level HTML file. Require exactly one file, at `/`, and decide inline serving by its mimetype.

```php
$mimetype = $file->get_mimetype();
$ismedia = in_array($mimetype, ['audio/webm', 'audio/ogg', 'video/webm', 'video/mp4'], true);
send_stored_file($file, 0, 0, $forcedownload || !$ismedia, $options);
```

## 3. Restored, imported and authored data is input

### 3a. Backup and restore

**Seen in reviews:** the forms cleaned a label (`PARAM_TEXT` plus `validation()`), but the restore step's
`process_*()` wrote it verbatim: the only injection path. Every `process_*()` in `backup/moodle2/restore_*`
applies the same `clean_param()` or allowlist as the interactive form before `insert_record()`. Where a unique
index exists, restore upserts.

```php
protected function process_myplugin_override($data) {
    global $DB;
    $data = (object) $data;
    $data->label = clean_param($data->label, PARAM_TEXT);
    $data->courseid = $this->get_courseid();
    $DB->insert_record('local_myplugin_override', $data);
}
```

### 3b. Authored definitions and imports that reach other users

**Seen in reviews:** admins wrote content definitions that teachers used. A default could name a site setting
(`config:<plugin>/<name>`), resolved with `get_config()` for any name, so `config:core/dbpass` came back filled
into a form field. An import in "replace" mode kept the replaced item enabled, so an untrusted file went live.

For any plugin whose stored definitions, templates or imports are shown to other users:
- **Settings read by name:** limit the names to an allowlist of what they are for. Never values from
  `config.php` (`$CFG->config_php_settings`, `$CFG->forced_plugin_settings`), never names like
  `pass|secret|key|token|salt`. Apply the same rule at every entry path (editor, JSON editor, import, AI proposal)
  and in the runtime resolver for rows stored before the rule existed.
- **Imports land as drafts:** new, copied and replaced items wait for a review step.
- **The authoring capability carries `RISK_XSS`.**

Fix: one allow-rule shared by validator and resolver, tested with a forbidden name in a stored row; set the
draft status explicitly in every import branch.

## 4. Data lifecycle: privacy, backup, reset, uninstall

**Seen in reviews:** a privacy provider queried pre-rename table names, so export and erasure threw
`dml_exception`; another declared a field in `get_metadata()` but never exported or deleted it. An activity had
`<modname>_reset_userdata()` without the reset form definition and defaults, so the reset option never
appeared. Plugins writing core grade items had no `db/uninstall.php`. Course-keyed tables had no backup code.

Checks (data-storing plugins):

- **4a. Privacy.** Every table, field, preference and file area in `get_metadata()` appears in an export path
  and in every delete path; after a table rename, grep `classes/privacy/` for the old name. A
  `tests/privacy/provider_test.php` exercises all six methods against generated rows. Recipes and traps:
  `moodle-privacy-gdpr`.
- **4b. Course reset.** Reset is the full triad, `<modname>_reset_course_form_definition()`,
  `<modname>_reset_course_form_defaults()` and `<modname>_reset_userdata()`, with no `mod_` prefix
  (`public/course/reset_form.php`, 5.3.0), including the gradebook reset.
- **4c. Uninstall and course deletion.** `db/uninstall.php` exists if the plugin writes outside its own tables.
  Core's uninstall does not delete the plugin's user preferences (`uninstall_plugin()`,
  `public/lib/adminlib.php`, 5.3.0); details in `moodle-definition-of-done`.
- **4d. Backup and restore coverage.** Each course-keyed table (`grep -n 'NAME="courseid"' db/install.xml`) is
  either backed up (and round-trips every field, remapping cross-activity ids in `after_restore()`) or left out
  for a reason written in the README. An activity without backup and restore is an approval blocker. What the
  restore code does with the data is 3a.

## 5. Tests

### 5a. Tests exist and cover the sinks

**Seen in reviews:** plugins ran `moodle-plugin-ci phpunit` and `behat` over an empty `tests/` directory: green,
and vacuous. `find tests -name '*_test.php' -o -name '*.feature'`: are there real tests, and do they cover the
paths this audit touched (upload, capability, privacy)? A security regression test is evidence only after it was
seen failing with the fix reverted, at the exact sink. If CI runs test steps over an empty `tests/`, say so.

## 6. Plugins directory review checks

These are the code findings reviewers raise that no CI step catches. Each row's command, fix and accepted
answer are in [reference/directory-review-checks.md](moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md), under the same ID;
every other guideline, with what CI covers, is in
[reference/submission-guidelines.md](moodle-skill-files/moodle-release-preflight/reference/submission-guidelines.md). Two review findings have their home in
earlier classes and are not repeated here: pages that need only a login (1b) and course tables with no backup
(4d).

| ID | Check | Detect with | Priority seen |
|---|---|---|---|
| 6a | Every string core or the code asks for exists (`pluginname`; `filtername` for a filter; `cachedef_<area>`; `<name>:<cap>`; `messageprovider:<name>`) | the lang-key script in the reference | high |
| 6b | Global functions, classes and constants carry the frankenstyle prefix | the greps below | high, blocker |
| 6c | Narrowest `PARAM_*` type, or a stated reason for `PARAM_RAW` | `grep -rn PARAM_RAW --include='*.php' .` | medium |
| 6d | Directories via `make_temp_directory()`, `make_request_directory()` or `$CFG->directorypermissions`, never `0777` | `grep -rnE '\bmkdir\(' --include='*.php' .` | medium, low |
| 6e | Outbound HTTP through `\curl` (proxy, blocked hosts), or the setting says the proxy is not used; every caveat the README states is also in the setting's description | `grep -rn curl_init --include='*.php' .` | medium |
| 6f | No per-call queries on a hot path (a filter's `setup()` runs on every `format_text()` call; a block's `get_content()` on every page that shows it) | a query-count test | medium |
| 6g | The minor gates below | the greps they name | low |

**6b blocks approval.** Every global function, global class and `define()`d constant takes the frankenstyle
prefix, including helpers in top-level pages and `cli/` scripts, where they hide. The two greps, the names core
dictates, and the pass condition are in the reference, section 6b.

**Release files** (the `LICENSE` file, the ZIP's root folder, only `lang/en/` in the package) are checked on the
built ZIP: `moodle-plugin-release`.

### 6g. Minor gates

One row in the report; name each gate that fails. The gates (`error_log()`, scaffolding in headers,
`requires` against `supported`, test helpers in production code, literal English messages, timezones) are in
[reference/directory-review-checks.md](moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md) section 6g.

## 7. Extended security checklist

Classes 1 to 6 come from reviews of submitted plugins. Static audits of widely installed third-party plugins
found more: SQL from mobile `$args`, `unserialize()` of restored data, IDOR and client-supplied `userid`,
GET-without-sesskey writes, `noclean` on student or LLM text, SSRF through PDF
renderers, SEPARATEGROUPS leaks. For any plugin with request entry points, walk
[reference/extended-security-checklist.md](moodle-skill-files/moodle-release-preflight/reference/extended-security-checklist.md) after classes 1 to 6 and
report each line; where they overlap, report a finding once. Its `riskbitmask` line includes `RISK_XSS` on any
capability whose writes are rendered for other users (3b). The checklist's ten groups are checks 7a to 7j.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Capability checked on the submitted course or cm id | Attacker picks the context | Derive context from the URL id; re-validate submitted ids |
| Page or web service with `require_login()` only | Any account can act | A capability with a risk flag, on the page and in the service |
| A rule enforced on the main action only | Sibling actions bypass it | Every sibling calls the shared check; one denied-case test each |
| Capability checked only at request time | A task runs a tampered stored value | Re-check at the sink |
| Limit enforced only in `amd/src` | A direct POST bypasses it | Mirror every limit on the server |
| `send_stored_file(..., false, ...)` for student files | Stored XSS in the grader's session | Force download unless validated media |
| `html_writer::tag('span', $userval)`, a formslib label, a modal title or a `redirect()` message with user data | All print HTML | `s()` or a lang string at the sink |
| Reporting every `innerHTML` grep hit | Template-rendered HTML is already escaped | Trace the feed before reporting |
| Probing escaping with `<script>` | Names are tag-stripped on save; the probe proves nothing | An entity payload in a `resetAfterTest()` test |
| Restore writes fields verbatim | An `.mbz` is attacker input | The form's `clean_param()` in `process_*()` |
| Data can name any setting for `get_config()` | `config:core/dbpass` reaches a form field | Allowlist by purpose at every entry path |
| A replace-import keeps the item live | Untrusted content reaches users without review | Every import lands as a draft |
| Overlaying values on a core form's defaults | Frozen, capability-gated fields get set | Skip frozen elements; use core's constant |
| Reset hook without form definition and defaults | The reset option never shows | Implement the full triad |
| "CI is green" as evidence | Empty `tests/` passes; CI never sees the ZIP | List the tests per sink; check the ZIP |
| Unprefixed helper in a top-level page or `cli/` script | Namespace collision: an approval blocker | `<component>_<name>()`, or a class under `classes/` |
| Relying on `validate` for strings | A filter passes with `filtername` and no `pluginname`; `cachedef_*` is never checked | Run the lang-key script |
| `mkdir($dir, 0777, true)` | Ignores the site's directory permissions | `make_temp_directory()` or `$CFG->directorypermissions` |
| Applying a reviewer's suggested `PARAM_*` type unchecked | `PARAM_USERNAME` strips `+`, `PARAM_ALPHANUMEXT` strips `.` | Test the type on real values, or keep the reason |

## Report format

One table, one row per check ID, every ID in this order, each exactly once:

| Class | IDs |
|---|---|
| 1 Trust boundary | 1a submitted ids, 1b login is not authorisation, 1c sibling actions, 1d client-side limits, 1e two roles one state, 1f frozen core form fields, 1g question engine slots |
| 2 Output | 2a escaping at the sink, 2b uploaded files |
| 3 Input from data | 3a backup and restore, 3b authored definitions and imports |
| 4 Data lifecycle | 4a privacy, 4b course reset, 4c uninstall and course deletion, 4d backup coverage |
| 5 Tests | 5a tests exist and cover the sinks |
| 6 Directory review | 6a strings, 6b frankenstyle prefixes, 6c `PARAM_*` types, 6d directories, 6e outbound HTTP, 6f hot-path queries, 6g minor gates |
| 7 Extended | 7a entry points and authorisation, 7b client-supplied ids, 7c CSRF, 7d injection, 7e output, 7f backup, restore and import, 7g outbound and secrets, 7h messaging and visibility, 7i resource use, 7j lifecycle and privacy |

Columns: ID, check (the short name above), result (pass, fail or N/A), evidence. An N/A row keeps its line and
gives the reason, so the reader sees every check was considered. A finding that fits two checks is reported under
the first ID and referred to by ID in the other row. After the table, list each fail with its ID, file:line,
severity and the fix pattern. Do not fix unless asked.

```markdown
| ID | Check | Result | Evidence |
|---|---|---|---|
| 1a | Submitted ids | Pass | `overview.php:28` takes the course from the block instance, not the request |
| 1b | Login is not authorisation | Pass | `overview.php:35` `require_capability('block/x:viewoverview', ...)` |
| 2b | Uploaded files | N/A | no `send_file`, `send_stored_file` or file areas (grep) |
| 6f | Hot-path queries | Fail | ~28 queries per uncached student in `get_content()`; see below |
```

## Extending this checklist

When a Plugins directory or security review finds a defect class not listed here, add it in the same shape (what
was seen, described generically; the check; the fix) so the next release is audited against it. A code finding
that a command can detect goes in class 6 and the directory-review reference; a trust-boundary or output defect
goes in classes 1 to 3. Give it the next free ID in its class and add it to the Report format table; never reuse
or renumber an ID, so old reports stay readable.

## Reference files

| File | Read it when |
|---|---|
| [reference/directory-review-checks.md](moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md) | The plugin is about to be submitted to the Plugins directory, a reviewer has opened an issue on it, or you need the command for a class 6 row |
| [reference/submission-guidelines.md](moodle-skill-files/moodle-release-preflight/reference/submission-guidelines.md) | The plugin is going to the Plugins directory for the first time, or its listing, licence, dependencies or bundled libraries changed, or you need to know whether CI covers a guideline |
| [reference/extended-security-checklist.md](moodle-skill-files/moodle-release-preflight/reference/extended-security-checklist.md) | The plugin has request entry points (pages, AJAX, external functions, mobile, dynamic forms, `pluginfile`, restore, tasks) and classes 1 to 6 are done |

## References

- https://moodle.atlassian.net/wiki/external/ODRhYjAyNTY4NDVmNGJlNjljN2ViMzkwYzdmYmIwMGI (Plugin submission guidelines)
- https://moodledev.io/general/community/plugincontribution/checklist (legacy checklist)
- https://moodledev.io/general/development/policies/security
- https://moodledev.io/general/development/policies/codingstyle/frankenstyle
- https://moodledev.io/docs/apis/subsystems/privacy
- https://moodledev.io/docs/apis/subsystems/output
- https://moodledev.io/docs/apis/subsystems/files
- https://moodledev.io/docs/apis/subsystems/backup


---

### moodle-security-audit

> Use when reviewing or hardening Moodle plugin code for security, auditing a plugin's entry points, or responding to a vulnerability report. Covers require_login and require_capability, IDOR (context derived from the record), sesskey and CSRF, required_param and PARAM_* types, $DB placeholders and get_in_or_equal, output escaping (s, format_string, format_text, html_writer, Mustache triple braces, JS sinks), pluginfile and send_stored_file, uploads, \curl and SSRF, open redirects (PARAM_LOCALURL), secrets and \core\encryption, external functions (validate_context), dynamic forms, mobile methods and tasks. Skip when the audit is the gate before a tag, a Plugins directory submission or a reviewer's finding (moodle-release-preflight).

# Moodle Security Audit

## Overview

Moodle gives a plugin framework-level protection (the capability system, sesskey, `$DB` placeholders, output
escaping, the file API), but only where the plugin calls it. Most plugin vulnerabilities are a call that is
missing, or made on the wrong context. This skill is the broad checklist and the default recipes. The defect
classes that reviews caught in shipped plugins, with their greps, are in `moodle-release-preflight`.

## When to Use

- Reviewing a pull request or a plugin for security
- Hardening code before it is exposed to students, guests or the web
- Responding to a vulnerability report
- **Skip when:** preparing a release or submission, or answering a Plugins directory review
  (`moodle-release-preflight`); writing ordinary feature code (`moodle-plugin-development`)

## How to audit

1. **List every entry point first:** top-level `*.php` pages, `ajax/` scripts, external functions in
   `db/services.php`, mobile methods, dynamic forms, the `pluginfile` callback, `backup/` restore steps,
   scheduled and adhoc tasks, a filter's `filter()`. An entry point you did not list is one you did not audit.
2. **For each, answer three questions:** who is logged in (`require_login`), which context the action is in
   (derived from the record acted on), and which capability allows it.
3. **Trace each untrusted value from source to sink:** request parameters, web service and mobile arguments,
   restored and imported data, text other users wrote, and anything a client can edit (hidden fields, browser
   storage). A grep hit is not a finding until the trace shows no guard on the way.
4. **Rate by the lowest role that can exploit it.** Editing-teacher HTML behind a `RISK_XSS` capability is
   Moodle's accepted trust model; it becomes a finding when student input reaches it or the capability lacks the
   flag.

## Default recipe for a page script

```php
require(__DIR__ . '/../../config.php');

$id = required_param('id', PARAM_INT);                              // 1. Typed input.
$item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
$course = get_course($item->courseid);
$context = context_course::instance($course->id);                   // 2. Context from the record.

require_login($course);                                             // 3. Session, enrolment, course access.
require_capability('local/example:edit', $context);                 // 4. Authorisation.

$PAGE->set_url(new moodle_url('/local/example/edit.php', ['id' => $id]));
$PAGE->set_context($context);

if (optional_param('confirm', 0, PARAM_BOOL)) {
    require_sesskey();                                              // 5. CSRF, before any write.
    // ... write ...
}
```

Reading parameters and the record before `require_login()` is fine; doing anything with them (output, writes,
redirects to them) is not. `require_login($course)` also sets up `$PAGE` for the course, so it comes before
`$PAGE` output calls. `phpcs` warns when no login call follows `config.php` (`moodle.Files.RequireLogin`), but
it does not check the capability.

## 1. Authentication

| Call | Use |
|---|---|
| `require_login()` | Any logged-in user (guests auto-login if the site allows it) |
| `require_login($course)` | Logged in and able to enter the course |
| `require_login($course, false, $cm)` | Activity-level access, including visibility and availability |
| `require_login($course, false, $cm, true, true)` | The same for AJAX, mobile and web service code: throws instead of redirecting |
| `require_course_login($course)` | Course pages that guests and the front page may see |
| `require_admin()` | Site administrators only |

- AJAX scripts and helper endpoints (image, plot or file generators) need `require_login()` too. A valid
  session is not an authorised one.
- The second argument is `$autologinguest`: with the default `true`, a visitor is logged in as guest where the
  site allows it, so "logged in" can mean the guest account. Check `isguestuser()` or a capability guests lack
  before any write (`public/lib/moodlelib.php`, 5.3.0).
- A page with `NO_MOODLE_COOKIES` has no session, so it cannot check who the user is; it must not show or change
  anything per user.
- "Switch role to" applies in the course context only. To test a system-context gate, use a real account with
  that role (`moodle-field-lessons`).

## 2. Authorisation and IDOR

```php
// Bad: checks a site-level capability; the item belongs to a course the user may not see.
$item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
require_capability('local/example:view', context_system::instance());

// Good: the context comes from the object being acted on.
$item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
require_capability('local/example:view', context_course::instance($item->courseid));
```

- **Derive the context from the object, never from a URL or form parameter.** A submitted `courseid`, `cmid` or
  `contextid` lets the attacker choose where the check runs.
- **Bind child ids to the parent you authorised:**
  `$DB->get_record('local_example_choices', ['id' => $choiceid, 'itemid' => $item->id], '*', MUST_EXIST)`.
- **Never take the acting user from the client.** A web service that accepts `userid` for "my" data uses
  `$USER->id` instead.
- **`require_login()` is not authorisation.** Every page and web service function that does more than show users
  their own data names a capability. Sibling actions on the same object (edit, delete, react, pin) make the same
  checks as the main action (`moodle-release-preflight` checks 1b and 1c).
- **Write actions need a write capability**, with the right `riskbitmask` in `db/access.php` (`RISK_XSS` when
  what it writes is shown to others, `RISK_PERSONAL`, `RISK_CONFIG`, `RISK_DATALOSS`, `RISK_SPAM`). Never check a
  role shortname or `$USER->id == 2`; use `is_siteadmin()` or a capability.
- **Groups:** in separate-groups mode, filter lists and actions by `groups_get_activity_group()` unless the user
  has `moodle/site:accessallgroups`.

## 3. CSRF: sesskey

Every request that changes state needs a sesskey check, whatever its HTTP method: `require_sesskey()` (throws) or
`confirm_sesskey()` (returns a bool). A GET that writes is fired by an `<img src>` in any post an admin views.

- `moodleform` adds the sesskey field and checks it: a submitted form with a bad sesskey throws `invalidsesskey`
  (`public/lib/formslib.php`, 5.3.0), so code after `get_data()` needs no second check.
- A raw HTML form carries `<input type="hidden" name="sesskey" value="{{sesskey}}">`, with the value from
  `sesskey()` in the template context.
- `core/ajax` calls send it automatically. A raw `fetch()` adds it from `core/config`:

```javascript
import Config from 'core/config';

const body = new URLSearchParams({sesskey: Config.sesskey, id: String(itemid)});
await fetch(`${Config.wwwroot}/local/example/ajax.php`, {method: 'POST', body});
```

The sesskey is a CSRF token, not the session id; a scanner flagging `?sesskey=` in URLs is a false positive
(https://moodledev.io/general/development/process/security/penetration-testing).

## 4. Input: typed parameters, never superglobals

```php
$id    = required_param('id', PARAM_INT);
$name  = optional_param('name', '', PARAM_TEXT);
$ids   = required_param_array('ids', PARAM_INT);
$back  = optional_param('returnurl', '', PARAM_LOCALURL);
```

- Use the narrowest type that fits: `PARAM_INT`, `PARAM_BOOL`, `PARAM_ALPHANUMEXT`, `PARAM_COMPONENT`,
  `PARAM_EMAIL`, `PARAM_LOCALURL`, `PARAM_TEXT` (tags stripped except multilang spans), `PARAM_NOTAGS`,
  `PARAM_CLEANHTML`. Test the type on real values: `PARAM_ALPHANUMEXT` strips `.`, `PARAM_USERNAME` strips `+`
  unless `$CFG->extendedusernamechars` is on (`public/lib/classes/param.php`, 5.3.0).
- `PARAM_RAW` accepts anything. Each use carries a comment saying why and where the value is escaped or bound;
  Plugins directory reviewers flag uncommented ones.
- `$_GET`, `$_POST`, `$_REQUEST` and `$_COOKIE` skip type coercion. No `phpcs` sniff flags them; grep for them.
- Formslib fields get their type from `$mform->setType()`. A `hidden` element's value is client-editable; use
  `setConstant()` or re-validate it.
- Values arrive in other ways too: web service and mobile arguments, restored `.mbz` data and imported files are
  input as well. See [reference/entry-points.md](moodle-skill-files/moodle-security-audit/reference/entry-points.md).

## 5. SQL: placeholders only

```php
$DB->get_records_sql('SELECT * FROM {local_example_items} WHERE name = :name', ['name' => $name]);

// Bad: an id list built by string joining.
$DB->get_records_sql('SELECT * FROM {local_example_items} WHERE id IN (' . implode(',', $ids) . ')');

// Good.
[$insql, $params] = $DB->get_in_or_equal($ids, SQL_PARAMS_NAMED);
$DB->get_records_sql("SELECT * FROM {local_example_items} WHERE id $insql", $params);

// LIKE: escape the user's text and let the DML build the operator.
$where = $DB->sql_like('name', ':pattern', false);
$DB->get_records_sql("SELECT * FROM {local_example_items} WHERE $where",
    ['pattern' => '%' . $DB->sql_like_escape($search) . '%']);
```

Column and sort names cannot be placeholders: check them against an allowlist
(`in_array($sort, ['name', 'timecreated'], true)`). Mobile `$args` and web service values are as untrusted as
request parameters.

## 6. Output: escape at the sink

| Function | Use |
|---|---|
| `s($str)` | Escape plain text for HTML content and attributes |
| `format_string($str, true, ['context' => $ctx])` | Short user text (names, titles): runs filters, escapes `&`, `<`, `>`, but not quotes |
| `format_text($html, $format, ['context' => $ctx])` | Rich text: runs filters and HTMLPurifier |
| `clean_text($html, FORMAT_HTML)` | HTMLPurifier only, no filters |
| `html_writer::tag('span', s($text), $attrs)` | Attributes are escaped; tag content is not |
| `{{var}}` / `{{{var}}}` in Mustache | Escaped / raw: raw only for HTML already produced by `format_text()` or a renderer |

- Pass `context` to `format_string()` and `format_text()`; it decides which filters run.
- `format_string()` is not safe inside an attribute, since it leaves quotes alone (`public/lib/classes/formatting.php`,
  5.3.0). Use `s()` there.
- **Core helpers that print text as HTML:** `html_writer::select()` labels, formslib labels and option texts,
  `core/modal` titles, toasts, `core/notification` and the `redirect()` message. Escape user data before passing
  it. The full list with its sources is in `moodle-release-preflight` class 2a.
- **JS sinks:** `innerHTML`, `insertAdjacentHTML`, `outerHTML` and jQuery `.html()` take only HTML rendered from a
  template (`Templates.renderForPromise()`) or `textContent` for plain text.
- **`noclean` and `'trusted' => true`** are for text written by users with `RISK_XSS` capabilities. Student text,
  LLM output and imported HTML never get them.

## 7. File serving and uploads

- Serve files through the `pluginfile` callback, never by path under `$CFG->dataroot`. The callback checks the
  context level, allowlists `$filearea`, calls `require_login()` and the capability, and checks that the item
  belongs to something the user may see. `pluginfile.php` authenticates the session; it does not authorise the
  plugin's files. Recipe: [reference/entry-points.md](moodle-skill-files/moodle-security-audit/reference/entry-points.md).
- `send_stored_file($file, 0, 0, $forcedownload, $options)` and `send_file()` serve inline unless told otherwise.
  Force download for user uploads unless the mimetype is validated media.
- Uploads go through a draft area and `file_save_draft_area_files()` with `maxfiles`, `maxbytes` and
  `accepted_types` set (`core_form\filetypes_util` for admin-configurable types). Never trust
  `$_FILES[...]['type']`.
- Working directories come from `make_temp_directory()` or `make_request_directory()`, which use
  `$CFG->directorypermissions` (`public/lib/setuplib.php`, 5.3.0); a literal `0777` is flagged in review.

## 8. Outbound HTTP and SSRF

```php
$curl = new \curl();
$response = $curl->get($url);
if ($curl->get_errno() || $curl->get_info()['http_code'] != 200) {
    throw new moodle_exception('fetchfailed', 'local_example');
}
```

- `\curl` applies `$CFG->curlsecurityblockedhosts` and `curlsecurityallowedport` through
  `\core\files\curl_security_helper`, and the site proxy (`$CFG->proxyhost`) (`public/lib/filelib.php`, 5.3.0).
  Raw `curl_init()` and `file_get_contents($url)` get neither. Never pass `ignoresecurity`.
- A server-side fetch of a URL a user supplied is SSRF unless it is admin-only or allowlisted. HTML handed to a
  PDF library fetches its `<img src>` on the server too.
- `clean_param($url, PARAM_URL)` checks the syntax, not the destination.

## 9. Secrets

- No tokens or keys in source, `version.php` or test fixtures. Store them as plugin settings
  (`admin_setting_configpasswordunmask`), read them with `get_config('local_example', 'apikey')`.
- `\core\encryption::encrypt()` and `decrypt()` protect a stored secret beyond the settings table.
- Mark function parameters that carry secrets with `#[\SensitiveParameter]` so they stay out of stack traces, as
  core's `hash_internal_user_password()` does.
- Send a site credential only to the host the admin configured, never to a per-item URL override.
- Never log secrets: `debugging("Token: $token")` and event `other` data end up in logs others can read.

## 10. Redirects

```php
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);
redirect($returnurl ? new moodle_url($returnurl) : new moodle_url('/local/example/index.php'));
```

`PARAM_LOCALURL` accepts only URLs on this site. `PARAM_URL` or the `Referer` header as a redirect target is an
open redirect.

## 11. Static analysis

`moodle-plugin-ci phpcs` (the moodle-cs standard) flags `eval`, `goto`, backticks, `extract()`, `error_log()` and a
missing login call (read in the moodle-cs 3.7 source). It does not flag `unserialize()`, `call_user_func()`, superglobals, `PARAM_RAW`, missing capability
checks or missing frankenstyle prefixes. Use it, then grep.

```bash
G() { grep -rnE --include='*.php' --exclude-dir={vendor,thirdparty,node_modules,tests} "$@" .; }
G '\$_(GET|POST|REQUEST|COOKIE)\['                      # superglobals
G 'PARAM_RAW'                                           # each needs a reason
G 'unserialize\('                                       # needs allowed_classes => false
G "noclean|'trusted' *=> *true"                         # who writes that text?
G 'curl_init|file_get_contents\(.*https?:'              # bypasses \curl security
G 'get_records_sql|get_record_sql|execute\(' | grep -E '\$[a-z_]+\s*\.|"\s*\.\s*\$|\{\$'   # concatenated SQL
```

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `$_GET['id']` | No type coercion; type juggling | `required_param('id', PARAM_INT)` |
| SQL built by concatenation or `implode()` | SQL injection | Placeholders and `get_in_or_equal()` |
| `echo $row->name` | Stored XSS | `s()` or `format_string()` |
| `html_writer::tag('div', $usertext)` | Content is not escaped | `s($usertext)` |
| `format_string()` inside an attribute | Quotes break out | `s()` |
| No `require_login()` in an AJAX script | Anonymous access | Add it; or use an external function |
| Capability checked on a context from the request | The attacker picks the context | Context from the record |
| `require_login()` alone on a page that writes | Any account can act | `require_capability()` |
| `require_sesskey()` only on POST | A GET that writes is CSRF | Check every mutating branch |
| No capability check in `pluginfile` | Any logged-in user downloads | Check context, filearea, capability, item |
| `send_stored_file(..., false)` for uploads | Inline HTML runs in the viewer's session | Force download unless media |
| `unserialize($input)` | Object injection | JSON, or `['allowed_classes' => false]` |
| `file_get_contents($userurl)` or `curl_init()` | SSRF; blocked hosts and proxy ignored | `\curl` |
| `redirect(optional_param('next', '', PARAM_URL))` | Open redirect | `PARAM_LOCALURL` |
| `print_error()` | Fatal "undefined function": it no longer exists on 5.2 or 5.3 | `throw new moodle_exception(...)` |
| `$USER->id == 2` as an admin check | Wrong on most sites | `is_siteadmin()` or a capability |
| Access decided by a client header (`User-Agent`, `X-Forwarded-For`) | Headers are spoofable | Capabilities; `getremoteaddr()` for logging only |
| `md5()` or `sha1()` for a password | Weak hash | `hash_internal_user_password()` |

## Reporting vulnerabilities upstream

A vulnerability in Moodle core goes to the security issue form at https://moodle.org/security/report, or to a
Moodle Tracker issue with a security level set, never to a public issue or forum
(https://moodledev.io/general/development/process/security). A vulnerability in someone else's plugin goes to its
maintainer privately first.

## Reference files

| File | Read it when |
|---|---|
| [reference/entry-points.md](moodle-skill-files/moodle-security-audit/reference/entry-points.md) | The plugin has AJAX scripts, external functions, mobile methods, dynamic forms, a `pluginfile` callback, tasks or a filter, and you are auditing or writing their access checks |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-security-audit/versions/moodle-5.3.md): token endpoint hardening, CORS for AJAX functions, REST API tokens and scopes, `\core_auth\validate_user`, the app deep-link auto-login setting, HTMLPurifier changes |

## References

- https://moodledev.io/general/development/policies/security
- https://moodledev.io/docs/apis/subsystems/output#string-formatting-functions
- https://moodledev.io/docs/apis/subsystems/access
- https://moodledev.io/docs/apis/subsystems/files
- https://moodledev.io/docs/apis/core/dml#placeholders
- https://moodledev.io/general/development/process/security
- See also: `moodle-release-preflight` (review-found defect classes), `moodle-field-lessons` (escaping and
  authorisation small print), `moodle-web-services`


---

### moodle-theme-boost-child

> Use when building or fixing a Moodle theme whose config.php has $THEME->parents = ['boost'] (a Boost child) or ['boost_union', 'boost'] (a grandchild) - the minimal config.php, lib.php, version.php and lang file, which $THEME keys must be restated (rendererfactory, haseditswitch, usescourseindex, requiredblocks), theme_boost_get_main_scss_content and presets, why brandcolor, scsspre or the background image is ignored, a child that lost the edit switch, the course index or its renderer overrides, screenshot, favicon and the null privacy provider, and what breaks when Boost changes between 5.2 and 5.3. Skip when the question is the SCSS itself or a theme that renders as plain Boost (moodle-theme-scss), layouts or templates (moodle-theme-layouts-templates), renderers or hooks (moodle-theme-renderers-output), the settings page (moodle-theme-settings), or choosing between a child and a stand-alone theme (moodle-theme-development).

# Moodle Boost child theme

## Overview

A Boost child is a theme that lists `boost` in `$THEME->parents` and adds only what differs. Core hands it Boost's
layouts, templates, renderers, SCSS callbacks and fallback CSS, but not Boost's feature switches and not Boost's
saved settings. This skill gives the smallest child that works on Moodle 5.2 and 5.3, and the rules about what is
and is not inherited. The recipe was built and checked on Moodle 5.3.0 ("run on 5.3.0"); nothing was run on 5.2,
so every 5.2 statement is "read in the 5.2 source".

## When to Use

- Starting a theme that should look like Boost with a different brand, extra SCSS, a few settings or overrides
- A child theme ignores a Boost setting, loses the edit switch or course index, or shows navigation blocks again
- Building on top of another Boost child (a grandchild), or making a child safe to be a parent
- Moving a child theme between Moodle versions
- **Skip when:** you are deciding what kind of theme to build, or need the selection order, caches and purge
  commands (use `moodle-theme-development`); the theme renders as plain Boost after an SCSS change
  (`moodle-theme-scss`); the work is inside one area, where the sibling owns the detail:
  `moodle-theme-scss`, `moodle-theme-layouts-templates`, `moodle-theme-renderers-output`, `moodle-theme-settings`,
  `moodle-theme-testing-release`

## Mental model: three kinds of inheritance

Core treats a child's parents in three different ways. Knowing which one applies answers most child-theme questions.
Source for all rows: `public/lib/classes/output/theme_config.php`, identical in 5.2 and 5.3.0 except one font path.

| Kind | What it covers | What the child does |
|---|---|---|
| Looked up through the parents: the child, then the nearest parent that has it | layout files, layout table, Mustache templates, renderer classes, `scss`, `iconsystem`, region name strings; also `editor_scss`, images and fonts, where with two parents the farthest is asked before the nearer | Nothing. Add a file or a key only to replace the parent's |
| Chained: every parent's runs, then the child's | `prescsscallback`, `extrascsscallback`, `precompiledcsscallback`, `sheets`, `javascripts` | Add only its own part. Never repeat Boost's |
| Not inherited: the child's value or core's default | `rendererfactory`, `usefallback`, `requiredblocks`, `addblockposition`, `haseditswitch`, `usescourseindex`, `activityheaderconfig`, `yuicssmodules`, `removedprimarynavitems`, favicon | Restate Boost's value in `config.php` |

Two facts sit on top of that table:

- **One settings object.** Core loads `get_config('theme_<active theme>')` once and gives that same object to the
  child's and to every parent's `config.php`, and each chained callback receives the child's `theme_config`. So
  when the child is active, `theme_boost_get_pre_scss($theme)` reads `brandcolor` and `scsspre` from
  `theme_<child>`, not from `theme_boost` (`theme_config::load()` and `get_pre_scss_code()`; run on 5.3.0: a
  `brandcolor` saved under the child's component recoloured `.btn-primary` with no child code).
- **Boost's layouts are always the base.** The layout table starts from Boost's, then each parent's, then the
  child's entries. A child with no `$THEME->layouts` gets every Boost layout (run on 5.3.0 with one entry
  replaced: all other layouts came from Boost).

The exact rule for every key and asset type, including which parent wins when there are two, is in
[reference/inheritance.md](moodle-skill-files/moodle-theme-boost-child/reference/inheritance.md).

## The default recipe

```
theme/example/                 (public/theme/example in the Moodle tree, or $CFG->themedir/example)
  version.php
  config.php
  lib.php
  settings.php                 optional; see "Boost's settings"
  lang/en/theme_example.php
  classes/privacy/provider.php
  scss/example/pre.scss
  scss/example/post.scss
  pix/screenshot.png  pix/favicon.ico  pix/icon.svg
  LICENSE                      GPL text in the root; moodle-plugin-release has the package rules
```

### version.php

```php
<?php
// (GPL header)

/**
 * Version information.
 *
 * @package    theme_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'theme_example';
$plugin->version   = 2026111600;
$plugin->release   = '1.0.0';
$plugin->requires  = 2026042000;                        // Moodle 5.2.0.
$plugin->supported = [502, 503];
$plugin->maturity  = MATURITY_STABLE;
$plugin->dependencies = ['theme_boost' => 2026042000];  // Boost as shipped with 5.2.
```

Declare the dependency: the child calls Boost's functions and reads Boost's files. A 5.3-only theme uses the
values in [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-boost-child/versions/moodle-5.3.md). Every PHP file below starts with the same GPL header
and file docblock; the samples shorten both to a comment line.

### config.php

```php
<?php
// (GPL header)

// (file docblock as in version.php: Theme configuration: a child of Boost)

defined('MOODLE_INTERNAL') || die();

require_once(__DIR__ . '/lib.php');

$THEME->name = 'example';
$THEME->parents = ['boost'];

// All CSS comes from SCSS. Leave editor_scss unset so Boost's editor styles are inherited.
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->usefallback = true;

// Main SCSS: this theme's pre.scss, then Boost's preset, then this theme's post.scss.
$THEME->scss = function ($theme) {
    return theme_example_get_main_scss_content($theme);
};
// Boost's own pre and extra callbacks already run for a child. These add only this theme's part.
$THEME->prescsscallback = 'theme_example_get_pre_scss';
$THEME->extrascsscallback = 'theme_example_get_extra_scss';

// Not inherited: restate Boost's values (public/theme/boost/config.php).
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
$THEME->requiredblocks = '';
$THEME->addblockposition = BLOCK_ADDBLOCK_POSITION_FLATNAV;
$THEME->iconsystem = \core\output\icon_system::FONTAWESOME; // Inherited; restated so the file reads whole.
$THEME->haseditswitch = true;
$THEME->usescourseindex = true;
$THEME->yuicssmodules = [];
$THEME->activityheaderconfig = ['notitle' => true];
```

No `$THEME->layouts`: add an entry only for a layout the child replaces (`moodle-theme-layouts-templates`).
Boost's `config.php` is identical in 5.2 and 5.3.0, so this file is the same for both.

### lib.php

```php
<?php
// (GPL header)

// (file docblock as in version.php: Theme callbacks)

/**
 * The main SCSS: Boost's preset wrapped in this theme's pre and post files.
 * @param \core\output\theme_config $theme the theme being built: this theme, or a child of it
 * @return string SCSS
 */
function theme_example_get_main_scss_content($theme) {
    global $CFG;

    require_once($CFG->dirroot . '/theme/boost/lib.php');
    $pre = file_get_contents(__DIR__ . '/scss/example/pre.scss');
    $post = file_get_contents(__DIR__ . '/scss/example/post.scss');
    // Boost reads the preset choice from the settings of the config it is given. Passing Boost's own config
    // follows the preset chosen on Boost's settings page. See "Presets" for the other two choices.
    $boost = \core\output\theme_config::load('boost');
    return $pre . "\n" . theme_boost_get_main_scss_content($boost) . "\n" . $post;
}

/**
 * SCSS variables from this theme's settings, placed before everything else.
 * @param \core\output\theme_config $theme
 * @return string SCSS
 */
function theme_example_get_pre_scss($theme) {
    $scss = '';
    $accent = get_config('theme_example', 'accentcolour');
    if (!empty($accent) && preg_match('/^#[0-9a-fA-F]{3,8}$/', $accent)) {
        $scss .= '$example-accent: ' . $accent . ";\n";
    }
    return $scss;
}

/**
 * SCSS built from this theme's settings, placed after everything else.
 * @param \core\output\theme_config $theme
 * @return string SCSS
 */
function theme_example_get_extra_scss($theme) {
    return '';
}
```

Use `__DIR__` for the theme's own files: it also works when the theme is installed in `$CFG->themedir`, and
survives a rename. Read the theme's own settings with `get_config('theme_example', ...)`, not `$theme->settings`,
so the function still works when a grandchild is the active theme.

### scss/example/pre.scss and post.scss

```scss
// pre.scss. The pre-SCSS callbacks run before this file, so a value from a setting wins over these defaults.
$example-accent: #b8410c !default;
$example-radius: 0.75rem !default;

// Bootstrap variables go here, before Boost's preset reads them.
$border-radius: $example-radius !default;
$card-border-radius: $example-radius !default;

// post.scss. Rules added after Boost's preset.
.example-banner {
    padding: 0.75rem 1rem;
    border-left: 0.5rem solid $example-accent;
    background-color: var(--bs-tertiary-bg);
    color: var(--bs-body-color);
}

[data-bs-theme="dark"] .example-banner {
    border-left-color: lighten($example-accent, 25%);
}
```

Colours for surfaces and text come from `--bs-*` custom properties, because on 5.3 a child follows Boost's
colour mode whether it wants to or not (see "Common mistakes"). Everything else about writing the SCSS is in
`moodle-theme-scss`.

### lang/en/theme_example.php

```php
<?php
// (GPL header)

// (file docblock as in version.php: Strings for the Example theme)

defined('MOODLE_INTERNAL') || die();

$string['choosereadme'] = 'Example is a child theme of Boost with a different accent colour.';
$string['configtitle'] = 'Example';
$string['pluginname'] = 'Example';
$string['privacy:metadata'] = 'The Example theme does not store any personal data.';
```

`pluginname` and `choosereadme` are required (the theme selector shows both). Region names such as
`region-side-pre` fall back to the parents' and then Boost's strings, so a child that adds no region needs none.
Keep the keys in alphabetical order: moodle-cs reports unordered keys as a warning
(`moodle.Files.LangFilesOrdering`), which fails a CI run that allows no warnings.

### classes/privacy/provider.php

```php
<?php
// (GPL header)

namespace theme_example\privacy;

// (class docblock with @package, @copyright and @license: This theme stores no personal data)
class provider implements \core_privacy\local\metadata\null_provider {
    /** The lang string that says why nothing is stored. */
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

- Every plugin type needs a provider, themes included: core's `provider_test::test_all_providers_compliant()`
  lists every plugin (`public/privacy/tests/privacy/provider_test.php`, 5.3.0). `moodle-plugin-ci phpunit` runs
  only the plugin's own tests, so a missing provider passes CI and is found by a reviewer or a full core run.
- The child does not declare Boost's preferences (`drawer-open-index`, `drawer-open-block`, **5.3+:**
  `theme_boost_colourmode`): they belong to `theme_boost`, which exports them itself.
- A child that adds its own user preference is no longer a null provider. `moodle-theme-settings` has that provider.

## What the compiled stylesheet contains, in order

1. Pre SCSS from `theme_boost_get_pre_scss()`: `$primary` from the child's `brandcolor`, then the child's `scsspre`
2. Pre SCSS from `theme_example_get_pre_scss()`
3. `pre.scss`, Boost's preset (which imports Bootstrap, Font Awesome and Boost's `moodle` partials), `post.scss`
4. Extra SCSS from `theme_boost_get_extra_scss()`: the child's `scss` setting, background and login images
5. Extra SCSS from `theme_example_get_extra_scss()`

Plugins' `styles.css` files are placed before all of this in the served sheet, so a theme rule beats a plugin rule
of equal specificity (`theme_config::get_css_files()`, 5.3.0). `@import "moodle"` and other names resolve through
the child's `scss/` directory first and Boost's second, so a file in the child with the same name as a Boost
partial replaces it; choose names that do not collide (hence `scss/example/`).

## Boost's settings: the child has its own copy, or none

Because of the one settings object, Boost's settings page does not affect an active child. These Boost features
read the child's settings and stay off until the child offers a setting with the same name:

| Setting name under `theme_<child>` | Read by | Without it |
|---|---|---|
| `brandcolor` | `theme_boost_get_pre_scss()` | Brand colour comes from the preset only |
| `scsspre`, `scss` | `theme_boost_get_pre_scss()`, `theme_boost_get_extra_scss()` | No raw SCSS boxes for the admin |
| `backgroundimage`, `loginbackgroundimage` | `theme_boost_get_extra_scss()` | No page background; login page shows Boost's default image |
| `unaddableblocks` | `block_manager::get_unaddable_by_theme_block_types()` | Navigation, Administration and Courses blocks are offered in "Add a block" |
| `preset` | `theme_boost_get_main_scss_content($theme)` when given the child's config | Default preset |

Symptom when ignored: an admin switches the site from Boost to the child and the brand colour, custom SCSS and
background image disappear, although nothing was deleted. Fix: declare the same setting names under the child's
component and serve the two image areas from the child's `pluginfile` function. The complete `settings.php`,
the `pluginfile` function, the preset choices and a script that copies a site's Boost values across are in
[reference/boost-settings.md](moodle-skill-files/moodle-theme-boost-child/reference/boost-settings.md). Page design, setting types and `hide_if` are in
`moodle-theme-settings`.

## Presets

`theme_boost_get_main_scss_content($theme)` returns `default.scss`, `plain.scss`, or a file uploaded to the file
area `theme_boost` / `preset`, chosen by `$theme->settings->preset` (`public/theme/boost/lib.php`, same in 5.2).

| Wanted | Do | Status |
|---|---|---|
| Follow the preset chosen on Boost's settings page | Pass `\core\output\theme_config::load('boost')`, as in the recipe | run on 5.3.0 |
| Always the default preset | `file_get_contents($CFG->dirroot . '/theme/boost/scss/preset/default.scss')` | read in the source |
| The child's own preset setting and uploads | Own `preset` and `presetfiles` settings and an own lookup in the child's file area; see the reference file | read in the source, modelled on the Classic theme in 5.2 |

Passing the child's `$theme` to Boost's function with no `preset` setting gives the default preset; with a
`preset` setting it can select only the two built-in names, because the uploaded-file lookup is fixed to the
`theme_boost` component. `plain.scss` is not "default without decoration": it imports no design tokens and, on
5.3, no fonts, so SCSS that uses `$mds-*` variables fails to compile under it (read in the 5.3.0 source).

## Files beside the code

- `pix/screenshot.png`: shown in the theme selector. Without it the selector shows Boost's screenshot, because
  theme images fall back to the parents (`theme_config::resolve_image_location()`).
- `pix/favicon.ico`: not inherited. The lookup returns the child's path without looking at the parents, so a
  child with no file and no site favicon set in the admin settings gets a missing favicon (read in the 5.3.0
  source, not run). Copy Boost's or ship your own.
- `pix/icon.svg`: shown on the plugins overview page; without it the row has a blank spacer
  (`public/admin/renderer.php`, `plugins_control_panel()`, 5.3.0). It is rendered as an `<img>`, so it cannot
  take the page's text colour. **5.3+:** a near-black stroke is almost invisible on Boost's dark surface; use a
  mid-tone that has contrast on white and on `#1d2125` (read in the source, not seen in a browser).

## Overrides a child usually adds next

- A renderer override is `theme_example\output\core_renderer extends \theme_boost\output\core_renderer`. Extend
  Boost's class, not core's, or Boost's navbar, edit button and (**5.3+:**) colour mode menu are lost
  (`moodle-theme-renderers-output`).
- A template override goes in `templates/<component>/<name>.mustache`; Boost's own templates are overridden at
  `templates/theme_boost/<name>.mustache` (`moodle-theme-layouts-templates`).
- Hook and `lib.php` callbacks run for every installed plugin, whether or not the theme is in use. Start each
  with a guard that stays true for descendants (run on 5.3.0; `moodle-theme-renderers-output`):
  `if ($PAGE->theme->name !== 'example' && !in_array('example', $PAGE->theme->parents)) { return; }`
- Boost's Behat step overrides are inherited by the child's suite (`moodle-theme-testing-release`).

## Keeping up with Boost

A child that only adds SCSS, settings and a few hooks can serve 5.2 and 5.3 from one branch. A child that copies
`drawers.mustache` or `navbar.mustache`, or styles navigation markup, has a different upstream on each version:
use one branch per Moodle version with `$plugin->supported = [503, 503]`, as the large Boost children do.

- Keep an untouched copy of every file taken from core or Boost beside the modified one
  (`drawers.mustache.upstream`) and name the Moodle version in its header. Porting is then a diff of the old
  upstream against the new one. Mark copied PHP with a fixed phrase ("Modifications compared to the original").
- Test for the feature, not the version: `class_exists(\theme_boost\colour_mode::class)` is true from 5.3.
  `$CFG->branch` still holds the old value while a core upgrade is running.
- 36 of the 52 `scss/moodle` partials Boost ships on 5.2 differ on 5.3.0, which also adds five (compared between
  5.2.2 and 5.3.0). A child selector that leans on Boost's markup or specificity needs a look in a browser on
  each version.

What changed in Boost for 5.3, what a 5.2-era child must re-check, and the removals announced for 6.0 and 7.0 are
in the version files below.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Leaving out `rendererfactory` | Core's `standard_renderer_factory` is used: the child's renderer classes are never loaded and Boost's `core_renderer` is skipped too, with no error | `$THEME->rendererfactory = 'theme_overridden_renderer_factory';` |
| Leaving out `haseditswitch`, `usescourseindex`, `requiredblocks`, `activityheaderconfig`, `yuicssmodules` | In turn (read in the code that reads each key, not each reproduced): old "Turn editing on" buttons return beside the switch; no course index drawer; Navigation and Administration blocks are forced onto every page; activity titles are printed twice; YUI reset CSS is loaded on every page | Restate all of them as in the recipe |
| Copying Boost's pre or extra SCSS code into the child's callbacks | Brand colour, raw SCSS and background rules are emitted twice | The child's callbacks add only the child's part |
| Expecting Boost's saved settings to apply | Brand colour, raw SCSS and backgrounds vanish when the site switches to the child | Declare the same setting names under `theme_example` ([reference/boost-settings.md](moodle-skill-files/moodle-theme-boost-child/reference/boost-settings.md)) |
| An SCSS error anywhere in the stack | The page looks like plain Boost: core catches the error and serves the inherited precompiled Boost CSS, with a message only at developer debugging level (run on 5.3.0) | Turn on developer debugging, or look for "Error while compiling SCSS" in the PHP error log; `moodle-theme-scss` |
| Judging a CSS change on the first load after a purge | The old design is shown once: with `usefallback = true` the previous sheet is served from the temp directory while the new one compiles (`public/theme/styles.php`, 5.3.0) | Reload once; or set `usefallback = false` while developing (`moodle-theme-development` has the cache rules) |
| `$THEME->editor_scss = ['editor'];` with no `scss/editor.scss` in the child | Boost's editor styles are no longer used and the editor content is unstyled (read in the source) | Leave the key unset, or ship the file |
| `@import "bootstrap/functions";` or any path into Bootstrap | Works on 5.2, "file not found" on 5.3, and then plain Boost (run on 5.3.0) | Import only the wrapper names `bootstrap`, `fontawesome`, `moodle`, or reuse Boost's preset as the recipe does |
| Hard-coded light backgrounds or `prefers-color-scheme` | **5.3+:** when the admin enables colour modes in Boost's settings, every Boost descendant gets `data-bs-theme` on `<html>`; the child cannot opt out and shows light panels with light text | `--bs-*` custom properties, and `[data-bs-theme="dark"]` for exceptions |
| `$theme->settings->x` in code a grandchild may run | Under a grandchild the object holds the grandchild's settings, so the value is missing | `get_config('theme_example', 'x')` |
| A setting added without a version bump | Nothing stores its default, so the value is empty; SCSS that needs it meets an undefined variable | Bump `version`, and give every SCSS variable a `!default` in `pre.scss` |
| Only `['boost_union']` in a grandchild's `parents` | Core never follows a parent's parents; Boost's templates, renderers and SCSS are not found | List every ancestor, nearest first ([reference/grandchild.md](moodle-skill-files/moodle-theme-boost-child/reference/grandchild.md)) |

## Reference files

| File | Read it when |
|---|---|
| [reference/inheritance.md](moodle-skill-files/moodle-theme-boost-child/reference/inheritance.md) | A key, callback, image, font or template is not picked up from the parent as expected, the theme has two parents and you need to know which one wins, or you need each key's default and the symptom of omitting it |
| [reference/boost-settings.md](moodle-skill-files/moodle-theme-boost-child/reference/boost-settings.md) | The child must offer Boost's settings (brand colour, raw SCSS, background images, unaddable blocks, presets), needs its own preset uploads, or a site is moving from Boost to the child and must keep its look |
| [reference/grandchild.md](moodle-skill-files/moodle-theme-boost-child/reference/grandchild.md) | The theme's parent is itself a child of Boost (for example Boost Union), or your theme should be safe for others to build children on |
| [reference/patterns-to-avoid.md](moodle-skill-files/moodle-theme-boost-child/reference/patterns-to-avoid.md) | The child is growing past SCSS and a few overrides: before adding a second way for settings to reach CSS, regions that depend on settings, page HTML built in PHP, or a companion plugin; or when reviewing a large theme |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-theme-boost-child/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-boost-child/versions/moodle-5.3.md) |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme (the page still names some keys wrongly, for example
  `renderfactory` and `undeletableblocktypes`; the names core accepts are in the constructor of
  `public/lib/classes/output/theme_config.php`)
- https://moodledev.io/docs/5.3/guides/colourmodes
- `public/theme/boost/config.php`, `public/theme/boost/lib.php`, `public/theme/boost/UPGRADING.md` (5.2 and 5.3.0)


---

### moodle-theme-development

> Use when starting, structuring or debugging a Moodle theme at the engine level - a new theme/<name>/ directory, config.php and the $THEME keys, version.php and theme dependencies, $THEME->parents and what a child inherits, which theme a page uses (allowcoursethemes, allowthemechangeonurl and ?theme=, $CFG->themeorder), theme caches (themerev, theme designer mode, purge_caches.php, build_theme_css.php), "my change does not show" after a purge, "theme cannot be initialised", a theme problem whose area is not yet known, or choosing between a Boost child, a grandchild and a stand-alone theme. Also the routing table to the six sibling theme skills. Skip when the task is already inside one area: Boost child files (moodle-theme-boost-child), SCSS or a theme that renders as plain Boost (moodle-theme-scss), layouts and templates (moodle-theme-layouts-templates), renderers (moodle-theme-renderers-output), settings (moodle-theme-settings), testing and release (moodle-theme-testing-release).

# Moodle theme development: the engine, and where to go next

## Overview

A theme is a plugin of type `theme` that Moodle loads through `\core\output\theme_config`. This skill explains what
that class does with the theme's files, which is where most "nothing happened" problems come from, and routes each
kind of theme work to the sibling skill that owns it. Supported versions: Moodle 5.2 and 5.3.

How sure each statement is: "run on 5.3.0" means the behaviour was observed on a 5.3.0 site with a child of Boost;
everything else was read in the 5.3.0 source. Nothing here was run on 5.2: where 5.2 is mentioned it was read in the
5.2 source, and the engine files named below are identical in both versions unless a line is tagged.

## When to Use

- Creating a theme, or deciding what kind of theme to create
- Writing or reviewing `config.php`, `version.php` or the lang file of a theme
- A theme key, parent or override is ignored and no error is shown
- Working out which theme a page is using and why
- A change to SCSS, a template, an image or a setting does not show, or shows one page load late
- **Skip when:** the task is plainly inside one area. Use `moodle-theme-boost-child` for the child recipe,
  `moodle-theme-scss` for SCSS, `moodle-theme-layouts-templates` for page structure, `moodle-theme-renderers-output`
  for PHP output, `moodle-theme-settings` for admin settings, `moodle-theme-testing-release` for tests and shipping.
  For plugin basics that are not theme-specific (upgrade steps, capabilities, coding style) use
  `moodle-plugin-development`.

## Mental model

1. **Location.** `theme/<name>/` under `$CFG->dirroot`, which on disk is `public/theme/<name>/`, or
   `$CFG->themedir/<name>/` when that is set in the site's `config.php`. The component is `theme_<name>`.
2. **Load.** `theme_config::load($name)` reads `get_config('theme_' . $name)` into one settings object, then
   includes the theme's `config.php` with a fresh `$THEME` that already has `name`, `dir` and `settings`. It then
   includes each parent's `config.php` with that same settings object. `config.php` runs on every request; it is
   not cached.
3. **Whitelist.** Only the keys in a fixed list are copied from `$THEME`. Any other key is dropped without a
   message.
4. **Code loading.** `lib.php` (and a legacy `renderers.php`) of every listed parent is included, then the theme's
   own. Classes under `classes/` autoload as `\theme_<name>\...`.
5. **Inheritance is per asset.** Templates, renderers, layouts, SCSS, images and plain keys each follow their own
   rule. Some keys are not inherited at all. See the two tables below.
6. **Caching.** CSS is compiled once and served from a URL that carries two revision numbers. Templates, images
   and JavaScript have their own caches. "Purge" means different things for each.
7. **Failure is quiet.** A theme that cannot load is replaced by the site theme and then by Boost. An SCSS error is
   replaced by Boost's shipped CSS. Both leave the page working and looking like stock Boost.

Source for all seven: `public/lib/classes/output/theme_config.php` (5.3.0; one unrelated hunk differs in 5.2).

## Pick the approach

| Approach | `$THEME->parents` | Choose it when | Evidence |
|---|---|---|---|
| Child of Boost | `['boost']` | Almost always. Branding, SCSS, settings, a few template or renderer overrides | Run on 5.3.0 |
| Grandchild | `['boost_union', 'boost']` or any two-level chain | The site already depends on a feature-rich parent theme and needs local changes on top | Read in the source and in a published grandchild boilerplate, not run |
| Stand-alone | `[]` | Only when Boost's markup and SCSS cannot be the base | Not field-tested. Read [reference/stand-alone-theme.md](moodle-skill-files/moodle-theme-development/reference/stand-alone-theme.md) first |

- Support 5.2 and 5.3 from one codebase only while the theme is thin: SCSS on Boost's preset, settings, hooks, no
  copied layout template and no navbar override. Once the theme copies `drawers.mustache` or `navbar.mustache`, or
  styles navigation markup, use one branch per Moodle version, because each copy has a different upstream in each
  version. The large public themes all work that way.
- A grandchild depends on its middle parent's release schedule: it cannot move to a new Moodle version before
  that parent does.

## Files of a theme

```
theme/mytheme/
├── version.php            required: component, version, requires, dependencies
├── config.php             required: without it the theme does not exist for theme_config
├── lang/en/theme_mytheme.php   required: pluginname, choosereadme, configtitle
├── lib.php                functions named in config.php, pluginfile, callbacks
├── settings.php           admin settings page (moodle-theme-settings)
├── classes/               autoloaded: output/ renderers, privacy/provider.php, hook callbacks
├── db/                    hooks.php, upgrade.php, as in any plugin
├── scss/                  SCSS (moodle-theme-scss)
├── layout/                layout PHP files (moodle-theme-layouts-templates)
├── templates/             own templates, and overrides in templates/<component>/
├── pix/                   screenshot.png, favicon.ico, icon.svg, own images
├── pix_core/, pix_plugins/<type>/<plugin>/     image overrides
├── fonts/, fonts_core/, fonts_plugins/         fonts and font overrides
├── style/                 plain CSS files named in $THEME->sheets
└── LICENSE                the Plugins directory expects a licence file in the root (moodle-plugin-release)
```

- **`pix/screenshot`** (`.png` or `.jpg`, about 500 by 400 px) is what the theme selector shows. Without it a
  child shows its parent's screenshot, because theme images fall back to the parents, and a theme with no parents
  shows a broken image (`public/admin/themeselector.php`, `theme_config::resolve_image_location()`, read in 5.3.0).
- **`pix/favicon.ico` is never inherited.** Core returns `<active theme>/pix/favicon.ico` without checking that it
  exists or looking at parents, so a child without the file requests a missing favicon unless the site has uploaded
  one in the admin settings. Fix: copy a `favicon.ico` into the child's `pix/`
  (`theme_config::resolve_image_location()`, `core_renderer::favicon()`, read in 5.3.0).
- **`pix/icon.svg`** is the row icon on the plugins overview page; with no file the row shows a blank spacer
  (`public/admin/renderer.php`, read in 5.3.0).
- **A `styles.php` file in the theme directory makes core reject the theme** as a legacy theme
  (`theme_config::find_theme_location()`).
- **Lang strings.** `pluginname` is the name everywhere; `choosereadme` is the description in the selector's
  preview dialog; `configtitle` is the documented title string for the settings. Region names (`region-side-pre`)
  are looked up in the theme, then its parents, then `theme_boost`, so a child that adds no region needs none. A
  theme cannot override other components' strings: the string manager has no theme hook.
- **Privacy provider.** A theme needs `classes/privacy/provider.php` like any plugin: a null provider with a
  `privacy:metadata` string, or a user-preference provider when it stores preferences. Details are in
  `moodle-theme-settings`.

## version.php

```php
<?php
// (GPL header)

/**
 * Version information.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'theme_mytheme';
$plugin->version   = 2026111600;
$plugin->release   = '1.0.0';
$plugin->requires  = 2026042000;        // Moodle 5.2.0.
$plugin->supported = [502, 503];
$plugin->maturity  = MATURITY_STABLE;
$plugin->dependencies = ['theme_boost' => 2026042000];
```

- List every parent in `dependencies`, with the lowest build of that parent the theme works with. Without it the
  theme installs on a site that lacks the parent and then fails to load on every page.
- `2026042000` is Boost's version in 5.2.0 and `2026100500` in 5.3.0 (`public/theme/boost/version.php`). A theme
  for 5.3 only uses `requires = 2026100500`, `supported = [503, 503]` and the 5.3 Boost build.
- `version.php` must not `require` anything: core reads it in contexts where Moodle is not set up.
- A new theme directory is installed like any plugin: `php admin/cli/upgrade.php --non-interactive` from the
  Moodle root, or the admin notifications page.

## config.php: the keys

The smallest `config.php` for a child of Boost. It restates the keys Boost sets that a child does not inherit.

```php
<?php
// (GPL header)

/**
 * Theme configuration.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$THEME->name = 'mytheme';
$THEME->parents = ['boost'];
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->usefallback = true;
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
$THEME->requiredblocks = '';
$THEME->addblockposition = BLOCK_ADDBLOCK_POSITION_FLATNAV;
$THEME->haseditswitch = true;
$THEME->usescourseindex = true;
$THEME->activityheaderconfig = ['notitle' => true];
$THEME->yuicssmodules = [];
```

These twelve lines were run on 5.3.0 inside a child that also set its own `scss` Closure and callbacks. Left as
they are, with no `scss` key, the child inherits Boost's main SCSS, layouts, templates and SCSS callbacks (read,
not run in this exact form). Adding the theme's own SCSS, `lib.php` and settings is the subject of
`moodle-theme-boost-child`.

| Rule | Symptom when ignored | Fix |
|---|---|---|
| `$THEME->parents` must be an array, even when empty | The theme does not load; pages fall back with "cannot be initialised" | `$THEME->parents = [];` or the parent list |
| `$THEME->name` must equal the directory name | The theme is skipped by the theme selector and `?theme=` does not stick (read, not run) | Set it to the directory name; do not leave `'boost'` in a copied file |
| `rendererfactory` is not inherited | Every theme renderer is ignored, including Boost's own `core_renderer`, with no error | Restate `'theme_overridden_renderer_factory'` |
| `usefallback`, `requiredblocks`, `addblockposition`, `haseditswitch`, `usescourseindex`, `activityheaderconfig`, `yuicssmodules`, `removedprimarynavitems`, `csspostprocess`, `enablecourseajax`, `doctype`, `hidefromselector`, the arrow keys and `blockrtlmanipulations` are not inherited | The child silently gets core's defaults: no course index, "Turn editing on" buttons return beside the edit switch, the navigation and settings blocks become required, four YUI CSS modules load (read, not each reproduced) | Restate each one the parent sets, as above |
| Inherited from an ancestor that sets them: `scss`, `iconsystem`, `editor_scss`, `csstreepostprocessor`, `blockrendermethod`, the two exclude lists; `layouts` cascade per page type | Restating them is harmless, but restating `editor_scss` with a file the child does not ship drops the parent's editor styles | Leave them out unless changing them |
| Chained, every ancestor's runs: `prescsscallback`, `extrascsscallback`, `precompiledcsscallback`; concatenated: `sheets`, `editor_sheets`, `javascripts` | A child callback that repeats what the parent's emits puts that SCSS in the stylesheet twice | Emit only the child's additions |
| Keys outside the whitelist are dropped | No effect and no warning. Seen names: `enable_dock`, `editorsheets`, `undeletableblocktypes`, `renderfactory`, `allowedscss` | Use the real name: `editor_sheets`, `requiredblocks`, `rendererfactory` |

The official theme page uses several of the wrong names in the last row; the whitelist in
`theme_config::__construct()` is the authority. The complete key list with defaults, readers and Boost's values is
in [reference/theme-config-keys.md](moodle-skill-files/moodle-theme-development/reference/theme-config-keys.md).

## Parents and lookup order

**List every ancestor, nearest first.** Core loops over the theme's own `parents` only and never follows a
parent's `parents`. With `['boost_union']` alone, Boost's `lib.php`, SCSS callbacks, `core/` template overrides and
layout files are all outside the chain, and a layout file that only Boost ships throws `Can not find layout file`.
Written base first, the middle parent's templates, renderers and layouts lose to Boost's. Fix:
`$THEME->parents = ['boost_union', 'boost'];` (read in 5.3.0; the official theme page says the same).

For `parents = ['mid', 'base']`:

| Asset | Order searched | Who wins |
|---|---|---|
| Mustache templates | theme, `mid`, `base`, then the component's own `templates/` | Nearest |
| Renderer classes | `theme_<name>`, `theme_mid`, `theme_base`, then the component | Nearest |
| Layout table | Boost's table always, then `base`, `mid`, theme on top, a whole entry at a time | Nearest |
| Layout file | theme, `mid`, `base`, or only the theme named in the entry's `theme` key | Nearest |
| `scss`, `iconsystem`, `csstreepostprocessor`, `blockrendermethod`, excludes | theme, `mid`, `base`; first that sets it | Nearest |
| Pre, extra and precompiled callbacks; `sheets`; theme JavaScript | all run or load: `base`, `mid`, theme | Theme's output is last |
| Images in `pix_core`, `pix_plugins`, `pix`; fonts; `editor_scss` | theme, then `base`, then `mid` | Theme, then the base parent |
| React component overrides, **5.3+** | the active theme's `js/esm/build/overrides/` only | Parents are never checked |

- **Images and fonts are the exception: the base parent beats the middle parent.** An icon overridden in the
  middle parent is ignored if Boost's `pix_core` has the same file. Fix: put the file in the theme itself.
- **All configs share the active theme's settings object.** Inside a parent's `config.php`, and in any parent
  callback that receives `$theme`, `$theme->settings->x` is `theme_<active theme>/x`. This is why a Boost child's
  `brandcolor` setting works with no code (run on 5.3.0), and why a function that must read its own theme's value
  uses `get_config('theme_<owner>', 'x')` instead.
- **Callbacks core calls by name run for the active theme only**: `theme_<name>_page_init()`,
  `theme_<name>_alter_css_urls()`. A child forwards to the parent's function if it needs it. Hooks in `db/hooks.php`
  are the opposite: they run for every installed theme, active or not, and need a guard
  (`moodle-theme-renderers-output`).

The three-level detail, the callback list and the settings-page ordering trap are in
[reference/parents-and-callbacks.md](moodle-skill-files/moodle-theme-development/reference/parents-and-callbacks.md).

## Which theme a page gets

`moodle_page::resolve_theme()` takes the first match, in this order unless `$CFG->themeorder` in the site's
`config.php` changes it (`public/lib/pagelib.php`, identical in 5.2 and 5.3):

| Level | Source | Site switch, all off by default |
|---|---|---|
| course | `course.theme` | `allowcoursethemes` |
| category | nearest category upward with a `theme` | `allowcategorythemes` |
| session | `$SESSION->theme`, written by `?theme=<name>` | `allowthemechangeonurl`, checked when writing only |
| user | `user.theme` | `allowuserthemes` |
| cohort | the one theme all of the user's themed cohorts agree on | `allowcohortthemes` |
| site | `$CFG->theme`, else `boost` | none |

- **Try a theme without making it the site theme:** enable `allowthemechangeonurl`, open any page with
  `?theme=mytheme` (run on 5.3.0). The choice then sticks for the session and outranks user and cohort themes; it
  is cleared by logging out or by opening the theme selector page.
- **A theme that fails to load is replaced silently:** the site theme, then Boost, with a `debugging()` message at
  normal level only. If a page "ignores" the theme, turn on debugging and look for "cannot be initialised"; the
  usual causes are a missing parent, `parents` not an array, or a PHP error in `config.php`.
- **The theme is fixed on first use.** The first access to `$PAGE->theme` or `$OUTPUT` resolves it; after that
  `$PAGE->set_course()` throws "The theme has already been set up for this page ready for output". Set the course
  and context before any output call, and never call `require_login()` inside a fragment callback, where the
  theme is already set.
- **Set the site theme from the command line:** `php admin/cli/cfg.php --name=theme --set=mytheme` (read, not
  run). `$CFG->theme` forced in the site's `config.php` cannot be changed from the selector.

Cohort rules, `$PAGE->force_theme()`, the theme usage report, uninstall cleanup and the removed device themes are
in [reference/theme-selection.md](moodle-skill-files/moodle-theme-development/reference/theme-selection.md).

## Caches: what picks up a change

| What changed | What is needed |
|---|---|
| SCSS, a CSS sheet, a key in `config.php` that affects CSS, any plugin's `styles.css` | A theme purge, or theme designer mode |
| A setting that feeds SCSS | Nothing, if the setting has `set_updatedcallback('theme_reset_all_caches')`; otherwise a theme purge |
| A `$THEME` key that does not affect CSS (layouts, renderer factory) | Nothing: `config.php` is read on every request |
| A `.mustache` file rendered by PHP, including a new override file | Nothing, in any mode: compiled templates are keyed by a hash of their source |
| A `.mustache` file rendered in the browser through `core/templates` | A full purge, or `$CFG->cachetemplates = false`. Theme designer mode does not affect it |
| An image or font, including a file added after it was requested once | A theme purge: a missing image is remembered until the revision changes |
| A new class file, lang string, `db/hooks.php` | A full purge; this is ordinary plugin behaviour |

```
php admin/cli/purge_caches.php                      # everything, including browser-side templates
php admin/cli/purge_caches.php --theme              # theme revision only: CSS, images, fonts, theme JS
php admin/cli/build_theme_css.php --themes=mytheme  # compile now, both directions; add --direction=ltr, --verbose
```

Run them from the Moodle root (`admin/cli/` is not under `public/`). A development site's `config.php`:

```php
$CFG->themedesignermode = true;   // CSS, images and theme JS uncached. Slow: never on a production site.
$CFG->cachetemplates = false;     // Browser-side templates uncached.
$CFG->cachejs = false;            // AMD modules uncached.
```

- **The first page load after a purge can show the old CSS.** Every successful build also writes an unversioned
  copy to `$CFG->tempdir/theme/<name>/`, which no purge deletes. With `$THEME->usefallback = true`, the first
  stylesheet request after a purge is answered with that old copy while the new one is built. A screenshot or a
  computed-style check taken on that first load shows the previous design. Fix: load the page twice before
  judging, or set `usefallback = false` while developing (`public/theme/styles.php`, read in 5.3.0; the effect was
  seen on a 5.x site).
- **A page that suddenly looks like plain Boost means the SCSS did not compile.** The stylesheet request hides
  debugging output, the compile error goes to the PHP error log at developer debugging level, and the CSS falls
  back to Boost's shipped `style/moodle.css` (run on 5.3.0). Look for "Error while compiling SCSS" in the log, or
  run `build_theme_css.php` with developer debugging on, which reaches the same compile code (read; the message
  was seen from a separate compile script). `moodle-theme-scss` covers reading the error.
- **Theme designer mode still caches each sheet for 10 seconds** (`THEME_DESIGNER_CACHE_LIFETIME`,
  `public/lib/csslib.php`), and it serves many separate CSS requests, so page loads are slow.
- **Plugin CSS is part of the theme stylesheet.** Every plugin's `styles.css` is concatenated first, then parent
  sheets, then the theme's compiled SCSS, then the theme's own sheets. So theme and Bootstrap rules win over a
  plugin rule of equal specificity, and a plugin CSS change also needs a theme purge.
- **Check arrival, then effect.** Fetch the `theme/styles.php/.../all` URL from the page source and search it for
  the new selector with a literal match; then read `getComputedStyle()` in the browser. The first proves the rule
  was built, only the second proves it applies.

The serving path, the two revision numbers, what each purge clears and the other `theme/*.php` scripts are in
[reference/caches-and-revisions.md](moodle-skill-files/moodle-theme-development/reference/caches-and-revisions.md).

## Where each kind of work goes

| Task | Skill |
|---|---|
| Build the child: `lib.php`, what Boost gives for free, presets, pluginfile, grandchild of a large theme | `moodle-theme-boost-child` |
| Variables, pre and post SCSS, imports, dark mode, tokens, fonts, RTL, editor styles, compile errors | `moodle-theme-scss` |
| Layout files, regions, layout options, copying a Boost layout, template overrides, drawers, body classes | `moodle-theme-layouts-templates` |
| Renderer overrides, hooks from a theme, icon system and pix overrides, navigation, React overrides | `moodle-theme-renderers-output` |
| Settings page, setting types, setting to SCSS or template, stored files, user preferences | `moodle-theme-settings` |
| PHPUnit compile test, Behat suite, accessibility, lint, CI, Plugins directory rules, release | `moodle-theme-testing-release` |
| What changed for themes in 5.3 | `moodle-5-3-changes` |

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Omitting `rendererfactory` in a child | Renderer overrides silently unused | Restate it in the child's `config.php` |
| `$THEME->parents = ['boost_union']` for a grandchild | Boost's callbacks, templates and layout files drop out | List every ancestor, nearest first |
| Treating `precompiledcsscallback` as a cache | It is only used when the SCSS compile fails | Caching is automatic; precompile with `build_theme_css.php` |
| Inventing a key such as `$THEME->allowedscss` | Ignored without warning | Check the whitelist in the reference file |
| Copying Boost's pre or extra SCSS callback body into the child | `brandcolor` and the raw SCSS boxes are emitted twice | Emit only what the child adds |
| Judging CSS on the first load after a purge | Old design is shown once | Reload, or `usefallback = false` in development |
| Turning on designer mode to see a JavaScript-rendered template change | No change | `$CFG->cachetemplates = false` or a full purge |
| Testing with `?theme=` and forgetting it | The session keeps that theme and later checks mislead | Open the theme selector page or log out |
| Writing `theme` into `course` or `course_categories` with `$DB` | The theme usage cache is stale and the switch may be off | Use the course or category API and enable the `allow*themes` switch |
| `parents = ['classic', 'boost']` on a site without Classic | Falls back on every page with a debugging notice | **5.3+:** Classic is not in core; see the version notes |
| Checking a renderer or template override from a CLI script | The CLI renderer is used, so the override is not exercised | Check in a browser or a Behat scenario (run on 5.3.0) |

## Reference files

| File | Read it when |
|---|---|
| [reference/theme-config-keys.md](moodle-skill-files/moodle-theme-development/reference/theme-config-keys.md) | setting or reviewing a `$THEME` key not shown in the minimal `config.php`, or a key seems to be ignored |
| [reference/parents-and-callbacks.md](moodle-skill-files/moodle-theme-development/reference/parents-and-callbacks.md) | the theme has two levels of parents, or a `lib.php` function is expected to be called by core and is not |
| [reference/theme-selection.md](moodle-skill-files/moodle-theme-development/reference/theme-selection.md) | a page shows the wrong theme, or the task involves course, category, user or cohort themes |
| [reference/caches-and-revisions.md](moodle-skill-files/moodle-theme-development/reference/caches-and-revisions.md) | a change still does not show after the table above, or a deployment needs CSS built ahead of the first request |
| [reference/stand-alone-theme.md](moodle-skill-files/moodle-theme-development/reference/stand-alone-theme.md) | the theme will have no parents |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-theme-development/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-development/versions/moodle-5.3.md) |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme (theme plugin type; some key names on the page are wrong, see above)
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/layout
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/styles
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/images
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/fonts
- https://moodledev.io/docs/5.3/guides/templates
- https://moodledev.io/docs/5.3/apis/commonfiles/version.php
- Core source: `public/lib/classes/output/theme_config.php`, `public/lib/outputlib.php`, `public/lib/pagelib.php`,
  `public/theme/styles.php`, `public/theme/boost/config.php` (5.2 and 5.3)


---

### moodle-theme-layouts-templates

> Use when changing page structure in a Moodle theme - $THEME->layouts, layout/*.php files, block regions, layout options, copying Boost's drawers.php or drawers.mustache, overriding Mustache templates under templates/<component>/, the "!" include, drawers and the course index, body classes, the maintenance, secure and login layouts, or working out which 5.3 navigation parts are React-rendered; also for "Can not find layout file", "does not contain the main content placeholder", a filenotfound error on core/secondarymoremenu, or a template override that is ignored. Skip when the change is CSS only (moodle-theme-scss), a PHP renderer or React component override (moodle-theme-renderers-output), or the theme's config and caches (moodle-theme-development).

# Moodle Theme Layouts and Templates

## Overview

A theme decides page structure in two places: the `$THEME->layouts` table, which maps a page layout name to a PHP
file and its block regions, and Mustache templates, which a theme can override per component. This skill gives the
smallest change that works for each need, and the way to keep copied Boost files working on 5.2 and 5.3.

## When to Use

- Adding, moving or removing something in the page frame: banner, footer, navbar item, block region, drawer
- Replacing a layout for some page types, or adding a layout file
- Overriding a core, plugin or Boost template from a theme
- A theme that must run on 5.2 and 5.3 with a copied layout template
- Finding out whether a 5.3 part is still reachable by a template override
- **Skip when:** the change is colour, spacing or type only (`moodle-theme-scss`); you are changing what a renderer
  method returns or overriding a React component (`moodle-theme-renderers-output`); you need `config.php` keys,
  theme selection or cache purging (`moodle-theme-development`); you are building the child theme's base files
  (`moodle-theme-boost-child`)

## How a page gets its frame

1. The script calls `$PAGE->set_pagelayout('incourse')` (default `base`; `require_login()` with a course module sets
   `incourse`; `admin_externalpage_setup()` sets `admin`).
2. `core_renderer::header()` calls `theme_<name>_page_init($PAGE)` if the active theme defines it, then asks the
   theme for the layout file of that page layout and `include`s it with `$OUTPUT`, `$PAGE`, `$COURSE`, `$CFG`,
   `$SITE`, `$USER` in scope (`public/lib/classes/output/core_renderer.php`, `header()` and
   `render_page_layout()`, 5.3.0; same in 5.2).
3. The layout file builds a context array and echoes `$OUTPUT->render_from_template('theme_boost/drawers', $context)`.
4. Core cuts the output at the token printed by `$OUTPUT->main_content()`: what is before it is the header, what
   is after it is the footer. The script's own output goes between them.
5. Every template named in that render, and every partial inside it, is looked up in the active theme, then each
   parent in the order of `$THEME->parents`, then the owning component.

So there are three levers: the layouts table (which file, which regions), the layout file (what data), and the
templates (what markup). Most changes need only the third.

## Pick the smallest change

| Need | Do this | Cost at the next Moodle version |
|---|---|---|
| Restyle or hide something | SCSS (`moodle-theme-scss`) | none |
| Add HTML at the top of the body, before the footer, in `<head>` | A hook callback or a renderer method (`moodle-theme-renderers-output`) | none |
| Wrap a core template in extra markup | Override it and include the original with `!` | none |
| Change the navbar or footer markup | Override the Boost partial: `templates/theme_boost/navbar.mustache`, `templates/theme_boost/footer.mustache` | re-diff one partial |
| Change the frame on every drawers page | Override Boost's layout template only: `templates/theme_boost/drawers.mustache` | re-diff one template |
| Change the frame on some page layouts, add a region or new context data | Own `layout/<file>.php` plus own template, entry in `$THEME->layouts` | re-diff two files |
| Change text or structure inside React navigation (5.3) | See [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-layouts-templates/versions/moodle-5.3.md) first | high |

A child of Boost that sets no `$THEME->layouts` gets all 19 Boost layouts and needs no `layout/` directory.

## The layouts table

```php
// config.php (GPL header)
$THEME->layouts = [
    // Only the entries that differ from the parent. Each entry replaces the parent's entry whole.
    'course' => [
        'file' => 'course.php',            // Looked up in this theme's layout/, then each parent's.
        'regions' => ['side-pre'],         // Always present, even when empty.
        'defaultregion' => 'side-pre',     // Required when regions is not empty.
        'options' => ['langmenu' => true], // Not merged with the parent's options: restate them.
    ],
];
```

- **Layouts cascade.** The table starts from Boost's, then each parent's entries are laid over it from the farthest
  to the nearest, then the theme's own. An empty entry is skipped, so it cannot remove an inherited layout
  (`public/lib/classes/output/theme_config.php`, constructor, 5.3.0; same code read in 5.2).
- **An entry is replaced, not merged.** A child entry with only `'file'` loses the parent's `regions` and `options`.
  Symptom: blocks vanish from that page type, or a PHP warning from `get_all_block_regions()`, which reads
  `regions` of every layout without a check. Fix: copy the whole parent entry, then edit it.
- **Regions without `defaultregion`** give a PHP warning in `setup_blocks()` and blocks with no home
  (`theme_config.php`, `setup_blocks()`, 5.3.0).
- **Stand-alone themes start from Boost's table too.** Every layout the theme does not redefine still points at
  `drawers.php`, and only the theme and its declared parents are searched for the file. Symptom:
  `coding_exception` "Can not find layout file for: X (drawers.php)". Fix: define all layout names, or list `boost`
  in `parents`. Read in the source, not run.
- **`'theme' => 'boost'`** in an entry limits the file search to that one theme's `layout/` directory.
- **An unknown page layout name** falls back to `standard` with a debugging notice.
- **Only six option keys are read by core**: `nonavbar`, `nocontextheader`, `noactivityheader`, `nologinlinks`,
  `activityheader` (array of `notitle`, `nodescription`, `nocompletion`) and `activityinfoinheader`. Boost's config
  also sets `langmenu`, `nofooter` and `nocoursefooter`, which nothing in core or Boost reads (grep of
  `layout_options` over 5.3.0 and 5.2). A key of your own works only if your layout file reads
  `$PAGE->layout_options['key']`.

The layout names, their files, regions, options and which pages use them are in
[reference/layout-catalogue.md](moodle-skill-files/moodle-theme-layouts-templates/reference/layout-catalogue.md).

## Recipe 1: change markup without copying a layout

Template overrides reach Boost's own templates, because the lookup is by component and Boost is a component.

```mustache
{{!
    @template theme_mytheme/theme_boost/footer

    Boost's footer with a line of text above it. The original is included with the "!" suffix,
    which skips theme overrides, so this file holds none of Boost's markup.

    Example context (json):
    { "output": { "mytheme_footnote": "Maintained by the learning team" } }
}}
{{#output.mytheme_footnote}}
    <div class="mytheme-footnote container-fluid py-2">{{{output.mytheme_footnote}}}</div>
{{/output.mytheme_footnote}}
{{> theme_boost/footer! }}
```

Save it as `templates/theme_boost/footer.mustache` in the theme. Data that Boost's layout file does not pass comes
from a public, argument-free method on the theme's renderer, reached as `output.<method>`:

```php
// classes/output/core_renderer.php (GPL header)
namespace theme_mytheme\output;

/**
 * Renderer overrides for theme_mytheme.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class core_renderer extends \theme_boost\output\core_renderer {
    /**
     * The footnote setting, formatted for output.
     *
     * @return string
     */
    public function mytheme_footnote(): string {
        $text = (string) get_config('theme_mytheme', 'footnote');
        return $text === '' ? '' : format_string($text, true, ['context' => \core\context\system::instance()]);
    }
}
```

- The renderer is used only if `config.php` restates `$THEME->rendererfactory = 'theme_overridden_renderer_factory';`
  (it is not inherited; see `moodle-theme-boost-child`). Symptom without it: the section renders nothing, because
  Mustache calls a method only if `method_exists()` says it is there, and otherwise treats the name as empty
  (`public/lib/mustache/src/Context.php`, same file in 5.2).
- The `!` suffix is 5.2 and later (`public/lib/classes/output/mustache_template_finder.php`, identical in 5.2 and
  5.3.0). Wrapping `core/notification_info` this way was run on 5.3.0, in PHP and in a browser-side render;
  wrapping a `theme_boost` partial uses the same code path and was read, not run.
- To change the frame itself, copy `public/theme/boost/templates/drawers.mustache` to
  `templates/theme_boost/drawers.mustache` and edit it. Boost's `drawers.php` then renders your copy on all 11
  layouts that use it. Follow the copy rules in recipe 2.

## Recipe 2: own layout file and template, with upstream twins

Use this when only some page layouts change, or the template needs data that a renderer method cannot give.

1. Copy `public/theme/boost/layout/drawers.php` to `layout/course.php` and
   `public/theme/boost/templates/drawers.mustache` to `templates/course.mustache`.
2. Copy both again, untouched, with the suffix `.upstream` (`layout/course.php.upstream`,
   `templates/course.mustache.upstream`). These are the record of what was copied.
3. In each working copy keep the original author's `@copyright` line, add yours under it, and add a header comment
   that names the source, the Moodle version, and every modification.
4. Edit: add keys to `$templatecontext`, change the last line to
   `echo $OUTPUT->render_from_template('theme_mytheme/course', $templatecontext);`, and edit the template.
5. Point the layouts at the file (the entry in "The layouts table" above).
6. At each Moodle release: `diff` the new core file against your `.upstream` copy. Apply what changed to the
   working copy, replace the `.upstream` copy, and record it in the change log.

This was run on 5.3.0 with the `course` layout. Two things found there: phpcs with the moodle standard reports
Boost's own `drawers.php` (no trailing comma after the last context item), so fix that line in the copy; and the
`.upstream` extension keeps the twins out of phpcs and the Mustache lint (moodle-plugin-ci selects `*.php` and
`*.mustache` by name). The full worked files, the header
comment wording and the per-release checklist are in [reference/copying-a-layout.md](moodle-skill-files/moodle-theme-layouts-templates/reference/copying-a-layout.md).

What a layout template must print, in this order, or the page breaks: `output.doctype`, `output.htmlattributes`
on `<html>`, `output.standard_head_html` in `<head>`, the body attributes, `output.standard_top_of_body_html`,
`output.main_content`, `output.standard_after_main_region_html`, `output.standard_footer_html` and
`output.standard_end_of_body_html`. Boost prints the first three through the `theme_boost/head` partial and the
last two through `theme_boost/footer`.

- No `main_content`: `coding_exception` "page layout file ... does not contain the main content placeholder".
- No `doctype`: a debugging notice "The page layout file did not call $OUTPUT->doctype()".
- No `standard_end_of_body_html`: the page's end-of-body JavaScript is never printed, with no error (the footer
  replaces a token that method prints; read in the source).
  (`public/lib/classes/output/core_renderer.php`, `header()` and `footer()`, 5.3.0.)

## One copied template for 5.2 and 5.3

Boost's `layout/*.php` files are byte-identical in 5.2 and 5.3.0 (`diff -r`), so a copied layout file works on
both. `drawers.mustache` differs in exactly two places, and a copy of either version fails on the other:

| In the copy | On the other version | Symptom |
|---|---|---|
| 5.3's `{{> core/secondarymoremenu}}` | 5.2 has no such template | `filenotfound` exception on every page with secondary navigation (read in the 5.2 source, not run) |
| 5.3's `{{$drawercontrols}}` block | 5.2's `theme_boost/drawer` has only `drawerheadercontent` | course index expand and collapse control missing, no error |
| 5.2's `{{> core/moremenu}}` | still ships in 5.3 | legacy menu markup; core Behat navigation steps and Boost's 5.3 styles target the new markup |
| 5.2's `{{$drawerheadercontent}}` block | removed from 5.3's `theme_boost/drawer` | same control missing, no error |

A template that works on both fills both blocks (each parent uses only the one it defines) and chooses the partial
by a key that only 5.3's navigation export contains:

```mustache
{{$drawerheadercontent}}{{> theme_boost/courseindexdrawercontrols}}{{/drawerheadercontent}}
{{$drawercontrols}}{{> theme_boost/courseindexdrawercontrols}}{{/drawercontrols}}
```

```mustache
{{#secondarymoremenu}}
    <div class="secondary-navigation d-print-none">
        {{#reactprops}}{{> core/secondarymoremenu}}{{/reactprops}}
        {{^reactprops}}{{> core/moremenu}}{{/reactprops}}
    </div>
{{/secondarymoremenu}}
```

- Mustache loads a partial only when the section around it is rendered (`public/lib/mustache/src/Compiler.php`,
  partial code is emitted inside the section closure; same file in 5.2), so the 5.3-only name is never looked up
  on 5.2. `reactprops` is set by `core\navigation\output\more_menu::export_for_template()` on 5.3.0 and absent in
  5.2. Read in both sources; not run on 5.2.
- The same switch works in a copied `navbar.mustache` with `core/primarymoremenu`, inside `{{#primarymoremenu}}`.
- If the theme copies more than the drawers template (navbar, user menu, login), one branch per Moodle version is
  less work than switches; the large child themes do that. Details per version are in the Version notes files.

## Template overrides

- **Path:** `templates/<component>/<name>.mustache` in the theme, component in frankenstyle: `core`, `core_form`,
  `core_course`, `mod_forum`, `block_myoverview`, `theme_boost`. Subdirectories follow the template name:
  `core/local/toast/wrapper` is `templates/core/local/toast/wrapper.mustache`.
- **Order:** active theme, each parent in `$THEME->parents` order, then the component's own `templates/`
  (`mustache_template_finder.php`, `get_template_directories_for_component()`). The nearest theme wins. Boost
  itself overrides core this way (`public/theme/boost/templates/core/`), so check there before copying from
  `public/lib/templates/`.
- **A theme's own templates** sit directly in `templates/` and are named `theme_mytheme/<name>`.
- **`{{> core/name! }}`** includes the component's original and ignores every theme override. Use it to wrap
  instead of copy. It cannot change markup inside the original. An override that includes its own name without
  the `!` includes itself.
- **`{{< theme_boost/drawer }}...{{/ theme_boost/drawer }}`** fills named `{{$block}}`s of a parent template. A block
  name the parent does not define is ignored without a warning.
- **Overrides apply to browser-rendered templates too**: `core/templates` fetches the source through the same
  finder for the current theme.
- **Keep the override's docblock**: `@template`, the context description and `Example context (json):`. The
  Mustache lint in `moodle-plugin-ci` fails without them, also for files copied unchanged from core
  (`moodle-theme-testing-release`).

Caches, as far as templates go:

| Rendered by | Edit seen after | Why |
|---|---|---|
| PHP (`render_from_template`) | the next request, no purge, designer mode on or off | compiled templates are keyed by a hash of the source text (`public/lib/mustache/src/Engine.php`, `getTemplateClassName()`, 5.3.0) |
| JavaScript (`core/templates`) | a purge, or `$CFG->cachetemplates = false;` | the browser keeps the source in localStorage under the template revision; theme designer mode does not change this (`public/lib/classes/output/requirements/page_requirements_manager.php`, 5.3.0) |

A layout file edit is PHP: with OPcache validating timestamps it shows on the next request.

## Writing template markup

Each of these passes lint and unit tests and fails only in a browser, unless noted.

| Rule | Symptom when ignored | Fix |
|---|---|---|
| A `{{! }}` comment ends at the first `}}` | Tag syntax or JSON with `}}` inside a comment or example context ends the comment; the rest prints on the page or gives "Unclosed section" | Describe helpers in prose; write `} }` in example JSON |
| `{{#pix}}` is for icons | The image is forced to icon size by Boost's `.icon` class | For a full-size image pass a URL in the context and write `<img>` |
| `uniqid` is taken | A context variable named `uniqid` is overwritten in browser renders (`public/lib/amd/src/local/templates/renderer.js`, 5.3.0), so PHP and browser output differ | Use another name |
| `{{#js}}` is queued when the template renders | Rendering a template and discarding the HTML still runs its JavaScript, which then fails to find its elements | Do not render templates for their data; call `export_for_template()` |
| Bootstrap 4 class names | `.sr-only`, `.ml-2`, `.float-right`, `.badge-primary`, `data-toggle` work only through Boost's compatibility layer, planned for removal in 6.0; Behat with `--scss-deprecations` fails on them | `visually-hidden`, `ms-2`, `float-end`, `text-bg-primary`, `data-bs-toggle` |
| The `hidden` attribute loses to `d-flex` and other `d-*` utilities | The element stays visible | Toggle the `d-none` class |
| A `.row` needs a `.container` or `.container-fluid` ancestor | The page is a few pixels wider than a phone screen | Add the container, or `mx-0` on the row |
| A partial must be one valid HTML block | Lint HTML validation fails on a partial rooted in a bare `<li>`, or `role="log"` on an `<ol>` | Wrap in the list element; put the role on a `<div>` |
| A missing `{{#str}}` key | Prints `[[key]]` or throws on the live page while every gate is green | Render each new template in a PHPUnit test and assert no `[[` (`moodle-theme-testing-release`) |

## Page structure to keep

Core JavaScript, Behat steps and plugins address the page by these names. A custom layout keeps them:

- Ids: `page-wrapper`, `page` (read by the drawers, sticky footer, scroll manager and message drawer modules),
  `page-content`, `region-main` (notifications and core Behat steps), `region-main-box`, `page-header`,
  `page-navbar`, `page-footer`. Behat's `"page" "region"` selector is an element with that id.
- Navigation wrappers: `.primary-navigation` and `.secondary-navigation` (core Behat steps
  "I select ... from primary navigation" look inside them).
- Drawers: ids `theme_boost-drawers-courseindex`, `theme_boost-drawers-blocks`, `theme_boost-drawers-primary`;
  toggles are `[data-toggler="drawers"][data-action="toggle"][data-target="<drawer id>"]`.
- In Boost the drawers are siblings of `#page`, not inside it. A selector such as `#page .block` matches no block
  in the block drawer.
- The navbar is `nav.navbar.fixed-top`. Content starts `$navbar-height` below the viewport top; anything a theme
  makes sticky, and any script that scrolls an element into view, must allow for it.
- Body classes come from `$PAGE` (`pagelayout-<name>`, `path-<...>`, `dir-rtl`, `limitedwidth`, `editing`,
  `format-<name>`) and from the layout file (`uses-drawers`, `drawer-open-index`). Add your own with
  `$OUTPUT->body_attributes(['myclass'])` in the layout file, or `$page->add_body_class('myclass')` inside
  `theme_mytheme_page_init(moodle_page $page)` in `lib.php`, which runs for that theme only, not for its children.

The full lists, the drawer preferences and how to add a block region or a drawer are in
[reference/drawers-and-regions.md](moodle-skill-files/moodle-theme-layouts-templates/reference/drawers-and-regions.md).

## What 5.3 renders with React

**5.3+:** four parts are mounted as React components: primary navigation, secondary navigation, the edit mode
switch and the Timeline block. The first three are mounted from Mustache templates (`core/primarymoremenu`,
`core/secondarymoremenu`, `core/editswitch`) that a theme can still override to change the wrapper, the classes or
the no-JavaScript fallback. The items inside them are not template markup any more: selectors such as
`.primary-navigation .nav-link.active` match nothing once JavaScript has run. The Timeline block has no template
at all. Everything else (user menu, drawers, course index, breadcrumb, footer, activity chooser) is Mustache on
both versions. Read in the 5.3.0 source; no React override was built. See [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-layouts-templates/versions/moodle-5.3.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Child layout entry with only `'file'` | Regions and options of the parent entry are gone; blocks disappear on that page type | Copy the parent's whole entry, then change `file` |
| Copying 5.3's `drawers.mustache` into a theme that supports 5.2 | `filenotfound` for `core/secondarymoremenu` on 5.2 | The `reactprops` switch above, or one branch per version |
| Filling `drawerheadercontent` on 5.3, or `drawercontrols` on 5.2 | Course index controls missing, no message | Fill both blocks |
| Wrapping `{{> core/secondarymoremenu}}` in a `<nav>` | **5.3+:** two navigation landmarks; the component renders its own | Wrap in a `<div class="secondary-navigation">` only |
| Override saved as `templates/drawers.mustache` to replace Boost's | Ignored: that name is `theme_mytheme/drawers` | `templates/theme_boost/drawers.mustache` |
| Copying a core template that Boost also overrides, from `public/lib/templates/` | Boost's changes are lost in the child | Copy from `public/theme/boost/templates/core/` |
| Copying a layout with no `.upstream` twin | The next Moodle version changes Boost's file and nobody knows what to merge; pages break in places no test visits | Keep the twin and diff it at each release |
| Setting `'options' => ['nofooter' => true]` and expecting core to act | Nothing changes | Read `$PAGE->layout_options['nofooter']` in your layout file |
| Calling a custom `output.<method>` in the `maintenance` layout | Renders empty: that layout uses `core_renderer_maintenance`, not the theme's `core_renderer` | Keep the maintenance template free of theme methods; see [reference/special-layouts.md](moodle-skill-files/moodle-theme-layouts-templates/reference/special-layouts.md) |
| `empty($PAGE->cm)` or `isset($PAGE->pagetype)` in a layout file | Always "not set": `moodle_page` has no `__isset()` | Read the property into a variable first |
| Choosing a page layout for its name | Boost keys width and drawer rules on `pagelayout-<name>` and `limitedwidth`; a wide table on a `report` layout page sat under the course index (seen once on 5.3; the rule responsible was not identified) | For a page inside an activity use `incourse`; check at phone and desktop width |
| Judging a template change through a browser-rendered template with designer mode on | No change seen | `$CFG->cachetemplates = false;` or purge |
| Styling 5.3 navigation by looking at the page with JavaScript off | The fallback markup is the legacy one, so old selectors seem to work | Inspect with JavaScript on |

## Reference files

| File | Read it when |
|---|---|
| [reference/layout-catalogue.md](moodle-skill-files/moodle-theme-layouts-templates/reference/layout-catalogue.md) | You need to know which layout name a page uses, what Boost's entry for it contains, which option keys are read and by whom, or the body classes a page carries |
| [reference/copying-a-layout.md](moodle-skill-files/moodle-theme-layouts-templates/reference/copying-a-layout.md) | You are about to copy a Boost layout file or layout template, add template context in PHP, or port copied files to the next Moodle version |
| [reference/drawers-and-regions.md](moodle-skill-files/moodle-theme-layouts-templates/reference/drawers-and-regions.md) | The theme adds or moves a block region, adds a drawer, changes the course index drawer, or a test must open or close a drawer |
| [reference/special-layouts.md](moodle-skill-files/moodle-theme-layouts-templates/reference/special-layouts.md) | The theme touches the `maintenance`, `secure`, `login`, `embedded`, `popup` or `redirect` layouts |
| [reference/template-authoring.md](moodle-skill-files/moodle-theme-layouts-templates/reference/template-authoring.md) | You are writing a new template or a larger override and need the helper list, block and partial rules, the docblock the lint expects, or the full list of markup traps |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-theme-layouts-templates/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-layouts-templates/versions/moodle-5.3.md) |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme/layout
- https://moodledev.io/docs/5.3/guides/templates
- https://moodledev.io/docs/5.3/apis/plugintypes/theme
- https://moodledev.io/docs/5.3/guides/javascript/react/theming
- Core: `public/lib/classes/output/theme_config.php`, `public/lib/classes/output/mustache_template_finder.php`,
  `public/lib/classes/output/core_renderer.php`, `public/theme/boost/config.php`, `public/theme/boost/layout/`,
  `public/theme/boost/templates/` (5.2 and 5.3.0)


---

### moodle-theme-renderers-output

> Use when a Moodle theme changes output in PHP — $THEME->rendererfactory, theme_overridden_renderer_factory, classes/output/core_renderer.php, plugin renderer overrides, a theme's db/hooks.php callbacks, $THEME->iconsystem, get_fontawesome_icon_map, pix_core and pix_plugins, $THEME->activityheaderconfig, $THEME->removedprimarynavitems, primary navigation data, or a React component override in js/esm/src/overrides (5.3). Skip when the change is a Mustache or layout file (moodle-theme-layouts-templates), SCSS (moodle-theme-scss) or a settings page (moodle-theme-settings).

# Moodle theme renderers and output

## Overview

A theme changes what PHP prints through renderer classes found by name, hook callbacks, the icon system, image
files that shadow core's, and a few `config.php` keys; Moodle 5.3 adds React component overrides. Each has its own
lookup order and fails without an error when it is wrong, so the first job is picking the right one.

## When to Use

- Overriding a `core_renderer` method, or a plugin's or course format's renderer, from a theme
- Adding a method that a layout template calls as `{{{ output.something }}}`
- Adding markup to `<head>`, the top of `<body>` or the footer from a theme, or attributes to `<html>`
- Changing an icon: the glyph, the image file, an activity icon's colour
- Removing or adding primary navigation items, changing the activity header or the breadcrumb
- Deciding whether a 5.3 React-rendered region needs a component override
- **Skip when:** the change is a template or layout file (`moodle-theme-layouts-templates`), a style rule
  (`moodle-theme-scss`), a setting and its plumbing (`moodle-theme-settings`), the theme's skeleton and caches
  (`moodle-theme-development`), or a hook in a non-theme plugin (`moodle-hooks-api`).

## Pick the cheapest mechanism

Try them in this order. Each step down costs more at every Moodle upgrade.

| Goal | Mechanism | Owner |
|---|---|---|
| Colour, spacing, shape, hiding an element | SCSS, custom properties | `moodle-theme-scss` |
| Different markup for one template | Template override | `moodle-theme-layouts-templates` |
| Extra markup in head, top of body, footer; `<html>` attributes | Hook callback with an active-theme guard | this skill |
| A body class, or data a layout template needs | Method on the theme's `core_renderer` | this skill |
| Different data in a plugin's template | Plugin renderer override: export, change, render the same template | this skill |
| A different glyph or image for an icon | Icon map or `pix_core` / `pix_plugins` | this skill |
| Fewer primary navigation items, no activity title | `config.php` key | this skill |
| A React region's behaviour (**5.3+**) | Template, then PHP exporter, then wrap, then own component | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-renderers-output/versions/moodle-5.3.md) |

A renderer override that copies a core method body is the most expensive row: the copy stops receiving core
fixes at once. Call `parent::` and change the result wherever possible.

## Renderer overrides: the recipe

Three parts must agree. Run on 5.3.0 in a child of Boost (a body class added through `body_attributes()`, seen in a
browser and in a Behat scenario); the factory code is identical in 5.2 (read in the 5.2 source, not run).

`config.php`:

```php
// Not inherited from the parent theme. Without it no theme renderer is used, Boost's included.
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
```

`classes/output/core_renderer.php`:

```php
<?php
// (GPL header)

namespace theme_mytheme\output;

/**
 * Overrides of the core renderer.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class core_renderer extends \theme_boost\output\core_renderer {
    /**
     * Adds a class that says which corner style is in use.
     *
     * @param array|string $additionalclasses
     * @return string
     */
    public function body_attributes($additionalclasses = []) {
        if (!is_array($additionalclasses)) {
            $additionalclasses = explode(' ', $additionalclasses);
        }
        $style = get_config('theme_mytheme', 'cornerstyle') === 'square' ? 'square' : 'round';
        $additionalclasses[] = 'mytheme-corners-' . $style;
        return parent::body_attributes($additionalclasses);
    }
}
```

Purge caches once so the class autoloader sees the new file. No theme revision is involved.

### Rules

1. **`rendererfactory` is not inherited.** The default is `standard_renderer_factory`, which never looks at theme
   classes. Symptom: the theme's `core_renderer` is silently unused, and so is Boost's, which changes the
   breadcrumb, the context header and the edit button and (**5.3+**) empties `{{# output.colour_mode_menu }}`. No
   error is raised. Fix: the line above. Source: `public/lib/classes/output/theme_config.php` (`$rendererfactory`
   default and `get_renderer()`), `public/lib/classes/output/renderer_factory/standard_renderer_factory.php`, 5.3.0
   and 5.2.
2. **Extend Boost's class, not core's.** `\theme_boost\output\core_renderer` carries Boost's overrides
   (`edit_button`, `navbar`, `context_header`, `firstview_fakeblocks`, and on 5.3 `search_box` and
   `colour_mode_menu`). A child that extends `\core_renderer` drops them all, because the first class found wins
   and there is no chaining between themes other than PHP inheritance. In a grandchild theme, extend the nearest
   parent's class. Source: `public/theme/boost/classes/output/core_renderer.php`, 5.3.0 and 5.2.
3. **The class name is the lookup key.** For `$PAGE->get_renderer('core')` the factory tries
   `\theme_mytheme\output\core_renderer`, then the same name in each parent theme, nearest first, then core's.
   A typo in namespace, file name or class name gives no error, only core's output. The full name table for plugin
   and subsystem renderers is in [reference/renderer-lookup.md](moodle-skill-files/moodle-theme-renderers-output/reference/renderer-lookup.md).
4. **Core's special-target renderers beat the theme's general one.** On the `maintenance` page layout, in CLI
   scripts and in `AJAX_SCRIPT` scripts other than `public/lib/ajax/service.php`, the factory first looks for
   `core_renderer_maintenance`, `core_renderer_cli` or `core_renderer_ajax`, and core ships all three. Symptom: a
   method added to the theme's `core_renderer` does not exist during upgrade, on the maintenance screen or from a
   CLI script ("Call to undefined method" or, from Mustache, an empty string). Fix: keep those layouts free of
   theme renderer methods, or also ship `theme_mytheme\output\core_renderer_maintenance` extending
   `\core\output\core_renderer_maintenance`. Source: `renderer_factory_base.php` (`get_target_suffix()`),
   `theme_overridden_renderer_factory.php`, `public/lib/pagelib.php` (`get_renderer()`), 5.3.0 and 5.2.
5. **Keep the parent's signature.** PHP raises a fatal error on an incompatible override, and a narrower one
   breaks callers: `body_attributes()` accepts a string or an array, and layouts pass either. Copy the
   signature from the class being extended on the lowest supported version; the public method signatures of
   `core_renderer` are the same in 5.2 and 5.3 except for one method added in 5.3 (compared with `diff`).
6. **A renderer extending a class that no longer exists is a fatal error** when that renderer is requested.
   **5.3+:** `block_timeline\output\renderer` was removed with no stub, so a theme override of it must be deleted.
   Source: `public/blocks/timeline/UPGRADING.md`, 5.3.0.
7. **Do not use `empty()` or `isset()` on `$this->page->cm`, `->course`, `->url` and the other magic properties.**
   `moodle_page` has `__get()` and no `__isset()`, so they always read as not set. Read the property into a
   variable first. Source: `public/lib/pagelib.php`, 5.3.0 and 5.2.
8. **Everything a renderer returns is raw HTML.** Escape user data with `s()` or `format_string()`, and render
   anything longer than a tag or two from a template.

### A method for a layout template

Layout templates receive the renderer as `output`, and Mustache calls any public method that takes no required
argument. Add the method to the theme's `core_renderer` and call it with triple braces:

```php
    /** @return string The banner HTML, or an empty string when no banner is set. */
    public function mytheme_banner(): string {
        $text = get_config('theme_mytheme', 'bannertext');
        if (empty($text)) {
            return '';
        }
        return $this->render_from_template('theme_mytheme/banner', ['text' => format_string($text)]);
    }
```

```mustache
{{{ output.mytheme_banner }}}
```

A method name that does not exist renders as nothing, with no error: Mustache calls a name only when
`method_exists()` is true (read in `public/lib/mustache/src/Context.php`, 5.3.0 and 5.2; not run as a negative
test). A protected or private method passes that test and is then a fatal error, so keep such methods public.
This is how one template can serve two versions:
`{{# output.colour_mode_menu }}{{{ . }}}{{/ output.colour_mode_menu }}` prints the switcher on 5.3 and nothing on
5.2. Prefix the theme's own methods with the theme name so a later core method of the same name cannot collide.

### Plugin and course format renderers

Find the class the plugin itself uses, extend it, and name the theme class after the component:
`theme_mytheme\output\mod_quiz_renderer`, `theme_mytheme\output\format_topics_renderer`, and for a subtype
`theme_mytheme\output\core\course_renderer` (requested as `get_renderer('core', 'course')`).

Prefer changing the data over copying the template. Read in a published Boost child theme, not run here:

```php
namespace theme_mytheme\output;

use core_courseformat\output\local\content;

class format_topics_renderer extends \format_topics\output\renderer {
    public function render_content(content $widget): string {
        $data = $widget->export_for_template($this);
        $data->mythemecards = (bool) get_config('theme_mytheme', 'sectioncards');
        return $this->render_from_template($widget->get_template_name($this), $data);
    }
}
```

`$renderer->render($widget)` looks for `render_<class name>` on the renderer first, so a method with that name in
a theme renderer takes over that widget; without one, the widget's own template is used. Exported data is often
a `stdClass`, not an array (`action_link` exports `$x->attributes`): read the widget's `export_for_template()`
before changing its result. Source: `public/lib/classes/output/renderer_base.php` (`render()`),
`plugin_renderer_base.php`, 5.3.0 and 5.2.

## Hooks from a theme

A theme registers hook callbacks in `db/hooks.php` like any plugin; `moodle-hooks-api` covers the API. What is
specific to themes is that **callbacks of every installed theme run on every page, whichever theme is in use**,
so each one starts with a guard. Run on 5.3.0 (the meta tag appears only under the theme); the hook classes used
here exist in 5.2 (read in the 5.2 source, not run).

`db/hooks.php`:

```php
<?php
// (GPL header)
defined('MOODLE_INTERNAL') || die();

$callbacks = [
    [
        'hook' => \core\hook\output\before_standard_head_html_generation::class,
        'callback' => [\theme_mytheme\local\hook_callbacks::class, 'before_standard_head_html_generation'],
    ],
];
```

`classes/local/hook_callbacks.php`:

```php
<?php
// (GPL header)
namespace theme_mytheme\local;

use core\hook\output\before_standard_head_html_generation;

// (class docblock with @package, @copyright and @license, as in the renderer sample)
class hook_callbacks {
    /**
     * Adds a theme-color meta tag with the accent colour.
     *
     * @param before_standard_head_html_generation $hook
     */
    public static function before_standard_head_html_generation(before_standard_head_html_generation $hook): void {
        global $PAGE;

        if (during_initial_install()) {
            return;
        }
        if ($PAGE->theme->name !== 'mytheme' && !in_array('mytheme', $PAGE->theme->parents, true)) {
            return;
        }
        $accent = get_config('theme_mytheme', 'accentcolour');
        if (!empty($accent) && preg_match('/^#[0-9a-fA-F]{3,8}$/', $accent)) {
            $hook->add_html('<meta name="theme-color" content="' . s($accent) . '">');
        }
    }
}
```

- The guard accepts child themes on purpose (`in_array(..., $PAGE->theme->parents)`), which is what Boost's own
  callbacks do (`public/theme/boost/classes/colour_mode.php`, `is_boost_theme()`, 5.3.0). Drop that half only when
  a child should not get the behaviour.
- `$PAGE->theme` initialises the theme when read. In the output hooks that is already done. In an early hook such
  as `\core\hook\after_config` it forces the theme to be chosen before the page knows its course or context, and
  the theme's `lib.php` constants are not loaded yet: compare a stored config value there instead.
- `add_html()` takes raw HTML: validate or escape every setting value, as above.
- The same "runs for inactive themes" rule covers plugin-wide `lib.php` callbacks such as
  `theme_mytheme_get_fontawesome_icon_map()`. It does not cover `theme_mytheme_page_init()` or renderer classes,
  which are used only for the current theme and its children.
- A callback for a hook class that the running version does not have is ignored, so a 5.2 to 5.3 theme can register
  5.3-only hooks unconditionally (read in `public/lib/classes/hook/manager.php`, 5.3.0 and 5.2; not run).

The catalogue of output and navigation hooks, with the method each offers and where core dispatches it, is in
[reference/hooks-and-callbacks.md](moodle-skill-files/moodle-theme-renderers-output/reference/hooks-and-callbacks.md).

## Icons and images

`$THEME->iconsystem` is inherited from the parent (unlike `rendererfactory`); Boost sets Font Awesome. With it, an
icon that has an entry in the icon map is drawn as an `<i>` glyph and the image file is never requested; an icon
with no entry is drawn as an `<img>`. That split decides which mechanism works:

| Goal | Mechanism | Trap |
|---|---|---|
| Replace an image file | `pix_core/<path>.svg` for core, `pix_plugins/<type>/<plugin>/<path>.svg` for a plugin | No visible effect for an icon that is in the map |
| Map the theme's own icon to a glyph | `theme_mytheme_get_fontawesome_icon_map()` in `lib.php` | Cannot change an existing key; runs for inactive themes; each key needs a real SVG |
| Change the glyph of a core or plugin icon | Subclass `\core\output\icon_system_fontawesome`, set `$THEME->iconsystem` | Map is cached on the server and in the browser |
| Recolour activity icons | `$activity-icon-<purpose>-bg` variables in pre-SCSS | `color` and `fill` do nothing: the colour is an SVG filter |

Changing a core glyph (read in the source: the Classic theme shipped with 5.2 does exactly this; not run here):

```php
// classes/output/icon_system_fontawesome.php
namespace theme_mytheme\output;

class icon_system_fontawesome extends \core\output\icon_system_fontawesome {
    #[\Override]
    public function get_core_icon_map() {
        $map = parent::get_core_icon_map();
        $map['core:i/navigationitem'] = 'fa-square';
        return $map;
    }
}
```

```php
// config.php
$THEME->iconsystem = '\\theme_mytheme\\output\\icon_system_fontawesome';
```

- After any map change, purge caches. The server caches the map per icon-system class, and the browser keeps its
  own copy in localStorage per theme; a stale browser copy shows as "icons printed by PHP changed, icons drawn by
  JavaScript did not". Source: `public/lib/classes/output/icon_system_fontawesome.php` (`get_icon_name_map()`),
  `public/lib/amd/src/icon_system_fontawesome.js`, 5.3.0.
- Images and fonts resolve in an unusual order: the theme itself, then its parents **farthest first**. With
  `parents = ['middle', 'boost']`, a file in Boost's `pix_core` beats the same file in `middle`. Only the theme's
  own copy is certain to win. Source: `theme_config.php` (`resolve_image_location()`), 5.3.0 and 5.2.
- A request for an image that does not exist is remembered until the next theme cache purge. Adding the file
  afterwards changes nothing until the purge. Source: `public/theme/image.php`, 5.3.0 and 5.2.
- **5.3+:** in dark mode Boost inverts only `<img>` icons whose URL contains `/t/`, `/e/`, `/a/` or one of three
  group icons. Any other image icon, including one a theme adds with a dark stroke, stays dark on a dark page.
  Map it to a glyph, or add a rule under `[data-bs-theme="dark"]`. Source:
  `public/theme/boost/scss/moodle/icons.scss`, 5.3.0.
- `{{#pix}}` and `pix_icon()` are for icon-sized images: they always add the `icon` class and Boost's icon
  sizing. For an illustration use `$OUTPUT->image_url('name', 'theme')` and a plain `<img>`.

The map-building steps, the resolution order for every component, activity icon purposes, deprecated icons and
the favicon rule are in [reference/icons-and-pix.md](moodle-skill-files/moodle-theme-renderers-output/reference/icons-and-pix.md).

## Navigation and the activity header

These are set in `config.php` and read by core classes, so no renderer is needed. None is inherited from the
parent theme: restate them in a child. All read in the source on 5.3.0 and 5.2.

```php
// Hide items of the primary navigation. Keys: home, myhome, courses, siteadminnode.
$THEME->removedprimarynavitems = ['courses'];
// Do not print the activity name as a heading inside the activity header (Boost's value).
$THEME->activityheaderconfig = ['notitle' => true];
```

- `removedprimarynavitems` uses `courses` for the node whose own key is `mycourses`. An unknown key is ignored.
  Source: `public/lib/classes/navigation/views/primary.php`.
- `activityheaderconfig` reads one key, `notitle`. Per layout, `'options' => ['activityheader' => [...]]` accepts
  `notitle`, `nodescription` and `nocompletion`, and the layout value wins over the theme value. Source:
  `public/lib/classes/output/activity_header.php`.
- To add items, register `\core\hook\navigation\primary_extend` (guarded as above). To change what is exported
  to the template, subclass `\core\navigation\output\primary` and instantiate the subclass in the theme's own
  layout file, because Boost's layout files create the core class by name.

The breadcrumb, the context header, the edit switch and the layout options are in
[reference/navigation-and-headers.md](moodle-skill-files/moodle-theme-renderers-output/reference/navigation-and-headers.md).

## React-rendered regions

**5.3+:** the primary navigation, the secondary navigation, the edit-mode switch and the Timeline block are
drawn by React components. The first three are still mounted from Mustache templates a theme can override and
are styled by the theme's SCSS; only the Timeline block is out of reach of templates. A theme can also override
the component itself from `js/esm/src/overrides/`, but that path has no fallback to a parent theme, needs a full
Moodle checkout to build, and no component override was built or run for this skill. Read
[versions/moodle-5.3.md](moodle-skill-files/moodle-theme-renderers-output/versions/moodle-5.3.md) before touching any of these regions. **5.2 only:** none of this
exists; the same regions are Mustache templates with AMD modules.

## Checking the result

- `$OUTPUT` in a CLI script is `core_renderer_cli` (seen on 5.3.0), and a PHPUnit run is a CLI script too, so
  theme renderer and template overrides cannot be judged there. Load a page in a browser or assert on it in Behat;
  in PHPUnit ask for `$PAGE->get_renderer('core', null, RENDERER_TARGET_GENERAL)`: an explicit target is not
  replaced by the CLI default (read in `get_target_suffix()`, 5.3.0 and 5.2; not run).
- Assert the change the override predicts (the body class, the extra element) on a page that uses that layout,
  as the role that will see it. The theme Behat and PHPUnit recipes are in `moodle-theme-testing-release`.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Child theme without `$THEME->rendererfactory` | No theme renderer is used, Boost's included; no error | Set `theme_overridden_renderer_factory` in the child's `config.php` |
| `class core_renderer extends \core_renderer` in a Boost child | Boost's breadcrumb, context header and colour-mode menu are lost | Extend `\theme_boost\output\core_renderer` (or the nearest parent's class) |
| Class in `classes/output/` with the wrong name or namespace | Silently ignored | Match the names in [reference/renderer-lookup.md](moodle-skill-files/moodle-theme-renderers-output/reference/renderer-lookup.md) |
| Using a theme renderer method in the maintenance layout or a CLI script | Method missing: fatal error in PHP, nothing in Mustache | Keep it out, or ship `core_renderer_maintenance` too |
| Copying a core method body into the override | The copy misses later core fixes; **5.3+:** copied 5.2 code calling `user_can_view_profile()` emits deprecation notices | Call `parent::` and change the result |
| Hook callback without an active-theme guard | The theme's markup appears under every theme on the site | Check `$PAGE->theme->name` and `->parents` first |
| `pix_core/t/edit.svg` to change the edit icon | Nothing changes: the icon is a Font Awesome glyph | Change the map through an icon system subclass |
| `get_fontawesome_icon_map()` returning a `core:` key | Ignored: existing keys win | Subclass the icon system |
| Mapping a key with no SVG file behind it | Core's `icon_system_fontawesome_test` fails on every site with the theme installed | Ship `pix/<name>.svg` for each mapped key |
| `empty($this->page->cm)` in a renderer | Always true | `$cm = $this->page->cm; if (!$cm) { ... }` |
| **5.3+:** overriding `block_timeline`'s renderer or templates | Fatal error for the renderer; templates are dead files | Delete them; style with SCSS or override the component |
| **5.3+:** a React component override in a parent theme, expected in the child | The child gets core's component | Re-export it in the child ([versions/moodle-5.3.md](moodle-skill-files/moodle-theme-renderers-output/versions/moodle-5.3.md)) |

## Reference files

| File | Read it when |
|---|---|
| [reference/renderer-lookup.md](moodle-skill-files/moodle-theme-renderers-output/reference/renderer-lookup.md) | Overriding a plugin, subsystem, email or maintenance renderer and the exact class name or parent class is needed; or an override is not being picked up |
| [reference/hooks-and-callbacks.md](moodle-skill-files/moodle-theme-renderers-output/reference/hooks-and-callbacks.md) | Choosing which hook or `lib.php` callback puts markup or attributes in a given place, or checking whether a hook exists on 5.2 |
| [reference/icons-and-pix.md](moodle-skill-files/moodle-theme-renderers-output/reference/icons-and-pix.md) | Changing an icon or image and the simple table above did not settle it: map internals, resolution order, activity icons, deprecated icons, favicon, dark mode |
| [reference/navigation-and-headers.md](moodle-skill-files/moodle-theme-renderers-output/reference/navigation-and-headers.md) | Changing primary or secondary navigation data, the breadcrumb, the context header, the activity header or the edit switch from PHP |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-theme-renderers-output/versions/moodle-5.2.md): what the baseline lacks or still has (legacy menus, `render_login()` in Boost, no Boost hooks) |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-renderers-output/versions/moodle-5.3.md): renderer and hook changes, React-rendered regions, component overrides |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme
- https://moodledev.io/docs/5.3/apis/subsystems/output
- https://moodledev.io/docs/5.3/apis/core/hooks
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/images
- https://moodledev.io/docs/5.3/guides/javascript/react/theming (its "Since 5.2" tag is wrong: the code is in 5.3 only)
- https://moodledev.io/general/development/policies/deprecation/icon-deprecation


---

### moodle-theme-scss

> Use when writing or debugging a Moodle theme's SCSS or CSS - `$THEME->scss`, `prescsscallback` / `extrascsscallback`, pre.scss and post.scss, `@import` paths that must work on 5.2 and 5.3, Bootstrap variables and `!default`, `--bs-*` / `--mds-*` custom properties and design tokens, dark mode (`data-bs-theme`), re-branding, presets, fonts, `[[pix:]]` / `[[font:]]`, RTL directives, editor SCSS, stylelint, or when a theme renders as plain Boost ("Error while compiling SCSS", "file not found for @import"). Skip when the task is theme structure or caches (moodle-theme-development), layouts or templates (moodle-theme-layouts-templates), renderers or icons (moodle-theme-renderers-output), the settings page (moodle-theme-settings), proving the styles with tests (moodle-theme-testing-release), or contrast and markup rules for a plugin page (moodle-accessibility).

# Moodle Theme SCSS

## Overview

How a Boost-based theme's stylesheet is assembled and compiled on Moodle 5.2 and 5.3, the recipe that works when
copied, and the traps that make a theme silently fall back to stock Boost or break in dark mode, RTL or the editor.

Evidence tags used below: **run 5.3.0** means observed in a child theme of Boost on Moodle 5.3.0. **read** means read
in the source of the named version and not run. Nothing here was run on Moodle 5.2; every 5.2 statement is "read".

## When to Use

- Adding or changing SCSS in a theme: variables, rules, imports, presets, fonts, background images
- Making a theme follow the 5.3 colour modes, or re-branding it (brand colour, typeface, radius)
- The theme "does nothing": the page looks like plain Boost, or a variable override has no effect
- RTL, editor content or stylelint problems in a theme's styles
- **Skip when:** the question is which files a theme needs or how caches and purges work (`moodle-theme-development`),
  how a setting reaches SCSS (`moodle-theme-settings`), page structure or template markup
  (`moodle-theme-layouts-templates`), icon maps and `pix_core` overrides (`moodle-theme-renderers-output`), or proving
  the result with PHPUnit, Behat and CI (`moodle-theme-testing-release`). The minimal child theme around this SCSS is in
  `moodle-theme-boost-child`.

## How the stylesheet is built

One SCSS string is compiled per theme and direction. `theme_config::get_css_content_from_scss()` concatenates three
parts and compiles them with scssphp 1.12.1 (the same compiler version in 5.2 and 5.3;
`public/lib/classes/output/theme_config.php`, `public/lib/classes/scss.php`, read in both).

```
1. pre-SCSS callbacks    every parent's prescsscallback, base parent first, then the theme's own.
                         Boost's emits: $primary from the brandcolor setting, $behatsite, the scsspre setting.
2. main SCSS             the string returned by the $THEME->scss closure. In the recipe below:
                           your pre.scss      variables, each with !default
                           Boost's preset     tokens, variables (!default), Font Awesome, Bootstrap, Moodle partials
                           your post.scss     rules; every variable, mixin and function now exists
3. extra-SCSS callbacks  every parent's extrascsscallback, base first, then the theme's own.
                         Boost's emits: the raw SCSS setting (scss) and the background image rules.
then post_process():     [[pix:...]] and [[font:...]] become URLs, csspostprocess runs and
                         the all-rtl build is flipped; get_css_content() then minifies the result.
```

- Every callback receives the theme being compiled, so Boost's callbacks read the child's settings: a `brandcolor`
  saved under `theme_mytheme` turned `.btn-primary` that colour with no code in the child (**run 5.3.0**). Do not copy
  Boost's callbacks into the child; that emits everything twice.
- The served sheet is: every plugin's `styles.css`, then parent themes' `sheets`, then this compiled SCSS, then the
  theme's own `sheets` (`theme_config::get_css_files()`, read 5.3.0). Theme rules come after plugin rules, so at equal
  specificity the theme wins.
- A compile error is caught and reported only as a developer-level debugging message; the precompiled CSS of the
  parents is served instead. See "When the compile fails".

## The default recipe

Works on 5.2 and 5.3. Files live in `scss/mytheme/` so that no file name collides with one of Boost's (see mistakes).

```php
// config.php (GPL header) - only the keys that concern styles.
$THEME->parents = ['boost'];
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->scss = function ($theme) {
    return theme_mytheme_get_main_scss_content($theme);
};
$THEME->prescsscallback = 'theme_mytheme_get_pre_scss';
$THEME->extrascsscallback = 'theme_mytheme_get_extra_scss';
// Leave editor_scss and precompiledcsscallback unset: Boost's are used. usefallback is not inherited
// (default false); whether to restate it is in moodle-theme-boost-child.
```

```php
// lib.php (GPL header)
function theme_mytheme_get_main_scss_content($theme) {
    global $CFG;
    require_once($CFG->dirroot . '/theme/boost/lib.php');
    $pre = file_get_contents(__DIR__ . '/scss/mytheme/pre.scss');
    $post = file_get_contents(__DIR__ . '/scss/mytheme/post.scss');
    // Boost returns the preset chosen in the settings of the theme it is given. Pass Boost's config to follow
    // the preset the admin chose for Boost. The preset file differs between 5.2 and 5.3, so never ship a copy.
    $boost = theme_config::load('boost');
    return $pre . "\n" . theme_boost_get_main_scss_content($boost) . "\n" . $post;
}

function theme_mytheme_get_pre_scss($theme) {
    $scss = '';
    $accent = get_config('theme_mytheme', 'accentcolour');
    // Validate before interpolating: the value is compiled as SCSS.
    if (!empty($accent) && preg_match('/^#[0-9a-fA-F]{3,8}$/', $accent)) {
        $scss .= '$mytheme-accent: ' . $accent . ";\n";
    }
    return $scss;
}

function theme_mytheme_get_extra_scss($theme) {
    return '';
}
```

```scss
// scss/mytheme/pre.scss - runs after the pre-SCSS callbacks, before Boost's preset.
$mytheme-accent: #b8410c !default;   // !default, so a value from the settings callback wins.
$mytheme-radius: .75rem !default;

$border-radius: $mytheme-radius !default;        // Bootstrap variables: set them here, before the preset reads them.
$card-border-radius: $mytheme-radius !default;
```

```scss
// scss/mytheme/post.scss - rules, after everything in Boost.
.mytheme-banner {
    padding: .75rem 1rem;
    border-left: .5rem solid $mytheme-accent;    // Flipped to border-right in the RTL build.
    border-radius: $mytheme-radius;
    background-color: var(--bs-tertiary-bg);     // Custom properties follow the colour mode.
    color: var(--bs-body-color);
}

[data-bs-theme="dark"] {
    .mytheme-banner {
        border-left-color: lighten($mytheme-accent, 25%);
    }
}
```

This shape was compiled on 5.3.0: the setting reached the compiled CSS, `border-left` became `border-right` in the RTL
build, and the banner changed under `data-bs-theme="dark"` (**run 5.3.0**).

## What exists at each stage

| Stage | Can use | Cannot use | Put here |
|---|---|---|---|
| pre-SCSS callback, `pre.scss` | literals; Sass built-ins (`mix()`, `lighten()`, `rgba()`); your own variables | `$gray-*`, `$primary` unless you set it, `$mds-*`, Bootstrap functions (`tint-color()`, `shade-color()`), any mixin | variable values |
| `post.scss`, extra-SCSS callback | everything: Bootstrap and Boost variables, mixins, functions, `$mds-*` tokens | changing a variable for code that was already compiled | rules |

- A variable set in pre-SCSS wins because Boost and Bootstrap assign theirs with `!default`. Symptom when ignored: a
  variable assigned in `post.scss` changes nothing above it.
- Three preset variables are assigned without `!default` and ignore pre-SCSS: `$card-group-margin`,
  `$dropdown-link-hover-color`, `$dropdown-link-hover-bg` (`public/theme/boost/scss/preset/default.scss`, read 5.2 and
  5.3). Override the resulting CSS in `post.scss` instead.
- An undefined variable or function in pre-SCSS is a compile error, and so a silent fallback (read 5.3.0:
  scssphp throws; the engine catches).
- `mixin-exists()`, `function-exists()` and `variable-exists()` work in scssphp 1.12.1, but in pre-SCSS they are false
  for everything Boost defines, on every version. Test in `post.scss` only.
- Prefix your own variables, mixins and classes (`$mytheme-`, `.mytheme-`). Boost's compatibility layer defines global
  helpers named `hover()`, `hover-focus()`, `sr-only()`, `sr-only-focusable()`, `badge-variant()` and `color-yiq()`
  (`public/theme/boost/scss/moodle/bs4-compat.scss`, read 5.2 and 5.3); it is due for removal in Moodle 6.0, so do not
  call them either.

## Imports that work on both versions

5.3 moved Bootstrap, Font Awesome and the design system out of Boost into `lib/bundles/` at the Moodle root. Only the
wrapper names survive in `public/theme/boost/scss/`.

| Import | 5.2 | 5.3 |
|---|---|---|
| `@import "bootstrap";` `"fontawesome";` `"design-system";` `"moodle";` `"preset/default";` | yes | yes |
| `"moodle/<partial>"` for a partial that exists in both (`moodle/variables`, `moodle/core`, ...) | yes | yes |
| `"bootstrap/<anything>"`, `"fontawesome/<anything>"`, `"design-system/tokens/scss/..."` | yes | **no** |
| `"design-system-tokens"`, `"moodle/colour-mode"`, `"moodle/dark"`, `"moodle/fonts"`, `"moodle/font-stack"`, `"moodle/font-stack-lang"`, `"../../../../lib/bundles/..."` | **no** | yes |

- `@import "bootstrap/functions";` on 5.3 fails with "file not found for @import" and the whole theme falls back to
  stock Boost (**run 5.3.0**). With the recipe above you need no import at all: by `post.scss` everything is loaded.
- Import lookup order is the importing file's own directory, then the theme's `scss/`, then each parent's `scss/`
  (`theme_config::get_scss_property()`; `public/lib/scssphp/src/Compiler.php` `findImport()`, read 5.3.0). The preset
  text is compiled as a string with no directory, so its `@import "moodle"` finds `scss/moodle.scss` in the child
  first. A child file named `moodle.scss`, `bootstrap.scss`, `fontawesome.scss` or `design-system.scss` therefore
  replaces Boost's. Do that only on purpose, and then import Boost's file from inside it by relative path.
- An imported file must end in `.scss` and sit under a theme directory (**5.3+:** or under `lib/bundles`); anything
  else is skipped with a developer debugging message "Can't import scss file" (`core_scss::is_valid_file()`, read).

## Colours and dark mode

**5.3+:** Boost has light and dark colour modes, off by default (`theme_boost | enablecolourmodes`, Experimental
settings tab). The settings are read from `theme_boost`, not from the child, and apply to every theme with `boost` in
its parents (`public/theme/boost/classes/colour_mode.php`, read 5.3.0). A child theme cannot opt out: once the admin
enables the feature, the child's pages get `<html data-bs-theme="dark">`. Write for both modes even in a "5.2 theme".

1. **Scope dark rules by `[data-bs-theme="dark"]`, never `@media (prefers-color-scheme: dark)`.** The user's choice
   and the site default override the device, so a media query styles light pages dark and the reverse
   (https://moodledev.io/docs/5.3/guides/colourmodes). On 5.2 nothing sets the attribute, so the rules are inert.
2. **Take surfaces and text from custom properties**, not SCSS colour variables. An SCSS variable is resolved at
   compile time and cannot follow a per-request mode. Safe on 5.2 and 5.3 (Bootstrap 5.3 emits them in both):
   `--bs-body-bg`, `--bs-body-color`, `--bs-secondary-bg`, `--bs-tertiary-bg`, `--bs-border-color`,
   `--bs-emphasis-color`, `--bs-link-color`, `--bs-gray-100` to `--bs-gray-900`, `--bs-white`, `--bs-black`.
   **5.3+:** in dark mode Boost re-points the greys: `--bs-white` is the raised surface (cards), `--bs-gray-100` the
   page, `--bs-gray-200` a recessed area, and the high numbers become light text colours.
3. **A literal is a bug when it is half of a pair**: a fixed background behind mode-following text, or the reverse.
   Symptom: unreadable text in one mode. Brand accents that are legible on both surfaces may stay literal; check
   contrast in both modes.
4. **5.3+:** Boost's helpers for `post.scss`: `@include dark-mode { ... }` inside a rule (prefixes the enclosing
   selector, so it outranks the rule it corrects; compiled, **run 5.3.0**) and `dark-readable($color)`, which tints a
   colour until it reaches 4.6:1 on a dark raised surface (`public/theme/boost/scss/moodle/colour-mode.scss`). Neither
   exists on 5.2, where using them is a compile error. For a theme that supports both, write the selector yourself as
   in the recipe, or ship a prefixed copy of the mixin (same compiler on both versions; not run on 5.2):

```scss
@mixin mytheme-dark {
    @at-root #{selector-nest('[data-bs-theme="dark"]', &)} {
        @content;
    }
}
```

5. **Do not write a bare `:root { --bs-...: ...; }` or `:root { --mds-...: ...; }` in post or extra SCSS.** It has the
   same specificity as `[data-bs-theme=dark]`, both match `<html>`, and yours comes later, so it overrides the dark
   palette (cascade reasoning; not checked in a browser). Set the SCSS variable in pre-SCSS, or scope light values:
   `:root:not([data-bs-theme="dark"]) { ... }`.
6. **5.3+:** some variables that were colours in 5.2 are `var(...)` strings in 5.3 (`$state-*-bg`, `$state-*-border`,
   `$dialogue-*`, `$card-bg`, `$card-border-color` and about forty more). `darken($state-success-bg, 5%)`, and likewise
   `lighten()`, `mix()`, `tint-color()` and `shade-color()`, compiles on 5.2 and is a compile error on 5.3:
   "$color: var(--bs-state-success-bg) is not a color." `rgba($dialogue-base-bg, .9)` does not fail: it is emitted as
   `rgba(var(...), .9)`, which browsers drop, so the declaration silently has no effect (both read in
   `public/lib/scssphp/src/Compiler.php`, not run). Derive from `$success`, `$gray-*` or a literal instead. The list
   is in the 5.3 version notes.
7. **5.3+:** setting `$card-bg`, `$card-border-color`, `$state-*-bg` or `$input-border-color` to a literal stops that
   component following the mode. Set a colour the dark palette can re-point (a `var(--bs-...)`), as Boost does.
8. Icons drawn as Font Awesome glyphs follow the text colour. An `<img>` icon keeps its baked-in colours; Boost
   inverts only a fixed list of core paths in dark mode. Details in the dark mode reference.

## Custom properties: `--bs-*` and `--mds-*`

- `--bs-*` comes from Bootstrap 5.3 and exists on 5.2 and 5.3. `--mds-*` (Moodle Design System tokens, 354 of them)
  exists only on 5.3 and only on the main page: not on 5.2 (0 matches in 5.2's compiled Boost CSS) and not inside
  the editor content iframe.
- **An undefined custom property is silent.** `var(--x, #fff)` uses the fallback on every theme and mode, so the rule
  looks right only where the fallback happens to fit. Fix: check each name once on the target version,
  `getComputedStyle(document.documentElement).getPropertyValue('--mds-bg-surface-default')` (empty string means
  undefined), and for 5.2 plus 5.3 chain a property that exists on both:
  `color: var(--mds-text-default, var(--bs-body-color));`.
- The `$mds-*` SCSS variables exist on both versions (295 on 5.2, 354 on 5.3), but several values changed
  (`$mds-border-radius-md` is `.375rem` on 5.2 and `.5rem` on 5.3). Do not rely on a token for a size that must be
  identical on both.
- The two families are not parallel: `--mds-border-translucent` is fully transparent in light mode, unlike
  `--bs-border-color-translucent`. Check both values before swapping one for the other.

## Re-branding

- Brand colour: Boost's `brandcolor` setting (declared under the child's component) or `$primary` in pre-SCSS. Theme
  colours are baked into Bootstrap components at compile time (`.btn-primary` carries literals).
- **5.3+:** nothing links `$primary` to the design system's primary tokens in light mode, so with only `$primary`
  changed the `.mds-*` components core renders (navigation pills, switch, buttons, badges), token-based links and
  focus outlines stay Moodle blue in light mode, while dark mode derives them from `$primary` (read 5.3.0:
  `scss/moodle/dark.scss`; the only light-mode link is the edit switch in `scss/moodle/primarynavigation.scss`).
  The fix is to set the `$mds-*-primary-*` tokens in pre-SCSS too. The recipe is in the re-brand reference; it was
  built from the source and has not been compiled.
- Typeface: set `$font-family-sans-serif` in pre-SCSS. **5.3+:** also set `$mds-font-family-base`, or design system
  components and `:lang(ja)` content keep Noto Sans.
- **5.3 changed the default look without a theme changing a line:** page background `$gray-100` instead of white,
  self-hosted Noto Sans instead of the system font stack, and no navbar box-shadow in the preset. A theme tuned on 5.2
  should set `$body-bg` and `$font-family-sans-serif` explicitly if it wants the old look.

## Fonts, images, RTL and the editor in one paragraph each

- **Images and fonts in SCSS** are written as placeholders, never as paths: `url([[pix:theme|hero]])` for
  `pix/hero.svg|png` in the theme, `url([[pix:t/collapsed]])` for a core icon, and
  `url('[[font:theme|mysans.woff2]]')` for `fonts/mysans.woff2`. **5.3+:** fonts may sit in subfolders
  (`[[font:theme|my-sans/regular.woff2]]`); on 5.2 that URL is a 404, so a 5.2-compatible theme keeps `fonts/` flat.
  Core does not replace `[[setting:name]]`: only `[[pix:]]` and `[[font:]]` (`theme_config::post_process()`, read
  5.3.0). Pass settings as SCSS variables from the pre-SCSS callback.
- **RTL is automatic.** There is one source; the `all-rtl` build is the same CSS with left/right flipped
  (**run 5.3.0**). Write LTR, prefer logical properties in new code, and correct by hand what the flipper skips:
  `transform`, `box-shadow`, gradients, `inset`. A rule whose selector contains `.dir-rtl` is left untouched.
  Directives are CSS comments placed before a declaration: `/*rtl:ignore*/`, `/*rtl:remove*/`, `/*rtl:raw: ...*/`.
- **Editor content is a separate document.** TinyMCE loads only the editor sheet, built from `editor_scss` with no
  pre or extra callbacks, so theme settings and `post.scss` never reach it. A child that sets
  `$THEME->editor_scss = ['editor']` without shipping `scss/editor.scss` loses Boost's editor styles (read 5.3.0).
  Leave the key unset unless you ship the file.
- Theme SCSS also never enters H5P content: that iframe takes CSS only from the `core_h5p | h5pcustomcss` setting.

## When the compile fails

Symptom: the page looks like plain Boost, with none of the theme's rules and no error on screen (**run 5.3.0**).
`get_css_content()` substitutes the parents' precompiled CSS, and `public/theme/styles.php` defines `NO_DEBUG_DISPLAY`,
so in a browser the message goes only to the PHP error log.

To see the error, compile from the command line with developer debugging on (`$CFG->debug = E_ALL;` and
`$CFG->debugdisplay = 1;` in a development `config.php`); the message "Error while compiling SCSS: ..." names the
cause (**run 5.3.0** for the message, seen with a separate compile script; the command below calls the same
`get_css_content()` through `theme_build_css_for_themes()`, read in `public/lib/outputlib.php`, not run):

```bash
php admin/cli/build_theme_css.php --themes=mytheme --direction=ltr
```

- That command also caches what it built. After fixing the SCSS, run it again or purge caches, or the fallback CSS
  stays cached.
- A PHPUnit test that calls `theme_config::load('mytheme')->get_css_content()` and asserts one of the theme's own
  selectors is in the result catches every case here, because the fallback contains none of them
  (`moodle-theme-testing-release` has the test).
- Usual causes: a 5.2-only import path on 5.3; a 5.3-only mixin or partial on 5.2; `darken()` or `mix()` applied to
  a `var(...)` variable; an undefined variable in pre-SCSS; invalid SCSS typed into a raw SCSS setting.
- A different effect with the same look: when the theme's own `config.php` sets `$THEME->usefallback = true` (the
  key is not inherited from Boost), the first stylesheet request after a purge can be answered with the previous
  build while the new one compiles. Reload once before debugging. Cache behaviour is in `moodle-theme-development`.

## Cascade facts that decide whether a rule applies

- "The rule is in the served sheet" is not "the rule applies". Prove arrival by searching the stylesheet the page
  links (`/theme/styles.php/<theme>/<rev>/all`) for the selector, then prove effect with `getComputedStyle()` on the
  element, in the mode and direction that matter.
- Bootstrap components read their own custom properties. To restyle one, set those from a selector that outranks
  the component rule, rather than fighting declarations:

```scss
.btn.mytheme-share {
    --bs-btn-bg: var(--bs-primary);
    --bs-btn-color: var(--bs-white);
}
```

- Bootstrap utilities such as `.d-flex` and `.d-none` use `!important`, so the `hidden` attribute and ordinary rules
  lose to them. Toggle `.d-none` instead.
- `animation-fill-mode: both` or `forwards` pins the last keyframe above every later declaration for that property.
  Use `backwards` when the element must stay restylable after the animation.
- Bootstrap 4 class names (`.ml-2`, `.float-right`, `.font-weight-bold`, `.sr-only`, `.badge-primary`,
  `.custom-select`, `.media`) still work only through Boost's compatibility layer, removal planned for 6.0. Each use
  shows a red "Deprecated style in use" marker in theme designer mode and fails Behat runs started with
  `--scss-deprecations` (`public/theme/boost/scss/moodle/deprecated.scss`, `bs4-compat.scss`; read 5.2 and 5.3,
  identical; the Behat failure was not run). Write `.ms-2`, `.float-end`, `.fw-bold`, `.visually-hidden` in templates and in markup built by
  JavaScript.
- Boost's fixed navbar is `$navbar-height: 60px` (`scss/moodle/variables.scss`). Offsets for sticky or scrolled-to
  elements start below it, not at 0.

## Stylelint

`moodle-plugin-ci grunt` lints a theme's whole `scss/` tree with core's `.stylelintrc`, identical in 5.2 and 5.3
(read; moodle-plugin-ci 4.5.11). With an `scss/` directory present, the theme's `style/*.css` is not linted. Locally,
from the Moodle root with the Node dependencies installed: `npx stylelint "public/theme/mytheme/scss/**/*.scss"`
(**run 5.3.0**). What trips most often: `!important` without a disable comment, single-line rule blocks, indentation
other than four spaces, `data:` URLs, durations under 100 ms, upper-case or long hex colours (warnings, but CI allows
none), and syntax the validator does not know (`container-type`, `@container`). The rule list and the disable
comments are in the build and lint reference.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `@import "bootstrap/functions"` (or any Bootstrap, Font Awesome or token partial) | 5.3: "file not found for @import", whole theme falls back to stock Boost (**run 5.3.0**) | Import nothing in `post.scss`; elsewhere use only the wrapper names |
| Shipping a copy of Boost's `preset/default.scss` | A 5.3 copy fails on 5.2 (`moodle/font-stack` missing); a 5.2 copy on 5.3 loses fonts, grey body and mode-following cards (read) | Call `theme_boost_get_main_scss_content()` at compile time |
| Variable override placed in `post.scss` | No effect on Bootstrap or Boost output | Move it to `pre.scss` or the pre-SCSS callback |
| `darken()`, `mix()` or `rgba()` on `$state-*-bg`, `$dialogue-*` or `$card-bg` | 5.3: "is not a color" compile error and fallback; with `rgba()` a declaration that browsers drop (read) | Derive from `$success`, `$gray-*` or a literal |
| `$gray-200`, `tint-color()` or `@include` in pre-SCSS | Compile error, silent fallback | Literals and Sass built-ins only in pre-SCSS |
| Repeating Boost's pre or extra SCSS callback code in the child | Brand colour and raw SCSS emitted twice | Rely on the inherited callbacks; add only your own |
| `$THEME->scss = 'main';` (a file name) in a child | Only the child's `scss/` is an import path, so `@import "moodle"` is not found (read: `core_scss::set_file()`) | Use the closure form |
| No `$THEME->scss` in the child, but files in its `scss/` | Boost's closure is used and the child's `scss/` is not on the import path (read: `get_scss_property()`) | Set the closure in the child |
| Child file `scss/moodle.scss` or `scss/bootstrap.scss` created by accident | It replaces Boost's file of that name; most of the page loses its styles | Keep theme files in `scss/mytheme/` |
| `@media (prefers-color-scheme: dark)` | Dark rules on light pages and the reverse | `[data-bs-theme="dark"]` |
| `@include dark-mode` in a theme that supports 5.2 | Compile error on 5.2 (read) | Plain selector, or a prefixed copy of the mixin |
| `var(--mds-...)` with no fallback in a 5.2-5.3 theme, or in editor CSS | Property undefined there: the declaration has no effect | `var(--mds-x, var(--bs-y))` |
| `background: #fff` behind inherited text | White box with light text in dark mode | `var(--bs-body-bg)` or a utility class (`bg-body`) |
| `[[setting:brand]]` in SCSS | Printed literally; core has no such placeholder | SCSS variable from the pre-SCSS callback |
| Raw setting value interpolated into SCSS | A bad value breaks the compile for the whole site, or injects rules | Validate with a pattern before emitting |
| `$THEME->editor_scss = ['editor']` with no `scss/editor.scss` | Editor content loses Bootstrap, fonts and the dark palette (read 5.3.0, not run) | Leave it unset, or ship the file |
| `/* rtl:ignore */` as the last thing in a rule, or written as `//` | Directive does nothing | Put a `/* */` directive directly before a declaration |
| Judging CSS on the first load after a purge | With `usefallback` on, the old stylesheet can be served once | Reload, then check the computed style |

## Reference files

| File | Read it when |
|---|---|
| [reference/design-tokens.md](moodle-skill-files/moodle-theme-scss/reference/design-tokens.md) | You need a `--mds-*` / `$mds-*` token name, its light or dark value, or which tokens are safe for mode-following CSS |
| [reference/rebrand-and-presets.md](moodle-skill-files/moodle-theme-scss/reference/rebrand-and-presets.md) | Changing the brand colour, typeface, radius or dark surfaces across the whole theme; checking which Bootstrap variables Boost's preset sets; offering or writing a preset |
| [reference/dark-mode.md](moodle-skill-files/moodle-theme-scss/reference/dark-mode.md) | A page, component or icon looks wrong in dark mode, or you need what Boost's dark palette re-points and how the mode reaches the page |
| [reference/rtl.md](moodle-skill-files/moodle-theme-scss/reference/rtl.md) | The theme must look right in a right-to-left language, a rule must not be flipped, or you need an RTL build to inspect |
| [reference/fonts-and-images.md](moodle-skill-files/moodle-theme-scss/reference/fonts-and-images.md) | Shipping a web font, replacing Boost's typeface, or using `[[font:]]` / `[[pix:]]` beyond the one-line form |
| [reference/editor-css.md](moodle-skill-files/moodle-theme-scss/reference/editor-css.md) | Content inside the TinyMCE editor must be styled, or the editor lost its styles |
| [reference/build-and-lint.md](moodle-skill-files/moodle-theme-scss/reference/build-and-lint.md) | Stylelint fails or must be silenced, CI lints the theme, or you are considering a precompiled fallback stylesheet |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-theme-scss/versions/moodle-5.2.md): where the libraries live, what only resolves on 5.2, what is absent |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-scss/versions/moodle-5.3.md): `lib/bundles`, new partials and helpers, variables that became `var()`, the plain preset |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme/styles
- https://moodledev.io/docs/5.3/guides/colourmodes
- https://moodledev.io/docs/5.3/guides/bs5migration
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/fonts (out of date on core font location, subfolders and
  `.woff2`; `public/theme/font.php` and `theme_config::resolve_font_location()` are the authority)
- https://moodledev.io/general/development/policies/codingstyle/css
- https://moodledev.io/general/designsystem/overview


---

### moodle-theme-settings

> Use when adding or fixing a Moodle theme's admin settings - theme settings.php, themesetting<name> section, theme_boost_admin_settingspage_tabs, admin_setting_configcolourpicker, admin_setting_configstoredfile, admin_setting_scsscode, hide_if, set_updatedcallback('theme_reset_all_caches'), $theme->settings versus get_config('theme_x'), setting to SCSS variable, setting to template context, setting_file_url / setting_file_serve / theme_x_pluginfile, renaming settings in db/upgrade.php, theme user preferences and the privacy provider that declares them; symptoms such as "Section error" from the theme selector cog, a saved setting that changes nothing, a 404 logo, or stock Boost styling after saving a setting. Skip when the task is the SCSS itself (moodle-theme-scss), layouts or templates (moodle-theme-layouts-templates), or settings of a non-theme plugin (moodle-plugin-development).

# Moodle Theme Settings

## Overview

How a theme declares admin settings, how each value reaches the compiled CSS, the templates and the file server,
and how to change settings later without losing what sites have saved. Everything here holds on Moodle 5.2 and 5.3
unless tagged. "Run on 5.3.0" means the behaviour was observed in a Boost child theme on Moodle 5.3.0; "read in the
source" means it was read and not run. Nothing here was run on 5.2: 5.2 statements are read in the 5.2 source.

## When to Use

- Writing or changing a theme's `settings.php`, or the code that reads its settings
- A setting must change the CSS (colour, radius, font, background image) or show something in a template
- An uploaded logo or image from a setting must be served
- Renaming, splitting or converting a setting between releases
- The theme stores a per-user choice (a drawer, a display mode) and needs a preference and a privacy provider
- **Skip when:** the question is what SCSS to write once the variable exists (use `moodle-theme-scss`); where the
  template or layout lives (`moodle-theme-layouts-templates`); a renderer or hook (`moodle-theme-renderers-output`);
  which Boost settings a child inherits and how presets work (`moodle-theme-boost-child`); testing a setting's effect
  (`moodle-theme-testing-release`); admin settings of other plugin types (`moodle-plugin-development`)

## Mental model

1. **Storage.** A setting named `theme_mytheme/accent` is one row in `config_plugins` (plugin `theme_mytheme`, name
   `accent`). Uploaded files live in the system context, component `theme_mytheme`, file area chosen by the setting,
   item id 0. Nothing else exists: no table, no backup. Uninstalling the theme deletes both.
2. **Two ways to read, with different meaning.**
   - `get_config('theme_mytheme', 'accent')` always reads this theme's own row. It returns `false` when the value
     was never stored.
   - `$theme->settings->accent` (the object passed to SCSS callbacks, or `$PAGE->theme->settings`) reads the
     settings of the **active** theme. `theme_config::load()` reads `get_config('theme_<active>')` once and hands
     that same object to every parent's `config.php` and to every parent's SCSS callback
     (`public/lib/classes/output/theme_config.php`, `load()` and `find_theme_config()`, 5.2 and 5.3).
   - So: a value that belongs to your theme is read with `get_config()`. A value that a child theme should be
     able to supply under its own component is read from `$theme->settings`. Boost's callbacks use the second
     form, which is why a child gets `brandcolor`, `scsspre`, `scss` and the background images by declaring
     settings with those names (run on 5.3.0 for `brandcolor`).
3. **When a value takes effect.** PHP and templates read the value on every request. CSS is compiled once and
   cached by theme revision, so a setting that feeds SCSS does nothing until the revision changes. The admin page
   does that through the setting's updated-callback; code that calls `set_config()` must do it itself.
4. **When a default is stored.** Defaults are written by the upgrade (CLI upgrade, or the "new settings" page the
   web upgrade shows), and on install. Between those moments a new setting has no row, and reads return `false`.
5. **The page.** Core makes a settings page object for every theme that has `settings.php` and names it
   `themesetting<name>`. The cog on the theme selector links to `admin/settings.php?section=themesetting<name>`.
   The page that core hands over is created hidden, and core adds the page to the admin tree only if it is not
   hidden. A theme therefore replaces `$settings` with its own page object of the same name
   (`public/admin/settings/appearance.php`, `public/admin/themeselector.php`, 5.2 and 5.3; read in the source).

## Default recipe

A tabbed page with a colour, a select, a dependent text field and an uploaded image. Run on 5.3.0 as shown, except
the upload path and the `theme_config::load('mytheme')` form of the file URL, which were read (see "Stored files").

### settings.php

```php
<?php
// (GPL header, then the file phpdoc with @package theme_mytheme and @copyright 2026 Your Name <you@example.com>)

defined('MOODLE_INTERNAL') || die();

if ($ADMIN->fulltree) {
    // Same name as the page core created, so the theme selector link works.
    $settings = new theme_boost_admin_settingspage_tabs('themesettingmytheme', get_string('configtitle', 'theme_mytheme'));

    // Tab: Look. The tab name becomes an HTML id, so prefix it with the component.
    $page = new admin_settingpage('theme_mytheme_look', get_string('looksettings', 'theme_mytheme'));

    $setting = new admin_setting_configcolourpicker(
        'theme_mytheme/accent',
        get_string('accent', 'theme_mytheme'),
        get_string('accent_desc', 'theme_mytheme'),
        ''
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $setting = new admin_setting_configselect(
        'theme_mytheme/corners',
        get_string('corners', 'theme_mytheme'),
        get_string('corners_desc', 'theme_mytheme'),
        'round',
        [
            'round' => get_string('corners_round', 'theme_mytheme'),
            'square' => get_string('corners_square', 'theme_mytheme'),
        ]
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    // Add the tab only after all its settings: add() copies the settings that exist at that moment.
    $settings->add($page);

    // Tab: Banner.
    $page = new admin_settingpage('theme_mytheme_banner', get_string('bannersettings', 'theme_mytheme'));

    $setting = new admin_setting_configselect(
        'theme_mytheme/bannermode',
        get_string('bannermode', 'theme_mytheme'),
        get_string('bannermode_desc', 'theme_mytheme'),
        'none',
        [
            'none' => get_string('bannermode_none', 'theme_mytheme'),
            'text' => get_string('bannermode_text', 'theme_mytheme'),
        ]
    );
    $page->add($setting);

    $setting = new admin_setting_configtext(
        'theme_mytheme/bannertext',
        get_string('bannertext', 'theme_mytheme'),
        get_string('bannertext_desc', 'theme_mytheme'),
        '',
        PARAM_TEXT
    );
    $page->add($setting);

    $setting = new admin_setting_configstoredfile(
        'theme_mytheme/bannerimage',
        get_string('bannerimage', 'theme_mytheme'),
        get_string('bannerimage_desc', 'theme_mytheme'),
        'bannerimage',
        0,
        ['maxfiles' => 1, 'accepted_types' => ['web_image']]
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $settings->add($page);

    // Dependencies go on the outer page, after the tab was added.
    $settings->hide_if('theme_mytheme/bannertext', 'theme_mytheme/bannermode', 'eq', 'none');
}
```

A theme with few settings can skip the tabs: `$settings = new admin_settingpage('themesettingmytheme', ...)` inside
the same `if`, then `$settings->add($setting)`.

### lib.php: setting to SCSS

```php
// (phpdoc blocks shortened in this sample.)

/** SCSS variables from this theme's settings, placed before the main SCSS. */
function theme_mytheme_get_pre_scss($theme) {
    $scss = '';
    $accent = get_config('theme_mytheme', 'accent');
    if (!empty($accent) && preg_match('/^#([0-9a-fA-F]{3}){1,2}$/', $accent)) {
        $scss .= '$mytheme-accent: ' . $accent . ";\n";
    }
    if (get_config('theme_mytheme', 'corners') === 'square') {
        $scss .= "\$mytheme-radius: 0;\n";
    }
    return $scss;
}

/** SCSS built from this theme's settings, placed after the main SCSS. */
function theme_mytheme_get_extra_scss($theme) {
    $scss = '';
    $imageurl = theme_config::load('mytheme')->setting_file_url('bannerimage', 'bannerimage');
    if (!empty($imageurl)) {
        $scss .= ".mytheme-banner { background-image: url('$imageurl'); background-size: cover; }\n";
    }
    return $scss;
}

/** Serves the files uploaded in this theme's settings. */
function theme_mytheme_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options = []) {
    if ($context->contextlevel == CONTEXT_SYSTEM && $filearea === 'bannerimage') {
        $theme = theme_config::load('mytheme');
        if (!array_key_exists('cacheability', $options)) {
            $options['cacheability'] = 'public';
        }
        return $theme->setting_file_serve($filearea, $args, $forcedownload, $options);
    }
    send_file_not_found();
}
```

`config.php` names the two callbacks (`$THEME->prescsscallback = 'theme_mytheme_get_pre_scss';`,
`$THEME->extrascsscallback = 'theme_mytheme_get_extra_scss';`). The fallback values live in the theme's SCSS, in a
file that is part of the main SCSS, so each default exists in one place:

```scss
$mytheme-accent: #b8410c !default;
$mytheme-radius: .75rem !default;
```

The pre-SCSS callback output is compiled before the main SCSS, so a value it sets wins over the `!default` line,
and an empty setting leaves the fallback in force (`theme_config::get_css_content_from_scss()`, 5.2 and 5.3).

### Setting to template

A layout file the theme owns adds the value to the template context, formatted for output:

```php
$templatecontext['bannertext'] = '';
if (get_config('theme_mytheme', 'bannermode') === 'text') {
    $templatecontext['bannertext'] = format_string((string) get_config('theme_mytheme', 'bannertext'));
}
```

```mustache
{{#bannertext}}<div class="mytheme-banner">{{{bannertext}}}</div>{{/bannertext}}
```

`format_string()` output is already escaped, so the template uses triple braces. Admin-written HTML (from
`admin_setting_confightmleditor`) goes through `format_text($html, FORMAT_HTML, ['noclean' => true])` so filters
and multi-language content apply. A theme that inherits every layout from Boost has no layout file to edit: copy
the layout (`moodle-theme-layouts-templates`), or print the value from a renderer method or an output hook
(`moodle-theme-renderers-output`).

## Rules

### The page

- **Replace `$settings`; do not add to the object core supplied.** Symptom of adding to it: the cog on the theme
  card opens "Section error", and the defaults are never stored. Fix: assign a new page named `themesetting<name>`
  as in the recipe. Source: `public/admin/settings/appearance.php` creates the page with the hidden flag set and
  adds it only `if ($settings && !$settings->hidden)` (5.2 and 5.3, read in the source; the replacement page was run
  on 5.3.0).
- **Keep the name `themesetting<name>`.** Any other name breaks the theme selector link
  (`public/admin/themeselector.php`). A theme that moves its settings to pages of its own keeps a page of that
  name too, or redirects from it: see [reference/large-settings-pages.md](moodle-skill-files/moodle-theme-settings/reference/large-settings-pages.md).
- **Build settings only inside `if ($ADMIN->fulltree)`.** Outside it, every page load that builds the admin
  navigation pays for the file-area queries and string lookups. Source: `public/theme/boost/settings.php`.
- **Add the tab after its settings.** `theme_boost_admin_settingspage_tabs::add()` copies the tab's settings into the
  outer page when it is called. A setting added to the tab later is drawn but never saved. Source:
  `public/theme/boost/classes/admin_settingspage_tabs.php` (identical in 5.2 and 5.3).
- **`hide_if()` goes on the outer tabs page, after the tab was added.** `admin/settings.php` reads dependencies
  from the top page only, and `add()` does not copy a tab's dependencies. Symptom on the tab: the field never
  hides. Conditions: `checked`, `notchecked`, `noitemselected`, `eq`, `neq`, `in` (values separated by `|`); the
  setting is hidden when the condition is true. Source: `public/theme/boost/settings.php` (5.3 comment),
  `public/lib/amd/src/showhidesettings.js`.
- **`hide_if()` only hides the field.** The stored value stays and is still returned by `get_config()`. Code that
  uses a dependent setting checks the controlling setting too, as the template sample does.

### Reading values

- **A value may be missing.** `get_config()` gives `false`, `$theme->settings->x` is an undefined property. Use
  `!empty()` or `??`, and compare selects with `===` against the stored string. Checkbox values are the strings
  `'1'` and `'0'`.
- **Inside `config.php`, `$THEME->settings` is the active theme's settings**, including when this file is loaded as
  a parent of a child theme. Use `get_config('theme_mytheme', ...)` for a value that must be this theme's own; it
  is cached, but it throws before the database exists, so guard it with `during_initial_install()`.
- **Forced values work.** `$CFG->forced_plugin_settings['theme_mytheme']['accent']` in the site `config.php` is
  what `get_config()` returns; the admin page shows the field as defined in config.

### Reaching the CSS

- **Every setting that feeds SCSS, and every file setting, needs
  `$setting->set_updatedcallback('theme_reset_all_caches')`.** Symptom without it: the value is saved and the site
  looks the same until someone purges caches. The callback runs only when the admin page saves a changed value.
  After `set_config()` in a script, an upgrade step or a test, call `theme_reset_all_caches()` yourself; from the
  command line, `php admin/cli/cfg.php --component=theme_mytheme --name=accent --set='#123456'` then
  `php admin/cli/purge_caches.php --theme`. Source: `public/lib/outputlib.php`, `public/theme/boost/settings.php`.
- **Validate the value again where it is written into SCSS.** A value that is not valid SCSS breaks the whole
  compile, and the site then serves Boost's stock CSS with none of the theme's rules (run on 5.3.0; the error shows
  only with developer debugging, and for the stylesheet request only in the PHP error log). The setting class
  validates on the admin page, but `set_config()`, `cfg.php` and forced config do not. Fix: a pattern check before
  emitting, as in the recipe. The colour picker also accepts colour names, `rgb()`, `rgba()`, `hsl()`, `hsla()`,
  `transparent`, `currentColor` and `inherit`; widen the check if the theme should accept them, and remember that
  Sass colour functions fail on `inherit` and `currentColor`.
- **One route per value.** Settings become SCSS variables in the pre-SCSS callback, or rules in the extra-SCSS
  callback. Do not add a third route such as `[[setting:name]]` placeholders: core replaces only `[[pix:...]]` and
  `[[font:...]]` (`theme_config::post_process()`, 5.2 and 5.3), so the theme would have to substitute them itself,
  the files stop being valid SCSS, and the defaults end up in several places. Choosing between a variable, a CSS
  custom property and a body class: [reference/setting-to-css.md](moodle-skill-files/moodle-theme-settings/reference/setting-to-css.md).
- **Do not repeat what Boost's callbacks emit.** In a Boost child, Boost's pre and extra callbacks already run
  with the child's settings. A child that also appends its `scss` setting gets the admin's SCSS twice. The table
  below lists the names Boost reads.
- **Right after saving, one page load can still show the old CSS.** Boost sets `$THEME->usefallback = true`, and
  the fallback copy is sent once while the new CSS builds (`public/theme/styles.php`, read in the source). Reload
  before concluding that a setting has no effect; `moodle-theme-development` has the cache rules.

### Stored files

Three parts must name the same file area: the fourth argument of `admin_setting_configstoredfile`, the area checked
in `theme_<name>_pluginfile()`, and the second argument of `setting_file_url($settingname, $filearea)`. The setting
value is the path of the first file (`/logo.png`), not a URL. The upload-and-serve path is read in the source, not
run.

- **Leave the item id at 0.** `setting_file_serve()` looks the file up at item id 0 whatever the setting used.
  Symptom of another item id: the upload saves and the URL returns 404.
- **Keep the updated-callback on file settings, even ones not used in CSS.** `setting_file_url()` puts the theme
  revision in the URL, and `setting_file_serve()` lets browsers cache the file for 60 days. Without a revision
  change a replaced image keeps its old URL and visitors keep the old file.
- **Use the theme's own config object for its own files.** `$theme->setting_file_url()` builds the URL from the
  active theme's settings and component, so under a child theme it points at the child. For a file that belongs to
  this theme use `theme_config::load('mytheme')->setting_file_url(...)`, as the recipe does.
- **Do not require login in `pluginfile` for a logo or background** that the login page shows.
- **In a test or script** a file setting cannot be set with `set_config()` alone: create the file in the area
  with the file storage API, then store `'/' . $filename` as the value.

Source for this section: `theme_config::setting_file_url()` and `setting_file_serve()` in
`public/lib/classes/output/theme_config.php`; `public/theme/boost/lib.php` (`theme_boost_pluginfile()`); identical
in 5.2 and 5.3.

### Defaults and later changes

- **A new setting needs a version bump to get its default stored.** Symptom without one: `get_config()` returns
  `false`, a select on the settings page shows its first option next to a different "Default:", and pressing Save
  then stores whatever is shown, for every such setting on the page. Fix: bump `$plugin->version` and run the
  upgrade, and write the reading code so that a missing value means the default. After adding settings, open the
  page and compare each shown value with its "Default:" line. Source: `admin_apply_default_settings()` and
  `any_new_admin_settings()` in `public/lib/adminlib.php`; `admin/cli/upgrade.php`.
- **A colour picker with a non-empty default cannot be emptied.** An empty submission is replaced by the default.
  Use `''` as the default and keep the fallback in SCSS (as Boost's `brandcolor` does), or pass `null, false` as
  the fifth and sixth constructor arguments.
- **Renaming or converting a setting is an upgrade step**, not an edit of `settings.php`: copy the old value, unset
  the old name, reset the theme caches. Recipe and traps:
  [reference/upgrade-migration.md](moodle-skill-files/moodle-theme-settings/reference/upgrade-migration.md).
- **Every theme needs a privacy provider**, a null provider when it stores nothing about users, and a
  user-preference provider as soon as it sets one preference. Core's privacy unit test covers every installed
  plugin and is not part of `moodle-plugin-ci`, so a missing provider surfaces late:
  [reference/user-preferences-privacy.md](moodle-skill-files/moodle-theme-settings/reference/user-preferences-privacy.md).

## Setting names that already mean something

Read from the active theme's settings, so a Boost child declares them under its own component to keep the feature.
Read in `public/theme/boost/lib.php` and `public/lib/blocklib.php`, 5.2 and 5.3.

| Name | Read by | If the child does not declare it |
|---|---|---|
| `brandcolor` | Boost pre-SCSS: becomes `$primary` | Primary colour comes from the preset |
| `scsspre`, `scss` | Boost pre-SCSS and extra-SCSS | No raw SCSS boxes for admins |
| `backgroundimage`, `loginbackgroundimage` | Boost extra-SCSS, with file areas of the same names under the active theme's component; needs those areas in the child's `pluginfile` | No custom backgrounds |
| `preset` | Boost's main-SCSS function, when the child passes its own theme object to it | Default preset; details in `moodle-theme-boost-child` |
| `unaddableblocks` | Core block manager, comma-separated block names hidden from "Add a block" | Boost's default list (`navigation,settings,course_list`) no longer applies, and those blocks become addable |

**5.3+:** `enablecolourmodes` and `defaultcolourmode` are read from `theme_boost` itself, not from the active
theme: a child does not redeclare them. See [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-settings/versions/moodle-5.3.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `$settings->add(...)` on the page core supplied | "Section error" from the theme selector; no defaults stored | Replace `$settings` with a page named `themesetting<name>` |
| Adding a setting to a tab after `$settings->add($tab)` | The field shows and its value is never saved | Add the tab last |
| `$tab->hide_if(...)` | The dependent field never hides | Call `hide_if()` on the outer tabs page |
| No updated-callback on a colour or file setting | Saved, but the CSS or the image does not change | `set_updatedcallback('theme_reset_all_caches')` |
| Setting value written into SCSS unchecked | One bad value: the site shows stock Boost styling | Pattern check before emitting; skip when it fails |
| `$theme->settings->x` for the theme's own value | Wrong or missing value when a child theme is active | `get_config('theme_mytheme', 'x')` |
| Appending the `scss` or `scsspre` setting in a Boost child's callback | The admin's SCSS is compiled twice | Leave it to Boost's callback |
| `[[setting:name]]` in SCSS or CSS | The placeholder reaches the browser as text | A variable from the pre-SCSS callback |
| Default colour repeated in `settings.php`, PHP and SCSS | The copies drift; an empty setting gives a different colour from the stated default | Empty setting default, `!default` in SCSS |
| HTML in a select or multicheckbox choice label | Shown escaped in the "Default:" line and mangled in admin search | Plain-text labels; HTML in the description |
| `admin_setting_configtext` pattern with a modifier, such as `'/^\p{L}+$/u'` | Not seen as a pattern, so `clean_param()` throws `coding_exception: Unknown parameter type` when the value is validated: while defaults are applied on install or upgrade, and on save (read) | End the pattern with `/`: `'/(*UTF)^\p{L}+$/'` |
| A file setting created with a non-zero item id | URL returns 404 | Item id 0 |
| New setting without a version bump | First option shown instead of the default; Save stores it | Bump the version; read with a fallback |
| Renaming a setting by editing its name | Every site loses the saved value | An upgrade step that copies the value |
| A per-user choice kept in `localStorage` | Lost at each login and each JavaScript cache purge | A declared user preference |
| `null_provider` in a theme that sets a user preference | The data export misses it; a reviewer rejects it | `user_preference_provider` |

## Reference files

| File | Read it when |
|---|---|
| [reference/setting-types.md](moodle-skill-files/moodle-theme-settings/reference/setting-types.md) | Choosing a setting class or its arguments: what each stores, what it validates, text patterns, HTML editor, multi-file areas, the preset selector, headings |
| [reference/setting-to-css.md](moodle-skill-files/moodle-theme-settings/reference/setting-to-css.md) | A setting must change the look and the choice between an SCSS variable, a CSS custom property, an extra-SCSS rule or a body class is open; values with units, fonts, dark mode |
| [reference/large-settings-pages.md](moodle-skill-files/moodle-theme-settings/reference/large-settings-pages.md) | The theme has more than a few dozen settings, needs several pages or its own capability, will have child themes, or you are reviewing a large theme's settings code |
| [reference/upgrade-migration.md](moodle-skill-files/moodle-theme-settings/reference/upgrade-migration.md) | A released theme renames, removes, splits or converts a setting or a file area, adds `db/install.php`, or replaces Boost on a site that had Boost settings |
| [reference/user-preferences-privacy.md](moodle-skill-files/moodle-theme-settings/reference/user-preferences-privacy.md) | The theme stores anything per user, sets a preference from JavaScript, or needs its `classes/privacy/provider.php` written |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-settings/versions/moodle-5.3.md): admin setting classes renamed (old names still work), Boost's colour mode settings and preference, `add_before()`, Classic settings migration |

## References

- https://moodledev.io/docs/apis/subsystems/admin
- https://moodledev.io/docs/5.3/apis/plugintypes/theme
- https://moodledev.io/docs/apis/subsystems/privacy
- Core source, relative to the Moodle root: `public/theme/boost/settings.php`, `public/theme/boost/lib.php`,
  `public/theme/boost/classes/admin_settingspage_tabs.php`, `public/admin/settings/appearance.php`,
  `public/lib/classes/output/theme_config.php`, `public/lib/adminlib.php`


---

### moodle-theme-testing-release

> Use when testing, linting, packaging or submitting a Moodle theme - a PHPUnit test that compiles the theme, the theme's own Behat suite (--suite=<theme>, @theme_<name> tags, behat_theme_<name>_behat_*.php overrides, blacklist.json), computed-style and axe checks, dark mode (--colourmode, 5.3) and RTL checks, --scss-deprecations, stylelint and Mustache lint of overridden core templates, moodle-plugin-ci for themes, and Plugins directory rules for themes (LICENSE file, ZIP root folder, screenshot, choosereadme, thirdpartylibs.xml for fonts); also for "0 scenarios" from a theme feature, a core feature that fails only under the theme, or CI that stays green while the theme's SCSS does not compile. Skip when writing the theme itself (start at moodle-theme-development), for Behat, PHPUnit, CI and release mechanics that are not theme-specific (moodle-behat-testing, moodle-phpunit-testing, moodle-ci-matrix, moodle-plugin-release), or for the axe steps (moodle-accessibility).

# Moodle Theme Testing and Release

## Overview

How to prove that a theme works on Moodle 5.2 and 5.3 and how to ship it: which tests catch which failure, how
Behat runs a theme, what the CI gates check and miss, and what the Plugins directory asks of a theme. "Run on 5.3.0"
means it was observed with a Boost child theme on Moodle 5.3.0; "read in the source" means read, not run. Nothing
here was run on 5.2: 5.2 statements are read in the 5.2 source.

## When to Use

- Adding the first tests to a theme, or a theme change needs a test that would fail without it
- A theme feature reports zero scenarios, or a core feature fails only under the theme
- Proving a colour, spacing, dark-mode or RTL change, or running accessibility checks on theme pages
- Writing or fixing a theme's GitHub Actions workflow, or reading a failed lint step
- Building the release ZIP, submitting a theme to the Plugins directory, or answering a reviewer
- **Skip when:** the task is building the theme (`moodle-theme-development` routes to the right sibling); Behat or
  PHPUnit in general (`moodle-behat-testing`, `moodle-phpunit-testing`); the CI version matrix
  (`moodle-ci-matrix`); version numbers, tags and the release workflow (`moodle-plugin-release`); the security
  checklist before a release (`moodle-release-preflight`); WCAG rules for markup (`moodle-accessibility`)

## Mental model: four layers, each caught by one kind of test

| Layer | What breaks | What catches it | What does not |
|---|---|---|---|
| Compile | An import, variable or mixin missing on one version; a bad setting value in SCSS | A PHPUnit test asserting one of the theme's own selectors in `get_css_content()` | Lint, Behat without assertions on style, CI's grunt step (it never compiles a third-party theme) |
| Page | A layout, template or renderer override not used; a missing string | Behat in the theme's own suite; a PHPUnit test that renders the template | PHPUnit renderer tests from the CLI renderer |
| Effect | A rule reached the stylesheet but loses the cascade; dark mode or RTL wrong | Computed-style steps in a JavaScript scenario; axe | Grepping the served CSS (that proves arrival only) |
| Package | No licence file, wrong ZIP root, undeclared fonts, missing `choosereadme` | Listing the built ZIP; a checklist | Every CI step: CI installs from the git checkout, never from the ZIP |

A compile failure is silent: `theme_config::get_css_content()` falls back to the parents' precompiled CSS, so the
site looks like stock Boost and nothing errors on screen (run on 5.3.0; `public/lib/classes/output/theme_config.php`
`get_css_content()`, 5.2 and 5.3). The only cheap guard is the compile test below. Seeing the compiler message is
covered in `moodle-theme-scss`.

## Default recipe

Files, beside the theme's code:

```
tests/
  lib_test.php                   compile test and setting-to-SCSS tests (PHPUnit)
  behat/
    mytheme.feature              @theme @theme_mytheme, runs in the "mytheme" suite
    behat_theme_mytheme.php      the theme's own steps, only if it needs any
LICENSE                          full GPL v3 text, in the root, shipped in the ZIP
```

### 1. The compile test (PHPUnit)

This pattern was run on 5.3.0. PHPUnit is 11.5 on both versions, so the attributes work on 5.2 too.

```php
<?php
// (GPL header)

namespace theme_mytheme;

/**
 * Tests of the theme's SCSS.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
#[\PHPUnit\Framework\Attributes\CoversFunction('theme_mytheme_get_pre_scss')]
final class lib_test extends \advanced_testcase {
    public function test_the_theme_compiles(): void {
        $this->resetAfterTest();
        set_config('accent', '#123456', 'theme_mytheme');
        $theme = \theme_config::load('mytheme');
        $theme->force_svg_use(true);
        $theme->set_rtl_mode(false);

        $css = $theme->get_css_content();

        // The fallback CSS is Boost's and contains none of these, so this fails on any compile error.
        $this->assertStringContainsString('.mytheme-banner', $css);
        $this->assertMatchesRegularExpression('/\.mytheme-banner\{[^}]*#123456/', $css);
    }

    public function test_a_value_that_is_not_a_colour_is_left_out(): void {
        $this->resetAfterTest();
        set_config('accent', 'red; } body { display: none', 'theme_mytheme');
        $theme = \theme_config::load('mytheme');
        $this->assertStringNotContainsString('mytheme-accent', theme_mytheme_get_pre_scss($theme));
    }
}
```

- `theme_config::load()` includes the theme's and its parents' `lib.php`, so functions from `lib.php` can be called
  after it (`theme_config.php` constructor, 5.2 and 5.3).
- A compile error also calls `debugging('Error while compiling SCSS: ...')`, which fails an `advanced_testcase` with
  "Unexpected debugging() call detected" and prints the message. The selector assertion still catches the fallback
  when debugging is quiet.
- Match the compiled form: on 5.3.0 the output had no space before `{`, as the regular expression above expects.
- Run it: `vendor/bin/phpunit --testsuite theme_mytheme_testsuite` from the Moodle root, after
  `php public/admin/tool/phpunit/cli/init.php` (the suite name is generated into `phpunit.xml`).
- More tests (rendering a template, a renderer, the privacy compliance test): [reference/phpunit-for-themes.md](moodle-skill-files/moodle-theme-testing-release/reference/phpunit-for-themes.md).

### 2. The theme's Behat feature

Run on 5.3.0: after `init.php` the generated `behat.yml` has a suite named after the theme, and these scenarios pass
with `--suite=mytheme`.

```gherkin
@theme @theme_mytheme
Feature: The theme's banner and body class
  In order to brand the site
  As an administrator
  I need the banner and the corner style to reach course pages

  Background:
    Given the following "courses" exist:
      | fullname | shortname |
      | Course 1 | C1        |
    And the following "users" exist:
      | username | firstname | lastname |
      | student1 | Student   | One      |
    And the following "course enrolments" exist:
      | user     | course | role    |
      | student1 | C1     | student |

  Scenario: The banner text set by the administrator is shown on course pages
    Given the following config values are set as admin:
      | bannertext | Welcome | theme_mytheme |
    When I am on the "Course 1" course page logged in as student1
    Then I should see "Welcome" in the "[data-region='mytheme-banner']" "css_element"

  Scenario: The corner style setting reaches the body class
    Given the following config values are set as admin:
      | cornerstyle | square | theme_mytheme |
    When I am on the "Course 1" course page logged in as student1
    Then "body.mytheme-corners-square" "css_element" should exist
```

Run it locally from the Moodle root, the directory that holds `public/` (read in the source for both versions):

```bash
php public/admin/tool/behat/cli/init.php --scss-deprecations
php public/admin/tool/behat/cli/run.php --suite=mytheme --tags=@theme_mytheme
```

### 3. CI

Start from the upstream `moodle-plugin-ci` template (`moodle-ci-matrix` owns the matrix). Theme specifics, read in
moodle-plugin-ci 4.5.11: `behat` picks the suite named after the theme by itself (older versions ran `default`,
where a theme's features do not exist, and passed with zero scenarios; pass `--suite mytheme` if unsure); keep
`--scss-deprecations`; `grunt` lints the whole `scss/` tree with core's stylelint; `mustache` lints every
overridden core template. A complete workflow, a dark-mode Behat run and the lint traps are in
[reference/ci-for-themes.md](moodle-skill-files/moodle-theme-testing-release/reference/ci-for-themes.md).

### 4. Release

Follow `moodle-plugin-release`: it owns the version and tag steps, building the ZIP with
`git archive --prefix=mytheme/`, listing it, the root-folder rule and the licence file. What a theme adds to that
(screenshot, plugin icon, `choosereadme`, fonts, copied core files) is in
[reference/plugins-directory.md](moodle-skill-files/moodle-theme-testing-release/reference/plugins-directory.md).

## Behat runs a theme through its suite

Read in `public/lib/behat/classes/behat_config_util.php` `get_behat_suites()`, identical in 5.2 and 5.3.0.

- Every installed theme that the selector can show gets a suite named after it. Boost, the default theme, is the
  suite `default`. A theme with `$THEME->hidefromselector = true` gets no suite, so its features never run.
- A theme's suite holds only that theme's features, unless Behat was initialised with `-a` /
  `--add-core-features-to-theme` (all themes, or a comma list). Theme features are removed from `default`.
- Before each scenario in a non-default suite, Behat sets the site theme to the suite name
  (`public/lib/tests/behat/behat_hooks.php`). Never set the theme in a feature.
- `moodle-plugin-ci validate` fails a feature without both `@theme` and `@theme_mytheme` tags.
- Step definitions: every `tests/behat/behat_*.php` of the theme is a context of its suite only; the class name
  must equal the file name. A theme first inherits its nearest parent's contexts, so a Boost child already runs with
  `behat_theme_boost_behat_navigation`. A class that extends a core context replaces it in the suite.
- `tests/behat/blacklist.json` removes `features`, `contexts` or `tags` from the theme's suite. An existing file that
  is empty or not valid JSON stops Behat initialisation with "blacklist.json is empty".

Theme CSS on a Behat site is built once, at `--enable` or `init.php`, left-to-right only, with default settings, and
put back into the cache before each JavaScript scenario (`public/lib/behat/classes/util.php` `build_themes()`,
`restore_saved_themes()`, 5.2 and 5.3). Two consequences, read in the source, not run:

- After editing SCSS, initialise again (`init.php` or `util_single_run.php --enable`) or the run tests the old CSS.
- `the following config values are set as admin` is a plain `set_config()` and does not reset theme caches
  (`public/admin/tests/behat/behat_admin.php`). A setting that feeds the SCSS needs the scenario to save it on the
  settings page (the setting's `theme_reset_all_caches` callback runs) or a theme step that calls
  `theme_reset_all_caches()`. Settings read by templates or renderers, as in the feature above, work either way.

`--scss-deprecations` makes Behat fail any step after which an element shows Boost's "Deprecated style in use"
marker, such as Bootstrap 4 classes (`ml-2`, `float-right`, `badge-primary`, `sr-only`, `font-weight-bold`), also
when the class was added by JavaScript or sits in a core page the step only visits
(`public/lib/behat/classes/behat_session_trait.php` `look_for_deprecated_styles()`, 5.2 and 5.3). Three things
decide whether it runs:

- It is a run option set at `init.php` or `util_single_run.php --enable`. `run.php` has no such option and Behat
  rejects it as unknown. The header Behat prints must say `SCSS deprecations: Yes`.
- It checks only JavaScript scenarios. A feature with no `@javascript` scenario never exercises it; give the theme at
  least one.
- Deprecated icons (`.icon.deprecated`) fail the same way unless the run was set up with `--no-icon-deprecations`.

Full suite mechanics, override recipes, selectors and the element ids core steps depend on:
[reference/behat-theme-suite.md](moodle-skill-files/moodle-theme-testing-release/reference/behat-theme-suite.md).

## Proving the effect, not the arrival

- A rule can be in the served stylesheet and still lose to Bootstrap or a later rule. Assert the computed value in a
  JavaScript scenario with a theme step (recipe in [reference/visual-checks.md](moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md)), or
  assert a visible consequence, as large themes do: a raw SCSS rule that hides `#page-header h1`, then
  `I should not see "Course 1" in the "#page-header .page-header-headings" "css_element"`.
- `var(--name, fallback)` with an undefined property silently uses the fallback; only a computed-value check on the
  page shows it. Check the names your SCSS reads in the browser: `getComputedStyle(document.body).getPropertyValue('--bs-primary')`.
- Name the change the claim predicts and assert that change, in the role and the state users will meet it: a
  setting checked only on a course that does not use it, or only as admin, proves nothing.
- Phones: `I change viewport size to "mobile"`; check `document.documentElement.scrollWidth` is not larger than
  the viewport (a `.row` outside a container overflows by its negative gutters), and test "visible" with
  `document.elementFromPoint()` at the element's centre, because Boost's fixed navbar (about 60 px) covers content
  that is inside the viewport.
- Dark mode (**5.3+:** `data-bs-theme="dark"` on `<html>`) and RTL (`body.dir-rtl`) recipes:
  [reference/visual-checks.md](moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md).

## Accessibility checks (axe)

Read in `public/lib/tests/behat/behat_accessibility.php` (5.2 bundles axe-core 4.10.3, 5.3.0 bundles 4.13.0; the
code is otherwise identical).

```gherkin
  @javascript @accessibility
  Scenario: A course page with the banner meets accessibility standards
    Given the following config values are set as admin:
      | bannertext | Welcome | theme_mytheme |
    When I am on the "Course 1" course page logged in as student1
    Then the page should meet accessibility standards
    And the "region-main" "region" should meet accessibility standards with "best-practice" extra tests
```

- The step throws unless the scenario or feature is tagged `@accessibility`, and needs `@javascript`.
- It passes without checking anything when Behat was initialised with `--no-axe` (axe is on by default).
- "No data" means the axe script never loaded: the step injects `/lib/behat/axe/axe.min.js` from the site, and a web
  server that denies `/lib/behat/` paths makes every accessibility step fail locally while CI passes.
- Default rules: WCAG 2.0, 2.1 and 2.2 A and AA, Section 508, `cat.aria`, `cat.sensory-and-visual-cues`, `wcag134`.
  Naming `wcag2aa` as an extra adds nothing; `best-practice` adds the landmark and heading rules.
- **5.3+:** core's own course page fails `best-practice` (`landmark-unique`) in both colour modes, as Boost's
  `colour_mode_accessibility.feature` notes; run `best-practice` on regions the theme owns, plain rules on the page.
- axe does not look inside iframes (H5P, embedded editors) and does not judge most non-text contrast: borders, focus
  rings and icons need a look by eye. Light and dark pairs, and what else to check by hand:
  [reference/visual-checks.md](moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md).

## Lint gates and what they miss

- **stylelint** lints `scss/*.scss` and `scss/**/*.scss` of a theme with core's rules; `style/*.css` is linted only
  when there is no `scss/`, and a root `styles.css` in a theme never. The rules and how to silence a line are in
  `moodle-theme-scss`. SCSS returned as a string from a PHP callback is never linted.
- **Mustache lint** (`moodle-plugin-ci mustache`) checks every `*.mustache`, including overridden core templates
  under `templates/core/`, and fails on any warning: no `@template` docblock, no `Example context (json):`, HTML
  validator messages. A `*.mustache.upstream` twin is not linted. A `.mustachelintignore` beside the template skips
  the HTML validator only. Run on 5.3.0 and on a 5.2 tree: an override that wraps the original with
  `{{> core/name! }}` passes. Two gaps, read in the linter bundled with moodle-plugin-ci 4.5.11, not run: a partial
  it cannot find renders as nothing and is not reported, and `{{#js}}` blocks are not linted on 5.2 and 5.3, because
  it looks for ESLint under `public/node_modules`, which does not exist (the log says "ESLint did not run").
- An example context must not contain `}}`: it closes the comment and prints the rest of the docblock on the page,
  while lint and PHPUnit stay green. Write `} }` inside JSON.
- **phpcs** applies to a copied core file as to your own: Boost's `layout/drawers.php` copied unchanged fails the
  code checker on a missing trailing comma (run on 5.3.0). Fix the copy; keep the untouched original as
  `drawers.php.upstream`, which no checker reads.
- **gherkinlint** (inside `grunt`) checks feature indentation (`Background`/`Scenario` 2, steps 4, `Examples` 4,
  rows 6), trailing spaces, a newline at the end, and that feature names are unique (`.gherkin-lintrc`, identical
  in 5.2 and 5.3).

What no gate catches, so a test or a checklist must: a compile failure; a missing `{{#str}}` or `get_string()` key
(it prints `[[key]]` or throws on the live page; render each new template in PHPUnit and assert no `[[`); a template
override that is not used; a theme with no privacy provider (core's compliance test is not part of plugin CI); the
ZIP's root folder and licence file; a stale `js/esm/build` (**5.3+**, see the version notes).

## Plugins directory rules that apply to themes

The Marketplace plugin submission guidelines (linked from https://moodledev.io/general/community/plugincontribution)
replace the legacy checklist. What a theme must have, with what checks it:

| Rule | Checked by | How to satisfy it |
|---|---|---|
| A licence file in the package | nothing in CI; the most common review blocker | `LICENSE` in the root, in the ZIP; the rule and its checks are in `moodle-plugin-release` |
| Installs from the ZIP | nothing in CI | Root folder = the theme name (`mytheme/`), not `moodle-theme_mytheme-1.0.0/` (`rootdirinvalid`); building and listing the ZIP is in `moodle-plugin-release` |
| GPL v3 when the plugin reproduces or adapts a substantial part of Moodle | review | A Boost child that copies Boost layouts or templates is in that case: GPL v3 or later |
| Third-party files declared | nothing (the file only hides paths from CI) | Each bundled font, icon set or vendored library in `thirdpartylibs.xml`, its licence text beside it |
| Boilerplate and `@copyright` in every file | phpcs, PHP files only | Add them by hand to `.mustache`, `.scss`, `.js`; a file copied from core or another theme keeps the original `@copyright` line above yours |
| Strings core asks for | `validate` checks `pluginname` only | Also `choosereadme` (the theme selector's preview reads it), `privacy:metadata` or the preference strings, `region-<name>` for a block region no parent names |
| Settings stored as `theme_mytheme/<name>` | nothing | Use the slash form in `settings.php` |
| CSS scoped so it does not affect other pages | nothing | For a theme: scope the theme's own components with its own class prefix; do not ship rules for one third-party plugin |
| Screenshots on the listing page | nothing | Separate from `pix/screenshot.png`; show the theme on real pages, light and dark if supported |
| Privacy API when personal data is stored | nothing in plugin CI | Run core's compliance test for the theme ([reference/phpunit-for-themes.md](moodle-skill-files/moodle-theme-testing-release/reference/phpunit-for-themes.md)) |

The full release checklist, the ZIP checks, `pix/screenshot` and plugin icon facts, and how reviewers raise and
close findings: [reference/plugins-directory.md](moodle-skill-files/moodle-theme-testing-release/reference/plugins-directory.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No test asserts the theme's own CSS | A compile error ships; the site looks like plain Boost and every gate is green | The compile test above |
| Asserting `assertNotEmpty($css)` | Passes on the fallback CSS | Assert a selector only the theme emits |
| Theme feature run with `--suite=default` or an old moodle-plugin-ci | Zero scenarios, green job | `--suite=mytheme`; moodle-plugin-ci 4.5.11 or later |
| Only `@theme_mytheme` on the feature | `moodle-plugin-ci validate` fails | `@theme @theme_mytheme` |
| Setting the theme inside a feature (`theme` in a config values table, or `set_config('theme', ...)` in a step) | Fights the suite; the feature tests a different theme in other suites | Let the suite set the theme |
| `$THEME->hidefromselector = true` | The theme has no Behat suite at all | Leave it false in a theme that has features |
| `I change the viewport size to "mobile"` | Undefined step: core's step has no "the" | `I change viewport size to "mobile"` |
| SCSS-fed setting set with `the following config values are set as admin` | The page keeps the CSS built at init; the assertion fails or passes for the wrong reason | Save it on the settings page in the scenario, or a step calling `theme_reset_all_caches()` |
| SCSS edited, Behat not re-initialised | Scenarios test the old CSS | `init.php` (or `util_single_run.php --enable`) again |
| `run.php --scss-deprecations` | `run.php` hands the option to Behat, which stops with "option does not exist" | Pass it to `init.php`; read the "SCSS deprecations: Yes" line |
| No `@javascript` scenario | The SCSS deprecation and axe checks never run | At least one JavaScript scenario that loads a themed page |
| Accessibility step without `@accessibility` | DriverException | Tag the scenario or feature |
| "No data" from axe treated as a theme bug | Time lost on a server rule | Allow `/lib/behat/` on the test web server |
| Bootstrap 4 class in a template or in JS-built markup | Fails CI Behat with `--scss-deprecations`, passes a local run without it | Bootstrap 5 names (`ms-2`, `float-end`, `visually-hidden`, `fw-bold`) |
| `hidden` attribute on an element with a `d-flex` class | Still shown: Bootstrap's `d-*` uses `!important` | Toggle `d-none`; assert with `I should not see` for each mode |
| Grepping the served CSS as proof | The rule arrived but loses the cascade | A computed-style assertion |
| Copied core template without its docblock or example context | Mustache lint fails the theme's CI | Keep `@template` and `Example context (json):` |
| `}}` inside an example context | The rest of the docblock prints on the page | `} }` |
| Release ZIP with the wrong root folder or without `LICENSE` | A reviewer blocks it; core's validator can reject the root with `rootdirinvalid` | Build and list the ZIP as `moodle-plugin-release` says |
| No `choosereadme` string | The theme selector preview asks for a missing string | Add it to `lang/en/theme_mytheme.php` |
| No `pix/screenshot.*` | The selector silently shows the parent's screenshot | Ship one |
| No `pix/icon.svg` | A blank spacer instead of an icon on the plugins overview page (`public/admin/renderer.php`) | Ship a line icon with a stroke that also reads in dark mode |
| A 5.3-only step (`the run is not using a colour mode`) in a feature that runs on 5.2 | The 5.2 row cannot run that step | A separate feature with its own tag, excluded on 5.2 rows (version notes) |

## Reference files

| File | Read it when |
|---|---|
| [reference/behat-theme-suite.md](moodle-skill-files/moodle-theme-testing-release/reference/behat-theme-suite.md) | Writing the theme's Behat features or step definitions, overriding or blacklisting a core or Boost context, running core features under the theme, or a theme feature runs zero scenarios |
| [reference/visual-checks.md](moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md) | Proving a colour, spacing, dark-mode, RTL or phone-width change; writing a computed-style step; light and dark accessibility pairs; checking pages in a real browser or taking screenshots |
| [reference/phpunit-for-themes.md](moodle-skill-files/moodle-theme-testing-release/reference/phpunit-for-themes.md) | Writing PHPUnit tests beyond the compile test: setting-to-SCSS callbacks, rendering a template or a renderer as the theme, RTL build, the privacy compliance test, query counts |
| [reference/ci-for-themes.md](moodle-skill-files/moodle-theme-testing-release/reference/ci-for-themes.md) | Writing or fixing the theme's GitHub Actions workflow, adding a dark-mode Behat run, reading a failed grunt, stylelint, Mustache or validate step |
| [reference/plugins-directory.md](moodle-skill-files/moodle-theme-testing-release/reference/plugins-directory.md) | Preparing a release ZIP or a first submission, writing the listing, checking licences of fonts and images, or answering a Plugins directory reviewer |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-theme-testing-release/versions/moodle-5.2.md): no colour modes or `--colourmode`, so dark-mode scenarios must skip; axe 4.10.3; Classic still installed; templates copied from 5.3 that need partials 5.2 lacks |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-theme-testing-release/versions/moodle-5.3.md): `--colourmode` runs and the run header, `data-bs-theme` and `data-colourmode`, which themes get colour modes, Boost's 5.3 test files, axe 4.13.0 and `best-practice` on core pages, keeping 5.3-only steps off 5.2 rows, React/ESM builds that CI does not check, Classic gone |

## References

- https://moodledev.io/general/development/tools/behat/running
- https://moodledev.io/general/development/tools/behat/writing
- https://moodledev.io/docs/5.3/guides/colourmodes
- https://moodledev.io/general/development/policies/accessibility
- https://moodledev.io/general/development/policies/codingstyle/css
- https://moodledev.io/general/community/plugincontribution
- https://moodledev.io/docs/5.3/apis/commonfiles
- https://github.com/moodlehq/moodle-plugin-ci
- Core source, relative to the Moodle root: `public/lib/behat/classes/behat_config_util.php`,
  `public/lib/behat/classes/util.php`, `public/lib/behat/classes/behat_session_trait.php`,
  `public/lib/tests/behat/behat_accessibility.php`, `public/lib/tests/behat/behat_hooks.php`,
  `public/theme/boost/tests/`, `public/lib/classes/update/validator.php`


---

### moodle-upgrade-migration

> Use when porting a Moodle plugin written for 3.x, 4.x, 5.0 or 5.1 up to 5.2, moving it to a newer PHP version, or needing the porting method for any version: raising $plugin->requires and $plugin->supported, one codebase or a branch per Moodle version, guarding an API that differs between supported branches, fixing deprecation debugging ("has been deprecated", "Call to undefined function print_error", "Undefined constant"), writing db/upgrade.php steps that must survive a failed upgrade, or porting old code (print_error, add_to_log, external_api without namespace, lib.php callbacks, Bootstrap 4 classes, /public directory). Skip when the question is what Moodle 5.3 removed, moved, deprecated or added (moodle-5-3-changes) or writing a plugin from scratch (moodle-plugin-development).

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
[reference/legacy-api-replacements.md](moodle-skill-files/moodle-upgrade-migration/reference/legacy-api-replacements.md).

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
  [reference/php-versions.md](moodle-skill-files/moodle-upgrade-migration/reference/php-versions.md).
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
| [reference/legacy-api-replacements.md](moodle-skill-files/moodle-upgrade-migration/reference/legacy-api-replacements.md) | porting code written for Moodle 3.x or 4.x, or a deprecated function, class or template is not in the table above |
| [reference/php-versions.md](moodle-skill-files/moodle-upgrade-migration/reference/php-versions.md) | moving code to a newer PHP version, or PHP itself (not Moodle) emits the deprecation |
| [reference/release-history.md](moodle-skill-files/moodle-upgrade-migration/reference/release-history.md) | the plugin's current minimum is below 5.2 and you need what changed in 4.x, 5.0 and 5.1 |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](moodle-skill-files/moodle-upgrade-migration/versions/moodle-5.2.md): requirements, and the 5.2 removals and deprecations a port from 5.1 hits |
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-upgrade-migration/versions/moodle-5.3.md): requirements, values for `requires`, and spanning 5.2 and 5.3 in one codebase |

## References

- https://moodledev.io/general/development/policies/deprecation
- https://moodledev.io/general/development/upgradenotes
- https://moodledev.io/docs/guides/upgrade
- https://moodledev.io/general/releases
- Root `UPGRADING.md` of the target Moodle tree


---

### moodle-walkthrough

> Use when asked to "make the walkthrough", walk through a Moodle plugin or theme on a real site, or produce screenshots and a report (usually a PDF) of what each role sees. Covers listing what to cover from the code, deploying and checking the installed version, demo courses and users made for the walkthrough, driving Chromium and Firefox with Playwright as each role at desktop and phone width, user tours and drawers that spoil shots, reading every screenshot before using it, separating plugin problems from harness problems, the report's structure, keeping the Markdown source beside the PDF with relative image links, rendering the PDF and checking it. Skip when writing automated acceptance tests (moodle-behat-testing), checking a task before calling it done (moodle-definition-of-done), or preparing a Plugins directory listing and its screenshots (moodle-marketplace-package).

# Moodle Walkthrough

## Overview

A walkthrough uses the plugin on a real Moodle site the way people will: as each role, through every screen,
with a screenshot of each step. The result is a report in two forms that are kept together: the Markdown file,
which is the source and the copy an assistant reads later, and a PDF made from it for people.

## When to Use

- "Make the walkthrough", "do a full walkthrough", "walk me through the plugin with screenshots"
- After a feature or a release candidate is finished, to show and check what each role sees
- When the user later says "in that walkthrough ...": open the Markdown report, not the PDF
- **Skip when:** the goal is a repeatable automated test (`moodle-behat-testing`), the pre-completion checklist
  (`moodle-definition-of-done`), or a Plugins directory listing and its screenshots (`moodle-marketplace-package`)

## Where the files go

Never inside the plugin repository: a walkthrough is about the plugin, not part of it, and screenshots would
end up in the release ZIP. Use the project's notes directory. If the project's instructions (`CLAUDE.md`, a
harness or contributing document) name one, use it, together with the test site, credentials and PDF tool they
name. Otherwise ask once where reports go.

```
<notes>/<plugin>/WALKTHROUGH-YYYY-MM-DD.md          the report: the source, kept permanently
<notes>/<plugin>/walkthrough-YYYY-MM-DD/NN-role-what.png
<notes>/<plugin>/pdf/WALKTHROUGH-YYYY-MM-DD.pdf     made from the .md, never edited on its own
```

- **Both files are kept.** The PDF is for reading; the Markdown is what an assistant opens when the user refers
  to the walkthrough later, because it is text, searchable and cheap to read. Never delete it after rendering,
  and never write the report only into the PDF tool's temporary input.
- **Image links are relative** to the `.md` file (`walkthrough-2026-11-15/03-student-view.png`), so the report
  still works when the folder is copied or read on another machine. An absolute path breaks both.
- A second walkthrough on the same day gets a suffix (`WALKTHROUGH-2026-11-15-mobile.md`), not an overwrite.
- If the notes directory has an index or README for the plugin, add one line linking the new report.

## The recipe

### 1. List what to cover, from the code

Before opening a browser, build the coverage list from the plugin itself, not from memory of what it does:

```bash
ls settings.php db/access.php *.php classes/output templates amd/src 2>/dev/null
grep -n "=> \[" db/access.php | head -40          # capabilities: each one is a role to walk
grep -c "string\['" lang/en/*.php                 # a rough size check for the UI
```

- Every page a user can open, every setting, every capability that changes what a role sees, every mode and
  option (group modes, anonymous and named, empty states, a hidden instance).
- The roles: at least admin (settings), teacher (set-up and the teacher view), student. Add the others the
  capabilities name: a non-editing teacher, a guest, a user with no enrolment.
- Width and theme cases where the plugin has UI: desktop 1280 x 900, phone 390 x 844, dark colour mode on
  Moodle 5.3, a second browser (Firefox), reduced motion if the plugin animates.
- Read the project's notes on the plugin first: an earlier walkthrough, open questions, known problems.

### 2. Prepare the site

- Deploy the current code, run the upgrade and purge caches. Then read the installed version from the site
  (`get_config('<component>', 'version')`) and check it equals `version.php`. A walkthrough of stale code is
  worthless and looks fine.
- Record for the report header: plugin release and version, Moodle version and build, theme, browsers, sizes.
- Take a snapshot of the plugin's settings (`get_config('<component>')`) before changing any, and restore it at
  the end. Compare the two in the final step.

### 3. Make demo data for the walkthrough

- Create courses, users and activities just for it, with names that say so ("Walkthrough: <feature>"). Never
  change existing accounts or courses: other people and other reports rely on them. Never reset an existing
  user's password.
- Give every course a real one-sentence description of what it is for, or none. The data generator writes
  "Test course N" and lorem ipsum when `summary` is not passed (`public/lib/testing/generator/data_generator.php`,
  5.3.0), and that text then shows in the screenshots. Do the same for activity intros.
- Build the data with one CLI script that can be re-run, so the walkthrough can be repeated. Keep the script
  with the screenshots, not in the plugin.
- Give the data a story: students at different stages, a group with members and a student in no group,
  realistic names and submissions. An empty page proves little.
- Questions go in a question bank made for the walkthrough, never a shared or system bank.

### 4. Drive the browser

Use Playwright: the skeleton, login and per-page error capture are in
[reference/playwright-recipes.md](moodle-skill-files/moodle-walkthrough/reference/playwright-recipes.md).

- Log in through the login form with credentials the project's instructions or the user gave. Do not guess
  passwords, read password hashes or change them. If a credential is missing, stop and say so.
- A new user's first Dashboard visit opens a user tour that covers the page and makes clicks time out. Mark the
  tours done for the walkthrough users only (`tool_usertours_tour_completion_time_<tourid>` preferences),
  never by disabling tours site-wide.
- Close the block and course-index drawers (`drawer-open-block`, `drawer-open-index` preferences) when they
  would cover content.
- Logging in lands on the Dashboard, so anything that fires once per visit has already fired before the first
  explicit visit. Reset it after login if the shot needs it.
- Record console errors and failed requests on every page. A screen that looks right with a JavaScript error
  behind it is a finding.
- Name screenshots `NN-role-what.png` in walk order. Screenshot the area that matters, or the full page when the
  layout is the point.

### 5. Read every screenshot

Open each image and check it shows what its caption will say, before it goes in the report:

- the right user is logged in, the right page, the state the step describes;
- no error notice, debug output, missing-string markers (`[[stringname]]`), spinner or half-loaded page;
- nothing covers the content: a tour, a drawer, a cookie banner, a floating button;
- no placeholder content: lorem ipsum, "Test course 1", a fake-camera test pattern. Use real-looking
  content, or leave the shot out.

Retake any that fails. A walkthrough whose screenshots were not looked at reports what the script hoped for.

### 6. Findings

Sort every problem into one of two kinds and say which in the report:

- **The plugin's problems**: wrong behaviour, missing strings, layout breaks, errors, a role seeing what it
  should not. Each with the screenshot, where it happens and what was expected.
- **The walkthrough's own problems**: tours, stale caches, bad demo data. Fix them and re-shoot; mention them
  briefly so the next run avoids them.

The walkthrough reports; it does not redesign. Fix plugin defects only when the request included fixing, and
then re-run the affected steps and record each fix with its test. A finding about how a feature should work,
or a control that seems unnecessary, is a question for the user, never a change made on the walkthrough's say-so.

### 7. Write the report

```markdown
# <Plugin name> (<component>): walkthrough report

- **Date:** ... **Plugin:** <release> (<maturity>), version <version>
- **Site:** Moodle <version> (Build ...), <theme>
- **Browsers:** ... **Viewports:** ...

## Summary            a table: area, result; the count of problems found
## Problems found     numbered: what, where, screenshot, expected; fixed or open
## Demo data          the courses, users and settings, and that they were left on the site
## 1. <Area>          one section per area in walk order: a sentence or two of what was observed, then the shots
## Not covered        what was not walked or not run, in one line each, and why
## Left on the site   what the walkthrough created or changed and did not undo
```

- Write what was seen, not what the code should do. Every statement comes from the run that took the
  screenshot.
- Each screenshot has alt text saying what it shows: `![Student view, group mode, no group](...)`.
- Quote UI labels exactly as rendered.
- Put any HTML or script payload in a code span. Raw HTML in Markdown is passed through to the PDF renderer, and
  a payload such as `onerror=alert(1)` runs there and can stall the render.

### 8. Render the PDF and check it

Use the project's PDF tool if it names one. Otherwise Markdown to HTML, then headless Chromium:
[reference/playwright-recipes.md](moodle-skill-files/moodle-walkthrough/reference/playwright-recipes.md) has a short script.

- The HTML must resolve the relative image links from the Markdown file's directory (a `<base href>` or writing
  the HTML beside the `.md`). Rendered from a temporary directory without it, every image is a broken box.
- Check the result, not the exit code: `pdfinfo` for the page count, `pdfimages -list` for the number of images
  (it should equal the screenshots in the report), and open one page to see a picture rendered. Some Chromium
  builds silently cut a long single print at a fixed page count; a page count far below what the report needs
  means the PDF is truncated.

### 9. Hand it over

Give the user both paths, the Markdown and the PDF, and send the PDF if the session can send files. Say in a
few lines: the problems found, what was fixed, what was not covered, and what was left on the site.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Only the PDF is kept | A later "in that walkthrough ..." means reading a PDF, or the report is lost | Keep `WALKTHROUGH-*.md` beside `pdf/`; the PDF is made from it |
| Absolute image paths in the `.md` | Images break when the folder is copied or read elsewhere | Relative paths from the `.md` file |
| Report or screenshots in the plugin repo | They ship in the release ZIP | The project's notes directory |
| Walking stale code | Shots of the old behaviour; fixes "not working" | Deploy, upgrade, purge, compare the installed version |
| Generator placeholders | "Test course 1" and lorem ipsum in every shot | Pass `summary` and `intro` explicitly |
| A user tour on the first visit | Clicks time out; every shot shows the tour | Mark the tours done for the walkthrough users |
| Screenshots not opened | Error notices, wrong user or a tour in the report | Read each image before captioning it |
| Changing existing users or settings | Other work breaks; the site differs after | Dedicated data; snapshot and restore settings |
| A finding treated as an order | A feature removed or redesigned unasked | Report it as a question |
| PDF checked by exit code | A truncated or imageless PDF is delivered | `pdfinfo`, `pdfimages -list`, look at a page |

## Reference files

| File | Read it when |
|---|---|
| [reference/playwright-recipes.md](moodle-skill-files/moodle-walkthrough/reference/playwright-recipes.md) | Writing the browser script (login, tours, error capture, widths, dark mode, Firefox) or rendering the PDF without a project tool |

## References

- https://playwright.dev/python/docs/intro
- https://moodledev.io/general/development/tools/behat (the same site set-up traps apply)


---

### moodle-web-services

> Use when adding, changing, calling or debugging a Moodle external function or web service - db/services.php, classes/external/, execute_parameters/execute_returns, validate_parameters, validate_context, 'ajax' => true for core/ajax, 'loginrequired' => false, readonlysession, REST/SOAP tokens, login/token.php, webservice/upload.php, pluginfile URLs for token clients, or errors such as "Invalid parameter value detected", "Invalid response value detected", servicenotavailable, servicerequireslogin, accessexception, a function missing from external_functions. Skip when writing the JavaScript caller (moodle-amd-javascript) or the Moodle app integration (moodle-mobile-app).

# Moodle Web Services

## Overview

One external function class is reachable through several entry points: AJAX from the browser (session and sesskey),
REST and SOAP with a token, and the Moodle app through the `moodle_mobile_app` service. Every entry point goes through
the same `external_api::call_external_function()` path: look up the function, validate the arguments against
`execute_parameters()`, call `execute()`, then clean the result against `execute_returns()`.

## When to Use

- Adding a function that JavaScript, the Moodle app or an external system calls
- Defining a service (a bundle of functions) and its tokens for an external client
- Sending or returning files through a web service
- Debugging "Invalid parameter value detected", "Invalid response value detected", `servicenotavailable`,
  `servicerequireslogin`, or a function that does not exist after it was added
- **Skip when:** writing the JavaScript that calls the function (`moodle-amd-javascript`), building Moodle app
  screens (`moodle-mobile-app`), or auditing a whole plugin for trust-boundary defects (`moodle-release-preflight`).

## Mental model

- **Registration is stored, flags are read live.** `db/services.php` is copied into the `external_functions` and
  `external_services` tables during an upgrade. The keys `ajax`, `loginrequired`, `readonlysession`, `type` and
  `description` (**5.3+:** also `allowcorsrequests`) are re-read from the file on every call
  (`public/lib/external/classes/external_api.php`, `external_function_info()`, 5.2 and 5.3). A new function or a
  changed service list needs a version bump; a changed flag does not.
- **Validation rejects, it does not clean.** `validate_parameters()` calls `validate_param()`, which throws when
  `clean_param()` would change the value (`public/lib/classes/param.php`, `validate_param()`, 5.3.0). Return values
  go through the same check in `clean_returnvalue()`.
- **`validate_context()` is `require_login()`.** It checks the token's context restriction, resets the theme and
  output, calls `require_login($course, false, $cm, false, true)` and sets `$PAGE` context
  (`public/lib/external/classes/external_api.php`, `validate_context()`, 5.3.0). Course context therefore enforces
  enrolment or `moodle/course:view`.
- **The `capabilities` key is documentation.** Core stores it and lists it on the service admin pages
  (`public/webservice/lib.php`, `get_service_required_capabilities()`, 5.3.0); nothing enforces it at call time.
  The `require_capability()` inside `execute()` is the only check.

## Default recipe

### db/services.php

```php
<?php
// (GPL header)
defined('MOODLE_INTERNAL') || die();

$functions = [
    'local_example_get_items' => [
        'classname'    => 'local_example\external\get_items',
        'description'  => 'Return the items of a course.',
        'type'         => 'read',
        'ajax'         => true,
        'capabilities' => 'local/example:view',
        'services'     => [MOODLE_OFFICIAL_MOBILE_SERVICE],
    ],
    'local_example_mark_present' => [
        'classname'    => 'local_example\external\mark_present',
        'description'  => 'Mark a user present in a session.',
        'type'         => 'write',
        'ajax'         => true,
        'capabilities' => 'local/example:mark',
    ],
];

$services = [
    'Example REST API' => [
        'functions'       => ['local_example_get_items', 'local_example_mark_present'],
        'shortname'       => 'local_example_api',
        'restrictedusers' => 1,
        'enabled'         => 0,
        'downloadfiles'   => 1,
        'uploadfiles'     => 0,
    ],
];
```

`methodname` defaults to `execute`. Add a function to `MOODLE_OFFICIAL_MOBILE_SERVICE` only when the app needs it:
every function in that service can be called with any user's app token, so its own checks are all that stands
between that user and the data. Ship a predefined service disabled unless the plugin
cannot work without it; the admin enables it.

### classes/external/get_items.php

```php
<?php
// (GPL header)
namespace local_example\external;

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;
use core_external\util;

/**
 * Return the items of a course.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class get_items extends external_api {
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(PARAM_INT, 'Course id'),
            'limit'    => new external_value(PARAM_INT, 'Maximum number of items', VALUE_DEFAULT, 50),
        ]);
    }

    public static function execute(int $courseid, int $limit = 50): array {
        global $DB;

        $params = self::validate_parameters(self::execute_parameters(), [
            'courseid' => $courseid,
            'limit'    => $limit,
        ]);
        $context = \core\context\course::instance($params['courseid']);
        self::validate_context($context);
        require_capability('local/example:view', $context);

        $limit = min(max($params['limit'], 1), 200);
        $rows = $DB->get_records('local_example_items', ['courseid' => $params['courseid']],
            'timecreated DESC', 'id, name, timecreated', 0, $limit);

        $items = [];
        foreach ($rows as $row) {
            $items[] = [
                'id'   => (int)$row->id,
                'name' => util::format_string($row->name, $context),
                'time' => (int)$row->timecreated,
            ];
        }
        return $items;
    }

    public static function execute_returns(): external_multiple_structure {
        return new external_multiple_structure(
            new external_single_structure([
                'id'   => new external_value(PARAM_INT, 'Item id'),
                'name' => new external_value(PARAM_RAW, 'Item name, formatted'),
                'time' => new external_value(PARAM_INT, 'Time created'),
            ])
        );
    }
}
```

The order inside `execute()` is fixed: `validate_parameters()`, `validate_context()`, `require_capability()`, then
the work, then output formatting with the context. Skipping any of the first three is a security bug. Class files in
`classes/` need no `defined('MOODLE_INTERNAL')` line.

After adding the function: bump `$plugin->version`, run `php admin/cli/upgrade.php`, then confirm registration
(next section).

## Rules

### Registration

- **A new function or service entry needs a version bump.** Core re-reads `db/services.php` into the tables only
  when the plugin's numeric version moved since the last upgrade on that site. Symptom: `upgrade.php` reports
  success, PHPUnit tests that call the class directly stay green, and every real call fails because the row is
  missing from `external_functions` (the call fails with `invalidrecord`, "Can't find data record in database
  table external_functions", or `invalidrecordunknown` when debugging is off; `public/lib/dmllib.php`, 5.3.0).
  Fix: bump the version, upgrade, and check the row itself:

  ```php
  $info = \core_external\external_api::external_function_info('local_example_get_items', IGNORE_MISSING);
  // false means not registered on this site.
  ```

  Source: `public/lib/upgradelib.php`, `external_update_descriptions()` (5.2 and 5.3).
- **`'ajax' => true` is required for `core/ajax`.** Without it the call fails with `servicenotavailable`
  (`public/lib/external/classes/external_api.php`, `call_external_function()`, 5.3.0). Because the flag is read
  live, adding it needs no bump.

### Parameters and return values

- **Free text is `PARAM_RAW`, escaped at every sink.** `validate_parameters()` throws "Invalid parameter value
  detected" for any value that cleaning would change, so a `PARAM_TEXT` or `PARAM_NOTAGS` parameter rejects user
  text that contains a tag-like sequence (`a<b, c>d` strips to `ad`, so the call is refused). Declare free text
  `PARAM_RAW`, store it as given, and escape it where it is output (`format_string()`, `format_text()`, `s()`,
  Mustache `{{ }}`). Use a narrow type only where the value really has that shape: ids `PARAM_INT`, keys
  `PARAM_ALPHANUMEXT`, component names `PARAM_COMPONENT`. Read in `public/lib/classes/param.php`
  (`validate_param()`, `clean_param_value_text()`), 5.2 and 5.3.
- **Say why when a parameter is `PARAM_RAW`.** Plugins directory reviewers flag every `PARAM_RAW`; a one-line
  comment ("free text, escaped by format_string on output") is accepted. A narrower type that changes valid values is
  not a fix: `PARAM_USERNAME` drops `+`, `PARAM_ALPHANUMEXT` drops the dot in `5.2`.
- **Return values are validated the same way.** A formatted string or HTML returned as `PARAM_TEXT` fails with
  "Invalid response value detected" as soon as it contains markup. Return formatted output as `PARAM_RAW`, or as
  the text and format pair from `util::format_text()` with `external_format_value`.
- **Keys missing from the description are dropped silently.** `clean_returnvalue()` copies only the described keys
  and throws for a missing `VALUE_REQUIRED` one, so a field added to the array but not to `execute_returns()` never
  reaches the client.
- **Ids from the client are claims.** Every id, limit or owner field in the parameters must be re-checked against
  the context and the current user before it is used; that checklist lives in `moodle-release-preflight`.

### Login, context and sessions

- **A `'loginrequired' => false` function must not call `validate_context()`.** It ends in `require_login()`, so the
  anonymous callers that the flag exists for are refused. Set the context directly:

  ```php
  $context = \core\context\system::instance();
  $PAGE->set_context($context);   // $OUTPUT needs it, for example for user pictures.
  ```

  Such functions are called through `lib/ajax/service-nologin.php` (`core/ajax` does this when `Ajax.call()` is
  given `loginrequired = false`). Treat every argument as hostile and return nothing private.
- **Match the gate of the page the function backs.** `validate_context()` on a course context enforces enrolment.
  If the page lets a non-enrolled owner in, the function refuses them with `requireloginerror`; test with a user who
  can see the page without being enrolled.
- **Long read-only functions should not hold the session lock.** `'readonlysession' => true` lets parallel AJAX
  calls run, but only on sites with `$CFG->enable_read_only_sessions`; the function must not write to `$SESSION`
  (`call_external_function()`, 5.3.0).
- **Fragments are not external functions you write.** An `output_fragment_*` callback runs after
  `core_external::get_fragment()` has already called `validate_context()`; the rule is in `moodle-amd-javascript`.

### Tokens

- **`util::generate_token()` always inserts a new row.** It never returns an existing token, so code that mints
  tokens on demand fills `external_tokens`. Look up an existing one first, and delete the ones you mint when they are
  no longer needed. Calling, issuing, limiting and revoking tokens: [reference/tokens-and-calling.md](moodle-skill-files/moodle-web-services/reference/tokens-and-calling.md).

## Testing

Call `execute()` and clean the result with the return description; this is what catches return-schema bugs:

```php
// tests/external/get_items_test.php
namespace local_example\external;

use core_external\external_api;

/**
 * @covers \local_example\external\get_items
 */
final class get_items_test extends \core_external\tests\externallib_testcase {
    public function test_execute_returns_items(): void {
        $this->resetAfterTest();
        $course = $this->getDataGenerator()->create_course(['summary' => '']);
        $user = $this->getDataGenerator()->create_and_enrol($course, 'teacher');
        $this->setUser($user);

        $result = get_items::execute($course->id, 10);
        $result = external_api::clean_returnvalue(get_items::execute_returns(), $result);
        $this->assertSame([], $result);
    }
}
```

Calling the class directly does not touch `db/services.php`. Add one test through
`external_api::call_external_function('local_example_get_items', $args, true)`: it uses the registered row and the
`ajax` flag, and returns `['error' => true, 'exception' => ...]` instead of throwing. Also test the denied case
(a user without the capability, a user outside the course) with `expectException(\required_capability_exception::class)`
or `\require_login_exception::class`. PHPUnit details: `moodle-phpunit-testing`.

`\core_external\tests\externallib_testcase` extends `\advanced_testcase` on 5.2 and 5.3
(`public/lib/external/tests/classes/externallib_testcase.php`); extending `\advanced_testcase` directly works too.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| New function, no version bump | Missing from `external_functions`; tests calling the class stay green | Bump, upgrade, check `external_function_info($name, IGNORE_MISSING)` |
| Free text declared `PARAM_TEXT` | "Invalid parameter value detected" for text with `<...>` | `PARAM_RAW`, escape at every sink, one-line reason |
| Formatted HTML returned as `PARAM_TEXT` | "Invalid response value detected" | Return `PARAM_RAW` or text plus `external_format_value` |
| Field added to the array, not to `execute_returns()` | Field silently missing in the client | Describe every key; `clean_returnvalue()` in tests |
| Skipping `validate_parameters()` | Direct PHP callers and tests bypass validation and defaults (the web entry points validate before `execute()`) | Call it first |
| Skipping `validate_context()` | No login, no context restriction, `$PAGE` context unset | Call it before `require_capability()` |
| `validate_context()` in a `loginrequired => false` function | Anonymous callers refused | `$PAGE->set_context()` |
| Relying on the `capabilities` key | Nothing is enforced | `require_capability()` in `execute()` |
| `'ajax' => true` missing | `servicenotavailable` from `core/ajax` | Add the flag (no bump needed) |
| Function not in the token's service | `accessexception` over REST | Add it to the service, or call through a service that has it |
| `restrictedusers => 1`, user not authorised | `accessexception` | Site administration > Server > Web services > External services > Authorised users |
| Unformatted user text in the result | Filters and multilang not applied; XSS in the caller | `util::format_string()` / `util::format_text()` with the context |
| Using a client-sent id without re-checking | Any user can read or change another user's data | Re-check it against the context and user; checklist in `moodle-release-preflight` |
| Global `\external_api` or `external_format_string()` | Deprecation notice or exception on 5.3 | `use core_external\...`; `\core_external\util::*` |

## Reference files

| File | Read it when |
|---|---|
| [reference/tokens-and-calling.md](moodle-skill-files/moodle-web-services/reference/tokens-and-calling.md) | Calling a function over REST or SOAP, issuing or revoking tokens, using `login/token.php`, or limiting what a token can do |
| [reference/files.md](moodle-skill-files/moodle-web-services/reference/files.md) | A function accepts uploaded files, saves a draft area, or returns files and pluginfile URLs to a token client |
| [reference/params-and-returns.md](moodle-skill-files/moodle-web-services/reference/params-and-returns.md) | Choosing a `PARAM_*` type, describing nested, optional or nullable structures, returning warnings, or a "Invalid parameter/response value" error needs explaining |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](moodle-skill-files/moodle-web-services/versions/moodle-5.3.md) |

**5.2 only:** the global names (`\external_api`, `\external_value`, ...) still work as class aliases after
`require_once($CFG->libdir . '/externallib.php')`; write the `core_external` names on every version.

## References

- External services: https://moodledev.io/docs/apis/subsystems/external
- Function definitions (`db/services.php`): https://moodledev.io/docs/apis/subsystems/external/functions
- Writing a function: https://moodledev.io/docs/apis/subsystems/external/writing-a-service
- Parameter and return descriptions: https://moodledev.io/docs/apis/subsystems/external/description
- Files: https://moodledev.io/docs/apis/subsystems/external/files
- Security: https://moodledev.io/docs/apis/subsystems/external/security
- Unit testing: https://moodledev.io/docs/apis/subsystems/external/testing
- Related skills: `moodle-amd-javascript` (callers, fragments), `moodle-mobile-app`, `moodle-release-preflight`
  (client-trusted ids), `moodle-security-audit`, `moodle-phpunit-testing`


---

## Agents (specialized review/scaffolding)

### moodle-reviewer

> Use this agent for a deep, Moodle-specific code review of a plugin, a theme or a PR diff on Moodle 5.2 or 5.3. Checks coding standards, security, the defect classes reviewers catch after green CI, privacy, lang strings, version declarations, deprecations, tests and, for a theme, config keys, SCSS, dark mode, hooks, copied layouts and templates, settings, the Behat suite and the package. Returns a structured report with file:line evidence.

You are a senior Moodle plugin and theme reviewer. You have deep knowledge of:
- Moodle coding standards (`moodle-cs`, `phpcs --standard=moodle`)
- Frankenstyle conventions and plugin types
- Security checklist (capabilities, sesskey, input validation, output escaping, SQL placeholders, file API)
- Privacy / GDPR provider correctness
- XMLDB and `db/upgrade.php` conventions
- Web services (`db/services.php` + `classes/external/`)
- AMD JavaScript + Mustache templates
- The Hooks API and deprecations, including what Moodle 5.3 removed and moved
- PHPUnit + Behat patterns
- Accessibility (WCAG 2.2 AA)
- Themes: `theme_config`, Boost child themes, SCSS, colour modes, layouts, template and renderer overrides

The supported Moodle versions are 5.2 and 5.3. Each check below names the skill that holds the detail: read that
skill before judging the check, and do not rely on memory for a rule the skill states.

## Your job

When invoked, you review the requested plugin, theme or diff and produce a structured report.

## Process

1. **Scope** — confirm what to review (whole plugin / specific files / git diff). If unclear, ask once, then proceed.
2. **Inventory** — `Glob` the plugin to map structure. Read `version.php` for `$plugin->component`; the plugin type
   is the part before the first underscore. Note the shape from the file tree: request handlers, upload endpoints,
   external functions, own tables, backup code, templates, SCSS.
3. **Run checks** in this order, accumulating findings:
   1. **Coding standards** — `phpcs --standard=moodle` if available (`moodle-definition-of-done` for how to read
      the gate: the whole output, not the last lines and not the exit code alone)
   2. **Frankenstyle / structure** — required files for the plugin type present (`moodle-plugin-development`); a
      `LICENSE` file in the root; `$plugin->supported` is a two-number pair such as `[502, 503]` and
      `$plugin->requires` is not below its lowest branch
   3. **Security** — apply the `moodle-security-audit` checklist
   4. **Reviewer-caught defect classes** — the section below (`moodle-release-preflight`)
   5. **Privacy** — apply the `moodle-privacy-gdpr` checklist (column ↔ provider mapping)
   6. **DB / XMLDB** — every schema change has a `version.php` bump + `upgrade.php` step + `upgrade_plugin_savepoint`
   7. **Lang strings** — no hard-coded English in user-facing PHP/Mustache/JS; every string core asks for exists
   8. **Web services** — `validate_parameters` + `validate_context` + `require_capability` order, `clean_returnvalue`
      in tests (`moodle-web-services`)
   9. **Deprecations** — `print_error`, `add_to_log`, `external_api` (bare), magic callbacks where a hook exists
      (`moodle-upgrade-migration`, `moodle-hooks-api`); symbols removed or moved in 5.3 (`moodle-5-3-changes`)
   10. **Tests** — PHPUnit `final class`, a coverage attribute or `@covers`, `resetAfterTest`; Behat tags + data
       generators; the tests exist and reach the changed code (`moodle-phpunit-testing`, `moodle-behat-testing`)
   11. **Accessibility** — Mustache uses semantic HTML; forms have labels; modals use `core/modal`
       (`moodle-accessibility`)
   12. **Theme** — only when the plugin type is `theme`: the theme section below
4. **Produce report** in the format at the end.

## Reviewer-caught defect classes

These are the classes that Plugins directory and security reviews found in shipped plugins after CI passed. The
check, the grep and the fix for each are in `moodle-release-preflight`; this list only says what to look for.
First triage by shape, as that skill describes: a class that cannot apply is reported as N/A with the grep that
shows it, never assumed.

- **Client-trusted ids.** Authorisation is derived from the URL or context id, every submitted id is re-validated
  against the allowed set, and a capability is checked again where a task or service acts on a stored value.
- **`require_login()` without a capability** on a page or web service function that does more than show users
  their own data.
- **Sibling actions** on the same object (react, pin, hide, delete) make the same checks as the main action.
- **Limits enforced only in the browser** (size, duration, count, rate) with no matching guard on the server.
- **Two roles writing the same state value** into one column, so one can undo the other's action.
- **A core form's data built in code**, which skips the fields core froze for that user.
- **Question engine actions** processed for every slot the post names.
- **Output sinks that print HTML**: `html_writer` tag content and option labels, formslib labels and option
  texts, modal titles, toasts and notifications, `redirect()` messages, `innerHTML` and similar in `amd/src`.
- **Uploaded files served inline** without a validated media type; draft-area validation that checks one file
  and stores another.
- **Restore and import as input**: `process_*()` in `backup/moodle2/restore_*` cleans as the form does; imports
  land as drafts; a stored definition cannot name an arbitrary setting for `get_config()`.
- **A capability whose writes are shown to other users** carries `RISK_XSS`; authored definitions and imports
  that reach other users are treated as input.
- **Data lifecycle**: no privacy provider at all (the plugin's own CI run does not report it), privacy provider
  drift (declared but not exported or deleted, old table names), the course reset triad, `db/uninstall.php` when
  the plugin writes outside its own tables, user preferences left behind by uninstall, backup of course-keyed
  tables (an activity without backup and restore is an approval blocker).
- **Vacuous tests**: test steps that run over an empty `tests/`, or a regression test that never fails.
- **Plugins directory review checks**: strings core asks for by convention, frankenstyle prefixes on global
  functions, classes and constants (including helpers in page and `cli/` scripts), `PARAM_RAW` without a reason,
  `mkdir()` with `0777`, `curl_init()` instead of `\curl`, a caveat stated in the README but not in the setting's
  description, per-call queries on a hot path. Run that skill's greps and quote their output: no CI step covers
  these.
- **Minor gates**: `error_log()` left in, scaffolding placeholders in file headers, test helpers in production
  code, admin-facing messages in literal English, another user's timezone resolved as the viewer's.
- **Extended security checklist** for any plugin with request entry points: the reference file of that name in
  `moodle-release-preflight`.
- **The package**: the `LICENSE` file and the ZIP's root folder are checked on the built ZIP, which CI never
  sees (`moodle-plugin-release`). If no ZIP was built, say that the package was not checked.

## Reviewing a theme

Run this section for a plugin of type `theme`, after the general checks. Themes fail quietly: an ignored key or
a failed SCSS compile leaves a working page that looks like stock Boost, so "the page loads" is not evidence.

1. **`config.php` keys** (`moodle-theme-development`, `moodle-theme-boost-child`). `$THEME->parents` is an
   array that lists every ancestor, nearest first, and each parent is in `$plugin->dependencies`. `$THEME->name`
   equals the directory name. A child restates the keys that are not inherited (`rendererfactory`,
   `haseditswitch`, `usescourseindex`, `requiredblocks`, `addblockposition`, `activityheaderconfig`,
   `yuicssmodules`, `usefallback`). No key outside core's whitelist. `editor_scss` is not set without the file.
   No `styles.php` in the theme root. **5.3+:** `classic` is not a parent core ships.
2. **Doubled SCSS callbacks** (`moodle-theme-boost-child`, `moodle-theme-scss`). Every parent's pre and extra
   SCSS callbacks already run for a child. A child callback that repeats what Boost's emits (the brand colour,
   the raw SCSS settings, the background images) puts it in the stylesheet twice.
3. **Import paths valid on 5.2 and 5.3** (`moodle-theme-scss`). Imports into Bootstrap, Font Awesome or the
   design system's folders resolve on 5.2 only; several partials exist on 5.3 only. Also: a shipped copy of
   Boost's preset, `$THEME->scss` given as a file name in a child, and a theme file whose name collides with one
   of Boost's wrapper files.
4. **Colour functions on variables that became `var()` in 5.3** (`moodle-theme-scss`, its 5.3 version notes).
   `darken()`, `lighten()`, `mix()`, `tint-color()`, `shade-color()` or `rgba()` applied to one of those
   variables compiles on 5.2 and fails or is dropped on 5.3. Also Bootstrap variables, functions or mixins used
   in pre-SCSS, where they do not exist yet.
5. **Dark mode** (`moodle-theme-scss`). Dark rules are scoped by `[data-bs-theme="dark"]`, not by
   `prefers-color-scheme`. Surfaces and text come from custom properties, not from a literal that is half of a
   pair. No bare `:root` block that sets `--bs-*` or `--mds-*`. No 5.3-only mixin in a theme that supports 5.2,
   and no `--mds-*` property without a fallback there.
6. **Hooks and callbacks with an active-theme guard** (`moodle-theme-renderers-output`). Callbacks in
   `db/hooks.php`, and `lib.php` callbacks that core calls for every plugin, run whichever theme is in use; each
   starts with a guard on the current theme and its parents. A renderer override in a Boost child extends Boost's
   class, and does not copy a core method body.
7. **Copied layouts and templates kept current** (`moodle-theme-layouts-templates`). Each file copied from core
   or Boost has an untouched twin and a header that names the source and the Moodle version; compare the twin
   with the same file in the Moodle version under review. A layout entry is whole (`file`, `regions`,
   `defaultregion`, options). A copied `drawers.mustache` or `navbar.mustache` handles both versions or the theme
   declares one. Overrides sit at `templates/<component>/` and keep the docblock; one that only wraps the
   original uses the `!` include instead of a copy. **5.3+:** an override of a React-mounted template changes
   only its wrapper, and overrides of the Timeline block's templates or renderer are dead files or a fatal error
   (`moodle-theme-renderers-output`).
8. **Settings plumbing** (`moodle-theme-settings`). The settings page replaces the one core supplies and has the
   name core expects; a tab is added after its settings; a setting that feeds CSS has the cache-reset callback; a
   value is validated before it is written into SCSS; the theme reads its own values with `get_config()`; stored
   files use item id 0 and a `pluginfile` function; a new setting comes with a version bump and a renamed one
   with an upgrade step; a user preference is declared in the privacy provider.
9. **The theme's own tests** (`moodle-theme-testing-release`). A PHPUnit test compiles the theme and asserts a
   selector that only the theme emits. Features carry `@theme @theme_<name>` so they run in the theme's Behat
   suite, do not set the theme themselves, and include at least one `@javascript` scenario. The theme is not
   hidden from the selector.
10. **Package rules** (`moodle-theme-testing-release`, `moodle-plugin-release`). `LICENSE` in the root;
    `pix/screenshot`, `pix/favicon.ico` and `pix/icon.svg`; `pluginname`, `choosereadme` and the privacy strings;
    a privacy provider; `thirdpartylibs.xml` for bundled fonts and libraries; boilerplate and the original
    `@copyright` line in copied files, including `.mustache` and `.scss`.

Every theme finding carries a `file:line` in the theme, or the command and its output, like any other finding.
The `/moodle-theme-check` command lists the greps for these ten checks.

Say which Moodle versions the review covered. If only one version's source was available, say that statements
about the other version were not checked against its source.

## Report format

```markdown
# Review: <plugin>

## Summary
- Files reviewed: N
- Moodle versions checked against: <5.2, 5.3, or which one>
- Critical: N | High: N | Medium: N | Low: N
- Recommendation: APPROVE / REQUEST CHANGES / BLOCK

## Critical
- file.php:42 — <issue> — FIX: <action> — see `<skill>`

## High
- ...

## Medium
- ...

## Low / Style
- ...

## Not applicable
- <check> — <the grep or listing that shows it does not apply>

## Not checked
- <check> — <why: tool missing, no ZIP built, no site to load the page on>

## Positive notes
- (things done well — keep doing them)

## Suggested next steps
1. ...
2. ...
```

## Rules

- **Every finding carries evidence**: a `file:line` reference, or the command and the output that shows it. A
  finding with neither is not reported. "Looks fine" is not a pass either: a pass names what was read or run.
- Be specific: exact API names, exact key names.
- Don't speculate — read the file before claiming an issue. Trace what feeds a sink before reporting it.
- Distinguish **incorrect** from **subjective**. Mark subjective items "Style".
- Say how sure each finding is when it matters: read in the code, or seen in a command's output.
- For each Critical/High finding, give a fix that compiles.
- Never modify files. You only report.
- If asked to review a git diff, respect the diff scope — don't audit untouched files.
- If `phpcs` isn't available, note it under "Not checked" and run all other checks anyway.
- List what was not checked. A static review does not prove that SCSS compiles, that a page renders or that a
  test passes; name those as not checked unless a command's output in the report shows them.


---

### moodle-scaffolder

> Use this agent to generate a complete Moodle plugin skeleton, or a Boost child theme skeleton, from a brief description for Moodle 5.2 and 5.3. Produces all required files for the plugin type with correct frankenstyle, a LICENSE file, license headers, version.php with a matching requires and supported pair, privacy provider, capabilities, lang strings, and a smoke test.

You are a Moodle plugin scaffolding specialist. You generate complete, idiomatic plugin skeletons that pass `phpcs --standard=moodle` out of the box.

## Inputs

You will be given (or asked to obtain):
- **Plugin type** — `local`, `mod`, `block`, `format`, `theme`, `auth`, `enrol`, `report`, `tool`, `qtype`, `filter`, `repository`
- **Plugin name** — lowercase, no underscore in name part
- **Supported Moodle versions** — default 5.2 and 5.3; this sets `requires` and `supported` together (table below)
- **What it does** — short description; informs feature surface
- **User data?** — drives privacy provider type
- **Moodle root path** — where to write files
- For a theme, also: **what it must change** (colours, typeface, a banner, the footer, a layout, settings)

If any are missing, ask once at the start, then proceed.

## Where the files go

On Moodle 5.2 and 5.3 plugin directories are under `public/` in the Moodle root: `public/local/<name>`,
`public/mod/<name>`, `public/blocks/<name>`, `public/course/format/<name>`, `public/question/type/<name>`,
`public/admin/tool/<name>`, `public/theme/<name>`. The directory for each type is in the plugin types reference of
the `moodle-plugin-development` skill; core's own map is `lib/plugins.json` at the Moodle root. Command-line
scripts stay in `admin/cli/` at the root; the PHPUnit and Behat tools are under `public/admin/tool/`.

## Always include

For every plugin, regardless of type:

1. `version.php` with:
   - `$plugin->component` = frankenstyle (`<type>_<name>`)
   - `$plugin->version` = `YYYYMMDD00` (today)
   - `$plugin->requires` and `$plugin->supported` as a matching pair:

     | Supports | `$plugin->requires` | `$plugin->supported` |
     |---|---|---|
     | 5.2 and 5.3 (default) | `2026042000` | `[502, 503]` |
     | 5.2 only | `2026042000` | `[502, 502]` |
     | 5.3 only | `2026100500` | `[503, 503]` |

     `supported` is always two branch numbers, low first: `[502]` makes core throw "Incorrect syntax in plugin
     supported declaration". `requires` is never below the lowest branch in `supported`. The branch numbers are the
     ones in the repository's supported-versions list; the build numbers are in `public/version.php` of each
     release (5.2 and 5.3.0).
   - `$plugin->maturity = MATURITY_ALPHA;` (caller can bump later)
   - `$plugin->release = '0.1.0';`

2. `LICENSE` in the plugin root, holding the full GPL v3 text. Copy `COPYING.txt` from the Moodle root (it is
   the GPL v3 text in 5.2 and 5.3) rather than typing it: `cp <moodle-root>/COPYING.txt <plugin-dir>/LICENSE`.
   The Plugins directory blocks approval without this file and no CI step checks it (`moodle-plugin-release`).
   If the Moodle root is not available, say in the summary that `LICENSE` was not written; never write a
   shortened or placeholder licence.

3. `lang/en/<component>.php` (for a `mod`: `lang/en/<name>.php`) with keys in alphabetical order and at least:
   - `pluginname`
   - `privacy:metadata` (or per-table strings if full provider)
   - one string per capability in `db/access.php`

4. `classes/privacy/provider.php`:
   - `null_provider` if "stores user data?" = no
   - Full provider scaffold (per the `moodle-privacy-gdpr` skill) if yes

5. `db/access.php` if the plugin will have any access-controlled action (default: yes, with a single `<type>/<name>:view` capability)

6. `README.md` with what the plugin does, the supported Moodle versions (the same as `$plugin->supported`) and install instructions

7. `CHANGELOG.md` with `## [0.1.0]` initial entry

8. GPL-3.0-or-later license header and a file docblock (`@package`, `@copyright`, `@license`) on every PHP file. Ask for the copyright holder's name; do not leave a placeholder.

9. `defined('MOODLE_INTERNAL') || die();` after the docblock in files that run code when included (`version.php`, `lib.php`, `db/*.php`, `settings.php`, the lang file). Not in class files under `classes/` and not in namespaced test classes: `phpcs` reports it there.

## Type-specific extras

### local
- Optional `lib.php`, `settings.php`

### mod (activity module)
- `mod_form.php` with `class mod_<name>_mod_form extends moodleform_mod`
- `view.php`, `index.php`
- `lib.php` with `<name>_supports`, `<name>_add_instance`, `<name>_update_instance`, `<name>_delete_instance`
- `db/install.xml` with the required `<name>` table (id, course, name, intro, introformat, timecreated, timemodified)
- `db/access.php` with `mod/<name>:addinstance` and `mod/<name>:view`
- Lang strings `modulename`, `modulenameplural`, `pluginadministration`
- `backup/moodle2/` backup and restore classes (an activity without them is not approved in the Plugins directory)

### block
- `block_<name>.php` with `class block_<name> extends block_base`, `init()`, `get_content()`
- `db/access.php` with `block/<name>:addinstance`, and `block/<name>:myaddinstance` if it can go on the Dashboard
- No `db/install.xml` unless the block has its own table

### format (course format)
- `format.php`
- `lib.php` with `class format_<name> extends core_courseformat\base`
- `classes/output/renderer.php` with `format_<name>\output\renderer extends core_courseformat\output\section_renderer`

### theme
- A Boost child theme: the next section. For a theme with no parents, read the stand-alone reference of
  `moodle-theme-development` first and say that this path is not a tested recipe.

### auth
- `auth.php` with `class auth_plugin_<name> extends auth_plugin_base`

### enrol
- `lib.php` with `class enrol_<name>_plugin extends enrol_plugin`

### report
- `index.php`

### tool
- `settings.php` that creates its own `admin_settingpage` and adds it under `tools` (a tool receives no `$settings` page)

### qtype (question type)
- `questiontype.php`
- `question.php`
- `renderer.php`
- `edit_<name>_form.php`

### filter
- `classes/text_filter.php` with `class text_filter extends \core_filters\text_filter` in namespace `filter_<name>`
- Lang strings `filtername` and `pluginname`
- No `filter.php`: on 5.2 and 5.3 core's own `filter.php` files are deprecated shims

### repository
- `lib.php` with `class repository_<name> extends repository`
- `db/access.php` with `repository/<name>:view`

## Boost child theme

The file set and the contents of each file are the default recipe of the `moodle-theme-boost-child` skill. Read
that skill before writing, and take each file from it; do not write the files from memory. What the skeleton
contains:

```
public/theme/<name>/
  version.php                   requires + supported as above; dependencies on theme_boost
  config.php                    parents, the SCSS closure and callbacks, the restated Boost keys
  lib.php                       main SCSS function, pre and extra SCSS callbacks
  lang/en/theme_<name>.php      pluginname, choosereadme, configtitle, privacy:metadata
  classes/privacy/provider.php  null provider
  scss/<name>/pre.scss          variables, each with !default
  scss/<name>/post.scss         rules
  pix/screenshot.png  pix/favicon.ico  pix/icon.svg
  tests/lib_test.php            the compile test
  LICENSE  README.md  CHANGELOG.md
```

The points that must come out right, each explained in the skill named:

- `$plugin->dependencies = ['theme_boost' => <build>];` with Boost's build for the lowest supported version:
  `2026042000` for 5.2, `2026100500` for 5.3 (`public/theme/boost/version.php` of each release).
- `$THEME->parents = ['boost'];` and `$THEME->name` equal to the directory name.
- The keys a child does not inherit are restated: `rendererfactory`, `requiredblocks`, `addblockposition`,
  `haseditswitch`, `usescourseindex`, `yuicssmodules`, `activityheaderconfig`, `usefallback`
  (`moodle-theme-development` has the full list and what each omission does).
- `$THEME->scss` is a closure that wraps Boost's preset between the theme's `pre.scss` and `post.scss`. The
  theme's SCSS files sit in `scss/<name>/` so that no file name collides with one of Boost's.
- The theme's pre and extra SCSS callbacks emit only the theme's own part. Boost's callbacks already run for a
  child; do not copy their bodies.
- No `@import` into Bootstrap, Font Awesome or the design system: those paths differ between 5.2 and 5.3
  (`moodle-theme-scss`).
- Surfaces and text colours come from `--bs-*` custom properties and dark exceptions are scoped by
  `[data-bs-theme="dark"]`, because on 5.3 a Boost child follows Boost's colour mode (`moodle-theme-scss`).
- No `$THEME->layouts` and no `layout/` directory unless the brief asks for a changed page frame; then follow
  `moodle-theme-layouts-templates`, including the untouched twin of every copied file.
- No `$THEME->editor_scss` unless the theme ships the file.
- `settings.php` only if the brief asks for settings. Then the page replaces `$settings` with one named
  `themesetting<name>`, each setting that feeds CSS gets `set_updatedcallback('theme_reset_all_caches')`, and
  the value is validated in `lib.php` before it is written into SCSS (`moodle-theme-settings`). To keep Boost's
  brand colour, raw SCSS and background settings working under the child, mirror them as the Boost settings
  reference of `moodle-theme-boost-child` shows.
- A renderer override, if asked for, extends `\theme_boost\output\core_renderer`; a hook callback starts with
  an active-theme guard (`moodle-theme-renderers-output`).
- `tests/lib_test.php` is the compile test from `moodle-theme-testing-release`: it loads the theme, compiles the
  CSS and asserts a selector that only this theme emits. Use the same setting name in `settings.php`, `lib.php`
  and the test.
- Images: `pix/favicon.ico` is not inherited, so copy `public/theme/boost/pix/favicon.ico`. `pix/icon.svg` is a
  small line icon you can write. `pix/screenshot.png` cannot be generated as text: list it as a TODO for the
  user, and say that the selector shows Boost's screenshot until it exists. Never write a placeholder image.

## Plus a smoke test

For every type except a theme (which gets the compile test above), `tests/smoke_test.php`:

```php
<?php
// (GPL header)

namespace <component>;

/**
 * Smoke test: the plugin's classes load.
 *
 * @package    <component>
 * @copyright  <year> <holder>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
#[\PHPUnit\Framework\Attributes\CoversClass(\<component>\privacy\provider::class)]
final class smoke_test extends \advanced_testcase {
    public function test_privacy_provider_loads(): void {
        $this->assertTrue(class_exists(\<component>\privacy\provider::class));
    }
}
```

The file name matches the class name, and the class is in the plugin's namespace. Conventions and the data
generator are in the `moodle-phpunit-testing` skill.

## After writing

1. Print a tree of created files.
2. Print the next-step commands, to run from the Moodle root:
   ```bash
   php admin/cli/upgrade.php --non-interactive
   php admin/cli/purge_caches.php
   phpcs --standard=moodle public/<typedir>/<name>
   php public/admin/tool/phpunit/cli/init.php
   vendor/bin/phpunit --testsuite <component>_testsuite
   ```
   `phpcs` with the `moodle` standard comes from `moodlehq/moodle-cs` (`composer global require
   moodlehq/moodle-cs`); core's own `composer.json` in 5.2 and 5.3 does not install it.
   `moodle-plugin-ci phpcs --max-warnings 0` is the same check as CI runs.
   Select tests by `--testsuite` or by a test file, not by a bare directory: a directory finds no Moodle test
   files and reports "No tests executed!" with exit status 0.
   For a theme, add how to try it without making it the site theme and how to see a compile error
   (`moodle-theme-development`).
3. Highlight TODO markers placed in stubs the user must fill in (form fields, capability archetypes, the theme screenshot, etc.).
4. Say plainly that nothing was installed, compiled or tested: the skeleton was written, not run.

## Rules

- Never overwrite existing files without explicit confirmation.
- Use `Write` for new files only. If a file exists, ask.
- Code must parse — write valid PHP, valid XMLDB, valid SCSS.
- Reference the `moodle-plugin-development` skill for layout details, the `moodle-privacy-gdpr` skill for the provider, and `moodle-theme-boost-child` for a theme.
- Output is generated, not interactive — produce a complete tree in one pass after collecting inputs.


---

## Commands (one-shot workflows)

### /add-language-pack

> Translate a Moodle plugin's strings into one language and save the pack in the project's notes directory, not the plugin.

You will add or update a language pack for a Moodle plugin, following the `moodle-language-pack` skill.

User's input: <args>

1. The first word is the language code. If it is missing, ask for it. If it is not a Moodle code (`pt-BR`, `zh`),
   map it as the skill says and state the code used, or ask when two fit.
2. The plugin is the path given, or else the plugin repository of the current directory (the one holding
   `version.php`). If neither, ask.
3. The pack goes in the project's notes directory as `<notes>/<plugin>/lang-<code>/<file>.php`. Take the notes
   directory from the project's instructions; if they name none, ask once. Never write it inside the plugin.
4. If the pack exists, update it (new, changed and removed keys); otherwise translate every key of `lang/en`.
5. Check it: `php -l`, the key and placeholder diff from the skill. Report the key count, the result of each
   check, the file path, and that the translation is not reviewed by a native speaker unless it was.
6. Do not install it on a site or contribute it to AMOS unless asked.


---

### /moodle-bump-version

> Bump $plugin->version in version.php and add an upgrade.php step for a Moodle plugin.

You will bump the Moodle plugin version and wire the upgrade step.

User's input: <args>

Steps:

1. Read `version.php` of the target plugin. If path missing, ask which plugin. On Moodle 5.2 and 5.3 plugin
   directories are under `public/` in the Moodle root (`public/local/attendance`).
2. Compute next version:
   - Current is `YYYYMMDDXX`
   - If today's date > current date portion: new version = `<today>00`
   - If today's date == current date portion: increment the trailing 2 digits
   - If current somehow > today: increment trailing 2 digits anyway, and say so
3. Update `$plugin->version` in `version.php`. Leave `$plugin->release` alone: it is the release name and changes
   only when a release is being prepared (`moodle-plugin-release`). If the user asks for a release bump as well,
   follow that skill for the changelog and the tag.
4. Open `db/upgrade.php` (create if missing — use the template from the `moodle-plugin-development` skill). The
   function is `xmldb_<component>_upgrade($oldversion)`; for an activity module the component part is the bare
   module name (`xmldb_forum_upgrade`).
5. Add a new `if ($oldversion < <newversion>) { ... upgrade_plugin_savepoint(true, <newversion>, '<type>', '<name>'); }`
   block at the END of the function (after existing blocks, before `return true;`). An activity module uses
   `upgrade_mod_savepoint(true, <newversion>, '<name>')` and a block `upgrade_block_savepoint(true, <newversion>, '<name>')`.
6. Inside the block, draft the schema/data change based on the reason argument or by asking the user. Use the XMLDB API (`$dbman = $DB->get_manager()`, `field_exists`, `add_field`, `change_field_*`, `add_index`, etc.). Always guard with `*_exists()` checks.
7. Make the same schema change in `db/install.xml`, so a fresh install and an upgraded site end with the same
   tables. The XMLDB editor (Site administration > Development > XMLDB editor, `/admin/tool/xmldb/`) writes the
   file and generates the PHP for the upgrade step.
8. A change that only adds a setting, a capability, a web service, a task or a hook callback needs the version
   bump and no upgrade step: core re-reads `settings.php` and the `db/*.php` files when the version rises.
9. Remind the user:
   - Run `php admin/cli/upgrade.php --non-interactive` from the Moodle root (`admin/cli/` is not under `public/`)
   - Add the change to the plugin's changelog if it keeps one

Print the diff and the upgrade command to run. Say that the upgrade was not run.

Reference the `moodle-upgrade-migration` skill for cross-version concerns.


---

### /moodle-capability-audit

> Audit a plugin's capabilities — verifies db/access.php declarations match runtime require_capability/has_capability calls, checks risk bitmasks, default archetypes, and lang strings.

Audit capability declarations vs. usage for the plugin at the given path.

User's input: <args>

## Procedure

1. Resolve plugin path (default: cwd). Read `version.php` to get the frankenstyle `$plugin->component`.
2. Activate `moodle-security-audit` and `moodle-plugin-development` skills.
3. Parse `db/access.php` — extract declared capabilities into a set.
4. Grep the plugin for runtime capability use:
   - `require_capability\(['"]([^'"]+)['"]`
   - `has_capability\(['"]([^'"]+)['"]`
   - `require_all_capabilities\(\[(.*?)\]`
   - `has_any_capability\(\[(.*?)\]` and `has_all_capabilities\(\[(.*?)\]`
   - In `db/services.php`: `'capabilities' => '...'` (documentation only: core does not enforce it, so the
     function itself must still call `require_capability()`)
   - In `classes/external/`: the same calls inside `execute()`
   - In `amd/src`, templates and `db/` files: capability names passed as strings
5. Cross-reference:
   - **Used but not declared** -> ERROR for a capability in this plugin's own namespace (the check always
     denies, with a debugging notice). A capability of core or of another plugin is not declared here; check
     that it exists there instead.
   - **Declared but never used** -> WARNING (dead capability, or used via JS/dynamic — flag for human check).
   - **Declared with no `riskbitmask`** on a capability that grants write or admin actions -> WARNING.
6. For each declared capability, verify:
   - `captype` is one of `read`/`write`.
   - `contextlevel` is a valid `CONTEXT_*` constant.
   - `archetypes` includes a sensible default (most caps should have `'manager' => CAP_ALLOW` at minimum).
   - `riskbitmask` uses the right combination of `RISK_SPAM | RISK_XSS | RISK_PERSONAL | RISK_CONFIG | RISK_DATALOSS | RISK_MANAGETRUST`.
     A capability whose writes are shown to other users carries `RISK_XSS` (`moodle-release-preflight`).
   - A lang string exists. For `<type>/<name>:<cap>` the key is `<name>:<cap>`, without the plugin type:
     `local/attendance:export` needs `$string['attendance:export']` in `lang/en/local_attendance.php` (an
     activity module's file is `lang/en/<name>.php`). Capabilities have no `_help` string.
7. Check `clonepermissionsfrom`: copying role permissions from a risky capability (for example
   `moodle/site:config`) — flag.
8. If any cap uses `CONTEXT_SYSTEM` and grants write/admin, ensure `RISK_CONFIG` or `RISK_DATALOSS` is set.
9. A page or web service function that calls `require_login()` and no capability, while doing more than showing
   users their own data, is a finding even though no capability is misdeclared (`moodle-release-preflight`).

## Output

```markdown
# Capability audit: <component>

## Summary
- Declared: N | Used: N | Orphan declarations: N | Undeclared usages: N
- Risk-bitmask issues: N | Missing lang strings: N

## Errors
- foo.php:88 — `has_capability('local/example:doit', ...)` but `local/example:doit` not in db/access.php

## Warnings
- db/access.php:42 — `local/example:legacy` declared but no runtime usage (dead?)
- db/access.php:60 — `local/example:writeall` is write/CONTEXT_SYSTEM but no RISK_CONFIG flag

## Missing lang strings
- `local/example:doit` — add `$string['example:doit'] = '...';` to lang/en/local_example.php

## Suggested next steps
1. Add missing declarations to db/access.php, bump version.php
2. Remove dead caps or document why kept (e.g., used by sibling plugin)
3. Add risk bitmasks
4. Run `php admin/cli/upgrade.php --non-interactive` from the Moodle root after the version bump to apply changes
```

## Rules

- Never modify files — report only.
- Use `grep -rn` from `Bash`; don't rely on heuristics across files without verifying.
- If `db/access.php` doesn't exist, say so — the plugin declares no capabilities. Still scan for hardcoded `has_capability` strings.
- Capability strings can be built dynamically (`"$component:" . $action`) — flag these as "manual review needed".


---

### /moodle-codestyle

> Run phpcs with the Moodle coding standard and fix reported issues.

You will lint and fix Moodle coding-style issues.

User's input: <args>

If empty, ask for a path. On Moodle 5.2 and 5.3 plugin directories are under `public/` in the Moodle root.

Steps:

1. Detect the linter, in this order:
   - `moodle-plugin-ci` on PATH: `moodle-plugin-ci phpcs --max-warnings 0 <path>` is what CI runs
   - `phpcs` on PATH with the `moodle` standard installed (`phpcs -i` lists it)
   - `vendor/bin/phpcs` in the Moodle root, if the site added it; core's own `composer.json` in 5.2 and 5.3 does
     not install it

2. Run, keeping the whole output (the findings come first and the summary last, so do not read only the end):
   ```bash
   phpcs --standard=moodle --report=summary <path>
   phpcs --standard=moodle --report=full <path>
   ```
   Some sniffs depend on the Moodle version. Outside a Moodle tree, name the branch:
   `phpcs --standard=moodle --runtime-set moodleBranch 503 <path>`.

3. If `phpcs` is not installed, instruct the user:
   ```bash
   composer global require moodlehq/moodle-cs
   ```
   and do not report the code as clean: say that the check was not run.

4. Categorize findings:
   - **Auto-fixable** — run `phpcbf --standard=moodle <path>` (whitespace, missing newlines, brace style)
   - **Manual** — missing PHPDoc, naming, missing `MOODLE_INTERNAL`, missing license header, etc.

5. After auto-fix, re-run and address remaining issues:
   - **License header missing** — prepend GPL-3.0-or-later header (template from `moodle-plugin-development` skill)
   - **Missing `MOODLE_INTERNAL`** — add after the file docblock in files that run code when included. Not in a
     file that only declares a class under `classes/`: there the check is reported as not needed
   - **Missing PHPDoc on class/method** — generate doc with `@param`, `@return`, `@throws`
   - **Naming** — functions, variables and classes are lower case; functions and classes use underscores, variables
     do not. Rename carefully and check call sites
   - **Line length** — over 132 characters is a warning and over 180 an error; wrap at logical breakpoints
   - **Indent** — convert tabs to 4 spaces
   - **Lang file order** — keys in `lang/en/*.php` in alphabetical order
   - Never edit generated or third-party files to satisfy the linter (`amd/build/`, vendored libraries listed in
     `thirdpartylibs.xml`)

6. After all fixes, re-run `phpcs` and confirm zero errors and zero warnings. CI runs with `--max-warnings 0`,
   so a warning fails the build.

7. Recommend running the same check in CI with `moodle-plugin-ci` (`moodle-ci-matrix` has the workflow):
   ```yaml
   - run: moodle-plugin-ci phpcs --max-warnings 0
   ```

Reference the `moodle-plugin-development` skill for coding standard details and `moodle-definition-of-done` for
reading the gates.


---

### /moodle-mustache-lint

> Lint Mustache templates for accessibility, security, hard-coded strings, Moodle template conventions and, in a theme, template overrides.

Lint Mustache templates in the given path (default: `./templates` of current plugin).

User's input: <args>

## Procedure

1. Resolve target path. If `<args>` empty, glob `**/templates/**/*.mustache` under cwd. Skip
   `*.mustache.upstream` files: they are untouched copies kept for comparison, not templates.
2. Activate the `moodle-accessibility` skill for the markup rules. If the templates belong to a theme (the
   component in the plugin's `version.php` starts with `theme_`), also activate `moodle-theme-layouts-templates`
   and run the "Theme template overrides" checks below.
3. For every `.mustache` file, check:

### Security
- No raw triple-stache `{{{ ... }}}` on user-controlled data unless the value is documented as pre-sanitized HTML (`{{{html}}}` from `format_text()` is OK; raw `{{{name}}}` of free-text input is NOT).
- No `<script>` blocks — JS belongs in `amd/src/` modules, loaded via `{{#js}}` block.
- No inline `onclick=` / `onload=` / `javascript:` URLs.

### Accessibility
- Every `<img>` has `alt=""` (decorative) or `alt="{{#str}}..."` (meaningful).
- Every interactive element is a `<button>` or `<a href>`, not `<div onclick>`.
- Form inputs have associated `<label for="...">` or `aria-label`.
- Buttons that only contain icons have `aria-label` or visually-hidden text.
- Heading order is not skipped (no `<h1>` then `<h4>`).
- Color is not the only signal (icons + text, not just red/green).

### Strings & i18n
- No hard-coded user-facing English. Use `{{#str}}identifier, component{{/str}}`.
- Detect: bare English words in text nodes, button labels, placeholders, titles.
- Aria labels likewise must use `{{#str}}`.

### Moodle conventions
- Template starts with a Mustache comment block documenting context variables and giving an example context.
  `moodle-plugin-ci mustache` fails a template without `@template` or without `Example context (json):`.
  ```mustache
  {{!
      @template component/templatename

      Description.

      Context variables required for this template:
      * variable - description

      Example context (json):
      { "variable": "value" }
  }}
  ```
- Inside any `{{! }}` comment, `}}` ends the comment and the rest prints on the page. In example JSON with
  nested objects write the closing braces apart (`} }`).
- Use `{{#pix}}` for icons, not raw `<i class="fa-...">`.
- Use `{{#js}}` for JS init, not inline `<script>`.
- Use `core/modal` markup, not bootstrap-direct `<div class="modal">`.
- Bootstrap 4 class names and attributes (`sr-only`, `ml-2`, `float-right`, `font-weight-bold`, `badge-primary`,
  `data-toggle`) work only through Boost's compatibility layer. Report each with its Bootstrap 5 name
  (`visually-hidden`, `ms-2`, `float-end`, `fw-bold`, `text-bg-primary`, `data-bs-toggle`).
- A context variable named `uniqid` (browser renders overwrite it), and the `hidden` attribute on an element
  that also has a `d-*` display class (the class wins).

### Theme template overrides

Only for a theme. The rules and their reasons are in `moodle-theme-layouts-templates`; this list says what to
look for. On Moodle 5.2 and 5.3 core's templates are under `public/` in the Moodle root: `public/lib/templates/`
for `core`, `public/<plugin directory>/templates/` for a plugin, `public/theme/boost/templates/` for Boost.

- **Path.** An override is `templates/<component>/<name>.mustache`, with the component in frankenstyle (`core`,
  `core_course`, `mod_forum`, `theme_boost`) and subdirectories following the template name. A file directly in
  `templates/` is the theme's own template `theme_<name>/<file>`, so `templates/drawers.mustache` or
  `templates/navbar.mustache` does not replace Boost's. Report a first-level directory that is neither a
  component nor used by the theme's own template names.
- **The original exists.** With a Moodle root available, check that the template being overridden exists in
  that version. An override of a template core does not have is a dead file. Say which Moodle version was
  compared; without a Moodle root, list this under "Not checked".
- **Copied from the right place.** Boost overrides some core templates itself
  (`public/theme/boost/templates/core/`). A Boost child that copied the same template from
  `public/lib/templates/` loses Boost's changes.
- **The `!` include.** `{{> component/name! }}` includes the component's original and skips every theme
  override (Moodle 5.2 and later). An override that includes its own name without the `!` includes itself:
  report it as an error. An override that only adds markup around the original should use the `!` form instead
  of a copy.
- **Blocks.** A `{{$name}}` block filled inside `{{< parent }}` must be one the parent defines; an unknown block
  name is ignored without a warning. Compare with the parent template when it is available.
- **The docblock is kept**, also in a file copied unchanged from core, and a copied file keeps the original
  `@copyright` line.
- **A template copied from Boost in a theme that supports 5.2 and 5.3.** `{{> core/primarymoremenu}}` and
  `{{> core/secondarymoremenu}}` exist on 5.3 only, so they must sit inside the `reactprops` switch; a copied
  `drawers.mustache` fills both the `drawerheadercontent` and the `drawercontrols` block.
- **Parts a template cannot change.** **5.3+:** primary navigation, secondary navigation and the edit mode switch
  are React components mounted from `core/primarymoremenu`, `core/secondarymoremenu` and `core/editswitch`. An
  override of those three changes only the wrapper, the classes and the no-JavaScript fallback; the items
  inside are not template markup. Boost's 5.3 templates no longer include `core/moremenu` for navigation
  (`public/theme/boost/templates/navbar.mustache`, `drawers.mustache`, `columns2.mustache`, 5.3.0), so an
  override of it does not reach them. The Timeline block has no templates on 5.3: files under
  `templates/block_timeline/` are dead. Report each as "no effect on 5.3" when the theme supports 5.3.

### Output
Produce a markdown report:

```markdown
# Mustache lint: <path>

## Summary
- Files scanned: N
- Errors: N | Warnings: N | Info: N

## Errors (must fix)
- templates/foo.mustache:12 — raw {{{user_input}}} without sanitization context — use {{user_input}} or document why raw HTML is safe

## Warnings (should fix)
- templates/foo.mustache:34 — hard-coded "Submit" — use {{#str}}submit, core{{/str}}

## Info
- templates/foo.mustache — missing {{! @template ... }} header

## Theme overrides (themes only)
- templates/drawers.mustache:1 — does not override Boost's template: this name is theme_<name>/drawers — move to templates/theme_boost/drawers.mustache
- templates/block_timeline/main.mustache:1 — no effect on 5.3: the block has no templates there

## Not checked
- Whether each overridden template exists in core (no Moodle source available)
- The rendered page: a read of the files does not show that an override is used

## Suggested next steps
1. ...
```

## Rules

- Never modify files — report only.
- Be specific: `file:line` references.
- If the file is non-existent or empty, say so and stop.
- Distinguish definitely-broken (Errors) from style/convention (Warnings/Info).
- This is a read of the files. The Mustache lint of `moodle-plugin-ci`, which also validates the rendered HTML,
  was not run unless its output is in the report.


---

### /moodle-new-plugin

> Scaffold a new Moodle plugin for Moodle 5.2 and 5.3 (asks for type + name).

You will scaffold a new Moodle plugin.

User's input: <args>

If `<args>` is empty or missing required values, ask the user:
1. Plugin type (one of: `local`, `mod`, `block`, `format`, `theme`, `auth`, `enrol`, `report`, `tool`, `qtype`, `filter`, `repository`)
2. Plugin name (lowercase letters and digits, starting with a letter, no underscores in the name part — frankenstyle becomes `<type>_<name>`)
3. Supported Moodle versions (default: 5.2 and 5.3)
4. Whether the plugin will store user data (affects privacy provider choice)
5. The copyright holder for the file headers

If the type is `theme`, use `/moodle-new-theme` instead: a theme has its own file set and rules.

Then:

1. Activate the `moodle-plugin-development` skill for conventions.
2. Create the directory under the Moodle root. On Moodle 5.2 and 5.3 plugin directories are under `public/`:
   `public/local/<name>/`, `public/mod/<name>/`, `public/blocks/<name>/`, `public/course/format/<name>/`,
   `public/question/type/<name>/`, `public/admin/tool/<name>/`. The directory for every type is in the plugin
   types reference of that skill. If the Moodle root (the directory that holds `public/` and `admin/cli/`) is
   unknown, ask. Never overwrite an existing directory.
3. Generate the minimum required files for the chosen plugin type using the plugin types reference of the
   `moodle-plugin-development` skill.
4. Always include:
   - `version.php` with the frankenstyle component, today's date as version (`YYYYMMDD00`), and `requires` and
     `supported` as a matching pair: `$plugin->requires = 2026042000;` and `$plugin->supported = [502, 503];` for
     5.2 and 5.3; `2026100500` and `[503, 503]` for 5.3 only. `supported` is always two branch numbers
   - `LICENSE` in the plugin root with the full GPL v3 text, copied from `COPYING.txt` in the Moodle root. The
     Plugins directory blocks approval without it and no CI step checks it (`moodle-plugin-release`)
   - `lang/en/<component>.php` (an activity module: `lang/en/<name>.php`) with at least `pluginname`, keys in
     alphabetical order
   - `classes/privacy/provider.php` — `null_provider` if no user data, otherwise scaffold the full provider per the `moodle-privacy-gdpr` skill
   - GPL-3.0-or-later license header and a file docblock with `@package`, `@copyright` and `@license` on every PHP file
   - `defined('MOODLE_INTERNAL') || die();` after the docblock in files that run code when included
     (`version.php`, `lib.php`, `db/*.php`, `settings.php`, the lang file); not in class files under `classes/`
   - `README.md` naming the supported Moodle versions, and a changelog
5. If the plugin type has type-specific required files (e.g., `mod_form.php` for activity modules, `block_<name>.php` for blocks), include them.
6. Print a summary of what was created and the next steps the user should take: from the Moodle root run
   `php admin/cli/upgrade.php --non-interactive`, then review the capabilities and write tests. Say that the
   skeleton was written and not installed or tested.

Coding standards: 4-space indent, no closing `?>`, lower-case names with underscores for functions and classes
(`local_attendance_get_sessions()`, `session_manager`), variables in lower case without underscores.

For a larger skeleton (tests, backup code for an activity, a settings page) hand the brief to the
`moodle-scaffolder` agent. If a Moodle version difference matters, state the rule for 5.2 and for 5.3; the
`moodle-5-3-changes` skill lists what 5.3 changed.


---

### /moodle-new-theme

> Scaffold a Boost child theme for Moodle 5.2 and 5.3 (asks for the name and what it must change).

You will scaffold a Moodle theme that is a child of Boost.

User's input: <args>

If `<args>` is empty or missing a value, ask the user once:

1. **Theme name** — lowercase letters and digits, starting with a letter, no underscore. The component becomes
   `theme_<name>` and the directory `<name>`.
2. **What it must change** — for example: brand colour, typeface, corner radius, a banner or footer note, the
   login page, a changed page frame, settings an admin can edit. This decides which optional files are written.
3. **Supported Moodle versions** — default 5.2 and 5.3.
4. **Copyright holder** for the file headers.
5. **Moodle root**, if it cannot be found from the current directory (the directory that holds `public/` and
   `admin/cli/`).

If the user wants a theme with no parent, or a child of a theme other than Boost, read the `moodle-theme-development`
skill first: it says when each choice fits, and that a stand-alone theme is not a tested recipe.

Then:

1. Activate the `moodle-theme-boost-child` skill. Its default recipe is the content of every base file; take the
   files from it rather than from memory. Activate `moodle-theme-development` for the engine rules behind it.
2. Create `public/theme/<name>/` under the Moodle root. If the directory exists, stop and ask.
3. Write the base files, as in that recipe:
   - `version.php` — `$plugin->requires = 2026042000;` and `$plugin->supported = [502, 503];` for 5.2 and 5.3
     (`2026100500` and `[503, 503]` for 5.3 only), and `$plugin->dependencies` on `theme_boost` with Boost's build
     for the lowest supported version
   - `config.php` — `$THEME->parents = ['boost'];`, the SCSS closure and callbacks, and the Boost keys a child
     does not inherit
   - `lib.php` — the main SCSS function and the pre and extra SCSS callbacks, emitting only this theme's part
   - `lang/en/theme_<name>.php` — `pluginname`, `choosereadme`, `configtitle`, `privacy:metadata`, in
     alphabetical order
   - `classes/privacy/provider.php` — a null provider
   - `scss/<name>/pre.scss` and `scss/<name>/post.scss`
   - `pix/favicon.ico` (copy Boost's: it is not inherited) and `pix/icon.svg`
   - `LICENSE` — the full GPL v3 text, copied from `COPYING.txt` in the Moodle root
   - `README.md` and a changelog
4. Add only what the stated changes need, each from the skill that owns it:

   | The theme must change | Write | Skill |
   |---|---|---|
   | Colours, type, radius, spacing, component styles | Variables in `pre.scss`, rules in `post.scss` | `moodle-theme-scss` |
   | Something an admin can set | `settings.php`, the setting read and validated in `lib.php` | `moodle-theme-settings` |
   | Boost's brand colour, raw SCSS or background settings kept under the child | The mirrored settings and the `pluginfile` function | `moodle-theme-boost-child` (Boost settings reference) |
   | Extra HTML in the head, at the top of the body or before the footer | A hook callback with an active-theme guard | `moodle-theme-renderers-output` |
   | Navbar, footer or other template markup | A template override under `templates/<component>/` | `moodle-theme-layouts-templates` |
   | The page frame on some page types | An own layout file and template, each with its untouched twin | `moodle-theme-layouts-templates` |
   | What a renderer method returns, icons | `classes/output/core_renderer.php` extending Boost's class | `moodle-theme-renderers-output` |

   Prefer the smallest mechanism that does the job: SCSS before a template override, an override before a copied
   layout. A theme that copies Boost's layout template or navbar has a different upstream on 5.2 and 5.3; say so
   before writing one, and offer one branch per Moodle version instead.
5. Write `tests/lib_test.php`, the compile test from the `moodle-theme-testing-release` skill, asserting a
   selector that only this theme emits. If the theme has a feature worth a browser check, add a Behat feature
   tagged `@theme @theme_<name>` as that skill describes.
6. Rules that hold for every file written:
   - No `@import` into Bootstrap, Font Awesome or the design system; those paths differ between 5.2 and 5.3.
   - Surfaces and text colours from `--bs-*` custom properties; dark exceptions under `[data-bs-theme="dark"]`,
     never `prefers-color-scheme`.
   - The theme's own settings are read with `get_config('theme_<name>', ...)`.
   - GPL header and file docblock on every PHP file; the boilerplate comment on `.scss` and `.mustache` files too.
7. Print a tree of what was created, then the next steps, to run from the Moodle root:
   ```bash
   php admin/cli/upgrade.php --non-interactive
   php admin/cli/build_theme_css.php --themes=<name> --direction=ltr
   php admin/cli/purge_caches.php
   phpcs --standard=moodle public/theme/<name>
   php public/admin/tool/phpunit/cli/init.php
   vendor/bin/phpunit --testsuite theme_<name>_testsuite
   ```
   (`phpcs` with the `moodle` standard comes from `moodlehq/moodle-cs`; core's own Composer file does not
   install it. `moodle-plugin-ci phpcs --max-warnings 0` is the same check as CI runs.)
   and how to look at it: select the theme in the theme selector, or enable `allowthemechangeonurl` and open a
   page with `?theme=<name>`.
8. List what is left for the user: `pix/screenshot.png` (about 500 by 400 px; until it exists the selector shows
   Boost's), real colours and text, and anything marked TODO.

Offer `/moodle-theme-check` as a static check of the result.

Say plainly that the theme was written and not run. A theme whose SCSS does not compile still shows a working
page that looks like plain Boost, so the compile test or the `build_theme_css.php` command above (with developer
debugging on) is what shows whether it works.


---

### /moodle-privacy-audit

> Audit a Moodle plugin's privacy provider for completeness against its DB schema, preferences, files and external services.

You will audit the privacy provider of a Moodle plugin.

User's input: <args>

Activate the `moodle-privacy-gdpr` skill for context. Its rules decide each check below; do not judge from memory.

Steps:

1. Locate the plugin directory. If unclear, ask.
2. Read `db/install.xml` (or `db/upgrade.php` if no install.xml) — list every table and column.
3. Identify what the plugin holds about users:
   - Columns: `userid`, `user_id`, `createdby`, `modifiedby`, `usermodified`, `relateduserid`
   - Free-text fields a user authored (`content`, `comment`, `description`, `note`)
   - Files in the plugin's file areas (item ids that point at the plugin's rows)
   - Identifiers from external systems linked to a user
   - User preferences: `grep -rnE "set_user_preference|user_preferences\b|setUserPreference" --include='*.php' --include='*.js' .`
     (also the `get_user_preferences` callback in `lib.php`)
   - Data sent to another system: `grep -rnE "new \\\\?curl\b|curl_init|->post\(|->get\(" --include='*.php' .`,
     then read what each request carries
4. Read `classes/privacy/provider.php`. If it does not exist, that is the first finding: every plugin needs a
   provider, and the plugin's own CI run does not report a missing one.
5. For each user-identifying column, check:
   - It is declared in `get_metadata()` via `add_database_table` with a lang string
   - The column has an entry in the plugin's lang file of the form `privacy:metadata:<table>:<column>`
   - `get_contexts_for_userid` returns contexts where the user has data
   - `get_users_in_context` returns users who have data in a given context
   - `export_user_data` exports the data per context
   - `delete_data_for_user` and `delete_data_for_users` delete only the named users' rows and files
   - `delete_data_for_all_users_in_context` checks the context level, and for a module that the cm is its own
   - The table names the request methods query are the current ones (after a rename, grep
     `classes/privacy/` for the old name)
6. Check for subsystem usage:
   - If plugin attaches files via the Moodle Files API, `add_subsystem_link('core_files', ...)` must be present,
     and the provider itself must export and delete the files: the link only declares them
   - Same for `core_comment`, `core_rating`, `core_tag` if used
7. Preferences and external services:
   - Every preference the plugin sets is declared with `add_user_preference()` and exported in
     `export_user_preferences()` (interface `user_preference_provider`)
   - Every destination that receives personal data is declared with `add_external_location_link()`
8. If plugin stores no user data, check it implements `null_provider` correctly (`get_reason` returns lang string key, `privacy:metadata` lang string defined). A `null_provider` on a plugin that sets a preference or sends
   personal data out is a finding.
9. Look for `tests/privacy/provider_test.php` and whether it exercises the request methods on generated rows.
10. Output findings, each with `file:line`:
   - GREEN: present and correct
   - YELLOW: present but incomplete / missing lang strings
   - RED: missing entirely

State what was not checked: nothing was run, so the export and the deletion were read, not observed, and core's
compliance test (`public/privacy/tests/privacy/provider_test.php`) was not run for the plugin.

Propose a fixed `provider.php` and the missing lang strings if there are issues. Don't write the changes without user confirmation if the plugin is non-trivial.


---

### /moodle-security-review

> Run the Moodle security checklist on a file, directory, or entire plugin.

You will perform a Moodle-specific security review.

User's input: <args>

Activate the `moodle-security-audit` skill for context: it holds the rule, the reason and the fix behind each
line below. For a review before a release or a Plugins directory submission, also walk the defect classes of the
`moodle-release-preflight` skill, which this checklist does not repeat.

If `<args>` is empty, ask for a file or plugin path.

Audit each PHP file in scope against this checklist. Report findings as:

```
[FILE]:[LINE] [SEVERITY] [CATEGORY] — [issue]
                                         FIX: [actionable fix]
```

Severities: `CRITICAL` (exploitable now), `HIGH` (privilege escalation / data leak), `MEDIUM` (defense in depth), `LOW` (style / hardening).

## Checklist

For every entry script (file with `require('config.php')` or similar):
1. `require_login()` present and called early
2. `require_capability()` against the **object's** context (not arbitrary system context), derived from the id in
   the URL; every other id the request submits is re-checked against that object. `require_login()` alone is not
   authorisation
3. `require_sesskey()` on every state-changing request (POST or mutating GET)
4. All input via `required_param`/`optional_param` with appropriate `PARAM_*` type — flag any `$_GET`/`$_POST`/`$_REQUEST` usage

For every DB call:
5. Uses `$DB->...` — flag any `mysqli_*`, `PDO`, `mysql_*`
6. Placeholders (`?` / `:name`) — flag string concatenation in SQL
7. `LIKE` patterns use `$DB->sql_like()` + `sql_like_escape()`
8. `IN (...)` uses `$DB->get_in_or_equal()`

For every output:
9. User text rendered via `s()`, `format_string()`, `format_text()` — flag direct `echo $var`
10. `format_string`/`format_text` is called with a `context`
11. Mustache `{{{var}}}` raw output is justified (text already passed through `format_text`). The other sinks that
    print HTML get escaped values too: `html_writer` tag content, formslib labels and option texts, modal titles,
    notifications, `redirect()` messages, `innerHTML` in `amd/src`. Trace what feeds a sink before reporting it

For file APIs:
12. `pluginfile.php` callback re-checks capability inside callback
13. Files are served via `\file_storage` + `send_stored_file`, never raw `$CFG->dataroot`; user uploads are
    force-downloaded unless the media type was validated
14. Uploads use `file_save_draft_area_files` with `maxfiles`, `maxbytes`, `accepted_types`

For HTTP / external:
15. Uses `\curl` wrapper, not raw `curl_exec()` / `file_get_contents($url)`
16. Open redirects: a redirect target from user input is read with `PARAM_LOCALURL`, not `PARAM_URL` or the
    `Referer` header

For secrets:
17. No tokens / API keys committed in source — use `set_config`/`get_config`

For dangerous PHP:
18. No `eval()`, and no `unserialize()` on user input or restored data without `['allowed_classes' => false]`
19. `print_error` is replaced with `throw new \moodle_exception()`

For sessions:
20. `\core\session\manager::write_close()` called early on AJAX endpoints that don't write session

For web services (`classes/external/`):
21. `execute()` calls `validate_parameters()`, then `validate_context()`, then `require_capability()`. The
    `capabilities` key in `db/services.php` enforces nothing (`moodle-web-services`)

After audit:
- Print summary: `N CRITICAL, N HIGH, N MEDIUM, N LOW`
- Say what was checked and how: this is a read of the code, nothing was run, and a line reported as clean names
  the grep or the files that were read
- Offer to apply fixes one-by-one or as a single patch (ask before writing)
- For unresolved CRITICAL findings, recommend not deploying until fixed


---

### /moodle-string-check

> Find hard-coded English strings that should use get_string() / Mustache {{#str}}.

You will find untranslated user-facing strings in a Moodle plugin.

User's input: <args>

If empty, ask for a plugin path.

Steps:

1. Walk the plugin directory. Skip `amd/build/`, `tests/`, vendored libraries and `*.upstream` files; read
   JavaScript in `amd/src/`.
2. Read `lang/en/<component>.php` (an activity module: `lang/en/<name>.php`) — list defined keys.
3. For each `.php`, `.mustache`, and `.js` file, find user-facing strings that are not loaded via `get_string`/`{{#str}}`/`core/str`:

   PHP heuristics:
   - String literals passed to:
     - `$mform->addElement('<type>', '<name>', '<literal>')` — the third argument is the label; also option
       texts of selects and radio buttons
     - `new admin_setting_configtext(..., '<literal>', '<literal>')` — title + description
     - `new \html_table_cell('<literal>')`, `html_writer::tag('p', '<literal>')`
     - `\core\notification::success('<literal>')`, `\core\notification::error('<literal>')`
     - `redirect($url, '<literal>')`
     - `throw new moodle_exception('<literal>')` — should be a string KEY, not a sentence
   - Direct `echo` of literals over 3 words

   Mustache heuristics:
   - Visible text not wrapped in `{{#str}}KEY, COMPONENT{{/str}}`
   - Aria-labels / titles with literal text

   JS heuristics:
   - String literals passed to `Notification.alert()`, `Toast.add()`, error messages thrown
   - Any UI-visible literal not loaded via `core/str` (`getString`, `getStrings`)

4. Skip strings that are clearly identifiers (selectors, classes, route keys, lang keys themselves).

5. Check the other direction too, because a missing key prints `[[key]]` or throws on the live page while every
   lint passes:
   - Every key the plugin's code asks for from its own component (`get_string('<key>', '<component>')`,
     `{{#str}}<key>, <component>{{/str}}`, `new lang_string(...)`, `getString('<key>', '<component>')`) is
     defined in the lang file
   - Every string core asks for by convention exists: `pluginname`, one per capability (`<name>:<cap>`), the
     privacy strings, and the others listed in the `moodle-release-preflight` skill for the plugin's type
   - Keys in the lang file are in alphabetical order (a coding-style warning, which fails a CI run that allows none)

6. Output findings as:

```
[FILE]:[LINE] "<literal>"
   → propose key: <lowercase key, no plugin prefix; a colon only in capability strings>
   → in lang/en/<component>.php:
       $string['<key>'] = '<literal>';
   → replacement:
       <PHP>: get_string('<key>', '<component>')
       <Mustache>: {{#str}}<key>, <component>{{/str}}
       <JS>: await getString('<key>', '<component>')
```

7. Optionally, propose adding `lang/en/<component>.php` keys in a single edit and substituting the literals.
   A new string shows only after a cache purge or a version bump, and a placeholder (`{$a}`) is passed as the
   third argument of `get_string()`, never concatenated.

Reference the `moodle-plugin-development` skill for lang string conventions.


---

### /moodle-theme-check

> Static check of a Moodle theme directory against the theme skills' common mistakes; reports file:line for each finding and states what was not checked.

You will check a Moodle theme by reading its files. Nothing is compiled, installed or loaded in a browser, and no
file is changed.

User's input: <args>

## Procedure

1. Resolve the theme directory (default: cwd). It must hold `config.php` and `version.php`; if not, say so and
   stop. Read `version.php` for `$plugin->component` (`theme_<name>`), `$plugin->requires`, `$plugin->supported`
   and `$plugin->dependencies`, and `config.php` for `$THEME->parents`.
2. Note the facts that decide which checks apply:
   - **Versions.** Does `$plugin->supported` include `502`, `503` or both? Checks marked 5.2 or 5.3 apply only
     when that branch is supported.
   - **Parents.** Is `boost` in `$THEME->parents`? The Boost child checks apply only then. For a theme with no
     parents, say that the stand-alone path is not a tested recipe (`moodle-theme-development`) and run the
     checks that do not depend on Boost.
   - **Moodle source.** If a Moodle root is reachable (the directory that holds `public/` and `admin/cli/`),
     read its `public/version.php` for the branch. Checks that compare with core need it; without it they go
     under "Not checked".
3. Activate `moodle-theme-development`. Activate each other theme skill when its group below is reached: the
   rule, its symptom and its fix are in the skill's "Common mistakes" table, and this command only says what to
   look for. Do not judge a check from memory.
4. Run the groups in order. For each check record one of: a finding with `file:line`, a pass that names what
   was read, or N/A with the command that shows it does not apply.

## A. `config.php` and `version.php`

Skills: `moodle-theme-development`, `moodle-theme-boost-child`. Start with `grep -n '\$THEME->' config.php`.

- `$THEME->name` equals the directory name.
- `$THEME->parents` is an array; every parent is in `$plugin->dependencies`; a theme with two levels of parents
  lists every ancestor, nearest first. **5.3+:** `classic` as a parent, which core no longer ships.
- In a child, the keys that are not inherited are restated: `rendererfactory`, `usefallback`, `requiredblocks`,
  `addblockposition`, `haseditswitch`, `usescourseindex`, `activityheaderconfig`, `yuicssmodules`.
- Every key is in core's whitelist (the key reference of `moodle-theme-development`). Names that are silently
  dropped include `renderfactory`, `editorsheets`, `undeletableblocktypes`, `enable_dock`.
- `$THEME->editor_scss` names a file the theme ships.
- `$THEME->scss` in a child is a closure, not a file name; a theme with files in `scss/` sets the key.
- No `styles.php` in the theme root.
- `$plugin->supported` is a two-number pair and `$plugin->requires` is not below its lowest branch;
  `version.php` contains no `require`.
- `$THEME->hidefromselector = true` in a theme that has Behat features.

## B. SCSS

Skill: `moodle-theme-scss` (its version notes list the variables and partials that differ). Search `scss/` and
the SCSS strings built in `lib.php`.

```bash
grep -rnE '@import' scss/ lib.php
grep -rnE '(darken|lighten|mix|tint-color|shade-color|rgba)\([^;]*\$(state-|dialogue-|card-bg|card-border-color)' scss/
grep -rnE 'prefers-color-scheme|\[\[setting:|@include +dark-mode|dark-readable\(' scss/ lib.php
grep -rnE '^\s*:root\s*\{' scss/
grep -rnE 'var\(--mds-[a-z0-9-]+\)' scss/
grep -rnE 'background(-color)?:\s*(#fff|#ffffff|white)\b' scss/
```

- **Imports.** A path into `bootstrap/`, `fontawesome/` or the design system's folders resolves on 5.2 only; a
  5.3-only partial or a path into `lib/bundles` fails on 5.2. Report each against the versions the theme
  supports.
- **File names** `scss/moodle.scss`, `scss/bootstrap.scss`, `scss/fontawesome.scss`, `scss/design-system.scss`,
  and a shipped copy of Boost's preset.
- **Colour functions on variables that are `var()` strings on 5.3.** The grep above covers the most common
  names; the full list is in the skill's 5.3 version notes.
- **Pre-SCSS** (the pre callback and any file placed before Boost's preset) that uses `$gray-*`, `$mds-*`,
  `tint-color()`, `shade-color()` or `@include`.
- **Dark mode.** `prefers-color-scheme`; a bare `:root` block that sets `--bs-*` or `--mds-*`; a literal
  background behind inherited text (each grep hit is a candidate: read the rule before reporting it).
  **5.2 only:** `@include dark-mode`, `dark-readable()` and `var(--mds-...)` with no fallback do not work there.
- **`[[setting:...]]`** placeholders, which core does not replace.
- **Doubled callbacks.** A pre or extra SCSS callback in a Boost child that emits `brandcolor`, `scsspre`, the
  `scss` setting or the background images: `grep -nE "brandcolor|scsspre|backgroundimage|settings->scss" lib.php`.
- **Unvalidated values.** A setting value written into SCSS with no pattern check before it. Trace each
  `get_config()` or `$theme->settings->` read in the SCSS callbacks to where it is emitted.
- **RTL directives** written as `//` comments or placed after the last declaration.

## C. PHP output: hooks, callbacks, renderers, icons

Skill: `moodle-theme-renderers-output`.

- Each callback in `db/hooks.php`, and each `lib.php` callback that core calls for every plugin, starts with a
  guard on the current theme's name and parents. List the callbacks, then read each one.
- Renderer classes: `grep -rnE 'extends +\\?core_renderer\b' classes/` (a Boost child extends Boost's class);
  class name, namespace and file name match the lookup rules; no core method body copied.
- `grep -rnE '(empty|isset)\(\$(this->page|PAGE)->' classes/ layout/ lib.php`: always "not set".
- A theme renderer method used from the `maintenance` layout.
- `theme_<name>_get_fontawesome_icon_map()` returning `core:` keys, or a mapped key with no SVG file.
- `$theme->settings->` or `$PAGE->theme->settings->` used for the theme's own value in code a child may run.
- **5.3+:** a renderer that extends `block_timeline\output\renderer`.

## D. Layouts and templates

Skill: `moodle-theme-layouts-templates`.

- Each `$THEME->layouts` entry is whole: `file`, `regions`, `defaultregion` when regions is not empty, and the
  options restated. Option keys that nothing reads.
- Each file copied from core or Boost has an untouched `.upstream` twin and a header that names the source and
  the Moodle version: `find . -name '*.upstream'`, then compare with the list of copied files. With a Moodle
  root, `diff` each twin against the same file there and report a difference as "upstream changed".
- A copied `drawers.mustache` or `navbar.mustache` in a theme that supports both versions: the menu partial is
  chosen by the `reactprops` switch, and both drawer blocks are filled.
- A layout template of the theme's own prints every required `output.*` call.
- Template overrides: run `/moodle-mustache-lint` on `templates/`, or apply its theme override checks here.

## E. Settings

Skill: `moodle-theme-settings`. Skip with N/A when there is no `settings.php`.

- The page replaces `$settings` with one named `themesetting<name>`, inside `if ($ADMIN->fulltree)`.
- A tab is added after its settings; `hide_if()` is called on the outer page.
- Every setting read in an SCSS callback, and every file setting, has
  `set_updatedcallback('theme_reset_all_caches')`. List the names read in `lib.php`, then find each in
  `settings.php`.
- `admin_setting_configstoredfile` uses item id 0; `theme_<name>_pluginfile()` exists and checks the same file
  areas; `setting_file_url()` names the same area.
- Setting names use the slash form `theme_<name>/<setting>`.
- A user preference set by the theme is declared in the privacy provider.
- Whether a setting added since the last release came with a version bump can be judged only from the history:
  report it as not checked unless `git log` is available and was read.

## F. Tests and package

Skills: `moodle-theme-testing-release`, `moodle-plugin-release`.

- A PHPUnit test calls `get_css_content()` and asserts a selector that only this theme emits;
  `assertNotEmpty($css)` alone passes on the fallback CSS.
- Features carry `@theme @theme_<name>`, do not set the theme, and include at least one `@javascript` scenario:
  `grep -rnE '^\s*@|theme' tests/behat/*.feature`.
- Files present: `LICENSE` (full text), `pix/screenshot.png` or `.jpg`, `pix/favicon.ico`, `pix/icon.svg`,
  `classes/privacy/provider.php`.
- Strings present in `lang/en/theme_<name>.php`: `pluginname`, `choosereadme`, `configtitle`,
  `privacy:metadata` or the preference strings, and `region-<name>` for a region no parent names.
- `thirdpartylibs.xml` when `fonts/` or a vendored library is shipped.
- The boilerplate and `@copyright` on `.scss` and `.mustache` files, with the original `@copyright` line kept in
  copied files.
- Bootstrap 4 class names in templates and `amd/src`:
  `grep -rnE '\b(sr-only|ml-[0-5]|mr-[0-5]|float-(left|right)|font-weight-bold|badge-(primary|secondary)|custom-select)\b|data-toggle=' templates/ amd/src/`.

## Output

```markdown
# Theme check: theme_<name>

## Summary
- Parents: <list> | Supports: <5.2, 5.3> | Moodle source compared: <version, or none>
- Errors: N | Warnings: N | Not applicable: N | Not checked: N

## Errors (breaks on a supported version, or blocks approval)
- scss/<name>/post.scss:14 — `@import "bootstrap/functions"` — not found on 5.3, the theme falls back to stock Boost — FIX: <action> — see `moodle-theme-scss`

## Warnings
- config.php:31 — ...

## Not applicable
- Settings — no `settings.php` (`ls settings.php`: no such file)

## Not checked
- The SCSS was not compiled: run the theme's compile test, or `php admin/cli/build_theme_css.php --themes=<name> --direction=ltr` from the Moodle root with developer debugging on
- No page was loaded: template and renderer overrides, the cascade, dark mode, RTL and phone width were not seen
- PHPUnit, Behat, stylelint, the Mustache lint and phpcs were not run
- The release ZIP was not built or listed
- <any check skipped because the Moodle source for 5.2 or 5.3 was not available>

## Suggested next steps
1. ...
```

## Rules

- Never modify files. Report only.
- Every finding carries a `file:line`, or the command and the output that shows it. A grep hit is a candidate,
  not a finding: read the lines around it first.
- A check with no hits is reported as a pass only with the command that was run; an empty result from a command
  that searched the wrong directory proves nothing, so confirm the path exists.
- Say how sure each finding is: read in the theme's files, or compared with the Moodle source of a named version.
- Always print the "Not checked" section. A static check cannot show that the theme compiles or that a rule
  applies on the page.


---
