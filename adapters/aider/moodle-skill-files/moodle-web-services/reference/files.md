# Files through web services

Read this when an external function accepts uploaded files, saves a draft area, or returns files and pluginfile URLs
to a token client (REST or the Moodle app).

## Upload: draft area first, then your function

A token client cannot send a file inside a function call. It uploads to its own draft area, then passes the draft
item id to your function.

1. Upload with a multipart POST to `webservice/upload.php`. The service must have `uploadfiles => 1`, otherwise
   "Web service file upload must be enabled in external service settings".

   ```bash
   curl -s "$SITE/webservice/upload.php" \
     -F "token=$TOKEN" \
     -F "itemid=0" \
     -F "file_1=@report.pdf"
   ```

   `itemid=0` creates a new draft item; pass a returned `itemid` again to add more files to the same draft. The
   response is a JSON array with one entry per file, each holding `itemid`, `filename` and so on. There is no
   `filearea` parameter: the script always writes to the token user's draft area (`public/webservice/upload.php`,
   5.2 and 5.3).
2. Call your function with the draft item id as a `PARAM_INT` parameter.
3. In `execute()`, after the usual validation, move the files into your area:

   ```php
   $usercontext = \core\context\user::instance($USER->id);
   $fs = get_file_storage();
   if (!$fs->get_area_files($usercontext->id, 'user', 'draft', $params['draftitemid'], 'id', false)) {
       throw new \moodle_exception('nofile', 'error');
   }
   file_save_draft_area_files($params['draftitemid'], $context->id, 'local_example', 'attachments',
       $itemid, ['subdirs' => 0, 'maxfiles' => 5, 'maxbytes' => $maxbytes]);
   ```

   `file_save_draft_area_files()` reads the draft area of the current user only, so a draft id belonging to someone
   else saves nothing; that is the protection, so do not look the draft up by id across users. Enforce limits in the
   options; the upload script does not know your plugin's limits.

AJAX callers use the normal file picker or `core_form` dynamic forms instead; they also end with a draft item id.

## Download: URLs a token client can open

A token client has no session cookie, so a normal `pluginfile.php` URL returns the login page. Return URLs through
the web service file server:

- For a whole file area, use the helper, which builds the URLs and the standard description:

  ```php
  use core_external\external_files;
  use core_external\util;

  // In execute():
  $files = util::get_area_files($context->id, 'local_example', 'attachments', $item->id);

  // In execute_returns(), inside the item structure:
  'files' => new external_files('Attachments', VALUE_OPTIONAL),
  ```

  `get_area_files()` returns `filename`, `filepath`, `filesize`, `fileurl`, `timemodified`, `mimetype` and
  `isexternalfile`, with `fileurl` pointing at `webservice/pluginfile.php`
  (`public/lib/external/classes/util.php`, `get_area_files()`, 5.3.0).
- For one file, `\moodle_url::make_webservice_pluginfile_url($contextid, $component, $area, $itemid, $path, $name)`.
- The client appends `?token=...` to the URL. The service must have `downloadfiles => 1`
  (`public/webservice/pluginfile.php`, 5.3.0).
- Your plugin's `pluginfile` callback still runs and still does the access check, as the token user.

## Text with embedded files

Rich text that contains `@@PLUGINFILE@@` links must be rewritten for the caller. `util::format_text()` does this when
given the file area:

```php
[$text, $format] = util::format_text($item->intro, $item->introformat, $context,
    'local_example', 'intro', $item->id);
```

It returns the formatted text and the format; describe them in the returns with `PARAM_RAW` for the text and
`new external_format_value('intro')` for the format. Called from a web service request (REST or the app),
the rewritten URLs point at the web service file server; from AJAX they point at `pluginfile.php`, which the
session can open. Source: `public/lib/external/classes/util.php`, `format_text()`, and
`public/lib/ajax/service.php` (`external_settings` with `set_file('pluginfile.php')`), 5.3.0.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Returning `moodle_url::make_pluginfile_url()` to a token client | The client downloads the login page | `util::get_area_files()` or `make_webservice_pluginfile_url()` |
| Service without `downloadfiles => 1` | File URLs fail for that service | Set it in `$services`, bump, upgrade |
| Sending `filearea=draft` to `upload.php` | Ignored; harmless but misleading | Leave it out |
| Not checking that the draft has files | The function "succeeds" and saves nothing | Check the draft area, throw a clear error |
| Returning raw `@@PLUGINFILE@@` text | Broken images in the client | `util::format_text()` with component, area and item id |
