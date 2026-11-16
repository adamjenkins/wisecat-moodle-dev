# Core AMD modules: exact APIs and promise types

Read this when you need the exact API of a core module, or whether it returns a jQuery promise or a native one.
Everything here was read in the 5.3.0 source and checked to exist in 5.2 unless tagged; nothing was run.

## Promise type decides what you can chain

| Call | Returns | `finally`? | Safe form |
|---|---|---|---|
| `Ajax.call([...])` | Array of jQuery promises | No | `Promise.resolve(Ajax.call([...])[0])` |
| `get_string()`, `get_strings()` (`core/str`) | jQuery promise | No | Use `getString()` / `getStrings()` |
| `getString()`, `getStrings()` | Native promise | Yes | As is |
| `Templates.render()` | jQuery promise (`html, js` as two arguments) | No | `renderForPromise()` |
| `Templates.renderForPromise()` | Native promise of `{html, js}` | Yes | As is |
| `Fragment.loadFragment()` | jQuery promise (`html, js` as two arguments) | No | `.done((html, js) => ...)` |
| `Modal.create()` and subclasses | Native promise of the modal | Yes | As is |
| `modal.show()` | jQuery promise | No | Do not chain `finally` |
| `Notification.saveCancelPromise()` | Native promise: resolves on save, rejects on hide | Yes | `.catch(() => {})` for cancel |

`await` works on both kinds, because a jQuery promise is a thenable. The difference only bites when you chain.

## core/ajax

```javascript
import Ajax from 'core/ajax';

const [course, users] = await Promise.all(Ajax.call([
    {methodname: 'local_example_get_course', args: {courseid: 5}},
    {methodname: 'local_example_get_users', args: {courseid: 5}},
]));
```

- Signature: `call(requests, async, loginrequired, nosessionupdate, timeout, cachekey)`
  (`public/lib/amd/src/ajax.js:48`). `async = false` is deprecated and warns. `loginrequired = false` uses the
  no-login endpoint and needs `'loginrequired' => false` on the function in `db/services.php`.
- Several requests in one call go in one HTTP request and run in order on the server; one failing request rejects
  its own promise only.
- Each method must be declared with `'ajax' => true`. The sesskey is added by the module.
- An exception from the server rejects with an object that has `errorcode`, `message`, `debuginfo`;
  `Notification.exception(error)` shows it.

## core/str

```javascript
import {getString, getStrings} from 'core/str';

const label = await getString('itemcount', 'local_example', {count: 3});
const [title, body] = await getStrings([
    {key: 'confirm', component: 'core'},
    {key: 'confirmdelete', component: 'local_example', param: name},
]);
```

- Strings are cached in the browser per `jsrev`; strings needed on page load can be preloaded from PHP with
  `$PAGE->requires->strings_for_js(['key'], 'local_example')` and read with `M.str.local_example.key`.
- The `{$a}` placeholder shape (`{$a}` or `{$a->count}`) is chosen by the argument you pass; nothing checks they
  agree. Lang string rules live in `moodle-plugin-development`.

## core/templates

| Method | Use |
|---|---|
| `renderForPromise(name, context)` | Render; resolves `{html, js}` |
| `replaceNode(node, html, js)` | Replace the node itself and run the template JS |
| `replaceNodeContents(node, html, js)` | Replace the children |
| `appendNodeContents(node, html, js)` / `prependNodeContents(...)` | Add children |
| `runTemplateJS(js)` | Run the JS when you insert the HTML yourself |
| `renderPix(key, component, title)` | Render one icon |

- A template's `{{#js}}` block is not run by `render()` alone; pass `js` to one of the DOM methods or to
  `runTemplateJS()`.
- The renderer adds its own helpers to the context (`uniqid`, `str`, `cleanstr`, `pix`, `quote`, `js`, ...) and
  overwrites a context key of the same name (`public/lib/amd/src/local/templates/renderer.js:516-526`).
- `{{#str}}` keys are fetched in one request per render; a missing key renders `[[key]]`. Assert in a test that the
  rendered HTML has no `[[`.
- Template names load through `core/templates` from the current theme first, so a theme override applies to JS
  renders too.

## core/notification and core/toast

```javascript
import Notification from 'core/notification';
import {add as addToast} from 'core/toast';

Notification.addNotification({message: await getString('saved', 'local_example'), type: 'success'});
addToast(await getString('saved', 'local_example'), {type: 'success', delay: 4000});
Notification.saveCancelPromise(
    getString('confirm', 'core'),
    getString('confirmdelete', 'local_example'),
    getString('delete', 'core'),
    {triggerElement: button},
).then(() => remove()).catch(() => null);
```

- `addToast(message, {type, delay, autohide, closeButton})`; defaults `info`, 4000 ms, autohide on
  (`public/lib/amd/src/toast.js:83-100`). The toast region is `role="status" aria-live="polite"`.
- `Notification.confirm()` is a wrapper around `saveCancel()`; use `saveCancelPromise()` or `deleteCancelPromise()`.
- Messages, titles and button labels are inserted as HTML: lang strings only.

## core/pending

```javascript
import Pending from 'core/pending';

const pending = new Pending('local_example/thing:load');
try {
    await work();
} finally {
    pending.resolve();
}
```

Behat's "I wait until the page is ready" waits until every pending key resolves. Use one key per operation and
resolve it on every path, including errors. `Pending.request()` no longer exists on either version (removed in 5.2,
listed under "5.2" in `public/lib/UPGRADING.md`). **5.3+:** the module is `public/lib/js/esm/src/pending.ts`, served
to AMD through the RequireJS map, with the same API.

## core/fragment

```javascript
import Fragment from 'core/fragment';
import Notification from 'core/notification';
import Templates from 'core/templates';

Fragment.loadFragment('local_example', 'details', contextid, {id: 4})
    .done((html, js) => Templates.replaceNodeContents(node, html, js))
    .fail(Notification.exception);
```

The jQuery promise resolves with two arguments, `html` and `js` (`public/lib/amd/src/fragment.js:108-115`).
`await` or `Promise.resolve()` keeps only the first, so the fragment's JavaScript is lost; use `.done()`. The PHP
side is `function local_example_output_fragment_details(array $args): string` in `lib.php`; it receives
`$args['context']`, must check capabilities itself, and must not call `require_login()` (see SKILL.md).

## core/url, core/config, core/log

- `import Url from 'core/url'`: `Url.relativeUrl('/local/example/view.php', {id: 3})`,
  `Url.fileUrl('/pluginfile.php', '/1/local_example/area/0/a.png')`, `Url.imageUrl('i/info', 'core')`.
  `relativeUrl()` throws "relativeUrl function does not accept absolute urls" for anything starting with
  `http:`/`https:` or containing `://` (5.2: `public/lib/amd/src/url.js:64`; 5.3: `public/lib/js/esm/src/url.ts:77`).
- `import Config from 'core/config'`: `Config.wwwroot`, `Config.sesskey`, `Config.jsrev`, `Config.contextid`;
  prefer it to reading `M.cfg` directly.
- `import Log from 'core/log'`: `Log.debug()` / `Log.info()`; core sets the level to `warn`, or `trace` when
  `$CFG->debugdeveloper` is on (`page_requirements_manager.php`, read 5.3.0).

## Browser storage

`core/localstorage` and `core/sessionstorage` expose `get(key)`, `set(key, value)`, `clean()`. Keys are prefixed per
site, but the clear on login change and on `jsrev` change calls the browser's `Storage.clear()` and wipes the whole
origin (5.2: `public/lib/amd/src/storagewrapper.js:86-101` and `storage_validation.js`; 5.3:
`public/lib/js/esm/src/Storage.ts:98-120`). With JavaScript caching off (`jsrev = -1`) the wrappers do nothing.
Use them only as a cache that can be rebuilt.

## core/local/aria/focuslock

```javascript
import {trapFocus, untrapFocus} from 'core/local/aria/focuslock';

trapFocus(dialogElement);   // focuses the first focusable descendant
// ... later
untrapFocus();              // releases the most recent region; returns nothing
opener.focus();
```

`trapFocus()` returns nothing; regions stack, so nested dialogs work if every trap has its `untrapFocus()`
(`public/lib/amd/src/local/aria/focuslock.js:328,363`, read 5.2 and 5.3). `core/modal` already does this; use it
directly only for your own overlay. Accessibility rules for overlays are in `moodle-accessibility`.

## Events between modules

- Native events: `import {dispatchEvent} from 'core/event_dispatcher'`; `dispatchEvent('local_example/saved',
  {id}, element)` creates a bubbling `CustomEvent` with `detail`. Listen on `document` with
  `addEventListener('local_example/saved', ...)`.
- Form events: `core_form/events` exports `eventTypes` and `notifyFormSubmittedByJavascript(form, skipValidation)`.
- Modal events: `core/modal_events` has `shown`, `hidden`, `destroyed`, `bodyRendered`, `outsideClick`, `save`,
  `delete`, `cancel` (jQuery events on `modal.getRoot()`); `core/modal:shown` and `core/modal:bodyRendered` are also
  dispatched as native events on the modal element.
