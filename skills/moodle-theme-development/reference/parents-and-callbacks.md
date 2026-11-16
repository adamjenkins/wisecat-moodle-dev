# Parents, multi-level inheritance, and the functions core calls by name

Read this when the theme has two levels of parents (a grandchild), or when a `lib.php` function is expected to be
called by core and is not.

Source: `public/lib/classes/output/theme_config.php`, `public/lib/classes/output/mustache_template_finder.php` and
`public/lib/classes/output/renderer_factory/`, read in 5.3.0. The finder and the factories are byte-identical in
the 5.2 source, and `theme_config.php` differs in one unrelated hunk. None of this was run with a two-level chain:
the Boost child facts marked "run on 5.3.0" are single-level.

## How parents are loaded

1. `theme_config::load('mytheme')` includes `mytheme/config.php`. `$THEME->parents` must be an array.
2. Each **directly listed** parent must have a loadable `config.php` with an array `parents`. If one does not, the
   whole theme is rejected and the page falls back to the site theme, then Boost. The parents of parents are not
   checked and not followed.
3. In the order written in `$THEME->parents`, core includes each parent's `lib.php` and legacy `renderers.php`,
   and keeps the parent's raw `$THEME` object. Then it includes the theme's own `lib.php`.
4. Every `config.php` in the chain is included with the **same settings object**, the active theme's
   `get_config('theme_mytheme')`.

Consequences:

- **List every ancestor, nearest first:** `$THEME->parents = ['mid', 'base'];`. An ancestor left out contributes
  nothing: no `lib.php`, no callbacks, no templates, no layout files, no images.
- **A listed parent's `lib.php` is already loaded whenever a theme object exists**, so SCSS callbacks and
  renderers can call parent functions directly. A `require_once` of the parent's `lib.php` is still needed where
  no theme object has been built: in `settings.php`, in an upgrade step, or in a PHPUnit test that calls the
  theme's function directly. Symptom without it: "Call to undefined function theme_boost_...".
- **A parent's `config.php` runs once per theme object, with your settings.** A parent that computes something
  from `$THEME->settings` in its `config.php` computes it from the active theme's settings.

## Lookup order for `parents = ['mid', 'base']`

| Asset | Order | Notes |
|---|---|---|
| Mustache template `component/name` | `theme/mytheme/templates/component/`, `mid`, `base`, then the component's own `templates/` | A name ending in `!`, as in `core/name!`, skips every theme and goes straight to the component. A grandchild that wraps `core/name!` therefore also bypasses its parents' overrides of that template |
| A parent theme's own template `theme_mid/name` | `theme/mytheme/templates/theme_mid/name.mustache`, then the parents, then `mid/templates/` | This is how a child overrides Boost's `theme_boost/navbar`: `templates/theme_boost/navbar.mustache` |
| Renderer class | prefixes `theme_mytheme`, `theme_mid`, `theme_base`, then the component's renderer | Only with `rendererfactory = 'theme_overridden_renderer_factory'`, which is not inherited |
| Layout table | Boost's table, overlaid by `base`, then `mid`, then the theme | Boost's table is the starting point even when Boost is not a parent |
| Layout file | `mytheme/layout/`, `mid/layout/`, `base/layout/` | An entry with a `theme` key searches only that theme |
| `scss` | first of theme, `mid`, `base` that sets it | Import paths are the `scss/` directories from that config onward in the same order |
| `prescsscallback`, `extrascsscallback` | all run: `base`, `mid`, theme | Each is called with the active theme's `theme_config` |
| `precompiledcsscallback` | all run and are concatenated: `base`, `mid`, theme | Used only when the SCSS compile fails |
| `sheets`, `editor_sheets`, `javascripts` | all loaded: `base`, `mid`, theme | Subject to the exclude keys |
| `iconsystem`, `csstreepostprocessor`, `blockrendermethod`, exclude lists | first of theme, `mid`, `base` | |
| `editor_scss` | theme, else first of `base`, `mid` | The files are read from the directory of the config that supplied the key |
| Images: `pix_core/`, `pix_plugins/<type>/<plugin>/`, `pix/` | theme, then `base`, then `mid`, then the site's `dataroot/pix` or `dataroot/pix_plugins`, then the component | Core's own comment: "Base first, the immediate parent last" |
| Fonts: `fonts_core/`, `fonts_plugins/<type>/<plugin>/`, `fonts/` | theme, then `base`, then `mid` | |
| Region name string `region-<name>` | `theme_mytheme`, `theme_mid`, `theme_base`, then `theme_boost` | |
| Behat step-definition overrides | the nearest parent that has any, then the theme's own on top | `public/lib/behat/classes/behat_config_util.php`; details in `moodle-theme-testing-release` |
| React component overrides, **5.3+** | `mytheme/js/esm/build/overrides/` only, then the original | A parent's override is not used by its children. Details in `moodle-theme-renderers-output` |

Two rows surprise people:

- **Images and fonts: the base parent beats the middle parent.** With `['boost_union', 'boost']`, a file in
  Boost's `pix_core/` wins over the same file in the middle parent. Only the theme's own copy is certain to win.
- **`favicon` has no lookup at all.** It is always `<active theme>/pix/favicon.ico`, whether or not the file
  exists.

## `$theme->settings` or `get_config()`

Any function that receives `$theme` during a CSS build receives the active theme's object, whichever theme the
function belongs to.

| Code | Reads |
|---|---|
| `$theme->settings->brandcolor` inside `theme_boost_get_pre_scss($theme)` | `theme_<active theme>/brandcolor` |
| `get_config('theme_mid', 'brandcolor')` | always `mid`'s own value, whichever descendant is active |
| `theme_config::load('mid')->settings->brandcolor` | `mid`'s own value, through a second theme object |

- A function that should follow whichever theme is active reads `$theme->settings`. Boost does this, which is why
  a Boost child gets `brandcolor`, `scsspre`, `scss`, `backgroundimage` and `loginbackgroundimage` working by naming
  its settings the same (run on 5.3.0 for `brandcolor`).
- A function that owns a setting and must behave the same under any descendant reads
  `get_config('theme_<owner>', 'x')`.
- To make a parent function use the parent's own configuration, pass it the parent's object:

```php
// In the child's main SCSS function: take the preset the site chose in Boost's own settings.
$boost = \core\output\theme_config::load('boost');
$scss = theme_boost_get_main_scss_content($boost);
```

  Run on 5.3.0. Passing the child's `$theme` instead makes Boost look for a `preset` setting on the child and for
  an uploaded preset in Boost's file area, and silently fall back to `default.scss` when they do not match.

- **Doubling.** Because every ancestor's pre and extra callback already runs, a child callback that calls
  `theme_boost_get_extra_scss($theme)` or appends `$theme->settings->scss` itself puts that SCSS in the stylesheet
  twice. With a middle parent that replays its own parent's callbacks, check for a third copy.

## Functions core calls by name

| Function in `lib.php` | Called | For which themes |
|---|---|---|
| `theme_<name>_page_init(moodle_page $page)` | At the start of page output, from `theme_config::init_page()` | The active theme only, not its parents |
| `theme_<name>_alter_css_urls(&$urls)` | After the stylesheet URLs are built | The active theme only |
| `theme_<name>_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options = [])` | When a file in the theme's file areas is requested | The theme named in the URL, active or not |
| `theme_<name>_user_preferences()` | When user preferences are validated | Every installed plugin that defines it, active or not |
| `theme_<name>_get_fontawesome_icon_map()` | When the Font Awesome icon map is built and cached | Every installed plugin that defines it |
| The functions named in `prescsscallback`, `extrascsscallback`, `precompiledcsscallback`, `csspostprocess`, `csstreepostprocessor`, and the `scss` Closure | During a CSS build | The theme being built and, for the chained ones, its listed parents |
| Hook callbacks registered in `db/hooks.php` | On every page | Every installed theme, active or not |

- **Active-theme-only callbacks do not chain.** A grandchild that needs its parent's `alter_css_urls` or
  `page_init` behaviour defines its own function and forwards:

```php
function theme_mytheme_alter_css_urls(&$urls) {
    theme_mid_alter_css_urls($urls);
}
```

- **Callbacks that run for every installed theme need a guard.** A hook callback, and anything a theme registers
  through the plugin-wide function lookup, runs while another theme is active. The guard Boost itself uses:

```php
$theme = $PAGE->theme;
if ($theme->name !== 'mytheme' && !in_array('mytheme', $theme->parents, true)) {
    return;
}
```

  Read in `public/theme/boost/classes/colour_mode.php` (5.3.0); the same test with a hook was run on 5.3.0.
  `moodle-theme-renderers-output` owns hooks from a theme.

## Settings pages with a parent theme

- Core creates one settings page per theme that has a `settings.php`, named `themesetting<name>`, and includes the
  files in alphabetical order of theme name (`public/admin/settings/appearance.php`, `core_component`'s sorted
  plugin list).
- A child that adds its page to an admin category created by its parent's `settings.php` depends on that order.
  When the child's name sorts before the parent's, the category does not exist yet: `$ADMIN->add()` emits the
  debugging message "parent does not exist!", returns false, and the page is missing from the admin tree (read in
  `admin_category::add()`, `public/lib/adminlib.php` on 5.2 and `public/admin/classes/setting/tree/category.php`
  on 5.3; not run). Fix: name the child so that it sorts after the parent, or add the page to the standard
  `themes` category.
- A child does not inherit the parent's settings values. `theme_child/brandcolor` and `theme_parent/brandcolor`
  are separate; what is shared is the code that reads them.

## Depending on a parent that is not Boost

- Put every ancestor in `$plugin->dependencies` with a minimum version.
- A middle parent that pins `$plugin->supported` to one Moodle branch forces the same on the grandchild.
- A grandchild `config.php` can include the middle parent's `config.php` to copy all its non-inherited keys, then
  overwrite `name`, `parents` and the SCSS keys. Use `require`, not `require_once`: the parent's file may already
  have been included once for another theme object in the same request, and `require_once` would then set nothing.

```php
require($CFG->dirroot . '/theme/boost_union/config.php');
$THEME->name = 'mytheme';
$THEME->parents = ['boost_union', 'boost'];
```

  Read in a published grandchild boilerplate, not run. The full grandchild recipe is in `moodle-theme-boost-child`.
