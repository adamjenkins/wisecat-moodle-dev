# Generators and fixtures

Read this when you write a plugin data generator, create activities, quiz attempts, enrolments or users for a test,
change module order, or back up and restore a course inside a test.

Sources are the 5.2 and 5.3.0 trees, paths relative to the Moodle root; "seen in practice" marks behaviour observed
on real plugins.

## Plugin generator

`tests/generator/lib.php`, class `<component>_generator`, extending one of the bases in
`public/lib/testing/generator/`: `component_generator_base` (any plugin), `testing_module_generator` (activities),
`testing_block_generator` (blocks). Behat's `the following "<component> > <entity>" exist:` step reaches the same
`create_*()` methods through a second class, `tests/generator/behat_<component>_generator.php`, which maps entity
names to them (`moodle-behat-testing`).

```php
<?php
// (GPL header)

/**
 * Data generator for local_example.
 *
 * @package    local_example
 * @category   test
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class local_example_generator extends component_generator_base {
    /** @var int Number of items created, for unique default names. */
    protected int $itemcount = 0;

    #[\Override]
    public function reset() {
        $this->itemcount = 0;
        parent::reset();
    }

    /**
     * Create an item.
     *
     * @param array $record Field values; defaults fill the rest.
     * @return \stdClass The stored record.
     */
    public function create_item(array $record = []): \stdClass {
        global $DB, $USER;
        $this->itemcount++;
        $record = (object) array_merge([
            'courseid' => 0,
            'userid' => $USER->id,
            'name' => 'Item ' . $this->itemcount,
            'timecreated' => \core\di::get(\core\clock::class)->time(),
        ], $record);
        $record->id = $DB->insert_record('local_example_items', $record);
        return $record;
    }
}
```

```php
$item = $this->getDataGenerator()->get_plugin_generator('local_example')->create_item(['name' => 'First']);
```

- Write through the plugin's own API when one exists (the manager class, not `insert_record()`), so the generator
  exercises the same code and events as production.
- A generator that needs other files (`require_once($CFG->dirroot . '/mod/example/locallib.php')`) requires them
  itself; the Behat process loads it without the PHPUnit bootstrap.

## Activity modules

- `testing_module_generator::create_instance()` calls `add_moduleinfo()` (`public/lib/testing/generator/module_generator.php`,
  5.2 and 5.3), which runs `edit_module_post_actions()`. What it does not do: build or validate the module's
  `mod_form`, run `data_preprocessing()` or `data_postprocessing()`, or take the update path. Symptom: create works
  in tests, while editing an existing activity, or creating one through the form, fails on the site. Fix: test
  updates through `update_moduleinfo()` with data shaped like the form's, and drive the real form once in Behat.
  The generator also passes `intro`/`introformat`; a real form post uses `introeditor` (`['text' => ..., 'format' =>
  FORMAT_HTML, 'itemid' => $draftid]`). Seen in practice.
- **Some module generators need a logged-in user.** The workshop generator calls `file_get_unused_draft_itemid()`
  (`public/mod/workshop/tests/generator/lib.php`), which throws `noguest` ("No guests here!") for the guest and
  for the not-logged-in user a test starts with. Fix: `$this->setAdminUser()` or `setUser()` before
  `create_module('workshop', ...)`. A workshop instance has two grade items, a ready fixture for multi-grade-item
  code.
- **Generators append modules to the end of a section.** To test another order, set the sequence and rebuild:

  ```php
  $DB->set_field('course_sections', 'sequence', "{$cm2->cmid},{$cm1->cmid}", ['id' => $sectionid]);
  rebuild_course_cache($course->id, true);
  ```

- **Completion on a generated module needs completion enabled** site-wide (`$CFG->enablecompletion`) and on the
  course (`create_course(['enablecompletion' => 1])`), or the generator emits a debugging() message that fails the
  run (`module_generator.php`, "Did you forget to set $CFG->enablecompletion").

## Users, roles and enrolments

- `create_user()` fills the name fields and required profile data. A user made another way (for example
  `create_user_record()`) without first name, last name or a required custom profile field is sent to
  `/user/edit.php` by every `require_login()`, so scripted requests get a 303 that looks harmless. Seen in practice.
- `getDataGenerator()->enrol_user()` uses the course's single enrolment instance of that method and returns `false`
  without an error when there is none or more than one (`data_generator.php`, `enrol_user()`). Assert its return
  value when the course was not made by `create_course()`.
- A capability override in a test must actually change something: `assign_capability()` does nothing when a row
  already exists unless its fifth argument `$overwrite` is `true`. Assert the gate flipped before testing it.

## Quiz attempts

- `mod_quiz_generator::create_attempt($quizid, $userid)` does not pass `$userid` on to
  `quiz_prepare_and_start_new_attempt()` (`public/mod/quiz/tests/generator/lib.php`, 5.3.0), so the attempt belongs
  to the current `$USER` and is a preview when that user can preview the quiz. Previews are ignored by
  `quiz_has_attempts()` (`public/mod/quiz/locallib.php`) and by reports. Symptom: "the attempt exists but the
  report or lock does not see it". Fix: `$this->setUser($student)` around `create_attempt()` and
  `submit_responses()`, then switch back. Seen in practice.
- Questions for the quiz go into a question bank you chose explicitly, normally a `mod_qbank` instance created in the
  course (`create_module('qbank', ['course' => $course->id])`), not the site-level shared bank.

## Grades

- `\core\task\grade_cron_task` (it locks grade items and grades whose lock time has passed) skips every course whose
  course grade item has `needsupdate = 1` (`public/lib/classes/task/grade_cron_task.php`). In a synthetic setup,
  call `grade_regrade_final_grades($course->id)` before running it. Seen in practice.
- `get_gradable_users()` throws `gradesneedregrading` while a regrade is pending (`graded_users_iterator::init()`
  calls `export_verify_grades()`, `public/grade/lib.php`); regrade first in tests that call it.

## Blocks

`block_<name>` classes are not autoloaded:

```php
require_once($CFG->libdir . '/blocklib.php');
block_load_class('example');
$block = new \block_example();
$block->init();
```

## Backup and restore inside a test

- **A `backup::MODE_GENERAL` backup is zipped and its temporary directory removed.** Restoring from the backup id then
  fails (the plan is null). Fix: extract the stored file with core's packer, then restore from that directory, as
  core's own tests do (`public/lib/tests/questionlib_test.php`, 5.3.0):

  ```php
  $bc = new \backup_controller(\backup::TYPE_1COURSE, $course->id, \backup::FORMAT_MOODLE,
      \backup::INTERACTIVE_NO, \backup::MODE_GENERAL, $USER->id);
  $bc->execute_plan();
  $file = $bc->get_results()['backup_destination'];
  $file->extract_to_pathname(get_file_packer('application/vnd.moodle.backup'),
      $CFG->tempdir . '/backup/test-restore');
  $bc->destroy();

  $newcourseid = \restore_dbops::create_new_course('Restored', 'R1', $course->category);
  $rc = new \restore_controller('test-restore', $newcourseid, \backup::INTERACTIVE_NO,
      \backup::MODE_GENERAL, $USER->id, \backup::TARGET_NEW_COURSE);
  $this->assertTrue($rc->execute_precheck());
  $rc->execute_plan();
  $rc->destroy();
  ```

  `backup::MODE_IMPORT` keeps the unzipped directory, so a restore can use `$bc->get_backupid()` directly, but it
  skips user data and some plugin steps; use it only when that is what you test.
- **`restore_dbops::create_new_course()` creates no enrolment instances.** `enrol_user()` then returns `false` and
  the user is never enrolled. Fix: `role_assign($roleid, $user->id, \context_course::instance($newcourseid))`, or
  add a manual instance first. Seen in practice.
- Repack an `.mbz` fixture only with `get_file_packer('application/vnd.moodle.backup')`. Core writes a gzip tar
  unless `$CFG->usezipbackups` is set (`public/lib/filestorage/mbz_packer.php`, 5.3.0); a hand-made archive with a
  different layout or root folder fails restore in ways that look like a bug in your restore code.
- Assert the end state after restore (`visible`, dates, settings of the target course): a restore overwrites target
  course settings, and dates are shifted by a fixed number of seconds.
