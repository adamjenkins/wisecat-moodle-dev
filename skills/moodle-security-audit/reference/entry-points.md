# Entry points other than page scripts

Read this when the plugin has AJAX scripts, external functions (`db/services.php`), mobile methods
(`db/mobile.php`), dynamic forms, a `pluginfile` callback, scheduled or adhoc tasks, or a filter, and you are
auditing or writing their access checks.

Every entry point needs the same three answers: who is logged in, which context the action is in (derived from a
record, not from the request), and which capability allows it. Each type below gets them in a different place.

## AJAX scripts

```php
define('AJAX_SCRIPT', true);
require(__DIR__ . '/../../config.php');

$itemid = required_param('itemid', PARAM_INT);
$item = $DB->get_record('local_example_items', ['id' => $itemid], '*', MUST_EXIST);
$context = context_course::instance($item->courseid);

require_login($item->courseid, false);
require_sesskey();
require_capability('local/example:edit', $context);

echo json_encode(['ok' => true]);
```

`AJAX_SCRIPT` changes only how errors are printed; it checks nothing. Prefer an external function with
`'ajax' => true`, which gets parameter validation and the session checks of `core/ajax` for free.

## External functions

```php
public static function execute(int $itemid): array {
    global $DB;
    ['itemid' => $itemid] = self::validate_parameters(self::execute_parameters(), ['itemid' => $itemid]);

    $item = $DB->get_record('local_example_items', ['id' => $itemid], '*', MUST_EXIST);
    $context = \core\context\course::instance($item->courseid);
    self::validate_context($context);
    require_capability('local/example:edit', $context);
    // ...
}
```

- `validate_context()` performs the login and course access check for that context
  (`public/lib/external/classes/external_api.php`, 5.3.0). Call it on the context of the record being acted on,
  never on a `courseid` or `contextid` parameter taken at face value.
- The `'capabilities'` key in `db/services.php` is documentation for token administrators. Nothing in
  `external_api` enforces it; the function calls `require_capability()` itself.
- `'loginrequired' => false` makes the function callable without a session. Such a function must not reveal or
  change anything per user.
- `validate_parameters()` rejects a value that cleaning would change rather than cleaning it, so free text is
  `PARAM_RAW` there and is escaped at every sink (`moodle-web-services`).
- Match the function's capability to the one the equivalent page requires. A service that is laxer than its page
  is the bypass.

## Mobile methods (`classes/output/mobile.php`)

The app calls them through `tool_mobile_get_content`, which validates only the component and method names,
takes every argument value as `PARAM_RAW`, and makes no course or activity access check
(`public/admin/tool/mobile/classes/external.php`, 5.3.0). Each method does all of it itself:

```php
public static function mobile_view($args) {
    global $DB;
    $cmid = clean_param($args['cmid'] ?? 0, PARAM_INT);
    $cm = get_coursemodule_from_id('example', $cmid, 0, false, MUST_EXIST);
    $context = \core\context\module::instance($cm->id);
    require_login($cm->course, false, $cm, true, true);
    require_capability('mod/example:view', $context);
    // ...
}
```

Never interpolate an `$args` value into SQL; bind it as a placeholder after `clean_param()`.

## Dynamic forms (`core_form\dynamic_form`)

The client posts the form's arguments, including any `contextid` or record id. In
`get_context_for_dynamic_submission()`, load the record named by the id and return its context; in
`check_access_for_dynamic_submission()`, call `require_capability()` on that context. Both are abstract on
`public/lib/form/classes/dynamic_form.php` (5.3.0). The form's constructor calls `validate_context()` on the
returned context and then the access check each time the form web service loads or submits the form, so these
two methods are the only gate: a check placed only in the page that opens the modal is bypassed by calling the
web service directly.

```php
protected function get_context_for_dynamic_submission(): \context {
    global $DB;
    $id = $this->optional_param('id', 0, PARAM_INT);
    $item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
    return \core\context\course::instance($item->courseid);
}

protected function check_access_for_dynamic_submission(): void {
    require_capability('local/example:edit', $this->get_context_for_dynamic_submission());
}
```

## `pluginfile` callbacks

`pluginfile.php` resolves the context from the URL and calls the component's callback. Authorisation is the
callback's job:

```php
function local_example_pluginfile($course, $cm, $context, $filearea, $args, $forcedownload, array $options = []) {
    if ($context->contextlevel !== CONTEXT_COURSE) {
        return false;
    }
    if ($filearea !== 'attachments') {
        return false;
    }
    require_login($course);
    require_capability('local/example:viewfile', $context);

    $itemid = (int) array_shift($args);
    $filename = array_pop($args);
    $filepath = $args ? '/' . implode('/', $args) . '/' : '/';

    $file = get_file_storage()->get_file($context->id, 'local_example', $filearea, $itemid, $filepath, $filename);
    if (!$file || $file->is_directory()) {
        return false;
    }
    send_stored_file($file, 0, 0, true, $options);   // Force download for user uploads.
}
```

- Check that the item id belongs to something the user may see (a submission of their own, or a grader's
  capability), not only the capability on the context.
- Serve inline only files you have validated as media or images; everything else force-downloads.

## Scheduled and adhoc tasks

A task runs without the requesting user's session. A capability checked when the task was queued is not
checked again when it runs, so a stored target (course id, user id) tampered with in between runs with the
task's rights. Re-check at the sink: `has_capability('local/example:push', $context, $userid)` for the user who
queued it, stored with the task. An adhoc task given `set_userid()` runs as that user.

## Filters

A filter's `filter()` runs on text written by any user and its output is not cleaned again. Build HTML with
`html_writer` or a template, escape every value taken from the text, and never expand secrets (the sesskey,
tokens) into the output. A filter is also on every page's hot path: `setup()` runs for every `format_text()`
call, and for every `format_string()` call on a site that filters all strings
(`public/lib/classes/formatting.php`, 5.3.0), so it must not run per-call queries.
