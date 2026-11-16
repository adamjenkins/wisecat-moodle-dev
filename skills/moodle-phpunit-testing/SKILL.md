---
name: moodle-phpunit-testing
description: Use when writing, running or debugging PHPUnit tests for a Moodle plugin or core - tests/*_test.php, advanced_testcase, resetAfterTest, data generators (tests/generator/lib.php), admin/tool/phpunit/cli/init.php and util.php, vendor/bin/phpunit --testsuite, "No tests executed!", "Unexpected debugging() call detected", "unexpected database modification", tests that pass on MySQL or MariaDB and fail on PostgreSQL, preventResetByRollback, redirectEvents/redirectMessages/redirectEmails, external functions with clean_returnvalue, route_testcase, privacy provider tests, mock_clock_with_frozen and get_mocked_http_client. Covers the test framework's mental model, the default test recipe, invocation traps, fixture and database traps from shipped plugins, and pointers to generators, special test cases and PostgreSQL isolation. Skip when writing Behat acceptance tests (moodle-behat-testing) or building a CI workflow (moodle-ci-matrix).
---

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
  (`public/lib/phpunit/bootstraplib.php`, 5.3.0), not that yours is broken. Re-run `init.php`. When your own schema change is not picked up, bump the plugin's `$plugin->version` or use
  `util.php --drop` then `init.php`.
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
- Coverage: a `#[CoversClass]`, `#[CoversFunction]`, `#[CoversMethod]` or `#[CoversNothing]` attribute, or an
  `@covers` docblock tag, at class or method level. A test with none gets the warning "is missing any coverage
  information". Attributes are recognised only when phpcs knows the branch is 5.0 or later; below 5.0 the docblock
  must sit directly above `class`, so run phpcs with `--runtime-set moodleBranch 502` (or your lowest branch).
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
same class. Generators, special test cases and PostgreSQL detail are in the reference files below.

- **Prefer the real test database to a mocked `$DB`.** The reset makes real rows cheap, and a mocked
  `moodle_database` tests your expectations of the DML API rather than the SQL. When a collaborator must be faked,
  inject it: obtain it in production code through `\core\di::get()` and replace it in the test with
  `\core\di::set(\local_example\remote\api::class, $mock)`. Never assign to the global `$DB`.
- **Coverage:** `vendor/bin/phpunit --coverage-text --testsuite local_example_testsuite` needs pcov or Xdebug loaded.
  `--group <name>` selects tests tagged `#[\PHPUnit\Framework\Attributes\Group('<name>')]`; Moodle does not add
  groups for you, so `--testsuite` is the reliable selector.
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
- **The bootstrap preloads what a page does not.** Free functions from `course/lib.php`, `lib/filelib.php` and
  `question/engine/lib.php` work in PHPUnit without a `require_once`. Fix: add the `require_once` in the file that
  calls them, and make one real web request to every new entry point before calling the work done.
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
  Since 5.2.2, `block_myoverview` and some exporters return numeric entities (`&#60;`) where earlier builds returned
  named ones (`&lt;`) (MDL-79755, `UPGRADING.md` of 5.2.2 and 5.3.0); compare decoded text,
  `html_entity_decode($value, ENT_QUOTES | ENT_HTML5)`, when a test must pass on 5.2.0 to 5.2.1 as well.
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
| [reference/generators-and-fixtures.md](reference/generators-and-fixtures.md) | You write a plugin data generator, create activities, quiz attempts, enrolments or users for a test, change module order, or back up and restore a course inside a test |
| [reference/special-testcases.md](reference/special-testcases.md) | You test an external function, a routed controller (`route_testcase`), a privacy provider, admin settings pages, an HTTP client call, a block class, or core AI actions |
| [reference/postgresql-and-isolation.md](reference/postgresql-and-isolation.md) | A test touches transactions, event observers, message processors, the log store or `perf_get_reads()`, or passes on MySQL/MariaDB and fails on PostgreSQL |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

## References

- https://moodledev.io/general/development/tools/phpunit
- https://moodledev.io/docs/apis/subsystems/testing/generators (data generators)
- https://moodledev.io/general/development/policies/codingstyle (test naming and docblocks)
- `public/lib/phpunit/classes/advanced_testcase.php` (5.2 and 5.3): every helper named above
- `public/admin/tool/phpunit/cli/init.php` and `util.php` (5.2 and 5.3)
- Upgrade-specific changes: `moodle-5-3-changes`. Pre-release walk: `moodle-definition-of-done`.
