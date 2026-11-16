# Tokens and calling over REST or SOAP

Read this when you call an external function over REST or SOAP, issue or revoke tokens, use `login/token.php`, or
need to limit what a token can do.

## Turning web services on for a client

An external client needs all of these on the site, in Site administration > Server > Web services (the "Overview"
page there walks through them):

1. Advanced features: "Enable web services" (`enablewebservices`). Without it every call fails with
   "Web services are not enabled in Advanced features."
2. The protocol enabled (Manage protocols: REST, SOAP). Without it: "You are not allowed to use the rest protocol".
3. A service that contains the functions, enabled. A predefined service from `db/services.php` appears here after
   the upgrade; enable it, or build a custom one.
4. If the service has `restrictedusers => 1`: the user added under Authorised users. Otherwise "The user is not
   allowed for this service".
5. The user holds `webservice/rest:use` (or `webservice/soap:use`) and every capability the functions check.
6. A token for that user and service.

Error texts read in `public/webservice/lib.php` (5.3.0).

## Calling over REST

```bash
SITE=https://moodle.example.com
TOKEN=0123456789abcdef0123456789abcdef

curl -s "$SITE/webservice/rest/server.php" \
  --data-urlencode "wstoken=$TOKEN" \
  --data-urlencode "moodlewsrestformat=json" \
  --data-urlencode "wsfunction=local_example_get_items" \
  --data-urlencode "courseid=5" \
  --data-urlencode "limit=10"
```

- Send the call as POST. Arrays use PHP form syntax: `ids[0]=3&ids[1]=4`, `items[0][name]=x`.
- An error comes back as a normal JSON body, not as an HTTP error, so check for an `exception` key:

  ```json
  {"exception":"invalid_parameter_exception","errorcode":"invalidparameter","message":"Invalid parameter value detected"}
  ```

  `debuginfo` (which names the failing key) is included only when the site has debugging on
  (`public/webservice/rest/locallib.php`, `generate_error()`, 5.3.0).
- Without `moodlewsrestformat=json` the response is XML.
- SOAP: `webservice/soap/server.php?wsdl=1&wstoken=...` gives the WSDL. XML-RPC is not in core on 5.2 or 5.3
  (`public/webservice/` holds only `rest` and `soap`).

## Getting a token

### For a user, with username and password: `login/token.php`

```bash
curl -s "$SITE/login/token.php" \
  --data-urlencode "username=student1" \
  --data-urlencode "password=..." \
  --data-urlencode "service=local_example_api"
```

The response is `{"token":"...","privatetoken":"..."}` or an error object; `service` is the service `shortname`.
The script calls `util::generate_token_for_current_user()`, which returns the user's existing valid token for that
service or creates one, and creates one only if the user holds `moodle/webservice:createmobiletoken` (for the mobile
service) or `moodle/webservice:createtoken` (any other service, not for site admins); otherwise it fails with
`cannotcreatetoken`. The service's `requiredcapability` and its authorised-users list are checked first
(`public/lib/external/classes/util.php`, `generate_token_for_current_user()`, 5.3.0).

**5.3+:** credentials in the query string throw a `coding_exception` ("Username and password can only be sent via
POST parameters"), a missing or disabled service fails with `servicenotavailable` before the user is
authenticated, and `appsitecheck` is gone (`public/login/token.php`, 5.3.0).

### Issued by code

```php
use core_external\util;

$service = $DB->get_record('external_services', ['shortname' => 'local_example_api'], '*', MUST_EXIST);
$token = util::generate_token(
    EXTERNAL_TOKEN_PERMANENT,
    $service,
    $user->id,
    \core\context\system::instance(),
    time() + DAYSECS * 30,      // validuntil, 0 for no expiry.
    '',                         // iprestriction, for example '192.0.2.0/24'.
    'Example integration'       // name shown on the token list.
);
```

Signature read in `public/lib/external/classes/util.php` (5.2 and 5.3). `generate_token()` always inserts a new row
and never returns an existing one. Before minting, look for a token you already issued:

```php
$existing = $DB->get_record('external_tokens', [
    'userid' => $user->id,
    'externalserviceid' => $service->id,
    'tokentype' => EXTERNAL_TOKEN_PERMANENT,
], '*', IGNORE_MULTIPLE);
```

Delete tokens you mint when the integration ends (`$DB->delete_records('external_tokens', ['id' => $id])`), and
remove them in the privacy provider and `db/uninstall.php` if the plugin owns them.

For the current user (for example a "connect the app" page), `util::generate_token_for_current_user($service)` reuses
a valid token and creates one only if none exists, with the capability checks described above.

### By an administrator

Site administration > Server > Web services > Manage tokens. Users with `moodle/webservice:createtoken` can see
their own tokens on the Security keys page (`user/managetoken.php`).

## Limiting what a token can do

- **Scope:** the token works only for the functions of its service. Build a custom service with only the functions
  the client needs rather than handing out a token for the mobile service.
- **Context restriction:** the context passed to `generate_token()` is enforced by `validate_context()`: a token
  created for a course context cannot reach another course (`restricted_context_exception`).
- **Expiry and network:** `validuntil` and `iprestriction` are checked on every call
  (`public/webservice/lib.php`, `webservice::authenticate_user()`, 5.3.0).
- **Rate limiting:** core has no per-token rate limit on 5.2 or 5.3. Limit at the reverse proxy (for example nginx
  `limit_req` on `/webservice/`), or keep a counter in your function and throw a `moodle_exception` when it is over.
- **Last use:** `external_tokens.lastaccess` records the last call, updated at most once a minute
  (`webservice::TOKEN_LASTACCESS_UPDATE_SECS`, 5.3.0).

## Calling from the browser

`core/ajax` posts to `lib/ajax/service.php` with the session and sesskey; no token is involved. The function needs
`'ajax' => true`. A function with `'loginrequired' => false` is called through `lib/ajax/service-nologin.php`, which
`core/ajax` uses when its third argument (`loginrequired`) is `false`. The JavaScript side, including how the
promise array works, is in `moodle-amd-javascript`.

**5.3+:** `'allowcorsrequests' => true` adds CORS headers to a `service-nologin.php` response, and only when every
function in the batch allows it and none needs login (`public/lib/ajax/service.php`, 5.3.0).
