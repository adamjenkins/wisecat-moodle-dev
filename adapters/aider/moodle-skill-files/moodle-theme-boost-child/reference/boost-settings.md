# Offering Boost's settings in a child theme

Read this when the child must offer Boost's own settings (brand colour, raw SCSS, background images, unaddable
blocks, presets), needs its own preset uploads, or a site is moving from Boost to the child and must keep its look.

## Why the child needs its own copy

When a child is the active theme, core gives Boost's functions the child's settings object
(`theme_config::load()`, `get_pre_scss_code()`, `get_extra_scss_code()` in
`public/lib/classes/output/theme_config.php`, same code in 5.2 and 5.3.0). Boost's functions then look for these
names in `theme_<child>`:

| Name | Where Boost reads it (`public/theme/boost/lib.php` unless stated) | Effect |
|---|---|---|
| `brandcolor` | `theme_boost_get_pre_scss()` | Emits `$primary: <value>;` |
| `scsspre` | `theme_boost_get_pre_scss()` | Raw SCSS before everything |
| `scss` | `theme_boost_get_extra_scss()` | Raw SCSS after the main SCSS, before the child's extra SCSS |
| `backgroundimage` | `theme_boost_get_extra_scss()` through `$theme->setting_file_url()` | `body` background image from 768px up |
| `loginbackgroundimage` | same | Login page image; Boost's default image when empty |
| `unaddableblocks` | `block_manager::get_unaddable_by_theme_block_types()` in `public/lib/blocklib.php` | Blocks left out of "Add a block" |
| `preset` | `theme_boost_get_main_scss_content()` | Only when the child passes its own config to that function |

A value saved under `theme_boost` is not seen. Run on 5.3.0 for `brandcolor`: saved under the child's component
it recoloured `.btn-primary` with no code in the child. The other rows are read in the source.

`$theme->setting_file_url()` builds the URL with the component `theme_<active theme>`, so the two images are
served by the child's `pluginfile` function, not Boost's.

**5.3+:** `enablecolourmodes` and `defaultcolourmode` are different: Boost reads them with
`get_config('theme_boost', ...)` (`public/theme/boost/classes/colour_mode.php`), so they stay on Boost's settings
page and apply to every descendant. Do not mirror them.

## settings.php that mirrors Boost's

Boost is always installed, so its lang strings can be reused. The setting classes are written with their global
names, which exist on 5.2 and are aliases on 5.3.

```php
<?php
// (GPL header)

/**
 * Theme settings.
 *
 * @package    theme_example
 * @copyright  2016 Ryan Wyllie
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

if ($ADMIN->fulltree) {
    $settings = new theme_boost_admin_settingspage_tabs('themesettingexample', get_string('configtitle', 'theme_example'));

    // General tab.
    $page = new admin_settingpage('theme_example_general', get_string('generalsettings', 'theme_boost'));

    $setting = new admin_setting_configtext(
        'theme_example/unaddableblocks',
        get_string('unaddableblocks', 'theme_boost'),
        get_string('unaddableblocks_desc', 'theme_boost'),
        'navigation,settings,course_list',
        PARAM_TEXT
    );
    $page->add($setting);

    $setting = new admin_setting_configstoredfile(
        'theme_example/backgroundimage',
        get_string('backgroundimage', 'theme_boost'),
        get_string('backgroundimage_desc', 'theme_boost'),
        'backgroundimage'
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $setting = new admin_setting_configstoredfile(
        'theme_example/loginbackgroundimage',
        get_string('loginbackgroundimage', 'theme_boost'),
        get_string('loginbackgroundimage_desc', 'theme_boost'),
        'loginbackgroundimage'
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    // An empty default lets the preset decide the colour.
    $setting = new admin_setting_configcolourpicker(
        'theme_example/brandcolor',
        get_string('brandcolor', 'theme_boost'),
        get_string('brandcolor_desc', 'theme_boost'),
        ''
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $settings->add($page);

    // Advanced tab.
    $page = new admin_settingpage('theme_example_advanced', get_string('advancedsettings', 'theme_boost'));

    $setting = new admin_setting_scsscode(
        'theme_example/scsspre',
        get_string('rawscsspre', 'theme_boost'),
        get_string('rawscsspre_desc', 'theme_boost'),
        '',
        PARAM_RAW
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $setting = new admin_setting_scsscode(
        'theme_example/scss',
        get_string('rawscss', 'theme_boost'),
        get_string('rawscss_desc', 'theme_boost'),
        '',
        PARAM_RAW
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $settings->add($page);
}
```

Rules that make this file work:

- The variable is `$settings` and the first argument is `themesetting<name>`. Core creates an
  `admin_settingpage` with that name before including the file, and afterwards adds whatever `$settings` holds
  to the Themes category (`public/admin/settings/appearance.php`, 5.3.0). The theme selector's settings link
  points at the section `themesetting<name>` (`public/admin/themeselector.php`), so a page under another name is
  not reached from there. Run on 5.3.0 with two tabs.
- Every setting that changes CSS calls `set_updatedcallback('theme_reset_all_caches')`. Without it the saved
  value shows only after someone purges the caches.
- The copyright line above ours credits the author of the file this one mirrors, as written in
  `public/theme/boost/settings.php`. A file that adapts another author's code keeps that author's line.
- Adding these settings to an installed theme needs a `version.php` bump, or their defaults are never stored.

## pluginfile for the two image areas

```php
/**
 * Serves the files uploaded in this theme's settings.
 *
 * @param stdClass $course
 * @param stdClass $cm
 * @param context $context
 * @param string $filearea
 * @param array $args
 * @param bool $forcedownload
 * @param array $options
 * @return bool
 */
function theme_example_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options = []) {
    $areas = ['backgroundimage', 'loginbackgroundimage'];
    if ($context->contextlevel == CONTEXT_SYSTEM && in_array($filearea, $areas, true)) {
        $theme = \core\output\theme_config::load('example');
        // Theme files are public by design: the login page needs them before anyone is logged in.
        if (!array_key_exists('cacheability', $options)) {
            $options['cacheability'] = 'public';
        }
        return $theme->setting_file_serve($filearea, $args, $forcedownload, $options);
    }
    send_file_not_found();
}
```

Modelled on `theme_boost_pluginfile()`. Symptom without it: the background rule is in the CSS but the image
request returns "file not found". Read in the source; a child's stored-file setting was rendered on 5.3.0 but
not exercised with an upload. `setting_file_serve()` serves from the component `theme_<name of the config
loaded>`, so load the child here, not Boost.

Any further stored-file setting of the child's own adds its file area to `$areas`. `moodle-theme-settings` covers
that setting type.

## Presets: three ways

`theme_boost_get_main_scss_content($theme)` picks by `$theme->settings->preset`: `default.scss`, `plain.scss`,
or a file in the file area `theme_boost` / `preset` (the component is fixed in the function), falling back to
`default.scss`.

### 1. Follow Boost's choice (run on 5.3.0)

```php
$boost = \core\output\theme_config::load('boost');
$scss = theme_boost_get_main_scss_content($boost);
```

The admin chooses and uploads presets on Boost's settings page. Changing that setting resets the theme caches
for every theme, so the child is rebuilt too.

### 2. One fixed preset (read in the source)

```php
$scss = file_get_contents($CFG->dirroot . '/theme/boost/scss/preset/default.scss');
```

Use this when the child's SCSS depends on things only the default preset provides, such as `$mds-*` token
variables. The plain preset does not import the design tokens, so such a child fails to compile if an admin
switches Boost to `plain.scss` under way 1.

### 3. The child's own preset setting and uploads (read in the source, not run)

Settings, added to the General tab:

```php
    $context = context_system::instance();
    $files = get_file_storage()->get_area_files($context->id, 'theme_example', 'preset', 0,
        'itemid, filepath, filename', false);
    $choices = [];
    foreach ($files as $file) {
        $choices[$file->get_filename()] = $file->get_filename();
    }
    $choices['default.scss'] = 'default.scss';
    $choices['plain.scss'] = 'plain.scss';

    $setting = new admin_setting_configthemepreset(
        'theme_example/preset',
        get_string('preset', 'theme_boost'),
        get_string('preset_desc', 'theme_boost'),
        'default.scss',
        $choices,
        'example'
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $setting = new admin_setting_configstoredfile(
        'theme_example/presetfiles',
        get_string('presetfiles', 'theme_boost'),
        get_string('presetfiles_desc', 'theme_boost'),
        'preset',
        0,
        ['maxfiles' => 20, 'accepted_types' => ['.scss']]
    );
    $page->add($setting);
```

The last argument of `admin_setting_configthemepreset` is the theme name without `theme_`. On save it loads that
theme and test-compiles an uploaded preset with that theme's pre and extra SCSS, and refuses a preset that does
not compile (`public/admin/classes/setting/setting/configthemepreset.php` on 5.3.0, `public/lib/adminlib.php` on
5.2). Passing `'boost'` here would validate against the wrong file area.

The lookup, replacing the Boost call in `theme_example_get_main_scss_content()`:

```php
    $name = get_config('theme_example', 'preset');
    $context = context_system::instance();
    $fs = get_file_storage();
    if ($name === 'plain.scss') {
        $scss = file_get_contents($CFG->dirroot . '/theme/boost/scss/preset/plain.scss');
    } else if ($name && $name !== 'default.scss'
            && ($file = $fs->get_file($context->id, 'theme_example', 'preset', 0, '/', $name))) {
        $scss = $file->get_content();
    } else {
        $scss = file_get_contents($CFG->dirroot . '/theme/boost/scss/preset/default.scss');
    }
```

An uploaded preset is a whole SCSS entry point: it has to import `bootstrap` and `moodle` itself, as Boost's
presets do. The preset files do not need serving through `pluginfile`; they are read on the server only.

## Moving a site from Boost to the child without losing its look

Symptom: after the site theme is switched to the child, the brand colour, custom SCSS and background images are
gone. Nothing was deleted; the values live under `theme_boost` and the child reads `theme_example`.

Copy them once when the child is installed. This is modelled on core's own
`upgrade_migrate_classic_theme_to_boost()` (`public/lib/db/upgradelib.php`, 5.3.0), which moves the same
settings between two themes. Read in the source, not run.

```php
<?php
// (GPL header)

/**
 * Install steps.
 *
 * @package    theme_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

/**
 * Copies the site's Boost look into this theme's own settings.
 */
function xmldb_theme_example_install() {
    foreach (['unaddableblocks', 'brandcolor', 'scsspre', 'scss'] as $name) {
        $value = get_config('theme_boost', $name);
        if ($value !== false && $value !== '') {
            set_config($name, $value, 'theme_example');
        }
    }

    $context = context_system::instance();
    $fs = get_file_storage();
    foreach (['backgroundimage', 'loginbackgroundimage'] as $area) {
        $files = $fs->get_area_files($context->id, 'theme_boost', $area, 0, 'id', false);
        if (!$files) {
            continue;
        }
        set_config($area, (string) get_config('theme_boost', $area), 'theme_example');
        foreach ($files as $file) {
            $fs->create_file_from_storedfile(['component' => 'theme_example'], $file);
        }
    }
}
```

Put it in `db/install.php`. For a theme that is already installed, do the same in a `db/upgrade.php` step behind
a version check and a savepoint, and only where the child's value is still unset, so an admin's later choice is
not overwritten. Say in the release notes that the copy happens once: later changes on Boost's page do not follow.

Things this does not move: logo, compact logo and favicon are core settings (`core_admin`), not Boost's, and
already apply to every theme. Uploaded preset files stay in Boost's file area; under way 1 they keep working.

## A zero is dropped

`theme_boost_get_pre_scss()` skips a value with `if (empty($value)) { continue; }`. If you extend the same
pattern for the child's own settings, a setting saved as `0` never reaches the SCSS, and after an upgrade a new
setting has no value at all until its default is stored. Give every variable the child's SCSS uses a `!default`
in `pre.scss`, test with `!== false && !== ''` instead of `empty()` where zero is a real value, and prefer string
choices such as `'yes'` and `'no'` to numeric ones for settings that feed SCSS.
