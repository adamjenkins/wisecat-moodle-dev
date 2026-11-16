You will bump the Moodle plugin version and wire the upgrade step.

User's input: {{{ input }}}

Steps:

1. Read `version.php` of the target plugin. If path missing, ask which plugin. On Moodle 5.2 and 5.3 plugin
   directories are under `public/` in the Moodle root (`public/local/attendance`).
2. Compute next version:
   - Current is `YYYYMMDDXX`
   - If today's date > current date portion: new version = `<today>00`
   - If today's date == current date portion: increment the trailing 2 digits
   - If current somehow > today: increment trailing 2 digits anyway, and say so
3. Update `$plugin->version` in `version.php`. Leave `$plugin->release` alone: it is the release name and changes
   only when a release is being prepared (`moodle-plugin-release`). If the user asks for a release bump as well,
   follow that skill for the changelog and the tag.
4. Open `db/upgrade.php` (create if missing — use the template from the `moodle-plugin-development` skill). The
   function is `xmldb_<component>_upgrade($oldversion)`; for an activity module the component part is the bare
   module name (`xmldb_forum_upgrade`).
5. Add a new `if ($oldversion < <newversion>) { ... upgrade_plugin_savepoint(true, <newversion>, '<type>', '<name>'); }`
   block at the END of the function (after existing blocks, before `return true;`). An activity module uses
   `upgrade_mod_savepoint(true, <newversion>, '<name>')` and a block `upgrade_block_savepoint(true, <newversion>, '<name>')`.
6. Inside the block, draft the schema/data change based on the reason argument or by asking the user. Use the XMLDB API (`$dbman = $DB->get_manager()`, `field_exists`, `add_field`, `change_field_*`, `add_index`, etc.). Always guard with `*_exists()` checks.
7. Make the same schema change in `db/install.xml`, so a fresh install and an upgraded site end with the same
   tables. The XMLDB editor (Site administration > Development > XMLDB editor, `/admin/tool/xmldb/`) writes the
   file and generates the PHP for the upgrade step.
8. A change that only adds a setting, a capability, a web service, a task or a hook callback needs the version
   bump and no upgrade step: core re-reads `settings.php` and the `db/*.php` files when the version rises.
9. Remind the user:
   - Run `php admin/cli/upgrade.php --non-interactive` from the Moodle root (`admin/cli/` is not under `public/`)
   - Add the change to the plugin's changelog if it keeps one

Print the diff and the upgrade command to run. Say that the upgrade was not run.

Reference the `moodle-upgrade-migration` skill for cross-version concerns.
