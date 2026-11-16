---
name: moodle-plugin-development
description: Use when creating, modifying or reviewing any Moodle plugin (local, mod, block, format, auth, enrol, report, tool, qtype, filter, repository, tiny, availability, sub-plugins) for Moodle 5.2 and 5.3 - version.php ($plugin->version, requires, supported), db/install.xml and db/upgrade.php, db/access.php capabilities, db/services.php, db/tasks.php, db/caches.php, lang/en strings, classes/ autoloading and frankenstyle names, lib.php callbacks versus hooks, settings.php, page scripts (require_login, require_capability, sesskey, PARAM types), privacy provider, LICENSE and the plugin ZIP, "No upgrade needed" after a db/ change, "Incorrect syntax in plugin supported declaration". Skip when the plugin is a theme (use moodle-theme-development) or when you need the cross-cutting pitfall index (use moodle-field-lessons).
---

# Moodle plugin development

## Overview

A plugin is a directory that core maps to a frankenstyle component (`<type>_<name>`) and installs from its
`version.php`. This skill gives the mental model, a skeleton that installs and passes review, and the rules for
each `db/` file. Supported versions: Moodle 5.2 (baseline) and 5.3.

## When to Use

- Creating a plugin, or adding a table, capability, web service, task, cache, setting or page to one
- Reviewing a plugin for structure, naming, registration and coding-standard problems
- Deciding between a `lib.php` callback and a hook, or which files a plugin type needs
- **Skip when:** the plugin is a theme (`moodle-theme-development` and its siblings); you need the long list of
  non-obvious traps by topic (`moodle-field-lessons`); moving a plugin across Moodle versions
  (`moodle-upgrade-migration`, `moodle-5-3-changes`); preparing a release or a Plugins directory submission
  (`moodle-plugin-release`, `moodle-release-preflight`)

## The mental model

1. **The component name is the address.** `local_example` lives in `public/local/example/` (5.1+ layout: every
   plugin type directory is under `public/`). The type-to-directory map is `lib/plugins.json` at the Moodle root
   (5.3.0). Every global name the plugin defines (function, class, constant, table, setting, CSS class) starts
   with the component, because they all share one PHP process and one database.
2. **The numeric `$plugin->version` drives installation.** When it is higher than the value stored in
   `config_plugins`, the upgrade runs `db/upgrade.php` (or `db/install.xml` on a fresh install), then re-reads
   `db/access.php`, `db/log.php`, `db/services.php`, `db/tasks.php`, `db/messages.php` and `db/tag.php` into the
   database (`upgrade_component_updated()`) and `db/caches.php` into the cache configuration
   (`cache_helper::update_definitions()`; both in `public/lib/upgradelib.php`, 5.2 and 5.3).
   Edit one of those files without a bump and the upgrade prints "No upgrade needed"; nothing changes.
   `db/events.php` and `db/hooks.php` are read into the cache instead, so a cache purge picks them up.
3. **`classes/` is autoloaded by namespace.** `\local_example\task\cleanup` is
   `classes/task/cleanup.php`. Files outside `classes/` (`lib.php`, `locallib.php`, page scripts) are loaded
   only when something includes them.
4. **Every entry point authorises itself.** A page script, an external function and a `pluginfile` callback
   each establish login, context and capability. `require_login()` alone admits every account on the site.

## Default recipe: a skeleton that installs and survives review

```
local/example/
  LICENSE                      # full GPL v3 text; the Plugins directory blocks approval without it
  README.md                    # what it does, settings, dependencies, post-install steps
  version.php
  lang/en/local_example.php    # 'pluginname' at minimum
  classes/privacy/provider.php # null_provider if no personal data is stored
  db/                          # only the files you need: install.xml, upgrade.php, access.php, ...
  settings.php  lib.php  templates/  amd/src/  amd/build/  tests/
```

```php
<?php
// (GPL header)

/**
 * Version information.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'local_example';
$plugin->version   = 2026111600;       // YYYYMMDDXX.
$plugin->requires  = 2026042000;       // Moodle 5.2.
$plugin->supported = [502, 503];
$plugin->release   = '1.0.0';
$plugin->maturity  = MATURITY_STABLE;
```

- **`requires` is a core version number; `supported` is an inclusive pair of branch numbers.** 5.2 starts at
  `2026042000` (5.2.2+ is `2026042002.01`) and 5.3.0 is `2026100500` (`public/version.php` of each). A
  one-branch plugin says `[502, 502]`: `[502]` makes core throw `coding_exception('Incorrect syntax in plugin
  supported declaration')` whenever it loads plugin information (`public/lib/classes/plugininfo/base.php:311-320`,
  5.2 and 5.3). Keep `requires` at or above the lowest branch in `supported`.
- **`version` and `release` move separately.** Every `db/` change from mental model point 2 bumps `version`;
  `release` changes only when you cut a release (`moodle-plugin-release`).
- **`$plugin->dependencies`** takes the other plugin's `version` number, not `ANY_VERSION`, once your code
  calls something that plugin added: `['mod_quiz' => 2026042000]`.
- **`LICENSE` sits in the plugin root from the first commit.** `moodle-plugin-ci validate` does not check it and
  the Plugins directory blocks approval without it. How the ZIP is built and checked (one root folder named
  `example/`, the licence file inside it) is owned by `moodle-plugin-release`.

## db/install.xml and db/upgrade.php

- Generate `install.xml` with the XMLDB editor (Site administration > Development > XMLDB editor) and keep
  the `PREVIOUS`/`NEXT` chain intact if you edit it by hand. Table names start with the full component
  (`local_example_items`); only a `mod` may use the bare module name (`example_attempts`).
  `moodle-plugin-ci validate` checks the prefix.
- **Never write `CHAR ... NOTNULL="true" DEFAULT=""`.** XMLDB turns it into NOT NULL with no default and reports
  it only through `debugging()` on a fresh install, which aborts `moodle-plugin-ci install` while your upgraded
  site stays quiet. An optional CHAR is `NOTNULL="false"` with no default. Check while writing:
  `grep -n 'DEFAULT=""' db/install.xml` must print nothing.
- **Check each new column and table name against the reserved-word lists** in
  `public/lib/ddl/mysql_sql_generator.php`, `postgres_sql_generator.php` and `mssql_sql_generator.php`
  (`connection` is reserved on MySQL, read in 5.3.0). Renaming later touches every query.
- **Every `install.xml` change needs a matching `upgrade.php` step and a version bump.** `install.xml` runs only
  on fresh installs, so a correction without a step leaves existing sites unchanged while upgrade reports
  success. PHPUnit's `init.php` is also a no-op until some version changes.

```php
function xmldb_local_example_upgrade($oldversion) {
    global $DB;
    $dbman = $DB->get_manager();

    if ($oldversion < 2026111600) {
        $table = new xmldb_table('local_example_items');
        $field = new xmldb_field('status', XMLDB_TYPE_INTEGER, '4', null, XMLDB_NOTNULL, null, '0', 'name');
        if (!$dbman->field_exists($table, $field)) {
            $dbman->add_field($table, $field);
        }
        upgrade_plugin_savepoint(true, 2026111600, 'local', 'example');
    }
    return true;
}
```

- Write each step so it can run twice: DDL is not transactional on MySQL and MariaDB, so a step that dies
  halfway leaves the first changes in place (guard with `field_exists()`, `index_exists()`, `table_exists()`).
- Do not call grade, modinfo or course APIs from `upgrade.php`; queue an ad-hoc task instead. Details:
  `moodle-upgrade-migration`.
- XMLDB foreign keys are only indexes. Changing NULL-ability of a keyed field: `drop_key()`,
  `change_field_notnull()`, `add_key()`, or the upgrade throws `ddldependencyerror`.

## db/access.php

```php
$capabilities = [
    'local/example:manage' => [
        'riskbitmask'  => RISK_XSS | RISK_CONFIG,
        'captype'      => 'write',
        'contextlevel' => CONTEXT_SYSTEM,
        'archetypes'   => ['manager' => CAP_ALLOW],
    ],
];
```

- Each capability needs a lang string `$string['example:manage']`; a `mod` needs `mod/<name>:addinstance` (and
  its string) or `moodle-plugin-ci validate` fails.
- Set `riskbitmask` honestly: a capability that lets a user author HTML other users see carries `RISK_XSS`.
- `clonepermissionsfrom` replaces `archetypes`: the new capability copies every role's real grants of the source
  capability. A grant shipped by mistake is not re-derived when you fix `access.php`; existing sites keep it.

Full templates for every `db/` file (services, tasks, events, caches, messages, uninstall):
[reference/db-files.md](reference/db-files.md).

## Names: frankenstyle everywhere

- Global functions, global classes and `define()` constants take the full component prefix, including helpers
  in page scripts and `cli/` scripts: `local_example_render_table()`, not `example_render_table()`. For `mod`
  the prefix is the bare module name (`example_add_instance()`). `phpcs` checks only the case of function names,
  and the Plugins directory treats a missing prefix as an approval blocker. Better: put helpers in a class under
  `classes/`.
- Settings are stored in `config_plugins`: name them `local_example/settingname` in `settings.php`, read with
  `get_config('local_example', 'settingname')`, write with `set_config('settingname', $v, 'local_example')`.
- CSS selectors in `styles.css` are scoped to the plugin (`.local_example-panel`, `.path-mod-example ...`): all
  plugins' `styles.css` files are served as one sheet on every page.

## Page scripts

```php
require_once(__DIR__ . '/../../config.php');

$id = required_param('id', PARAM_INT);
$course = get_course($id);
$context = \core\context\course::instance($course->id);

require_login($course);
require_capability('local/example:manage', $context);

$PAGE->set_url(new moodle_url('/local/example/manage.php', ['id' => $id]));
$PAGE->set_context($context);
$PAGE->set_title(get_string('pluginname', 'local_example'));

if (optional_param('delete', 0, PARAM_INT) && confirm_sesskey()) {
    // State change here, then redirect.
}

echo $OUTPUT->header();
echo $OUTPUT->footer();
```

- Read input only through `required_param()` / `optional_param()` with the narrowest type that fits
  (`PARAM_INT`, `PARAM_ALPHANUMEXT`, `PARAM_COMPONENT`, `PARAM_NOTAGS`). A `PARAM_RAW` or `PARAM_RAW_TRIMMED`
  needs a comment saying why and where the value is escaped; reviewers flag every unexplained one.
- `require_login()` is not authorisation: name the capability each page and each sibling action needs, and give
  sibling actions (edit, delete, react, pin) the same checks as the main one.
- `confirm_sesskey()` with no argument reads `required_param('sesskey')` and throws `missingparam` when the request
  has none (`public/lib/sessionlib.php`, 5.3.0); call it only on requests that carry one.
- Temporary directories come from `make_temp_directory('local_example/x')` or `make_request_directory()`; a
  literal `mkdir($dir, 0777, true)` ignores `$CFG->directorypermissions` and is flagged in review.
- Outbound HTTP goes through core's `\curl` class so the site proxy and `curlsecurityblockedhosts` apply; if you
  must use raw cURL, say in the setting's description that the proxy is not used.

Settings pages (`settings.php` for each plugin type, external pages behind a custom capability) and more page
patterns: [reference/settings-and-pages.md](reference/settings-and-pages.md).

## Lang strings

- `lang/en/<component>.php` is data only: `$string['key'] = 'Value';` lines, sorted by key (phpcs
  `moodle.Files.LangFilesOrdering`). Only `lang/en` ships; translations go through AMOS.
- Strings core asks for by convention: `pluginname` (every plugin; filters also `filtername`), one
  `cachedef_<name>` per `db/caches.php` definition, one `<type>/<name>:<cap>` per capability,
  `privacy:metadata...` for the privacy provider, `messageprovider:<name>` per `db/messages.php` entry, and
  `modulename`/`modulenameplural`/`pluginadministration` for a `mod`. A missing one passes every automated gate
  and shows as `[[key]]` on the page.
- `{$a}` versus `{$a->name}` must match what the caller passes; nothing checks it. Placeholder rules, multilang
  and spelling: `moodle-field-lessons` (its output and lang strings reference).

## lib.php callbacks and hooks

- On 5.2 and 5.3 most output and navigation extension points are hooks (`db/hooks.php`, `\core\hook\...`). A
  legacy callback that a hook replaces is still called but emits a deprecation `debugging()`, which fails a
  `--fail-on-warning` CI run ("Callback ... should be migrated to new hook callback", `public/lib/moodlelib.php`,
  5.3.0). When the same plugin also registers the replacing hook, core skips the old callback
  (`\core\hook\manager::is_deprecating_hook_present()`), so both can coexist for older branches. See
  `moodle-hooks-api` for the list and the migration.
- Callbacks with no hook replacement are still normal `lib.php` functions: `<component>_pluginfile()`,
  `local_<name>_extend_navigation(global_navigation $nav)`, `<component>_extend_settings_navigation()`,
  `<modname>_supports()`, `<modname>_add_instance()` and the reset and grading callbacks.
- `core\hook\navigation\secondary_extend` is dispatched only when the course secondary navigation is built
  (`public/lib/classes/navigation/views/secondary.php`, 5.3.0). To add to an activity page's More menu from a
  non-activity plugin, use `<component>_extend_settings_navigation()` and the `modulesettings` node.

## Output, blocks and privacy

- HTML comes from templates (`$OUTPUT->render_from_template('local_example/panel', $data)`) or a renderer in
  `classes/output/renderer.php` extending `plugin_renderer_base`. User text is escaped at the sink: `s()` for
  plain text, `format_string()` for names, `format_text()` for rich text. `html_writer::tag()` escapes attributes,
  not contents.
- In a block class use `$this->page`, never `global $PAGE`; the moodle-cs sniff for blocks rejects the global.
- Every plugin declares privacy. With no personal data:

```php
namespace local_example\privacy;

class provider implements \core_privacy\local\metadata\null_provider {
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

  With personal data, implement the metadata, request and userlist providers (`moodle-privacy-gdpr`).

## Course lifecycle and module essentials

- A plugin that stores course- or user-scoped rows plans backup and restore (`backup/moodle2/`), course reset
  (the `_reset_course_form_definition()`, `_reset_course_form_defaults()` and `_reset_userdata()` triad), and
  `db/uninstall.php` for data outside its own tables (user preferences are not removed by core). If a table
  deliberately stays out of backups, say why in the README; reviewers accept a reasoned answer.
- Activity modules must implement backup and restore to be approved in the Plugins directory.
- Inside `<modname>_add_instance()` use `$data->coursemodule`; the `course_modules` row still has `instance = 0`,
  so any lookup by instance fails and rolls back the creation.
- Creating a module from code with core's `create_module()` (outside the test generator) needs
  `$data->introeditor = ['text' => ..., 'format' => FORMAT_HTML, 'itemid' => 0]` for any module that supports
  `FEATURE_MOD_INTRO`; without it the call throws `createmodulemissingattribut`, and `add_moduleinfo()` copies
  that array into `intro`/`introformat` (`public/course/lib.php` `create_module()`, `public/course/modlib.php`,
  read in 5.3.0).

Per-type required files, base classes and what `moodle-plugin-ci validate` demands, plus sub-plugins:
[reference/plugin-types.md](reference/plugin-types.md).

## Coding standard essentials

- Every PHP file starts with `<?php` and the GPL boilerplate, has a file docblock with `@package`,
  `@copyright` and `@license`, and no closing `?>`. Non-PHP files (templates, SCSS, JS) carry the boilerplate too;
  phpcs only checks PHP.
- `defined('MOODLE_INTERNAL') || die();` belongs only in files that run code when included (`version.php`,
  `lib.php`, `db/*.php`, `settings.php`); class files under `classes/` do not have it. phpcs decides: run
  `vendor/bin/phpcs --standard=moodle path/to/plugin` and fix what it reports, including in files copied from
  another plugin.
- Code adapted from another author keeps that author's `@copyright` line above yours.
- After installing a change on a site: run the upgrade, then purge caches. A new class file returns 500 on the
  site until the class map cache is rebuilt, even though PHPUnit is green.

```bash
php admin/cli/upgrade.php --non-interactive
php admin/cli/purge_caches.php
php public/admin/tool/phpunit/cli/init.php
vendor/bin/phpunit --testsuite local_example_testsuite
```

Core CLI stays in `admin/cli/` at the Moodle root; the PHPUnit and Behat tools are under `public/admin/tool/`
(5.2 and 5.3).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `db/services.php` or `db/tasks.php` edited, no version bump | "No upgrade needed"; function or task never registered | Bump `version`; check `external_function_info($name, IGNORE_MISSING)` |
| `$plugin->supported = [502];` | `coding_exception` on every plugin list | `[502, 502]` |
| `CHAR NOTNULL="true" DEFAULT=""` | `debugging()` on fresh install only; CI install aborts | `NOTNULL="false"`, no default |
| `install.xml` fixed, no upgrade step | Existing sites keep the old schema | Pair every schema change with a step |
| No `LICENSE` in the root, or ZIP root `moodle-local_x-1.0.0/` | Plugins directory blocker; `rootdirinvalid` on install | `LICENSE` in root; build the ZIP as `moodle-plugin-release` says |
| Helper `function render_x()` in a page script | Namespace collision blocker in review | Component prefix or a class |
| Page with `require_login()` only | Any account can use it | `require_capability()` per page and action |
| `PARAM_RAW` on a name or id | Review finding; unvalidated input | Narrowest `PARAM_*`, or a comment with the reason |
| `mkdir($d, 0777, true)` | Ignores site permissions | `make_temp_directory()` |
| Capability without a lang string, cache without `cachedef_` | `[[key]]` on admin pages | Add the string |
| `global $PAGE` in a block | moodle-cs error | `$this->page` |
| Lookup by instance in `add_instance()` | Creation rolled back | `$data->coursemodule` |
| Legacy callback that a hook replaced | Deprecation notice fails CI | Register the hook |

## Reference files

| File | Read it when |
|---|---|
| [reference/db-files.md](reference/db-files.md) | writing or reviewing `db/services.php`, `db/tasks.php`, `db/events.php`, `db/caches.php`, `db/messages.php`, `db/uninstall.php` or an external function class |
| [reference/settings-and-pages.md](reference/settings-and-pages.md) | writing `settings.php` for any plugin type, an admin external page behind a custom capability, or a page that handles a form POST |
| [reference/plugin-types.md](reference/plugin-types.md) | creating a plugin of a type other than `local`, checking which files and base classes a type needs, or declaring sub-plugins |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

## References

- Plugin types: https://moodledev.io/docs/apis/plugintypes
- Common files: https://moodledev.io/docs/apis/commonfiles and https://moodledev.io/docs/apis/commonfiles/version.php
- Frankenstyle: https://moodledev.io/general/development/policies/codingstyle/frankenstyle
- Coding style: https://moodledev.io/general/development/policies/codingstyle
- XMLDB and DDL: https://moodledev.io/docs/apis/core/dml/ddl
- Access API: https://moodledev.io/docs/apis/subsystems/access
- Privacy API: https://moodledev.io/docs/apis/subsystems/privacy
- Hooks API: https://moodledev.io/docs/apis/core/hooks
- Security guidelines: https://moodledev.io/general/development/policies/security
