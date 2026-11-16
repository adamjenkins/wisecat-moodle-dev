---
name: moodle-privacy-gdpr
description: Use when writing, reviewing or testing a Moodle plugin's privacy provider (classes/privacy/provider.php), adding a table, user preference, file area or external API call that holds personal data, or when the Plugin privacy registry says "Requires attention" or "Userlist provider missing". Covers null_provider vs metadata provider plus request\plugin\provider, get_metadata (add_database_table, add_subsystem_link, add_external_location_link, add_user_preference), get_contexts_for_userid, get_users_in_context, export_user_data, delete_data_for_all_users_in_context, delete_data_for_user, delete_data_for_users, core_userlist_provider, user_preference_provider, exporting and deleting files, comments, ratings and tags through core's helpers, activity and subplugin providers, and provider_testcase tests. Skip when auditing request handling for security (moodle-security-audit) or running the whole pre-release audit (moodle-release-preflight).
---

# Moodle Privacy / GDPR

## Overview

Every plugin ships `classes/privacy/provider.php`. The provider declares what personal data the plugin holds and
implements export and erasure for it, so that the privacy tool (`tool_dataprivacy`) can answer a data request and
apply retention. The privacy API is the same on 5.2 and 5.3 (`public/privacy/` is identical apart from
`phpunit.xml`, read in the source).

## When to Use

- Creating a plugin (every plugin needs a provider, even one that stores nothing)
- Adding or renaming a table, a user preference, a file area, or a call that sends user data to another system
- Reviewing a provider before a release or a Plugins directory submission
- The Plugin privacy registry (Site administration > Users > Privacy and policies) flags the plugin
- **Skip when:** auditing pages, web services and output for security (`moodle-security-audit`); running the full
  pre-release defect audit (`moodle-release-preflight`, whose class 4 points back here)

## How the privacy API works

- **`\core_privacy\manager` drives everything.** It finds `\<component>\privacy\provider` for every installed
  component and calls the interface methods. Nothing else in core calls your provider.
- **Compliant means one of two things** (`manager::component_is_compliant()`, `public/privacy/classes/manager.php`,
  5.3.0): the class implements `\core_privacy\local\metadata\null_provider`, or it implements
  `\core_privacy\local\metadata\provider` **and** a `\core_privacy\local\request\data_provider` (in practice
  `request\plugin\provider`, `request\user_preference_provider`, or a subplugin interface). A metadata provider
  alone is not compliant. The registry shows a non-compliant plugin as "Requires attention."
  (`public/admin/tool/dataprivacy/lang/en/tool_dataprivacy.php`, 5.3.0).
- **`request\plugin\provider` needs `request\core_userlist_provider` too.** Core's
  `test_userdata_provider_implements_userlist` fails without it, and the registry says "Userlist provider
  missing". `user_preference_provider` alone does not need it.
- **Export:** the user's contexts come from `get_contexts_for_userid()`; the admin approves them; the manager
  passes an `approved_contextlist` (one user, one component, those contexts) to `export_user_data()`.
- **Erasure has three entry points**, all of which must remove the same data:
  - `delete_data_for_user(approved_contextlist)`: one user, several contexts (a deletion request).
  - `delete_data_for_users(approved_userlist)`: several users, one context (retention expiry per user). The users
    come from `get_users_in_context()`.
  - `delete_data_for_all_users_in_context(\context)`: everything in a context (retention expiry of the context).
    The manager calls it **for every component** on that context (`manager::delete_data_for_all_users_in_context()`),
    so a context that is not yours arrives here too.
- **After your method, core removes what it owns for you:** activity completion and similar data for module
  contexts (`request\helper::delete_data_for_user()`, `public/privacy/classes/local/request/helper.php`, 5.3.0).
  Your own tables, files, comments, ratings and tags are yours to remove.

## Choose the interfaces

| The plugin stores | Implement |
|---|---|
| No personal data at all (only events, which log stores cover) | `metadata\null_provider` with `get_reason()` |
| Only site-wide user preferences | `metadata\provider` + `request\user_preference_provider` |
| Rows in its own tables, files, comments, ratings or tags keyed to users | `metadata\provider` + `request\plugin\provider` + `request\core_userlist_provider` |
| Context-specific preferences | All three above, plus `user_preference_provider` for any site-wide ones; the per-context ones are exported and deleted as context data |
| Data it only sends elsewhere (an API, an AI service) | `metadata\provider` with `add_external_location_link()` + `request\plugin\provider` + `core_userlist_provider` with empty methods |
| Data inside a parent plugin (an `assignsubmission_` plugin) | `metadata\provider` + the parent's subplugin interface: [reference/activities-and-subplugins.md](reference/activities-and-subplugins.md) |

The devdocs FAQ suggests a metadata provider alone for data sent only to another subsystem; by
`component_is_compliant()` that is not compliant. Use `null_provider` when the only trace is in the logs.

## Null provider

```php
// (GPL header)
namespace local_example\privacy;

class provider implements \core_privacy\local\metadata\null_provider {
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

`$string['privacy:metadata'] = 'The Example plugin does not store any personal data.';` Core's
`test_null_provider` calls `get_string()` on the reason.

A null provider is wrong when the plugin has any table with a `userid` column or a foreign key to `user.id`:
core's `test_table_coverage` lists every such table in `db/install.xml` that no metadata provider declares
(`public/privacy/tests/privacy/provider_test.php`, 5.3.0). Columns such as `usermodified` with no key are not
detected by that test, and still count as personal data.

## Default recipe: a plugin with its own table and a file area

```php
// (GPL header)
namespace local_example\privacy;

use core_privacy\local\metadata\collection;
use core_privacy\local\request\approved_contextlist;
use core_privacy\local\request\approved_userlist;
use core_privacy\local\request\contextlist;
use core_privacy\local\request\transform;
use core_privacy\local\request\userlist;
use core_privacy\local\request\writer;

class provider implements
    \core_privacy\local\metadata\provider,
    \core_privacy\local\request\plugin\provider,
    \core_privacy\local\request\core_userlist_provider {

    public static function get_metadata(collection $collection): collection {
        $collection->add_database_table('local_example_items', [
            'userid' => 'privacy:metadata:items:userid',
            'content' => 'privacy:metadata:items:content',
            'timecreated' => 'privacy:metadata:items:timecreated',
        ], 'privacy:metadata:items');
        $collection->add_subsystem_link('core_files', [], 'privacy:metadata:core_files');
        return $collection;
    }

    public static function get_contexts_for_userid(int $userid): contextlist {
        $sql = "SELECT ctx.id
                  FROM {local_example_items} i
                  JOIN {context} ctx ON ctx.instanceid = i.courseid AND ctx.contextlevel = :courselevel
                 WHERE i.userid = :userid";
        $contextlist = new contextlist();
        $contextlist->add_from_sql($sql, ['courselevel' => CONTEXT_COURSE, 'userid' => $userid]);
        return $contextlist;
    }

    public static function get_users_in_context(userlist $userlist): void {
        $context = $userlist->get_context();
        if (!$context instanceof \core\context\course) {
            return;
        }
        $userlist->add_from_sql('userid', 'SELECT userid FROM {local_example_items} WHERE courseid = :courseid',
            ['courseid' => $context->instanceid]);
    }

    public static function export_user_data(approved_contextlist $contextlist): void {
        global $DB;
        $userid = $contextlist->get_user()->id;
        foreach ($contextlist->get_contexts() as $context) {
            if (!$context instanceof \core\context\course) {
                continue;
            }
            $rows = $DB->get_records('local_example_items', ['courseid' => $context->instanceid, 'userid' => $userid]);
            foreach ($rows as $row) {
                $subcontext = [get_string('pluginname', 'local_example'), $row->id];
                writer::with_context($context)
                    ->export_data($subcontext, (object) [
                        'content' => writer::with_context($context)->rewrite_pluginfile_urls(
                            $subcontext, 'local_example', 'attachment', $row->id, $row->content),
                        'timecreated' => transform::datetime($row->timecreated),
                    ])
                    ->export_area_files($subcontext, 'local_example', 'attachment', $row->id);
            }
        }
    }

    public static function delete_data_for_all_users_in_context(\context $context): void {
        global $DB;
        if (!$context instanceof \core\context\course) {
            return;
        }
        get_file_storage()->delete_area_files($context->id, 'local_example', 'attachment');
        $DB->delete_records('local_example_items', ['courseid' => $context->instanceid]);
    }

    public static function delete_data_for_user(approved_contextlist $contextlist): void {
        $userid = (int) $contextlist->get_user()->id;
        foreach ($contextlist->get_contexts() as $context) {
            if ($context instanceof \core\context\course) {
                self::delete_items($context, [$userid]);
            }
        }
    }

    public static function delete_data_for_users(approved_userlist $userlist): void {
        $context = $userlist->get_context();
        if ($context instanceof \core\context\course) {
            self::delete_items($context, $userlist->get_userids());
        }
    }

    /** One delete path, so the three entry points cannot drift apart. */
    private static function delete_items(\context $context, array $userids): void {
        global $DB;
        if (!$userids) {
            return;
        }
        [$insql, $params] = $DB->get_in_or_equal($userids, SQL_PARAMS_NAMED);
        $params['courseid'] = $context->instanceid;
        $select = "courseid = :courseid AND userid $insql";
        $ids = $DB->get_fieldset_select('local_example_items', 'id', $select, $params);
        $fs = get_file_storage();
        foreach ($ids as $id) {
            $fs->delete_area_files($context->id, 'local_example', 'attachment', $id);
        }
        $DB->delete_records_select('local_example_items', $select, $params);
    }
}
```

Strings: one per summary and one per field identifier you pass (`privacy:metadata:items`,
`privacy:metadata:items:userid`, ..., `privacy:metadata:core_files`). Core's `test_metadata_provider` calls
`get_string()` on each and checks that each declared table exists.

## Rules

### What you declare must be what you export and delete

**Fact:** every table, field, preference, file area and external location in `get_metadata()` has an export path
and a path in all three delete methods. Nothing checks this except your own tests: core's tests check that the
declared table exists and has strings, not that the request methods touch it. **Symptom:** a declared field that
is never exported or erased is a compliance defect a reviewer finds by reading; a provider whose request
methods still query a table's old name after a rename throws `dml_exception` on the first export or erasure,
while `get_metadata()` (already updated) passes. **Fix:** route the three deletes through one helper, as in the
recipe; after any table rename, `grep -rn '<oldname>' classes/privacy`; write a provider test on generated rows
that covers all six methods. Source: `public/privacy/tests/privacy/provider_test.php` (5.3.0).

### A subsystem link declares; it does not export or delete

**Fact:** `add_subsystem_link('core_files', ...)` tells the registry that the plugin stores files. It does not
export or delete them: `\core_files\privacy\provider` handles only private-key data in the user context
(`public/files/classes/privacy/provider.php`, 5.3.0). **Symptom:** the export has no attachments, and erasure
leaves the user's files in `{files}`. **Fix:** export with `writer::with_context($ctx)->export_area_files()` (and
`rewrite_pluginfile_urls()` for text that embeds them); delete with `get_file_storage()->delete_area_files()`.
Comments, ratings and tags have their own helper calls: [reference/core-subsystems.md](reference/core-subsystems.md).
Only link a real subsystem: core's test asserts `core_component::is_core_subsystem()`, and there is no
`core_log` subsystem (`lib/components.json`, 5.3.0).

### Every context passed in may not be yours

**Fact:** `delete_data_for_all_users_in_context()` runs for every component on every expiring context, and
approved lists can carry context levels your plugin never uses. **Symptom:** an unguarded method deletes by the
wrong key (a module plugin deleting rows for whatever `instanceid` a course or another module's context has).
**Fix:** check the class (`instanceof \core\context\course`, `\core\context\module`) and, for a module, that the
cm is yours: `get_coursemodule_from_id('example', $context->instanceid)` returns false for another module's cm
(`public/mod/choice/classes/privacy/provider.php`, 5.3.0).

### Erasing one user touches only that user

**Fact:** `delete_data_for_user()` and `delete_data_for_users()` remove the named users' rows and files, nothing
else. **Symptom:** one erasure request deletes every user's files in a shared area (a file area keyed by
activity, not by row), or deletes the activity instance itself. **Fix:** key file areas by the row id that
belongs to one user, delete by that item id, and keep shared content (the activity, other users' replies).
Where content written by several users cannot be split, delete the personal part and keep the shared text, as
core's forum does by blanking authored fields.

### Ids come back as strings

**Fact:** `contextlist::get_contextids()` after `add_from_sql()` returns the database values, which are strings
(`public/privacy/classes/local/request/contextlist.php`, 5.3.0), and `$context->instanceid` is not cast either
(`public/lib/classes/context.php`, 5.3.0). **Symptom:** `$this->assertContains($context->id, $list->get_contextids())`
fails (PHPUnit's `assertContains` is strict) and `===` comparisons in provider code are silently false. **Fix:**
`array_map('intval', ...)` before comparing, or `assertEqualsCanonicalizing()`. `userlist::get_userids()` is
built from array keys and is int.

### User preferences

**Fact:** `add_user_preference($name, $stringid)` declares one preference; there is no wildcard, so numbered
preferences are declared one by one. `export_user_preferences(int $userid)` reads each with
`get_user_preferences($name, null, $userid)` and writes it with
`writer::export_user_preference('local_example', $name, $value, get_string(...))`. Site-wide preferences need no
delete method. **Symptom:** a preference that is set but not declared is undeclared personal data; core's uninstall
does not remove a plugin's preferences (`uninstall_plugin()`, `public/lib/adminlib.php`, 5.3.0; the uninstall
recipe is in `moodle-definition-of-done`). **Fix:** declare and export each; a child theme declares only the
preferences it adds, not its parent's. Source: `public/theme/boost/classes/privacy/provider.php` (5.2 and 5.3).

**5.3+:** Boost also stores the colour mode as preference `theme_boost_colourmode` and declares it in its own
provider; theme-side detail is in `moodle-theme-development`.

### Data sent to another system

**Fact:** a plugin that sends personal data out (an external API, an AI provider, analytics) declares it with
`add_external_location_link('<name>', ['<field>' => '<stringid>'], '<summarystringid>')` and still implements the
request interfaces, with empty methods when the data cannot be retrieved back. **Symptom:** a `null_provider` on a
plugin that posts names, emails or user text to a service is undeclared egress, and the Plugins directory
guidelines make a compliant privacy API an approval blocker for any plugin that processes personal data or
integrates with an external system. **Fix:** one external location per destination, the fields actually sent,
and the same statement in the plugin description. Source:
https://moodledev.io/docs/apis/subsystems/privacy/faq.

### Exports are readable

Use `transform::datetime()` for Unix timestamps (`transform::date()` for dates, `transform::yesno()`,
`transform::percentage()`), export language-independent ids only where they mean something to the user, put
each item in its own subcontext (`[get_string('pluginname', ...), $row->id]`), and use
`export_related_data()` for data about the item rather than its own content. Source:
`public/privacy/classes/local/request/transform.php`, `content_writer.php` (5.3.0).

## Testing

Extend `\core_privacy\tests\provider_testcase` in `tests/privacy/provider_test.php`, generate rows for two users,
and cover all six methods. Its helpers are `get_contexts_for_userid($userid, $component)`,
`export_all_data_for_user($userid, $component)` and `export_context_data_for_user($userid, $context, $component)`;
it has no delete helper (`public/privacy/classes/tests/provider_testcase.php`, 5.3.0). Assertions read the test
writer: `writer::with_context($context)->get_data([...])`, `has_any_data()`, `get_files()`. Full test and how to
run core's compliance checks for one plugin: [reference/testing.md](reference/testing.md).

Core's compliance tests (group `plugin_checks`) are not part of a plugin's `moodle-plugin-ci phpunit` run, which
runs only the plugin's own suite, so a missing or broken provider passes CI.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No `classes/privacy/provider.php` | Registry: "Requires attention."; core's compliance test fails | At least a `null_provider` |
| `null_provider` while a table has `userid` | `test_table_coverage` fails; data never exported or erased | Full provider |
| `metadata\provider` with no request interface | Not compliant | Add `plugin\provider` (or `user_preference_provider`) |
| `plugin\provider` without `core_userlist_provider` | "Userlist provider missing"; core test fails | Implement `get_users_in_context()` and `delete_data_for_users()` |
| A declared table or field missing from export or a delete | Compliance defect; erasure leaves data | One delete helper; a test per method |
| Provider still names a table's old name | `dml_exception` on export or erasure | Grep `classes/privacy` after every rename |
| Relying on `add_subsystem_link('core_files')` to delete files | Files survive erasure and are missing from the export | `export_area_files()`, `delete_area_files()` |
| `add_subsystem_link('core_log')` | Core test fails: no such subsystem | Nothing to declare for events |
| No context-class check in `delete_data_for_all_users_in_context()` | Deletes another component's data by a coincident id | `instanceof` check and, for a module, `get_coursemodule_from_id()` |
| One user's erasure deletes a shared file area | Other users lose their files | Key areas by the user's row id |
| Strict comparison of context ids | Test or check silently fails | `intval` them first |
| Missing `privacy:metadata:*` strings | `test_metadata_provider` fails; registry shows `[[key]]` | One string per summary and field |
| `transform::datetime()` on a non-timestamp | Nonsense dates in the export | Only for Unix timestamps |
| Expecting `provider_testcase` to delete for you | Method does not exist | Call the provider's delete methods directly |

## Reference files

| File | Read it when |
|---|---|
| [reference/core-subsystems.md](reference/core-subsystems.md) | The plugin stores files, comments, ratings, tags, favourites, question attempts or plagiarism data through core, and you are writing their export and delete calls |
| [reference/activities-and-subplugins.md](reference/activities-and-subplugins.md) | The plugin is an activity module (data in module contexts), defines subplugin types, or is a subplugin of another plugin |
| [reference/testing.md](reference/testing.md) | You are writing `tests/privacy/provider_test.php`, or need to run core's compliance checks against the plugin before a release |

## References

- https://moodledev.io/docs/apis/subsystems/privacy
- https://moodledev.io/docs/apis/subsystems/privacy/faq
- https://moodledev.io/docs/apis/subsystems/privacy/utils
- See also: `moodle-release-preflight` (class 4, lifecycle), `moodle-definition-of-done` (uninstall and user
  preferences), `moodle-field-lessons`
