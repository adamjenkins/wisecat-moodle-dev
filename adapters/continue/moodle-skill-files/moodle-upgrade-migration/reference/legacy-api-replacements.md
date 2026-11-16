# Legacy API replacements

Read this when porting code written for Moodle 3.x or 4.x, or when a deprecated function, class or template is not
in the table in `SKILL.md`.

"Removed" below means the symbol does not exist in the 5.2 or 5.3.0 source (grep of `public/lib`, `public/course`,
`public/mod`; read, not run). "Alias" means the old name still resolves. Each row says what to write instead; the
code in the right-hand column is valid on 5.2 and 5.3.

## How to tell what state a symbol is in

| What you see | State | What to do |
|---|---|---|
| Works, "has been deprecated" `debugging()` | Initial deprecation | Replace before the next major (6.0 for 4.5-5.2 deprecations, 7.0 for 5.3 ones) |
| Throws `coding_exception` "... can not be used any more" or similar | Final deprecation: a stub | Replace now; it never works |
| "Call to undefined function", "Class not found", "Undefined constant" | Removed | Replace now |
| Old class name works silently | Legacy alias (`public/lib/db/legacyclasses.php`) or rename map (`db/renamedclasses.php`, which does emit a notice) | Prefer the new name; required only when the alias is deprecated |

Core marks deprecated PHP with `#[\core\attribute\deprecated(replacement: ..., since: ..., mdl: ..., final: ...)]`
and emits the notice with `\core\deprecation::emit_deprecation()` (`public/lib/classes/deprecation.php`). Use the
same in your own plugin's public API:

```php
// replacement, reason or mdl is required; since is free text (here the plugin's own release).
#[\core\attribute\deprecated(replacement: '\local_example\api::get_items', since: '2.0')]
function local_example_get_items(int $courseid): array {
    \core\deprecation::emit_deprecation(__FUNCTION__);
    return \local_example\api::get_items($courseid);
}
```

## Errors, logging, notifications

| Old | Status | New |
|---|---|---|
| `print_error($key, $component, $link, $a)` | Removed | `throw new \moodle_exception($key, $component, $link, $a)` |
| `add_to_log()` | Removed | An event class under `classes/event/`, then `::create([...])->trigger()` |
| `notify($text, $class)` | Removed | `\core\notification::add($text, \core\notification::ERROR)` (shown on the next page) or `echo $OUTPUT->notification($text, 'error')` |
| `redirect($url, $msg, 0)` with a delay to show text | Works, but the delay page is dated | `redirect($url, $msg, null, \core\notification::SUCCESS)` |
| `error()` | Removed | `throw new \moodle_exception(...)` |
| `new moodle_exception(..., $debuginfo)` without the cause | Works | 5.3+: `previous: $e` as a named argument chains the cause (MDL-88579) |

## Output and pages

| Old | Status | New |
|---|---|---|
| `html_writer`, `moodle_url`, `pix_icon`, `single_button`, `action_link` (global names) | Aliases, no notice | `\core\output\html_writer`, `\core\url`, `\core\output\pix_icon`, ... (both work on 5.2 and 5.3) |
| `context_course::instance()`, `context_module::instance()` | Aliases, no notice | `\core\context\course::instance()`, `\core\context\module::instance()` |
| `get_context_instance(CONTEXT_COURSE, $id)` | Removed | `\core\context\course::instance($id)` |
| `new \Mustache_Engine` in plugin code | Works, bypasses theme overrides and helpers | `$OUTPUT->render_from_template('local_example/x', $context)` |
| `format_text($text)` without context | Uses `$PAGE->context`, wrong for cron and web services | `format_text($text, $format, ['context' => $context])` |
| `$PAGE->requires->yui_module()` and YUI widgets | YUI is legacy; `moodle-core-notification-confirm` removed in 5.2 | AMD/ES modules: `core/modal`, `core/notification` |
| `core/modal_factory`, `core/modal_registry` | Removed in 5.2 (MDL-79182) | `import Modal from 'core/modal'; await Modal.create({...})` or a subclass's `create()` |
| `M.util.set_user_preference()` | Removed in 5.2 | `core_user/repository` `setUserPreference()` |
| `core_renderer::sr_text()` | Deprecated, removal in 6.0 | `visually_hidden_text()` |
| `<component>_before_footer()` and other output `lib.php` callbacks | Deprecated, debugging notice | Hooks (`moodle-hooks-api`) |

## Forms

| Old | Status | New |
|---|---|---|
| `$mform->setHelpButton()` | Removed | `$mform->addHelpButton('field', 'identifier', 'component')` |
| `duration` element with `units` that exclude the default unit | 5.3: throws | Pass a `defaultunit` from `units` (`moodle-5-3-changes`) |
| Form-only `require_once` of `externallib.php` | Not needed | autoloaded classes |

## Web services

| Old | Status | New |
|---|---|---|
| `class x extends external_api` (global) | 5.2 alias; 5.3 deprecated via the rename map | `use core_external\external_api;` (namespace since 4.2) |
| `external_value`, `external_single_structure`, `external_multiple_structure`, `external_function_parameters`, `external_warnings`, `external_files`, `external_format_value`, `external_description`, `external_settings`, `external_util`, `restricted_context_exception` | Same | `\core_external\...` same short name (`external_util` is `\core_external\util`) |
| `external_format_text()`, `external_format_string()`, `external_validate_format()`, `external_generate_token()`, `external_create_service_token()`, `external_delete_descriptions()`, `external_generate_token_for_current_user()`, `external_log_token_request()` | 5.2: work without a notice (`public/lib/externallib.php`); 5.3: stubs that throw `coding_exception` (MDL-81225) | `\core_external\util::format_text()`, `format_string()`, `validate_format()`, `generate_token()`, `delete_service_descriptions()`, `generate_token_for_current_user()`, `log_token_request()` |

A plugin that still supports a branch before 4.2 aliased the classes itself:

```php
if (!class_exists(\core_external\external_api::class)) {
    class_alias(\external_api::class, \core_external\external_api::class);
}
```

On 5.2 and 5.3 the namespaced classes always exist, so drop such shims.

## Courses, formats, activities

| Old | Status | New |
|---|---|---|
| `format_base` | Removed | `\core_courseformat\base` (since 4.0) |
| Format output in `renderer.php` only | Works for old formats | Output classes under `classes/output/courseformat/` extending `\core_courseformat\output\local\...` (4.0+) |
| `coursecat` (class), `coursecat::get()` | Removed | `core_course_category::get()` |
| `course_delete_module($cmid)` | Deprecated in 5.2 (MDL-86856) | `\core_courseformat\formatactions::cm($courseid)->delete($cmid)` |
| `duplicate_module($course, $cm)` | Deprecated in 5.2 (MDL-86858) | `formatactions::cm($courseid)->duplicate($cmid)` |
| `moveto_module($mod, $section, $beforemod)` | Deprecated in 5.2 (MDL-86854) | `formatactions::cm($courseid)->move_before($cmid, $beforecmid)` or `move_end_section($cmid, $sectionid)` |
| `get_return_section()` on a format | Deprecated in 5.3 | `get_page_section()` (5.3+) |
| `course/changenumsections.php` | Deprecated in 5.1 | `course/format/update.php` actions |
| Format setting `maxsections`, `get_max_sections()` | Deprecated in 5.1, removal in 6.0 | Your own format setting |
| `FEATURE_GROUPMEMBERSONLY` in `<mod>_supports()` | 5.3: install and upgrade throw | Delete the case |
| `ASSIGN_ATTEMPT_REOPEN_METHOD_NONE` | Removed in 5.2 (MDL-87425) | The remaining `ASSIGN_ATTEMPT_REOPEN_METHOD_*` constants |
| `\assign_header` (global) | Moved in 4.0 | `\mod_assign\output\assign_header` |

`formatactions` and the `cmactions` methods above exist on 5.2 and 5.3 (`public/course/format/classes/formatactions.php`,
`local/cmactions.php`); a plugin that still supports 5.1 or earlier guards each call with `method_exists()`.

## Front end

| Old | Status | New |
|---|---|---|
| Bootstrap 4 classes: `.sr-only`, `.ml-*`, `.mr-*`, `.pl-*`, `.pr-*`, `.float-left/right`, `.text-left/right`, `.badge-*`, `.media`, `.form-group`, `.custom-select` | Compat layer, removal in 6.0 (MDL-84465); outlined in Behat with `--scss-deprecations` | `.visually-hidden`, `.ms-*`, `.me-*`, `.ps-*`, `.pe-*`, `.float-start/end`, `.text-start/end`, `.text-bg-*`, flex utilities, `.mb-3`, `.form-select` |
| `data-toggle`, `data-target`, `data-dismiss` | Rewritten by `theme_boost/bs4-compat` only when that module runs; removal in 6.0 | `data-bs-toggle`, `data-bs-target`, `data-bs-dismiss` |
| jQuery Bootstrap plugins (`$(el).tooltip()`) | `window.jQuery` kept for them until 6.0 | `import {Tooltip} from 'theme_boost/index';` (5.2 and 5.3) or `from 'bootstrap'` (5.3+) |
| `theme_boost/bootstrap/<module>` imports | 5.3: alias, deprecated, removal in 7.0 | as above |
| `M.str`, `M.util.get_string()` | Works | `core/str` `getString()` |

Theme-side detail (SCSS imports, variables that became custom properties, copied templates): the theme skills,
starting at `moodle-theme-development`.

## Libraries and Composer

- Moodle 5.1 put the web root at `public/` and Composer's `vendor/` beside it at `$CFG->root`; plugins live under
  `public/`. A plugin that bundled a library keeps it in its own directory and lists it in `thirdpartylibs.xml`.
- On 5.3 core's own Composer packages must be installed (`composer install` at the Moodle root), and features that
  need one check `\core\di::get(\core\composer::class)->get_package_status('vendor/package')->installed`
  (MDL-88576).
