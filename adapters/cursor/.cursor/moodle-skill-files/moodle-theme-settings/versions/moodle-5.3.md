# Theme settings: what is specific to Moodle 5.3

Read this when the theme supports Moodle 5.3 and you are deciding which class names to use, reading core's setting
classes, dealing with Boost's colour mode settings, or handling a site that came from the Classic theme. It lists
only what differs from the 5.2 baseline. Read in the 5.3.0 source unless a line says it was run.

## Admin setting classes were renamed; the old names still work

In 5.3 the admin tree and setting classes moved out of `public/lib/adminlib.php` into autoloaded classes of
`core_admin`. The old global names are kept as aliases (`public/lib/db/legacyclasses.php`, and a `class_alias()` at
the end of each new file). The root `UPGRADING.md` says "Existing classes are currently unaffected".

| Old name (5.2 and 5.3) | New name (5.3 only) | Source file in 5.3.0 |
|---|---|---|
| `admin_setting` | `\core_admin\setting` | `public/admin/classes/setting.php` |
| `admin_settingpage` | `\core_admin\setting\settingpage\settingpage` | `public/admin/classes/setting/settingpage/settingpage.php` |
| `admin_settingdependency` | `\core_admin\setting\settingpage\dependency` | `public/admin/classes/setting/settingpage/dependency.php` |
| `admin_category` | `\core_admin\setting\tree\category` | `public/admin/classes/setting/tree/category.php` |
| `admin_externalpage` | `\core_admin\setting\tree\externalpage` | `public/admin/classes/setting/tree/externalpage.php` |
| `admin_setting_configtext`, `..._configselect`, `..._configcheckbox`, `..._configcolourpicker`, `..._configstoredfile`, `..._scsscode`, `..._configthemepreset`, and the rest | `\core_admin\setting\setting\configtext` and so on (the part after `admin_setting_`) | `public/admin/classes/setting/setting/<name>.php` |

What to do:

- **A theme that supports 5.2 and 5.3 uses the old global names everywhere**: in `settings.php`, in type hints and
  in `extends`. The new names do not exist on 5.2, so using one is a fatal "class not found" there. The recipe in
  `SKILL.md` was run on 5.3.0 with the old names.
- A custom setting class that extends `admin_setting_configstoredfile` (or any other) keeps working on 5.3: the
  alias and the real class are the same class, so `instanceof` checks in core accept it.
- `theme_boost_admin_settingspage_tabs` is not renamed. Its file is byte-identical in 5.2 and 5.3
  (`public/theme/boost/classes/admin_settingspage_tabs.php`).
- When reading core to check behaviour, the 5.2 code of every class is in `public/lib/adminlib.php`; in 5.3 use
  the files in the table. The behaviour described in this skill (colour validation, stored-file handling, SCSS
  validation, `hide_if()` conditions, default handling) was compared in both and is the same.
- A theme that supports 5.3 only may use the new names. Nothing is gained by mixing both in one file.

## New on the settings page class: `add_before()`

`admin_settingpage::add_before($setting, $beforesibling)` inserts a setting before a named sibling (the sibling's
name includes the plugin prefix, for example `theme_mythemeaccent`). It does not exist on 5.2. It is of little use
with the tabbed page: called on the outer tabs page it registers the setting for saving but puts it in no tab, so
the field is not drawn.

## Boost's colour mode settings and preference

5.3 adds an "Experimental" tab to Boost's settings page (`public/theme/boost/settings.php`):

| Setting | Type and default | Read by |
|---|---|---|
| `theme_boost/enablecolourmodes` | Checkbox, default off | `\theme_boost\colour_mode::is_enabled()` |
| `theme_boost/defaultcolourmode` | Select, default light; hidden while the checkbox is off | `\theme_boost\colour_mode::get_site_default()` |

- Both are read with `get_config('theme_boost', ...)`, not from the active theme's settings. They apply to Boost
  and to every theme that has Boost among its parents (`colour_mode::is_boost_theme()`).
- **A child theme does not redeclare them, and cannot override them under its own component.** A setting named
  `theme_mychild/enablecolourmodes` is never read by core. The admin switches colour modes on Boost's settings
  page even while the child is the site theme; say so in the child's documentation, or link to that page from a
  description in the child's settings.
- The user's choice is the preference `theme_boost_colourmode`, declared in `theme_boost_user_preferences()` with
  the valid modes as `choices` and light as `default`, and listed in Boost's privacy provider. A child theme reads
  the effective mode through Boost, not by reading the preference itself; the SCSS side is in `moodle-theme-scss`.
- This tab is also core's own example of the dependency rule: the `hide_if()` call is made on the outer tabs
  page, and the comment above it explains that a dependency recorded on a tab never reaches the JavaScript.
- A theme that supports 5.2 and offers its own colour settings must not assume these two keys exist: on 5.2
  `get_config('theme_boost', 'enablecolourmodes')` is `false`.

## Sites that used Classic

Classic is no longer in core in 5.3. During the upgrade, when the Classic files are not present, core copies the
Classic settings that had been customised to Boost and uninstalls Classic
(`upgrade_migrate_classic_theme_to_boost()` in `public/lib/db/upgradelib.php`; `public/theme/UPGRADING.md`).

- Copied to `theme_boost`: `unaddableblocks` (merged with Boost's own list), `brandcolor`, `scsspre`, `scss`, and
  the files and values of `backgroundimage` and `loginbackgroundimage`.
- Not copied: `preset` and uploaded preset files, and Classic's `navbardark`.
- For a theme author this matters in two ways. A child theme with `parents = ['classic', 'boost']` no longer loads
  on 5.3 unless Classic is installed as an add-on (`moodle-5-3-changes`). And the function is a compact, current
  example of copying settings and their files from one theme component to another, which is what a theme does when
  it takes over from Boost.

## Browser storage

On 5.3 the storage wrapper is `public/lib/js/esm/src/Storage.ts`. It clears the whole origin's storage on a
JavaScript revision change and on a login change, as 5.2 does, and the login check now also covers
`sessionStorage`. The conclusion is the same on both versions: per-user theme choices belong in a user preference.
