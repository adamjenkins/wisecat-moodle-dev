# Testing blind spots: PHPUnit, security regression tests, Behat, browser automation, CI

Read this when a PHPUnit or Behat test passes but the feature fails on a site, when writing a security regression
test or a date/timezone assertion, when driving Moodle with a browser automation tool, or when a CI run is green
and you are not sure it checked anything.

The full testing recipes are in `moodle-phpunit-testing`, `moodle-behat-testing` and `moodle-ci-matrix`. This file
keeps the traps those recipes do not spell out. Samples are valid on Moodle 5.2 and 5.3.

## PHPUnit traps

- **PHPUnit cannot see what its bootstrap already loaded.** Free functions from `course/lib.php`,
  `lib/filelib.php` and `question/engine/lib.php` are preloaded in PHPUnit but not on a web request, so a missing
  `require_once` passes every test and fatals on the page ("Call to undefined function"). The same holds for
  routed POST handlers, hook and navigation dispatch, draft file areas, backup and restore, and external HTTP
  integrations. Fix: add the explicit requires, and give each such change one real web request.

  ```php
  require_once($CFG->dirroot . '/course/lib.php');
  require_once($CFG->libdir . '/filelib.php');
  require_once($CFG->dirroot . '/question/engine/lib.php');
  ```

- **A script that uses a data generator outside PHPUnit** (a CLI script building demo data) gets it from
  `\core\test\testing_util::get_data_generator()`, which loads `lib/testing/generator/lib.php` itself
  (`public/lib/classes/test/testing_util.php`, 5.2 and 5.3). `new \testing_data_generator()` written directly is a
  "Class not found" fatal outside PHPUnit unless the script requires that file first.
- **`assign_capability()` defaults to `$overwrite = false`** and does nothing when a row exists (for example the
  archetype's `CAP_ALLOW`), so a test of the denied path silently tests the allowed one. Pass `true`, clear the
  caches, and assert the gate flipped before testing it.

  ```php
  assign_capability('mod/myplugin:view', CAP_PROHIBIT, $roleid, $context->id, true);
  accesslib_clear_all_caches_for_unit_testing();
  $this->assertFalse(has_capability('mod/myplugin:view', $context, $user));
  ```

- **`block_<name>` classes are not autoloaded.** Load them first; `block_load_class()` requires both `block_base`
  and the block file.

  ```php
  require_once($CFG->libdir . '/blocklib.php');
  block_load_class('myplugin');
  $block = new \block_myplugin();
  $block->init();
  ```

- **Assorted traps:** `$cm->id` is a numeric string (use `assertEquals` or cast); `$PAGE->cm` is a magic property,
  so `empty($PAGE->cm)` is always true (read it into a variable first); `CLI_SCRIPT` is true under PHPUnit, so a
  CLI-only guard short-circuits every positive-path test, and a suite of only `assertFalse` then passes
  vacuously; your own observers (for example on `course_deleted`) may delete fixtures the test built.
- **Some module generators need a real user**: call `$this->setAdminUser()` before `create_module('workshop', ...)`
  ("No guests here!"). `mod_workshop` creates two grade items per instance, a ready multi-grade-item fixture.
- **Generators append modules to the end of a section.** To test another order, set `course_sections.sequence`
  and rebuild the cache.

  ```php
  $DB->set_field('course_sections', 'sequence', "$cm2,$cm1", ['id' => $sectionid]);
  rebuild_course_cache($course->id, true);
  ```

- **`route_testcase` group paths:** pass `''` as `$grouppath` to `add_class_routes_to_route_loader()` for a page
  route; `ROUTE_GROUP_PAGE` is `'/'` and builds a `//path` pattern that never matches (every expected-404 test
  then passes for the wrong reason), and `null` guesses from the namespace and throws "Unable to determine route
  path" for anything but an `api` class. Always include a 200 case. A route in the `''` group runs without the
  login and validation middleware the site attaches to page routes, so it does not test those
  (`public/lib/tests/classes/router/route_testcase.php`, `public/lib/classes/router.php`, read in 5.3.0).
- **`\core\task\grade_cron_task` locks nothing** in courses whose course grade item has `needsupdate = 1`. Call
  `grade_regrade_final_grades($courseid)` before running it in synthetic setups.
- **Derive expected timestamps independently** whenever DST, a timezone or a window boundary is involved, and paste
  the command into a comment. When a new test fails, first ask whether the test or the code is wrong: a
  hand-computed expectation leads to "fixing" correct code.

  ```php
  // python3 -c "from datetime import datetime; from zoneinfo import ZoneInfo;
  //   print(int(datetime(2026, 11, 3, 9, tzinfo=ZoneInfo('Europe/London')).timestamp()))"
  ```

- **Users made outside the generator** (for example `create_user_record()`) need firstname, lastname and required
  profile fields, or `require_login()` redirects every request to `/user/edit.php` and scripted POSTs return an
  innocent-looking 303.
- **Multilang in tests:** set `$SESSION->forcelang` after `setUser()` (which clears it); `force_current_language()`
  does nothing without an installed language pack.
- **Test helpers need full docblocks** (description, blank line, `@param`, `@return`); run phpcs and moodlecheck on
  test files too.
- **Core's `phpunit.xml.dist` sets `failOnWarning="true"`** (root of the Moodle tree, 5.3.0), so a run that "passes
  with warnings" is a failing run locally as well as in CI.
- **More PHPUnit traps with their own home:** the per-test transaction on PostgreSQL and SQL Server and
  `preventResetByRollback()`, `MODE_GENERAL` backups in tests, quiz attempt previews, `contextlist` ids as
  strings: `moodle-phpunit-testing`.

## Security regression tests

See also `moodle-security-audit` and `moodle-release-preflight`.

- **A security test is evidence only after you saw it fail with the fix reverted, for the right reason.** Build the
  fixture from the columns the renderer actually reads, and assert the exact sink position with its surrounding
  markup, not a page-wide substring that an escaped attribute next door can satisfy.

  ```php
  $this->assertStringContainsString('>' . s($payload) . '</option>', $html);
  ```

- **Negative tests assert the specific error**, not just "rejected": a forged backup rejected as malformed proves
  nothing about the check under test.
- **Probe escaping with an entity payload** (`Theo &amp;`) too, since names are tag-stripped on save (`moodle-release-preflight`).

## Behat and browser automation

See also `moodle-behat-testing`.

- **Gradebook navigation:** the action-bar selector is a `li[role=option][data-value]` listbox with no anchors. Use
  core's step with `@javascript`: `And I navigate to "Setup > Gradebook setup" in the course gradebook`.
- **`I navigate to "A > B" in site administration` does not fail on an ambiguous path**; two plugins' "General
  settings" pages collide. Navigate to your plugin's category, then follow the page link.
- **Generator-created rich-text activities** need an explicit HTML format (for example `contentformat` 1) for
  TinyMCE to attach.
- **Run local Behat with `--scss-deprecations`** as CI does; Bootstrap 4 class names fail there even on core steps
  that merely visit the page.
- **Checkboxes outside a moodleform** (Mustache bulk-select tables) need the HTML5 `form="<formid>"` attribute on
  each input; in non-JS Behat, check the field rather than clicking it.
- **Browser automation (Playwright and similar):** wait for network idle before filling a password field (core's
  `togglesensitive` module replaces the input via `outerHTML`, discarding early input) and assert the value before
  submitting. Select buttons by role and name (submit buttons are never unique on a Moodle page); read
  `getAttribute('action')`, not `form.action` (shadowed by a hidden input named `action`); quiz answer radios have
  no `label[for]`.
- **Playwright's `click()` and `fill()` scroll the target clear first**, so they pass on a control a person cannot
  click. On 5.3 activity pages a fixed activity-navigation footer (about 65 px, `.course-linear-navigation`) covers
  the bottom of the window and dropdown menus under it; Boost's fixed navbar covers the top. Check each control
  with `document.elementFromPoint()` at its centre, without scrolling and after the page's own initial scroll, on
  5.3 (5.2 has no footer).
- **A voice feature tested with a fake microphone file never hears itself.** Chromium's
  `--use-file-for-fake-audio-capture=<wav>%noloop` feeds a file; also run with the page's audio output looped back
  into `getUserMedia` (an init script that tees `AudioNode.connect` to the destination into a
  `MediaStreamDestination`). An echo-only run must not trigger barge-in or a turn.
- **A form-decorating plugin is tested on a Moodle with only standard plugins** as well as on your development
  site: other installed plugins add fields, hooks and JS that hide or cause failures.

## CI false greens

See also `moodle-ci-matrix` and `moodle-definition-of-done`.

- **Derive every matrix cell** (Moodle x PHP x DB) from each branch's `public/admin/environment.xml`; never cross
  current PHP or database versions with old branches. Check service images, `include` entries missing axes, and
  artifact-name characters.
- **Vacuous passes:** an empty `tests/` passes phpunit and behat; `phpmd` exits 0 with violations; `mustache`
  needs an `Example context (json):` block per template; `.mustachelintignore` silences only HTML validation;
  `grunt --force` hides eslint failures and stale builds.
- **CI's coding standard lags upstream.** moodle-plugin-ci 4.5.11 locks moodle-cs v3.7.0; v3.9 adds a warning for
  `$CFG->admin` and `$CFG->httpswwwroot` and makes `@codingStandards*` tags an error. A plugin green today fails
  on the moodle-plugin-ci release that updates the lock: remove both now (`moodle-definition-of-done`,
  `reference/ci-gates.md`).
- **No `error_log()` in best-effort catch blocks** (a forbidden function in the coding standard). Treat
  "Unexpected debugging() call" or deprecation notices in a green run as findings; `--fail-on-warning` will fail
  them on the next branch.
- **A local MySQL or MariaDB run says nothing about PostgreSQL** (per-test transactions, cursors, stricter casts):
  treat a PostgreSQL-sensitive assertion as unverified until that CI row has run.

## References

- https://moodledev.io/general/development/tools/phpunit
- https://moodledev.io/general/development/tools/behat
- https://moodledev.io/general/development/tools/nodejs#grunt
