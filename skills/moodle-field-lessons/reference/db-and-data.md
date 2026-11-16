# DML, XMLDB and stored data: the small print

Read this when writing queries with `$DB`, changing `install.xml` or `upgrade.php`, adding a column next to an
existing value, running anything that writes to a database outside a test, or when a query behaves differently on
PostgreSQL.

The `install.xml`/`upgrade.php` recipe is in `moodle-plugin-development`; the version-to-version upgrade rules are
in `moodle-upgrade-migration`. Samples are valid on Moodle 5.2 and 5.3.

## DML calls

- **`update_record()` writes every property of the object you pass.** Near a counter that other requests
  increment, a read-modify-`update_record()` silently undoes their increments. Use `set_field()` or a scoped
  `UPDATE ... SET x = x + 1`.
- **`get_in_or_equal()` defaults to `?` placeholders.** Pass `SQL_PARAMS_NAMED` when the rest of the query uses
  named parameters, or the query dies with "Mixed types of sql query parameters!!".

  ```php
  [$insql, $params] = $DB->get_in_or_equal($ids, SQL_PARAMS_NAMED, 'item');
  $params['courseid'] = $courseid;
  $records = $DB->get_records_select('local_myplugin_items', "courseid = :courseid AND id $insql", $params);
  ```

- **`get_records()` has six parameters and is keyed by the first field in `$fields`** (`id` for `*`). A seventh
  "key by" argument is silently ignored, and rows with a duplicate key overwrite each other (with only a `debugging()` notice). Put the key column first in
  `$fields`, or use `get_records_menu()`.
- **Read a returned array's keys from the function's `return` statement**, not from memory: a wrong key reads as
  `null` with at most a warning.
- **Order rows written in the same request by `id`, not by a time column**: they share the same second, so
  `ORDER BY timecreated` returns them in an arbitrary order that differs between databases.
- **On PostgreSQL, a failed query aborts the transaction**: until the rollback, every further query fails too. Code
  that runs between a caught DML exception and the rollback (a `catch` block, a `finally`, a cache rebuild such as
  `rebuild_course_cache()`) must not touch the database.

## XMLDB and schema changes

- **XMLDB foreign keys are indexes, not enforced constraints.** Changing NOT NULL on a keyed column needs
  `drop_key()`, `change_field_notnull()`, `add_key()`, or the upgrade throws `ddldependencyerror`. Never write a
  raw `ALTER TABLE` with a hard-coded prefix.
- **Never declare `CHAR NOTNULL="true" DEFAULT=""`.** XMLDB rewrites it with a `debugging()` that fires only on a
  fresh install, which aborts `moodle-plugin-ci install` while an upgraded development site stays quiet; the
  PHPUnit and Behat init output does not show it either. An optional CHAR is `NOTNULL="false"` with no default.
  While writing a table: `grep -n 'DEFAULT=""' db/install.xml` must print nothing. After any `install.xml` change,
  install it fresh with `DEBUG_DEVELOPER` (or run `moodle-plugin-ci install`) and read the output.
- **Pair every `install.xml` change with an `upgrade.php` step and a version bump.** `install.xml` is read only on a
  fresh install, so a correction without a step changes nothing on existing sites while the upgrade reports
  success.
- **Check each new table and column name against the reserved-word lists** in
  `public/lib/ddl/*_sql_generator.php` while writing it (`connection` is reserved on MySQL); a rename later touches
  every query (`moodle-plugin-development`).
- **A new format or units column beside an existing value widens that value's contract** for every reader you
  cannot change: other plugins querying the table, web-service clients whose return structure has no such field.
  List the readers; if they cannot learn the new column, normalise on write.

## Writing to a database outside a test

- **Never run DDL or a mutating probe from a standalone CLI script.** A script that requires `config.php` writes to
  the site's live database. Put the probe in an `advanced_testcase` with `$this->resetAfterTest()`; if a script
  must touch the database, print `$CFG->dbname` and `$CFG->prefix` first.
- **Moodle's CLI setup changes the working directory** to the script's own directory
  (`chdir(dirname($_SERVER['argv'][0]))`, `public/lib/setup.php:253-258`, 5.3.0). A CLI script that takes a
  relative path argument resolves it against `$_SERVER['PWD']`, not `getcwd()`.

  ```php
  $path = $options['file'];
  if ($path !== '' && $path[0] !== '/') {
      $path = $_SERVER['PWD'] . '/' . $path;
  }
  ```

- **Importers and generators that create questions write them into a question bank chosen explicitly** (a
  `mod_qbank` instance the caller names or creates), never silently into the site-level shared bank; on 5.x
  questions live in `mod_qbank` instances, and a bank picked by fallback surprises the site's managers.

## References

- https://moodledev.io/docs/apis/core/dml
- https://moodledev.io/docs/apis/core/dml/ddl
- https://moodledev.io/general/development/tools/xmldb
