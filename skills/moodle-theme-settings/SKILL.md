---
name: moodle-theme-settings
description: Use when adding or fixing a Moodle theme's admin settings - theme settings.php, themesetting<name> section, theme_boost_admin_settingspage_tabs, admin_setting_configcolourpicker, admin_setting_configstoredfile, admin_setting_scsscode, hide_if, set_updatedcallback('theme_reset_all_caches'), $theme->settings versus get_config('theme_x'), setting to SCSS variable, setting to template context, setting_file_url / setting_file_serve / theme_x_pluginfile, renaming settings in db/upgrade.php, theme user preferences and the privacy provider that declares them; symptoms such as "Section error" from the theme selector cog, a saved setting that changes nothing, a 404 logo, or stock Boost styling after saving a setting. Skip when the task is the SCSS itself (moodle-theme-scss), layouts or templates (moodle-theme-layouts-templates), or settings of a non-theme plugin (moodle-plugin-development).
---

# Moodle Theme Settings

## Overview

How a theme declares admin settings, how each value reaches the compiled CSS, the templates and the file server,
and how to change settings later without losing what sites have saved. Everything here holds on Moodle 5.2 and 5.3
unless tagged. "Run on 5.3.0" means the behaviour was observed in a Boost child theme on Moodle 5.3.0; "read in the
source" means it was read and not run. Nothing here was run on 5.2: 5.2 statements are read in the 5.2 source.

## When to Use

- Writing or changing a theme's `settings.php`, or the code that reads its settings
- A setting must change the CSS (colour, radius, font, background image) or show something in a template
- An uploaded logo or image from a setting must be served
- Renaming, splitting or converting a setting between releases
- The theme stores a per-user choice (a drawer, a display mode) and needs a preference and a privacy provider
- **Skip when:** the question is what SCSS to write once the variable exists (use `moodle-theme-scss`); where the
  template or layout lives (`moodle-theme-layouts-templates`); a renderer or hook (`moodle-theme-renderers-output`);
  which Boost settings a child inherits and how presets work (`moodle-theme-boost-child`); testing a setting's effect
  (`moodle-theme-testing-release`); admin settings of other plugin types (`moodle-plugin-development`)

## Mental model

1. **Storage.** A setting named `theme_mytheme/accent` is one row in `config_plugins` (plugin `theme_mytheme`, name
   `accent`). Uploaded files live in the system context, component `theme_mytheme`, file area chosen by the setting,
   item id 0. Nothing else exists: no table, no backup. Uninstalling the theme deletes both.
2. **Two ways to read, with different meaning.**
   - `get_config('theme_mytheme', 'accent')` always reads this theme's own row. It returns `false` when the value
     was never stored.
   - `$theme->settings->accent` (the object passed to SCSS callbacks, or `$PAGE->theme->settings`) reads the
     settings of the **active** theme. `theme_config::load()` reads `get_config('theme_<active>')` once and hands
     that same object to every parent's `config.php` and to every parent's SCSS callback
     (`public/lib/classes/output/theme_config.php`, `load()` and `find_theme_config()`, 5.2 and 5.3).
   - So: a value that belongs to your theme is read with `get_config()`. A value that a child theme should be
     able to supply under its own component is read from `$theme->settings`. Boost's callbacks use the second
     form, which is why a child gets `brandcolor`, `scsspre`, `scss` and the background images by declaring
     settings with those names (run on 5.3.0 for `brandcolor`).
3. **When a value takes effect.** PHP and templates read the value on every request. CSS is compiled once and
   cached by theme revision, so a setting that feeds SCSS does nothing until the revision changes. The admin page
   does that through the setting's updated-callback; code that calls `set_config()` must do it itself.
4. **When a default is stored.** Defaults are written by the upgrade (CLI upgrade, or the "new settings" page the
   web upgrade shows), and on install. Between those moments a new setting has no row, and reads return `false`.
5. **The page.** Core makes a settings page object for every theme that has `settings.php` and names it
   `themesetting<name>`. The cog on the theme selector links to `admin/settings.php?section=themesetting<name>`.
   The page that core hands over is created hidden, and core adds the page to the admin tree only if it is not
   hidden. A theme therefore replaces `$settings` with its own page object of the same name
   (`public/admin/settings/appearance.php`, `public/admin/themeselector.php`, 5.2 and 5.3; read in the source).

## Default recipe

A tabbed page with a colour, a select, a dependent text field and an uploaded image. Run on 5.3.0 as shown, except
the upload path and the `theme_config::load('mytheme')` form of the file URL, which were read (see "Stored files").

### settings.php

```php
<?php
// (GPL header, then the file phpdoc with @package theme_mytheme and @copyright 2026 Your Name <you@example.com>)

defined('MOODLE_INTERNAL') || die();

if ($ADMIN->fulltree) {
    // Same name as the page core created, so the theme selector link works.
    $settings = new theme_boost_admin_settingspage_tabs('themesettingmytheme', get_string('configtitle', 'theme_mytheme'));

    // Tab: Look. The tab name becomes an HTML id, so prefix it with the component.
    $page = new admin_settingpage('theme_mytheme_look', get_string('looksettings', 'theme_mytheme'));

    $setting = new admin_setting_configcolourpicker(
        'theme_mytheme/accent',
        get_string('accent', 'theme_mytheme'),
        get_string('accent_desc', 'theme_mytheme'),
        ''
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $setting = new admin_setting_configselect(
        'theme_mytheme/corners',
        get_string('corners', 'theme_mytheme'),
        get_string('corners_desc', 'theme_mytheme'),
        'round',
        [
            'round' => get_string('corners_round', 'theme_mytheme'),
            'square' => get_string('corners_square', 'theme_mytheme'),
        ]
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    // Add the tab only after all its settings: add() copies the settings that exist at that moment.
    $settings->add($page);

    // Tab: Banner.
    $page = new admin_settingpage('theme_mytheme_banner', get_string('bannersettings', 'theme_mytheme'));

    $setting = new admin_setting_configselect(
        'theme_mytheme/bannermode',
        get_string('bannermode', 'theme_mytheme'),
        get_string('bannermode_desc', 'theme_mytheme'),
        'none',
        [
            'none' => get_string('bannermode_none', 'theme_mytheme'),
            'text' => get_string('bannermode_text', 'theme_mytheme'),
        ]
    );
    $page->add($setting);

    $setting = new admin_setting_configtext(
        'theme_mytheme/bannertext',
        get_string('bannertext', 'theme_mytheme'),
        get_string('bannertext_desc', 'theme_mytheme'),
        '',
        PARAM_TEXT
    );
    $page->add($setting);

    $setting = new admin_setting_configstoredfile(
        'theme_mytheme/bannerimage',
        get_string('bannerimage', 'theme_mytheme'),
        get_string('bannerimage_desc', 'theme_mytheme'),
        'bannerimage',
        0,
        ['maxfiles' => 1, 'accepted_types' => ['web_image']]
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $page->add($setting);

    $settings->add($page);

    // Dependencies go on the outer page, after the tab was added.
    $settings->hide_if('theme_mytheme/bannertext', 'theme_mytheme/bannermode', 'eq', 'none');
}
```

A theme with few settings can skip the tabs: `$settings = new admin_settingpage('themesettingmytheme', ...)` inside
the same `if`, then `$settings->add($setting)`.

### lib.php: setting to SCSS

```php
// (phpdoc blocks shortened in this sample.)

/** SCSS variables from this theme's settings, placed before the main SCSS. */
function theme_mytheme_get_pre_scss($theme) {
    $scss = '';
    $accent = get_config('theme_mytheme', 'accent');
    if (!empty($accent) && preg_match('/^#([0-9a-fA-F]{3}){1,2}$/', $accent)) {
        $scss .= '$mytheme-accent: ' . $accent . ";\n";
    }
    if (get_config('theme_mytheme', 'corners') === 'square') {
        $scss .= "\$mytheme-radius: 0;\n";
    }
    return $scss;
}

/** SCSS built from this theme's settings, placed after the main SCSS. */
function theme_mytheme_get_extra_scss($theme) {
    $scss = '';
    $imageurl = theme_config::load('mytheme')->setting_file_url('bannerimage', 'bannerimage');
    if (!empty($imageurl)) {
        $scss .= ".mytheme-banner { background-image: url('$imageurl'); background-size: cover; }\n";
    }
    return $scss;
}

/** Serves the files uploaded in this theme's settings. */
function theme_mytheme_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options = []) {
    if ($context->contextlevel == CONTEXT_SYSTEM && $filearea === 'bannerimage') {
        $theme = theme_config::load('mytheme');
        if (!array_key_exists('cacheability', $options)) {
            $options['cacheability'] = 'public';
        }
        return $theme->setting_file_serve($filearea, $args, $forcedownload, $options);
    }
    send_file_not_found();
}
```

`config.php` names the two callbacks (`$THEME->prescsscallback = 'theme_mytheme_get_pre_scss';`,
`$THEME->extrascsscallback = 'theme_mytheme_get_extra_scss';`). The fallback values live in the theme's SCSS, in a
file that is part of the main SCSS, so each default exists in one place:

```scss
$mytheme-accent: #b8410c !default;
$mytheme-radius: .75rem !default;
```

The pre-SCSS callback output is compiled before the main SCSS, so a value it sets wins over the `!default` line,
and an empty setting leaves the fallback in force (`theme_config::get_css_content_from_scss()`, 5.2 and 5.3).

### Setting to template

A layout file the theme owns adds the value to the template context, formatted for output:

```php
$templatecontext['bannertext'] = '';
if (get_config('theme_mytheme', 'bannermode') === 'text') {
    $templatecontext['bannertext'] = format_string((string) get_config('theme_mytheme', 'bannertext'));
}
```

```mustache
{{#bannertext}}<div class="mytheme-banner">{{{bannertext}}}</div>{{/bannertext}}
```

`format_string()` output is already escaped, so the template uses triple braces. Admin-written HTML (from
`admin_setting_confightmleditor`) goes through `format_text($html, FORMAT_HTML, ['noclean' => true])` so filters
and multi-language content apply. A theme that inherits every layout from Boost has no layout file to edit: copy
the layout (`moodle-theme-layouts-templates`), or print the value from a renderer method or an output hook
(`moodle-theme-renderers-output`).

## Rules

### The page

- **Replace `$settings`; do not add to the object core supplied.** Symptom of adding to it: the cog on the theme
  card opens "Section error", and the defaults are never stored. Fix: assign a new page named `themesetting<name>`
  as in the recipe. Source: `public/admin/settings/appearance.php` creates the page with the hidden flag set and
  adds it only `if ($settings && !$settings->hidden)` (5.2 and 5.3, read in the source; the replacement page was run
  on 5.3.0).
- **Keep the name `themesetting<name>`.** Any other name breaks the theme selector link
  (`public/admin/themeselector.php`). A theme that moves its settings to pages of its own keeps a page of that
  name too, or redirects from it: see [reference/large-settings-pages.md](reference/large-settings-pages.md).
- **Build settings only inside `if ($ADMIN->fulltree)`.** Outside it, every page load that builds the admin
  navigation pays for the file-area queries and string lookups. Source: `public/theme/boost/settings.php`.
- **Add the tab after its settings.** `theme_boost_admin_settingspage_tabs::add()` copies the tab's settings into the
  outer page when it is called. A setting added to the tab later is drawn but never saved. Source:
  `public/theme/boost/classes/admin_settingspage_tabs.php` (identical in 5.2 and 5.3).
- **`hide_if()` goes on the outer tabs page, after the tab was added.** `admin/settings.php` reads dependencies
  from the top page only, and `add()` does not copy a tab's dependencies. Symptom on the tab: the field never
  hides. Conditions: `checked`, `notchecked`, `noitemselected`, `eq`, `neq`, `in` (values separated by `|`); the
  setting is hidden when the condition is true. Source: `public/theme/boost/settings.php` (5.3 comment),
  `public/lib/amd/src/showhidesettings.js`.
- **`hide_if()` only hides the field.** The stored value stays and is still returned by `get_config()`. Code that
  uses a dependent setting checks the controlling setting too, as the template sample does.

### Reading values

- **A value may be missing.** `get_config()` gives `false`, `$theme->settings->x` is an undefined property. Use
  `!empty()` or `??`, and compare selects with `===` against the stored string. Checkbox values are the strings
  `'1'` and `'0'`.
- **Inside `config.php`, `$THEME->settings` is the active theme's settings**, including when this file is loaded as
  a parent of a child theme. Use `get_config('theme_mytheme', ...)` for a value that must be this theme's own; it
  is cached, but it throws before the database exists, so guard it with `during_initial_install()`.
- **Forced values work.** `$CFG->forced_plugin_settings['theme_mytheme']['accent']` in the site `config.php` is
  what `get_config()` returns; the admin page shows the field as defined in config.

### Reaching the CSS

- **Every setting that feeds SCSS, and every file setting, needs
  `$setting->set_updatedcallback('theme_reset_all_caches')`.** Symptom without it: the value is saved and the site
  looks the same until someone purges caches. The callback runs only when the admin page saves a changed value.
  After `set_config()` in a script, an upgrade step or a test, call `theme_reset_all_caches()` yourself; from the
  command line, `php admin/cli/cfg.php --component=theme_mytheme --name=accent --set='#123456'` then
  `php admin/cli/purge_caches.php --theme`. Source: `public/lib/outputlib.php`, `public/theme/boost/settings.php`.
- **Validate the value again where it is written into SCSS.** A value that is not valid SCSS breaks the whole
  compile, and the site then serves Boost's stock CSS with none of the theme's rules (run on 5.3.0; the error shows
  only with developer debugging, and for the stylesheet request only in the PHP error log). The setting class
  validates on the admin page, but `set_config()`, `cfg.php` and forced config do not. Fix: a pattern check before
  emitting, as in the recipe. The colour picker also accepts colour names, `rgb()`, `rgba()`, `hsl()`, `hsla()`,
  `transparent`, `currentColor` and `inherit`; widen the check if the theme should accept them, and remember that
  Sass colour functions fail on `inherit` and `currentColor`.
- **One route per value.** Settings become SCSS variables in the pre-SCSS callback, or rules in the extra-SCSS
  callback. Do not add a third route such as `[[setting:name]]` placeholders: core replaces only `[[pix:...]]` and
  `[[font:...]]` (`theme_config::post_process()`, 5.2 and 5.3), so the theme would have to substitute them itself,
  the files stop being valid SCSS, and the defaults end up in several places. Choosing between a variable, a CSS
  custom property and a body class: [reference/setting-to-css.md](reference/setting-to-css.md).
- **Do not repeat what Boost's callbacks emit.** In a Boost child, Boost's pre and extra callbacks already run
  with the child's settings. A child that also appends its `scss` setting gets the admin's SCSS twice. The table
  below lists the names Boost reads.
- **Right after saving, one page load can still show the old CSS.** Boost sets `$THEME->usefallback = true`, and
  the fallback copy is sent once while the new CSS builds (`public/theme/styles.php`, read in the source). Reload
  before concluding that a setting has no effect; `moodle-theme-development` has the cache rules.

### Stored files

Three parts must name the same file area: the fourth argument of `admin_setting_configstoredfile`, the area checked
in `theme_<name>_pluginfile()`, and the second argument of `setting_file_url($settingname, $filearea)`. The setting
value is the path of the first file (`/logo.png`), not a URL. The upload-and-serve path is read in the source, not
run.

- **Leave the item id at 0.** `setting_file_serve()` looks the file up at item id 0 whatever the setting used.
  Symptom of another item id: the upload saves and the URL returns 404.
- **Keep the updated-callback on file settings, even ones not used in CSS.** `setting_file_url()` puts the theme
  revision in the URL, and `setting_file_serve()` lets browsers cache the file for 60 days. Without a revision
  change a replaced image keeps its old URL and visitors keep the old file.
- **Use the theme's own config object for its own files.** `$theme->setting_file_url()` builds the URL from the
  active theme's settings and component, so under a child theme it points at the child. For a file that belongs to
  this theme use `theme_config::load('mytheme')->setting_file_url(...)`, as the recipe does.
- **Do not require login in `pluginfile` for a logo or background** that the login page shows.
- **In a test or script** a file setting cannot be set with `set_config()` alone: create the file in the area
  with the file storage API, then store `'/' . $filename` as the value.

Source for this section: `theme_config::setting_file_url()` and `setting_file_serve()` in
`public/lib/classes/output/theme_config.php`; `public/theme/boost/lib.php` (`theme_boost_pluginfile()`); identical
in 5.2 and 5.3.

### Defaults and later changes

- **A new setting needs a version bump to get its default stored.** Symptom without one: `get_config()` returns
  `false`, a select on the settings page shows its first option next to a different "Default:", and pressing Save
  then stores whatever is shown, for every such setting on the page. Fix: bump `$plugin->version` and run the
  upgrade, and write the reading code so that a missing value means the default. After adding settings, open the
  page and compare each shown value with its "Default:" line. Source: `admin_apply_default_settings()` and
  `any_new_admin_settings()` in `public/lib/adminlib.php`; `admin/cli/upgrade.php`.
- **A colour picker with a non-empty default cannot be emptied.** An empty submission is replaced by the default.
  Use `''` as the default and keep the fallback in SCSS (as Boost's `brandcolor` does), or pass `null, false` as
  the fifth and sixth constructor arguments.
- **Renaming or converting a setting is an upgrade step**, not an edit of `settings.php`: copy the old value, unset
  the old name, reset the theme caches. Recipe and traps:
  [reference/upgrade-migration.md](reference/upgrade-migration.md).
- **Every theme needs a privacy provider**, a null provider when it stores nothing about users, and a
  user-preference provider as soon as it sets one preference. Core's privacy unit test covers every installed
  plugin and is not part of `moodle-plugin-ci`, so a missing provider surfaces late:
  [reference/user-preferences-privacy.md](reference/user-preferences-privacy.md).

## Setting names that already mean something

Read from the active theme's settings, so a Boost child declares them under its own component to keep the feature.
Read in `public/theme/boost/lib.php` and `public/lib/blocklib.php`, 5.2 and 5.3.

| Name | Read by | If the child does not declare it |
|---|---|---|
| `brandcolor` | Boost pre-SCSS: becomes `$primary` | Primary colour comes from the preset |
| `scsspre`, `scss` | Boost pre-SCSS and extra-SCSS | No raw SCSS boxes for admins |
| `backgroundimage`, `loginbackgroundimage` | Boost extra-SCSS, with file areas of the same names under the active theme's component; needs those areas in the child's `pluginfile` | No custom backgrounds |
| `preset` | Boost's main-SCSS function, when the child passes its own theme object to it | Default preset; details in `moodle-theme-boost-child` |
| `unaddableblocks` | Core block manager, comma-separated block names hidden from "Add a block" | Boost's default list (`navigation,settings,course_list`) no longer applies, and those blocks become addable |

**5.3+:** `enablecolourmodes` and `defaultcolourmode` are read from `theme_boost` itself, not from the active
theme: a child does not redeclare them. See [versions/moodle-5.3.md](versions/moodle-5.3.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `$settings->add(...)` on the page core supplied | "Section error" from the theme selector; no defaults stored | Replace `$settings` with a page named `themesetting<name>` |
| Adding a setting to a tab after `$settings->add($tab)` | The field shows and its value is never saved | Add the tab last |
| `$tab->hide_if(...)` | The dependent field never hides | Call `hide_if()` on the outer tabs page |
| No updated-callback on a colour or file setting | Saved, but the CSS or the image does not change | `set_updatedcallback('theme_reset_all_caches')` |
| Setting value written into SCSS unchecked | One bad value: the site shows stock Boost styling | Pattern check before emitting; skip when it fails |
| `$theme->settings->x` for the theme's own value | Wrong or missing value when a child theme is active | `get_config('theme_mytheme', 'x')` |
| Appending the `scss` or `scsspre` setting in a Boost child's callback | The admin's SCSS is compiled twice | Leave it to Boost's callback |
| `[[setting:name]]` in SCSS or CSS | The placeholder reaches the browser as text | A variable from the pre-SCSS callback |
| Default colour repeated in `settings.php`, PHP and SCSS | The copies drift; an empty setting gives a different colour from the stated default | Empty setting default, `!default` in SCSS |
| HTML in a select or multicheckbox choice label | Shown escaped in the "Default:" line and mangled in admin search | Plain-text labels; HTML in the description |
| `admin_setting_configtext` pattern with a modifier, such as `'/^\p{L}+$/u'` | Not seen as a pattern, so `clean_param()` throws `coding_exception: Unknown parameter type` when the value is validated: while defaults are applied on install or upgrade, and on save (read) | End the pattern with `/`: `'/(*UTF)^\p{L}+$/'` |
| A file setting created with a non-zero item id | URL returns 404 | Item id 0 |
| New setting without a version bump | First option shown instead of the default; Save stores it | Bump the version; read with a fallback |
| Renaming a setting by editing its name | Every site loses the saved value | An upgrade step that copies the value |
| A per-user choice kept in `localStorage` | Lost at each login and each JavaScript cache purge | A declared user preference |
| `null_provider` in a theme that sets a user preference | The data export misses it; a reviewer rejects it | `user_preference_provider` |

## Reference files

| File | Read it when |
|---|---|
| [reference/setting-types.md](reference/setting-types.md) | Choosing a setting class or its arguments: what each stores, what it validates, text patterns, HTML editor, multi-file areas, the preset selector, headings |
| [reference/setting-to-css.md](reference/setting-to-css.md) | A setting must change the look and the choice between an SCSS variable, a CSS custom property, an extra-SCSS rule or a body class is open; values with units, fonts, dark mode |
| [reference/large-settings-pages.md](reference/large-settings-pages.md) | The theme has more than a few dozen settings, needs several pages or its own capability, will have child themes, or you are reviewing a large theme's settings code |
| [reference/upgrade-migration.md](reference/upgrade-migration.md) | A released theme renames, removes, splits or converts a setting or a file area, adds `db/install.php`, or replaces Boost on a site that had Boost settings |
| [reference/user-preferences-privacy.md](reference/user-preferences-privacy.md) | The theme stores anything per user, sets a preference from JavaScript, or needs its `classes/privacy/provider.php` written |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md): admin setting classes renamed (old names still work), Boost's colour mode settings and preference, `add_before()`, Classic settings migration |

## References

- https://moodledev.io/docs/apis/subsystems/admin
- https://moodledev.io/docs/5.3/apis/plugintypes/theme
- https://moodledev.io/docs/apis/subsystems/privacy
- Core source, relative to the Moodle root: `public/theme/boost/settings.php`, `public/theme/boost/lib.php`,
  `public/theme/boost/classes/admin_settingspage_tabs.php`, `public/admin/settings/appearance.php`,
  `public/lib/classes/output/theme_config.php`, `public/lib/adminlib.php`
