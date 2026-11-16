# Templates for the db/ definition files and external functions

Read this when writing or reviewing `db/services.php`, `db/tasks.php`, `db/events.php`, `db/caches.php`,
`db/messages.php`, `db/install.php`, `db/uninstall.php` or an external function class.

All samples are valid on Moodle 5.2 and 5.3. Each file starts with `<?php`, the GPL boilerplate, a file docblock
and `defined('MOODLE_INTERNAL') || die();`. Which of these files need a version bump is in `SKILL.md`, mental
model point 2: services, tasks, messages, caches, access and log do; events and hooks need only a cache purge.

## db/services.php and the external function class

```php
$functions = [
    'local_example_get_items' => [
        'classname'    => 'local_example\external\get_items',
        'description'  => 'Return the items of a course.',
        'type'         => 'read',
        'ajax'         => true,
        'capabilities' => 'local/example:view',
    ],
];
```

```php
namespace local_example\external;

use core_external\external_api;
use core_external\external_function_parameters;
use core_external\external_multiple_structure;
use core_external\external_single_structure;
use core_external\external_value;

class get_items extends external_api {
    public static function execute_parameters(): external_function_parameters {
        return new external_function_parameters([
            'courseid' => new external_value(PARAM_INT, 'Course id'),
        ]);
    }

    public static function execute(int $courseid): array {
        global $DB;
        ['courseid' => $courseid] = self::validate_parameters(self::execute_parameters(), ['courseid' => $courseid]);

        $context = \core\context\course::instance($courseid);
        self::validate_context($context);
        require_capability('local/example:view', $context);

        $result = [];
        foreach ($DB->get_records('local_example_items', ['courseid' => $courseid], 'id', 'id, name') as $record) {
            $result[] = [
                'id' => (int) $record->id,
                'name' => format_string($record->name, true, ['context' => $context]),
            ];
        }
        return $result;
    }

    public static function execute_returns(): external_multiple_structure {
        return new external_multiple_structure(new external_single_structure([
            'id' => new external_value(PARAM_INT, 'Item id'),
            'name' => new external_value(PARAM_TEXT, 'Item name'),
        ]));
    }
}
```

- `methodname` defaults to `execute`; `classname` is the namespaced class without a leading backslash.
- Verify registration on the site, not in a unit test that calls the class directly:
  `\core_external\external_api::external_function_info('local_example_get_items', IGNORE_MISSING)` returns false
  until a version bump has run the upgrade.
- `self::validate_context()` ends in `require_login()`. A function declared `'loginrequired' => false` must set
  `$PAGE->set_context()` itself instead, or anonymous callers are refused.
- `validate_parameters()` rejects a value that cleaning would change, so free text declared `PARAM_TEXT` fails on
  input such as `9.11 < 9.9`. Declare free text `PARAM_RAW` and escape it at every sink (`moodle-web-services`).
- The course context check enforces enrolment. If the page this function backs is gated on ownership or another
  capability, gate the function the same way, or unenrolled owners get `requireloginerror`.

## db/tasks.php and task classes

```php
$tasks = [
    [
        'classname' => 'local_example\task\cleanup',
        'blocking'  => 0,
        'minute'    => 'R',
        'hour'      => '3',
        'day'       => '*',
        'month'     => '*',
        'dayofweek' => '*',
    ],
];
```

```php
namespace local_example\task;

class cleanup extends \core\task\scheduled_task {
    public function get_name(): string {
        return get_string('taskcleanup', 'local_example');
    }

    public function execute(): void {
        // Work here. Re-check any capability the work depends on: the request that queued it is gone.
    }
}
```

- Check registration with `php admin/cli/scheduled_task.php --list | grep local_example` (core CLI, Moodle root).
- An ad-hoc task extends `\core\task\adhoc_task`, carries data with `set_custom_data()`, the acting user with
  `set_userid()`, and is queued with `\core\task\manager::queue_adhoc_task($task, true)`. **5.3+:** the return
  value of that call changed (see `versions/moodle-5.3.md`); do not branch on it across branches.

## db/events.php

```php
$observers = [
    [
        'eventname' => '\core\event\course_deleted',
        'callback'  => '\local_example\observer::course_deleted',
    ],
];
```

- Observers are `internal` by default: they run inside the transaction that triggered the event. Declare
  `'internal' => false` for work that must run only after the commit (default read in
  `public/lib/classes/event/manager.php`, 5.3.0). PHPUnit on PostgreSQL wraps each test in a transaction, so
  non-internal observers behave differently there (`moodle-phpunit-testing`).
- Your own `course_deleted` observer runs in your tests too and may delete fixtures a test built.

## db/caches.php

```php
$definitions = [
    'items' => [
        'mode'       => cache_store::MODE_APPLICATION,
        'simplekeys' => true,
        'staticacceleration' => true,
    ],
];
```

- Each definition needs `$string['cachedef_items']` in the lang file; a missing one shows as `[[cachedef_items]]`
  on the cache admin page and is a review finding.
- Use: `$cache = \cache::make('local_example', 'items');`. For values computed once per request (for example a
  filter's resolved configuration per context), a request cache (`MODE_REQUEST`) removes repeated queries.

## db/messages.php

```php
$messageproviders = [
    'itemready' => [
        'defaults' => [
            'popup' => MESSAGE_PERMITTED + MESSAGE_DEFAULT_ENABLED,
            'email' => MESSAGE_PERMITTED,
        ],
    ],
];
```

Each provider needs `$string['messageprovider:itemready']`. Send with a `\core\message\message` whose
`component` is `local_example` and `name` is `itemready`. Test the rendered subject and body with
`$this->redirectMessages()`, not the return value of `message_send()`.

## db/install.php and db/uninstall.php

```php
function xmldb_local_example_install() {
    // Runs once after install.xml has created the tables.
    return true;
}

function xmldb_local_example_uninstall() {
    global $DB;
    // Core drops the plugin's tables, config, capabilities and files.
    // Remove what lives elsewhere, for example user preferences.
    $DB->delete_records('user_preferences', ['name' => 'local_example_layout']);
    return true;
}
```

Core's uninstall leaves user preferences behind, so a plugin that stores any deletes them here.

## References

- https://moodledev.io/docs/apis/subsystems/external
- https://moodledev.io/docs/apis/subsystems/task
- https://moodledev.io/docs/apis/commonfiles/db-tasks.php
- https://moodledev.io/docs/apis/core/message
- https://moodledev.io/docs/apis/subsystems/muc
