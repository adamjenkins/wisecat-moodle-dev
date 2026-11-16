# Every `$THEME` key the engine accepts

Read this when setting or reviewing a `$THEME` key that is not in the minimal `config.php` of `SKILL.md`, or when a
key seems to be ignored.

Source: the whitelist in `theme_config::__construct()` and the property declarations above it,
`public/lib/classes/output/theme_config.php`, read in 5.3.0. The whitelist and every resolver quoted here are the
same in the 5.2 source. Nothing in this file was run unless a line says so.

## How to read the tables

- **Default** is what `theme_config` uses when neither the theme nor, for inherited keys, any parent sets the key.
- **Inherited** describes what core does when the theme leaves the key unset. "No" means the theme gets the
  default even if its parent sets something else.
- **Boost** is the value in `public/theme/boost/config.php` (identical in 5.2 and 5.3). For a child of Boost, every
  row where Inherited is "No" and Boost has a value is a line the child has to restate to behave like Boost.
- For parents listed as `['mid', 'base']`, "nearest first" means theme, `mid`, `base`; "base first" means theme,
  `base`, `mid`.

## Structure and parents

| Key | Default | Meaning | Inherited | Boost |
|---|---|---|---|---|
| `name` | directory name | Preset by core before `config.php` runs. If `config.php` sets a different value, the theme selector skips the theme and `?theme=` does not stick | n/a | `'boost'` |
| `parents` | none: required | Array of every ancestor, nearest first. Not an array means the theme is rejected. Each listed parent must load | n/a | `[]` |
| `layouts` | `[]` | Page type to layout entry. Not in the whitelist: handled separately as a cascade | Yes: Boost's table, then each parent from base to nearest, then the theme, replacing a whole entry per page type. An empty entry is skipped, so it cannot remove an inherited one | 19 page types |
| `hidefromselector` | `false` | Hide the theme in the theme selector unless theme designer mode is on | No | unset |
| `rendererfactory` | `'standard_renderer_factory'` | Class that finds renderers. The standard factory ignores all theme renderers | No | `'theme_overridden_renderer_factory'` |
| `doctype` | `'html5'` | `html5`, `xhtml5` or `xhtml`; only `html5` is supported in practice | No | unset |

## CSS and SCSS

| Key | Default | Meaning | Inherited | Boost |
|---|---|---|---|---|
| `scss` | `false` | A file name in `scss/` without the extension, or a Closure `function ($theme)` returning SCSS text | Yes, nearest first. The `scss/` directories of the config that supplied it and of the configs after it become the import paths | a Closure calling `theme_boost_get_main_scss_content($theme)` |
| `prescsscallback` | `null` | Name of a function `($theme)` returning SCSS placed before the main SCSS | Chained: every ancestor's runs, base first, then the theme's. Each receives the active theme's object | `'theme_boost_get_pre_scss'` |
| `extrascsscallback` | `null` | Name of a function `($theme)` returning SCSS placed after the main SCSS | Chained, same order | `'theme_boost_get_extra_scss'` |
| `precompiledcsscallback` | `null` | Name of a function `($theme)` returning ready CSS. Used only when the SCSS compile fails. It is not a cache | Chained and concatenated, same order. A function that does not exist is skipped | `'theme_boost_get_precompiled_css'`, which returns `style/moodle.css` |
| `sheets` | `[]` | Names of `style/<name>.css` files, in order, added after the compiled SCSS | Parents' sheets are added before the compiled SCSS, base first, unless excluded | `[]` |
| `parents_exclude_sheets` | `null` | `true` to drop all parent sheets, or `['parentname' => true]`, or `['parentname' => ['sheet1', 'sheet2']]` | Yes, nearest first | unset |
| `plugins_exclude_sheets` | `null` | `true` to drop every plugin's `styles.css`, or `['mod' => true]`, or `['mod' => ['forum']]` | Yes, nearest first | unset |
| `editor_sheets` | `[]` | Names of `style/<name>.css` files for editor content | Parents' sheets are always included, base first | `[]` |
| `editor_scss` | unset | Names of `scss/<name>.scss` files compiled for editor content | Yes, base first, and the files are then read from that parent's directory. If the theme sets it, only the theme's own `scss/` is read: naming a file the theme does not ship silently drops the parent's editor styles | `['editor']` |
| `csspostprocess` | `null` | Name of a function `($css, $theme)` run on the CSS text after `[[pix:]]` and `[[font:]]` are replaced and before RTL flipping | No | unset |
| `csstreepostprocessor` | `null` | Callable `($tree, $theme)` on the parsed CSS tree. Setting it forces a full CSS parse on every build | Yes, nearest first | unset |
| `usefallback` | `false` | Serve the previous build from the temp directory while a new stylesheet compiles | No | `true` |
| `yuicssmodules` | `['cssreset', 'cssfonts', 'cssgrids', 'cssbase']` | YUI CSS modules added to every page | No | `[]` |

Notes:

- `[[setting:name]]` placeholders in CSS are not replaced by any core code. A theme that wants them has to do the
  replacement itself in its `csspostprocess` function. The usual route is an SCSS variable emitted from the
  `prescsscallback` instead.
- There is no magic callback name. The SCSS callbacks are whatever function names `config.php` assigns; core does
  not look for `theme_<name>_get_extra_scss()` by itself.
- A child theme's own `scss/` directory is an import path only when the child sets `$THEME->scss`. A child that
  inherits its parent's Closure cannot `@import` its own partials.

## JavaScript

| Key | Default | Meaning | Inherited | Boost |
|---|---|---|---|---|
| `javascripts` | `[]` | Names of `javascript/<name>.js` files loaded in the head through `theme/javascript.php` | Parents' files are loaded first, base first, unless excluded | unset |
| `javascripts_footer` | `[]` | The same, loaded in the footer | Same | unset |
| `parents_exclude_javascripts` | `null` | Same shape as `parents_exclude_sheets` | Yes, nearest first | unset |

Themes on 5.2 and 5.3 normally ship AMD modules in `amd/src` instead; these keys are the older mechanism and still
work.

## Blocks, navigation and page furniture

| Key | Default | Meaning | Inherited | Boost |
|---|---|---|---|---|
| `requiredblocks` | `false` | `false`: the navigation and settings blocks cannot be deleted. `''`: no required blocks. A comma-separated string or an array: those block names | No | `''` |
| `addblockposition` | unset, treated as `BLOCK_ADDBLOCK_POSITION_DEFAULT` | Where the "Add a block" control is: `BLOCK_ADDBLOCK_POSITION_DEFAULT` (0, a fake block in the default region), `BLOCK_ADDBLOCK_POSITION_FLATNAV` (1), `BLOCK_ADDBLOCK_POSITION_CUSTOM` (-1, the theme renders it) | No | `BLOCK_ADDBLOCK_POSITION_FLATNAV` |
| `blockrendermethod` | `null`, resolved to `'blocks'` | `'blocks'` or `'blocks_for_region'` | Yes, nearest first | unset |
| `blockrtlmanipulations` | `[]` | Map of region to region swapped in right-to-left languages, for example `['side-pre' => 'side-post']` | No | unset |
| `haseditswitch` | `false` | The theme renders its own edit-mode switch, so core stops adding "Turn editing on" buttons and menu items | No | `true` |
| `usescourseindex` | `false` | Enables the course index drawer | No | `true` |
| `activityheaderconfig` | `[]` | Theme-wide defaults for the activity header, for example `['notitle' => true]` | No | `['notitle' => true]` |
| `removedprimarynavitems` | `[]` | Items removed from the primary navigation: any of `home`, `myhome`, `courses`, `siteadminnode` | No | unset |
| `enablecourseajax` | `true` | `false` turns off AJAX course editing. Read once, by `course_ajax_enabled()` in `public/course/lib.php` | No | unset |
| `iconsystem` | unset, resolved to `\core\output\icon_system::STANDARD` | Class extending `\core\output\icon_system` | Yes, nearest first | `\core\output\icon_system::FONTAWESOME` |
| `rarrow`, `larrow`, `uarrow`, `darrow` | chosen from the browser and text direction | Arrow characters used in breadcrumbs and links | No | unset |

Blocks hidden from "Add a block" are not a `$THEME` key: core reads the setting `unaddableblocks` of the active
theme, `theme_<name>/unaddableblocks`, a comma-separated list (`public/lib/blocklib.php`).

## Names that look like keys and are not

Anything outside the whitelist is dropped without a warning. These appear in existing themes, in generated code or
in the official documentation:

| Written | Status | Use instead |
|---|---|---|
| `$THEME->enable_dock` | Set in Boost's own `config.php` but not in the whitelist; has no effect | Nothing: the dock no longer exists |
| `$THEME->editorsheets` | The official theme page uses this spelling in one place | `editor_sheets` |
| `$THEME->undeletableblocktypes` | Official theme page, with two different meanings | `requiredblocks` |
| `$THEME->renderfactory` | A heading on the official theme page | `rendererfactory` |
| `$THEME->allowedscss` | Does not exist anywhere in core | Nothing |
| `$THEME->settings`, `$THEME->dir` | Preset by core; assigning them in `config.php` is not carried into the theme object | Read them, do not set them. Changing a property of `$THEME->settings` does carry, because every config shares that one object |

The official page also recommends an empty string for `yuicssmodules`; Boost uses an empty array, and both stop
the modules loading.

## Layout entries

Layout files and options belong to `moodle-theme-layouts-templates`. The engine rules that affect whether the theme
loads at all:

- An entry is `['file' => 'drawers.php', 'regions' => ['side-pre'], 'defaultregion' => 'side-pre', 'options' => [...]]`.
  An optional `'theme' => 'boost'` restricts the file lookup to that one theme's `layout/` directory.
- Always give `regions`, as an empty array when there are none. `get_all_block_regions()` reads it without a
  guard, and a non-empty `regions` without `defaultregion` breaks block setup.
- A page type that is not in the table falls back to `standard` with a debugging message.
- A layout file that is in neither the theme nor a listed parent throws
  `coding_exception: Can not find layout file for: <pagetype> (<file>)`.
- A child entry replaces the parent's whole entry for that page type, including its `options`. Copy the parent's
  entry and change it; do not write a partial one.
