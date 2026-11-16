---
name: moodle-security-audit
description: Use when reviewing or hardening Moodle plugin code for security, auditing a plugin's entry points, or responding to a vulnerability report. Covers require_login and require_capability, IDOR (context derived from the record), sesskey and CSRF, required_param and PARAM_* types, $DB placeholders and get_in_or_equal, output escaping (s, format_string, format_text, html_writer, Mustache triple braces, JS sinks), pluginfile and send_stored_file, uploads, \curl and SSRF, open redirects (PARAM_LOCALURL), secrets and \core\encryption, external functions (validate_context), dynamic forms, mobile methods and tasks. Skip when preparing a release or answering a Plugins directory reviewer (use moodle-release-preflight).
---

# Moodle Security Audit

## Overview

Moodle gives a plugin framework-level protection (the capability system, sesskey, `$DB` placeholders, output
escaping, the file API), but only where the plugin calls it. Most plugin vulnerabilities are a call that is
missing, or made on the wrong context. This skill is the broad checklist and the default recipes. The defect
classes that reviews caught in shipped plugins, with their greps, are in `moodle-release-preflight`.

## When to Use

- Reviewing a pull request or a plugin for security
- Hardening code before it is exposed to students, guests or the web
- Responding to a vulnerability report
- **Skip when:** preparing a release or submission, or answering a Plugins directory review
  (`moodle-release-preflight`); writing ordinary feature code (`moodle-plugin-development`)

## How to audit

1. **List every entry point first:** top-level `*.php` pages, `ajax/` scripts, external functions in
   `db/services.php`, mobile methods, dynamic forms, the `pluginfile` callback, `backup/` restore steps,
   scheduled and adhoc tasks, a filter's `filter()`. An entry point you did not list is one you did not audit.
2. **For each, answer three questions:** who is logged in (`require_login`), which context the action is in
   (derived from the record acted on), and which capability allows it.
3. **Trace each untrusted value from source to sink:** request parameters, web service and mobile arguments,
   restored and imported data, text other users wrote, and anything a client can edit (hidden fields, browser
   storage). A grep hit is not a finding until the trace shows no guard on the way.
4. **Rate by the lowest role that can exploit it.** Editing-teacher HTML behind a `RISK_XSS` capability is
   Moodle's accepted trust model; it becomes a finding when student input reaches it or the capability lacks the
   flag.

## Default recipe for a page script

```php
require(__DIR__ . '/../../config.php');

$id = required_param('id', PARAM_INT);                              // 1. Typed input.
$item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
$course = get_course($item->courseid);
$context = context_course::instance($course->id);                   // 2. Context from the record.

require_login($course);                                             // 3. Session, enrolment, course access.
require_capability('local/example:edit', $context);                 // 4. Authorisation.

$PAGE->set_url(new moodle_url('/local/example/edit.php', ['id' => $id]));
$PAGE->set_context($context);

if (optional_param('confirm', 0, PARAM_BOOL)) {
    require_sesskey();                                              // 5. CSRF, before any write.
    // ... write ...
}
```

Reading parameters and the record before `require_login()` is fine; doing anything with them (output, writes,
redirects to them) is not. `require_login($course)` also sets up `$PAGE` for the course, so it comes before
`$PAGE` output calls. `phpcs` warns when no login call follows `config.php` (`moodle.Files.RequireLogin`), but
it does not check the capability.

## 1. Authentication

| Call | Use |
|---|---|
| `require_login()` | Any logged-in user (guests auto-login if the site allows it) |
| `require_login($course)` | Logged in and able to enter the course |
| `require_login($course, false, $cm)` | Activity-level access, including visibility and availability |
| `require_login($course, false, $cm, true, true)` | The same for AJAX, mobile and web service code: throws instead of redirecting |
| `require_course_login($course)` | Course pages that guests and the front page may see |
| `require_admin()` | Site administrators only |

- AJAX scripts and helper endpoints (image, plot or file generators) need `require_login()` too. A valid
  session is not an authorised one.
- The second argument is `$autologinguest`: with the default `true`, a visitor is logged in as guest where the
  site allows it, so "logged in" can mean the guest account. Check `isguestuser()` or a capability guests lack
  before any write (`public/lib/moodlelib.php`, 5.3.0).
- A page with `NO_MOODLE_COOKIES` has no session, so it cannot check who the user is; it must not show or change
  anything per user.
- "Switch role to" applies in the course context only. To test a system-context gate, use a real account with
  that role (`moodle-field-lessons`).

## 2. Authorisation and IDOR

```php
// Bad: checks a site-level capability; the item belongs to a course the user may not see.
$item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
require_capability('local/example:view', context_system::instance());

// Good: the context comes from the object being acted on.
$item = $DB->get_record('local_example_items', ['id' => $id], '*', MUST_EXIST);
require_capability('local/example:view', context_course::instance($item->courseid));
```

- **Derive the context from the object, never from a URL or form parameter.** A submitted `courseid`, `cmid` or
  `contextid` lets the attacker choose where the check runs.
- **Bind child ids to the parent you authorised:**
  `$DB->get_record('local_example_choices', ['id' => $choiceid, 'itemid' => $item->id], '*', MUST_EXIST)`.
- **Never take the acting user from the client.** A web service that accepts `userid` for "my" data uses
  `$USER->id` instead.
- **`require_login()` is not authorisation.** Every page and web service function that does more than show users
  their own data names a capability. Sibling actions on the same object (edit, delete, react, pin) make the same
  checks as the main action (`moodle-release-preflight` class 1).
- **Write actions need a write capability**, with the right `riskbitmask` in `db/access.php` (`RISK_XSS` when
  what it writes is shown to others, `RISK_PERSONAL`, `RISK_CONFIG`, `RISK_DATALOSS`, `RISK_SPAM`). Never check a
  role shortname or `$USER->id == 2`; use `is_siteadmin()` or a capability.
- **Groups:** in separate-groups mode, filter lists and actions by `groups_get_activity_group()` unless the user
  has `moodle/site:accessallgroups`.

## 3. CSRF: sesskey

Every request that changes state needs a sesskey check, whatever its HTTP method: `require_sesskey()` (throws) or
`confirm_sesskey()` (returns a bool). A GET that writes is fired by an `<img src>` in any post an admin views.

- `moodleform` adds and checks the sesskey; `get_data()` returns null on a bad one.
- A raw HTML form carries `<input type="hidden" name="sesskey" value="{{sesskey}}">`, with the value from
  `sesskey()` in the template context.
- `core/ajax` calls send it automatically. A raw `fetch()` adds it from `core/config`:

```javascript
import Config from 'core/config';

const body = new URLSearchParams({sesskey: Config.sesskey, id: String(itemid)});
await fetch(`${Config.wwwroot}/local/example/ajax.php`, {method: 'POST', body});
```

The sesskey is a CSRF token, not the session id; a scanner flagging `?sesskey=` in URLs is a false positive
(https://moodledev.io/general/development/process/security/penetration-testing).

## 4. Input: typed parameters, never superglobals

```php
$id    = required_param('id', PARAM_INT);
$name  = optional_param('name', '', PARAM_TEXT);
$ids   = required_param_array('ids', PARAM_INT);
$back  = optional_param('returnurl', '', PARAM_LOCALURL);
```

- Use the narrowest type that fits: `PARAM_INT`, `PARAM_BOOL`, `PARAM_ALPHANUMEXT`, `PARAM_COMPONENT`,
  `PARAM_EMAIL`, `PARAM_LOCALURL`, `PARAM_TEXT` (tags stripped except multilang spans), `PARAM_NOTAGS`,
  `PARAM_CLEANHTML`. Test the type on real values: `PARAM_ALPHANUMEXT` strips `.`, `PARAM_USERNAME` strips `+`
  unless `$CFG->extendedusernamechars` is on (`public/lib/classes/param.php`, 5.3.0).
- `PARAM_RAW` accepts anything. Each use carries a comment saying why and where the value is escaped or bound;
  Plugins directory reviewers flag uncommented ones.
- `$_GET`, `$_POST`, `$_REQUEST` and `$_COOKIE` skip type coercion. No `phpcs` sniff flags them; grep for them.
- Formslib fields get their type from `$mform->setType()`. A `hidden` element's value is client-editable; use
  `setConstant()` or re-validate it.
- Values arrive in other ways too: web service and mobile arguments, restored `.mbz` data and imported files are
  input as well. See [reference/entry-points.md](reference/entry-points.md).

## 5. SQL: placeholders only

```php
$DB->get_records_sql('SELECT * FROM {local_example_items} WHERE name = :name', ['name' => $name]);

// Bad: an id list built by string joining.
$DB->get_records_sql('SELECT * FROM {local_example_items} WHERE id IN (' . implode(',', $ids) . ')');

// Good.
[$insql, $params] = $DB->get_in_or_equal($ids, SQL_PARAMS_NAMED);
$DB->get_records_sql("SELECT * FROM {local_example_items} WHERE id $insql", $params);

// LIKE: escape the user's text and let the DML build the operator.
$where = $DB->sql_like('name', ':pattern', false);
$DB->get_records_sql("SELECT * FROM {local_example_items} WHERE $where",
    ['pattern' => '%' . $DB->sql_like_escape($search) . '%']);
```

Column and sort names cannot be placeholders: check them against an allowlist
(`in_array($sort, ['name', 'timecreated'], true)`). Mobile `$args` and web service values are as untrusted as
request parameters.

## 6. Output: escape at the sink

| Function | Use |
|---|---|
| `s($str)` | Escape plain text for HTML content and attributes |
| `format_string($str, true, ['context' => $ctx])` | Short user text (names, titles): runs filters, escapes `&`, `<`, `>`, but not quotes |
| `format_text($html, $format, ['context' => $ctx])` | Rich text: runs filters and HTMLPurifier |
| `clean_text($html, FORMAT_HTML)` | HTMLPurifier only, no filters |
| `html_writer::tag('span', s($text), $attrs)` | Attributes are escaped; tag content is not |
| `{{var}}` / `{{{var}}}` in Mustache | Escaped / raw: raw only for HTML already produced by `format_text()` or a renderer |

- Pass `context` to `format_string()` and `format_text()`; it decides which filters run.
- `format_string()` is not safe inside an attribute, since it leaves quotes alone (`public/lib/classes/formatting.php`,
  5.3.0). Use `s()` there.
- **Core helpers that print text as HTML:** `html_writer::select()` labels, formslib labels and option texts,
  `core/modal` titles, toasts, `core/notification` and the `redirect()` message. Escape user data before passing
  it. The full list with its sources is in `moodle-release-preflight` class 2a.
- **JS sinks:** `innerHTML`, `insertAdjacentHTML`, `outerHTML` and jQuery `.html()` take only HTML rendered from a
  template (`Templates.renderForPromise()`) or `textContent` for plain text.
- **`noclean` and `'trusted' => true`** are for text written by users with `RISK_XSS` capabilities. Student text,
  LLM output and imported HTML never get them.

## 7. File serving and uploads

- Serve files through the `pluginfile` callback, never by path under `$CFG->dataroot`. The callback checks the
  context level, allowlists `$filearea`, calls `require_login()` and the capability, and checks that the item
  belongs to something the user may see. `pluginfile.php` authenticates the session; it does not authorise the
  plugin's files. Recipe: [reference/entry-points.md](reference/entry-points.md).
- `send_stored_file($file, 0, 0, $forcedownload, $options)` and `send_file()` serve inline unless told otherwise.
  Force download for user uploads unless the mimetype is validated media.
- Uploads go through a draft area and `file_save_draft_area_files()` with `maxfiles`, `maxbytes` and
  `accepted_types` set (`core_form\filetypes_util` for admin-configurable types). Never trust
  `$_FILES[...]['type']`.
- Working directories come from `make_temp_directory()` or `make_request_directory()`, which use
  `$CFG->directorypermissions` (`public/lib/setuplib.php`, 5.3.0); a literal `0777` is flagged in review.

## 8. Outbound HTTP and SSRF

```php
$curl = new \curl();
$response = $curl->get($url);
if ($curl->get_errno() || $curl->get_info()['http_code'] != 200) {
    throw new moodle_exception('fetchfailed', 'local_example');
}
```

- `\curl` applies `$CFG->curlsecurityblockedhosts` and `curlsecurityallowedport` through
  `\core\files\curl_security_helper`, and the site proxy (`$CFG->proxyhost`) (`public/lib/filelib.php`, 5.3.0).
  Raw `curl_init()` and `file_get_contents($url)` get neither. Never pass `ignoresecurity`.
- A server-side fetch of a URL a user supplied is SSRF unless it is admin-only or allowlisted. HTML handed to a
  PDF library fetches its `<img src>` on the server too.
- `clean_param($url, PARAM_URL)` checks the syntax, not the destination.

## 9. Secrets

- No tokens or keys in source, `version.php` or test fixtures. Store them as plugin settings
  (`admin_setting_configpasswordunmask`), read them with `get_config('local_example', 'apikey')`.
- `\core\encryption::encrypt()` and `decrypt()` protect a stored secret beyond the settings table.
- Mark function parameters that carry secrets with `#[\SensitiveParameter]` so they stay out of stack traces, as
  core's `hash_internal_user_password()` does.
- Send a site credential only to the host the admin configured, never to a per-item URL override.
- Never log secrets: `debugging("Token: $token")` and event `other` data end up in logs others can read.

## 10. Redirects

```php
$returnurl = optional_param('returnurl', '', PARAM_LOCALURL);
redirect($returnurl ? new moodle_url($returnurl) : new moodle_url('/local/example/index.php'));
```

`PARAM_LOCALURL` accepts only URLs on this site. `PARAM_URL` or the `Referer` header as a redirect target is an
open redirect.

## 11. Static analysis

`moodle-plugin-ci phpcs` (the moodle-cs standard) flags `eval`, backticks, `extract()`, `error_log()` and a missing
login call. It does not flag `unserialize()`, `call_user_func()`, superglobals, `PARAM_RAW`, missing capability
checks or missing frankenstyle prefixes. Use it, then grep.

```bash
G() { grep -rnE --include='*.php' --exclude-dir={vendor,thirdparty,node_modules,tests} "$@" .; }
G '\$_(GET|POST|REQUEST|COOKIE)\['                      # superglobals
G 'PARAM_RAW'                                           # each needs a reason
G 'unserialize\('                                       # needs allowed_classes => false
G "noclean|'trusted' *=> *true"                         # who writes that text?
G 'curl_init|file_get_contents\(.*https?:'              # bypasses \curl security
G 'get_records_sql|get_record_sql|execute\(' | grep -E '\$[a-z_]+\s*\.|"\s*\.\s*\$|\{\$'   # concatenated SQL
```

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `$_GET['id']` | No type coercion; type juggling | `required_param('id', PARAM_INT)` |
| SQL built by concatenation or `implode()` | SQL injection | Placeholders and `get_in_or_equal()` |
| `echo $row->name` | Stored XSS | `s()` or `format_string()` |
| `html_writer::tag('div', $usertext)` | Content is not escaped | `s($usertext)` |
| `format_string()` inside an attribute | Quotes break out | `s()` |
| No `require_login()` in an AJAX script | Anonymous access | Add it; or use an external function |
| Capability checked on a context from the request | The attacker picks the context | Context from the record |
| `require_login()` alone on a page that writes | Any account can act | `require_capability()` |
| `require_sesskey()` only on POST | A GET that writes is CSRF | Check every mutating branch |
| No capability check in `pluginfile` | Any logged-in user downloads | Check context, filearea, capability, item |
| `send_stored_file(..., false)` for uploads | Inline HTML runs in the viewer's session | Force download unless media |
| `unserialize($input)` | Object injection | JSON, or `['allowed_classes' => false]` |
| `file_get_contents($userurl)` or `curl_init()` | SSRF; blocked hosts and proxy ignored | `\curl` |
| `redirect(optional_param('next', '', PARAM_URL))` | Open redirect | `PARAM_LOCALURL` |
| `print_error()` | Fatal: removed after its final deprecation | `throw new moodle_exception(...)` |
| `$USER->id == 2` as an admin check | Wrong on most sites | `is_siteadmin()` or a capability |
| Access decided by a client header (`User-Agent`, `X-Forwarded-For`) | Headers are spoofable | Capabilities; `getremoteaddr()` for logging only |
| `md5()` or `sha1()` for a password | Weak hash | `hash_internal_user_password()` |

## Reporting vulnerabilities upstream

A vulnerability in Moodle core goes to the security issue form at https://moodle.org/security/report, or to a
Moodle Tracker issue with a security level set, never to a public issue or forum
(https://moodledev.io/general/development/process/security). A vulnerability in someone else's plugin goes to its
maintainer privately first.

## Reference files

| File | Read it when |
|---|---|
| [reference/entry-points.md](reference/entry-points.md) | The plugin has AJAX scripts, external functions, mobile methods, dynamic forms, a `pluginfile` callback, tasks or a filter, and you are auditing or writing their access checks |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md): token endpoint hardening, CORS for AJAX functions, REST API tokens and scopes, `\core_auth\validate_user`, the app deep-link auto-login setting, HTMLPurifier changes |

## References

- https://moodledev.io/general/development/policies/security
- https://moodledev.io/docs/apis/subsystems/output#escaping-content
- https://moodledev.io/docs/apis/subsystems/access
- https://moodledev.io/docs/apis/subsystems/files
- https://moodledev.io/docs/apis/core/dml#placeholders
- https://moodledev.io/general/development/process/security
- See also: `moodle-release-preflight` (review-found defect classes), `moodle-field-lessons` (escaping and
  authorisation small print), `moodle-web-services`
