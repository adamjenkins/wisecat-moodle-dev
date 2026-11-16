# Moodle 5.3: new APIs by area

Read this when you want to use an API added in 5.3 (React rendering, attribute DI, auth and password services,
personal access tokens, the OAuth2 server, route scopes, the email hook, page footer controls, soft task retries,
report builder or course format additions), or need to know whether one also exists on 5.2.

Everything here is 5.3 only unless the entry says "also on the 5.2 branch". A plugin whose range includes 5.2
guards each use with `class_exists()` / `method_exists()`. Sources: the `## 5.3` section of the 5.3.0 root
`UPGRADING.md` and the cited files of the 5.3.0 tree, read, not run. Entries marked "not in the notes" were found
in the code or the tracker only.

## Output and React

### `html_writer::react_component()` (MDL-89296)

`react_component(string $modulename, array|string|\stdClass|\JsonSerializable $props): string` returns the mount
point and JSON-encodes the props itself; pass the array, not a JSON string.

```php
echo \core\output\html_writer::react_component('@moodle/lms/local_example/Widget', ['count' => 3]);
```

### `\core\output\react_component_renderable` (MDL-89296)

A renderable implementing it is rendered by `$OUTPUT->render()` as a React component instead of a template.
`get_react_component_name()` returns the path inside the `lms` package without the `@moodle/lms/` prefix (the
renderer adds it), unlike `html_writer::react_component()`, which takes the full specifier.

```php
final class widget implements \core\output\react_component_renderable {
    public function get_react_component_name(): string {
        return 'local_example/Widget';
    }
    public function get_react_component_props(\core\output\renderer_base $renderer): \stdClass {
        return (object) ['count' => 3];
    }
}
```

### AMD `core/import` and `core/component` (MDL-88505)

`core/import`'s default export is a native dynamic `import()` that Babel does not rewrite, for ESM specifiers
resolved by the import map. `core/component` exports `appendToDom(moduleName, properties, element)` and
`prependToDom(...)`, which create a `data-react-component` / `data-react-props` container for auto-initialisation;
properties must be JSON-serialisable.

```js
import nativeImport from 'core/import';
const mod = await nativeImport('@moodle/lms/mod_book/viewer');
```

### `scripts/swizzle.mjs` (MDL-88509)

A Node CLI at the Moodle root. Without arguments it starts a wizard that ejects or wraps a core React component into
a theme. `manifest generate` aggregates each component's `js/esm/src/swizzle.json` and adds a risky/risky entry for
undeclared components; `manifest set` sets the safety level (`safe`, `risky`, `prohibited`) for eject and wrap. A
plugin that ships React components declares its levels. The CLI skips everything under `public/theme/`. Theme use:
`moodle-theme-renderers-output`.

```sh
./scripts/swizzle.mjs manifest generate
./scripts/swizzle.mjs manifest set
```

### Page methods

| Method | Purpose | MDL |
|---|---|---|
| `$PAGE->set_show_navigation_footer(bool)`, `should_show_navigation_footer()` | Suppress the sticky previous/next footer on a page (default true) | MDL-87575 |
| `$PAGE->set_has_sticky_footer(bool)`, `has_sticky_footer()` | Record that a sticky footer was rendered so a second is not | MDL-87302 |
| `$PAGE->set_supplementary_content(?action_link)`, `get_supplementary_content()` | A secondary link in the sticky footer | MDL-88601 |

### Menus and images

- `core\output\action_menu\subpanel` takes a fifth optional `?moodle_url $url = null`, so the item links somewhere
  as well as opening its subpanel; `core\output\submenu` is a renderable list usable as a subpanel for multi-level
  menus (MDL-88312).
- `core/imagedetails/modal` `getImageDetails(file)` shows an image-details dialogue and resolves to `{alt,
  presentation, width, height}` or `null` on cancel (0 width/height keeps the original size). Plugins with their own
  image upload or embed UI use it and store the alt text or decorative flag (MDL-89214).

```js
import {getImageDetails} from 'core/imagedetails/modal';
const details = await getImageDetails(file);
```

- `flexible_table::set_columnheadersattributes(['col' => ['class' => 'visually-hidden']])` (MDL-89384; also on the
  5.2 branch in a 5.2.2+ build, so guard with `method_exists()` for earlier 5.2 releases).

## Dependency injection, auth, sessions, exceptions

### Attribute injection (MDL-89528)

The container honours `#[\DI\Attribute\Inject]` on properties of objects obtained with `\core\di::get()` (container
entry) or `\core\di::make()` (new instance each call). Recommended for routed controllers.

```php
class example_service {
    #[\DI\Attribute\Inject]
    public \core\formatting $formatter;
}
$service = \core\di::get(example_service::class);
```

### Auth and password services (MDL-88580)

The global functions still exist and are not deprecated; they delegate to DI services with instance methods:

| Function | Service method |
|---|---|
| `validate_internal_user_password()`, `hash_internal_user_password()`, `update_internal_user_password()`, `password_is_legacy_hash()`, `get_password_peppers()`, `exceeds_password_length()` | `\core\authentication\password`: `validate()`, `hash()`, `update()`, `is_legacy_hash()`, `get_peppers()`, `exceeds_max_length()` |
| `exists_auth_plugin()`, `is_enabled_auth()`, `get_auth_plugin()`, `get_enabled_auth_plugins()`, `is_internal_auth()`, `is_restored_user()` | `\core\authentication`: `plugin_exists()`, `is_enabled()`, `get_plugin()`, `get_enabled_plugins()`, `is_internal()`, `is_restored_user()` |

```php
$auth = \core\di::get(\core\authentication::class)->get_plugin('manual');
$ok = \core\di::get(\core\authentication\password::class)->validate($user, $password);
```

`\core_auth\validate_user` centralises login checks: `validate_before_web_login()`, `validate_before_external_login()`,
`validate_before_token_login()`, and single checks (`validate_maintenance_mode_access()`, `validate_not_deleted()`,
`validate_is_confirmed()`, `validate_is_not_suspended()`, `validate_auth_not_disabled()`,
`validate_credentials_not_expired()`, `validate_user_is_not_guest_user()`), each taking `\stdClass $user` and
throwing typed exceptions from `\core_auth\exception\`.

### Session cookie support (MDL-87174)

`\core\session\manager::supports_cookies()`, `set_cookies_supported(bool)`, `set_initial_cookie_support()` replace
checks of `NO_MOODLE_COOKIES` (which still sets the initial value). To start a session later in a no-cookie script:

```php
if (!\core\session\manager::supports_cookies()) {
    \core\session\manager::set_cookies_supported(true);
    \core\session\manager::start();
}
```

Routed controllers pass `cookies: true|false` in the route attribute, which is `\core\router\route` (the notes show
`\core\router\attributes\route`, which does not exist).

### Exceptions

`moodle_exception` takes a sixth argument `?\Throwable $previous = null`; subclasses that override the constructor
should forward it (MDL-88579).

```php
throw new \moodle_exception('errorwhilesaving', 'local_example', previous: $e);
```

## REST API, tokens, OAuth2

### Personal access tokens (MDL-87706)

`\core\api\token_manager` (get it from `\core\di::get()`; its constructor takes repositories and a clock) has
`issue_token(string $name, int $userid, array $scopes, ?string $description, int $expirytime): string`, which mints
a token with a `pat_` prefix. The longest lifetime is one year (`MAX_LIFETIME`); the form offers 7, 30, 60, 90 and
365 days and preselects 30. Users manage tokens at `/user/personalaccesstokens.php`, which requires the new system
capability `moodle/api:createtoken` (`RISK_SPAM | RISK_PERSONAL`; allowed by default for the authenticated user and
manager archetypes, `public/lib/db/access.php`). Issue tokens through `token_manager`, not the repository classes.

### OAuth2 authorization server (MDL-89181)

`\core\oauth2\server\client_manager` manages server clients (`create_client()`, `get_client()`,
`get_client_by_id()`, `update_client()`, `disable_client()`, `reactivate_client()`, `delete_client()`), secrets
(`create_secret()`, `get_secrets()`, `revoke_secret()`) and redirect URIs (`get_redirect_uris()`,
`add_redirect_uri()`, `remove_redirect_uri()`, `validate_redirect_uri()`, `validate_redirect_uri_format()`). It
needs the Composer package `league/oauth2-server`.

It is an authorization server for Moodle's own REST API, not an OpenID Connect provider: there is no `id_token`,
userinfo endpoint, discovery document or JWKS in `public/lib/classes/oauth2/server/` (read in 5.3.0). A plugin that
needs Moodle as an SSO identity provider for another system still needs an OIDC provider plugin. An OIDC relying
party rejects an `id_token` that lacks the `nonce` it sent while the token exchange itself returns 200, so such a
failure shows only in the relying party's log.

### Route scopes (not in the notes; MDL-89089, MDL-89710)

Scope classes extend `\core\router\scope\abstract_scope`, carry `identifier_attribute`, `summary_attribute` and
`description_attribute`, and live in `classes/route/scope/` (auto-discovered, cached). Route methods declare
required scopes with repeatable `#[\core\router\scope\scopeset(...)]` (AND within a set, OR across sets) or opt out
with `#[\core\router\scope\unscoped_resource]`. A route with neither attribute has no scope restriction at runtime:
declaring scopes is enforced by tests (`route_testcase::assert_route_is_scoped()`, `assert_route_is_unscoped()`,
`assert_route_required_scopes()`), not by the router. Name scope strings like core's fixed `core_course` ones
(`course_content_read_scope_summary`, `..._desc`).

```php
namespace local_example\route\scope;

use core\router\scope\abstract_scope;
use core\router\scope\description_attribute;
use core\router\scope\identifier_attribute;
use core\router\scope\summary_attribute;

#[identifier_attribute('read')]
#[summary_attribute('example_read_scope_summary', 'local_example')]
#[description_attribute('example_read_scope_desc', 'local_example')]
class read extends abstract_scope {
}
```

### Web services

- `'allowcorsrequests' => true` in `db/services.php` (default false): `lib/ajax/service.php` sends
  `Access-Control-Allow-Origin: *` only for no-login AJAX requests where every function in the batch has it and
  `'loginrequired' => false`. Use it only for functions safe to call from any origin (MDL-87150).

```php
'local_example_get_public_info' => [
    'classname' => \local_example\external\get_public_info::class,
    'type' => 'read',
    'ajax' => true,
    'loginrequired' => false,
    'allowcorsrequests' => true,
],
```

- New functions: `mod_assign_save_overrides`, `mod_assign_get_overrides`, `mod_assign_delete_overrides`
  (MDL-86513); `mod_forum_set_read_state` (MDL-87887); `mod_quiz_get_users_in_report`, which also returns
  `extrafieldsdisplay` labels (MDL-81096, MDL-89765). `mod_assign_get_submission_status` returns an optional
  `feedback.markerfeedback` array for marking allocation (MDL-89346). `gradereport_user_get_grade_items` returns an
  optional `parentcategoryid` (MDL-64304).
- Course-module services build from `core_course\external\helper_for_get_mods_by_courses::
  standard_coursemodule_elements_returns()` and `standard_coursemodule_element_values()`, so
  `core_course_get_course_module(_by_instance)` and several module services return extra fields (`lang` among
  them). Activity plugins' own `get_*_by_courses` services should use the helper (MDL-87241; exact field diff per
  service not checked).
- `\tool_mobile\api::get_subscription_information(..., &$errormessage = '')` receives an error description
  (MDL-88458). New setting `tool_mobile/enabledeeplinkautologin` (default off) gates app auto-login from deep links
  that carry `token`/`privatetoken`; integrations generating such links tell admins to enable it (MDL-88924, not in
  the notes).

### Composer status (not in the notes; MDL-88576)

`\core\composer` (via DI): `is_installed()`, `get_status()`, `get_package_status(string $package)` (`->installed`).
Core's `composer.json` requires packages that are not bundled; features that need one degrade with a warning until
`composer install` has run at the Moodle root.

```php
$composer = \core\di::get(\core\composer::class);
if (!$composer->get_package_status('league/oauth2-server')->installed) {
    return;
}
```

## Email

`email_to_user()` dispatches `\core\hook\email\before_email_to_user`; callbacks change `$hook->email` fields, add
headers with `add_additional_header()`, or block the send with `add_block_reason()` (MDL-69724). Registration and
a dual-version callback: `moodle-hooks-api`.

## Tasks

- `adhoc_task::set_soft_retry_delay(?int $delay = null)`, `get_soft_retry_delay()`, `is_adhoc_task_delayed()`:
  called inside `execute()`, reschedules without counting as a failure (null: exponential backoff; positive:
  seconds; `<= 0` throws). Attempts are still decremented, and `manager::adhoc_task_delayed()` caps the backoff at
  24 hours based on the remaining attempts. Also on the 5.2 branch from 5.2.2 (MDL-79763).

```php
public function execute() {
    if (!$this->remote_ready()) {
        $this->set_soft_retry_delay(300);
        return;
    }
    // ...
}
```

- `\core\task\manager::set_scheduled_task_nextruntime()` returns false (and changes nothing) when the lock cannot be
  taken or the task is running, true once `nextruntime` is set; callers check it (MDL-89200).
- `queue_adhoc_task()` returns the task id (the behaviour change is in `SKILL.md`).

## Course formats and courses

- `base::uses_linear_navigation()` (static, false by default) opts a format into previous/next navigation
  (MDL-87302); the site setting `format_<name>/enablelinearnav` controls it.
- Format option definitions accept `inline_help`: the edit form shows the help text and docs link under the setting
  as static text, independent of `help`. The notes call it a flag; the code passes the value to
  `get_formatted_help_string()` as a string identifier, so give it a string id with a matching `<id>_help` string
  (MDL-88669; intended usage not confirmed).
- `core_course\route\controller\course_navigation` helpers: `get_all_section_cms(modinfo, section_info)`,
  `get_adjacent_section(modinfo, section_info, 'next'|'previous')`, `is_first_navigable()`, `is_last_navigable()`
  (both throw `coding_exception` if the cm is not in the list), `get_section(cm_info)` (MDL-88604).
- Activity chooser items can be disabled with a reason (MDL-87373).
- `\core_user::get_users_search_sql()` gains `bool $allowcustom = false` (custom profile identity fields) and
  `array $custommappings = []` (MDL-81096).

## Report builder

| Addition | MDL |
|---|---|
| `week`, `month`, `year` aggregations for `TYPE_TIMESTAMP`, extending the new abstract `datebase` (which `date` now extends); custom date aggregations extend `datebase` | MDL-84635 |
| `prepend_join()`, `prepend_joins()`; the base entity prepends its joins to every column, filter and condition it adds, so `->add_joins($this->get_joins())` boilerplate can go | MDL-87405 |
| `column::add_header_attributes(array $attributes): self` (also on the 5.2 branch in a 5.2.2+ build) | MDL-89384 |
| `set_main_table_sql(string $tablesql, string $tablealias)` for complex SQL as the main table | MDL-88397 |
| `column::add_fields(string\|array $sql, array $params = [])` accepts an array (on the column class, not the report) | MDL-89004 |

## Grades, AI, questions, activities

- `grade_outcome::add_outcome_to_module()`, `remove_outcome_from_module()`, `get_outcomes_in_module()`,
  `get_used_outcomes_in_course()`: outcomes linked to course modules without a scale; do not assume an outcome has a
  `scaleid` (MDL-88881).
- `ai_action_register.courseid` (int, default 0) filled at log time: `-1` means the context is not in a course,
  `0` an older row not yet backfilled. New course report `report_aiusage` with `report/aiusage:view` and
  `report/aiusage:viewown` (MDL-80893).
- `aiprovider_gemini`: `gemini-3.1-flash-image` is the default image model; endpoints ending `:generateContent` use
  the Gemini protocol, others Imagen `:predict`, decided by URL (MDL-89431).
- `\core_question\local\bank\bulk_action_base::get_action_icon()` returns the pix identifier for the bulk action
  button; the base returns `i/empty`, so a qbank plugin with a bulk action overrides it (the notes give a wrong
  `\core\question\` namespace; core example `qbank_bulkmove\bulk_move_action` returns `i/move_2d`) (MDL-73051).
- `mod_assign`: `\mod_assign\override_manager` (MDL-86513); `calculate_penalised_grade(stdClass $grade,
  ?\grade_grade $usergraderecord = null): array` applies grade-item scaling itself, so remove your own (MDL-88407);
  `get_grading_batch_operation_details()` may return `confirmationyes` (also on the 5.2 branch, MDL-88688).
- `mod_quiz`: `report_base::print_action_bar()`, `setup_report_data()`, `has_permission()` and the JS
  `mod_quiz/searchwidget/user` (MDL-81096); `quiz.duedate` (default 0) and `quiz_overrides.duedate` (null means the
  quiz value), which copy, backup and report code must carry (MDL-82521).
- `mod_forum`: `discussion::get_discussion_navigation_buttons()` (MDL-88602).
- `badge_message_from_template()` takes an optional third `?stdClass $user` to fill user name placeholders
  (MDL-87859).
- `tiny_premium` supports the Premium `markdown` plugin with `tiny/premium:usemarkdown` (MDL-88547);
  `tiny_recordrtc` always offers a download, offers one when a recording is too large to upload, and writes the
  duration metadata when recording stops (MDL-88603).
- `assignfeedback_editpdf`: Ghostscript's `%d` page placeholder is now inside the quoted output filename, fixing
  multi-page conversion on Windows (MDL-76966).

## Site administration

- `core_admin_renderer::warning_with_label()` (protected) prefixes a notification with a bold severity label
  (MDL-89290).
- `$CFG->disablenotificationctas` hides individual "From Moodle" cards on the notifications page (MDL-89290).
- The available-updates check sends an optional `siteidentifier` (md5 of the registration secret, only when
  registered) and `countrycode` (MDL-89513); a daily `core\task\registration_reporting_check_task` notifies admins
  when hub reporting pauses (MDL-89463).
- Site administration links to the site content bank, site participants and user notes; the profile's
  Miscellaneous section links to Tags (MDL-89309, MDL-88655, MDL-88687; not in the notes, not checked in detail).
