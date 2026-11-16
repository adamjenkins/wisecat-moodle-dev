# Modals, modal and dynamic forms, TinyMCE plugins, autocomplete handlers

Read this when writing a modal subclass, a form shown in a modal, a TinyMCE (`editor_tiny`) plugin, or a
`core/form-autocomplete` AJAX handler. Everything here was read in the 5.3.0 source and checked to exist in 5.2
unless tagged; nothing was run.

## Modal lifecycle in one table

| Call | What it does | Source (`public/lib/amd/src/modal.js`) |
|---|---|---|
| `await Sub.create(config)` | Renders `Sub.TEMPLATE` (or `config.template`), constructs, then `configure(config)` | `create()`, line 229 |
| `configure({show, large, isVerticallyCentered, removeOnClose, scrollable, returnElement, title, body, footer, buttons})` | Defaults: `show = false`, `removeOnClose = false`, `scrollable = true` | line 277 |
| `show()` | Attaches to the DOM, traps focus (`FocusLock.trapFocus`), returns a jQuery promise | `attachToDOM()` |
| `hide()` | Releases the focus trap, hides, triggers `ModalEvents.hidden` | line 963 |
| `destroy()` | `hide()`, then `this.root.remove()`, then triggers `ModalEvents.destroyed` on the removed root | lines 1008-1013 |

So a handler for `ModalEvents.destroyed` bound with `modal.getRoot().on(...)` never runs: jQuery's `remove()` unbinds
it first. Teardown that must run on every close path goes on `ModalEvents.hidden`, or checks
`modal.getRoot()[0].isConnected` where the code later needs to know the modal has gone. Cancel, Escape, the close
button and a backdrop click never run a save handler.

`title`, `body` and `footer` accept a string or a promise (`getString()`, `Templates.render()`); the modal shows a
loading icon until the promise resolves. They are inserted as HTML.

## A modal subclass

```javascript
// amd/src/modal_pick.js (GPL header)
/**
 * A modal with its own template and a "Pick" action.
 *
 * @module     local_example/modal_pick
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
import Modal from 'core/modal';

export default class ModalPick extends Modal {
    static TYPE = 'local_example/modal_pick';
    static TEMPLATE = 'local_example/modal_pick';

    registerEventListeners() {
        super.registerEventListeners();
        this.registerCloseOnCancel();
        this.getModal().on('click', '[data-action="pick"]', (e) => {
            e.preventDefault();
            this.getRoot().trigger('local_example:picked', [e.currentTarget.dataset.id]);
            this.destroy();
        });
    }
}

ModalPick.registerModalType();
```

- `static TYPE` and `static TEMPLATE` are all `create()` needs. `registerModalType()` only feeds the legacy registry
  (`modal.js:171-189` says it is not needed for code that runs only on 4.3 and later); it is harmless and core still
  calls it, so keep it if anything might look the type up.
- The template extends `core/modal` and fills its blocks:

```mustache
{{< core/modal }}
    {{$title}}{{#str}}pick, local_example{{/str}}{{/title}}
    {{$body}}<ul class="list-unstyled">{{#items}}<li><button type="button" class="btn btn-link" data-action="pick" data-id="{{id}}">{{name}}</button></li>{{/items}}</ul>{{/body}}
    {{$footer}}<button type="button" class="btn btn-secondary" data-action="cancel">{{#str}}cancel, core{{/str}}</button>{{/footer}}
{{/ core/modal }}
```

- `registerCloseOnSave()`, `registerCloseOnCancel()`, `registerCloseOnDelete()` exist on the base class; the
  footer buttons must carry `data-action="save"` / `"cancel"` / `"delete"` (`getActionSelector()`).
- `core/modal_save_cancel` refuses `setFooter()` and expects both buttons in its template; change labels with
  `setSaveButtonText()` or `configure({buttons: {save: getString('add', 'core')}})`.
- Template authoring rules (example context, `{{! }}` comments, partials) belong to
  `moodle-theme-layouts-templates`; heading levels and labelling of the dialog belong to `moodle-accessibility`.

## A form in a modal: `core_form/modalform` and `\core_form\dynamic_form`

```javascript
import ModalForm from 'core_form/modalform';
import {getString} from 'core/str';

const form = new ModalForm({
    formClass: 'local_example\\form\\edit_item',
    args: {id: Number(button.dataset.id)},
    modalConfig: {title: getString('edititem', 'local_example')},
    returnFocus: button,
});
form.addEventListener(form.events.FORM_SUBMITTED, (e) => {
    // e.detail is what process_dynamic_submission() returned.
    window.location.reload();
});
form.show();
```

```php
namespace local_example\form;

use context;
use context_system;
use moodle_url;

class edit_item extends \core_form\dynamic_form {
    protected function get_context_for_dynamic_submission(): context {
        return context_system::instance();
    }

    protected function check_access_for_dynamic_submission(): void {
        require_capability('local/example:manage', $this->get_context_for_dynamic_submission());
    }

    public function set_data_for_dynamic_submission(): void {
        global $DB;
        $id = $this->optional_param('id', 0, PARAM_INT);
        $this->set_data($DB->get_record('local_example_items', ['id' => $id], 'id, name', MUST_EXIST));
    }

    public function process_dynamic_submission() {
        global $DB;
        $data = $this->get_data();
        $DB->set_field('local_example_items', 'name', $data->name, ['id' => $data->id]);
        return ['id' => $data->id];
    }

    protected function get_page_url_for_dynamic_submission(): moodle_url {
        return new moodle_url('/local/example/index.php');
    }

    protected function definition(): void {
        $mform = $this->_form;
        $mform->addElement('hidden', 'id');
        $mform->setType('id', PARAM_INT);
        $mform->addElement('text', 'name', get_string('name'));
        $mform->setType('name', PARAM_TEXT);
        $mform->addRule('name', null, 'required', null, 'client');
    }
}
```

- The five abstract methods are in `public/lib/form/classes/dynamic_form.php:90-148`. The form is rendered and
  submitted through the `core_form_dynamic_form` web service, so `check_access_for_dynamic_submission()` is the only
  access check: re-check the record belongs to the context (a client-sent `id` is not trusted;
  `moodle-release-preflight`).
- The form class is loaded by the web service, not by a page script, so any library it needs that is not autoloaded
  must be `require_once`d at the top of the class file, and any AMD it needs is requested from code that runs when
  the form renders (a `render()` override), not from `definition()`, which also runs on submission.
- `config.moduleName` selects another modal class than `core/modal_save_cancel`; `saveButtonText` relabels Save.
- A throwaway page form that contains a file picker element can break a later modal form's file picker: the picker's
  templates are printed once per request (`moodle-field-lessons`).

## TinyMCE (editor_tiny) plugin layout

Files of `public/lib/editor/tiny/plugins/h5p` (5.3.0), the smallest core plugin with a button and a menu item:

| File | Job |
|---|---|
| `classes/plugininfo.php` | `extends \editor_tiny\plugin implements plugin_with_buttons, plugin_with_menuitems`; `get_available_buttons()` returns `['tiny_example/example']`; add `plugin_with_configuration` to pass per-context data such as capabilities |
| `amd/src/common.js` | The names used by the other files: `component` (`'tiny_example'`), `pluginName` (`'tiny_example/plugin'`), the button name and the icon name |
| `amd/src/plugin.js` | Default export is a promise that calls `tinyMCE.PluginManager.add(`${component}/plugin`, setup)` and resolves `[`${component}/plugin`, Configuration]` |
| `amd/src/commands.js` | `getSetup()` resolves a function that calls `editor.ui.registry.addButton()` / `addMenuItem()` |
| `amd/src/configuration.js` | `configure(instanceConfig)` returns `{toolbar: addToolbarButton(...), menu: addMenubarItem(...)}` from `editor_tiny/utils` |
| `amd/src/options.js` | Registers and reads the options passed from `get_plugin_configuration_for_context()` |

```javascript
// amd/src/configuration.js
import {component as buttonName} from './common';
import {addMenubarItem, addToolbarButton} from 'editor_tiny/utils';

export const configure = (instanceConfig) => ({
    toolbar: addToolbarButton(instanceConfig.toolbar, 'content', buttonName),
    menu: addMenubarItem(instanceConfig.menu, 'insert', buttonName),
});
```

- Without `configuration.js` (or with a `configure()` that returns nothing) the button is registered but never placed:
  the plugin loads, no error is logged, and the toolbar has no button.
- `PluginManager.add()` does not accept a promise; everything asynchronous (strings, icons, metadata) is awaited
  before it, as `plugin.js` does with `Promise.all`.
- A no-op setup function for an option you do not use needs a body for eslint `no-empty-function`: a comment is
  enough.
- The editor saves its content into the textarea on blur and on the form's jQuery `submit`
  (`public/lib/editor/tiny/amd/src/editor.js:633-646`, 5.3.0). JavaScript that reads the form without submitting it
  calls `getInstanceForElement(textarea)?.save()` from `editor_tiny/editor` first.
- **5.3+:** the editor picks the `oxide-dark` skin when `data-bs-theme="dark"` is on the page at setup and keeps it
  until reload; its content iframe has Bootstrap's stock palette, not the `--mds-*` tokens. Styling for editor
  content is `moodle-theme-scss`.

## core/form-autocomplete with an AJAX source

```php
$mform->addElement('autocomplete', 'userids', get_string('users'), [], [
    'multiple' => true,
    'ajax' => 'local_example/form_user_selector',
    'valuehtmlcallback' => function($userid) {
        global $DB, $OUTPUT;
        $user = $DB->get_record('user', ['id' => $userid, 'deleted' => 0]);
        return $user ? fullname($user) : false;
    },
]);
```

```javascript
// amd/src/form_user_selector.js
import Ajax from 'core/ajax';

/**
 * Fetch matches.
 *
 * @param {String} selector The select element selector
 * @param {String} query What the user typed
 * @param {Function} success Receives an array of results
 * @param {Function} failure Receives the error
 */
export const transport = async(selector, query, success, failure) => {
    try {
        success(await Ajax.call([{methodname: 'local_example_search_users', args: {query}}])[0]);
    } catch (error) {
        failure(error);
    }
};

/**
 * Turn results into options.
 *
 * @param {String} selector The select element selector
 * @param {Array} results What transport() passed to success
 * @return {Array} Options as {value, label}
 */
export const processResults = (selector, results) => results.map((u) => ({value: u.id, label: u.fullname}));
```

- The handler module exports exactly `transport` and `processResults` (`public/lib/amd/src/form-autocomplete.js:713`;
  core's model is `public/user/amd/src/form_user_selector.js`). Passing a string instead of an array to `success`
  shows it as a message, which is how core reports "too many results".
- With `ajax` or `tags`, `setValue()` adds any submitted value as an option and `exportValue()` returns it unchecked
  (`public/lib/form/autocomplete.php:165-202`). Validate every id in the form's `validation()` and again in the
  web service that acts on it.
- `valuehtmlcallback` renders the labels of already selected values when the form is redisplayed; without it they
  show as bare ids. Its output is HTML: escape user data in it.
- `label` from `processResults()` is HTML too; render it from a template or escape it.
