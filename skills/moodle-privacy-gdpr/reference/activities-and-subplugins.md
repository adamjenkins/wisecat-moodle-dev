# Activity modules, subplugin types and subplugins

Read this when the plugin is an activity module (its data lives in module contexts), defines subplugin types
whose plugins store data for it, or is itself a subplugin of another plugin.

Everything here was read in the 5.3.0 source and holds on 5.2 (the privacy API directories are identical); none
of it was run.

## Activity modules

An activity's data belongs to the module context of each instance. The interfaces are the same as for any plugin
(`metadata\provider`, `request\plugin\provider`, `request\core_userlist_provider`).

### Finding contexts and users

Join from the context through `course_modules` and `modules` to your instance table, filtering on your module
name, as core's choice does (`public/mod/choice/classes/privacy/provider.php`):

```php
public static function get_contexts_for_userid(int $userid): contextlist {
    $sql = "SELECT ctx.id
              FROM {context} ctx
              JOIN {course_modules} cm ON cm.id = ctx.instanceid AND ctx.contextlevel = :modlevel
              JOIN {modules} m ON m.id = cm.module AND m.name = :modname
              JOIN {example} e ON e.id = cm.instance
              JOIN {example_entries} en ON en.exampleid = e.id
             WHERE en.userid = :userid";
    $contextlist = new contextlist();
    $contextlist->add_from_sql($sql, ['modlevel' => CONTEXT_MODULE, 'modname' => 'example', 'userid' => $userid]);
    return $contextlist;
}

public static function get_users_in_context(userlist $userlist): void {
    $context = $userlist->get_context();
    if (!$context instanceof \core\context\module) {
        return;
    }
    $sql = "SELECT en.userid
              FROM {course_modules} cm
              JOIN {modules} m ON m.id = cm.module AND m.name = :modname
              JOIN {example_entries} en ON en.exampleid = cm.instance
             WHERE cm.id = :cmid";
    $userlist->add_from_sql('userid', $sql, ['modname' => 'example', 'cmid' => $context->instanceid]);
}
```

Without the `modules` join, a cm id of another module type with the same instance number matches your rows.

### Exporting

Start each context's export from core's generic module data, then add your own:

```php
$contextdata = \core_privacy\local\request\helper::get_context_data($context, $user);   // name, intro, completion
$contextdata = (object) array_merge((array) $contextdata, $mydata);
writer::with_context($context)->export_data([], $contextdata);
\core_privacy\local\request\helper::export_context_files($context, $user);              // intro files
```

`get_context_data()` returns the formatted activity name, the intro (with its files rewritten) and the user's
completion state for that cm (`public/privacy/classes/local/request/helper.php`). Put per-item data in
subcontexts below the activity (`[get_string('entries', 'mod_example'), $entry->id]`).

### Deleting

```php
public static function delete_data_for_all_users_in_context(\context $context): void {
    global $DB;
    if (!$context instanceof \core\context\module) {
        return;
    }
    if (!$cm = get_coursemodule_from_id('example', $context->instanceid)) {
        return;                                       // Another module's context.
    }
    get_file_storage()->delete_area_files($context->id, 'mod_example', 'entry');
    $DB->delete_records('example_entries', ['exampleid' => $cm->instance]);
}
```

- The same two guards go at the top of `delete_data_for_users()` and inside the loop of `delete_data_for_user()`.
- Never delete the instance row (`{example}`), its settings or other users' entries in a per-user delete.
- After your methods run, core's `request\helper` deletes the activity completion data for the cm, so you do not.
- Grades pushed with `grade_update()` are removed by `core_grades` in the course context; the module declares
  `add_subsystem_link('core_grades', ...)` if it grades.

## A plugin that defines subplugin types

When the subplugins store data that only makes sense inside the parent (assign's submission and feedback
plugins), the parent owns the contract:

1. Define one interface per subplugin type, extending `\core_privacy\local\request\plugin\subplugin_provider`,
   with the methods the parent will call (`public/mod/assign/classes/privacy/assignsubmission_provider.php`).
   Add a second interface for the userlist methods if the subplugins hold per-user rows
   (`assignsubmission_user_provider.php` in the same directory).
2. Declare the type in the parent's metadata:
   `$collection->add_plugintype_link('examplesub', [], 'privacy:metadata:examplesubpluginsummary');`
   Core's `test_metadata_provider` checks that the plugin type exists.
3. From each of the parent's request methods, call every installed subplugin through the manager:

```php
\core_privacy\manager::plugintype_class_callback('examplesub',
    \mod_example\privacy\examplesub_provider::class, 'export_examplesub_user_data', [$requestdata]);
```

`plugintype_class_callback(string $plugintype, string $interface, string $methodname, array $params)` calls the
method on each plugin of that type whose provider implements the interface
(`public/privacy/classes/manager.php`). The parent keeps working when a subplugin is uninstalled.

If the parent passes no data or context to its subplugins (editor plugins that only add buttons), it defines no
subplugin interface; each subplugin that stores data of its own has an ordinary provider.

## A subplugin of another plugin

Implement `metadata\provider` plus the parent's interface, and read the parent's interface for the exact methods:

```php
namespace assignsubmission_example\privacy;

class provider implements
    \core_privacy\local\metadata\provider,
    \mod_assign\privacy\assignsubmission_provider,
    \mod_assign\privacy\assignsubmission_user_provider {
    // ...
}
```

`subplugin_provider` extends `request\shared_data_provider`, which extends `request\data_provider`, so this pair is
compliant without `request\plugin\provider` (`public/privacy/classes/local/request/plugin/subplugin_provider.php`).
Core's own examples are in `public/mod/assign/submission/*/classes/privacy/provider.php`.

Plugin types called only through a core subsystem follow that subsystem's interface instead: a plagiarism
plugin implements `\core_plagiarism\privacy\plagiarism_provider`; a portfolio plugin
`\core_portfolio\privacy\portfolio_provider`.
