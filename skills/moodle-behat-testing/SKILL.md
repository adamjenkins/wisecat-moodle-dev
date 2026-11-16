---
name: moodle-behat-testing
description: Use when writing, running or debugging Behat acceptance tests for a Moodle plugin - tests/behat/*.feature, behat_<component>.php step definitions, tests/generator/behat_<component>_generator.php and the "the following ... exist" step, public/admin/tool/behat/cli/init.php and run.php, @javascript scenarios, --scss-deprecations, "Deprecated style in use", "Deprecated styles found", gherkinlint failures in moodle-plugin-ci grunt, "I set the field" matching the wrong field, "I should not see" passing for the wrong reason, a new feature or step not being picked up, faildumps, or user tours blocking clicks. Covers the Behat site's mental model, the default feature and step recipe, and locator and assertion traps. Skip when testing business logic without a browser (moodle-phpunit-testing), building the CI workflow (moodle-ci-matrix), writing or fixing the axe accessibility steps (moodle-accessibility), or running a theme's own suite (moodle-theme-testing-release).
---

# Moodle Behat testing

## Overview

Behat drives a browser, or the BrowserKit driver for scenarios without `@javascript`, against a second Moodle site
built for testing. Features live in `<plugin>/tests/behat/*.feature`; custom steps in
`tests/behat/behat_<component>.php`. Most failures that waste time are not in the scenario: the run used a stale copy,
a locator matched another field, or a negative step passed because the text was never going to be on the page.

How sure each statement is: rules marked "seen in practice" were observed on real plugins and themes; everything
else was read in the 5.2 and 5.3.0 source (paths relative to the Moodle root) and not run for this skill.

## When to Use

- Writing a feature for a plugin's UI, forms, JavaScript, permissions or navigation
- Adding a Behat data generator or custom step
- A scenario passes locally and fails in CI, or the other way round
- A step matches the wrong element, a negative step passes vacuously, or a change is not picked up
- **Skip when:** testing logic without a browser (`moodle-phpunit-testing`), building the CI workflow
  (`moodle-ci-matrix`), or testing a theme's own suite, overrides and `blacklist.json`
  (`moodle-theme-testing-release`).

## Mental model

1. **A separate site.** `$CFG->behat_wwwroot`, `$CFG->behat_prefix` and `$CFG->behat_dataroot` in `config.php` define
   it (`config-dist.php`). `init.php` installs it and writes the Behat config (`behat.yml`) listing every feature
   and context class found in the Moodle tree. Never edit `behat.yml`; it is regenerated.
2. **The run reads the Moodle tree, not your repository.** Behat executes the copy of the plugin installed under the
   Moodle root. A new `.feature` file, a new `behat_*.php` context, or a new generator entity is unknown until
   `init.php` (or `util.php --enable`) runs again. Behat also caches each parsed feature and reuses the parse while
   the cache entry is newer than the feature file (`FileCache::isFresh()` in `vendor/behat/gherkin`), so a copy that
   keeps old timestamps can run the old scenario; `touch` the copied features. Seen in practice.
3. **Run options are fixed at init.** `init.php --scss-deprecations`, `--no-axe`, `--no-icon-deprecations` and
   (**5.3+:**) `--colourmode=dark` are stored for the site; `run.php` has no such options. The run header prints them
   under "Run optional tests:" (`public/lib/behat/classes/util.php`, 5.2 and 5.3). Read that banner before trusting
   a run.
4. **Suites follow themes.** The default theme's suite is `default`; every other installed theme gets a suite named
   after it holding only that theme's features (`public/lib/behat/classes/behat_config_util.php`). A plugin's
   features run in `default`.
5. **Each scenario starts from a fresh site.** Data comes from `Background` generator steps, not from earlier
   scenarios. Theme CSS is prebuilt at init and restored per scenario, so a changed SCSS or `styles.css` needs a
   re-init too.

## Setup and running

From the Moodle root (5.1 and later keep `admin/tool/behat` under `public/`):

```bash
php public/admin/tool/behat/cli/init.php --scss-deprecations          # as CI runs it
php public/admin/tool/behat/cli/run.php --tags=@local_example          # the plugin's features
php public/admin/tool/behat/cli/run.php --tags=@local_example --name="Teacher marks a student present"
php public/admin/tool/behat/cli/init.php --parallel=3 && php public/admin/tool/behat/cli/run.php --tags=@local_example
```

- `@javascript` scenarios need a WebDriver server (Selenium, or chromedriver/geckodriver) at the address in
  `$CFG->behat_profiles` or the default `localhost:4444`.
- **Run local Behat with `--scss-deprecations`, as `moodle-plugin-ci behat --scss-deprecations` does in the standard
  workflow.** With it, every step of a JavaScript scenario fails when any element on the page shows a Bootstrap 4
  compatibility class such as `.sr-only`, `.mr-2`, `.ml-auto` or `.font-weight-bold` ("Deprecated style in use",
  `look_for_deprecated_styles()` in `public/lib/behat/classes/behat_session_trait.php`; the class list is
  `public/theme/boost/scss/moodle/bs4-compat.scss`, 5.2 and 5.3), including markup your JavaScript builds and core
  steps that only visit your page. Fix: Bootstrap 5 names (`visually-hidden`, `me-2`, `ms-auto`, `fw-bold`). Seen
  in practice on 5.2 and 5.3. `run.php` hands options it does not know to Behat, so `--scss-deprecations` given
  to `run.php` fails with "option does not exist".
- **Compare the scenario count with the repository.** Before reading a result, check the summary's scenario count
  against `grep -c '^ *Scenario' tests/behat/*.feature`. A lower count means a stale or missing copy. Seen in
  practice.

## The default feature

```gherkin
@local @local_example
Feature: Mark attendance
  In order to track presence
  As a teacher
  I need to mark students present

  Background:
    Given the following "courses" exist:
      | fullname | shortname |
      | Maths    | M101      |
    And the following "users" exist:
      | username | firstname | lastname |
      | teacher1 | Tina      | Teach    |
      | student1 | Sam       | Student  |
    And the following "course enrolments" exist:
      | user     | course | role           |
      | teacher1 | M101   | editingteacher |
      | student1 | M101   | student        |

  @javascript
  Scenario: Teacher marks a student present
    Given I am on the "M101" "Course" page logged in as "teacher1"
    When I click on "Mark present" "button" in the "Sam Student" "table_row"
    Then I should see "1 present" in the "Today" "region"
    And I should not see "0 present" in the "Today" "region"
```

- **Tags.** `moodle-plugin-ci validate` requires both `@<plugintype>` and `@<component>` on every feature
  (`@local @local_example`; `@mod @mod_example`; `@theme @theme_example`). `@javascript` selects a real browser.
  `@_file_upload`, `@_switch_window` and `@_alert` mark scenarios that need those browser features.
- **Shape that gherkinlint enforces** (core `.gherkin-lintrc`, run by `moodle-plugin-ci grunt`): Feature at column
  0, Background and Scenario at 2, steps at 4, `Examples` at 4, example rows at 6; no trailing spaces; no two empty
  lines in a row; a newline at the end of the file; no duplicate feature names; no file without scenarios. A blank
  line after the last step fails as "Multiple empty lines are not allowed": the linter splits on newlines, so the
  blank line and the final newline count as two empty lines (`no-multiple-empty-lines` in gherkin-lint 4.2.2, read
  in its source, not run).
- **One scenario, one claim, proved in both directions** (see the rules below). Prefer `I am on the "<identifier>"
  "<type>" page logged in as "<user>"` to clicking through navigation.

## Data generators and custom steps

Plugin entities for `the following "local_example > items" exist:` come from a Behat generator next to the PHPUnit
one, `tests/generator/behat_local_example_generator.php`, which reuses the PHPUnit generator's `create_item()`:

```php
class behat_local_example_generator extends behat_generator_base {
    #[\Override]
    protected function get_creatable_entities(): array {
        return [
            'items' => [
                'singular' => 'item',
                'datagenerator' => 'item',
                'required' => ['name'],
                'switchids' => ['course' => 'courseid', 'user' => 'userid'],
            ],
        ];
    }
}
```

`switchids` turns a `course` column (shortname) and a `user` column (username) into ids through `get_course_id()`
and `get_user_id()` of `behat_generator_base` (`public/lib/behat/classes/behat_generator_base.php`). Custom steps go
in `tests/behat/behat_local_example.php`, class `behat_local_example extends behat_base`. The full step template,
page resolvers and named selectors are in [reference/generators-and-steps.md](reference/generators-and-steps.md).

## Rules for locating and asserting

Each was seen in practice on shipped plugins.

- **`I set the field "X"` matches any field whose label contains X.** "Name" also matches "Short name" and "Name
  display". Fix: use the element id, `I set the field "id_name" to "Maths"`, or a scoped form
  `I set the field "Name" in the "General" "fieldset" to "Maths"`.
- **Field locators match id, name, `<label>` text and placeholder, not `aria-label`.** A row checkbox with only an
  `aria-label` cannot be set. Fix in the template: give it an id and an `accesshide` label:
  `<input type="checkbox" id="item-{{id}}" name="items[]" value="{{id}}"><label for="item-{{id}}" class="accesshide">{{name}}</label>`.
- **A page-wide "I should not see" also reads the course index, block drawer and navigation.** An activity name
  that you expect to be gone from the table is still in the course index, so the step fails; text that never renders
  anywhere makes it pass for nothing. Fix: scope it to the container that would hold the text,
  `I should not see "Quiz 2" in the "Student One" "table_row"` or `... in the "region-main" "region"`, and pair it
  with a positive step in the same container so the container is known to exist.
- **Submit buttons are never unique on a Moodle page.** The page header, a block or a modal can hold another
  "Save changes". Fix: `I press "Save changes"` only when it is the single one; otherwise scope it,
  `I click on "Save changes" "button" in the "Edit item" "dialogue"`.
- **Every "I should see" for a mode needs "I should not see" for the other modes.** A setting with three modes
  gets, per mode, positive steps for that mode's fields and negative steps for the other two. Without them a form
  that shows every field in every mode passes.
- **Assert what only the success state shows.** A heading or message that also appears on the failure page, or a URL
  change that differs only by `#fragment` (which does not reload), proves nothing. Fix: assert a marker unique to the
  destination, such as the saved value in the table or a success notification.
- **Restriction and availability texts differ per condition.** A date condition in the past says "Available until
  <date>", not "Not available unless". Fix: copy the expected text from the condition's lang string or the page,
  never from memory.
- **Generator-created rich text needs an HTML format.** An activity created with `intro` and no format, or a text
  field with `FORMAT_MOODLE`, can stop TinyMCE attaching in JavaScript scenarios. Fix: pass the format column,
  for example `| introformat | 1 |`.
- **TinyMCE writes to the hidden `name[text]` textarea only on submit.** A step or script that reads the textarea
  before submitting reads the old value; code that submits a form from JavaScript must call
  `notifyFormSubmittedByJavascript()` from `core_form/events` first (`moodle-amd-javascript`).
- **formslib puts a radio's class on its label, and `:checked` does not see JavaScript-set state.** Select the radio
  by its id, assert with `the field "id_mode_2" matches value "1"`, not a CSS `:checked` selector. A drop or paste
  scenario that passes while real users get an empty file usually means the code read the `File` after the event
  handler returned, when the browser has already emptied the `DataTransfer`; read it inside the handler
  (`moodle-amd-javascript`).
- **`I navigate to "A > B" in site administration` does not fail on an ambiguous path.** Two plugins with a "General
  settings" page collide and the step opens the other one. Fix: navigate to your category, then follow your page.
- **Read the failure dump first.** Set `$CFG->behat_faildump_path`; the HTML and screenshot of the failing step
  usually show the cause (a debugging() message, a modal, the wrong page) faster than re-running.

## Environment facts that break scenarios

- **Site home is off on new installs.** `enablemyhome` defaults to 0 on 5.2 and 5.3
  (`public/admin/settings/appearance.php`), so `I am on site homepage` lands on the dashboard and logged-out users go
  to the login page (`public/index.php`). A feature that needs site home sets it in the Background, as core
  features do (`public/lib/tests/behat/switch_editing_mode.feature`, 5.3.0); add `defaulthomepage` 0 too when users
  must land on it after login:

  ```gherkin
    Background:
      Given the following config values are set as admin:
        | enablemyhome    | 1 |
        | defaulthomepage | 0 |
  ```

  Upgraded sites keep site home (an upgrade step sets `enablemyhome` to 1, `public/lib/db/upgrade.php`).
- **User tours cover the page on a user's first visit.** A tour's backdrop blocks clicks and screenshots. On a
  Behat site the shipped tours are installed disabled (`public/admin/tool/usertours/classes/manager.php`); in other
  browser automation, mark the tours complete for the test users first. Seen in practice.
- **Accessibility steps load axe from `/lib/behat/axe/axe.min.js`.** A web-server rule that denies paths containing
  `/behat/` (some hardened configurations do) makes every `the page should meet accessibility standards` step fail
  with "No data". Steps also need `@accessibility` and `@javascript`, and pass without checking anything when the
  site was initialised with `--no-axe`. Seen in practice. Accessibility rules: `moodle-accessibility`.
- **Boost puts the block drawer outside `#page`.** Selectors that scope to `#page` do not see blocks; use the
  `"block"` selector with the block title (`moodle-theme-layouts-templates` for page structure).
- **Add activities with core's step**, `I add an "assign" activity to course "M101" section "1"` (or `... and I
  fill the form with:`), rather than clicking the chooser. The first argument is the module name, not its display
  name; the step opens `course/modedit.php?add=assign` directly, and the course may be named by idnumber, short
  name or full name (`public/course/tests/behat/behat_course.php`, `behat_session_trait::get_course_id()`, 5.2 and
  5.3). A hand-written click path breaks: "Add an activity or resource" is a plain button in some places and an
  item inside the "Add content" dropdown in others (`hasactionlinks` in
  `public/course/format/templates/local/content/activitychooserbutton.mustache`), and that dropdown's button shows
  only an icon on 5.2 and an icon with the text on 5.3.
- **A debugging() message fails the step that showed it.** A deprecated API called by your page (for example
  `moveto_module()` on 5.2) fails Behat even though PHPUnit passed; fix the call (`moodle-upgrade-migration`).
- **A deprecated core step fails the scenario.** It throws "Deprecated step, rather than using this step you can:"
  unless `$CFG->behat_usedeprecated` is set (`public/lib/behat/behat_deprecated_base.php`, 5.2 and 5.3). Use the
  replacement it names; when the replacement does not exist on your lowest branch, write the step in your own
  context.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| New feature, step or generator entity, no re-init | "Undefined step", or the old scenario runs | `init.php` again; compare the scenario count |
| Local run without `--scss-deprecations` | Green locally, red in CI on Bootstrap 4 classes | `init.php --scss-deprecations`; read the banner |
| Missing `@<plugintype>` tag | `moodle-plugin-ci validate` fails | `@local @local_example` on every feature |
| Trailing blank line, trailing spaces or tab indentation in a feature | gherkinlint fails the `grunt` step | End the file with one newline right after the last step; indent with spaces |
| `I set the field "Name"` | Sets "Short name" or the wrong form | `id_<element>` or a scoped step |
| Page-wide `I should not see` | Fails on the course index, or passes for nothing | Scope to the container |
| Only positive steps for a mode switch | Every field shown in every mode passes | Negative steps for the other modes |
| `I wait "5" seconds` | Slow and still flaky | `I wait until the page is ready`, or a step that waits for an element |
| AJAX UI scenario without `@javascript` | BrowserKit cannot run the JavaScript | Tag `@javascript` |
| Generator entity defined in `behat_<component>.php` | "the following ... exist" does not know it | `tests/generator/behat_<component>_generator.php` |
| `get_string()` text copied by memory | Expected text never matches | Copy from the lang file or the page |
| Editing `behat.yml` | Lost on the next init | Change `config.php` or init options |
| `I press "Save changes"` with two such buttons on the page | Presses the wrong one, or the step is ambiguous | Scope it to the form, region or dialogue |
| `I am on site homepage` on a fresh 5.2 or 5.3 site | Lands on the dashboard or login page | Set `enablemyhome` 1 in the Background |
| Accessibility step without `@accessibility` | The step throws | Tag the scenario `@accessibility @javascript` |

## Reference files

| File | Read it when |
|---|---|
| [reference/generators-and-steps.md](reference/generators-and-steps.md) | You add a Behat data generator entity, a custom step definition or a named selector, or need to know which built-in steps and selectors exist |
| [reference/debugging-and-runs.md](reference/debugging-and-runs.md) | A run gives a result you do not trust: scenarios missing, a change not picked up, a failure only in CI, parallel runs, faildumps, or you drive Moodle with Playwright or a similar tool outside Behat |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

## References

- https://moodledev.io/general/development/tools/behat
- https://moodledev.io/general/development/tools/behat/writing
- https://moodledev.io/general/development/tools/behat/running
- https://moodledev.io/docs/apis/subsystems/testing/generators (Behat generators)
- `public/lib/behat/classes/behat_generator_base.php`, `public/lib/tests/behat/behat_general.php`,
  `public/lib/tests/behat/behat_forms.php` (5.2 and 5.3): the step and generator source
- Theme suites and overrides: `moodle-theme-testing-release`. CI workflow: `moodle-ci-matrix`.
