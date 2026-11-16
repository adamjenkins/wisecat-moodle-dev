# Testing a privacy provider

Read this when you are writing `tests/privacy/provider_test.php`, or need to run core's compliance checks against
the plugin before a release.

Two kinds of test matter, and they catch different defects:

| Test | Catches | Runs in the plugin's CI |
|---|---|---|
| The plugin's own `tests/privacy/provider_test.php` on generated rows | Request methods that miss a table, query an old table name, delete too much or too little | Yes |
| Core's `public/privacy/tests/privacy/provider_test.php` (group `plugin_checks`) | No provider, a metadata provider with no request interface, no userlist provider, missing strings, declared tables that do not exist, user tables not declared | No |

Facts below were read in the 5.3.0 source (the same on 5.2); the commands were not run.

## The plugin's own test

`\core_privacy\tests\provider_testcase` extends `advanced_testcase` and resets the writer in `tearDown()`. Its
helpers are `get_contexts_for_userid(int $userid, string $component)`,
`export_all_data_for_user(int $userid, string $component)` and
`export_context_data_for_user(int $userid, \context $context, string $component)`. It has no delete helpers
(`public/privacy/classes/tests/provider_testcase.php`). Under PHPUnit, `writer::with_context()` returns the test
writer, `\core_privacy\tests\request\content_writer`, which records instead of writing a ZIP
(`public/privacy/classes/local/request/writer.php`).

Cover all six methods, with two users so that over-deletion shows:

```php
// (GPL header)
namespace local_example\privacy;

use core_privacy\local\request\approved_userlist;
use core_privacy\local\request\userlist;
use core_privacy\local\request\writer;
use core_privacy\tests\provider_testcase;
use core_privacy\tests\request\approved_contextlist;

/**
 * @covers \local_example\privacy\provider
 */
final class provider_test extends provider_testcase {
    /** @var string */
    private const COMPONENT = 'local_example';

    private function add_item(int $courseid, int $userid): int {
        global $DB;
        return $DB->insert_record('local_example_items',
            ['courseid' => $courseid, 'userid' => $userid, 'content' => 'Text', 'timecreated' => time()]);
    }

    public function test_get_contexts_and_users(): void {
        $this->resetAfterTest();
        $course = $this->getDataGenerator()->create_course(['summary' => '']);
        $u1 = $this->getDataGenerator()->create_user();
        $u2 = $this->getDataGenerator()->create_user();
        $this->add_item($course->id, $u1->id);
        $context = \core\context\course::instance($course->id);

        $contextids = array_map('intval', provider::get_contexts_for_userid($u1->id)->get_contextids());
        $this->assertSame([$context->id], $contextids);                  // Strings without intval().
        $this->assertCount(0, provider::get_contexts_for_userid($u2->id));

        $userlist = new userlist($context, self::COMPONENT);
        provider::get_users_in_context($userlist);
        $this->assertEquals([$u1->id], $userlist->get_userids());
    }

    public function test_export_user_data(): void {
        $this->resetAfterTest();
        $course = $this->getDataGenerator()->create_course(['summary' => '']);
        $u1 = $this->getDataGenerator()->create_user();
        $itemid = $this->add_item($course->id, $u1->id);
        $context = \core\context\course::instance($course->id);

        $this->export_context_data_for_user($u1->id, $context, self::COMPONENT);

        $writer = writer::with_context($context);
        $this->assertTrue($writer->has_any_data());
        $data = $writer->get_data([get_string('pluginname', self::COMPONENT), $itemid]);
        $this->assertEquals('Text', $data->content);
    }

    public function test_delete_data_for_user_keeps_other_users(): void {
        global $DB;
        $this->resetAfterTest();
        $course = $this->getDataGenerator()->create_course(['summary' => '']);
        $u1 = $this->getDataGenerator()->create_user();
        $u2 = $this->getDataGenerator()->create_user();
        $this->add_item($course->id, $u1->id);
        $this->add_item($course->id, $u2->id);
        $context = \core\context\course::instance($course->id);

        provider::delete_data_for_user(new approved_contextlist($u1, self::COMPONENT, [$context->id]));

        $this->assertFalse($DB->record_exists('local_example_items', ['userid' => $u1->id]));
        $this->assertTrue($DB->record_exists('local_example_items', ['userid' => $u2->id]));
    }

    public function test_delete_data_for_users_and_context(): void {
        global $DB;
        $this->resetAfterTest();
        $course = $this->getDataGenerator()->create_course(['summary' => '']);
        $other = $this->getDataGenerator()->create_course(['summary' => '']);
        $u1 = $this->getDataGenerator()->create_user();
        $u2 = $this->getDataGenerator()->create_user();
        $this->add_item($course->id, $u1->id);
        $this->add_item($course->id, $u2->id);
        $this->add_item($other->id, $u1->id);
        $context = \core\context\course::instance($course->id);

        provider::delete_data_for_users(new approved_userlist($context, self::COMPONENT, [$u1->id]));
        $this->assertEquals(1, $DB->count_records('local_example_items', ['courseid' => $course->id]));

        provider::delete_data_for_all_users_in_context($context);
        $this->assertEquals(0, $DB->count_records('local_example_items', ['courseid' => $course->id]));
        $this->assertEquals(1, $DB->count_records('local_example_items', ['courseid' => $other->id]));

        // A context of another level must be ignored.
        provider::delete_data_for_all_users_in_context(\core\context\user::instance($u1->id));
        $this->assertEquals(1, $DB->count_records('local_example_items', ['courseid' => $other->id]));
    }
}
```

- Generate data the way the plugin really stores it: through the plugin's own API or data generator where one
  exists, so a renamed table or a new file area is exercised. Pass `'summary'` to `create_course()`; without it
  the generator writes placeholder text (`public/lib/testing/generator/data_generator.php`).
- Add files to the area in the export and delete tests when the plugin has one, and assert on
  `$writer->get_files($subcontext)` and on `get_file_storage()->is_area_empty()`.
- For user preferences: set one with `set_user_preference()`, call `provider::export_user_preferences($userid)`, and
  read `writer::with_context(\core\context\system::instance())->get_user_preferences(self::COMPONENT)`.
- `assertContains()` is strict: compare context ids after `intval`, or with `assertEqualsCanonicalizing()`.

## Core's compliance checks for one plugin

Core's test class iterates every installed component as a data set named after the component
(`get_component_list()`). On a site with the plugin installed and PHPUnit initialised, from the Moodle root:

```bash
vendor/bin/phpunit public/privacy/tests/privacy/provider_test.php --filter 'local_example'
```

It runs, for that component: `test_null_provider` (the reason string exists), `test_metadata_provider` (each
declared table exists, each plugin type and subsystem link is real, every summary and field string exists),
`test_all_providers_compliant`, `test_userdata_provider_implements_userlist`, and `test_table_coverage` (every
table in the plugin's `db/install.xml` with a `userid` field or a foreign key to `user.id` is declared). The
filter matches the data-set name, which PHPUnit prints as `with data set "local_example"`; if it matches nothing
the run reports no tests, which proves nothing, so check the count. The whole group (`--group plugin_checks`)
also runs other plugin checks for every installed plugin.

The devdocs page https://moodledev.io/docs/apis/subsystems/privacy/utils has CLI scripts that list non-compliant
components and run a full export and deletion for a user. They act on the site they run on: run them on a
throwaway development site only, never on one with real users.
