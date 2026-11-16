---
name: moodle-hooks-api
description: Use when a plugin listens to or dispatches a Moodle hook — db/hooks.php, \core\hook\manager, \core\di, hook classes under classes/hook/, replacing lib.php callbacks such as before_http_headers, before_footer, before_standard_html_head, before_standard_top_of_body_html, add_htmlattributes, after_config or bulk_user_actions, the debugging message "Callback ... should be migrated to new hook callback", extend_user_menu, primary_extend, secondary_extend, or testing hook callbacks with phpunit_get_instance. Skip when reacting to a logged fact with \core\event observers (moodle-plugin-development), or when choosing where a theme puts page markup (moodle-theme-renderers-output).
---

# Moodle Hooks API

## Overview

A hook is a plain PHP object that core (or a plugin) creates, hands to `\core\hook\manager::dispatch()`, and then
reads back. Callbacks registered in each component's `db/hooks.php` receive that object and change it: add HTML,
add attributes, add a menu item, stop propagation. The API is PSR-14 underneath and is the same on Moodle 5.2 and
5.3 apart from the hooks listed in the version notes (`public/lib/classes/hook/manager.php` is byte-identical in
both, read in the 5.2 and 5.3.0 source).

## When to Use

- A plugin must add something to every page (head HTML, top of body, footer, `<html>` attributes, HTTP headers)
- Replacing a `lib.php` callback that core now reports as "should be migrated to new hook callback"
- Reacting to a core action that has a hook (course created or deleted, user enrolled, group changed, file
  created, quiz structure changed) and needing to change the outcome, not only log it
- Writing a hook in your own plugin so other plugins can extend it
- Testing a hook callback in PHPUnit
- **Skip when:** you only need to react to something that already happened and was logged (an event observer in
  `db/events.php`, see `moodle-plugin-development`), or you are choosing which hook a theme uses for page output
  (`moodle-theme-renderers-output`).

Hooks versus events: an event is a record of a fact, delivered after the transaction, and an observer cannot change
the outcome. A hook runs inline, and the dispatcher reads what callbacks put into it.

## How a dispatch works

1. Core builds the hook object, for example `new before_footer_html_generation($renderer)`.
2. For hooks that replace a legacy callback, core calls `$hook->process_legacy_callbacks()` first, which calls the
   old `lib.php` functions of plugins that have not registered the hook.
3. `\core\di::get(\core\hook\manager::class)->dispatch($hook)` calls each registered callback in priority order
   (highest first, default 100). If the hook implements `\Psr\EventDispatcher\StoppableEventInterface`, the
   manager checks `isPropagationStopped()` before each callback.
4. Core reads the result (`$hook->get_output()`, `get_attributes()` and so on).

Source: `public/lib/classes/output/core_renderer.php` (`htmlattributes()`, `standard_head_html()`) and
`public/lib/classes/hook/manager.php` (`dispatch()`, `prioritise_callbacks()`), 5.3.0.

## Listening to a core hook (the default recipe)

`db/hooks.php`:

```php
<?php
// (GPL header)
defined('MOODLE_INTERNAL') || die();

$callbacks = [
    [
        'hook' => \core\hook\output\before_footer_html_generation::class,
        'callback' => [\local_example\hook_callbacks::class, 'before_footer'],
        'priority' => 100,
    ],
];
```

`classes/hook_callbacks.php`:

```php
<?php
// (GPL header)
namespace local_example;

use core\hook\output\before_footer_html_generation;

/**
 * Hook callbacks for local_example.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
final class hook_callbacks {
    /**
     * Add the help banner to the footer.
     *
     * @param before_footer_html_generation $hook
     */
    public static function before_footer(before_footer_html_generation $hook): void {
        if (during_initial_install() || !isloggedin() || isguestuser()) {
            return;
        }
        $hook->add_html($hook->renderer->render_from_template('local_example/banner', []));
    }
}
```

Then purge caches (`php admin/cli/purge_caches.php` from the Moodle root) or bump `$plugin->version`; the upgrade
purges too.

Rules the manager enforces (`manager.php` `normalise_callback()`, `is_callback_valid()`, 5.3.0):

- **The callback must be a static method.** A non-static method is skipped with the debugging message "Callback
  method not a static method", so the hook silently does nothing on a site without developer debugging. Write
  `public static function`.
- `callback` is either `[Class::class, 'method']` or the string `'\local_example\hook_callbacks::method'`. A
  closure or a plain function name is rejected with debugging and ignored.
- `hook` is the class name as a string. A class that does not exist is not an error: the entry is stored under that
  name and never dispatched (`add_component_callbacks()`). This is what lets one `db/hooks.php` register a 5.3-only
  hook and still install on 5.2.
- `priority` is an integer; higher runs first; equal priorities have no guaranteed order.

## Migrating a lib.php callback

Core marks a legacy callback as replaced with `#[\core\attribute\hook\replaces_callbacks('before_footer')]` on the
hook class (or the older `deprecated_callback_replacement` interface). Two behaviours follow, both in
`public/lib/moodlelib.php` (`get_plugins_with_function()`, `component_callback()`), 5.2 and 5.3.0:

- A plugin that still has only the old function gets it called, plus the developer debugging "Callback
  before_footer in local_example component should be migrated to new hook callback for ...". Under
  `moodle-plugin-ci phpunit --fail-on-warning` or Behat this debugging fails the run.
- A plugin that has both the old function and a `db/hooks.php` entry for the replacing hook gets only the hook
  called. So keeping the old function costs nothing while you still support a branch without the hook.

| Legacy `lib.php` callback | Hook (all exist on 5.2 and 5.3) |
|---|---|
| `<component>_before_http_headers()` | `\core\hook\output\before_http_headers` |
| `<component>_before_standard_html_head()` | `\core\hook\output\before_standard_head_html_generation` |
| `<component>_before_standard_top_of_body_html()` | `\core\hook\output\before_standard_top_of_body_html_generation` |
| `<component>_add_htmlattributes()` | `\core\hook\output\before_html_attributes` |
| `<component>_before_footer()` | `\core\hook\output\before_footer_html_generation` |
| `<component>_standard_footer_html()` | `\core\hook\output\before_standard_footer_html_generation` |
| `<component>_standard_after_main_region_html()` | `\core\hook\output\after_standard_main_region_html_generation` |
| `<component>_after_config()` | `\core\hook\after_config` |
| `<component>_bulk_user_actions()` | `\core_user\hook\extend_bulk_user_actions` |
| `<component>_before_file_created()`, `_after_file_created()` | `\core_files\hook\before_file_created`, `after_file_created` |
| `quiz_structure_modified` / `quiz_attempt_deleted` callback classes | `\mod_quiz\hook\structure_modified`, `attempt_state_changed` |

Source: `replaces_callbacks` attributes under `public/lib/classes/hook/`, `public/files/classes/hook/`,
`public/mod/quiz/classes/hook/` and `get_deprecated_plugin_callbacks()` in
`public/user/classes/hook/extend_bulk_user_actions.php`, read in 5.2 and 5.3.0.

These are still ordinary `lib.php` callbacks with no hook on 5.2 or 5.3, so do not look for one:
`extend_navigation()`, `extend_navigation_course()`, `extend_navigation_user()`, `extend_navigation_frontpage()`,
`extend_settings_navigation()`, `extend_navigation_user_settings()`, `extend_navigation_category_settings()`,
`myprofile_navigation()`, `after_require_login()`, `before_session_start()`, `pre_course_delete()`,
`pre_user_delete()`, `coursemodule_standard_elements()`, `coursemodule_edit_post_actions()`,
`control_view_profile()`, `render_navbar_output()`, `pluginfile()`, `output_fragment_*()`, `get_fontawesome_icon_map()`
(from the `get_plugins_with_function()` and `component_callback()` calls in the 5.3.0 source).
`\core\hook\navigation\primary_extend` and `secondary_extend` exist but replace nothing: they give
`get_primaryview()` / `get_secondaryview()` for adding nodes to those views.

Migration steps:

1. `grep -nE "function [a-z]+_[a-z0-9]+_(before_http_headers|before_standard_html_head|before_standard_top_of_body_html|add_htmlattributes|before_footer|standard_footer_html|standard_after_main_region_html|after_config|bulk_user_actions|before_file_created|after_file_created)\(" lib.php`
2. Move each body into a static method of `classes/hook_callbacks.php`; a legacy callback that returned a string
   now calls `$hook->add_html($html)`; `add_htmlattributes()` that returned an array calls
   `$hook->add_attribute($name, $value)` per pair.
3. Register each in `db/hooks.php`.
4. Delete the old function once every branch you support has the hook (all of the table above exist on 5.2), or
   keep it as the fallback for older branches; core will not call both.
5. Purge caches and run with `DEBUG_DEVELOPER`; the "should be migrated" message must be gone.

## Writing your own hook

Put the class in your component's `hook` namespace (`classes/hook/`), which is how the Hooks overview page and
`\core\hooks::discover_hooks()` find it (`public/lib/classes/hooks.php`, 5.3.0):

```php
<?php
// (GPL header)
namespace local_example\hook;

/**
 * Lets other plugins add actions to the widget toolbar or stop it rendering.
 *
 * @package    local_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    https://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
#[\core\attribute\label('Allows plugins to add actions to the widget toolbar')]
#[\core\attribute\tags('widget', 'output')]
final class before_widget_toolbar implements \Psr\EventDispatcher\StoppableEventInterface {
    use \core\hook\stoppable_trait;

    /** @var array<string, string> action name => HTML */
    private array $actions = [];

    /**
     * Constructor.
     *
     * @param \context $context The widget context.
     * @param int $widgetid The widget id.
     */
    public function __construct(
        /** @var \context The widget context */
        public readonly \context $context,
        /** @var int The widget id */
        public readonly int $widgetid,
    ) {
    }

    /**
     * Add an action.
     *
     * @param string $name
     * @param string $html
     */
    public function add_action(string $name, string $html): void {
        $this->actions[$name] = $html;
    }

    /**
     * Get the actions added by callbacks.
     *
     * @return array<string, string>
     */
    public function get_actions(): array {
        return $this->actions;
    }
}
```

Dispatch it and read it back:

```php
$hook = new \local_example\hook\before_widget_toolbar($context, $widget->id);
\core\di::get(\core\hook\manager::class)->dispatch($hook);
if ($hook->isPropagationStopped()) {
    return '';
}
$actions = $hook->get_actions();
```

- Description: either the two attributes above or `implements \core\hook\described_hook` with static
  `get_hook_description()` and `get_hook_tags()`. Both feed Site administration > Development > Hooks overview
  (`/admin/hooks.php`).
- Stopping: `stoppable_trait` gives `stop_propagation()` and `isPropagationStopped()`. There is no
  `\core\hook\stoppable_event_interface`; implement the PSR interface. Only make a hook stoppable when a veto means
  something.
- Keep inputs `readonly` and give callbacks narrow methods (`add_action()`), so a callback cannot rewrite what
  other callbacks added. Once released, the hook class, its constructor and its methods are a public API under the
  deprecation policy (https://moodledev.io/general/development/policies/deprecation).
- If your hook replaces a callback of your own, add `#[\core\attribute\hook\replaces_callbacks('mycallback')]` and a
  `process_legacy_callbacks()` method that calls `get_plugins_with_function(function: 'mycallback',
  migratedtohook: true)`, and call it before `dispatch()`, as the core output hooks do.
- `dispatch()` before `setup.php` has finished only logs "Hooks cannot be dispatched yet" and returns the hook
  unchanged.

## Testing hook callbacks

Hook callbacks are not cached in PHPUnit (`should_cache()` returns false), so a callback in `db/hooks.php` runs in
tests exactly as on the site. Two ways to test:

```php
// 1. Call the callback directly with a real hook object: tests the callback alone.
$page = new \moodle_page();
$renderer = $page->get_renderer('core');
$hook = new \core\hook\output\before_footer_html_generation($renderer);
\local_example\hook_callbacks::before_footer($hook);
$this->assertStringContainsString('local_example-banner', $hook->get_output());

// 2. Dispatch through the real manager: also proves db/hooks.php is right.
\core\di::get(\core\hook\manager::class)->dispatch($hook);
```

To test code that dispatches your own hook with a known set of callbacks, replace the manager:

```php
\core\di::set(
    \core\hook\manager::class,
    \core\hook\manager::phpunit_get_instance([
        'local_example' => __DIR__ . '/fixtures/hooks.php',
    ]),
);
```

or redirect one hook to a closure with
`\core\di::get(\core\hook\manager::class)->phpunit_redirect_hook(hookclass::class, fn($hook) => ...)` and undo it
with `phpunit_stop_redirections()` (`manager.php`; core example `public/lib/tests/core_renderer_test.php`, 5.3.0).
Cover both branches: the callback acts, and the callback returns early (guest, wrong page, feature off).

## Traps

- **An exception thrown from an `after_config` callback never reaches the browser with your status code.** The
  page is answered `500 Internal Server Error` by the bootstrap renderer, or `404 Not Found` by
  `core_renderer::fatal_error()` when output has not started, whatever `http_response_code()` you set first
  (`public/lib/classes/output/bootstrap_renderer.php` `early_error()`, `core_renderer.php` `fatal_error()`, read in
  5.3.0, not run). The same holds for an `after_require_login()` callback. To refuse with a real 403, send it and stop:

  ```php
  public static function after_config(\core\hook\after_config $hook): void {
      if (during_initial_install() || CLI_SCRIPT || !self::must_refuse()) {
          return;
      }
      if (PHPUNIT_TEST) {
          throw new \moodle_exception('accessdenied', 'admin');
      }
      http_response_code(403);
      echo '<!DOCTYPE html><html><head><meta charset="utf-8"><title>403</title></head><body><p>' .
          s(get_string('accessdenied', 'admin')) . '</p></body></html>';
      exit;
  }
  ```

- **`after_config` runs on every request**, including CLI scripts, cron, web services and the upgrade itself.
  Return early unless the request is one you mean to change; database reads there cost on every hit.
- **A hook callback in a plugin runs site-wide**, including on pages of other plugins and, for a theme's callbacks,
  under other themes. Gate on the page (`$PAGE->url`, a capability, `$PAGE->theme->name`), not on the assumption
  that you are only called where you wanted. Theme-specific gating: `moodle-theme-renderers-output`.
- **`$PAGE->pagetype` is not a safe gate for course pages**: `course-view-<format>` is also set on backup, report
  and grade pages. Content injected onto course pages from a non-activity plugin has more traps (anchoring,
  reactive reloads, subsection order): `moodle-field-lessons`.
- **Editing `db/hooks.php` without purging** leaves the old list in the callback cache (`$CFG->cachedir` and
  `$CFG->localcachedir`, file `hookcallbacks.php`); the new callback does not run and nothing reports it.
- **Site admins can re-prioritise or disable a callback** in `config.php` with `$CFG->hooks_callback_overrides`
  (`['\core\hook\output\before_footer_html_generation' => ['local_example\hook_callbacks::before_footer' =>
  ['disabled' => true]]]`). When a callback "does not run" on one site only, look there.
- **Order between plugins is not a contract.** If your callback must see what another added, give it a lower
  priority and still handle the case where the other plugin is absent.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Instance method as callback | Skipped; only a developer debugging line says why | `public static function` |
| `'callback' => function ($hook) {...}` | Rejected at load, hook never runs | `[Class::class, 'method']` |
| Implementing `\core\hook\stoppable_event_interface` | Fatal: interface does not exist | `\Psr\EventDispatcher\StoppableEventInterface` + `\core\hook\stoppable_trait` |
| Calling `stop()` on a core stoppable hook | Fatal: no such method | `$hook->stop_propagation()` |
| `get_primary_view()` on `primary_extend` | Fatal: undefined method | `$hook->get_primaryview()` |
| `new before_standard_top_of_body_html_generation()` in a test | ArgumentCountError: the renderer is required | Pass `$PAGE->get_renderer('core')` |
| Looking for a hook that replaces `extend_navigation()` | None exists on 5.2 or 5.3 | Keep the `lib.php` callback |
| Removing the legacy function while a supported branch lacks the hook | That branch loses the feature | Keep both; core skips the old one when the hook is registered |
| Throwing from `after_config` to deny access | Browser gets 500 or 404 | Send 403, print a minimal page, `exit` |
| `php admin/cli/hooks_list.php` | No such script | Site administration > Development > Hooks overview (`/admin/hooks.php`) |
| Treating the "should be migrated" debugging as noise | `--fail-on-warning` CI and Behat fail | Register the hook |

## Reference files

| File | Read it when |
|---|---|
| [reference/core-hook-catalogue.md](reference/core-hook-catalogue.md) | you need to know whether core has a hook for an action (course, enrolment, group, user, file, AI, backup, quiz, output) and its class name, constructor and methods |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md): hooks added in 5.3 (email, import map, RequireJS, Composer DI) and the `extend_user_menu` change |

## References

- https://moodledev.io/docs/apis/core/hooks
- https://moodledev.io/docs/apis/core/di
- https://moodledev.io/general/development/policies/deprecation
- `public/lib/classes/hook/manager.php` (5.2 and 5.3.0)
