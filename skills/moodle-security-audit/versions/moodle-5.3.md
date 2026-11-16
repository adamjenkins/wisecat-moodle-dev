# Moodle 5.3: security-relevant changes

Read this when the plugin supports 5.3 and it calls the token endpoint, defines external functions for
`core/ajax`, adds REST API routes, builds Moodle app deep links, or checks whether a user may log in. Each item
is new in 5.3 against 5.2; all were read in the 5.3.0 source and its `UPGRADING.md`, not run. The full 5.3
catalogue is `moodle-5-3-changes`.

## The token endpoint takes credentials by POST only

`login/token.php` throws a `coding_exception` when `username` or `password` arrive as GET parameters, checks that
the requested service exists and is enabled before it authenticates, and no longer answers `appsitecheck`
(`public/login/token.php`; MDL-87010). A client or test that built a token URL with a query string fails on 5.3:

```bash
curl -s -X POST "$WWWROOT/login/token.php" \
    --data-urlencode "username=$USERNAME" --data-urlencode "password=$PASSWORD" --data-urlencode "service=moodle_mobile_app"
```

## CORS for AJAX functions: `allowcorsrequests`

A function in `db/services.php` may declare `'allowcorsrequests' => true`. `lib/ajax/service.php` then sends
`Access-Control-Allow-Origin: *`, but only on the no-cookie (no-login) AJAX endpoint and only when every function
in the batch allows CORS and none has `loginrequired` (`public/lib/ajax/service.php`; MDL-87150). Set it only on a
`'loginrequired' => false` function whose answer is safe for any site on the internet to read.

```php
'local_example_get_public_stats' => [
    'classname' => \local_example\external\get_public_stats::class,
    'type' => 'read',
    'ajax' => true,
    'loginrequired' => false,
    'allowcorsrequests' => true,
],
```

On 5.2 the key is ignored (`external_api` does not read it), so the declaration is harmless there.

## REST API: personal access tokens and route scopes

- `\core\api\token_manager` mints personal access tokens for the REST API; users manage theirs at
  `/user/personalaccesstokens.php`, gated by `moodle/api:createtoken` (`public/lib/classes/api/token_manager.php`;
  MDL-87706).
- A route method declares the scopes a token needs with the repeatable `#[\core\router\scope\scopeset(...)]`
  attribute, or declares that it needs none with `#[\core\router\scope\unscoped_resource]`. A method with neither
  has no scope restriction at all: `\core\router\util::get_all_required_scopes_for_method()` returns an empty
  list, as it does for an unscoped resource (`public/lib/classes/router/util.php`). Annotate every route so the
  intent is explicit and a token with narrow scopes cannot reach it by omission. A scope class that does not
  exist on the running version disables the whole scope set instead of dropping it (same file).

## `\core_auth\validate_user`: one place for "may this user log in"

`\core\di::get(\core_auth\validate_user::class)` centralises the checks core makes before a login
(`public/auth/classes/validate_user.php`; MDL-88580):

| Method | Checks |
|---|---|
| `validate_before_web_login($user)` | not suspended, auth method enabled |
| `validate_before_external_login($user)` | maintenance-mode access, not deleted, confirmed, not suspended, auth enabled, credentials not expired |
| `validate_before_token_login($user)` | maintenance-mode access, confirmed, credentials not expired |

Each throws an exception on failure. A plugin that authenticates users itself (an auth plugin, an SSO bridge, a
token endpoint of its own) calls the matching method rather than re-implementing the list. The class does not
exist on 5.2; guard with `class_exists(\core_auth\validate_user::class)` in a plugin that supports both. The same
change moved the auth helper functions (`get_auth_plugin()`, `is_enabled_auth()` and others) to
`\core\authentication`; the mapping is in `moodle-5-3-changes`.

## Mobile app deep-link auto-login is a setting, off by default

5.3 adds `tool_mobile/enabledeeplinkautologin` (default 0), returned to the app in the public site configuration
as `tool_mobile_enabledeeplinkautologin` (`public/admin/tool/mobile/settings.php`,
`public/admin/tool/mobile/classes/api.php`). A plugin that builds app deep links carrying tokens cannot assume
the app logs the user in from them on 5.3 (read in the source, not run).

## HTMLPurifier allows `<details>` and `<summary>`

`clean_text()` and `format_text()` keep HTML5 `<details>` and `<summary>` elements on 5.3, where 5.2 stripped
them (MDL-88618). Content a plugin stores on 5.3 with these elements loses them when shown on a 5.2 site, and a
test that asserts their removal fails on 5.3.
