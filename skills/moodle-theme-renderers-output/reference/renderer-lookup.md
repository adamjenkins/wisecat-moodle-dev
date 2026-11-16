# Renderer lookup: class names, targets and dispatch

Read this when a theme overrides a plugin, subsystem, email or maintenance renderer and the exact class name or
parent class is needed, or when an override exists but is not being used.

Everything here was read in `public/lib/classes/output/renderer_factory/` and
`public/lib/classes/output/theme_config.php` on Moodle 5.3.0. The three factory files are byte-identical in 5.2
(compared with `diff`). Only the `core_renderer` case was run (5.3.0, a child of Boost).

## How a renderer is found

1. Code asks `$PAGE->get_renderer($component, $subtype = null, $target = null)`. `$OUTPUT` is the result of
   `get_renderer('core')` for the main page.
2. `theme_config::get_renderer()` creates the factory named in `$THEME->rendererfactory` once per theme object.
   The key is read from the theme's own `config.php` only: it is not inherited.
3. `theme_overridden_renderer_factory` builds the list of prefixes `theme_<current>`, then `theme_<parent>` for
   each entry of `$THEME->parents` in the declared order (nearest first).
4. It makes four passes and returns the first class that exists:
   1. each prefix with the target suffix (`_maintenance`, `_cli`, ...);
   2. the component's own class with the target suffix;
   3. each prefix without the suffix;
   4. the component's own class without the suffix.

With the general target the suffix is empty, so passes 1 and 2 are the whole story: theme, parents, component.
With any other target, pass 2 is where core's special renderers win over the theme's general ones.

## Class names tried for a theme

`<P>` is the prefix `theme_mytheme`. `<C>` is the normalised component (`core`, `mod_quiz`, `format_topics`,
`core_h5p`). `<S>` is the subtype.

| Request | Namespaced names tried (autoloaded from `classes/`) | Legacy name (must already be loaded) |
|---|---|---|
| `get_renderer('<C>')` | `\<P>\output\<C>_renderer` | `<P>_<C>_renderer` |
| `get_renderer('<C>', '<S>')` | `\<P>\output\<C>\<S>_renderer`, then `\<P>\output\<C>\<S>\renderer` | `<P>_<C>_<S>_renderer` |

Legacy-named classes are found only if something has loaded them: core includes the theme's `renderers.php` (and
each parent's) when the theme is loaded, which is the only reason a class there works. New code uses the
namespaced names.

Worked examples:

| What is overridden | Theme class | File | Extends |
|---|---|---|---|
| Core renderer | `theme_mytheme\output\core_renderer` | `classes/output/core_renderer.php` | `\theme_boost\output\core_renderer` |
| Core renderer on the maintenance layout | `theme_mytheme\output\core_renderer_maintenance` | `classes/output/core_renderer_maintenance.php` | `\core\output\core_renderer_maintenance` |
| Course renderer (`get_renderer('core', 'course')`) | `theme_mytheme\output\core\course_renderer` | `classes/output/core/course_renderer.php` | `\core_course_renderer` |
| Course management (`get_renderer('core_course', 'management')`) | `theme_mytheme\output\core_course\management\renderer` | `classes/output/core_course/management/renderer.php` | `\core_course_management_renderer` |
| An activity module | `theme_mytheme\output\mod_quiz_renderer` | `classes/output/mod_quiz_renderer.php` | the class the plugin's own lookup returns |
| A course format | `theme_mytheme\output\format_topics_renderer` | `classes/output/format_topics_renderer.php` | `\format_topics\output\renderer` |
| H5P | `theme_mytheme\output\core_h5p_renderer` | `classes/output/core_h5p_renderer.php` | `\core_h5p\output\renderer` |

The "Extends" column for the course rows was taken from a published Boost child theme; check the parent class in
the version being targeted before copying it.

## Finding the class to extend

The component's own class is found by the same code, with these names (first that exists):

| Request | Names tried |
|---|---|
| `get_renderer('<C>')` | `\<C>\output\renderer`, then `<C>_renderer` |
| `get_renderer('<C>', '<S>')` | `\<C>\output\<S>_renderer`, then `\<C>\output\<S>\renderer`, then `<C>_<S>_renderer` |

Before trying names, the factory includes the component's `renderer.php` if it exists (for `core` with a subtype,
the subsystem's `renderer.php`), so a legacy parent class such as `mod_quiz_renderer` is loaded by the time the
theme class is autoloaded. Extend whichever of those names the plugin really defines; when both a namespaced
class and a legacy alias exist, extend the namespaced one.

A theme class is only loaded when that component's renderer is requested, and the request itself fails if the
component is not installed, so a theme may ship overrides for optional plugins. What does break is a parent class
that was removed from an installed component: the autoload of the theme class is then a fatal error.

## Targets and suffixes

`get_target_suffix()` decides the target:

| Situation | Target | Suffix |
|---|---|---|
| A normal page | general | none |
| `$PAGE->pagelayout === 'maintenance'` (maintenance mode message, web upgrade, upgrade settings page) | maintenance | `_maintenance` |
| `CLI_SCRIPT` with no explicit target (includes PHPUnit) | cli | `_cli` |
| `AJAX_SCRIPT` with no explicit target and no `PREFERRED_RENDERER_TARGET` | ajax | `_ajax` |
| Explicit `RENDERER_TARGET_TEXTEMAIL` / `RENDERER_TARGET_HTMLEMAIL` | email | `_textemail` / `_htmlemail` |

- `PREFERRED_RENDERER_TARGET`, when defined, wins over the CLI and AJAX rules. `public/lib/ajax/service.php`
  defines it as general, so web-service calls made through `core/ajax`, fragments included, use the general
  renderer and therefore the theme's `core_renderer`. Other `AJAX_SCRIPT` endpoints get `core_renderer_ajax`.
- Core ships `core_renderer_cli`, `core_renderer_ajax` and `core_renderer_maintenance`, all extending core's
  `core_renderer`, not Boost's or the theme's. Under those targets the theme's general `core_renderer` is never
  reached for the `core` component. Plugins rarely ship suffixed renderers, so a theme's plugin renderer override
  is still used under those targets (pass 3).
- `core_renderer_maintenance` returns an empty string from `block()`, `blocks()`, `blocks_for_region()`,
  `course_content_header()`, `course_content_footer()`, `course_header()`, `course_footer()`, `custom_menu()`,
  `file_picker()`, `lang_menu()`, `login_info()`, `secure_login_info()` and `user_picture()`, and its constructor
  throws unless both the target and the page layout are `maintenance`. The page can run while database tables are
  missing or out of date, so a maintenance renderer or template must not depend on theme settings, blocks, menus
  or a logged-in user. Source: `public/lib/classes/output/core_renderer_maintenance.php`, 5.3.0.
- Email renderers: a module that sends templated mail asks for a renderer with a subtype and an email target.
  The forum calls `get_renderer('mod_forum', 'email', $target)` with `htmlemail` and `textemail`
  (`public/mod/forum/classes/task/send_user_notifications.php`, 5.3.0 and 5.2). The theme class follows the
  subtype row with the suffix appended: `theme_mytheme\output\mod_forum\email_renderer_htmlemail` is tried first,
  then `theme_mytheme\output\mod_forum\email\renderer_htmlemail`; for plain text the suffix is `_textemail`.
  The forum's own classes are `\mod_forum\output\email\renderer` (HTML) and
  `\mod_forum\output\email\renderer_textemail`. Because the forum ships a suffixed text renderer, a theme class
  without the `_textemail` suffix never reaches plain-text mail (pass 2 wins over pass 3); an unsuffixed theme
  class does reach HTML mail. Read in the factory code and the forum source; not run.

## How `render()` picks a method

`$renderer->render($widget)` (`public/lib/classes/output/renderer_base.php`, 5.3.0):

1. Takes the widget's class name without namespace, minus a `_renderable` suffix, and calls
   `render_<name>()` if the renderer has it. For a class under `<component>\output\<a>\<b>` it first tries
   `render_<a>__<b>()` (double underscore between namespace parts).
2. **5.3+:** a `\core\output\react_component_renderable` is rendered as a React mount point.
3. A `named_templatable` is rendered with `get_template_name()` and `export_for_template()`.
4. A `templatable` is rendered with the template `<component>/<class name>`.
5. Otherwise a coding exception: "Can not render widget, renderer method ('render_x') not found."

A plugin renderer (`plugin_renderer_base`) that has no `render_<name>()` and whose widget is not a
`named_templatable` passes the widget to the core renderer, which is the theme's `core_renderer` on a normal page.
So there are two places a theme can take over a widget: `render_<name>()` on its override of the plugin's renderer,
or, for widgets rendered through `$OUTPUT`, `render_<name>()` on its `core_renderer`.

Calling an unknown method on a plugin renderer is forwarded to the core renderer by `__call()`, so plugin code
that calls `$this->mytheme_banner()` would work only under that theme. Do not make plugin code depend on theme
methods.

## Debugging an override that is not used

1. `config.php` of the theme being used (not the parent) sets `rendererfactory`.
2. The class name, namespace and file path match the tables above; the file is under `classes/` so the
   autoloader finds it; caches were purged after the file was added.
3. The request is for the component and subtype expected. `get_class($PAGE->get_renderer('mod_quiz'))` printed
   from a temporary page (not from CLI, which changes the target) names the class in use.
4. The page is not on the maintenance layout and the script is not CLI or a non-service AJAX script.
5. A nearer theme in the chain does not already define the same class: the first prefix that has it wins, and the
   classes of farther parents are not consulted.
6. The code path really goes through a renderer. Much newer core output renders a template straight from an
   output class; that is changed with a template override, not a renderer.
