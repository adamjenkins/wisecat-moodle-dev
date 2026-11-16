---
name: moodle-theme-boost-child
description: Use when building or fixing a Moodle theme whose config.php has $THEME->parents = ['boost'] (a Boost child) or ['boost_union', 'boost'] (a grandchild) - the minimal config.php, lib.php, version.php and lang file, which $THEME keys must be restated (rendererfactory, haseditswitch, usescourseindex, requiredblocks), theme_boost_get_main_scss_content and presets, why brandcolor, scsspre or the background image is ignored, a child that lost the edit switch, the course index or its renderer overrides, screenshot, favicon and the null privacy provider, and what breaks when Boost changes between 5.2 and 5.3. Skip when the question is the SCSS itself or a theme that renders as plain Boost (moodle-theme-scss), layouts or templates (moodle-theme-layouts-templates), renderers or hooks (moodle-theme-renderers-output), the settings page (moodle-theme-settings), or choosing between a child and a stand-alone theme (moodle-theme-development).
---

# Moodle Boost child theme

## Overview

A Boost child is a theme that lists `boost` in `$THEME->parents` and adds only what differs. Core hands it Boost's
layouts, templates, renderers, SCSS callbacks and fallback CSS, but not Boost's feature switches and not Boost's
saved settings. This skill gives the smallest child that works on Moodle 5.2 and 5.3, and the rules about what is
and is not inherited. The recipe was built and checked on Moodle 5.3.0 ("run on 5.3.0"); nothing was run on 5.2,
so every 5.2 statement is "read in the 5.2 source".

## When to Use

- Starting a theme that should look like Boost with a different brand, extra SCSS, a few settings or overrides
- A child theme ignores a Boost setting, loses the edit switch or course index, or shows navigation blocks again
- Building on top of another Boost child (a grandchild), or making a child safe to be a parent
- Moving a child theme between Moodle versions
- **Skip when:** you are deciding what kind of theme to build, or need the selection order, caches and purge
  commands (use `moodle-theme-development`); the theme renders as plain Boost after an SCSS change
  (`moodle-theme-scss`); the work is inside one area, where the sibling owns the detail:
  `moodle-theme-scss`, `moodle-theme-layouts-templates`, `moodle-theme-renderers-output`, `moodle-theme-settings`,
  `moodle-theme-testing-release`

## Mental model: three kinds of inheritance

Core treats a child's parents in three different ways. Knowing which one applies answers most child-theme questions.
Source for all rows: `public/lib/classes/output/theme_config.php`, identical in 5.2 and 5.3.0 except one font path.

| Kind | What it covers | What the child does |
|---|---|---|
| Looked up through the parents: the child, then the nearest parent that has it | layout files, layout table, Mustache templates, renderer classes, `scss`, `iconsystem`, region name strings; also `editor_scss`, images and fonts, where with two parents the farthest is asked before the nearer | Nothing. Add a file or a key only to replace the parent's |
| Chained: every parent's runs, then the child's | `prescsscallback`, `extrascsscallback`, `precompiledcsscallback`, `sheets`, `javascripts` | Add only its own part. Never repeat Boost's |
| Not inherited: the child's value or core's default | `rendererfactory`, `usefallback`, `requiredblocks`, `addblockposition`, `haseditswitch`, `usescourseindex`, `activityheaderconfig`, `yuicssmodules`, `removedprimarynavitems`, favicon | Restate Boost's value in `config.php` |

Two facts sit on top of that table:

- **One settings object.** Core loads `get_config('theme_<active theme>')` once and gives that same object to the
  child's and to every parent's `config.php`, and each chained callback receives the child's `theme_config`. So
  when the child is active, `theme_boost_get_pre_scss($theme)` reads `brandcolor` and `scsspre` from
  `theme_<child>`, not from `theme_boost` (`theme_config::load()` and `get_pre_scss_code()`; run on 5.3.0: a
  `brandcolor` saved under the child's component recoloured `.btn-primary` with no child code).
- **Boost's layouts are always the base.** The layout table starts from Boost's, then each parent's, then the
  child's entries. A child with no `$THEME->layouts` gets every Boost layout (run on 5.3.0 with one entry
  replaced: all other layouts came from Boost).

The exact rule for every key and asset type, including which parent wins when there are two, is in
[reference/inheritance.md](../moodle-skill-files/moodle-theme-boost-child/reference/inheritance.md).

## The default recipe

```
theme/example/                 (public/theme/example in the Moodle tree, or $CFG->themedir/example)
  version.php
  config.php
  lib.php
  settings.php                 optional; see "Boost's settings"
  lang/en/theme_example.php
  classes/privacy/provider.php
  scss/example/pre.scss
  scss/example/post.scss
  pix/screenshot.png  pix/favicon.ico  pix/icon.svg
  LICENSE                      GPL text in the root; moodle-plugin-release has the package rules
```

### version.php

```php
<?php
// (GPL header)

/**
 * Version information.
 *
 * @package    theme_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'theme_example';
$plugin->version   = 2026111600;
$plugin->release   = '1.0.0';
$plugin->requires  = 2026042000;                        // Moodle 5.2.0.
$plugin->supported = [502, 503];
$plugin->maturity  = MATURITY_STABLE;
$plugin->dependencies = ['theme_boost' => 2026042000];  // Boost as shipped with 5.2.
```

Declare the dependency: the child calls Boost's functions and reads Boost's files. A 5.3-only theme uses the
values in [versions/moodle-5.3.md](../moodle-skill-files/moodle-theme-boost-child/versions/moodle-5.3.md). Every PHP file below starts with the same GPL header
and file docblock; the samples shorten both to a comment line.

### config.php

```php
<?php
// (GPL header)

// (file docblock as in version.php: Theme configuration: a child of Boost)

defined('MOODLE_INTERNAL') || die();

require_once(__DIR__ . '/lib.php');

$THEME->name = 'example';
$THEME->parents = ['boost'];

// All CSS comes from SCSS. Leave editor_scss unset so Boost's editor styles are inherited.
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->usefallback = true;

// Main SCSS: this theme's pre.scss, then Boost's preset, then this theme's post.scss.
$THEME->scss = function ($theme) {
    return theme_example_get_main_scss_content($theme);
};
// Boost's own pre and extra callbacks already run for a child. These add only this theme's part.
$THEME->prescsscallback = 'theme_example_get_pre_scss';
$THEME->extrascsscallback = 'theme_example_get_extra_scss';

// Not inherited: restate Boost's values (public/theme/boost/config.php).
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
$THEME->requiredblocks = '';
$THEME->addblockposition = BLOCK_ADDBLOCK_POSITION_FLATNAV;
$THEME->iconsystem = \core\output\icon_system::FONTAWESOME; // Inherited; restated so the file reads whole.
$THEME->haseditswitch = true;
$THEME->usescourseindex = true;
$THEME->yuicssmodules = [];
$THEME->activityheaderconfig = ['notitle' => true];
```

No `$THEME->layouts`: add an entry only for a layout the child replaces (`moodle-theme-layouts-templates`).
Boost's `config.php` is identical in 5.2 and 5.3.0, so this file is the same for both.

### lib.php

```php
<?php
// (GPL header)

// (file docblock as in version.php: Theme callbacks)

/**
 * The main SCSS: Boost's preset wrapped in this theme's pre and post files.
 * @param \core\output\theme_config $theme the theme being built: this theme, or a child of it
 * @return string SCSS
 */
function theme_example_get_main_scss_content($theme) {
    global $CFG;

    require_once($CFG->dirroot . '/theme/boost/lib.php');
    $pre = file_get_contents(__DIR__ . '/scss/example/pre.scss');
    $post = file_get_contents(__DIR__ . '/scss/example/post.scss');
    // Boost reads the preset choice from the settings of the config it is given. Passing Boost's own config
    // follows the preset chosen on Boost's settings page. See "Presets" for the other two choices.
    $boost = \core\output\theme_config::load('boost');
    return $pre . "\n" . theme_boost_get_main_scss_content($boost) . "\n" . $post;
}

/**
 * SCSS variables from this theme's settings, placed before everything else.
 * @param \core\output\theme_config $theme
 * @return string SCSS
 */
function theme_example_get_pre_scss($theme) {
    $scss = '';
    $accent = get_config('theme_example', 'accentcolour');
    if (!empty($accent) && preg_match('/^#[0-9a-fA-F]{3,8}$/', $accent)) {
        $scss .= '$example-accent: ' . $accent . ";\n";
    }
    return $scss;
}

/**
 * SCSS built from this theme's settings, placed after everything else.
 * @param \core\output\theme_config $theme
 * @return string SCSS
 */
function theme_example_get_extra_scss($theme) {
    return '';
}
```

Use `__DIR__` for the theme's own files: it also works when the theme is installed in `$CFG->themedir`, and
survives a rename. Read the theme's own settings with `get_config('theme_example', ...)`, not `$theme->settings`,
so the function still works when a grandchild is the active theme.

### scss/example/pre.scss and post.scss

```scss
// pre.scss. The pre-SCSS callbacks run before this file, so a value from a setting wins over these defaults.
$example-accent: #b8410c !default;
$example-radius: 0.75rem !default;

// Bootstrap variables go here, before Boost's preset reads them.
$border-radius: $example-radius !default;
$card-border-radius: $example-radius !default;

// post.scss. Rules added after Boost's preset.
.example-banner {
    padding: 0.75rem 1rem;
    border-left: 0.5rem solid $example-accent;
    background-color: var(--bs-tertiary-bg);
    color: var(--bs-body-color);
}

[data-bs-theme="dark"] .example-banner {
    border-left-color: lighten($example-accent, 25%);
}
```

Colours for surfaces and text come from `--bs-*` custom properties, because on 5.3 a child follows Boost's
colour mode whether it wants to or not (see "Common mistakes"). Everything else about writing the SCSS is in
`moodle-theme-scss`.

### lang/en/theme_example.php

```php
<?php
// (GPL header)

// (file docblock as in version.php: Strings for the Example theme)

defined('MOODLE_INTERNAL') || die();

$string['choosereadme'] = 'Example is a child theme of Boost with a different accent colour.';
$string['configtitle'] = 'Example';
$string['pluginname'] = 'Example';
$string['privacy:metadata'] = 'The Example theme does not store any personal data.';
```

`pluginname` and `choosereadme` are required (the theme selector shows both). Region names such as
`region-side-pre` fall back to the parents' and then Boost's strings, so a child that adds no region needs none.
Keep the keys in alphabetical order: moodle-cs reports unordered keys as a warning
(`moodle.Files.LangFilesOrdering`), which fails a CI run that allows no warnings.

### classes/privacy/provider.php

```php
<?php
// (GPL header)

namespace theme_example\privacy;

// (class docblock with @package, @copyright and @license: This theme stores no personal data)
class provider implements \core_privacy\local\metadata\null_provider {
    /** The lang string that says why nothing is stored. */
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

- Every plugin type needs a provider, themes included: core's `provider_test::test_all_providers_compliant()`
  lists every plugin (`public/privacy/tests/privacy/provider_test.php`, 5.3.0). `moodle-plugin-ci phpunit` runs
  only the plugin's own tests, so a missing provider passes CI and is found by a reviewer or a full core run.
- The child does not declare Boost's preferences (`drawer-open-index`, `drawer-open-block`, **5.3+:**
  `theme_boost_colourmode`): they belong to `theme_boost`, which exports them itself.
- A child that adds its own user preference is no longer a null provider. `moodle-theme-settings` has that provider.

## What the compiled stylesheet contains, in order

1. Pre SCSS from `theme_boost_get_pre_scss()`: `$primary` from the child's `brandcolor`, then the child's `scsspre`
2. Pre SCSS from `theme_example_get_pre_scss()`
3. `pre.scss`, Boost's preset (which imports Bootstrap, Font Awesome and Boost's `moodle` partials), `post.scss`
4. Extra SCSS from `theme_boost_get_extra_scss()`: the child's `scss` setting, background and login images
5. Extra SCSS from `theme_example_get_extra_scss()`

Plugins' `styles.css` files are placed before all of this in the served sheet, so a theme rule beats a plugin rule
of equal specificity (`theme_config::get_css_files()`, 5.3.0). `@import "moodle"` and other names resolve through
the child's `scss/` directory first and Boost's second, so a file in the child with the same name as a Boost
partial replaces it; choose names that do not collide (hence `scss/example/`).

## Boost's settings: the child has its own copy, or none

Because of the one settings object, Boost's settings page does not affect an active child. These Boost features
read the child's settings and stay off until the child offers a setting with the same name:

| Setting name under `theme_<child>` | Read by | Without it |
|---|---|---|
| `brandcolor` | `theme_boost_get_pre_scss()` | Brand colour comes from the preset only |
| `scsspre`, `scss` | `theme_boost_get_pre_scss()`, `theme_boost_get_extra_scss()` | No raw SCSS boxes for the admin |
| `backgroundimage`, `loginbackgroundimage` | `theme_boost_get_extra_scss()` | No page background; login page shows Boost's default image |
| `unaddableblocks` | `block_manager::get_unaddable_by_theme_block_types()` | Navigation, Administration and Courses blocks are offered in "Add a block" |
| `preset` | `theme_boost_get_main_scss_content($theme)` when given the child's config | Default preset |

Symptom when ignored: an admin switches the site from Boost to the child and the brand colour, custom SCSS and
background image disappear, although nothing was deleted. Fix: declare the same setting names under the child's
component and serve the two image areas from the child's `pluginfile` function. The complete `settings.php`,
the `pluginfile` function, the preset choices and a script that copies a site's Boost values across are in
[reference/boost-settings.md](../moodle-skill-files/moodle-theme-boost-child/reference/boost-settings.md). Page design, setting types and `hide_if` are in
`moodle-theme-settings`.

## Presets

`theme_boost_get_main_scss_content($theme)` returns `default.scss`, `plain.scss`, or a file uploaded to the file
area `theme_boost` / `preset`, chosen by `$theme->settings->preset` (`public/theme/boost/lib.php`, same in 5.2).

| Wanted | Do | Status |
|---|---|---|
| Follow the preset chosen on Boost's settings page | Pass `\core\output\theme_config::load('boost')`, as in the recipe | run on 5.3.0 |
| Always the default preset | `file_get_contents($CFG->dirroot . '/theme/boost/scss/preset/default.scss')` | read in the source |
| The child's own preset setting and uploads | Own `preset` and `presetfiles` settings and an own lookup in the child's file area; see the reference file | read in the source, modelled on the Classic theme in 5.2 |

Passing the child's `$theme` to Boost's function with no `preset` setting gives the default preset; with a
`preset` setting it can select only the two built-in names, because the uploaded-file lookup is fixed to the
`theme_boost` component. `plain.scss` is not "default without decoration": it imports no design tokens and, on
5.3, no fonts, so SCSS that uses `$mds-*` variables fails to compile under it (read in the 5.3.0 source).

## Files beside the code

- `pix/screenshot.png`: shown in the theme selector. Without it the selector shows Boost's screenshot, because
  theme images fall back to the parents (`theme_config::resolve_image_location()`).
- `pix/favicon.ico`: not inherited. The lookup returns the child's path without looking at the parents, so a
  child with no file and no site favicon set in the admin settings gets a missing favicon (read in the 5.3.0
  source, not run). Copy Boost's or ship your own.
- `pix/icon.svg`: shown on the plugins overview page; without it the row has a blank spacer
  (`public/admin/renderer.php`, `plugins_control_panel()`, 5.3.0). It is rendered as an `<img>`, so it cannot
  take the page's text colour. **5.3+:** a near-black stroke is almost invisible on Boost's dark surface; use a
  mid-tone that has contrast on white and on `#1d2125` (read in the source, not seen in a browser).

## Overrides a child usually adds next

- A renderer override is `theme_example\output\core_renderer extends \theme_boost\output\core_renderer`. Extend
  Boost's class, not core's, or Boost's navbar, edit button and (**5.3+:**) colour mode menu are lost
  (`moodle-theme-renderers-output`).
- A template override goes in `templates/<component>/<name>.mustache`; Boost's own templates are overridden at
  `templates/theme_boost/<name>.mustache` (`moodle-theme-layouts-templates`).
- Hook and `lib.php` callbacks run for every installed plugin, whether or not the theme is in use. Start each
  with a guard that stays true for descendants (run on 5.3.0; `moodle-theme-renderers-output`):
  `if ($PAGE->theme->name !== 'example' && !in_array('example', $PAGE->theme->parents)) { return; }`
- Boost's Behat step overrides are inherited by the child's suite (`moodle-theme-testing-release`).

## Keeping up with Boost

A child that only adds SCSS, settings and a few hooks can serve 5.2 and 5.3 from one branch. A child that copies
`drawers.mustache` or `navbar.mustache`, or styles navigation markup, has a different upstream on each version:
use one branch per Moodle version with `$plugin->supported = [503, 503]`, as the large Boost children do.

- Keep an untouched copy of every file taken from core or Boost beside the modified one
  (`drawers.mustache.upstream`) and name the Moodle version in its header. Porting is then a diff of the old
  upstream against the new one. Mark copied PHP with a fixed phrase ("Modifications compared to the original").
- Test for the feature, not the version: `class_exists(\theme_boost\colour_mode::class)` is true from 5.3.
  `$CFG->branch` still holds the old value while a core upgrade is running.
- 36 of the 52 `scss/moodle` partials Boost ships on 5.2 differ on 5.3.0, which also adds five (compared between
  5.2.2 and 5.3.0). A child selector that leans on Boost's markup or specificity needs a look in a browser on
  each version.

What changed in Boost for 5.3, what a 5.2-era child must re-check, and the removals announced for 6.0 and 7.0 are
in the version files below.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Leaving out `rendererfactory` | Core's `standard_renderer_factory` is used: the child's renderer classes are never loaded and Boost's `core_renderer` is skipped too, with no error | `$THEME->rendererfactory = 'theme_overridden_renderer_factory';` |
| Leaving out `haseditswitch`, `usescourseindex`, `requiredblocks`, `activityheaderconfig`, `yuicssmodules` | In turn (read in the code that reads each key, not each reproduced): old "Turn editing on" buttons return beside the switch; no course index drawer; Navigation and Administration blocks are forced onto every page; activity titles are printed twice; YUI reset CSS is loaded on every page | Restate all of them as in the recipe |
| Copying Boost's pre or extra SCSS code into the child's callbacks | Brand colour, raw SCSS and background rules are emitted twice | The child's callbacks add only the child's part |
| Expecting Boost's saved settings to apply | Brand colour, raw SCSS and backgrounds vanish when the site switches to the child | Declare the same setting names under `theme_example` ([reference/boost-settings.md](../moodle-skill-files/moodle-theme-boost-child/reference/boost-settings.md)) |
| An SCSS error anywhere in the stack | The page looks like plain Boost: core catches the error and serves the inherited precompiled Boost CSS, with a message only at developer debugging level (run on 5.3.0) | Turn on developer debugging, or look for "Error while compiling SCSS" in the PHP error log; `moodle-theme-scss` |
| Judging a CSS change on the first load after a purge | The old design is shown once: with `usefallback = true` the previous sheet is served from the temp directory while the new one compiles (`public/theme/styles.php`, 5.3.0) | Reload once; or set `usefallback = false` while developing (`moodle-theme-development` has the cache rules) |
| `$THEME->editor_scss = ['editor'];` with no `scss/editor.scss` in the child | Boost's editor styles are no longer used and the editor content is unstyled (read in the source) | Leave the key unset, or ship the file |
| `@import "bootstrap/functions";` or any path into Bootstrap | Works on 5.2, "file not found" on 5.3, and then plain Boost (run on 5.3.0) | Import only the wrapper names `bootstrap`, `fontawesome`, `moodle`, or reuse Boost's preset as the recipe does |
| Hard-coded light backgrounds or `prefers-color-scheme` | **5.3+:** when the admin enables colour modes in Boost's settings, every Boost descendant gets `data-bs-theme` on `<html>`; the child cannot opt out and shows light panels with light text | `--bs-*` custom properties, and `[data-bs-theme="dark"]` for exceptions |
| `$theme->settings->x` in code a grandchild may run | Under a grandchild the object holds the grandchild's settings, so the value is missing | `get_config('theme_example', 'x')` |
| A setting added without a version bump | Nothing stores its default, so the value is empty; SCSS that needs it meets an undefined variable | Bump `version`, and give every SCSS variable a `!default` in `pre.scss` |
| Only `['boost_union']` in a grandchild's `parents` | Core never follows a parent's parents; Boost's templates, renderers and SCSS are not found | List every ancestor, nearest first ([reference/grandchild.md](../moodle-skill-files/moodle-theme-boost-child/reference/grandchild.md)) |

## Reference files

| File | Read it when |
|---|---|
| [reference/inheritance.md](../moodle-skill-files/moodle-theme-boost-child/reference/inheritance.md) | A key, callback, image, font or template is not picked up from the parent as expected, the theme has two parents and you need to know which one wins, or you need each key's default and the symptom of omitting it |
| [reference/boost-settings.md](../moodle-skill-files/moodle-theme-boost-child/reference/boost-settings.md) | The child must offer Boost's settings (brand colour, raw SCSS, background images, unaddable blocks, presets), needs its own preset uploads, or a site is moving from Boost to the child and must keep its look |
| [reference/grandchild.md](../moodle-skill-files/moodle-theme-boost-child/reference/grandchild.md) | The theme's parent is itself a child of Boost (for example Boost Union), or your theme should be safe for others to build children on |
| [reference/patterns-to-avoid.md](../moodle-skill-files/moodle-theme-boost-child/reference/patterns-to-avoid.md) | The child is growing past SCSS and a few overrides: before adding a second way for settings to reach CSS, regions that depend on settings, page HTML built in PHP, or a companion plugin; or when reviewing a large theme |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](../moodle-skill-files/moodle-theme-boost-child/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](../moodle-skill-files/moodle-theme-boost-child/versions/moodle-5.3.md) |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme (the page still names some keys wrongly, for example
  `renderfactory` and `undeletableblocktypes`; the names core accepts are in the constructor of
  `public/lib/classes/output/theme_config.php`)
- https://moodledev.io/docs/5.3/guides/colourmodes
- `public/theme/boost/config.php`, `public/theme/boost/lib.php`, `public/theme/boost/UPGRADING.md` (5.2 and 5.3.0)
