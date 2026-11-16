# Changing settings in a released theme

Read this when a theme that sites already use renames, removes, splits or converts a setting, moves an uploaded
file to another file area, adds `db/install.php`, or takes over from Boost on a site that had Boost settings.

Read in the 5.2 and 5.3.0 source (`public/lib/upgradelib.php`, `public/lib/adminlib.php`, `admin/cli/upgrade.php`).
The upgrade steps below follow core's own settings migration in `public/lib/db/upgradelib.php` (5.3.0) and were
not run in a theme.

## What an upgrade does with theme settings, in order

1. The theme's `db/upgrade.php` steps run (`xmldb_theme_<name>_upgrade($oldversion)`), when `$plugin->version` in
   `version.php` is higher than the installed one.
2. After all plugins are upgraded, defaults are stored for every setting that has no value yet: the CLI upgrade
   does it directly; the web upgrade shows the "new settings" page and stores them when the admin saves.
3. Updated-callbacks do not run for defaults.

So inside an upgrade step a setting introduced in the same release has no value yet (`get_config()` gives `false`),
and a value the step writes is kept: the default is applied only where nothing is stored. Without a version bump
neither step happens.

A theme has no database tables of its own for settings. All state is `config_plugins` rows, files in the system
context and user preferences, and each kind needs its own migration.

## Renaming a setting

```php
<?php
// (GPL header)

/**
 * Upgrade steps.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

/**
 * Runs the upgrade steps.
 *
 * @param int $oldversion the version being upgraded from
 * @return bool
 */
function xmldb_theme_mytheme_upgrade($oldversion) {
    if ($oldversion < 2026112000) {
        // The setting "maincolour" is now "accent".
        $old = get_config('theme_mytheme', 'maincolour');
        if ($old !== false) {
            if (get_config('theme_mytheme', 'accent') === false) {
                set_config('accent', $old, 'theme_mytheme');
            }
            unset_config('maincolour', 'theme_mytheme');
        }
        theme_reset_all_caches();

        upgrade_plugin_savepoint(true, 2026112000, 'theme', 'mytheme');
    }

    return true;
}
```

Rules:

- **Test for `false`, not for empty.** An admin who deliberately cleared the old setting has `''` stored, and that
  choice must survive the rename.
- **Do not overwrite a value already stored under the new name.** The step can run on a site where an earlier
  attempt half-finished, or where the admin opened the new settings page first.
- **Unset the old name only after the copy**, and check the two names are different. A copy-pasted step that reads
  a name, sets the same name and then unsets it deletes the value it just wrote; this has shipped in a public
  theme.
- **Every step ends with `upgrade_plugin_savepoint()`** using the same number as its `if`, and nothing runs between
  steps outside an `if`. Code placed between savepoints runs on every upgrade forever.
- **Reset the theme caches in a step that changes anything the CSS uses.** Calling `theme_reset_all_caches()` is
  cheap. Do not call `purge_all_caches()` from a theme's upgrade.
- The version number in the step, in `upgrade_plugin_savepoint()` and in `version.php` must be the same. Raising
  `$plugin->version` for a migration is required; whether the release string changes is a release decision
  (`moodle-plugin-release`).

## Converting a value

When the meaning of the stored value changes (a number that becomes a length, a checkbox that becomes a select),
keep the key only if every old value is still valid under the new rules. Otherwise use a new key and convert:

```php
    if ($oldversion < 2026112001) {
        // "radius" was a number of pixels; "cornerradius" stores a length with its unit.
        $old = get_config('theme_mytheme', 'radius');
        if ($old !== false && get_config('theme_mytheme', 'cornerradius') === false) {
            if (is_numeric($old)) {
                set_config('cornerradius', ((int) $old) . 'px', 'theme_mytheme');
            }
        }
        unset_config('radius', 'theme_mytheme');
        theme_reset_all_caches();

        upgrade_plugin_savepoint(true, 2026112001, 'theme', 'mytheme');
    }
```

- A checkbox turned into a select: map `'1'` and `'0'` to the new keys explicitly. Left alone, the stored `'1'` is
  not among the select's choices, the page shows no selection, and the reading code sees a value it does not know.
- An option removed from a select: rewrite sites that hold the removed key to the nearest remaining one.
- A setting that is simply removed: `unset_config()` it in a step, so the row does not stay behind and return if
  the name is reused.

For many renames, a table keeps the steps readable and testable:

```php
        $renames = [
            // Old key => [new key, converter or null].
            'maincolour' => ['accent', null],
            'radius' => ['cornerradius', fn($v) => is_numeric($v) ? ((int) $v) . 'px' : null],
            'oldfeature' => [null, null],
        ];
        foreach ($renames as $from => [$to, $convert]) {
            $old = get_config('theme_mytheme', $from);
            if ($old === false) {
                continue;
            }
            if ($to !== null && get_config('theme_mytheme', $to) === false) {
                $new = $convert ? $convert($old) : $old;
                if ($new !== null) {
                    set_config($to, $new, 'theme_mytheme');
                }
            }
            unset_config($from, 'theme_mytheme');
        }
```

Keep the table inside the versioned `if`. A table that is applied on every upgrade under a counter of its own (a
second "feature version" stored in config) can work, but it adds a second source of truth: one public theme writes
a different counter value on install than on upgrade, so a fresh install re-runs old renames on its first upgrade.
The plugin version and savepoints already solve this.

## Moving an uploaded file to another file area

The setting value (`/logo.png`) and the file must move together, and the new area must be in `pluginfile`:

```php
    if ($oldversion < 2026112002) {
        $fs = get_file_storage();
        $contextid = context_system::instance()->id;
        $files = $fs->get_area_files($contextid, 'theme_mytheme', 'headerimage', 0, 'id', false);
        if ($files && !$fs->get_area_files($contextid, 'theme_mytheme', 'bannerimage', 0, 'id', false)) {
            foreach ($files as $file) {
                $fs->create_file_from_storedfile(['filearea' => 'bannerimage'], $file);
            }
            $value = get_config('theme_mytheme', 'headerimage');
            set_config('bannerimage', $value === false ? '' : $value, 'theme_mytheme');
        }
        $fs->delete_area_files($contextid, 'theme_mytheme', 'headerimage');
        unset_config('headerimage', 'theme_mytheme');
        theme_reset_all_caches();

        upgrade_plugin_savepoint(true, 2026112002, 'theme', 'mytheme');
    }
```

`create_file_from_storedfile()` takes a record of the fields that change and copies the rest from the source file.
Core's Classic-to-Boost migration in 5.3 copies files between components the same way
(`upgrade_migrate_classic_theme_to_boost()` in `public/lib/db/upgradelib.php`).

## Install

`db/install.php` (`xmldb_theme_<name>_install()`) is rarely needed for settings: defaults are stored by the
install itself. Use it only for something a default cannot express, such as copying a value from another
component once. Whatever it writes must agree with what `db/upgrade.php` leaves behind on an upgraded site: a
fresh install of version N and a site upgraded to N should hold the same keys.

## Taking over from Boost

A site that switches from Boost to a child theme sees its Boost customisation disappear: brand colour, raw SCSS,
background images, the hidden-blocks list. Nothing is lost, but each of those lives under `theme_boost` and the
child reads its own component (see "Setting names that already mean something" in `SKILL.md`). Options:

- **Document it.** State in the README which Boost settings must be entered again. This is what large child
  themes do.
- **Copy once on install.** In `db/install.php`, for each key the child declares with Boost's name, copy the Boost
  value when it is set, and copy the files of `backgroundimage` and `loginbackgroundimage` to the child's
  component as in the file step above. Never copy `preset` blindly: an uploaded preset file lives in Boost's
  `preset` area and is not present in the child's.

Do not read `get_config('theme_boost', ...)` at run time as a fallback for the child's own setting: the admin then
has two places that change one thing, and clearing the child's value silently re-enables Boost's.

The site logo, compact logo and favicon are core settings (`core_admin/logo` and its siblings in
`public/admin/settings/appearance.php`, 5.2 and 5.3), not theme settings, so they survive a theme switch unless the
theme replaces them with settings of its own.

## What is not migrated for you

- **Backups.** Theme settings are not part of any course backup. Moving a configured theme between sites means
  entering the settings again, or a script that reads and writes the `config_plugins` rows and the file areas.
- **Forced values.** A value in `$CFG->forced_plugin_settings['theme_mytheme']` in the site's `config.php` keeps
  its old key after a rename, because the upgrade cannot edit that file. Mention renamed keys in the release notes.
- **User preferences.** Renaming a preference needs its own step over the `user_preferences` table, and the
  privacy provider must list the new name.
- **Uninstall.** Core removes the theme's config rows and files when the theme is uninstalled
  (`uninstall_plugin()` in `public/lib/adminlib.php`); the theme does not need code for it.

## Release notes

Each migration gets a line in the theme's change log that names the old and new setting, says the value is carried
over, and says what an admin should check (for example "the corner radius is now a length; `8` became `8px`").
A step should not print long notices of its own during the upgrade; a line in the change log is enough.

## Testing a migration

Put the migration logic in a function or class method of its own (taking no version argument), call it from the
versioned step, and test that function in PHPUnit: `set_config()` the old key, call it, then assert the new key
holds the converted value and the old key is `false`. Cover three cases: the old value set, the old value
deliberately empty, and a value already stored under the new key.

Calling `xmldb_theme_mytheme_upgrade()` itself from a test does not work as it stands:
`upgrade_plugin_savepoint()` throws a downgrade exception when the version passed to it is lower than the
installed one, which is always the case for an old step on a current test site (`public/lib/upgradelib.php`).
