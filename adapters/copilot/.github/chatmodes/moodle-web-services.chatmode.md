---
description: Use when adding, changing, calling or debugging a Moodle external function or web service - db/services.php, classes/external/, execute_parameters/execute_returns, validate_parameters, validate_context, 'ajax' => true for core/ajax, 'loginrequired' => false, readonlysession, REST/SOAP tokens, login/token.php, webservice/upload.php, pluginfile URLs for token clients, or errors such as "Invalid parameter value detected", "Invalid response value detected", servicenotavailable, servicerequireslogin, accessexception, a function missing from external_functions. Skip when writing the JavaScript caller (moodle-amd-javascript) or the Moodle app integration (moodle-mobile-app).
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
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
  no longer needed. Calling, issuing, limiting and revoking tokens: [reference/tokens-and-calling.md](../moodle-skill-files/moodle-web-services/reference/tokens-and-calling.md).

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
| [reference/tokens-and-calling.md](../moodle-skill-files/moodle-web-services/reference/tokens-and-calling.md) | Calling a function over REST or SOAP, issuing or revoking tokens, using `login/token.php`, or limiting what a token can do |
| [reference/files.md](../moodle-skill-files/moodle-web-services/reference/files.md) | A function accepts uploaded files, saves a draft area, or returns files and pluginfile URLs to a token client |
| [reference/params-and-returns.md](../moodle-skill-files/moodle-web-services/reference/params-and-returns.md) | Choosing a `PARAM_*` type, describing nested, optional or nullable structures, returning warnings, or a "Invalid parameter/response value" error needs explaining |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](../moodle-skill-files/moodle-web-services/versions/moodle-5.3.md) |

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
