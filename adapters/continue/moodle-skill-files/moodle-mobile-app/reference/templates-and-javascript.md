# App templates, directives and handler JavaScript

Read this when writing template markup beyond the recipe in SKILL.md: site-plugin directives, Moodle components,
`ion-icon` names, forms, the JavaScript scope of a handler, `init` methods and JavaScript overrides, lifecycle hooks.
Sources: the app's API reference and examples (moodledev.io, plugins development guide) and the Moodle app 5.3.0
source; nothing was run.

## Two template languages in one file

Templates under `templates/mobileapp/` are rendered by Moodle's Mustache on the server, then compiled by Angular in
the app. Put `{{=<% %>=}}` on the first line so that `<% name %>` is server data and `{{ ... }}` reaches Angular.
Server values go into Angular expressions as literals: quote strings (`title="<% name %>"`,
`[args]="{cmid: <% cmid %>}"`). Text that may contain quotes or HTML is safer in `otherdata`, read as
`CONTENT_OTHERDATA.x`.

Keep them in `templates/mobileapp/`: the guide reserves that folder (and `js/mobileapp/` for JavaScript) and says
linting of app templates is disabled because Angular and Ionic syntax would only produce warnings (moodledev.io,
Files location). If CI's Mustache HTML validation still flags them, list them in `.mustachelintignore`, which
silences that validation only.

## Values available in templates and JavaScript

| Name | What |
|---|---|
| `CONTENT_OTHERDATA` | `otherdata` of the method response, two-way bindable (`[(ngModel)]="CONTENT_OTHERDATA.name"`) |
| `CONTENT_TEMPLATES` | All templates of the response, by id |
| `INIT_OTHERDATA`, `INIT_TEMPLATES` | The same for the handler's `init` response |
| `openContent(title, args, component?, method?, jsData?, preSets?, ptrEnabled?)` | Open a new page with another method |
| `refreshContent(showSpinner = true)` | Re-request the current content |
| `updateContent(args?, component?, method?, jsData?, preSets?)` | Replace the current page's content (cached read: see SKILL.md) |
| `updateModuleCourseContent(cmId, alreadyFetched?)` | Refresh a module's `coursepagemethod` HTML |
| `updateCachedContent()` | Refresh cached content without re-rendering (app 4.4+) |

## Directives

| Directive | Use | Key attributes |
|---|---|---|
| `core-site-plugins-new-content` | Open another method's content, in a new page or `samePage` | `component`, `method`, `args`, `title`, `useOtherData`, `form`, `jsData`, `preSets` |
| `core-site-plugins-call-ws` | Call a web service on click; optionally confirm, show a message, refresh or go back | `name`, `params`, `preSets`, `useOtherDataForWS`, `form`, `confirmMessage`, `successMessage`, `refreshOnSuccess`, `goBackOnSuccess`, `(onSuccess)`, `(onError)`, `(onDone)` |
| `core-site-plugins-call-ws-new-content` | Call a web service, then open content with its result | The two lists above, plus `newContentPreSets` |
| `core-site-plugins-call-ws-on-load` | Call a web service when the template loads (logging a view) | `name`, `params`, `preSets`, `(onSuccess)` |
| `core-link`, `core-external-content`, `core-user-link`, `core-download-file`, `core-course-download-module-main-file` | Links and files handled the app's way | see the API reference |

- `useOtherData` / `useOtherDataForWS` with an array sends only those keys; with any other value (even `false`) the
  whole `otherdata`; omitted, none. Nested values are sent as JSON strings.
- A web service that returns a boolean needs `[preSets]="{typeExpected: 'boolean'}"`; one that returns `null`
  needs `{responseExpected: false}`; otherwise the app reports "Invalid response received" (troubleshooting page).
- `form="<id or name>"` reads the fields of that `<form>` from `document.forms` and adds them to the request.
- `core-rich-text-editor` does not work with `[(ngModel)]`: give it a `FormControl`
  (`this.nameControl = this.FormBuilder.control(...)`) and send `nameControl.value`, or put it inside a `<form>`
  with a `name`.

## Components

- `<core-format-text text="<% intro %>" component="mod_example" componentId="<% cmid %>">` renders Moodle HTML,
  with links, images and media handled the app's way; with `contextLevel` and `contextInstanceId` it also asks for
  filters. Use it for `format_text()` / `external_format_text()` output; plain `{{ }}` interpolation escapes HTML.
- `<core-file [file]="file" [component]="'mod_example'" [componentId]="cmid">` shows a downloadable file.
- `<ion-icon name="...">`: `fas-` or `fa-` (Font Awesome 6.3 solid), `far-` (regular), `fab-` (a few brands),
  `moodle-` (icons imported from LMS), `fam-` (app-only icons), otherwise Ionicons. Prefer Font Awesome names, which
  match the web site. An icon-only button needs an `aria-label` (`moodle-accessibility`).
- `<core-iframe src="..." [addSiteReferer]="true">` embeds content that requires the site as referer (LMS 5.2+ and
  app 5.2+; troubleshooting page). Inside `core-format-text`, mark such an iframe with `data-app-site-referer="true"`.

## Handler JavaScript

The `javascript` string of a response runs with `this` bound to the page's component. The app injects its
services as properties named after their classes, with `DelegateService` shortened to `Delegate`
(`src/core/features/compile/services/compile.ts`, `injectLibraries()`, app 5.3.0), for example:

| Property | Use |
|---|---|
| `this.CoreSitesProvider` | `getCurrentSite()`: `.read(ws, params, preSets)`, `.write(ws, params, preSets)`, `.getUserId()` |
| `this.CoreToastsService` | `show({message, translateMessage: true, duration: 'short'})` |
| `this.CoreContentLinksDelegate`, `this.CoreCourseModulePrefetchDelegate` | `registerHandler(...)` from `init` code |
| `this.FormBuilder`, `this.Validators` | Angular reactive forms |
| `this.ChangeDetectorRef` | `detectChanges()` after asynchronous updates |
| `this.componentContainer` | The component's root element: scope DOM queries to it |
| `this.CoreUtils`, `this.CoreText`, `this.CoreDom`, `this.CoreTime`, `this.CoreUrl` | Utility singletons |

`site.read()` defaults to `getFromCache: true, saveToCache: true`; `site.write()` defaults both to `false`
(`src/core/classes/sites/authenticated-site.ts:340-390`). Many `*Provider` names from older guides
(`CoreDomUtilsProvider`, `CoreUtilsProvider.isWebServiceError()`) are deprecated since app 5.0; check the method
still exists in the app source before copying an old example.

```javascript
// mobileapp/view.js, returned as the response's 'javascript'.
const that = this;

this.markAll = async() => {
    const site = that.CoreSitesProvider.getCurrentSite();
    try {
        await site.write('mod_example_mark_all', {cmid: that.CONTENT_OTHERDATA.cmid});
        await that.CoreToastsService.show({message: 'plugin.mod_example.done', translateMessage: true});
        that.refreshContent(false);
    } catch (error) {
        that.CoreToastsService.show({message: error.message || String(error)});
    } finally {
        that.ChangeDetectorRef.detectChanges();
    }
};
```

## Lifecycle and navigation hooks

Assign Ionic lifecycle hooks on `this` (`this.ionViewWillLeave = function() {...}`); `this.canLeave` returning
`false` (or a promise of it) blocks navigation away, for unsaved forms.

## JavaScript overrides (static handlers)

For question types, profile fields, quiz access rules and assignment sub-plugins, the last expression of the `init`
JavaScript is an object whose functions override the handler's defaults, and `componentInit` runs in the Angular
component's scope:

```javascript
var that = this;
var result = {
    componentInit: function() {
        // 'this' is the component; that.FormBuilder etc. are the injected services.
    },
};
result;
```

The interfaces to implement are linked from each delegate's entry in the API reference (for example
`CoreQuestionHandler` in `src/core/features/question/services/question-delegate.ts`).
