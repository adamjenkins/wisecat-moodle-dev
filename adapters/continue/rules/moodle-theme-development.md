---
name: moodle-theme-development
description: Use when starting, structuring or debugging a Moodle theme at the engine level - a new theme/<name>/ directory, config.php and the $THEME keys, version.php and theme dependencies, $THEME->parents and what a child inherits, which theme a page uses (allowcoursethemes, allowthemechangeonurl and ?theme=, $CFG->themeorder), theme caches (themerev, theme designer mode, purge_caches.php, build_theme_css.php), "my change does not show" after a purge, "theme cannot be initialised", a theme problem whose area is not yet known, or choosing between a Boost child, a grandchild and a stand-alone theme. Also the routing table to the six sibling theme skills. Skip when the task is already inside one area: Boost child files (moodle-theme-boost-child), SCSS or a theme that renders as plain Boost (moodle-theme-scss), layouts and templates (moodle-theme-layouts-templates), renderers (moodle-theme-renderers-output), settings (moodle-theme-settings), testing and release (moodle-theme-testing-release).
---

# Moodle theme development: the engine, and where to go next

## Overview

A theme is a plugin of type `theme` that Moodle loads through `\core\output\theme_config`. This skill explains what
that class does with the theme's files, which is where most "nothing happened" problems come from, and routes each
kind of theme work to the sibling skill that owns it. Supported versions: Moodle 5.2 and 5.3.

How sure each statement is: "run on 5.3.0" means the behaviour was observed on a 5.3.0 site with a child of Boost;
everything else was read in the 5.3.0 source. Nothing here was run on 5.2: where 5.2 is mentioned it was read in the
5.2 source, and the engine files named below are identical in both versions unless a line is tagged.

## When to Use

- Creating a theme, or deciding what kind of theme to create
- Writing or reviewing `config.php`, `version.php` or the lang file of a theme
- A theme key, parent or override is ignored and no error is shown
- Working out which theme a page is using and why
- A change to SCSS, a template, an image or a setting does not show, or shows one page load late
- **Skip when:** the task is plainly inside one area. Use `moodle-theme-boost-child` for the child recipe,
  `moodle-theme-scss` for SCSS, `moodle-theme-layouts-templates` for page structure, `moodle-theme-renderers-output`
  for PHP output, `moodle-theme-settings` for admin settings, `moodle-theme-testing-release` for tests and shipping.
  For plugin basics that are not theme-specific (upgrade steps, capabilities, coding style) use
  `moodle-plugin-development`.

## Mental model

1. **Location.** `theme/<name>/` under `$CFG->dirroot`, which on disk is `public/theme/<name>/`, or
   `$CFG->themedir/<name>/` when that is set in the site's `config.php`. The component is `theme_<name>`.
2. **Load.** `theme_config::load($name)` reads `get_config('theme_' . $name)` into one settings object, then
   includes the theme's `config.php` with a fresh `$THEME` that already has `name`, `dir` and `settings`. It then
   includes each parent's `config.php` with that same settings object. `config.php` runs on every request; it is
   not cached.
3. **Whitelist.** Only the keys in a fixed list are copied from `$THEME`. Any other key is dropped without a
   message.
4. **Code loading.** `lib.php` (and a legacy `renderers.php`) of every listed parent is included, then the theme's
   own. Classes under `classes/` autoload as `\theme_<name>\...`.
5. **Inheritance is per asset.** Templates, renderers, layouts, SCSS, images and plain keys each follow their own
   rule. Some keys are not inherited at all. See the two tables below.
6. **Caching.** CSS is compiled once and served from a URL that carries two revision numbers. Templates, images
   and JavaScript have their own caches. "Purge" means different things for each.
7. **Failure is quiet.** A theme that cannot load is replaced by the site theme and then by Boost. An SCSS error is
   replaced by Boost's shipped CSS. Both leave the page working and looking like stock Boost.

Source for all seven: `public/lib/classes/output/theme_config.php` (5.3.0; one unrelated hunk differs in 5.2).

## Pick the approach

| Approach | `$THEME->parents` | Choose it when | Evidence |
|---|---|---|---|
| Child of Boost | `['boost']` | Almost always. Branding, SCSS, settings, a few template or renderer overrides | Run on 5.3.0 |
| Grandchild | `['boost_union', 'boost']` or any two-level chain | The site already depends on a feature-rich parent theme and needs local changes on top | Read in the source and in a published grandchild boilerplate, not run |
| Stand-alone | `[]` | Only when Boost's markup and SCSS cannot be the base | Not field-tested. Read [reference/stand-alone-theme.md](../moodle-skill-files/moodle-theme-development/reference/stand-alone-theme.md) first |

- Support 5.2 and 5.3 from one codebase only while the theme is thin: SCSS on Boost's preset, settings, hooks, no
  copied layout template and no navbar override. Once the theme copies `drawers.mustache` or `navbar.mustache`, or
  styles navigation markup, use one branch per Moodle version, because each copy has a different upstream in each
  version. The large public themes all work that way.
- A grandchild depends on its middle parent's release schedule: it cannot move to a new Moodle version before
  that parent does.

## Files of a theme

```
theme/mytheme/
├── version.php            required: component, version, requires, dependencies
├── config.php             required: without it the theme does not exist for theme_config
├── lang/en/theme_mytheme.php   required: pluginname, choosereadme, configtitle
├── lib.php                functions named in config.php, pluginfile, callbacks
├── settings.php           admin settings page (moodle-theme-settings)
├── classes/               autoloaded: output/ renderers, privacy/provider.php, hook callbacks
├── db/                    hooks.php, upgrade.php, as in any plugin
├── scss/                  SCSS (moodle-theme-scss)
├── layout/                layout PHP files (moodle-theme-layouts-templates)
├── templates/             own templates, and overrides in templates/<component>/
├── pix/                   screenshot.png, favicon.ico, icon.svg, own images
├── pix_core/, pix_plugins/<type>/<plugin>/     image overrides
├── fonts/, fonts_core/, fonts_plugins/         fonts and font overrides
├── style/                 plain CSS files named in $THEME->sheets
└── LICENSE                the Plugins directory expects a licence file in the root (moodle-plugin-release)
```

- **`pix/screenshot`** (`.png` or `.jpg`, about 500 by 400 px) is what the theme selector shows. Without it a
  child shows its parent's screenshot, because theme images fall back to the parents, and a theme with no parents
  shows a broken image (`public/admin/themeselector.php`, `theme_config::resolve_image_location()`, read in 5.3.0).
- **`pix/favicon.ico` is never inherited.** Core returns `<active theme>/pix/favicon.ico` without checking that it
  exists or looking at parents, so a child without the file requests a missing favicon unless the site has uploaded
  one in the admin settings. Fix: copy a `favicon.ico` into the child's `pix/`
  (`theme_config::resolve_image_location()`, `core_renderer::favicon()`, read in 5.3.0).
- **`pix/icon.svg`** is the row icon on the plugins overview page; with no file the row shows a blank spacer
  (`public/admin/renderer.php`, read in 5.3.0).
- **A `styles.php` file in the theme directory makes core reject the theme** as a legacy theme
  (`theme_config::find_theme_location()`).
- **Lang strings.** `pluginname` is the name everywhere; `choosereadme` is the description in the selector's
  preview dialog; `configtitle` is the documented title string for the settings. Region names (`region-side-pre`)
  are looked up in the theme, then its parents, then `theme_boost`, so a child that adds no region needs none. A
  theme cannot override other components' strings: the string manager has no theme hook.
- **Privacy provider.** A theme needs `classes/privacy/provider.php` like any plugin: a null provider with a
  `privacy:metadata` string, or a user-preference provider when it stores preferences. Details are in
  `moodle-theme-settings`.

## version.php

```php
<?php
// (GPL header)

/**
 * Version information.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$plugin->component = 'theme_mytheme';
$plugin->version   = 2026111600;
$plugin->release   = '1.0.0';
$plugin->requires  = 2026042000;        // Moodle 5.2.0.
$plugin->supported = [502, 503];
$plugin->maturity  = MATURITY_STABLE;
$plugin->dependencies = ['theme_boost' => 2026042000];
```

- List every parent in `dependencies`, with the lowest build of that parent the theme works with. Without it the
  theme installs on a site that lacks the parent and then fails to load on every page.
- `2026042000` is Boost's version in 5.2.0 and `2026100500` in 5.3.0 (`public/theme/boost/version.php`). A theme
  for 5.3 only uses `requires = 2026100500`, `supported = [503, 503]` and the 5.3 Boost build.
- `version.php` must not `require` anything: core reads it in contexts where Moodle is not set up.
- A new theme directory is installed like any plugin: `php admin/cli/upgrade.php --non-interactive` from the
  Moodle root, or the admin notifications page.

## config.php: the keys

The smallest `config.php` for a child of Boost. It restates the keys Boost sets that a child does not inherit.

```php
<?php
// (GPL header)

/**
 * Theme configuration.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

$THEME->name = 'mytheme';
$THEME->parents = ['boost'];
$THEME->sheets = [];
$THEME->editor_sheets = [];
$THEME->usefallback = true;
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
$THEME->requiredblocks = '';
$THEME->addblockposition = BLOCK_ADDBLOCK_POSITION_FLATNAV;
$THEME->haseditswitch = true;
$THEME->usescourseindex = true;
$THEME->activityheaderconfig = ['notitle' => true];
$THEME->yuicssmodules = [];
```

These twelve lines were run on 5.3.0 inside a child that also set its own `scss` Closure and callbacks. Left as
they are, with no `scss` key, the child inherits Boost's main SCSS, layouts, templates and SCSS callbacks (read,
not run in this exact form). Adding the theme's own SCSS, `lib.php` and settings is the subject of
`moodle-theme-boost-child`.

| Rule | Symptom when ignored | Fix |
|---|---|---|
| `$THEME->parents` must be an array, even when empty | The theme does not load; pages fall back with "cannot be initialised" | `$THEME->parents = [];` or the parent list |
| `$THEME->name` must equal the directory name | The theme is skipped by the theme selector and `?theme=` does not stick (read, not run) | Set it to the directory name; do not leave `'boost'` in a copied file |
| `rendererfactory` is not inherited | Every theme renderer is ignored, including Boost's own `core_renderer`, with no error | Restate `'theme_overridden_renderer_factory'` |
| `usefallback`, `requiredblocks`, `addblockposition`, `haseditswitch`, `usescourseindex`, `activityheaderconfig`, `yuicssmodules`, `removedprimarynavitems`, `csspostprocess`, `enablecourseajax`, `doctype`, `hidefromselector`, the arrow keys and `blockrtlmanipulations` are not inherited | The child silently gets core's defaults: no course index, "Turn editing on" buttons return beside the edit switch, the navigation and settings blocks become required, four YUI CSS modules load (read, not each reproduced) | Restate each one the parent sets, as above |
| Inherited from an ancestor that sets them: `scss`, `iconsystem`, `editor_scss`, `csstreepostprocessor`, `blockrendermethod`, the two exclude lists; `layouts` cascade per page type | Restating them is harmless, but restating `editor_scss` with a file the child does not ship drops the parent's editor styles | Leave them out unless changing them |
| Chained, every ancestor's runs: `prescsscallback`, `extrascsscallback`, `precompiledcsscallback`; concatenated: `sheets`, `editor_sheets`, `javascripts` | A child callback that repeats what the parent's emits puts that SCSS in the stylesheet twice | Emit only the child's additions |
| Keys outside the whitelist are dropped | No effect and no warning. Seen names: `enable_dock`, `editorsheets`, `undeletableblocktypes`, `renderfactory`, `allowedscss` | Use the real name: `editor_sheets`, `requiredblocks`, `rendererfactory` |

The official theme page uses several of the wrong names in the last row; the whitelist in
`theme_config::__construct()` is the authority. The complete key list with defaults, readers and Boost's values is
in [reference/theme-config-keys.md](../moodle-skill-files/moodle-theme-development/reference/theme-config-keys.md).

## Parents and lookup order

**List every ancestor, nearest first.** Core loops over the theme's own `parents` only and never follows a
parent's `parents`. With `['boost_union']` alone, Boost's `lib.php`, SCSS callbacks, `core/` template overrides and
layout files are all outside the chain, and a layout file that only Boost ships throws `Can not find layout file`.
Written base first, the middle parent's templates, renderers and layouts lose to Boost's. Fix:
`$THEME->parents = ['boost_union', 'boost'];` (read in 5.3.0; the official theme page says the same).

For `parents = ['mid', 'base']`:

| Asset | Order searched | Who wins |
|---|---|---|
| Mustache templates | theme, `mid`, `base`, then the component's own `templates/` | Nearest |
| Renderer classes | `theme_<name>`, `theme_mid`, `theme_base`, then the component | Nearest |
| Layout table | Boost's table always, then `base`, `mid`, theme on top, a whole entry at a time | Nearest |
| Layout file | theme, `mid`, `base`, or only the theme named in the entry's `theme` key | Nearest |
| `scss`, `iconsystem`, `csstreepostprocessor`, `blockrendermethod`, excludes | theme, `mid`, `base`; first that sets it | Nearest |
| Pre, extra and precompiled callbacks; `sheets`; theme JavaScript | all run or load: `base`, `mid`, theme | Theme's output is last |
| Images in `pix_core`, `pix_plugins`, `pix`; fonts; `editor_scss` | theme, then `base`, then `mid` | Theme, then the base parent |
| React component overrides, **5.3+** | the active theme's `js/esm/build/overrides/` only | Parents are never checked |

- **Images and fonts are the exception: the base parent beats the middle parent.** An icon overridden in the
  middle parent is ignored if Boost's `pix_core` has the same file. Fix: put the file in the theme itself.
- **All configs share the active theme's settings object.** Inside a parent's `config.php`, and in any parent
  callback that receives `$theme`, `$theme->settings->x` is `theme_<active theme>/x`. This is why a Boost child's
  `brandcolor` setting works with no code (run on 5.3.0), and why a function that must read its own theme's value
  uses `get_config('theme_<owner>', 'x')` instead.
- **Callbacks core calls by name run for the active theme only**: `theme_<name>_page_init()`,
  `theme_<name>_alter_css_urls()`. A child forwards to the parent's function if it needs it. Hooks in `db/hooks.php`
  are the opposite: they run for every installed theme, active or not, and need a guard
  (`moodle-theme-renderers-output`).

The three-level detail, the callback list and the settings-page ordering trap are in
[reference/parents-and-callbacks.md](../moodle-skill-files/moodle-theme-development/reference/parents-and-callbacks.md).

## Which theme a page gets

`moodle_page::resolve_theme()` takes the first match, in this order unless `$CFG->themeorder` in the site's
`config.php` changes it (`public/lib/pagelib.php`, identical in 5.2 and 5.3):

| Level | Source | Site switch, all off by default |
|---|---|---|
| course | `course.theme` | `allowcoursethemes` |
| category | nearest category upward with a `theme` | `allowcategorythemes` |
| session | `$SESSION->theme`, written by `?theme=<name>` | `allowthemechangeonurl`, checked when writing only |
| user | `user.theme` | `allowuserthemes` |
| cohort | the one theme all of the user's themed cohorts agree on | `allowcohortthemes` |
| site | `$CFG->theme`, else `boost` | none |

- **Try a theme without making it the site theme:** enable `allowthemechangeonurl`, open any page with
  `?theme=mytheme` (run on 5.3.0). The choice then sticks for the session and outranks user and cohort themes; it
  is cleared by logging out or by opening the theme selector page.
- **A theme that fails to load is replaced silently:** the site theme, then Boost, with a `debugging()` message at
  normal level only. If a page "ignores" the theme, turn on debugging and look for "cannot be initialised"; the
  usual causes are a missing parent, `parents` not an array, or a PHP error in `config.php`.
- **The theme is fixed on first use.** The first access to `$PAGE->theme` or `$OUTPUT` resolves it; after that
  `$PAGE->set_course()` throws "The theme has already been set up for this page ready for output". Set the course
  and context before any output call, and never call `require_login()` inside a fragment callback, where the
  theme is already set.
- **Set the site theme from the command line:** `php admin/cli/cfg.php --name=theme --set=mytheme` (read, not
  run). `$CFG->theme` forced in the site's `config.php` cannot be changed from the selector.

Cohort rules, `$PAGE->force_theme()`, the theme usage report, uninstall cleanup and the removed device themes are
in [reference/theme-selection.md](../moodle-skill-files/moodle-theme-development/reference/theme-selection.md).

## Caches: what picks up a change

| What changed | What is needed |
|---|---|
| SCSS, a CSS sheet, a key in `config.php` that affects CSS, any plugin's `styles.css` | A theme purge, or theme designer mode |
| A setting that feeds SCSS | Nothing, if the setting has `set_updatedcallback('theme_reset_all_caches')`; otherwise a theme purge |
| A `$THEME` key that does not affect CSS (layouts, renderer factory) | Nothing: `config.php` is read on every request |
| A `.mustache` file rendered by PHP, including a new override file | Nothing, in any mode: compiled templates are keyed by a hash of their source |
| A `.mustache` file rendered in the browser through `core/templates` | A full purge, or `$CFG->cachetemplates = false`. Theme designer mode does not affect it |
| An image or font, including a file added after it was requested once | A theme purge: a missing image is remembered until the revision changes |
| A new class file, lang string, `db/hooks.php` | A full purge; this is ordinary plugin behaviour |

```
php admin/cli/purge_caches.php                      # everything, including browser-side templates
php admin/cli/purge_caches.php --theme              # theme revision only: CSS, images, fonts, theme JS
php admin/cli/build_theme_css.php --themes=mytheme  # compile now, both directions; add --direction=ltr, --verbose
```

Run them from the Moodle root (`admin/cli/` is not under `public/`). A development site's `config.php`:

```php
$CFG->themedesignermode = true;   // CSS, images and theme JS uncached. Slow: never on a production site.
$CFG->cachetemplates = false;     // Browser-side templates uncached.
$CFG->cachejs = false;            // AMD modules uncached.
```

- **The first page load after a purge can show the old CSS.** Every successful build also writes an unversioned
  copy to `$CFG->tempdir/theme/<name>/`, which no purge deletes. With `$THEME->usefallback = true`, the first
  stylesheet request after a purge is answered with that old copy while the new one is built. A screenshot or a
  computed-style check taken on that first load shows the previous design. Fix: load the page twice before
  judging, or set `usefallback = false` while developing (`public/theme/styles.php`, read in 5.3.0; the effect was
  seen on a 5.x site).
- **A page that suddenly looks like plain Boost means the SCSS did not compile.** The stylesheet request hides
  debugging output, the compile error goes to the PHP error log at developer debugging level, and the CSS falls
  back to Boost's shipped `style/moodle.css` (run on 5.3.0). Look for "Error while compiling SCSS" in the log, or
  run `build_theme_css.php` with developer debugging on, which reaches the same compile code (read; the message
  was seen from a separate compile script). `moodle-theme-scss` covers reading the error.
- **Theme designer mode still caches each sheet for 10 seconds** (`THEME_DESIGNER_CACHE_LIFETIME`,
  `public/lib/csslib.php`), and it serves many separate CSS requests, so page loads are slow.
- **Plugin CSS is part of the theme stylesheet.** Every plugin's `styles.css` is concatenated first, then parent
  sheets, then the theme's compiled SCSS, then the theme's own sheets. So theme and Bootstrap rules win over a
  plugin rule of equal specificity, and a plugin CSS change also needs a theme purge.
- **Check arrival, then effect.** Fetch the `theme/styles.php/.../all` URL from the page source and search it for
  the new selector with a literal match; then read `getComputedStyle()` in the browser. The first proves the rule
  was built, only the second proves it applies.

The serving path, the two revision numbers, what each purge clears and the other `theme/*.php` scripts are in
[reference/caches-and-revisions.md](../moodle-skill-files/moodle-theme-development/reference/caches-and-revisions.md).

## Where each kind of work goes

| Task | Skill |
|---|---|
| Build the child: `lib.php`, what Boost gives for free, presets, pluginfile, grandchild of a large theme | `moodle-theme-boost-child` |
| Variables, pre and post SCSS, imports, dark mode, tokens, fonts, RTL, editor styles, compile errors | `moodle-theme-scss` |
| Layout files, regions, layout options, copying a Boost layout, template overrides, drawers, body classes | `moodle-theme-layouts-templates` |
| Renderer overrides, hooks from a theme, icon system and pix overrides, navigation, React overrides | `moodle-theme-renderers-output` |
| Settings page, setting types, setting to SCSS or template, stored files, user preferences | `moodle-theme-settings` |
| PHPUnit compile test, Behat suite, accessibility, lint, CI, Plugins directory rules, release | `moodle-theme-testing-release` |
| What changed for themes in 5.3 | `moodle-5-3-changes` |

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Omitting `rendererfactory` in a child | Renderer overrides silently unused | Restate it in the child's `config.php` |
| `$THEME->parents = ['boost_union']` for a grandchild | Boost's callbacks, templates and layout files drop out | List every ancestor, nearest first |
| Treating `precompiledcsscallback` as a cache | It is only used when the SCSS compile fails | Caching is automatic; precompile with `build_theme_css.php` |
| Inventing a key such as `$THEME->allowedscss` | Ignored without warning | Check the whitelist in the reference file |
| Copying Boost's pre or extra SCSS callback body into the child | `brandcolor` and the raw SCSS boxes are emitted twice | Emit only what the child adds |
| Judging CSS on the first load after a purge | Old design is shown once | Reload, or `usefallback = false` in development |
| Turning on designer mode to see a JavaScript-rendered template change | No change | `$CFG->cachetemplates = false` or a full purge |
| Testing with `?theme=` and forgetting it | The session keeps that theme and later checks mislead | Open the theme selector page or log out |
| Writing `theme` into `course` or `course_categories` with `$DB` | The theme usage cache is stale and the switch may be off | Use the course or category API and enable the `allow*themes` switch |
| `parents = ['classic', 'boost']` on a site without Classic | Falls back on every page with a debugging notice | **5.3+:** Classic is not in core; see the version notes |
| Checking a renderer or template override from a CLI script | The CLI renderer is used, so the override is not exercised | Check in a browser or a Behat scenario (run on 5.3.0) |

## Reference files

| File | Read it when |
|---|---|
| [reference/theme-config-keys.md](../moodle-skill-files/moodle-theme-development/reference/theme-config-keys.md) | setting or reviewing a `$THEME` key not shown in the minimal `config.php`, or a key seems to be ignored |
| [reference/parents-and-callbacks.md](../moodle-skill-files/moodle-theme-development/reference/parents-and-callbacks.md) | the theme has two levels of parents, or a `lib.php` function is expected to be called by core and is not |
| [reference/theme-selection.md](../moodle-skill-files/moodle-theme-development/reference/theme-selection.md) | a page shows the wrong theme, or the task involves course, category, user or cohort themes |
| [reference/caches-and-revisions.md](../moodle-skill-files/moodle-theme-development/reference/caches-and-revisions.md) | a change still does not show after the table above, or a deployment needs CSS built ahead of the first request |
| [reference/stand-alone-theme.md](../moodle-skill-files/moodle-theme-development/reference/stand-alone-theme.md) | the theme will have no parents |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](../moodle-skill-files/moodle-theme-development/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](../moodle-skill-files/moodle-theme-development/versions/moodle-5.3.md) |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme (theme plugin type; some key names on the page are wrong, see above)
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/layout
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/styles
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/images
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/fonts
- https://moodledev.io/docs/5.3/guides/templates
- https://moodledev.io/docs/5.3/apis/commonfiles/version.php
- Core source: `public/lib/classes/output/theme_config.php`, `public/lib/outputlib.php`, `public/lib/pagelib.php`,
  `public/theme/styles.php`, `public/theme/boost/config.php` (5.2 and 5.3)
