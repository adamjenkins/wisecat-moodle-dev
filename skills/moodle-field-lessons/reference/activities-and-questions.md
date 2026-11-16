# Activity modules, grades, the question engine and availability conditions

Read this when writing an activity module's lifecycle callbacks or completion rules, creating modules or grading
from code, using the question engine outside `mod_quiz`, or writing an availability condition plugin.

The per-type file list and base classes are in `moodle-plugin-development`. Samples are valid on Moodle 5.2 and
5.3; source lines were read in 5.3.0 unless marked.

## Module lifecycle

- **Inside `<modname>_add_instance()` use `$data->coursemodule`**, never a lookup by instance: `add_moduleinfo()`
  sets `course_modules.instance` only after the callback returns, so `get_coursemodule_from_instance()` fails
  ("Can't find data record") and the creation rolls back (`public/course/modlib.php`, `add_moduleinfo()`).
- **Core's `create_module()` needs `introeditor`** (`['text' => ..., 'format' => FORMAT_HTML, 'itemid' => 0]`) for
  every module that supports `FEATURE_MOD_INTRO`, and throws `createmodulemissingattribut` without it; the test
  generator's `intro`/`introformat` fields do not apply there (`public/course/lib.php`, `create_module()`).
- **A module calendar event with a `groupid` is shown to that group's members only.** Core treats it as a group
  override: a teacher with `accessallgroups` who is not in the group gets only events whose `eventtype` is `group`
  (`public/calendar/classes/local/event/strategies/raw_event_retrieval_strategy.php`, read in 5.3.0). Give
  teachers another surface (the activity page, a report).
- **Declaring `FEATURE_COMPLETION_HAS_RULES` requires `classes/completion/custom_completion.php`**; test repeated
  and degenerate attempts (zero answers, a retake after completion), not only the happy path.
- **The module generator calls `add_moduleinfo()` but never builds the module's `mod_form`**
  (`public/lib/testing/generator/module_generator.php`, `create_instance()`, 5.2 and 5.3), so the form's
  `validation()`, `data_preprocessing()` and `data_postprocessing()`, and `update_moduleinfo()`, are untested by
  generator fixtures. Test create and update through the real form (a Behat scenario) as well.

## Grades and assignments from code

- **`assign::save_grade()` outside the grading form** needs `$data->attemptnumber = 0; $data->applytoall = 0;`
  (or the attempt you mean): it reads `$data->attemptnumber` to find the submission and the grade, so without it
  PHP warns about an undefined property and the lookup runs with `null`
  (`public/mod/assign/locallib.php`, `save_grade()`, read in 5.3.0).
- **`get_gradable_users()` throws `gradesneedregrading` while a regrade is pending** (`public/grade/lib.php`
  builds a `graded_users_iterator`, whose `init()` calls `export_verify_grades()`,
  `public/grade/export/lib.php:706-709`). Call `grade_regrade_final_grades($courseid)` first in code that runs
  right after changing grade items.

## The question engine outside mod_quiz

- **`process_all_actions()` without `slots` processes every slot the POST data names.** The data is client
  controlled, so a request can grade slots it was never shown. Filter the data to
  `$quba->get_field_prefix($slot)` and pass `slots`; a regression test posts a second slot's `:sequencecheck` and
  `-submit` and asserts it stayed untouched.

  ```php
  $prefix = $quba->get_field_prefix($slot);
  $postdata = array_filter($postdata, fn($k) => str_starts_with($k, $prefix), ARRAY_FILTER_USE_KEY);
  $postdata['slots'] = (string) $slot;
  $quba->process_all_actions(time(), $postdata);
  ```

- **Rendering a question off-page (AJAX, web service, fragment) has four traps:**
  1. The engine is not autoloaded: `require_once($CFG->dirroot . '/question/engine/lib.php');`. PHPUnit preloads it,
     so only a real request shows the fatal.
  2. Initialise the theme before collecting the question's JS: `$PAGE->start_collecting_javascript_requirements()`
     throws until `$PAGE->initialise_theme_and_output()` (or the header) has run, and it may be started only once
     per request (`public/lib/pagelib.php`).
  3. Put the rendered question inside a `<form>`: `render_question()` emits a `div`, and core's `core_form/submit`
     reads `button.form.dataset`, which throws on `null`. Give that form
     `data-double-submit-protection="off"` if it is submitted by JS.
  4. `$PAGE->requires->get_end_code()` returns `<script>` tags, while `Templates.replaceNodeContents()` wants raw
     JS: unwrap with `Fragment.processCollectedJavascript()`. `replaceNodeContents()` returns DOM nodes, not a
     promise.
- **Key long-lived question data on `questionbankentryid`**, never on a versioned question id: editing creates a
  new version and a new id, and backup maps the entry id (`annotate_ids('question_bank_entry', ...)`).
- **On a live site the quiz generator's `submit_responses()` throws** (it calls `quiz_attempt::get_question_usage()`,
  "only for use in unit tests", `public/mod/quiz/classes/quiz_attempt.php:874`). A script that simulates attempts
  builds the POST data per slot (`$qa->get_field_prefix()` plus `:sequencecheck` plus the answer variables, and
  `slots`), then calls `process_submitted_actions()`, `process_submit()` and `process_grade_submission()` on the
  `quiz_attempt`.
- **Questions created by plugin code go into a question bank chosen explicitly**: a `mod_qbank` instance the caller
  names or creates, never a fallback to the site-level shared bank.

## Availability conditions

- **`condition::is_available()` called outside `info::is_available()` throws** "info::get_modinfo available only
  during condition checking" for conditions that read modinfo, such as completion (`public/availability/classes/info.php:97-102`).
  `info::$modinfo` is protected and has no setter, so a plugin that evaluates single conditions subclasses
  `\core_availability\info_module` or `info_section`. Test with a completion condition; date, group and grade
  conditions never hit it.
- **On 5.2 and 5.3 the condition's form is a YUI module** `moodle-availability_<name>-form` in `yui/src/form/`, built
  with shifter; there is no AMD alternative (`public/availability/classes/frontend.php`).
- **Restore remaps ids only through `update_after_restore()`**; availability plugins get no backup structure hook.
- **The restriction text differs per condition and state** (a past "until" date reads "Available until ..."), so
  Behat steps copy it from the condition's lang string or a rendered page.

## References

- https://moodledev.io/docs/apis/plugintypes/mod
- https://moodledev.io/docs/apis/core/activitycompletion
- https://moodledev.io/docs/apis/subsystems/question
- https://moodledev.io/docs/apis/plugintypes/availability
