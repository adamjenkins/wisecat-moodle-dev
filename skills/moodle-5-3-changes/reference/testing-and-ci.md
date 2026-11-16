# Moodle 5.3: tests, CI and test sites

Read this when PHPUnit, Behat or CI fails or must change for 5.3, when you add `MOODLE_503_STABLE` to a CI matrix,
or when a script that sets up or tears down test data behaves differently on 5.3.

Sources: the 5.3.0 tree (`public/admin/environment.xml`, `public/admin/tool/behat/cli/`,
`public/admin/tool/phpunit/cli/util.php`, `public/lib/moodlelib.php`) and the `## 5.3` section of its root
`UPGRADING.md`, read, not run, unless stated. The general CI recipe is `moodle-ci-matrix`.

## CI matrix values for 5.3

| Item | 5.3 | 5.2 |
|---|---|---|
| Branch | `MOODLE_503_STABLE` | `MOODLE_502_STABLE` |
| PHP | 8.3 minimum, 8.4 supported | same |
| PostgreSQL | 17 or later | 16 or later |
| MariaDB | 11.4 or later | 10.11 or later |
| MySQL | 8.4 or later | same |
| SQL Server | 2019 (15.0) or later | same |

A job pairing `MOODLE_503_STABLE` with PostgreSQL 16 or MariaDB 10.11 fails at the environment check during
install. After checkout, core needs `composer install` at the Moodle root; confirm in the install step's log that
your CI ran it (not checked here for `moodle-plugin-ci`).

## Deprecations fail Behat, not PHPUnit

A deprecated call reached by a Behat scenario fails that step with the debugging message, while PHPUnit prints
"Unexpected debugging() call detected" and still passes. On 5.3 the usual sources are the 25 `user/lib.php`
functions, the global `\external_*` class names, `get_return_section()`, the `sr` URL parameter on
`course/modedit.php`, `course/mod.php` and `course/editsection.php`, and `extend_user_menu::add_navitem()`. Treat
the PHPUnit line as a failure and fix the call.

## Site home is off on fresh installs

- A fresh install has `enablemyhome = 0` (`public/admin/settings/appearance.php`); an upgraded site keeps the old
  behaviour because upgrade step `2026022700.01` sets it to 1 (`public/lib/db/upgrade.php`). This is already true on
  a fresh 5.2 install; it shows up in a 5.3 port because CI and new test sites are fresh installs.
- Symptom: Behat "I am on site homepage" lands on `/my/` (or the configured start page), and steps that expect the
  site home blocks or the "Site home" link fail.
- Fix in the feature's Background, when the scenario needs the site home:

```gherkin
Background:
  Given the following config values are set as admin:
    | enablemyhome    | 1 |
    | defaulthomepage | 0 |
```

## `delete_course()` can be asynchronous

- `delete_course($courseorid, $showfeedback = true, bool $asyncpreferred = true)` on 5.3 marks the course for
  deletion and, when the admin setting `moodlecourse/enablecourseasyncdeletion` is on (default off), queues
  `\core_course\task\course_async_deletion` and returns at once (`public/lib/moodlelib.php`). The course row and its
  shortname stay until cron runs.
- Symptom: a setup script that deletes a course and recreates it with the same shortname fails with "Short name is
  already used for another course" on a site where asynchronous deletion is enabled; a check that the course is
  gone right after the call fails.
- Fix: force synchronous deletion. The third argument is ignored on 5.2 (it has two parameters), so the call is
  safe on both:

```php
delete_course($course, false, false);
```

## Behat

| Change | Use | MDL |
|---|---|---|
| `--colourmode=<light\|dark>` on `admin/tool/behat/cli/init.php`, `util.php`, `util_single_run.php` (5.3 only); `behat_get_colour_mode()` exposes it | Run the suite once in dark mode. The option also turns colour modes on, so a scenario that assumes they are off starts with `Given the run is not using a colour mode`. Precedence: user preference, then run option, then site setting. Reference feature: `public/theme/boost/tests/behat/colour_mode_accessibility.feature` | MDL-68037 |
| `--scss-deprecations` (5.2 and 5.3) | Fails any JavaScript step on a page that uses a Bootstrap 4 compatibility class; worth running now because the layer goes in 6.0 | |
| `I set the focus on the "<element>" "<selector>"` | Move keyboard focus without activating; JavaScript scenarios only, throws otherwise | MDL-84065 |
| `the course linear navigation should be visible` / `should not be visible` | Assert the previous/next footer | MDL-87575 |
| `I set portfolio instance "X" to "Y"` deprecated | `I set the portfolio instance "X" to "Y"` | MDL-89069 |
| Navigation markup is React (`.mds-nav-pill`), search box is inline, modal titles are `<h2>` | Replace raw CSS/XPath selectors with named selectors or navigation steps | MDL-89294, MDL-87830, MDL-75699 |

```sh
php admin/tool/behat/cli/init.php --colourmode=dark
```

## PHPUnit

- `public/admin/tool/phpunit/cli/util.php` gains `--upgrade`, `--snapshot[=NAME]`, `--snapshot --list` and
  `--restore=NAME`, so CI can restore a cached core install and only upgrade after adding a plugin (MDL-88495, not in
  the notes).

```sh
php public/admin/tool/phpunit/cli/util.php --snapshot=core
php public/admin/tool/phpunit/cli/util.php --snapshot --list
# --restore needs the exact name printed by --list.
php public/admin/tool/phpunit/cli/util.php --restore=<name from --list>
php public/admin/tool/phpunit/cli/util.php --upgrade
```

- Assertions on formatted exporter strings: single-valued `PARAM_TEXT` properties come back with numeric entities
  (`&#38;` instead of `&amp;`, MDL-79755; also on the 5.2 branch from 5.2.2).
- Assertions on `queue_adhoc_task($task, true)`: a duplicate returns the existing id on 5.3, `false` on 5.2.
- Block uninstall tests: instances are deleted by `\core\task\delete_block_instances_task`; run ad-hoc tasks
  (`$this->runAdhocTasks()`) before asserting they are gone (MDL-89289).
- Route tests: `\core\tests\router\route_testcase` gains `assert_route_is_scoped()`, `assert_route_is_unscoped()`,
  `assert_route_required_scopes()`.

## Front-end checks

- Rebuild AMD after replacing `theme_boost/bootstrap/*` imports (`grunt amd`); `moodle-plugin-ci grunt` fails when
  `amd/build` is out of date.
- 5.3's stylelint rejects `container-type`, `@container` and `clamp()` in `font-size` through `csstree/validator`;
  the per-line workaround is in `moodle-theme-scss`.
