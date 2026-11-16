# Extended security checklist

Read this when the plugin has request entry points (pages, AJAX or API scripts, external functions, mobile
methods, dynamic forms, `pluginfile`, restore, tasks) and classes 1 to 6 of `SKILL.md` are done.

Classes 1 to 6 are the defects that Plugins directory and external security reviews caught in shipped plugins.
This file widens the net. It comes from a static audit of several dozen widely installed third-party plugins;
each class below was found in more than one of them. Examples are described as patterns only.

Report each line of the [checklist](#checklist) as pass, fail (file:line) or N/A (reason). Where a line repeats a
finding already reported under classes 1 to 6, report it once.

## How to run it

1. **List every entry point** before you read any code: top-level `*.php` pages, `ajax/` and `api/` scripts,
   `classes/external/` with `db/services.php`, `db/mobile.php` with `classes/output/mobile.php`,
   `core_form\dynamic_form` subclasses, `*_pluginfile`, `backup/`, scheduled and adhoc tasks, and a filter's
   `filter()`.
2. **Trace every grep hit** from the request source to the sink, including guards earlier in the call chain. A
   hit is not a finding until you have done that.
3. **Rate by the lowest role that can exploit it:**
   - High: a student, guest or anonymous user can read or write other users' data, run script in another
     session, escalate, or run SQL or code on the server.
   - Medium: it needs a teacher or editing role to reach beyond their own course, or a plausible but
     non-default setting.
   - Low: admin-only paths, hardening, and lifecycle or privacy gaps.

   Editing-teacher HTML behind a `RISK_XSS` capability is Moodle's accepted trust model. It becomes a finding
   only when student input reaches it, or when the capability lacks the flag.

```bash
G() { grep -rnE --include='*.php' --exclude-dir={thirdparty,vendor,node_modules,build,tests} "$@" .; }
```

## A. Injection

- **SQL built from request input.**
  - Pattern: a mobile or web service argument, a comma-separated id list, or a filter value concatenated into
    SQL, including a value that picks a column name.
  - Look: `G '\$DB->(get_records?_sql|execute|get_field_sql|count_records_sql|[a-z_]+_select)\('`, then read
    each SQL string for interpolation. Mobile `$args` are never cleaned by a `PARAM_*` type.
  - Fix: placeholders, `$DB->get_in_or_equal()`, `clean_param($v, PARAM_SEQUENCE)`, and column-name
    allowlists.
- **`unserialize()` across a trust boundary**, which is object injection.
  - Typical sources: imported files, restored block configdata, question-attempt step data.
  - Look: `G 'unserialize\('`. moodle-cs does not flag it.
  - Fix: `unserialize($s, ['allowed_classes' => false])`, `unserialize_object()` for configdata, or JSON.
- **Restored or imported executable state.**
  - Pattern: restore or import writes a cached or compiled artefact that the runtime executes without
    re-running the validation the edit form applies.
  - Look: `G '\b(exec|shell_exec|system|passthru|proc_open|popen|eval)\s*\('`, and any `*cache*`, `compiled*`
    or `*code*` column restored verbatim.
  - Fix: clear such caches on restore so the runtime recomputes them.
- **Path traversal.**
  - Pattern: a file name from the request, a form or a remote service builds a filesystem path.
  - Fix: `clean_param($n, PARAM_FILE)`, then `basename()`, then check that the resolved path stays inside the
    target directory.
- **Spreadsheet formula injection.**
  - Pattern: user strings written to CSV or XLSX cells, or placed inside `=HYPERLINK()`.
  - Fix: prefix cells that start with `= + - @`, a tab or a carriage return with `'`, and never build formulas
    from user data.

## B. Output (XSS)

- **`noclean` or `'trusted' => true` on student-influenced text.**
  - Typical cases: program output, report cells, HTML pulled from another module or block.
  - LLM output counts as student-influenced. Once it is pre-filled into a teacher's editor and saved, core
    renders it as trusted.
  - Look: `G "noclean|'trusted'\s*=>\s*true"`, and ask who writes each text.
- **Raw values in tag content or in `style`, `alt`, `href` or `tel:` attributes.**
  - Look: triple-stache `{{{ }}}` fed by data, `html_writer::tag()` content without `s()`, string-built HTML.
  - `format_string()` escapes `&`, `<` and `>` but not quotes (`public/lib/classes/formatting.php`, 5.3.0), so
    it is not safe inside an attribute.
  - Denylist "sanitisers" fail; use HTMLPurifier (`clean_text()`) or `s()`.
- **DOM sinks.** `innerHTML` fed by string-built HTML or by replayed `localStorage` content. Browser storage is
  shared by everyone who uses that browser.
- **Uploads served inline.** `send_stored_file($f, ..., false)` for files students upload, with no
  `accepted_types`. Fix: force download unless the file is proven media, and add `RISK_XSS` to the upload
  capability.
- **Restore and import write fields verbatim** that the form would have cleaned:
  - URLs with `javascript:`
  - names that end up in `style` attributes
  - enumerations outside the form's set
  - grade fractions above 100%
  - role ids from another site

## C. CSRF

- **A state change on GET with no `require_sesskey()`.** An `<img src>` in a forum post, viewed by an admin,
  fires it.
  - Typical cases: import-by-URL, edits made from admin tools, approvals, attempt and response deletion,
    message sending, heavy recalculation jobs.
  - Look: find each writing branch and `G "optional_param\('(action|delete|confirm|do|op)'"`.
- **The sesskey leaking into content.** A filter or template expands a `{sesskey}`-style token inside
  student-authored text, which hands the viewer's token to the author's link.

## D. Authorisation and trust boundaries

- **IDOR.** The most common class.
  - The capability is checked on the URL's cm, but the record id comes from the request and is never bound to
    that cm.
  - Typical ids: child-record ids (columns, choices, items), block instance ids, a web service `courseid`.
  - `setDefault()` on a hidden element can be edited by the client; `setConstant()` cannot.
  - Fix: look up `['id' => $x, '<parent>id' => $instance->id]` with `MUST_EXIST`.
- **Client-supplied user identity.** A web service or mobile handler takes `userid` or a response id from the
  client, so a student can forge, overwrite or wipe other users' data. Fix: use `$USER->id`.
- **An entry point with no login or capability check.**
  - a preview or embed branch that skips `require_login`
  - an AJAX endpoint that never checks access to the target block or cm
  - mobile content methods (core does not check access for these)
  - helper endpoints (loaders, image or plot generators) with no login
  - write actions gated on a read capability, and role-shortname checks
  - dynamic forms: never trust the client's `contextid` in `get_context_for_dynamic_submission()`
- **SEPARATEGROUPS and visibility bypassed.**
  - Typical cases: overview pages and queues that ignore groups; hidden profile fields or auth methods exposed
    as group names; hidden course names; "anonymous" posts that carry the author's id in the web service JSON.
  - Look: `G 'groups_get_activity_group|SEPARATEGROUPS|accessallgroups'`.
- **Membership driven by a field users can edit themselves.** A student edits their own profile field and joins
  a cohort or group.
- **Messaging bypasses.** `message_send()` to a recipient the sender chose, without
  `\core_message\api::can_send_message()`. Every action that reaches another user (a reaction, a pin, a
  mention) applies the same blocking and contact-privacy rules as sending a message.
- **State machines.**
  - Typical cases: negative quantities, replayable approvals, races, locks enforced only in the browser, the
    same work double-counted.
  - Content edited after it was reviewed or submitted, without a server-side lock or a re-review.

## E. Outbound requests and secrets

- **SSRF.**
  - Typical sources: content tags that fetch a URL, import-by-URL, template HTML rendered by a PDF library.
    TCPDF fetches `<img src>`, including local paths.
  - Look: `G 'new curl|download_file_content|file_get_contents\(.*http|curl_init|writeHTML'`.
  - Fix: make the fetch admin-only with an allowlist, never loosen `curlsecurityblockedhosts`, and resolve
    images to stored files yourself.
- **A site API key sent to a per-item endpoint override.** Never send site credentials to a host that was not
  configured.
- **Open redirects** (`PARAM_URL` or `Referer` used as a redirect target) and unauthenticated mail or AI relays.
  Fix: `PARAM_LOCALURL`, plus login and per-user rate limits.
- **Undeclared data egress.** Analytics scripts on the login and reset pages, or code and names sent to an
  external service, while the privacy provider is a `null_provider`.

## F. Resource abuse

- Typical cases:
  - an unauthenticated endpoint that compiles and caches per request key, which fills the disk
  - quadratic scans, and author regexes run on unbounded student input
  - throttles kept in `$SESSION`
  - uncapped stored versions or uploads
- Fix: validate the key against real records first, bound loops and stored versions, and key rate limits on the
  user and the site.

## G. Lifecycle, privacy, defaults

- **Privacy:**
  - a `null_provider` despite stored preferences or files
  - files missing from export and delete
  - no `core_userlist_provider`
  - erasing one user deletes everyone's files, or deletes the activity itself
- **Reset** does not clear the data, deletes by the wrong key, or cron undoes it.
- **Uninstall or course deletion** leaves locked memberships and orphan rows behind.
- **Raw deletes that bypass core APIs and events**, or that use the wrong key column.
- **Dangerous defaults:** bulk tools that pre-select everything, and filters enabled site-wide at install.
- **Capabilities missing `RISK_XSS`, `RISK_PERSONAL`, `RISK_CONFIG` or `RISK_DATALOSS`.**
- **Debug parameters** that show SQL to non-admins.
- **Spoofable conditions:** user-agent detection used as access control. It is advisory only, especially on AJAX
  and web service requests, which carry no browser headers you can trust.

## Checklist

**Entry points and authorisation**
- [ ] Every page calls `require_login` with the right course and cm before output or a write, with no `popup` or `embed` bypass.
- [ ] Every page and web service function that does more than show the user their own data names a capability; `require_login()` alone is not authorisation.
- [ ] Every write needs a write capability. No role-shortname checks.
- [ ] Sibling actions on the same object (edit, react, pin, delete) make the same checks as the main action.
- [ ] External functions call `validate_context()` and `require_capability()` on a context derived from the record.
- [ ] Every mobile method checks access itself and casts `$args`.
- [ ] Dynamic forms re-derive their context on the server.
- [ ] AJAX and API scripts check the specific target instance.
- [ ] `pluginfile` checks the cm, an allowlisted filearea, and whether the user may see that item.

**Client-supplied ids and values**
- [ ] Every request id is scoped to the authorised parent, `MUST_EXIST`.
- [ ] Hidden ids use `setConstant()` or are re-validated; select values are re-checked against the offered set.
- [ ] No client `userid`, `rid` or `submissionid` decides whose data is touched.
- [ ] Numbers are range- and sign-checked on the server; UI-only limits are also enforced there.
- [ ] Every request parameter has the narrowest `PARAM_*` type that fits; each `PARAM_RAW*` has a reason.
- [ ] Status transitions are checked against the current state; content cannot change after review or submission without re-review; races are guarded.

**CSRF**
- [ ] Every mutating branch has `require_sesskey()` or goes through moodleform `get_data()`.
- [ ] No filter or template expands a secret into user-authored content.

**Injection**
- [ ] No request, `$args` or imported value is interpolated into SQL; IN lists use `get_in_or_equal()`; columns are allowlisted.
- [ ] No `unserialize()` without `allowed_classes`.
- [ ] No exec or eval reachable from a request; restored compiled caches are cleared.
- [ ] File paths are `PARAM_FILE` plus `basename()` plus a containment check.
- [ ] Exports neutralise leading `= + - @`.

**Output**
- [ ] No `noclean` or `trusted` on student- or LLM-influenced text.
- [ ] Tag content and string-built HTML are `s()`-escaped; no raw attributes; no `format_string()` inside attributes.
- [ ] Every `{{{ }}}` is traced to safe HTML.
- [ ] JS DOM sinks, modal titles, toasts and notifications are fed only by template-rendered HTML or lang strings.
- [ ] Non-`RISK_XSS` uploads are force-downloaded unless proven media.
- [ ] Sanitisers are allowlists.

**Backup, restore, import**
- [ ] `process_*` applies the form's cleaning; URLs reject `javascript:`.
- [ ] Cross-course and cross-site ids are remapped or dropped.
- [ ] Importers apply the edit form's validation.

**Outbound and secrets**
- [ ] No server fetch of a user URL, including through a PDF or HTML renderer, unless it is admin-only and allowlisted.
- [ ] Keys go only to the configured host.
- [ ] Redirects are `PARAM_LOCALURL`; mail and AI endpoints need login and are rate-limited.
- [ ] Every external flow is declared in `get_metadata()`.

**Messaging and visibility**
- [ ] Message recipients are computed on the server, and `can_send_message()` is honoured by every action that reaches another user.
- [ ] SEPARATEGROUPS is respected; hidden courses, fields, auth methods and anonymous authors do not leak, including in web service payloads.
- [ ] No membership is driven by self-editable fields.

**Resource use**
- [ ] Unauthenticated endpoints validate keys before caching.
- [ ] Loops, regexes and stored versions are bounded; throttles are not session-scoped; heavy jobs need sesskey and a capability.

**Lifecycle and privacy**
- [ ] The provider covers every table, preference and file area, includes `core_userlist_provider`, and one user's erasure touches only that user.
- [ ] The reset triad clears the data, and cron does not undo it.
- [ ] Course deletion and uninstall clean up, including the plugin's user preferences.
- [ ] Bulk-destructive tools default to nothing selected and use core APIs.
- [ ] Capabilities carry the right `riskbitmask`.
- [ ] No debug parameter exposes internals.
- [ ] No access decision rests on the User-Agent or another client header.
