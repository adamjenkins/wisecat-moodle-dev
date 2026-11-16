# Plugin types: directories, required files and base classes

Read this when creating a plugin of a type other than `local`, checking which files and base classes a type
needs, or declaring sub-plugins.

Directories are relative to the Moodle root and use the 5.1+ layout (`public/`), which holds on 5.2 and 5.3.
The type-to-directory map is `lib/plugins.json` at the root. "validate" means `moodle-plugin-ci validate`
(read in its 4.5 source, `src/PluginValidate/Requirements/`); it is the check CI and the Plugins directory run.

## Every type

validate requires `version.php` and `lang/en/<component>.php` with `pluginname`, checks that every table in
`db/install.xml` starts with the component, that `db/upgrade.php` (if present) defines
`xmldb_<component>_upgrade()`, and that Behat features carry the `@<type>` and `@<component>` tags. Reviewers
also expect `LICENSE` in the root and a privacy provider, which validate does not check.

## Per type

| Type | Directory | Required beyond the common files | Base class or entry point |
|---|---|---|---|
| `local` | `public/local/<name>` | nothing | `lib.php` callbacks and hooks |
| `mod` | `public/mod/<name>` | `lib.php` with `<name>_add_instance()` and `<name>_update_instance()`, `mod_form.php`, `view.php`, `index.php`, `db/install.xml` with a `<name>` table, `db/access.php` with `mod/<name>:addinstance`; lang file is `lang/en/<name>.php` (no `mod_` prefix) with `modulename` or `pluginname` and `<name>:addinstance` | `mod_<name>_mod_form extends moodleform_mod`; `<name>_supports()`; backup and restore in `backup/moodle2/` (needed for Plugins directory approval) |
| `block` | `public/blocks/<name>` | `block_<name>.php`, `db/access.php` (`block/<name>:addinstance`, and `block/<name>:myaddinstance` if it can go on the Dashboard) | `class block_<name> extends block_base`; use `$this->page` |
| `format` | `public/course/format/<name>` | `format.php`, `lib.php` | `class format_<name> extends core_courseformat\base`; renderer `format_<name>\output\renderer extends core_courseformat\output\section_renderer` in `classes/output/renderer.php` |
| `filter` | `public/filter/<name>` | `classes/text_filter.php`; lang strings `filtername` (validate) and `pluginname` (reviewers ask for it) | `class text_filter extends \core_filters\text_filter` in namespace `filter_<name>`. No `filter.php` is needed on 5.2+; core's own `filter.php` files are deprecated shims (`public/filter/emoticon/filter.php`), and validate only prints "Skipping validation of missing or optional file: filter.php" |
| `auth` | `public/auth/<name>` | `auth.php` | `class auth_plugin_<name> extends auth_plugin_base` |
| `enrol` | `public/enrol/<name>` | `lib.php` | `class enrol_<name>_plugin extends enrol_plugin` |
| `repository` | `public/repository/<name>` | `lib.php`, `db/access.php` with `repository/<name>:view` and its string | `class repository_<name> extends repository` |
| `qtype` | `public/question/type/<name>` | `questiontype.php`, `question.php`, `renderer.php`, `edit_<name>_form.php`; tables start with `qtype_` or `question_` | `qtype_<name> extends question_type`; `qtype_<name>_question extends question_graded_automatically` (or another base) |
| `tool` | `public/admin/tool/<name>` | nothing | `settings.php` receives `$ADMIN` and `$hassiteconfig` but no `$settings` page: create an `admin_settingpage` and add it under `tools` |
| `report` | `public/report/<name>` | nothing | navigation callbacks or hooks; report builder classes |
| `tiny` | `public/lib/editor/tiny/plugins/<name>` | `classes/plugininfo.php` | `class plugininfo extends \editor_tiny\plugin` implementing `plugin_with_buttons` / `plugin_with_menuitems` / `plugin_with_configuration`; buttons appear only through `amd/src/configuration.js` |
| `availability` | `public/availability/condition/<name>` | `classes/condition.php`, `classes/frontend.php`, a YUI form module `yui/src/form/` | `class condition extends \core_availability\condition`; the form is loaded as YUI `moodle-availability_<name>-form` on 5.2 and 5.3 (`public/availability/classes/frontend.php`) |
| `theme` | `public/theme/<name>` | `config.php` | see `moodle-theme-development` |

Plugin types not listed (`assignsubmission`, `quizaccess`, `qbank`, `aiplacement`, `aiprovider`, `customfield`,
`dataformat`, `logstore` and others) follow the same pattern: read one core plugin of that type in the
branch you target and copy its file set.

## Sub-plugins

- A parent declares its sub-plugin types in `db/subplugins.json`:

```json
{
    "subplugintypes": {
        "exampletool": "tool"
    }
}
```

- `subplugintypes` values are relative to the parent's directory. The older `plugintypes` key (paths relative to
  the Moodle root) is read only when `subplugintypes` is absent, and then logs "Falling back to deprecated
  plugintypes value" (5.2 and 5.3);
  core's `public/mod/assign/db/subplugins.json` carries both keys, which is the safe form for a plugin that
  also supports branches before 5.1.
- The install directory comes from that file (here `public/mod/example/tool/<name>`), not from the type name
  (`\core\component::fetch_subtypes()`, `public/lib/classes/component.php`, 5.3.0). A deployment tool that
  guesses the directory from the type name puts sub-plugins in the wrong place.
- The declared directory must exist in the parent, even if empty (keep a placeholder such as a `readme.txt` in
  git): otherwise core logs "Invalid subtype directory" and the whole sub-plugin type is skipped, so its plugins
  never install (same file, 5.3.0).
- Sub-plugin components are `<subtype>_<name>` (`exampletool_report`), and their lang file, tables and global
  names use that component.

## References

- https://moodledev.io/docs/apis/plugintypes
- https://moodledev.io/docs/apis/plugintypes/mod
- https://moodledev.io/docs/apis/plugintypes/blocks
- https://moodledev.io/docs/apis/plugintypes/filter
- https://moodledev.io/docs/apis/plugintypes/tiny
- https://moodledev.io/docs/apis/plugintypes/availability
