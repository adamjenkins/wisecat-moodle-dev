# Grandchild themes: a child of a child of Boost

Read this when the theme's parent is itself a child of Boost (for example Boost Union), or when your own child
theme should be safe for other people to build children on.

Status: read in `public/lib/classes/output/theme_config.php` (5.3.0, same code in 5.2) and in the public Boost
Union and Boost Union Child repositories. No grandchild was built or run for this file. The single-parent
recipe in `SKILL.md` was run on 5.3.0; treat everything below as a traced code path and prove it with one
compile and one page load.

## The rules that change with two levels

1. **List every ancestor, nearest first.** `$THEME->parents = ['boost_union', 'boost'];`. Core loops over the
   list as written and never follows a parent's own `parents`. With only `['boost_union']`, Boost's templates,
   renderers, layout files and `scss/` directory are not searched. The official page says the same: "If the theme
   you inherit from inherits from a parent as well, you need to indicate the grandparent here too."
   (https://moodledev.io/docs/5.3/apis/plugintypes/theme).
2. **Every config in the chain sees the grandchild's settings.** `$THEME->settings` inside the parent's
   `config.php`, and `$theme->settings` in every chained SCSS callback, is `theme_<grandchild>`. A parent that
   reads its settings that way finds nothing unless the grandchild copies them in.
3. **Chained callbacks all run**, farthest first: Boost's, the middle parent's, then the grandchild's, each with
   the grandchild's `theme_config`.
4. **Lookups go nearest first, except images and fonts.** Templates, renderers and layout files: grandchild,
   middle parent, Boost. Images under `pix/`, `pix_core/`, `pix_plugins/` and fonts: grandchild, then Boost, then
   the middle parent. An image the middle parent overrides loses to a Boost file of the same name when it is
   requested through a grandchild; put the file in the grandchild to be sure.
5. **Callbacks core calls by name are for the active theme only**: `theme_<name>_page_init()` and
   `theme_<name>_alter_css_urls()`. If the parent depends on one, the grandchild defines its own and forwards.
6. **React component overrides do not inherit** (**5.3+**): only the active theme's
   `js/esm/build/overrides/` is searched (`public/lib/classes/output/requirements/import_map.php`). A parent's
   override does nothing under a grandchild.
7. **Settings pages are included in theme-name order** (`public/admin/settings/appearance.php` loops the sorted
   plugin list). A grandchild that adds its page to an admin category created by its parent's `settings.php`
   must sort after the parent, or the category does not exist yet. What the admin tree does in that case was not
   traced.

## config.php

Including the parent's `config.php` copies every key it sets, so the non-inherited keys do not have to be
restated one by one and stay right when the parent changes them.

```php
<?php
// (GPL header)

/**
 * Theme configuration: a child of Boost Union.
 *
 * @package    theme_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */

defined('MOODLE_INTERNAL') || die();

// Not require_once: core may already have included the parent's file for another theme object, and this
// include must still fill this $THEME.
require($CFG->dirroot . '/theme/boost_union/config.php');

require_once(__DIR__ . '/lib.php');

$THEME->name = 'example';
$THEME->parents = ['boost_union', 'boost'];
$THEME->scss = function ($theme) {
    return theme_example_get_main_scss_content($theme);
};
$THEME->prescsscallback = 'theme_example_get_pre_scss';
$THEME->extrascsscallback = 'theme_example_get_extra_scss';
```

This is the pattern of the Boost Union Child boilerplate. If you do not include the parent's config, restate
at least `rendererfactory`, plus every other non-inherited key the parent sets.

A parent in `$CFG->themedir` is not at `$CFG->dirroot . '/theme/...'`. If that matters, find it with
`core_component::get_plugin_directory('theme', 'boost_union')`.

In `version.php` depend on the nearest parent, which carries its own dependency on Boost:
`$plugin->dependencies = ['theme_boost_union' => 2026100502];` (use the build you tested against), together with
`requires` and `supported` for the Moodle versions that build supports. Large Boost children support exactly one Moodle
version per release, so a grandchild follows the same branch model.

## lib.php

Call a parent's SCSS function with the parent's own config object, so the parent reads its own settings:

```php
/**
 * The main SCSS: the parent theme's whole stack, then this theme's post.scss.
 * @param \core\output\theme_config $theme
 * @return string SCSS
 */
function theme_example_get_main_scss_content($theme) {
    global $CFG;

    require_once($CFG->dirroot . '/theme/boost_union/lib.php');
    $parent = \core\output\theme_config::load('boost_union');
    $scss = theme_boost_union_get_main_scss_content($parent);
    $scss .= file_get_contents(__DIR__ . '/scss/post.scss');
    return $scss;
}
```

Passing `$theme` instead would make the parent look for its settings under the grandchild's component.

The resulting stack, for grandchild C, middle parent U and Boost B:

- Pre SCSS: B's callback with C's settings, U's callback, C's callback.
- Main: C's Closure, which returns U's main SCSS (U in turn asks B for the preset, with B's own config, so the
  preset is the one chosen on Boost's settings page) followed by C's `post.scss`.
- Extra SCSS: B's callback with C's settings, U's callback, C's callback.

## Before copying a parent's settings into the grandchild

A common boilerplate step copies some parent settings into the runtime settings object in `config.php`:

```php
$THEME->settings->unaddableblocks = get_config('theme_boost_union', 'unaddableblocks');
```

This is right for `unaddableblocks`, which core's block manager reads through the active theme. For the raw
SCSS settings (`scss`, `scsspre`) check what the parent already does: a parent that detects an active child and
replays Boost's callbacks with its own config already emits its raw SCSS, and copying the same values into the
grandchild's settings makes Boost's chained callback emit them a second time. To check, put a marker comment in
the parent's raw SCSS setting, compile the grandchild and count the marker in the CSS.

How a parent detects "a child of mine is active" also matters. A test on `$PAGE->theme` is right for page
rendering, but the stylesheet is built by `public/theme/styles.php`, which loads the requested theme by name.
For a grandchild used only as a course, category or user theme, what `$PAGE->theme` is at that point was not
traced. If a grandchild's stylesheet lacks the parent's settings in that setup, this is the place to look.

## Overriding the parent's templates and behaviour

- A parent theme's own template is overridden under the parent's component name:
  `templates/theme_boost_union/<name>.mustache`. Core templates stay at `templates/core/<name>.mustache`.
- `{{< core/name! }}` loads the component's original and skips every theme, the middle parent included. A
  grandchild that wraps `core/name!` therefore also bypasses its parent's override of that template.
- Copies drift. A copied template that was right for one Moodle version silently loses markup the next version
  added; keep the `.upstream` twin and re-diff at each parent release, not only at each Moodle release.
- To run the parent's Behat features against the grandchild, they have to be copied into the grandchild and
  retagged in CI: Behat only collects the features of the theme whose suite is running.
  `moodle-theme-testing-release` has the suite mechanics.

## Making your own theme a good parent

- Read your own settings with `get_config('theme_example', ...)`, never `$theme->settings`, in every callback.
  Under a descendant the object holds the descendant's settings. A check in CI that rejects `theme->settings->`
  in a diff keeps it that way.
- Decide "is this theme in use" by name or ancestry:
  `$PAGE->theme->name === 'example' || in_array('example', $PAGE->theme->parents)`.
- If a feature must reach descendants, ship it through something that inherits: a template, a renderer, SCSS.
  Not through a React component override or a name-called callback, which stop at the active theme.
- Offer an extension callback where descendants need a hook, collect it with
  `get_plugins_with_function('<name>', 'lib.php')`, and wrap each call in `try`/`catch` so one broken descendant
  does not break the settings page.
- Use `__DIR__`, not a hard-coded `'/theme/example/'`, for your own files.
