# Forms, file pickers and admin settings: the small print

Read this when writing or debugging a moodleform, a `dynamic_form`, a file or filemanager element, a form posted or
filled from code, or an admin setting whose stored or shown value is wrong.

The `settings.php` recipe for each plugin type is in `moodle-plugin-development`; this file keeps the traps.
Samples are valid on Moodle 5.2 and 5.3; source lines were read in 5.3.0 unless marked.

## Buttons, sesskey and what a POST contains

- **Named submit buttons: `PARAM_RAW` and presence**, never `PARAM_INT`: the translated label cleans to 0 and the
  action silently does nothing. Put numeric flags in hidden inputs.

  ```php
  if (optional_param('confirm', '', PARAM_RAW) !== '' && confirm_sesskey()) {
      // Act.
  }
  ```

- **`confirm_sesskey()` with no argument calls `required_param('sesskey')`** and throws `missingparam` on a
  request without one, instead of returning false (`public/lib/sessionlib.php`, 5.3.0). On a page that is also
  reached by plain GET, read it first: `$sesskey = optional_param('sesskey', '', PARAM_RAW);` and branch on it.
- **formslib `hideIf()` also disables the element** (`public/lib/form/form.js`, the dependency handlers return
  `lock` and `hide` together), so hidden fields are not posted at all. Code or a test that builds the POST by hand
  must match what one real browser POST contains, not what `definition()` declares.
- **`sesskey` and `_qf__<formname>` are added after `definition()`**, under the last header
  (`public/lib/formslib.php:219-226`). Code that removes the last section of a form (a plugin decorating a core
  form) must keep those hidden fields, or every submit fails the sesskey check.
- **Checkboxes outside a moodleform** need `form="<formid>"` on each input to be submitted with it.

## validation(), files and draft areas

- **In `moodleform::validation()` never call `get_new_filename()`, `get_file_content()` or `save_file()`.** They
  call `is_validated()`, which runs validation again, and recurse until PHP runs out of memory. Read `$data` (a
  filepicker value is its draft itemid) or `$files`.
- **`file_get_submitted_draft_itemid($elname)` reads `$_REQUEST`, not the form's data**
  (`public/lib/filelib.php`). A form validated or submitted from code (a test, an importer, `mock_submit()`)
  gets 0 unless the request carries the field.
- **`file_save_draft_area_files()` reads the draft area of the current `$USER`** (`context_user::instance($USER->id)`,
  `public/lib/filelib.php`). Code that saves a draft for another user (a task, a web service acting for someone)
  must run as that user, or it saves nothing and reports success.
- **A plain `<input type="file">` does not fill a draft area**; only the JS filepicker does. Outside moodleform,
  store the upload into the user's draft area yourself before `file_save_draft_area_files()`.
- **The file picker's `accepted_types` silently drops extensions that core's file types list does not know**
  (for example `.stl`, `.obj`), so the picker refuses the file with no error to the developer. Use `'*'` and check
  the extension in `validation()`. Only a real upload shows it (Behat `@_file_upload`).
- **The file picker's templates are sent once per request** (a `static` in `initialise_filepicker()`,
  `public/repository/lib.php`). Building a throwaway form with a file element before the real one (to read its
  defaults, say) leaves a later modal's "Add" button with no templates. Build the throwaway form without file
  elements, or after the page's form.

## dynamic_form and forms built off-page

- **A `dynamic_form` runs in a web-service request**: `require_once` every non-autoloaded library it uses, and
  request its AMD module in an override of `render()`, not in `definition()` (definition runs again on submit,
  where no page is printed). Smoke-test it through `\core_form\external\dynamic_form::execute()`, which is the path
  the modal uses.
- **`$PAGE->start_collecting_javascript_requirements()` throws before the theme is initialised**
  ("`$OUTPUT->header()` needs to be called before collecting JavaScript requirements",
  `public/lib/pagelib.php`, `start_collecting_javascript_requirements()`, 5.3.0). Code that builds a form before
  the header (a bulk page, a test) cannot borrow core's helpers that start collection; swap the page's
  requirements manager for a throwaway `page_requirements_manager` instead (it is the protected
  `moodle_page::$_requires`, reached with Reflection), and restore it afterwards.
- **Building another page's form** (for example an activity's `mod_form` on an admin page) needs a private
  `moodle_page`, and saving and restoring `$PAGE`, `$COURSE` and `$OUTPUT` around it; the form constructor reads
  all three.

## mod_form specifics

- **A no-submit button's `setValue()` in `definition_after_data()` is overwritten** by modedit's later
  `set_data()` when the form is re-displayed. Write the value into `$mform->_submitValues[...]` as well.
- **Core module forms read the request, not only `set_data()`:** `mod_lti_mod_form` takes `typeid` from
  `optional_param()` (`public/mod/lti/mod_form.php:77`), the BigBlueButton form calls its server while it is
  built, and question edit forms default `defaultmark` to the user's last-used value. Code that builds or submits
  these forms always sends those fields explicitly.

## Admin settings

- **`admin_setting_configmulticheckbox` is unticked until first saved**; the default only feeds the "Default:" hint.
  Fall back only on a strict `false` (an admin who unticks everything stores `''`).

  ```php
  $value = get_config('local_myplugin', 'options');
  if ($value === false) {
      $value = $defaults;
  }
  ```

- **Choice labels of `configmulticheckbox` and `configselect` are plain text.** Core `s()`-escapes them in the
  "Default:" line and the admin search highlighter mangles markup in them. Put HTML in the setting's description.
- **`admin_setting_filetypes` calls `$this->visiblename->out()`**, so it needs a `lang_string` label; a plain
  `get_string()` result makes the settings page die with "Call to a member function out() on string"
  (`public/lib/adminlib.php:11365` on 5.2, `public/admin/classes/setting/setting/filetypes.php:121` on 5.3.0).
  No gate renders the settings page unless you do: add a test that does.

  ```php
  require_once($CFG->libdir . '/adminlib.php');
  $html = admin_get_root(true, true)->locate('local_myplugin')->output_html();
  $this->assertStringNotContainsString('[[', $html);
  ```

  `admin_settingpage` autoloads but `admin_get_root()` does not, so the `require_once` goes in `setUp()`; a suite
  that passes may hide a file that fails when run alone.
- **New settings without a version bump are never stored**, so a select shows its first choice and Save writes it (`moodle-theme-settings`).
- **A `configtext` regex paramtype takes no trailing modifier** (`/u` aborts install); use `(*UTF)` (`moodle-theme-settings`).
- **A new course-wide setting must win over older per-item values** where that is what the setting promises.
  When an earlier version stored a per-item value (per section, per activity), decide the precedence explicitly
  and test on a course that already has per-item values; a fresh test course hides the conflict.
- **`settings.php` of a `tool` or `local` plugin receives `$ADMIN` and `$hassiteconfig` but no `$settings`**:
  create an `admin_settingpage` inside `if ($hassiteconfig)` and add it with `$ADMIN->add('tools', $page)`, or
  `$settings->add()` on null crashes the upgrade (`moodle-plugin-development` has the recipe for each type).
- **An `admin_externalpage` guarded by a custom capability** goes outside the `if ($hassiteconfig)` block (core
  precedent: `public/report/log/settings.php`), or non-admin holders of the capability get "Access denied".
- **Without `moodle/backup:userinfo`** the backup "Include users" setting is a hidden input, not an unticked
  checkbox; a test or a script that looks for the checkbox finds nothing.

## References

- https://moodledev.io/docs/apis/subsystems/form
- https://moodledev.io/docs/apis/subsystems/form/usage/files
- https://moodledev.io/docs/apis/subsystems/admin
