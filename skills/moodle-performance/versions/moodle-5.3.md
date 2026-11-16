# Tasks and caching on Moodle 5.3

Read this when the plugin's `supported` range includes 503 and it queues ad-hoc tasks, tests "is this task already
queued", uninstalls blocks in a test or script, or a task test passes on 5.2 and fails on 5.3.

This file says what differs on 5.3 against the 5.2 baseline. Read in the 5.3.0 source and `UPGRADING.md`; nothing
here was run. The full upgrade catalogue is in `moodle-5-3-changes`.

## `queue_adhoc_task($task, true)` returns the existing task id

| | 5.2 | 5.3 |
|---|---|---|
| New task queued | new id | new id |
| Matching task already queued | `false` | the existing task's id (an exhausted one is revived first) |
| Component deprecated, or DML error | `false` | `false` |

Source: `public/lib/classes/task/manager.php`, `queue_adhoc_task()`, compared between 5.2 and 5.3.0; `UPGRADING.md`
(tool_task, MDL-86422). Duplicate detection on 5.3 uses a new `task_adhoc.identityhash` column.

Symptom: code that reads `=== false` as "already queued" never sees a duplicate on 5.3, and a test asserting
`assertFalse(queue_adhoc_task($task, true))` fails on every 5.3 CI row while passing on 5.2.

Fix that works on both versions: do not interpret the return value; ask the queue before queueing.
`get_queued_adhoc_task_record()` is public on 5.2 and 5.3 and is the lookup that 5.2's own duplicate check uses. It
matches class, component, custom data and, when the task has one, the user; `false` as the second argument leaves
out tasks that have used up their attempts.

```php
$already = \core\task\manager::get_queued_adhoc_task_record($task, false) !== false;
if (!$already) {
    \core\task\manager::queue_adhoc_task($task);
}
```

To inspect every queued instance of a class instead (for example in a test), use
`\core\task\manager::get_adhoc_tasks(\local_example\task\send_report::class)` and compare
`get_custom_data_as_string()` and `get_userid()`.

The general lesson: a core API's return value is part of the supported-range contract. Read the `UPGRADING.md` of
every branch in `$plugin->supported` before relying on one.

## Other task changes

- The protected `\core\task\manager::task_is_scheduled()` is deprecated; use `get_queued_adhoc_task_record()`
  (MDL-86422).
- `\core\task\manager::set_scheduled_task_nextruntime()` returns a bool, `false` when the task is running
  (MDL-89200). The method is not in the 5.2.2+ `manager.php`, so guard it with `method_exists()` in a plugin that
  supports 5.2.
- `queue_adhoc_task()` called from an upgrade step before the `identityhash` column exists queues a plain task
  without duplicate detection instead of failing (`manager.php` comment, MDL-89876).
- Uninstalling a block plugin no longer deletes its instances synchronously: `\core\task\delete_block_instances_task`
  deletes them in batches from cron. A test or script that uninstalls a block and then counts `block_instances` must
  run ad-hoc tasks first (MDL-89289).
- `adhoc_task::set_soft_retry_delay()` and `manager::adhoc_task_delayed()` are listed as new in 5.3's
  `UPGRADING.md` (MDL-79763), and were also backported to 5.2.2 (listed under "5.2.2" in the `UPGRADING.md` of the
  5.2 branch). They are absent from 5.2.0 and 5.2.1.

## Caching

No change to the MUC API between 5.2 and 5.3 was found: `public/cache/classes/` has the same files on both, and
`public/cache/UPGRADING.md` has no 5.3 entry.
