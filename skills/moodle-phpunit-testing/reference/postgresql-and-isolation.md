# PostgreSQL, transactions and test isolation

Read this when a test touches transactions, event observers, message processors, the log store or
`perf_get_reads()`, or passes on MySQL/MariaDB and fails on PostgreSQL (or the other way round).

Sources are the 5.2 and 5.3.0 trees, paths relative to the Moodle root, read and not run for this file; "seen in
practice" marks behaviour observed on real plugins.

## What differs, and why

`advanced_testcase::setup_test_environment()` starts a delegated transaction before each test when the database
family is `postgres` or `mssql`, and only when the previous test left the database clean
(`public/lib/phpunit/classes/advanced_testcase.php`, 5.2 and 5.3). At teardown that transaction is rolled back. On
MySQL and MariaDB, which cannot roll back DDL, there is no test transaction: the reset truncates tables instead.

So inside a PostgreSQL test, `$DB->is_transaction_started()` is true from the first line. Everything in core that
waits for "no transaction" waits forever:

| Code path | On MySQL/MariaDB | On PostgreSQL | Source |
|---|---|---|---|
| Event observers with `'internal' => false` | Run when the event is triggered | Buffered until commit, so they never run | `public/lib/classes/event/manager.php`, `process_buffers()` |
| Message processors (email, popup, mobile) | Called | Buffered until commit, so not called | `public/lib/classes/message/manager.php`, `send_conversation_message_to_processors()` and the single-message path |
| The standard log store (`tool_log` observes with `internal => false`) | Rows written | No rows | `public/admin/tool/log/db/events.php` |
| Your own `if ($DB->is_transaction_started())` guard | False | True | your code |
| Read counts from `$DB->perf_get_reads()` | One read per query | An unlimited `get_recordset_select()` is a cursor (`DECLARE`, `FETCH`, `CLOSE`), three or more reads per fetch | the pgsql driver; seen in practice |

Symptoms: an observer test, a "logged an event" test or a notification test is green locally and red on the
PostgreSQL CI row, or a read-count assertion is off by a driver-dependent amount.

## Fixes

- **Opt out of the transaction where the behaviour needs a commit.** Call `preventResetByRollback()` at the start of
  the test; the reset then truncates, as on MySQL. Core does this for its own log store tests
  (`public/admin/tool/log/store/standard/tests/store_test.php`, "Logging waits till the transaction gets committed"):

  ```php
  public function test_view_is_logged(): void {
      global $DB;
      $this->resetAfterTest();
      $this->preventResetByRollback();
      set_config('enabled_stores', 'logstore_standard', 'tool_log');
      set_config('buffersize', 0, 'logstore_standard');
      get_log_manager(true);

      \local_example\event\item_viewed::create(['context' => \context_system::instance(), 'objectid' => 1])->trigger();

      $this->assertSame(1, $DB->count_records('logstore_standard_log', ['eventname' => '\local_example\event\item_viewed']));
  }
  ```

  It costs speed, so use it only in tests that need it.
- **Test an event with `redirectEvents()` instead of through its observer** when what matters is that the event was
  triggered with the right data. Test the observer by calling it with a built event.
- **Test messages with `redirectMessages()` or `redirectEmails()`**; the sink captures before the processors, on both
  database families.
- **Assert only zero reads** with `perf_get_reads()` (a cache hit), or compare two runs of the same code on the same
  driver. Use `get_records_*` for small sets rather than recordsets when read counts matter.
- **Treat any PostgreSQL-sensitive assertion as unverified** until the PostgreSQL CI row has run it, when your local
  site is MySQL or MariaDB. Seen in practice.
- **A failed query inside a transaction aborts the whole transaction on PostgreSQL.** Code that catches a
  `dml_exception` and then queries again before the rollback gets "current transaction is aborted" on PostgreSQL
  only. In code, do not touch the database between the failed query and the rollback; in tests, expect the exception
  and stop.

## Isolation and order

- **"Test ... did not close database transaction"** is thrown at teardown when code under test started a transaction
  and neither committed nor rolled back (`teardown_test_environment()`). Fix the code path, usually an early return
  between `start_delegated_transaction()` and `allow_commit()`.
- **Order dependence.** A test that passes only after another test usually relies on a static cache, a config value
  or a file another test created. Run the suite with `--order-by=reverse`, and each new file alone; reset statics in
  `tearDown()`, then call `parent::tearDown()` once (moodle-cs requires the call).
- **Sequences start high.** Ids in the test database do not start at 1 and are sparse. Never assert a literal id, and
  never batch by `lastid + N`; order by id and count rows.
- **`resetAfterTest(false)`** keeps data for the next test in the same class; it makes order matter by design. Prefer
  a fixture method called from each test.
