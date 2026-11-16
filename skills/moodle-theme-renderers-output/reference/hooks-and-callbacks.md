# Hooks and callbacks a theme can use for output

Read this when choosing which hook or `lib.php` callback puts markup or attributes in a given place on the page,
or when checking whether a hook exists on Moodle 5.2.

How hooks are declared, prioritised and tested is in the `moodle-hooks-api` skill. This file lists the hooks that
matter for theme output and the rules that are specific to a theme. Read in the 5.3.0 and 5.2 source
(`public/lib/classes/hook/`, `public/lib/classes/output/core_renderer.php`); only
`before_standard_head_html_generation` was run from a theme (5.3.0).

## The rule that is specific to themes

`db/hooks.php` of every installed plugin is registered site-wide, and a theme is a plugin. A theme's callback
therefore runs on every page, including pages shown in another theme. Start each callback with:

```php
global $PAGE;

if (during_initial_install()) {
    return;
}
if ($PAGE->theme->name !== 'mytheme' && !in_array('mytheme', $PAGE->theme->parents, true)) {
    return;
}
```

Put it in one static helper (`\theme_mytheme\local\hook_callbacks::is_active()`) when there is more than one
callback. Boost itself does this for its colour-mode hooks (`public/theme/boost/classes/colour_mode.php`,
`is_boost_theme()`, 5.3.0), and that is also why a child of Boost gets Boost's hook behaviour.

Reading `$PAGE->theme` chooses and loads the theme if that has not happened yet. In the output hooks below it has
already happened. In hooks that run before output starts (`\core\hook\after_config` for example) it has not:
reading it there fixes the theme before the script has set its course and context, after which
`$PAGE->set_course()` throws "The theme has already been set up for this page ready for output", and the theme's
`lib.php` and its constants are not loaded either. In an early hook, decide from stored config
(`get_config('theme_mytheme', ...)`, `$CFG->theme`) and literal values only.

## Output hooks

All are in the namespace `\core\hook\output`. Each has a public read-only `$renderer` property except the two
configuration hooks at the end.

| Hook class | Dispatched from | What a callback can do | 5.2 |
|---|---|---|---|
| `before_html_attributes` | `core_renderer::htmlattributes()`, printed inside the `<html>` tag | `add_attribute($name, $value)`, `remove_attribute($name)` | yes |
| `before_http_headers` | start of `core_renderer::header()` | Run code before headers are sent (no output methods) | yes |
| `after_http_headers` | end of `core_renderer::header()` | `add_html($html)`: appended to what `header()` returns, so after the page header and before the page content | yes |
| `before_standard_head_html_generation` | `core_renderer::standard_head_html()`, inside `<head>` | `add_html($html)`: meta tags, links, inline script | yes |
| `before_standard_top_of_body_html_generation` | `core_renderer::standard_top_of_body_html()`, just after `<body>` | `add_html($html)`: banners, skip links | yes |
| `after_standard_main_region_html_generation` | `core_renderer::standard_after_main_region_html()` | `add_html($html)`: after the main region | yes |
| `before_footer_html_generation` | `core_renderer::footer()`, before the footer is built | `add_html($html)`: last chance to require JavaScript or add hidden markup | yes |
| `before_standard_footer_html_generation` | `core_renderer::standard_footer_html()` | `add_html($html)`: inside the standard footer | yes |
| `extend_url` | the mobile app tool only, for the URL it adds to the page (no general dispatch found by `grep` in 5.3.0) | `add_param(...)` | yes |
| `before_requirejs_config` | building the RequireJS configuration | Map AMD module names to ESM modules | **5.3+** |
| `before_import_map_config` | building the page's import map | `add_import(...)`: add an ESM specifier | **5.3+** |

Notes:

- A hook's HTML appears only if the layout template prints the matching renderer call. A theme layout that drops
  `{{{ output.standard_top_of_body_html }}}` or `{{{ output.standard_after_main_region_html }}}` silently
  disables every plugin's use of those hooks. Keep every `output.*` call of the Boost layout being copied.
- `add_html()` takes raw HTML. Escape values with `s()`, and validate anything read from a setting.
- `before_html_attributes` is how Boost puts `data-bs-theme` on `<html>` in 5.3. A theme that needs an attribute
  on `<html>` from the first byte (to avoid a flash before JavaScript runs) uses the same hook.
- Registering a callback for a hook class that the running version lacks is harmless: the entry is stored under
  the hook's name as a string and only the callback is checked. A theme supporting 5.2 and 5.3 can list the two
  5.3-only hooks without a version test (read in `public/lib/classes/hook/manager.php`; not run).
- Rendering a template queues its `{{#js}}` blocks on the page even when the returned HTML is thrown away. A
  callback that renders a template only to decide whether to print it still gets that JavaScript on the page.
- The legacy `lib.php` callbacks these hooks replaced (`<plugin>_before_standard_html_head()` and the like) are
  still called through each hook's `process_legacy_callbacks()`, with a deprecation path. Do not add new ones.

## Navigation hooks

Namespace `\core\hook\navigation`, both in 5.2 and 5.3:

| Hook class | Dispatched from | Use |
|---|---|---|
| `primary_extend` | end of `\core\navigation\views\primary::initialise()` | `$hook->get_primaryview()` returns the view; call `->add(...)` on it to add a primary navigation item |
| `secondary_extend` | `\core\navigation\views\secondary` | `$hook->get_secondaryview()`; add or remove secondary navigation nodes |

A theme callback for these needs the active-theme guard too, or the item shows under every theme.

```php
public static function primary_extend(\core\hook\navigation\primary_extend $hook): void {
    if (!self::is_active()) {
        return;
    }
    $hook->get_primaryview()->add(
        get_string('helpcentre', 'theme_mytheme'),
        new \core\url('/theme/mytheme/help.php'),
        \navigation_node::TYPE_CUSTOM,
        null,
        'mytheme_help',
    );
}
```

Read in the source, not run. For items an administrator should control, the site's custom menu setting is the
no-code route and reaches the same primary navigation.

## `lib.php` callbacks

| Function | Called for | Use |
|---|---|---|
| `theme_mytheme_page_init(moodle_page $page)` | The theme in use only (not its parents' functions) | Per-page set-up at the start of `header()`, such as requiring a JavaScript module on every page |
| `theme_mytheme_alter_css_urls(&$urls)` | The theme in use only | Change the stylesheet URLs |
| `theme_mytheme_get_fontawesome_icon_map()` | Every installed theme, active or not | Add icon map entries in the theme's own namespace |
| `theme_mytheme_get_deprecated_icons()` | Every installed theme | Mark the theme's own icons deprecated |
| `theme_mytheme_user_preferences()` | Every installed theme | Declare user preferences that JavaScript may set (`moodle-theme-settings`) |
| `theme_mytheme_pluginfile(...)` | By component | Serve files stored by theme settings (`moodle-theme-settings`) |

- `page_init` is looked up by the current theme's name only (`theme_config::init_page()`), so a child theme does
  not run its parent's `page_init` unless the child's function calls it.
- Functions found through `get_plugins_with_function()` (the icon callbacks, user preferences) run whenever the
  theme is installed. Keep them cheap and free of assumptions about the current page.
- The SCSS callbacks named in `config.php` are covered by `moodle-theme-scss`.

## Choosing between a hook and a renderer method

| Need | Use |
|---|---|
| Markup that must appear with any layout of this theme and of its children, with no template edit | Hook |
| Markup placed at a specific point of a layout the theme owns | Renderer method called from the template |
| Change what an existing renderer method returns | Renderer override |
| Run something on every page of this theme before output | `theme_mytheme_page_init()` |
| Content injected into the course page next to an activity | Hook `before_footer_html_generation` plus a JavaScript module that moves the markup; gate on `$PAGE->url`, not on the page type, because `course-view-<format>` is also set by backup, report and grade pages |

A hook survives a parent theme changing its layout templates; a template edit does not. Prefer the hook when both
would work.
