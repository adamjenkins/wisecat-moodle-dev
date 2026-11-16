# JavaScript, modals, TinyMCE, plugin CSS, navigation, blocks and the Moodle app

Read this when plugin JavaScript works once and then stops, a modal or TinyMCE button misbehaves, plugin CSS does
not apply or breaks on another theme, you add content to navigation, the course page or a block region, or a
Moodle app site plugin repeats stale content.

The AMD recipe is `moodle-amd-javascript`; theme-side CSS and templates are in `moodle-theme-scss` and
`moodle-theme-layouts-templates`; the app is `moodle-mobile-app`. Samples are valid on Moodle 5.2 and 5.3.

## AMD and core JS modules

- **Never chain `.finally()` onto a `core/ajax` promise.** It is a jQuery Deferred with no `finally`, so the chain
  throws while it is built; the `.then()` already ran, so the symptom is "works exactly once, then the button
  stays disabled". Wrap the promise, and `grep -rn '\.finally(' amd/src/` before shipping.

  ```javascript
  Promise.resolve(Ajax.call([{methodname: 'local_myplugin_do', args: {}}])[0])
      .then(render)
      .catch(Notification.exception)
      .finally(() => {
          button.disabled = false;
      });
  ```

- **AMD names resolve only to `amd/build/<name>.min.js`**, with no index fallback: a nested module needs its full
  path or a re-export shim. A dynamic `import()` in `amd/src` is rewritten by the build into a failing RequireJS
  call; vendor ES modules as `.js` files loaded from outside `amd/`, never `.mjs` (commonly served with a type
  browsers refuse for modules).
- **A module with `export default` loses its named exports in the AMD build**: one style per module (`moodle-amd-javascript`).
- **Never name a Mustache context variable `uniqid`**: `core/templates` overwrites it (`moodle-theme-layouts-templates`).
- **An `output_fragment_<name>` callback never calls `require_login()`**: it throws "The theme has already been set up" (`moodle-amd-javascript`).
- **Wall-clock to timestamp in JS:** re-measure the zone offset at the candidate instant; a single offset taken
  "now" is off by the DST amount near transitions.
- **Race every browser promise that can hang against a timeout**: an ES module that throws while running fires no
  `error` on its `<script>`, and media APIs such as `AudioContext.resume()` can stay pending for ever in some
  browsers.
- **Moodle 5.2 and 5.3 also have an ES module build** for `js/esm/src/*.ts|tsx` (`grunt react`); it picks up only
  `.ts` and `.tsx` sources (`moodle-amd-javascript` for that path).

## Modals and TinyMCE

- **`ModalEvents.destroyed` bound on `modal.getRoot()` never fires**: `destroy()` removes the root, which unbinds its
  handlers, before triggering the event (`public/lib/amd/src/modal.js:1011-1012`, 5.3.0). Bind elsewhere, or check
  `modal.getRoot()[0].isConnected` where you need to know. Do not tear down only in the save handler: Cancel,
  Escape and the backdrop bypass it.
- **TinyMCE buttons appear only through `configuration.js` `configure()`**; `editor.ui.registry.addButton()` alone
  only makes them referenceable. An empty stub function needs a comment body for eslint's `no-empty-function`.
- **TinyMCE copies its content into the textarea (`name[text]`) only on blur and on the form's submit event**
  (`public/lib/editor/tiny/amd/src/editor.js:633-646`, 5.3.0). JS that builds `FormData` or posts the form by
  itself while the editor has focus sends the old text; save each editor before reading the form, for example
  `getAllInstances().forEach((editor) => editor.save());` with `getAllInstances` imported from `editor_tiny/editor`
  (exported on 5.2 and 5.3).

## Plugin CSS and Bootstrap 5

- **Bootstrap 5 names on 5.2 and 5.3** (`visually-hidden`, `me-2`, `fw-bold`), including markup built in JS:
  Bootstrap 4 names (`sr-only`, `mr-2`, `font-weight-bold`) fail Behat's `--scss-deprecations` check even on core
  steps that visit the page.
- **The `hidden` attribute loses to Bootstrap display utilities** (`d-flex` and the other `d-*` classes carry
  `!important`): toggle `d-none` in JS-built markup.
- **`{{#pix}}` is icon-sized only**; never put tag syntax or `}}` inside a `{{! }}` comment or an example context,
  because the comment closes at the first `}}` and the rest prints on the page (`moodle-theme-layouts-templates`).
- **Check every CSS custom property exists** on the target theme
  (`getComputedStyle(el).getPropertyValue('--x')` returns `''` when it does not): an undefined `var(--x, fallback)`
  silently uses the fallback everywhere. Boost on 5.2 and 5.3 exposes Bootstrap's `--bs-*`; the Moodle app uses
  `--ion-text-color-step-N`/`--ion-background-color-step-N` and `:root.dark`.
- **A one-class plugin rule on an element Bootstrap styles (`.btn`) loses to the theme sheet**, which is emitted
  after plugin sheets. Set Bootstrap's own variables from a selector that outranks it:
  `.btn.local_myplugin-share { --bs-btn-bg: var(--bs-primary); }`. Check the effect in a screenshot or with
  `getComputedStyle()`: finding the rule in the served sheet proves only that it arrived.
- **Use `animation-fill-mode: backwards`**: `both` and `forwards` pin the last keyframe above the cascade, so a later
  state class cannot change the animated property.
- **Plugin `styles.css` is merged site-wide** (plugins, then parent themes, then the theme), so scope selectors to
  the plugin; a new file appears only after a cache purge. Moodle's stylelint wants one declaration per line and
  durations of at least 100 ms (`moodle-theme-testing-release`).
- **H5P content takes CSS only from the `core_h5p | h5pcustomcss` setting**: theme SCSS, additional HTML and plugin
  `styles.css` never enter the H5P iframe.

## Navigation, the course page and blocks

- **Module-page secondary navigation from a non-activity plugin:** use
  `<component>_extend_settings_navigation()` and add under
  `$nav->find('modulesettings', settings_navigation::TYPE_SETTING)` in `CONTEXT_MODULE`.
  `core\hook\navigation\secondary_extend` is dispatched only when the course secondary navigation is built
  (`public/lib/classes/navigation/views/secondary.php:439`, 5.3.0).
- **Content on course-page activity cards from a non-activity plugin** has no dedicated hook on 5.2 or 5.3: render
  it hidden on `\core\hook\output\before_footer_html_generation`, move it into `li[data-for=cmitem][data-id]` with
  an AMD module, and re-apply it from a `MutationObserver` after reactive reloads. Gate on `$PAGE->url`, not the
  page type (`course-view-<format>` is also set by other course pages); filter on `uservisible` and
  `is_visible_on_course_page()`; pick the anchor from core's template and the theme's SCSS. Course page order is
  not modinfo order: subsection content comes last.
- **A block cannot choose its default region**; the page layout and the "Add a block" control decide. Document a
  manual move instead of writing to the block tables.

## Moodle app site plugins

- **`updateContent()` is a cached read keyed on its arguments**: a "next item" handler works once, then repeats.
  Pass `getFromCache: false, saveToCache: false, emergencyCache: false`, and walk the loop to its end.
- **`otherdata` values starting with `{` or `[` arrive parsed**; call `detectChanges()` after awaits; recreate a
  `core-question` component with `*ngIf` to show new HTML.

## References

- https://moodledev.io/docs/guides/javascript
- https://moodledev.io/docs/guides/javascript/modal
- https://moodledev.io/docs/apis/plugintypes/tiny
- https://moodledev.io/docs/apis/core/navigation
