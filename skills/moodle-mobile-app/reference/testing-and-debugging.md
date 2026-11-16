# Testing and debugging app support

Read this when the plugin does nothing or errors in the app, you need the site settings the app requires, you want
to call `tool_mobile_get_content` with curl, run the app in a browser, or send push notifications. Server facts were
read in Moodle 5.2 and 5.3.0; app facts in the Moodle app 5.3.0 source and its developer docs. The failure patterns
below were seen in a running app; the commands were not re-run for this file.

## Level 1: call what the app calls (no app needed)

The app is a REST client. Most "does nothing in the app" bugs reproduce with two requests and a test account:

```bash
SITE=https://moodle.example.test
# 1. A token for the official mobile service. POST: 5.3 rejects credentials in the query string.
TOKEN=$(curl -s -X POST "$SITE/login/token.php" \
    --data-urlencode "username=student1" --data-urlencode "password=$TESTPASS" \
    -d "service=moodle_mobile_app" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("token", "NO TOKEN"))')

# 2. The content call exactly as the app makes it.
curl -s -X POST "$SITE/webservice/rest/server.php" \
    -d "wstoken=$TOKEN" -d "moodlewsrestformat=json" -d "wsfunction=tool_mobile_get_content" \
    -d "component=mod_example" -d "method=mobile_course_view" \
    -d "args[0][name]=cmid" -d "args[0][value]=42" \
    -d "args[1][name]=courseid" -d "args[1][value]=7" | python3 -m json.tool
```

Do the same for each web service your templates call, with the same token. Then check `otherdata` values are
strings, the first template is the one you expect, and `javascript` is what you meant to send.

- **Turn on developer debugging before reading an error.** Without it the REST layer returns
  `{"exception": "webservice_access_exception", "errorcode": "accessexception", "message": "Access control
  exception"}` with no detail; with it, `debuginfo` names the cause (a missing capability, a function not in the
  service).
- **A PHPUnit test that calls the method or `\tool_mobile\external::get_content()` in process proves less than it
  seems**: it never enters the web service permission layer (`webservice/rest:use`, service membership, token
  checks), which is where a site that is not set up for the app fails.

## Site settings the app needs

| Setting | Where | Why |
|---|---|---|
| `enablewebservices` | Advanced features | Web services at all |
| `enablemobilewebservice` | Advanced features ("Enable web services for mobile devices") | Enables the `moodle_mobile_app` service |
| `webservice/rest:use` for the authenticated user role | Set by the admin page above | Without it every REST call from a normal account is "Access control exception" |
| REST protocol enabled | Manage protocols | The app uses REST |
| HTTPS | Site URL | Default on for the mobile service only when the site runs on HTTPS (`public/admin/tool/mobile/settings.php:39`) |

Enabling the mobile service through the admin page also assigns `webservice/rest:use` to the default authenticated
role (`public/admin/classes/setting/setting/enablemobileservice.php`, 5.3.0; class in `public/lib/adminlib.php` on
5.2). Setting the config value from the CLI (`admin/cli/cfg.php --name=enablemobilewebservice --set=1`) does not: the
script calls `set_config()` directly and never runs the setting's `write_setting()` (`admin/cli/cfg.php`, read 5.2
and 5.3). A site configured that way fails every app call for non-admin users until the capability is assigned.

## Level 2: the app itself

Needed for rendering, navigation and anything in the "Traps that only show in the app" list in SKILL.md.

- Hosted builds of the app run in a Chromium browser (https://moodledev.io/general/app/development/setup/app-in-browser);
  Moodle HQ also publishes Docker images. Building from source needs the Node version in the app's `package.json`
  `engines`, which is newer than the one Moodle's grunt uses: install it with nvm for that shell only.
- **CORS stops a browser-hosted app at the first request.** The app's first call to a new site is an AJAX request
  from another origin. The error reads "Can't connect to site ... serverconnectionajax", which looks like DNS or a
  typo; `curl` to the same URL works. The app's documentation runs Chromium with `--disable-web-security
  --disable-site-isolation-trials` and a separate `--user-data-dir` for development. Never change the site for
  this: a packaged app on a device has no CORS restriction.
- Serve the app over the same scheme as the site; an HTTPS app calling an HTTP site is blocked as mixed content and
  also looks like "cannot connect".
- After a server change: pull to refresh for template or method changes; for `db/mobile.php` or `lang` changes,
  purge caches on the site, then log out and in again in the app (the handler list is cached in
  `tool_mobile/plugininfo` on the site and on the device).

## Reading failures in the app

Every app-runtime failure in this skill is silent: the web service returns 200, server tests are green, and the
console shows nothing unless you look in the right place.

1. Check something works at all (another plugin, the core activity next to yours) before debugging your code.
2. Open the browser's developer tools on the app tab: compile errors of your template and exceptions from your
   handler JavaScript are logged there by the app's compile service ("Error evaluating javascript").
3. Log from your handler JavaScript with `console.log()` and remove it afterwards; a `try` that swallows an
   exception is the usual reason for an empty view.
4. Compare the request the app sends (Network tab, `tool_mobile_get_content` payload) with your curl call: the app
   adds `userid`, `appid`, `appversioncode`, `appversionname`, `applang` and `appcustomurlscheme` to `args`.

## Behat for the app

Moodle app Behat runs app scenarios against a site with the app served locally
(https://moodledev.io/general/app/development/testing/acceptance-testing). It needs the app's Behat plugin
installed on the site and an app build; plan it as a separate CI job.

## Push notifications

The app receives the site's notifications through the `airnotifier` message output (`public/message/output/airnotifier`)
once that output is enabled with an access key from Moodle's push server, and the user has the app installed and
logged in. A plugin does nothing app-specific to send them:

1. Declare the message provider in `db/messages.php` and its strings.
2. Send with `message_send()`; set `contexturl` and `contexturlname` so a tap opens the right place, and
   `customdata` for data the app should get (core activities set `cmid` and `notificationiconurl`,
   `public/mod/assign/locallib.php:7272-7286`).
3. To handle a tap in your own app code, register a `CorePushNotificationsDelegate` click handler from `init`
   JavaScript (interface `CorePushNotificationsClickHandler` in the app's
   `src/core/features/pushnotifications/services/push-delegate.ts`).

Users choose per provider whether notifications reach the app (Preferences > Notification preferences, "Mobile"
column).
