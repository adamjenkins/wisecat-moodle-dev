# What a child theme inherits, key by key and asset by asset

Read this when a key, callback, image, font or template is not picked up from the parent as expected, when the
theme has two parents and you need to know which one wins, or when you need a key's default and the symptom of
leaving it out.

Everything here is read in `public/lib/classes/output/theme_config.php` on Moodle 5.3.0 unless another file is
named. The 5.2 file differs in one place only (where core fonts are found), so the rules are the same on 5.2
(read, not run). Rows marked "run" were also seen working in a Boost child on 5.3.0. This file gives the rules
as they bear on a child of Boost; the engine itself, including themes with no parents, belongs to
`moodle-theme-development`.

## How core builds a child's configuration

1. `theme_config::load('example')` reads `get_config('theme_example')` once. That one object becomes
   `$THEME->settings` in the child's `config.php` and in the `config.php` of every parent.
2. The child's `config.php` is included. Only keys in the constructor's `$configurable` list are copied to the
   theme object; any other `$THEME->x` is ignored without a message. `enable_dock` is such a key: Boost still sets
   it, core does not read it.
3. For each name in `$THEME->parents`, in the order written, core includes that parent's `config.php`, `lib.php`
   and `renderers.php`. It reads the list as written and never follows a parent's own `parents`.
4. The child's `lib.php` and `renderers.php` are included last.
5. The layout table is built: Boost's layouts first (always, whatever the parents are), then each parent's from
   the farthest to the nearest, then the child's. An entry replaces the whole entry of the same name.

A parent that cannot be found is dropped from the object without an error at this point, but `load()` has
already refused a theme whose direct parent is missing: the theme then falls back to the site theme or to Boost
with a `debugging()` message "This page should be using theme ... which cannot be initialised".

## Every `$THEME` key

"Parents consulted" says what core does when the child leaves the key unset.

| Key | Core default | Parents consulted? | Boost's value | Symptom when a Boost child leaves it out |
|---|---|---|---|---|
| `parents` | none, required | - | `[]` | The theme cannot be loaded |
| `scss` | `false` | Yes, nearest first; first one set wins | Closure | None: Boost's Closure is used. The child's `scss/` directory is then not an import path: core collects import paths from the theme that supplies `scss` onward, so a child that wants to `@import` its own partials, or shadow a Boost partial, has to set `scss` itself (`get_scss_property()`) |
| `prescsscallback`, `extrascsscallback` | none | Chained: farthest parent first, child last; each gets the child's `theme_config` | Boost's two functions | None |
| `precompiledcsscallback` | none | Chained the same way, results concatenated | `theme_boost_get_precompiled_css` | None. It is used only when the SCSS compile fails, which is why a broken child looks like plain Boost (run) |
| `editor_scss` | unset | Yes; the farthest parent that sets it is asked first, and the files are read from that parent's directory | `['editor']` | None: Boost's `scss/editor.scss` is used |
| `sheets`, `editor_sheets` | `[]` | Parents' sheets are always added before the child's | `[]` | None |
| `parents_exclude_sheets`, `plugins_exclude_sheets`, `parents_exclude_javascripts` | `null` | Yes, nearest parent that sets it | unset | None |
| `javascripts`, `javascripts_footer` | `[]` | Parents' files are added first | unset | None |
| `iconsystem` | unset | Yes, nearest first; final default `icon_system::STANDARD` | `FONTAWESOME` | None |
| `csstreepostprocessor` | `null` | Yes, child first | unset | None |
| `blockrendermethod` | `null` | Yes; final default `'blocks'` | unset | None |
| `layouts` | `[]` | Cascaded, see step 5 | full table | None (run with one replaced entry) |
| `rendererfactory` | `standard_renderer_factory` | No | `theme_overridden_renderer_factory` | Renderer overrides in the child and in Boost are never used; no error. Boost's navbar trimming, context header and (5.3) colour mode menu go missing |
| `usefallback` | `false` | No | `true` | After a purge the first visitor waits for the full compile instead of getting the previous sheet |
| `requiredblocks` | `false`, meaning Navigation and Administration are required | No | `''` | Those two blocks are added to every page and cannot be deleted (`block_manager::get_required_by_theme_block_types()`, `public/lib/blocklib.php`) |
| `addblockposition` | unset, treated as `BLOCK_ADDBLOCK_POSITION_DEFAULT` | No | `BLOCK_ADDBLOCK_POSITION_FLATNAV` | In edit mode an "Add a block" fake block appears in the default region (`public/lib/blocklib.php`) |
| `haseditswitch` | `false` | No | `true` | Core prints "Turn editing on" buttons again on course, admin, dashboard and grade pages, beside Boost's switch (`core_renderer::edit_button()`, `public/lib/adminlib.php`) |
| `usescourseindex` | `false` | No | `true` | No course index drawer (`core_renderer`, `public/course/format/classes/output/local/content.php`) |
| `activityheaderconfig` | `[]` | No | `['notitle' => true]` | The activity header prints the activity title although Boost's page header already shows it (`public/lib/classes/output/activity_header.php`, `is_title_allowed()`) |
| `yuicssmodules` | `['cssreset', 'cssfonts', 'cssgrids', 'cssbase']` | No | `[]` | Four YUI stylesheets are requested on every page and compete with Bootstrap's reset |
| `removedprimarynavitems` | `[]` | No | unset | None. Values: `home`, `myhome`, `courses`, `siteadminnode` |
| `enablecourseajax` | `true` | No | unset | None |
| `csspostprocess` | `null` | No | unset | None |
| `doctype` | `'html5'` | No | unset | None |
| `hidefromselector` | `false` | No | unset | None |
| `blockrtlmanipulations` | `[]` | No | unset | None |
| `rarrow`, `larrow`, `uarrow`, `darrow` | computed | No | unset | None |

The symptoms in the lower half are read in the source, not each reproduced. The recipe in `SKILL.md` restates
every "No" row where Boost's value differs from the default, and that configuration was run on 5.3.0.

The moodledev.io theme page lists some of these under wrong names (`renderfactory`, `editorsheets`,
`undeletableblocktypes`). A misspelt key is dropped at step 2 with no warning, so copy names from the
`$configurable` list in the constructor.

## Which parent wins, by asset

For a theme with `parents = ['mid', 'boost']` (a grandchild). With one parent the two directions give the same
answer.

| Asset | Search order | Notes |
|---|---|---|
| Mustache template `component/name` | child `templates/component/`, `mid`, `boost`, then the component's own `templates/` | `public/lib/classes/output/mustache_template_finder.php`. A name ending in `!` skips every theme and loads the component's own file |
| Renderer class | prefixes `theme_child`, `theme_mid`, `theme_boost`, then the component | `renderer_prefixes()`; needs `theme_overridden_renderer_factory` |
| Layout file named by a layout entry | child `layout/`, `mid`, `boost`; only the named theme when the entry has a `'theme'` key | `layout_file()`. A missing file is a `coding_exception` |
| `scss` and the import path | first of child, `mid`, `boost` that sets `scss`; import paths are the `scss/` directories from that theme onward, in the same order | `get_scss_property()`. A file in a theme that is on the path shadows a later theme's file of the same relative name |
| Images: `pix_core/`, `pix_plugins/<type>/<plugin>/`, `pix/` | child, then `boost`, then `mid` | `resolve_image_location()`. The farthest parent beats the nearer one. To be sure of an override in a grandchild, put the file in the grandchild |
| `pix/favicon.ico` | child only | The path is returned without checking the parents or that the file exists |
| Fonts: `fonts_core/`, `fonts_plugins/`, `fonts/` | child, then `boost`, then `mid` | `resolve_font_location()` |
| `editor_scss` | child if it sets the key, else `boost`, then `mid` | `editor_scss_to_css()` |
| Strings `region-<name>` | child, `mid`, `boost`, then `theme_boost` | `get_region_name()` |
| Behat step overrides | the nearest parent that has any, then the theme's own on top | `public/lib/behat/classes/behat_config_util.php` |
| React component overrides | **5.3+:** the active theme's own `js/esm/build/overrides/` only; parents are never searched | `public/lib/classes/output/requirements/import_map.php` |

## Callbacks core calls by name

These are looked up for the active theme only, not for its parents:

- `theme_<name>_page_init($page)` (`theme_config::init_page()`)
- `theme_<name>_alter_css_urls(&$urls)` (`theme_config::css_urls()`)

A child whose parent relies on one of them defines its own function and forwards the call:

```php
/**
 * Lets the parent theme adjust the stylesheet URLs, as it does when it is the active theme.
 * @param moodle_url[] $urls
 */
function theme_example_alter_css_urls(&$urls) {
    theme_parentname_alter_css_urls($urls);
}
```

Callbacks found through `get_plugins_with_function()` or `db/hooks.php` are the opposite case: they run for every
installed theme, active or not, so each needs an active-theme guard (the rule is in `SKILL.md`).

## Whose settings a function reads

| Code | Reads the settings of |
|---|---|
| `$THEME->settings->x` inside any `config.php` in the chain | the active theme |
| `$theme->settings->x` in a pre or extra SCSS callback | the active theme, because core passes its own `theme_config` |
| `$theme->settings->x` in a function you call yourself | whichever theme's config you passed |
| `get_config('theme_example', 'x')` | always `theme_example` |
| `$PAGE->theme->settings->unaddableblocks` in core's block manager | the active theme |

Rule of thumb: code that should follow whichever theme is active reads `$theme->settings`; code that owns a
setting reads `get_config()` with its own component, so it keeps working under any descendant.
