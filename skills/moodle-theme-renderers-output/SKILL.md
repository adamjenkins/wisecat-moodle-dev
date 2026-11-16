---
name: moodle-theme-renderers-output
description: Use when a Moodle theme changes output in PHP — $THEME->rendererfactory, theme_overridden_renderer_factory, classes/output/core_renderer.php, plugin renderer overrides, a theme's db/hooks.php callbacks, $THEME->iconsystem, get_fontawesome_icon_map, pix_core and pix_plugins, $THEME->activityheaderconfig, $THEME->removedprimarynavitems, primary navigation data, or a React component override in js/esm/src/overrides (5.3). Skip when the change is a Mustache or layout file (moodle-theme-layouts-templates), SCSS (moodle-theme-scss) or a settings page (moodle-theme-settings).
---

# Moodle theme renderers and output

## Overview

A theme changes what PHP prints through renderer classes found by name, hook callbacks, the icon system, image
files that shadow core's, and a few `config.php` keys; Moodle 5.3 adds React component overrides. Each has its own
lookup order and fails without an error when it is wrong, so the first job is picking the right one.

## When to Use

- Overriding a `core_renderer` method, or a plugin's or course format's renderer, from a theme
- Adding a method that a layout template calls as `{{{ output.something }}}`
- Adding markup to `<head>`, the top of `<body>` or the footer from a theme, or attributes to `<html>`
- Changing an icon: the glyph, the image file, an activity icon's colour
- Removing or adding primary navigation items, changing the activity header or the breadcrumb
- Deciding whether a 5.3 React-rendered region needs a component override
- **Skip when:** the change is a template or layout file (`moodle-theme-layouts-templates`), a style rule
  (`moodle-theme-scss`), a setting and its plumbing (`moodle-theme-settings`), the theme's skeleton and caches
  (`moodle-theme-development`), or a hook in a non-theme plugin (`moodle-hooks-api`).

## Pick the cheapest mechanism

Try them in this order. Each step down costs more at every Moodle upgrade.

| Goal | Mechanism | Owner |
|---|---|---|
| Colour, spacing, shape, hiding an element | SCSS, custom properties | `moodle-theme-scss` |
| Different markup for one template | Template override | `moodle-theme-layouts-templates` |
| Extra markup in head, top of body, footer; `<html>` attributes | Hook callback with an active-theme guard | this skill |
| A body class, or data a layout template needs | Method on the theme's `core_renderer` | this skill |
| Different data in a plugin's template | Plugin renderer override: export, change, render the same template | this skill |
| A different glyph or image for an icon | Icon map or `pix_core` / `pix_plugins` | this skill |
| Fewer primary navigation items, no activity title | `config.php` key | this skill |
| A React region's behaviour (**5.3+**) | Template, then PHP exporter, then wrap, then own component | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

A renderer override that copies a core method body is the most expensive row: the copy stops receiving core
fixes at once. Call `parent::` and change the result wherever possible.

## Renderer overrides: the recipe

Three parts must agree. Run on 5.3.0 in a child of Boost (a body class added through `body_attributes()`, seen in a
browser and in a Behat scenario); the factory code is identical in 5.2 (read in the 5.2 source, not run).

`config.php`:

```php
// Not inherited from the parent theme. Without it no theme renderer is used, Boost's included.
$THEME->rendererfactory = 'theme_overridden_renderer_factory';
```

`classes/output/core_renderer.php`:

```php
<?php
// (GPL header)

namespace theme_mytheme\output;

/**
 * Overrides of the core renderer.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class core_renderer extends \theme_boost\output\core_renderer {
    /**
     * Adds a class that says which corner style is in use.
     *
     * @param array|string $additionalclasses
     * @return string
     */
    public function body_attributes($additionalclasses = []) {
        if (!is_array($additionalclasses)) {
            $additionalclasses = explode(' ', $additionalclasses);
        }
        $style = get_config('theme_mytheme', 'cornerstyle') === 'square' ? 'square' : 'round';
        $additionalclasses[] = 'mytheme-corners-' . $style;
        return parent::body_attributes($additionalclasses);
    }
}
```

Purge caches once so the class autoloader sees the new file. No theme revision is involved.

### Rules

1. **`rendererfactory` is not inherited.** The default is `standard_renderer_factory`, which never looks at theme
   classes. Symptom: the theme's `core_renderer` is silently unused, and so is Boost's, which changes the
   breadcrumb, the context header and the edit button and (**5.3+**) empties `{{# output.colour_mode_menu }}`. No
   error is raised. Fix: the line above. Source: `public/lib/classes/output/theme_config.php` (`$rendererfactory`
   default and `get_renderer()`), `public/lib/classes/output/renderer_factory/standard_renderer_factory.php`, 5.3.0
   and 5.2.
2. **Extend Boost's class, not core's.** `\theme_boost\output\core_renderer` carries Boost's overrides
   (`edit_button`, `navbar`, `context_header`, `firstview_fakeblocks`, and on 5.3 `search_box` and
   `colour_mode_menu`). A child that extends `\core_renderer` drops them all, because the first class found wins
   and there is no chaining between themes other than PHP inheritance. In a grandchild theme, extend the nearest
   parent's class. Source: `public/theme/boost/classes/output/core_renderer.php`, 5.3.0 and 5.2.
3. **The class name is the lookup key.** For `$PAGE->get_renderer('core')` the factory tries
   `\theme_mytheme\output\core_renderer`, then the same name in each parent theme, nearest first, then core's.
   A typo in namespace, file name or class name gives no error, only core's output. The full name table for plugin
   and subsystem renderers is in [reference/renderer-lookup.md](reference/renderer-lookup.md).
4. **Core's special-target renderers beat the theme's general one.** On the `maintenance` page layout, in CLI
   scripts and in `AJAX_SCRIPT` scripts other than `public/lib/ajax/service.php`, the factory first looks for
   `core_renderer_maintenance`, `core_renderer_cli` or `core_renderer_ajax`, and core ships all three. Symptom: a
   method added to the theme's `core_renderer` does not exist during upgrade, on the maintenance screen or from a
   CLI script ("Call to undefined method" or, from Mustache, an empty string). Fix: keep those layouts free of
   theme renderer methods, or also ship `theme_mytheme\output\core_renderer_maintenance` extending
   `\core\output\core_renderer_maintenance`. Source: `renderer_factory_base.php` (`get_target_suffix()`),
   `theme_overridden_renderer_factory.php`, `public/lib/pagelib.php` (`get_renderer()`), 5.3.0 and 5.2.
5. **Keep the parent's signature.** PHP raises a fatal error on an incompatible override, and a narrower one
   breaks callers: `body_attributes()` is called with a string by some layouts and an array by others. Copy the
   signature from the class being extended on the lowest supported version; the public method signatures of
   `core_renderer` are the same in 5.2 and 5.3 except for one method added in 5.3 (compared with `diff`).
6. **A renderer extending a class that no longer exists is a fatal error** when that renderer is requested.
   **5.3+:** `block_timeline\output\renderer` was removed with no stub, so a theme override of it must be deleted.
   Source: `public/blocks/timeline/UPGRADING.md`, 5.3.0.
7. **Do not use `empty()` or `isset()` on `$this->page->cm`, `->course`, `->url` and the other magic properties.**
   `moodle_page` has `__get()` and no `__isset()`, so they always read as not set. Read the property into a
   variable first. Source: `public/lib/pagelib.php`, 5.3.0 and 5.2.
8. **Everything a renderer returns is raw HTML.** Escape user data with `s()` or `format_string()`, and render
   anything longer than a tag or two from a template.

### A method for a layout template

Layout templates receive the renderer as `output`, and Mustache calls any public method that takes no required
argument. Add the method to the theme's `core_renderer` and call it with triple braces:

```php
    /** @return string The banner HTML, or an empty string when no banner is set. */
    public function mytheme_banner(): string {
        $text = get_config('theme_mytheme', 'bannertext');
        if (empty($text)) {
            return '';
        }
        return $this->render_from_template('theme_mytheme/banner', ['text' => format_string($text)]);
    }
```

```mustache
{{{ output.mytheme_banner }}}
```

A method name that does not exist renders as nothing, with no error (read in the source, not run as a negative
test). This is how one template can serve two versions: `{{# output.colour_mode_menu }}{{{ . }}}{{/ output.colour_mode_menu }}`
prints the switcher on 5.3 and nothing on 5.2. Prefix the theme's own methods with the theme name so a later core
method of the same name cannot collide.

### Plugin and course format renderers

Find the class the plugin itself uses, extend it, and name the theme class after the component:
`theme_mytheme\output\mod_quiz_renderer`, `theme_mytheme\output\format_topics_renderer`, and for a subtype
`theme_mytheme\output\core\course_renderer` (requested as `get_renderer('core', 'course')`).

Prefer changing the data over copying the template. Read in a published Boost child theme, not run here:

```php
namespace theme_mytheme\output;

use core_courseformat\output\local\content;

class format_topics_renderer extends \format_topics\output\renderer {
    public function render_content(content $widget): string {
        $data = $widget->export_for_template($this);
        $data->mythemecards = (bool) get_config('theme_mytheme', 'sectioncards');
        return $this->render_from_template($widget->get_template_name($this), $data);
    }
}
```

`$renderer->render($widget)` looks for `render_<class name>` on the renderer first, so a method with that name in
a theme renderer takes over that widget; without one, the widget's own template is used. Exported data is often
a `stdClass`, not an array (`action_link` exports `$x->attributes`): read the widget's `export_for_template()`
before changing its result. Source: `public/lib/classes/output/renderer_base.php` (`render()`),
`plugin_renderer_base.php`, 5.3.0 and 5.2.

## Hooks from a theme

A theme registers hook callbacks in `db/hooks.php` like any plugin; `moodle-hooks-api` covers the API. What is
specific to themes is that **callbacks of every installed theme run on every page, whichever theme is in use**,
so each one starts with a guard. Run on 5.3.0 (the meta tag appears only under the theme); the hook classes used
here exist in 5.2 (read in the 5.2 source, not run).

`db/hooks.php`:

```php
<?php
// (GPL header)
defined('MOODLE_INTERNAL') || die();

$callbacks = [
    [
        'hook' => \core\hook\output\before_standard_head_html_generation::class,
        'callback' => [\theme_mytheme\local\hook_callbacks::class, 'before_standard_head_html_generation'],
    ],
];
```

`classes/local/hook_callbacks.php`:

```php
<?php
// (GPL header)
namespace theme_mytheme\local;

use core\hook\output\before_standard_head_html_generation;

// (class docblock with @package, @copyright and @license, as in the renderer sample)
class hook_callbacks {
    /**
     * Adds a theme-color meta tag with the accent colour.
     *
     * @param before_standard_head_html_generation $hook
     */
    public static function before_standard_head_html_generation(before_standard_head_html_generation $hook): void {
        global $PAGE;

        if (during_initial_install()) {
            return;
        }
        if ($PAGE->theme->name !== 'mytheme' && !in_array('mytheme', $PAGE->theme->parents, true)) {
            return;
        }
        $accent = get_config('theme_mytheme', 'accentcolour');
        if (!empty($accent) && preg_match('/^#[0-9a-fA-F]{3,8}$/', $accent)) {
            $hook->add_html('<meta name="theme-color" content="' . s($accent) . '">');
        }
    }
}
```

- The guard accepts child themes on purpose (`in_array(..., $PAGE->theme->parents)`), which is what Boost's own
  callbacks do (`public/theme/boost/classes/colour_mode.php`, `is_boost_theme()`, 5.3.0). Drop that half only when
  a child should not get the behaviour.
- `$PAGE->theme` initialises the theme when read. In the output hooks that is already done. In an early hook such
  as `\core\hook\after_config` it forces the theme to be chosen before the page knows its course or context, and
  the theme's `lib.php` constants are not loaded yet: compare a stored config value there instead.
- `add_html()` takes raw HTML: validate or escape every setting value, as above.
- The same "runs for inactive themes" rule covers plugin-wide `lib.php` callbacks such as
  `theme_mytheme_get_fontawesome_icon_map()`. It does not cover `theme_mytheme_page_init()` or renderer classes,
  which are used only for the current theme and its children.
- A callback for a hook class that the running version does not have is ignored, so a 5.2 to 5.3 theme can register
  5.3-only hooks unconditionally (read in `public/lib/classes/hook/manager.php`, 5.3.0 and 5.2; not run).

The catalogue of output and navigation hooks, with the method each offers and where core dispatches it, is in
[reference/hooks-and-callbacks.md](reference/hooks-and-callbacks.md).

## Icons and images

`$THEME->iconsystem` is inherited from the parent (unlike `rendererfactory`); Boost sets Font Awesome. With it, an
icon that has an entry in the icon map is drawn as an `<i>` glyph and the image file is never requested; an icon
with no entry is drawn as an `<img>`. That split decides which mechanism works:

| Goal | Mechanism | Trap |
|---|---|---|
| Replace an image file | `pix_core/<path>.svg` for core, `pix_plugins/<type>/<plugin>/<path>.svg` for a plugin | No visible effect for an icon that is in the map |
| Map the theme's own icon to a glyph | `theme_mytheme_get_fontawesome_icon_map()` in `lib.php` | Cannot change an existing key; runs for inactive themes; each key needs a real SVG |
| Change the glyph of a core or plugin icon | Subclass `\core\output\icon_system_fontawesome`, set `$THEME->iconsystem` | Map is cached on the server and in the browser |
| Recolour activity icons | `$activity-icon-<purpose>-bg` variables in pre-SCSS | `color` and `fill` do nothing: the colour is an SVG filter |

Changing a core glyph (read in the source: the Classic theme shipped with 5.2 does exactly this; not run here):

```php
// classes/output/icon_system_fontawesome.php
namespace theme_mytheme\output;

class icon_system_fontawesome extends \core\output\icon_system_fontawesome {
    #[\Override]
    public function get_core_icon_map() {
        $map = parent::get_core_icon_map();
        $map['core:i/navigationitem'] = 'fa-square';
        return $map;
    }
}
```

```php
// config.php
$THEME->iconsystem = '\\theme_mytheme\\output\\icon_system_fontawesome';
```

- After any map change, purge caches. The server caches the map per icon-system class, and the browser keeps its
  own copy in localStorage per theme; a stale browser copy shows as "icons printed by PHP changed, icons drawn by
  JavaScript did not". Source: `public/lib/classes/output/icon_system_fontawesome.php` (`get_icon_name_map()`),
  `public/lib/amd/src/icon_system_fontawesome.js`, 5.3.0.
- Images and fonts resolve in an unusual order: the theme itself, then its parents **farthest first**. With
  `parents = ['middle', 'boost']`, a file in Boost's `pix_core` beats the same file in `middle`. Only the theme's
  own copy is certain to win. Source: `theme_config.php` (`resolve_image_location()`), 5.3.0 and 5.2.
- A request for an image that does not exist is remembered until the next theme cache purge. Adding the file
  afterwards changes nothing until the purge. Source: `public/theme/image.php`, 5.3.0.
- **5.3+:** in dark mode Boost inverts only `<img>` icons whose URL contains `/t/`, `/e/`, `/a/` or one of three
  group icons. Any other image icon, including one a theme adds with a dark stroke, stays dark on a dark page.
  Map it to a glyph, or add a rule under `[data-bs-theme="dark"]`. Source:
  `public/theme/boost/scss/moodle/icons.scss`, 5.3.0.
- `{{#pix}}` and `pix_icon()` are for icon-sized images: they always add the `icon` class and Boost's icon
  sizing. For an illustration use `$OUTPUT->image_url('name', 'theme')` and a plain `<img>`.

The map-building steps, the resolution order for every component, activity icon purposes, deprecated icons and
the favicon rule are in [reference/icons-and-pix.md](reference/icons-and-pix.md).

## Navigation and the activity header

These are set in `config.php` and read by core classes, so no renderer is needed. None is inherited from the
parent theme: restate them in a child. All read in the source on 5.3.0 and 5.2.

```php
// Hide items of the primary navigation. Keys: home, myhome, courses, siteadminnode.
$THEME->removedprimarynavitems = ['courses'];
// Do not print the activity name as a heading inside the activity header (Boost's value).
$THEME->activityheaderconfig = ['notitle' => true];
```

- `removedprimarynavitems` uses `courses` for the node whose own key is `mycourses`. An unknown key is ignored.
  Source: `public/lib/classes/navigation/views/primary.php`.
- `activityheaderconfig` reads one key, `notitle`. Per layout, `'options' => ['activityheader' => [...]]` accepts
  `notitle`, `nodescription` and `nocompletion`, and the layout value wins over the theme value. Source:
  `public/lib/classes/output/activity_header.php`.
- To add items, register `\core\hook\navigation\primary_extend` (guarded as above). To change what is exported
  to the template, subclass `\core\navigation\output\primary` and instantiate the subclass in the theme's own
  layout file, because Boost's layout files create the core class by name.

The breadcrumb, the context header, the edit switch and the layout options are in
[reference/navigation-and-headers.md](reference/navigation-and-headers.md).

## React-rendered regions

**5.3+:** the primary navigation, the secondary navigation, the edit-mode switch and the Timeline block are
drawn by React components. The first three are still mounted from Mustache templates a theme can override and
are styled by the theme's SCSS; only the Timeline block is out of reach of templates. A theme can also override
the component itself from `js/esm/src/overrides/`, but that path has no fallback to a parent theme, needs a full
Moodle checkout to build, and no component override was built or run for this skill. Read
[versions/moodle-5.3.md](versions/moodle-5.3.md) before touching any of these regions. **5.2 only:** none of this
exists; the same regions are Mustache templates with AMD modules.

## Checking the result

- `$OUTPUT` in a CLI script is `core_renderer_cli` (seen on 5.3.0), and a PHPUnit run is a CLI script too, so
  theme renderer and template overrides cannot be judged there. Load a page in a browser or assert on it in Behat;
  in PHPUnit ask for `$PAGE->get_renderer('core', null, RENDERER_TARGET_GENERAL)` (read in the source, not run).
- Assert the change the override predicts (the body class, the extra element) on a page that uses that layout,
  as the role that will see it. The theme Behat and PHPUnit recipes are in `moodle-theme-testing-release`.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Child theme without `$THEME->rendererfactory` | No theme renderer is used, Boost's included; no error | Set `theme_overridden_renderer_factory` in the child's `config.php` |
| `class core_renderer extends \core_renderer` in a Boost child | Boost's breadcrumb, context header and colour-mode menu are lost | Extend `\theme_boost\output\core_renderer` (or the nearest parent's class) |
| Class in `classes/output/` with the wrong name or namespace | Silently ignored | Match the names in [reference/renderer-lookup.md](reference/renderer-lookup.md) |
| Using a theme renderer method in the maintenance layout or a CLI script | Method missing: fatal error in PHP, nothing in Mustache | Keep it out, or ship `core_renderer_maintenance` too |
| Copying a core method body into the override | The copy misses later core fixes; **5.3+:** copied 5.2 code calling `user_can_view_profile()` emits deprecation notices | Call `parent::` and change the result |
| Hook callback without an active-theme guard | The theme's markup appears under every theme on the site | Check `$PAGE->theme->name` and `->parents` first |
| `pix_core/t/edit.svg` to change the edit icon | Nothing changes: the icon is a Font Awesome glyph | Change the map through an icon system subclass |
| `get_fontawesome_icon_map()` returning a `core:` key | Ignored: existing keys win | Subclass the icon system |
| Mapping a key with no SVG file behind it | Core's `icon_system_fontawesome_test` fails on every site with the theme installed | Ship `pix/<name>.svg` for each mapped key |
| `empty($this->page->cm)` in a renderer | Always true | `$cm = $this->page->cm; if (!$cm) { ... }` |
| **5.3+:** overriding `block_timeline`'s renderer or templates | Fatal error for the renderer; templates are dead files | Delete them; style with SCSS or override the component |
| **5.3+:** a React component override in a parent theme, expected in the child | The child gets core's component | Re-export it in the child ([versions/moodle-5.3.md](versions/moodle-5.3.md)) |

## Reference files

| File | Read it when |
|---|---|
| [reference/renderer-lookup.md](reference/renderer-lookup.md) | Overriding a plugin, subsystem, email or maintenance renderer and the exact class name or parent class is needed; or an override is not being picked up |
| [reference/hooks-and-callbacks.md](reference/hooks-and-callbacks.md) | Choosing which hook or `lib.php` callback puts markup or attributes in a given place, or checking whether a hook exists on 5.2 |
| [reference/icons-and-pix.md](reference/icons-and-pix.md) | Changing an icon or image and the simple table above did not settle it: map internals, resolution order, activity icons, deprecated icons, favicon, dark mode |
| [reference/navigation-and-headers.md](reference/navigation-and-headers.md) | Changing primary or secondary navigation data, the breadcrumb, the context header, the activity header or the edit switch from PHP |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](versions/moodle-5.2.md): what the baseline lacks or still has (legacy menus, `render_login()` in Boost, no Boost hooks) |
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md): renderer and hook changes, React-rendered regions, component overrides |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme
- https://moodledev.io/docs/5.3/apis/subsystems/output
- https://moodledev.io/docs/5.3/apis/core/hooks
- https://moodledev.io/docs/5.3/apis/plugintypes/theme/images
- https://moodledev.io/docs/5.3/guides/javascript/react/theming (its "Since 5.2" tag is wrong: the code is in 5.3 only)
- https://moodledev.io/general/development/policies/deprecation/icon-deprecation
