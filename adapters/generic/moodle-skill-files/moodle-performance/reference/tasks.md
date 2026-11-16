# Tasks: scheduled tasks, locks, concurrency, retries, CLI

Read this when you write `db/tasks.php` or a scheduled task, add a lock or a concurrency limit, change how a task
retries, or run and debug tasks from the command line.

Sources: `public/lib/classes/task/manager.php`, `adhoc_task.php`, `scheduled_task.php`,
`public/lib/classes/lock/lock_config.php`, `admin/cli/adhoc_task.php`, `admin/cli/scheduled_task.php`, read on 5.3.0
and compared with 5.2 (the same unless stated).

## Scheduled task

```php
<?php
// (GPL header)
// db/tasks.php
defined('MOODLE_INTERNAL') || die();

$tasks = [
    [
        'classname' => \local_example\task\cleanup::class,
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
        return get_string('task_cleanup', 'local_example');
    }

    public function execute(): void {
        global $DB;
        $cutoff = \core\di::get(\core\clock::class)->time() - 90 * DAYSECS;
        $DB->delete_records_select('local_example_log', 'timecreated < ?', [$cutoff]);
        mtrace('Old log rows deleted.');
    }
}
```

- `'R'` in `minute` or `hour` picks a random value at install, so every site does not run the task at the same
  moment. Use it for anything that calls an external service.
- `'disabled' => 1` ships the task off; an administrator enables it.
- `db/tasks.php` is read on upgrade: a new task or changed default needs a version bump. Check it exists with
  `php admin/cli/scheduled_task.php --list | grep local_example`.
- Administrators can override the schedule in the UI or with `$CFG->scheduled_tasks` in `config.php`; once a task
  is customised, a new default in `db/tasks.php` does not replace the administrator's schedule
  (`manager::reset_scheduled_tasks_for_component()` skips a task whose `is_customised()` is true).
- Scheduled tasks run as the cron user, a copy of the main admin (`\core\cron::setup_user()`, 5.3.0). Code that must
  act for a particular user belongs in an ad-hoc task with `set_userid()`.
- Keep `blocking` at 0. A blocking task stops every other task from running while it runs.
- `\core\di::get(\core\clock::class)->time()` makes time testable; `time()` works but cannot be frozen in tests.

## Ad-hoc task details

- `set_custom_data()` takes anything `json_encode()` accepts; `get_custom_data()` returns objects, not arrays.
- `set_next_run_time($timestamp)` delays the first run.
- `\core\task\manager::reschedule_or_queue_adhoc_task($task)` updates the next run time of a queued task with the
  same user, class, component and custom data instead of adding another; use it with `set_next_run_time()`.
- `get_name()` is optional for ad-hoc tasks; it is what the task log and the admin queue page show.
- To test "is it already queued" on both versions, do not read the return value of `queue_adhoc_task($task, true)`
  (false for a duplicate on 5.2, the existing id on 5.3). Call
  `\core\task\manager::get_queued_adhoc_task_record($task, false)`, which returns the matching record or `false`, or
  list the queued instances with `\core\task\manager::get_adhoc_tasks(\local_example\task\send_report::class)`.

## Failures and retries

- A task that throws is marked failed and rescheduled with a growing delay, capped at 24 hours
  (`manager::adhoc_task_failed()` and `scheduled_task_failed()`).
- An ad-hoc task has 12 attempts by default (`adhoc_task::$attemptsavailable`); `set_attempts_available()` changes
  it before queueing. Override `retry_until_success()` to return `false` for a task that must run at most once.
- To wait for something without counting a failure (a remote service is busy, a lock is held), call
  `$this->set_soft_retry_delay()` (exponential) or `set_soft_retry_delay($seconds)` from `execute()` and return
  normally (`adhoc_task.php`; present from 5.2.2 and on 5.3, absent from 5.2.0 and 5.2.1, so a plugin whose
  `requires` is 5.2.0 guards the call with `method_exists()`).
- Make `execute()` safe to run twice: a task can fail after doing part of its work, and the retry starts again from
  the top.

## Locks

Cron already holds a lock per task, so the same scheduled task never runs twice at once. Take your own lock when
other code paths (a page, an ad-hoc task) can touch the same resource:

```php
$factory = \core\lock\lock_config::get_lock_factory('local_example');
if (!$lock = $factory->get_lock('course_' . $courseid, 10)) {
    // Someone else holds it; retry later rather than blocking the request.
    throw new \moodle_exception('locktimeout');
}
try {
    // ... work on the course's data ...
} finally {
    $lock->release();
}
```

- `get_lock($resource, $timeout, $maxlifetime = 86400)` waits up to `$timeout` seconds and returns `false` if it
  could not get the lock.
- Release in `finally`. An exception between `get_lock()` and `release()` otherwise leaves the lock held until the
  factory's own cleanup or `maxlifetime` frees it, and other callers time out meanwhile.
- Inside an ad-hoc task, prefer `set_soft_retry_delay()` and return over waiting a long time for a lock.

## Concurrency limits for ad-hoc tasks

Many queued instances of one class run in parallel on sites with several cron runners. To cap them, override in the
task class:

```php
protected function get_default_concurrency_limit(): int {
    return 1;
}
```

Administrators can override per class with `$CFG->task_concurrency_limit[\local_example\task\send_report::class]`
(`adhoc_task::get_concurrency_limit()`).

## Running tasks by hand

```bash
php admin/cli/scheduled_task.php --list
php admin/cli/scheduled_task.php --execute='\local_example\task\cleanup' --showdebugging
php admin/cli/adhoc_task.php --execute --classname='\local_example\task\send_report' --showdebugging
php admin/cli/adhoc_task.php --id=1234 --showdebugging --showsql   # one task, also a failed one
php admin/cli/adhoc_task.php --execute --failed                    # only tasks in their fail delay
```

`--force` runs even when cron is disabled on the site; `--ignorelimits` ignores the ad-hoc concurrency and runtime
limits (help text of `admin/cli/adhoc_task.php`, 5.3.0).

Run the commands as the web server user. The task log is in Site administration > Server > Tasks > Task logs.

In PHPUnit, run queued ad-hoc tasks with `$this->run_all_adhoc_tasks()` and a scheduled task by calling
`(new cleanup())->execute()` after `$this->setAdminUser()`; details are in `moodle-phpunit-testing`.

## Upgrade steps

Never call grade, modinfo or course APIs from `db/upgrade.php`; queue an ad-hoc task from the upgrade step and let
cron do the work (`moodle-upgrade-migration`). **5.3+:** `queue_adhoc_task()` called from an upgrade step that
runs before the `task_adhoc.identityhash` column exists queues the task without duplicate detection instead of
failing (`public/lib/classes/task/manager.php`, 5.3.0).
