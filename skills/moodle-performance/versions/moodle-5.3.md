# Tasks and caching on Moodle 5.3

What differs on 5.3 against the 5.2 baseline. Read in the 5.3.0 source and `UPGRADING.md`; nothing here was run.
The full upgrade catalogue is in `moodle-5-3-changes`.

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

Fix that works on both versions: do not interpret the return value; ask the queue.

```php
$queued = \core\task\manager::get_adhoc_tasks(\local_example\task\send_report::class);
$already = false;
foreach ($queued as $existing) {
    if ($existing->get_custom_data_as_string() === $task->get_custom_data_as_string()
            && $existing->get_userid() == $task->get_userid()) {
        $already = true;
        break;
    }
}
if (!$already) {
    \core\task\manager::queue_adhoc_task($task);
}
```

The general lesson: a core API's return value is part of the supported-range contract. Read the `UPGRADING.md` of
every branch in `$plugin->supported` before relying on one.

## Other task changes

- `\core\task\manager::task_is_scheduled()` is deprecated; use `get_queued_adhoc_task_record()` (MDL-86422).
- `\core\task\manager::set_scheduled_task_nextruntime()` now returns a bool, `false` when the task is running
  (MDL-89200).
- `queue_adhoc_task()` called from an upgrade step before the `identityhash` column exists queues a plain task
  without duplicate detection instead of failing (`manager.php` comment, MDL-89876).
- Uninstalling a block plugin no longer deletes its instances synchronously: `\core\task\delete_block_instances_task`
  deletes them in batches from cron. A test or script that uninstalls a block and then counts `block_instances` must
  run ad-hoc tasks first (MDL-89289).
- `adhoc_task::set_soft_retry_delay()` and `manager::adhoc_task_delayed()` are listed as new in 5.3's
  `UPGRADING.md` (MDL-79763); the methods are also present in the 5.2.2+ source read for this skill.

## Caching

No change to the MUC API between 5.2 and 5.3 was found: `public/cache/classes/` has the same files on both, and
`public/cache/UPGRADING.md` has no 5.3 entry.
