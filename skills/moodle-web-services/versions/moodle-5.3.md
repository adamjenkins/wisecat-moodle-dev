# Web services on Moodle 5.3

What differs on 5.3 against the 5.2 baseline. Read in the 5.3.0 source and its `UPGRADING.md`; the full upgrade
catalogue is in `moodle-5-3-changes`.

## Legacy global names are deprecated

The global classes and functions that `lib/externallib.php` aliased on 5.2 are deprecated on 5.3
(`public/lib/external/UPGRADING.md`, MDL-81225; `public/lib/db/renamedclasses.php`, "Since Moodle 5.3"):

| Old | Use on every version |
|---|---|
| `\external_api`, `\external_value`, `\external_single_structure`, `\external_multiple_structure`, `\external_function_parameters`, `\external_description`, `\external_format_value`, `\external_files`, `\external_warnings`, `\external_settings`, `\restricted_context_exception` | the same name in `core_external\` |
| `\external_util` | `\core_external\util` |
| `external_format_string()`, `external_format_text()` | `\core_external\util::format_string()`, `::format_text()` |
| `external_generate_token()`, `external_create_service_token()` | `\core_external\util::generate_token()` |
| `external_generate_token_for_current_user()`, `external_log_token_request()`, `external_validate_format()`, `external_delete_descriptions()` | the `\core_external\util` method of the same purpose |

- The old class names now resolve through the renamed-classes list, and the autoloader emits a developer
  `debugging()` notice ("Class 'external_api' has been renamed for the autoloader and is now deprecated"), which
  fails a PHPUnit or Behat run (`public/lib/classes/component.php`, read in 5.3.0, not run).
- The old functions are final deprecations on 5.3: they are stubs marked `final: true`, so calling one throws a
  `coding_exception` (`public/lib/externallib.php` and `public/lib/classes/deprecation.php`,
  `emit_deprecation_notice()`, 5.3.0). Code that still calls `external_format_string()` breaks.
- Find the old names, then switch to `use core_external\...;` (the namespaced names work on 5.2 too):

  ```bash
  grep -rnE '\bexternal_(api|value|single_structure|multiple_structure|function_parameters|format_value|files|warnings|util|settings|description|format_string|format_text|generate_token)\b' \
    --include=*.php . | grep -v 'core_external\\'
  ```

## `login/token.php`

- Username and password in the query string throw `coding_exception` ("Username and password can only be sent via
  POST parameters for security reasons.").
- The service is looked up first; a missing or disabled one fails with `servicenotavailable` before authentication.
- The `appsitecheck` mode is removed.

Source: `public/login/token.php` (5.3.0, compared with 5.2), MDL-87010.

## CORS for public AJAX functions

A new `db/services.php` key, `'allowcorsrequests' => true`, lets `lib/ajax/service-nologin.php` answer cross-origin
requests. CORS is sent only when the request has no Moodle cookies and every function in the batch allows it and has
`'loginrequired' => false` (`public/lib/ajax/service.php`, 5.3.0; MDL-87150). On 5.2 the key is ignored, so a plugin
that supports both versions can set it unconditionally.

## Course module returns

Core and module functions that return course modules (`core_course`, forum, h5p, assign) now share
`standard_coursemodule_elements`. A plugin's own `mod_*_get_*_by_courses` function should build its course-module
fields with `\core_course\external\helper_for_get_mods_by_courses` (`standard_coursemodule_element_values()` and
`standard_coursemodule_elements_returns()`) so the app sees the same shape (`UPGRADING.md`, MDL-87241;
`public/course/classes/external/helper_for_get_mods_by_courses.php`, 5.3.0).

## The REST API (routing engine) and personal access tokens

5.3 adds a token path that is separate from web service tokens:

- `\core\api\token_manager` mints personal access tokens for the routed REST API; users manage them at
  `/user/personalaccesstokens.php`, gated by `moodle/api:createtoken` (`UPGRADING.md`, MDL-87706;
  `public/lib/classes/api/`, absent on 5.2).
- Routes declare OAuth2 scopes with the `\core\router\scope\scopeset` attribute, or opt out with
  `\core\router\scope\unscoped_resource` (`public/lib/classes/router/scope/`, 5.3.0).
- The OAuth2 server needs `league/oauth2-server` from Composer (`composer.json`, 5.3.0; not in 5.2), so a site
  installed from Git needs `composer install`.

These tokens are not `external_tokens` rows and do not call `db/services.php` functions. Routed controllers belong
to the routing engine; see `moodle-upgrade-migration`.
