# Behat generators, custom steps and selectors

Read this when you add a Behat data generator entity, a custom step definition, a named selector or a page
resolver, or need to know which built-in steps and selectors exist.

Sources are the 5.2 and 5.3.0 trees, paths relative to the Moodle root, read and not run for this file unless a line
says "seen in practice".

## Data generator entities

The step `the following "<component> > <entity>" exist:` loads
`<plugin>/tests/generator/behat_<component>_generator.php` (`public/lib/tests/behat/behat_data_generators.php`,
5.2 and 5.3). The class there is the only place an entity is declared; a `get_creatable_entities()` method in
`tests/behat/behat_<component>.php` is never called.

```php
<?php
// (GPL header)

/**
 * Behat data generator for local_example.
 *
 * @package    local_example
 * @category   test
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
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

    /**
     * Look up an item id by its name, for 'switchids' => ['item' => 'itemid'] in other entities.
     *
     * @param string $name Item name as written in the feature.
     * @return int
     */
    protected function get_item_id(string $name): int {
        global $DB;
        return (int) $DB->get_field('local_example_items', 'id', ['name' => $name], MUST_EXIST);
    }
}
```

```gherkin
    And the following "local_example > items" exist:
      | name       | course | user     |
      | First item | M101   | student1 |
    And the following "local_example > item" exists:
      | name   | Second item |
      | course | M101        |
```

What happens to each row (`generate_items()` in `public/lib/behat/classes/behat_generator_base.php`, 5.3.0):

1. Every column in `required` must be present, or the step throws "requires the field ... to be specified".
2. Each `switchids` column present in the row is passed to `get_<column>_id()` on the generator class and replaced
   by the target field. The base class has `get_course_id()` (short name), `get_user_id()` (username),
   `get_activity_id()` (idnumber), `get_group_id()` (idnumber), `get_category_id()` (idnumber), `get_role_id()`
   (short name) and more. A missing method throws a `coding_exception` naming it.
3. `preprocess_<datagenerator>($row)` on the Behat generator, if defined, can rewrite the row.
4. The record is created by the first that exists: `process_<datagenerator>()` on the Behat generator, then
   `create_<datagenerator>()` on the PHPUnit generator `local_example_generator`, then on the core generator.
5. `finish_generate_<datagenerator>()` on the PHPUnit generator runs once after all rows.

- **Every value arrives as a string**, and the row is an array, not an object. The PHPUnit generator's
  `create_item(array $record)` receives `['name' => 'First item', 'courseid' => 5, 'userid' => 7]`; cast where the
  code is strict.
- The PHPUnit generator is loaded in a Behat process without the PHPUnit bootstrap, so it requires its own
  dependencies (`require_once($CFG->dirroot . '/local/example/locallib.php')`).
- A new entity, or a new file, is unknown until Behat is initialised again (see the main file).
- **Rich text needs a format column.** A generator row with `intro` or `content` and no format can leave TinyMCE
  unattached in JavaScript scenarios. Pass `| introformat | 1 |` (`FORMAT_HTML`). Seen in practice.
- Generators skip the form: data created this way never runs `mod_form` validation or the editor's draft file
  handling. Keep at least one scenario that goes through the real form.

## Custom step definitions

`tests/behat/behat_local_example.php`, class `behat_local_example` (exactly `behat_<component>`), extending
`behat_base`. The file can be loaded before `config.php`, so it has no `MOODLE_INTERNAL` check and requires the base
class by relative path, as core plugins do (`public/mod/forum/tests/behat/behat_mod_forum.php`):

```php
<?php
// (GPL header)

// NOTE: no MOODLE_INTERNAL test here, this file may be required by behat before including /config.php.

require_once(__DIR__ . '/../../../../lib/behat/behat_base.php');

use Behat\Mink\Exception\ExpectationException;

/**
 * Steps for local_example.
 *
 * @package    local_example
 * @category   test
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class behat_local_example extends behat_base {
    /**
     * Check how many items a course holds.
     *
     * @Then /^the course "(?P<shortname_string>(?:[^"]|\\")*)" should have "(?P<count_number>\d+)" items$/
     * @param string $shortname
     * @param int $count
     */
    public function the_course_should_have_items(string $shortname, int $count): void {
        global $DB;
        $courseid = $DB->get_field('course', 'id', ['shortname' => $shortname], MUST_EXIST);
        $actual = $DB->count_records('local_example_items', ['courseid' => $courseid]);
        if ($actual !== $count) {
            throw new ExpectationException("Expected {$count} items, found {$actual}", $this->getSession());
        }
    }
}
```

- The path `../../../../lib` counts from `<plugin>/tests/behat/` to the web root: `local/example/tests/behat` is four
  levels below `public/`. A plugin type nested deeper (`mod/assign/submission/x`) needs more `../`.
- Prefer composing core steps with `$this->execute('behat_forms::press_button', get_string('savechanges'))` to
  re-implementing them; `execute()` keeps the waits and exception checks of the core step.
- A step that reads the database sees committed data only: it runs in the Behat process, not in the browser's
  request. Data the page has just saved is visible once the page has reloaded.
- Reset static caches between scenarios with a hook, as `behat_mod_forum::reset_forum_caches()` does:
  `/** @BeforeScenario @local_example */ public function reset_caches(): void { ... }`.
- Put steps that change site state behind `Given`, assertions behind `Then`; Moodle's step list
  (`admin/tool/behat/index.php` on a Behat-enabled site) shows them grouped that way.

## Page resolvers

Give `I am on the "<identifier>" "<component> > <page type>" page` (and `... logged in as "<user>"`) a URL for your
pages, instead of clicking through navigation (`public/lib/tests/behat/behat_navigation.php`, `parse_page_name()`
and `resolve_page_instance_helper()`, 5.3.0):

```php
    /**
     * Convert page names to URLs for 'I am on the "[identifier]" "local_example > [page type]" page'.
     *
     * @param string $type Page type, for example 'View'.
     * @param string $identifier Item name.
     * @return moodle_url
     */
    protected function resolve_page_instance_url(string $type, string $identifier): moodle_url {
        global $DB;
        switch (strtolower($type)) {
            case 'view':
                $id = $DB->get_field('local_example_items', 'id', ['name' => $identifier], MUST_EXIST);
                return new moodle_url('/local/example/view.php', ['id' => $id]);
            default:
                throw new Exception('Unrecognised local_example page type "' . $type . '."');
        }
    }
```

```gherkin
    Given I am on the "First item" "local_example > View" page logged in as "teacher1"
```

`resolve_page_url(string $page)` does the same for pages without an instance (`I am on the "local_example >
Overview" page`). Writing `core > ...` is an error: core pages take no prefix.

## Named selectors

A selector for your own widgets, used as `"<locator>" "local_example > <alias>"`, comes from
`get_partial_named_selectors()` or `get_exact_named_selectors()` on the step class, returning
`behat_component_named_selector` objects (`public/lib/behat/classes/component_named_selector.php`):

```php
    /**
     * Return the list of partial named selectors.
     *
     * @return behat_component_named_selector[]
     */
    public static function get_partial_named_selectors(): array {
        return [
            new behat_component_named_selector('Item card', [
                ".//*[@data-region='local_example-item'][contains(., %locator%)]",
            ]),
        ];
    }
```

```gherkin
    Then I should see "Due tomorrow" in the "First item" "local_example > Item card"
```

## Built-in selectors

| Selector | Matches | Example |
|---|---|---|
| `link` | `<a>` by text, title or id | `I click on "Settings" "link"` |
| `button` | buttons and submit inputs by text or value | `I click on "Save changes" "button"` |
| `field` | form control by id, name, `<label>` text or placeholder (not `aria-label`) | `I set the field "id_name" to "X"` |
| `checkbox`, `radio`, `select` | that control type, same locators as `field` | `I click on "Visible" "checkbox"` |
| `table_row` | `<tr>` containing the text | `... in the "Sam Student" "table_row"` |
| `table` | table by id, class or caption | `the following should exist in the "items" table:` |
| `fieldset` | a form section by legend | `... in the "General" "fieldset"` |
| `region` | element by id, for example `region-main` | `... in the "region-main" "region"` |
| `block` | a block by title or instance name | `... in the "Calendar" "block"` |
| `dialogue` | a modal or YUI dialogue by title | `... in the "Delete item" "dialogue"` |
| `section` | a course section by name | `... in the "Topic 1" "section"` |
| `activity` | an activity on the course page by name | `... in the "Quiz 1" "activity"` |
| `list_item`, `icon`, `text` | as named | `... "Edit" "icon"` |
| `css_element`, `xpath_element` | raw selectors, last resort | `I click on "[data-action='mark']" "css_element"` |

The full list is in `public/lib/behat/classes/partial_named_selector.php` (5.2 and 5.3). Prefer a named selector
to `css_element`: class names change between branches (see the 5.3 version notes), names and labels rarely do.

## Built-in steps worth knowing

```gherkin
    Given I am on the "M101" "Course" page logged in as "teacher1"
    And I am on the "Quiz 1" "mod_quiz > View" page
    And I navigate to "Settings" in current page administration
    And I navigate to "Plugins > Local plugins > Example" in site administration
    And I navigate to "Setup > Gradebook setup" in the course gradebook
    And I wait until the page is ready
    And I wait until "Saved" "text" exists
    And I wait until "Loading" "text" does not exist
    And I run the scheduled task "\local_example\task\cleanup"
    And I run all adhoc tasks
    And the following config values are set as admin:
      | enabled  | 1   | local_example |
      | maxitems | 10  | local_example |
    And I press the escape key
    And I change window size to "mobile"
    Then "Mark present" "button" should exist in the "Sam Student" "table_row"
    And the following should exist in the "items" table:
      | Name       | Owner       |
      | First item | Sam Student |
```

- **`the following config values are set as admin:` has no header row.** Each row is `| name | value |` or
  `| name | value | plugin |` (`getRowsHash()` in `public/admin/tests/behat/behat_admin.php`, 5.2 and 5.3). A first
  row `| config | value | plugin |` sets a setting called `config` in a plugin called `plugin` and is silently
  accepted.
- **Gradebook pages** are reached through a listbox of `li[role=option]` items, not links; `I follow` cannot open
  them. Use `I navigate to "..." in the course gradebook` in a `@javascript` scenario
  (`public/grade/tests/behat/behat_grade.php`).
- **Checkboxes outside a moodleform**, for example in a Mustache bulk-action table, are only submitted when each
  input carries the HTML5 `form="<formid>"` attribute or sits inside the `<form>`. In a scenario without
  `@javascript`, set the field (`I set the field "item-5" to "1"`) instead of clicking it. Seen in practice.
- `I wait "N" seconds` is the last resort: it is slow and still races. Wait for the element or text that proves the
  JavaScript finished.
- Use `I am on the "..." "..." page logged in as "..."` rather than `I log in as` followed by navigation: it goes
  straight to the page without loading the dashboard first.
