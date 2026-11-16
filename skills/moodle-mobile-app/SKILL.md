---
name: moodle-mobile-app
description: Use when adding Moodle app (mobile) support to a plugin - db/mobile.php handlers and delegates (CoreMainMenuDelegate, CoreCourseModuleDelegate, CoreCourseOptionsDelegate, CoreBlockDelegate, CoreQuestionDelegate), classes/output/mobile.php methods called through tool_mobile_get_content, templates/mobileapp Mustache with {{=<% %>=}} and Ionic markup, otherdata and CONTENT_OTHERDATA, core-site-plugins-call-ws and other site-plugin directives, handler JavaScript (this.CoreSitesProvider, updateContent caching, detectChanges), offlinefunctions and prefetch, app CSS (--ion-*-color-step-N, :root.dark), push notifications, and errors such as "Scalar type expected, array or object received", "Access control exception", "serverconnectionajax" or a plugin that silently does nothing in the app. Skip when the plugin has no app UI and only needs web services (moodle-web-services).
---

# Moodle App Integration (site plugins)

## Overview

The Moodle app (Ionic and Angular) has no plugin code of its own for third-party plugins. It asks the site which
plugins support it, then asks each plugin's PHP for Angular templates, data and JavaScript, and compiles them at run
time. A plugin adds app support with PHP and templates only; no app build is involved. This skill gives the request
flow, a recipe that works, and the failures that show up only inside the app.

Evidence tags: **read** means read in the Moodle 5.2 or 5.3.0 source, the Moodle app 5.3.0 source or the app
developer docs, not run; **seen** means observed in a running app against a site.

## When to Use

- Writing `db/mobile.php` or `classes/output/mobile.php`, or templates under `templates/mobileapp/`
- An activity, block, course tab, main-menu page, question type or profile field must work in the app
- Calling web services from an app template, or making a view available offline
- The plugin works in the browser but shows nothing, an error, or stale content in the app
- **Skip when:** declaring the web service functions themselves (`moodle-web-services`); checking client-supplied
  arguments for SQL and access bugs before a release (`moodle-release-preflight`); styling the web site
  (`moodle-theme-scss`).

## How a request flows

1. On login the app calls `tool_mobile_get_plugins_supporting_mobile`. Core `require`s every plugin's
   `db/mobile.php`, reads `$addons`, and returns each handler JSON-encoded together with the `lang` strings in every
   installed language (`public/admin/tool/mobile/classes/api.php:160-230`, read 5.3.0). The result is cached in the
   `tool_mobile/plugininfo` MUC cache: after editing `db/mobile.php`, purge caches and log in again in the app.
2. When the user opens a handler, the app calls `tool_mobile_get_content(component, method, args)`. Core calls
   `\<component>\output\mobile::<method>(array $args)` directly (`external::get_content()` in
   `public/admin/tool/mobile/classes/external.php`, read 5.2 and 5.3). The method is not a web service: do not declare it in `db/services.php`.
3. The method returns `templates`, `javascript`, `otherdata`, `files`, and for `init` methods `restrict` and
   `disabled`. The app renders the first template, runs the JavaScript in the component's scope, and exposes
   `otherdata` as `CONTENT_OTHERDATA` (`INIT_OTHERDATA` for `init`).
4. Buttons in the template call your real web services (declared with `MOODLE_OFFICIAL_MOBILE_SERVICE` in
   `services`) through directives such as `core-site-plugins-call-ws`, or open more content with
   `core-site-plugins-new-content`.

`tool_mobile_get_content` validates nothing about your arguments and checks no capability: the method is a page
script and does what `view.php` does (`require_login`, `require_capability`). Every value in `$args` comes from the
client as a string.

## Default recipe: an activity view

```php
// db/mobile.php (GPL header)
defined('MOODLE_INTERNAL') || die();

$addons = [
    'mod_example' => [
        'handlers' => [
            'view' => [
                'delegate' => 'CoreCourseModuleDelegate',
                'method' => 'mobile_course_view',
                'displaydata' => [
                    'icon' => $CFG->wwwroot . '/mod/example/pix/monologo.svg',
                    'class' => '',
                ],
                'offlinefunctions' => [
                    'mobile_course_view' => [],
                ],
                'styles' => [
                    'url' => $CFG->wwwroot . '/mod/example/mobileapp/styles.css',
                    'version' => '1',
                ],
            ],
        ],
        'lang' => [
            ['pluginname', 'mod_example'],
            ['markdone', 'mod_example'],
            ['done', 'mod_example'],
        ],
    ],
];
```

```php
// classes/output/mobile.php (GPL header)
namespace mod_example\output;

use context_module;

/**
 * App content for mod_example.
 *
 * @package    mod_example
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class mobile {
    /**
     * The activity page in the app.
     *
     * @param array $args cmid, courseid, userid and app details, all sent by the app as strings
     * @return array
     */
    public static function mobile_course_view(array $args): array {
        global $DB, $OUTPUT, $USER;

        $cmid = clean_param($args['cmid'], PARAM_INT);
        $cm = get_coursemodule_from_id('example', $cmid, 0, false, MUST_EXIST);
        require_login($cm->course, false, $cm, true, true);
        $context = context_module::instance($cm->id);
        require_capability('mod/example:view', $context);

        $instance = $DB->get_record('example', ['id' => $cm->instance], '*', MUST_EXIST);
        $items = array_values($DB->get_records('example_items', ['exampleid' => $instance->id], 'sortorder', 'id, name'));
        foreach ($items as $item) {
            $item->name = format_string($item->name, true, ['context' => $context]);
        }

        return [
            'templates' => [[
                'id' => 'main',
                'html' => $OUTPUT->render_from_template('mod_example/mobileapp/view', [
                    'cmid' => $cm->id,
                    'name' => format_string($instance->name, true, ['context' => $context]),
                ]),
            ]],
            'javascript' => '',
            'otherdata' => [
                'items' => json_encode($items),
                'userid' => $USER->id,
            ],
            'files' => [],
        ];
    }
}
```

```handlebars
{{! templates/mobileapp/view.mustache: Mustache runs on the server with <% %>, Angular in the app with {{ }}. }}
{{=<% %>=}}
<ion-list>
    <ion-list-header><h2><% name %></h2></ion-list-header>
    <ion-item *ngFor="let item of CONTENT_OTHERDATA.items">
        <ion-label>{{ item.name }}</ion-label>
        <ion-button slot="end" core-site-plugins-call-ws name="mod_example_mark_done"
                [params]="{cmid: <% cmid %>, itemid: item.id}" [preSets]="{getFromCache: 0, saveToCache: 0}"
                successMessage="{{ 'plugin.mod_example.done' | translate }}" refreshOnSuccess="true">
            {{ 'plugin.mod_example.markdone' | translate }}
        </ion-button>
    </ion-item>
</ion-list>
```

Why each piece is there: the method checks access like a page; `json_encode` because each `otherdata` value must
be a scalar (an array fails the whole call with "Scalar type expected, array or object received"), and the app
parses any value starting with `{` or `[` back into an object before your JavaScript runs
(`src/core/features/siteplugins/services/siteplugins.ts:232`, app 5.3.0); `{{=<% %>=}}` stops server Mustache from
eating Angular's `{{ }}`; `getFromCache: 0` stops a write call from being answered from the app's cache; strings are
listed in `lang` and used as `plugin.<component>.<id>`. `mod_example_mark_done` is an ordinary external function
with `'services' => [MOODLE_OFFICIAL_MOBILE_SERVICE]` that checks access itself (`moodle-web-services`).

Handlers for other plugin types (main menu, course option, block, user profile, question type, format, settings)
differ only in the delegate and its options: [reference/handlers.md](reference/handlers.md).

## Traps that only show in the app

**The app's content cache repeats the first answer.** Content is fetched with a cached read keyed on component,
method and args. A "next item" flow that calls `this.updateContent(args)` works once and then shows the same item.
Pass presets that bypass the cache, or invalidate first, and walk every loop to its end in testing, since the first
iteration is the cold-cache case:

```javascript
this.updateContent({cmid: this.cmid, page: next}, undefined, undefined, undefined,
    {getFromCache: false, saveToCache: false, emergencyCache: false});
```

**Parsing `otherdata` again throws.** `JSON.parse(this.CONTENT_OTHERDATA.items)` on a value the app has already
parsed throws; inside a `try` the view just stays empty with nothing in the console.

**Handler JavaScript gets `this.componentContainer`, not an `ElementRef`.** Looking for your form with
`document.querySelector('form')` finds the first form in the whole app; scope DOM lookups to
`this.componentContainer` (`src/core/features/compile/components/compile-html/compile-html.ts:263-264`, app 5.3.0).

**Assignments after an `await` do not re-render.** They run outside the change detection the tap started. Call
`this.ChangeDetectorRef.detectChanges()` after updating properties in an async handler.

**`core-question` reads its question once.** Giving it a new question object does nothing; hide it with `*ngIf`,
let it be destroyed, and show it again on the next tick.

**JavaScript can run before the template is in the DOM** (API reference, Content responses): put DOM work in a
`setTimeout`, or better, drive everything from Angular bindings.

**Handler CSS applies to the whole app.** Scope every rule under your own class. The app has no
`--ion-color-step-*` variables: use `--ion-text-color-step-N` and `--ion-background-color-step-N`
(`src/theme/theme.light.scss`, app 5.3.0), and scope dark rules to `:root.dark`, the class the app toggles. Bump
`styles.version` on every change or devices keep the old file. An undefined `var(--x, fallback)` silently uses the
fallback, so check each name exists.

**Static templates are fetched once at login.** Question types, profile fields and other delegates marked "static"
in the API reference get no context in `$args` and are cached on the device until the next login.

**Offline covers reading only.** `offlinefunctions` (course-module handlers) and the `files` list make a view and
its files available after prefetch. A write made offline is not queued for you: the call fails, and the directive
shows the error. Design writes to fail visibly offline, or implement your own sync in handler JavaScript.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Declaring `mobile_course_view` in `db/services.php` | An external function that is not one (no `_parameters()`/`_returns()`), which the app never calls | The method is called by `tool_mobile_get_content`; declare only real web services |
| Class not at `\<component>\output\mobile` | `coding_exception`: "Missing method in ..." | `classes/output/mobile.php`, namespace `<component>\output` |
| No `require_login()` / capability check in the method | Any app user can read the content | Check access as `view.php` does |
| An array in `otherdata` | "Scalar type expected, array or object received"; the page fails | `json_encode()` the value |
| `JSON.parse()` of `otherdata` in JavaScript | Exception; empty view, nothing logged | Use the value as is |
| Server Mustache without `{{=<% %>=}}` | Angular expressions vanish on the server | Switch delimiters at the top of the template |
| String used in a template but not listed in `lang` | Raw `plugin.mod_example.x` shown | Add `[id, component]` to `lang`, purge, log in again |
| Write call without `getFromCache: 0` | Second tap returns the first response | Presets on writes; presets on `updateContent()` |
| Web service without `MOODLE_OFFICIAL_MOBILE_SERVICE` | "Access control exception" from the app | Add the service, upgrade |
| `offlinefunctions` on a main-menu or block handler | Ignored | Only `CoreCourseModuleDelegate` takes it; use a prefetch handler otherwise |
| Editing `db/mobile.php` and reloading the app | No change | Purge caches, then log out and in (handlers are cached in `tool_mobile/plugininfo`) |
| Styles changed, `version` not | Old CSS on devices | Bump `styles.version` |
| `--ion-color-step-*` or `prefers-color-scheme` in app CSS | Fallback colours; wrong in dark mode | `--ion-text-color-step-N`, `:root.dark` |
| `this.CoreDomUtilsProvider.showToast()` copied from an old example | Deprecated since app 4.5 (the whole class since 5.0); still present in app 5.3.0, will stop working when it is removed | `this.CoreToastsService.show({message, translateMessage: true})`, or `successMessage` on the directive |
| Testing only in PHPUnit | Green tests, broken app (the web service permission layer is never entered) | Call `tool_mobile_get_content` over REST: [reference/testing-and-debugging.md](reference/testing-and-debugging.md) |

## Reference files

| File | Read it when |
|---|---|
| [reference/handlers.md](reference/handlers.md) | Choosing a delegate for a plugin type other than an activity, or setting handler options (`displaydata`, `priority`, `restrict*`, `init`, `coursepagemethod`, `updatesnames`, `supportedfeatures`) |
| [reference/templates-and-javascript.md](reference/templates-and-javascript.md) | Writing template markup beyond the recipe: site-plugin directives, Moodle components (`core-format-text`, `core-file`, `core-rich-text-editor`), `ion-icon` names, forms, handler JavaScript scope, `init` methods and JavaScript overrides, lifecycle hooks |
| [reference/testing-and-debugging.md](reference/testing-and-debugging.md) | The plugin does nothing or errors in the app, you need the site settings the app requires, you want to call `tool_mobile_get_content` with curl, run the app in a browser, or send push notifications |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

App versions move separately from Moodle LMS. The app documentation marks app-version requirements (for example
`displayinusermenu` needs app 5.1, `CoreEnrolDelegate` app 4.3); check the app version your users run as well as the
site version.

## References

- Plugins development guide: https://moodledev.io/general/app/development/plugins-development-guide
- API reference (handlers, directives, components): https://moodledev.io/general/app/development/plugins-development-guide/api-reference
- Troubleshooting: https://moodledev.io/general/app/development/plugins-development-guide/troubleshooting
- Examples (course modules, forms, question types, prefetch): https://moodledev.io/general/app/development/plugins-development-guide/examples
- Running the app in a browser: https://moodledev.io/general/app/development/setup/app-in-browser
- App source: https://github.com/moodlehq/moodleapp
- Related skills: `moodle-web-services`, `moodle-release-preflight`, `moodle-accessibility`
