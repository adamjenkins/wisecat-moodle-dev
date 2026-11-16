# Handlers and delegates in `db/mobile.php`

Read this when choosing a delegate for a plugin type other than an activity, or setting handler options
(`displaydata`, `priority`, `restrict*`, `init`, `coursepagemethod`, `updatesnames`, `supportedfeatures`). Source: the
app's API reference (https://moodledev.io/general/app/development/plugins-development-guide/api-reference), read
against Moodle app 5.3.0; not run.

## Shape

```php
$addons = [
    '<component>' => [              // The addon name; normally the plugin's component.
        'handlers' => [
            '<handlername>' => [     // Alphanumeric, unique within the addon.
                'delegate' => '<Delegate>',
                'method' => '<method in classes/output/mobile.php>',
                'init' => '<optional init method>',
                'displaydata' => [...],
                'styles' => ['url' => '...', 'version' => '1'],
                // Delegate-specific options below.
            ],
        ],
        'lang' => [['<stringid>', '<component>'], ['cancel', 'moodle']],
        'dependencies' => [],
    ],
];
```

- Strings are used as `plugin.<component>.<stringid>` whatever component they came from, so `['cancel', 'moodle']`
  is `plugin.mod_example.cancel`. Every listed string is sent in every installed language and cached on the device:
  list only what templates use.
- Options common to most handlers: `delegate`, `method`, `init`, `styles` (`url` and `version`, both required),
  `moodlecomponent` (when a local plugin adds app support for another component), `restricttocurrentuser` (default
  `false`), `restricttoenrolledcourses` (default `true`).

## Delegates

| Delegate | Plugin type / place | Template | Specific options |
|---|---|---|---|
| `CoreMainMenuDelegate` | An entry in the More menu (never a bottom tab) | Dynamic | `displaydata.title`, `displaydata.icon` (required), `priority`, `ptrenabled` |
| `CoreMainMenuHomeDelegate` | A tab on the home page next to Dashboard and Site home | Dynamic | `displaydata.title`, `priority` |
| `CoreCourseOptionsDelegate` | A course tab, or an item in the course summary (`ismenuhandler`) | Dynamic | `displaydata.title`, `priority`, `ismenuhandler` |
| `CoreCourseModuleDelegate` | An activity or resource | Dynamic | `method`, `coursepagemethod`, `displaydata.icon`, `offlinefunctions`, `downloadbutton`, `isresource`, `updatesnames`, `supportedfeatures`, `display*` menu switches |
| `CoreCourseFormatDelegate` | A course format | Dynamic | `canviewallsections`, `displaycourseindex` |
| `CoreUserDelegate` | An item on the user profile (and user menu) | Dynamic | `displaydata.title`, `displaydata.icon`, `type` (`listitem` or `button`), `displayinusermenu` (`no`, `yes`, `only`; app 5.1+) |
| `CoreSettingsDelegate` | An entry in app settings | Dynamic | `displaydata.title`, `displaydata.icon`, `priority` |
| `AddonMessageOutputDelegate` | A message output's settings in notification preferences | Dynamic | `displaydata.title`, `displaydata.icon` |
| `CoreBlockDelegate` | A block on site home, Dashboard or the course page | Dynamic | `displaydata.title`, `displaydata.class`, `displaydata.type` (`title` or `prerendered`), `fallback` |
| `CoreQuestionDelegate` | A question type | Static | JavaScript overrides of `CoreQuestionHandler` |
| `CoreQuestionBehaviourDelegate` | A question behaviour | Static | JavaScript overrides |
| `CoreUserProfileFieldDelegate` | A custom profile field | Static | JavaScript overrides, `componentInit` |
| `AddonModQuizAccessRuleDelegate` | A quiz access rule | Static | JavaScript overrides |
| `AddonModAssignSubmissionDelegate`, `AddonModAssignFeedbackDelegate` | Assignment sub-plugins | Static | JavaScript overrides |
| `CoreEnrolDelegate` | An enrolment method (app 4.3+) | None | `enrolmentAction` (`browser`, `self`, `guest`), `infoIcons` |

Registered only from `init` JavaScript (no `delegate` in `db/mobile.php`, or `'delegate' => ''`):
`CoreContentLinksDelegate` (links), `CorePushNotificationsDelegate` (taps on notifications),
`CoreCourseModulePrefetchDelegate` (custom prefetch), `CoreFileUploaderDelegate`, `CorePluginFileDelegate`,
`CoreFilterDelegate` (only for JavaScript filters: PHP filters already ran on the HTML),
`AddonWorkshopAssessmentStrategyDelegate`. Handlers registered this way ignore `restrict` and `disabled`; check
those yourself.

**Dynamic** templates are rendered per request with context in `$args` (`courseid`, `cmid`, `userid` and app details
such as `applang`). **Static** templates are fetched once after login with no context and cached on the device.

## Course modules in detail

- No `method`: the activity is not clickable. `coursepagemethod`: plain HTML (no directives) rendered on the course
  page, and the activity is not clickable either.
- `offlinefunctions` maps names to parameter lists. A PHP method name always receives `courseid`, `cmid`, `userid`;
  a web service name with `[]` receives those defaults, or the listed names (`['courseid', 'exampleid']`, where
  `<modname>id` is the instance id). Methods that need other parameters (a page number) cannot be prefetched this
  way: write a prefetch handler.
- `updatesnames` is a regular expression over the field names `core_course_check_updates` returns; only matching
  updates mark the downloaded module as outdated (`'/^grades$|^gradeitems$/'`).
- `supportedfeatures`: `[FEATURE_NO_VIEW_LINK => true, FEATURE_MOD_PURPOSE => MOD_PURPOSE_ASSESSMENT]`; only
  `FEATURE_MOD_ARCHETYPE`, `FEATURE_MOD_PURPOSE`, `FEATURE_GRADE_HAS_GRADE`, `FEATURE_SHOW_DESCRIPTION` and
  `FEATURE_NO_VIEW_LINK` are used by the app.
- `displayopeninbrowser`, `displaydescription`, `displayrefresh`, `displayprefetch`, `displaysize` switch the
  module page's menu items (also settable from JavaScript, for example `this.displayRefresh = false;`).

## `init` methods

```php
'handlers' => [
    'links' => [
        'delegate' => '',
        'init' => 'mobile_init',
    ],
],
```

```php
public static function mobile_init(array $args): array {
    global $CFG;
    return [
        'templates' => [],
        'javascript' => file_get_contents($CFG->dirroot . '/mod/example/mobileapp/init.js'),
        'restrict' => [],
        'disabled' => false,
    ];
}
```

The JavaScript runs as soon as the plugin is loaded; its last expression is evaluated as an object whose properties
become available to all of the handler's JavaScript, and, for static handlers, override handler methods. Keep app
JavaScript in a file under the plugin (`mobileapp/` or `js/mobileapp/`) rather than in a PHP string, so it can be
read and linted. Core's own example is `public/mod/subsection/db/mobile.php` with `classes/output/mobile.php`
(5.2 and 5.3).
