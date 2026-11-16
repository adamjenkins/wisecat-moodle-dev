# A theme with no parents

Read this when the theme will have `$THEME->parents = []`, or when deciding whether it should.

Status: nothing in this file was field-tested. Every statement was read in the 5.3.0 source
(`public/lib/classes/output/theme_config.php`, `public/lib/classes/scss.php`, `public/theme/boost/`) and checked
against the 5.2 source where a line says so. Treat the recipe as a starting point to verify, not as a proven one.

## Decide first

A child of Boost can replace every layout file, every template and the whole main SCSS, and still keep Boost's
renderers, JavaScript, Behat support and upgrade path. The reasons to drop Boost as a parent are few: the theme
must not ship Bootstrap's CSS at all, or it must not change when Boost changes. Core is developed and tested
against Boost only since Classic left core in 5.3, so a stand-alone theme carries all of that work itself.

What is lost by not listing Boost as a parent:

| Lost | Consequence |
|---|---|
| Boost's layout files | Every page type must be given a layout file by the theme; see below |
| Boost's `core/` and `core_form/` template overrides and its own `theme_boost/` templates | Core's base templates are used. Boost's navbar, drawers and footer templates can still be included by name, as `theme_boost/navbar`, because they belong to an installed component |
| `theme_boost\output\core_renderer` and Boost's other renderers | The theme's renderers extend core's classes, and Boost-specific renderer methods that Boost's templates call are missing |
| Boost's pre and extra SCSS callbacks | `brandcolor`, the raw SCSS boxes and the background images need the theme's own code |
| `theme_boost_get_precompiled_css` | With no `precompiledcsscallback` of its own, a failed SCSS compile gives a page with plugin CSS only |
| Colour modes, **5.3+** | Boost applies `data-bs-theme` only when the active theme is Boost or has `boost` in `parents` |
| Core's Behat steps and features | Many assume Boost's markup; a stand-alone theme needs its own step overrides to run them |

## What still comes from Boost

- **The layout table.** `theme_config` starts every theme, parents or not, from Boost's `$THEME->layouts`. A
  stand-alone theme therefore begins with 19 page types pointing at `drawers.php`, `columns1.php`, `login.php`,
  `embedded.php`, `maintenance.php` and `secure.php`, files it does not have.
- **Region name strings**, which fall back to `theme_boost`.
- Boost stays installed. It can never be uninstalled, and it is the fallback when any theme fails to load.

## The layout rule

A layout file is searched for only in the theme and its listed parents. With no parents, any page type whose
entry still names a file the theme does not ship throws
`coding_exception: Can not find layout file for: <pagetype> (<file>)` the first time such a page is opened. A page
type missing from the table falls back to `standard`; an empty entry does not remove an inherited one.

Two ways to satisfy it:

1. Redefine every page type in `$THEME->layouts`: `base`, `standard`, `course`, `coursecategory`, `incourse`,
   `frontpage`, `admin`, `mycourses`, `mydashboard`, `mypublic`, `login`, `popup`, `frametop`, `embedded`,
   `maintenance`, `print`, `redirect`, `report`, `secure`.
2. Ship layout files with the six file names above. The inherited entries then resolve to the theme's files,
   with Boost's regions and options.

Either way, check the list against `public/theme/boost/config.php` of each supported version: a page type added
to Boost in a later version appears in the table of every theme.

Each entry needs `regions`, as an empty array when there are none, and `defaultregion` when there are regions.
Each layout file has to output `$OUTPUT->doctype()` and `$OUTPUT->main_content()`; core throws when the main
content marker is missing. The official theme page also says that every theme must include the elements with the
same ids that Boost's layouts have, because core JavaScript looks for them. `moodle-theme-layouts-templates` lists
them.

## config.php

```php
<?php
// (GPL header)

/**
 * Theme configuration for a theme with no parents.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

require_once(__DIR__ . '/lib.php');

$THEME->name = 'mytheme';
$THEME->parents = [];
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->scss = function ($theme) {
    return theme_mytheme_get_main_scss_content($theme);
};
$THEME->precompiledcsscallback = 'theme_mytheme_get_precompiled_css';
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
$THEME->iconsystem = \core\output\icon_system::FONTAWESOME;
$THEME->requiredblocks = '';
$THEME->addblockposition = BLOCK_ADDBLOCK_POSITION_FLATNAV;
$THEME->haseditswitch = true;
$THEME->usescourseindex = true;
$THEME->activityheaderconfig = ['notitle' => true];
$THEME->yuicssmodules = [];
// Plus $THEME->layouts, or layout files with Boost's six file names.
```

- `parents` must be present and an array. Leaving it out rejects the theme.
- `lib.php` has to define the two functions named here: `theme_mytheme_get_main_scss_content($theme)`, returning
  the SCSS text, and `theme_mytheme_get_precompiled_css($theme)`, shown below.
- Nothing is inherited, so `iconsystem` is restated here, unlike in a child. Font Awesome's fonts are found by
  core without Boost; the Font Awesome CSS is not, and has to be part of the theme's SCSS.
- `haseditswitch = true` and `usescourseindex = true` are promises that the theme's layouts render the edit
  switch and the course index. Set them only when the layouts do, otherwise editing mode cannot be turned on from
  the page, or the course index never appears.
- `version.php` has no `theme_boost` dependency unless the theme includes Boost's templates or imports Boost's
  SCSS, in which case it does depend on Boost and should say so.

## SCSS without a parent

- With a Closure in `$THEME->scss`, the only import path is the theme's own `scss/` directory.
- `core_scss` accepts an `@import` only when the file's real path is inside a theme directory, and on **5.3+**
  also inside `lib/bundles` at the Moodle root. Anything else is skipped with a developer debugging message and
  no compile error at that line, so the failure shows up later as an undefined variable or mixin.
- Bootstrap's SCSS is in a different place in each version: `public/theme/boost/scss/bootstrap/` on 5.2,
  `lib/bundles/bootstrap/scss/` on 5.3. Boost keeps a wrapper with the same name in both,
  `public/theme/boost/scss/bootstrap.scss`. A stand-alone theme that wants Bootstrap on both versions imports that
  wrapper by a relative path from its own `scss/` directory. Whether the relative path resolves the same way when
  the theme lives in `$CFG->themedir` was not checked.
- Ship a precompiled CSS file and return it from the `precompiledcsscallback` function, so that a compile failure
  degrades to the last good build and not to an unstyled site:

```php
function theme_mytheme_get_precompiled_css($theme) {
    return file_get_contents(__DIR__ . '/style/precompiled.css');
}
```

## Before relying on it

Verify on each supported version, at least: every page type in the layout table opens, including `login`,
`maintenance`, `secure`, `popup` and `embedded`; editing mode can be switched on; the course index and block
drawer open; a compile error falls back to the precompiled CSS; the theme's Behat suite initialises. Until that
has been done for the theme at hand, describe it as untested.
