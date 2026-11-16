---
name: moodle-performance
description: Use when a Moodle page, web service, filter or task is slow, runs too many queries, or runs out of memory, or when adding caching or background work - db/caches.php and \core_cache\cache::make (MUC application, session and request caches, cachedef_ strings, invalidation events), per-context or per-call repeated queries, N+1 loops, get_recordset vs get_records, batching large tables, $DB->perf_get_queries() budgets, ad-hoc and scheduled tasks (db/tasks.php, queue_adhoc_task, locks, retries), session locks, perfdebug, profiling and server tuning. Skip when the slowness is theme CSS compilation (moodle-theme-scss) or the task is a schema change (moodle-plugin-development).
---

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
[reference/diagnosis-and-server.md](reference/diagnosis-and-server.md).

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

Recipe for a definition: [reference/muc-caching.md](reference/muc-caching.md) holds the option table, data sources,
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
  task's id where 5.2 returned `false`; see [versions/moodle-5.3.md](versions/moodle-5.3.md).
- **Re-check permissions in `execute()`.** The user's capabilities may have changed between queueing and running.
- **Throwing from `execute()` marks the task failed** and cron retries it with a growing delay. To wait for something
  without counting a failure, call `$this->set_soft_retry_delay()` and return (present from 5.2.2 and on 5.3; guard
  with `method_exists()` if `requires` is 5.2.0).

Scheduled tasks, `db/tasks.php`, locks, concurrency limits, retries and running tasks from the CLI:
[reference/tasks.md](reference/tasks.md).

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
| [reference/muc-caching.md](reference/muc-caching.md) | Writing or changing a `db/caches.php` definition, choosing options (`simplekeys`, `staticacceleration`, identifiers, data source), invalidating, or testing cached code |
| [reference/tasks.md](reference/tasks.md) | Writing `db/tasks.php`, a scheduled task, a lock, a concurrency limit or retry handling, or running and debugging tasks from the CLI |
| [reference/diagnosis-and-server.md](reference/diagnosis-and-server.md) | Finding which query or function is slow (slow-query log, EXPLAIN, profiling), or tuning OPcache, sessions and cache stores on a server |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

## References

- Caching (MUC): https://moodledev.io/docs/apis/subsystems/muc
- Task API: https://moodledev.io/docs/apis/subsystems/task (ad-hoc: `/adhoc`, scheduled: `/scheduled`)
- Lock API: https://moodledev.io/docs/apis/core/lock
- Data manipulation API (recordsets): https://moodledev.io/docs/apis/core/dml
- Profiling: https://moodledev.io/docs/guides/profiling
- Related skills: `moodle-web-services` (`readonlysession`), `moodle-upgrade-migration`, `moodle-field-lessons`,
  `moodle-release-preflight` (Plugins directory review checks), `moodle-phpunit-testing`
