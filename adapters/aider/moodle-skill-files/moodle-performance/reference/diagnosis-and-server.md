# Finding the slow part, and server settings

Read this when you need to find which query or function is slow (slow-query log, EXPLAIN, SQL traces, profiling), or
when you tune OPcache, sessions and cache stores on a server.

## Which queries run, and from where

- **SQL trace in debugging output:** Site administration > Development > Debugging > "Show origin of SQL calls"
  (`debugsqltrace`: 1 line, 2 lines or a full trace; `public/admin/settings/development.php`, 5.3.0). Combine with
  `$CFG->debugdisplay = 1` on a development site to see where each query comes from.
- **Log queries to the database:** in `config.php`, inside `$CFG->dboptions`:

  ```php
  'logall'   => false,   // Every query into the log_queries table. Development only.
  'logslow'  => 200,     // Queries slower than 200 ms. An integer in milliseconds, not a string.
  'logerror' => true,    // Failing queries.
  ```

  Rows go to `{log_queries}` with the SQL, parameters, execution time and a backtrace (`config-dist.php` and the
  table in `public/lib/db/install.xml`, 5.3.0).
- **CLI scripts and tasks:** `--showsql` on `admin/cli/adhoc_task.php` and `admin/cli/scheduled_task.php` prints
  every query as it runs.
- **Database side:** the server's own slow-query log (MySQL `slow_query_log`, PostgreSQL `log_min_duration_statement`)
  catches what Moodle's logging misses, such as queries from other plugins on the same page.

## EXPLAIN

Take the SQL from the trace with the prefix replaced (`{user}` becomes `mdl_user`) and the parameters filled in:

```sql
-- MySQL / MariaDB
EXPLAIN SELECT ...;
-- PostgreSQL
EXPLAIN ANALYZE SELECT ...;
```

Look for a full scan of a big table (MySQL `type: ALL`, PostgreSQL `Seq Scan`), `Using filesort` or
`Using temporary`, and row estimates far above the rows returned. The fix is usually an index on the columns of the
`WHERE` and `JOIN`, in the order the query filters by; a composite index serves queries on its leftmost columns.
Indexes are declared in `db/install.xml` with an upgrade step (`moodle-plugin-development`).

## Profiling PHP

Moodle integrates XHProf and Tideways (`public/lib/xhprof/xhprof_moodle.php` checks for the `tideways_xhprof`,
`tideways` or `xhprof` extension, 5.3.0). The Profiling settings page appears only when one is loaded.

1. Install the PHP extension on the development server.
2. Site administration > Development > Profiling: turn on `profilingenabled`, and `profilingallowme`.
3. Add `PROFILEME` to the URL of the slow page (`/course/view.php?id=2&PROFILEME`); `DONTPROFILEME` stops it.
4. Open the run in Site administration > Development > Profiling runs (`admin/tool/profiling`), sort by inclusive
   wall time, and follow the call graph to your plugin's functions.

`profilingincluded` profiles matching scripts automatically, and `$CFG->earlyprofilingenabled = true` in `config.php`
starts profiling before setup so bootstrap time is included. Details: https://moodledev.io/docs/guides/profiling.

For a quick timing without a profiler, wrap the code in `microtime(true)` calls and `mtrace()` or `debugging()` the
difference; `$PERF` holds core's own counters for the footer and is not meant to be written by plugins.

## Server settings that matter

These are for the people running the site; plugin code must work without them.

- **OPcache** on, with enough memory for Moodle's file count:

  ```ini
  opcache.enable = 1
  opcache.memory_consumption = 256
  opcache.max_accelerated_files = 20000
  ; Production only: then reload PHP after every code deploy.
  opcache.validate_timestamps = 0
  ```

  With `validate_timestamps = 0`, a deployed file is not seen until PHP-FPM or the web server reloads; a
  "the fix did not work" report after a deploy is often this.
- **Sessions:** the default session handler is fine for one web server. For several, use Redis:
  `$CFG->session_handler_class = '\core\session\redis';` with `$CFG->session_redis_host` and friends
  (`config-dist.php`, 5.3.0). Redis sessions also lock per session, so long requests still block a user's other
  requests until `\core\session\manager::write_close()`.
- **Cache stores:** core ships `apcu`, `file`, `redis`, `session` and `static` stores on 5.2 and 5.3
  (`public/cache/stores/`). Map application caches to Redis on a cluster; APCu is per server, so use it only for
  definitions marked `canuselocalstore` or for single-server sites.
- **Directories:** `$CFG->cachedir` and `$CFG->tempdir` must be shared by all web servers; `$CFG->localcachedir` is
  per server and holds files Moodle can rebuild (compiled JavaScript, theme CSS, language caches). Put it on fast
  local disk (`config-dist.php`, 5.3.0).
- **Production switches:** `$CFG->cachejs`, `$CFG->cachetemplates` on and `$CFG->themedesignermode` off.
  `config-dist.php` marks the changed value of each as not for production servers; with them changed, JavaScript,
  templates or theme CSS are rebuilt or re-sent instead of cached.
- **Cron:** run `admin/cli/cron.php` every minute, or keep-alive runners for sites with many ad-hoc tasks; slow or
  stopped cron shows as tasks that never run, not as slow pages.

## Browser-side evidence

The performance footer is part of the page. A full-page screenshot of a page with it enabled is dominated by the
footer, and automated layout checks that measure page height include it; switch `perfdebug` off before taking
screenshots or measuring layout.
