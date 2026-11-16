# settings.php for each plugin type, admin pages, and pages that handle a form

Read this when writing `settings.php` for any plugin type, an admin external page behind a custom capability,
or a page that handles a form POST.

Samples are valid on Moodle 5.2 and 5.3. The admin setting classes keep their global names
(`admin_settingpage`, `admin_setting_configtext`, ...) on both. **5.3+:** they are aliases of namespaced classes
(`\core_admin\setting\setting\configtext`, `\core_admin\setting\settingpage\settingpage`), which do not exist
on 5.2, so a plugin that supports both keeps the global names.

## What settings.php receives

`settings.php` is included by the type's `load_settings()` method (`public/lib/classes/plugininfo/<type>.php`)
while `public/admin/settings/plugins.php` builds the admin tree (5.3.0). What exists in scope depends on the type:

| Type | In scope | What you do |
|---|---|---|
| `mod`, `block`, `filter`, `format`, `auth`, `enrol`, `qtype`, `tiny`, most others | `$settings`, an `admin_settingpage` core created; `$ADMIN`; `$hassiteconfig` | Add settings to `$settings` inside `if ($ADMIN->fulltree)` |
| `local` | `$ADMIN`, `$hassiteconfig`; no `$settings` | Create a page and add it to `localplugins` (or any category) |
| `tool` | `$ADMIN`, `$hassiteconfig`; no `$settings` | Create a page and add it under `tools` (or the category that fits) |
| `report` | `$ADMIN`; a `$settings` page core created, added under Plugins > Reports (`reportplugins`) only if still set after the include (`public/admin/settings/plugins.php`, 5.3.0) | Add settings to `$settings`, or add an `admin_externalpage` for the report and set `$settings = null;` |

Calling `$settings->add()` where no `$settings` exists is a fatal error during upgrade.

A `repository` plugin has no `settings.php`: core links its admin entry to `admin/repository.php`
(`public/lib/classes/plugininfo/repository.php`, 5.3.0), and the plugin's options come from
`type_config_form()` and `get_type_option_names()` in its `repository_<name>` class (`public/repository/lib.php`).

```php
// mod, block, filter and similar types.
if ($ADMIN->fulltree) {
    $settings->add(new admin_setting_configtext(
        'mod_example/maxitems',
        new lang_string('maxitems', 'mod_example'),
        new lang_string('maxitems_desc', 'mod_example'),
        10,
        PARAM_INT
    ));
}
```

```php
// local and tool: create the page yourself.
if ($hassiteconfig) {
    $settings = new admin_settingpage('local_example', new lang_string('pluginname', 'local_example'));
    $ADMIN->add('localplugins', $settings);
    if ($ADMIN->fulltree) {
        $settings->add(new admin_setting_configcheckbox(
            'local_example/enabled',
            new lang_string('enabled', 'local_example'),
            new lang_string('enabled_desc', 'local_example'),
            0
        ));
    }
}
```

Rules that hold for every type:

- Setting names are `<component>/<name>` with a slash, so values go to `config_plugins`; read them with
  `get_config('<component>', '<name>')`.
- Labels and descriptions are `lang_string` objects (lazy, cheap while the tree is built).
- A new setting is stored with its default only when the upgrade runs, so add settings in a version-bumping
  change. Until then `get_config()` returns `false` and the form shows the first choice of a select next to
  "Default: ...". Traps of individual setting classes (multicheckbox defaults, `configtext` regex paramtypes,
  `filetypes` labels): `moodle-field-lessons` (its forms and settings reference).
- A page can name a capability other than `moodle/site:config`: the third argument of `admin_settingpage`, the
  fourth of `admin_externalpage`. Such a page must be added outside `if ($hassiteconfig)`, or the non-admin
  holders of that capability get "Access denied". Core precedent: `public/report/log/settings.php`.

```php
$ADMIN->add('reports', new admin_externalpage(
    'local_example_report',
    new lang_string('report', 'local_example'),
    new moodle_url('/local/example/report.php'),
    'local/example:viewreport'
));
```

The page itself then calls `admin_externalpage_setup('local_example_report');`, which does the login,
capability check and page setup for that entry.

## A page that handles a moodleform

```php
require_once(__DIR__ . '/../../config.php');

$id = required_param('id', PARAM_INT);
$course = get_course($id);
$context = \core\context\course::instance($course->id);
require_login($course);
require_capability('local/example:manage', $context);

$url = new moodle_url('/local/example/edit.php', ['id' => $id]);
$PAGE->set_url($url);
$PAGE->set_context($context);

$form = new \local_example\form\edit_item($url);
if ($form->is_cancelled()) {
    redirect(new moodle_url('/course/view.php', ['id' => $id]));
} else if ($data = $form->get_data()) {
    // get_data() has already checked the sesskey and the form's validation().
    \local_example\local\items::save($course->id, $data);
    redirect($url, get_string('saved', 'local_example'));
}

echo $OUTPUT->header();
$form->display();
echo $OUTPUT->footer();
```

- The form class lives in `classes/form/edit_item.php` and extends `\moodleform`.
- `redirect($url, $message)` prints the message as HTML; pass lang strings, never user data unescaped.
- A state change triggered by a link or a button outside a moodleform needs `require_sesskey()` (or
  `confirm_sesskey()` on a request that carries `sesskey`) before acting.
- For a page that is not tied to a course, use `\core\context\system::instance()` and `require_login()` with no
  course; for a module page, `require_login($course, false, $cm)` and the module context.

## References

- https://moodledev.io/docs/apis/subsystems/admin
- https://moodledev.io/docs/apis/subsystems/form
- https://moodledev.io/docs/apis/subsystems/access
