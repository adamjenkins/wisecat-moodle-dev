# Plugins directory review checks

Read this when the plugin is about to be submitted to the Moodle Plugins directory (a first submission or a new
version), or when a reviewer has opened an issue on it and you are fixing what it reports.

Each section is headed with the ID of the `SKILL.md` check it serves. Each is one kind of finding that Plugins directory reviewers raised on real submissions, none of which
`moodle-plugin-ci` caught. Each gives what is flagged, a command that detects it, the fix, and what answer was
accepted. Run the commands from the plugin's root directory. Set the component once:

```bash
c=local_myplugin          # the full component name
short=${c#*_}             # myplugin
```

Reviews give each finding a priority (blocker, high, medium, low), and some are marked as approval blockers.
The licence-file and ZIP-root-folder findings are the most common of all; they are checks on the built ZIP and
belong to `moodle-plugin-release`. The repository half takes one command: `git ls-files --error-unmatch LICENSE`
must succeed in the plugin root (the full licence text, committed before the tag).

## 6a. Missing language strings (high)

Flagged: a string that the plugin's code or core asks for is not in `lang/en/<component>.php`. The reviewers' tool
reports it as a missing required string with the key and component.

Why CI misses it: `moodle-plugin-ci validate` asks only for `pluginname` (for a filter, only `filtername`; for an
activity, `modulename` or `pluginname`, plus `<name>:addinstance`; read in the moodle-plugin-ci 4.5 source).
Strings that core builds from a convention are not checked at all.

Keys core asks for by convention (read in the 5.3.0 source):

| Key | Who asks | Source |
|---|---|---|
| `pluginname` | every plugin's display name | `public/lib/classes/plugininfo/base.php` |
| `filtername` | a filter's display name in core; the Plugins directory's scripted check also asks a filter for `pluginname`, so ship both | `public/lib/classes/plugininfo/filter.php` |
| `modulename`, `modulenameplural` | activity names in course pages, reset and recent activity | `public/course/reset_form.php`, `public/course/recent_form.php` |
| `pluginadministration` | an activity's settings navigation node | `public/lib/classes/navigation/settings_navigation.php` |
| `cachedef_<area>` | one per definition in `db/caches.php` | `public/cache/classes/definition.php` |
| `messageprovider:<name>` | one per provider in `db/messages.php` | message preferences page |
| `<name>:<cap>` for capability `<type>/<name>:<cap>` | `get_capability_string()` | `public/lib/accesslib.php` |
| `choosereadme` | a theme's description in the theme selector | `public/admin/amd/src/themeselector/preview_modal.js` |
| every `privacy:metadata*` key the provider names | the privacy registry | `classes/privacy/provider.php` |

Command: collect every key the plugin names and every convention key, then look each up.

```bash
lang="lang/en/$c.php"
{
  grep -rhoE "(get_string|new lang_string)\('[A-Za-z0-9_:./-]+', *'$c'" --include='*.php' . | cut -d"'" -f2
  grep -rhoE "\{\{#str\}\} *[A-Za-z0-9_:./-]+, *$c" --include='*.mustache' . | sed -E 's/^\{\{#str\}\} *([^,]+),.*/\1/'
  grep -rhoE "getString\('[A-Za-z0-9_:./-]+', *'$c'" amd/src 2>/dev/null | cut -d"'" -f2
  grep -hoE "^    '[a-z0-9_]+' *=> *(\[|array\()" db/caches.php 2>/dev/null | cut -d"'" -f2 | sed 's/^/cachedef_/'
  grep -hoE "^    '[a-z0-9_]+' *=> *(\[|array\()" db/messages.php 2>/dev/null | cut -d"'" -f2 | sed 's/^/messageprovider:/'
  grep -hoE "^    '[a-z]+/[a-z0-9_]+:[a-z0-9_]+' *=>" db/access.php 2>/dev/null | cut -d"'" -f2 | sed -E 's|^[a-z]+/||'
  grep -rhoE "'privacy:metadata[A-Za-z0-9_:]*'" classes/privacy 2>/dev/null | tr -d "'"
  echo pluginname
} | sort -u | while read -r k; do
  grep -qF "\$string['$k']" "$lang" || echo "missing: $k"
done
```

Each `missing:` line is a finding. Add the type-specific keys from the table by hand (`filtername`,
`modulename`, `modulenameplural`, `pluginadministration`, `choosereadme`). The greps assume the usual layout
(four-space indentation in `db/*.php`, literal keys); keys built at runtime and `getStrings([{key, component}])`
calls need a read. Fix: add the string. A string added under the wrong key still prints `[[key]]`.

## 6b. Global names without the frankenstyle prefix (high, approval blocker)

Every global function, global class and `define()`d constant takes the frankenstyle prefix, including helpers in
top-level pages and `cli/` scripts, which is where they hide. For `mod_`, core's prefix is the bare module name, so
set `c` to that.

```bash
c=local_myplugin
grep -rnE '^(abstract |final )?(function|class|interface|trait) +[A-Za-z_0-9]+' --include='*.php' \
    --exclude-dir=classes --exclude-dir=tests --exclude-dir=thirdparty --exclude-dir=vendor . \
    | grep -vE ":(abstract |final )?(function|class|interface|trait) +(xmldb_)?${c}_"
grep -rnE "^ *define\('" --include='*.php' --exclude-dir=tests --exclude-dir=thirdparty --exclude-dir=vendor . \
    | grep -vE "define\('(CLI_SCRIPT|AJAX_SCRIPT|NO_MOODLE_COOKIES|NO_DEBUG_DISPLAY|READ_ONLY_SESSION|MOODLE_INTERNAL)'|define\('$(echo "$c" | tr a-z A-Z)_"
```

Each line printed is a finding or needs a reason. Names core dictates are not findings: `block_<name>`,
`backup_*` and `restore_*` classes in `backup/moodle2/`, `mod_<name>_mod_form`, `mod_<name>_core_calendar_*`,
`assign_submission_<name>` and `assign_feedback_<name>`, and `<filter>_filter_local_settings_form`. No output
with exit status 1 is the pass; check that `grep` itself ran. Fix: rename to `<component>_<name>()`, or move the
code into a class under `classes/`.

`phpcs` checks function names for lower case only (`moodle.NamingConventions.ValidFunctionName`), so CI stays
green.

Accepted fix: rename to `<component>_<name>()`, and search for siblings of the same mistake in other scripts
before replying. Better still, move the helper into a class under `classes/`.

## 1b. Pages that need only a login (medium)

Flagged: pages (and the web service behind them) that call `require_login()` and nothing else, so any account
can upload, share or publish.

Why CI misses it: `phpcs` checks only that some login call follows `config.php`
(`moodle.Files.RequireLogin`).

Command: list page scripts with a login call and no capability check.

```bash
for f in $(grep -rlE --include='*.php' --exclude-dir={classes,tests,db,lang,backup,vendor,thirdparty} \
        'require_(course_)?login\(' .); do
    grep -qE 'require_capability|has_capability|require_admin|admin_externalpage_setup' "$f" || echo "$f"
done
```

Each file printed needs a capability or a written reason (a page that shows the user only their own data). Fix:
add a capability in `db/access.php` with the right `riskbitmask` (`RISK_SPAM` or `RISK_XSS` for content others
see), call `require_capability()` on the page and in the web service, and hide the entry links without it.

## 1c. A rule applied to one action but not its siblings (medium)

Flagged: the main action (sending a message) applied a rule (blocking, contacts-only privacy, a disabled
conversation), and two secondary actions on the same object (reacting, pinning) did not, although the
documentation said the rule applied. The other user saw the result with the actor's name.

No grep finds this. For every write action, list the checks its siblings make on the same object, and compare.
Where the main action calls a shared check, every sibling calls it too, and the UI hides the control when it
fails. Add one PHPUnit test per action for the denied case. Moodle's own rule for messaging is
`\core_message\api::can_send_message()` and `\core_message\api::is_blocked()`.

## 6c. `PARAM_RAW` where a narrower type fits (medium)

Flagged: inputs read as `PARAM_RAW` or `PARAM_RAW_TRIMMED` although a narrower type exists, even behind sesskey
and a capability, and even when the value is escaped on output.

Command: `grep -rnE 'PARAM_RAW' --include='*.php' --exclude-dir={tests,vendor,thirdparty} .`

Each hit gets the narrowest type that fits (`PARAM_TEXT`, `PARAM_NOTAGS`, `PARAM_ALPHANUMEXT`,
`PARAM_COMPONENT`, `PARAM_INT`, `PARAM_EMAIL`) or a one-line comment saying why raw input is needed and where it
is escaped. Check a suggested type before you apply it: `PARAM_USERNAME` strips `+` unless
`$CFG->extendedusernamechars` is on, and `PARAM_ALPHANUMEXT` strips `.`, so `5.2` becomes `52`
(`public/lib/classes/param.php`, 5.3.0). A kept `PARAM_RAW` with its reason stated was accepted.

## 6d. Directories created with a literal mode (medium) and temp files outside the File API (low)

Flagged: `mkdir($dir, 0777, true)`, which ignores the site's `$CFG->directorypermissions`.

Command: `grep -rnE '\bmkdir\(' --include='*.php' --exclude-dir={tests,vendor,thirdparty} .`

Fix: use core's helpers, which create directories with `$CFG->directorypermissions`
(`public/lib/setuplib.php`, 5.3.0):

```php
$dir = make_temp_directory('local_myplugin/import');   // Under $CFG->tempdir, kept across requests.
$dir = make_request_directory();                       // Removed at the end of this request.
$dir = make_writable_directory($CFG->dataroot . '/local_myplugin');
// If you must call mkdir(), pass the site mode.
mkdir($path, $CFG->directorypermissions, true);
```

## 4d. Course-scoped data with no backup and restore (medium)

Flagged: tables keyed by course (and user) but no `backup/moodle2/` code. For an activity module a missing
backup is an approval blocker; for other types it is a question.

Command: `grep -nE 'NAME="(courseid|course)"' db/install.xml; ls backup/moodle2 2>/dev/null`

For each course-keyed table decide: copied with the course, or not. Implement backup and restore for data that
belongs to the course content. For operational or historical records that must not travel with a course,
write the reason in the README (deleted with the course, covered by the privacy provider) and give it as the
answer. That reasoned "no" was accepted without a code change. Backup recipes: `moodle-plugin-development`.

## 6e. Outbound HTTP that ignores the site proxy (medium)

Flagged: raw `curl_init()` instead of Moodle's `\curl`, so `$CFG->proxyhost` is never used and the feature fails
silently on a site that reaches the internet only through a proxy.

Command: `grep -rnE 'curl_init|file_get_contents\(.*https?:|fsockopen' --include='*.php' --exclude-dir={tests,vendor,thirdparty} .`

Fix: use `new \curl()`, which applies the proxy settings and core's `curl_security_helper` blocked hosts and
ports (`public/lib/filelib.php`, 5.3.0). If raw cURL is a deliberate choice (address pinning, a size cap), say
in the setting's description that the site proxy is not used. Admins read the settings page, not the README.
The same goes for any limitation the README states about a feature (what it never does, what it needs, where
data goes): it also belongs in that feature's setting description, `<setting>_desc` in the lang file. The
finding was raised although the README already said it.

## 6f. Database queries on a hot path (medium)

Flagged: a filter that ran one query per ancestor context on every `format_text()` and `format_string()` call.
Core calls each active filter's `setup()` for every `format_text()` call, and for every `format_string()` call
on a site that filters all strings (`public/lib/classes/formatting.php` calls `setup_page_for_filters()`,
5.3.0), so the cost is paid on every page, even when the filter changes nothing.

Command: no grep. Count queries around the hot path in a PHPUnit test and assert a ceiling:

```php
$before = $DB->perf_get_queries();
foreach ($contexts as $context) {
    format_text('Plain text', FORMAT_HTML, ['context' => $context]);
}
$this->assertLessThanOrEqual(5, $DB->perf_get_queries() - $before);
```

Fix: resolve each context once per request (a static array keyed by context id, or a MUC request cache), and
reuse what core already loaded (`$this->localconfig` in a filter). Caching recipes: `moodle-performance`.

## 6g. Minor gates

- `error_log()` in a best-effort `catch` is flagged by `phpcs`. Prefer silent handling, `debugging()` or an
  event; if kept, document why and add the `phpcs:ignore`.
- Scaffolding left in file headers (a generator's default `@copyright` holder, `TODO` package names): grep for
  them.
- `version.php` `$plugin->requires` is not below the lowest branch in `$plugin->supported`.
- **Test helpers in production code.** `moodleform::mock_submit()` replaces `$_POST` and `$_FILES` (and `$_GET`
  for a GET form); code that uses it outside tests saves and restores all of them in a `finally`. Reflection into
  protected core members needs a test that fails when they change.
- **Admin-facing messages in literal English** (validation problems, import reports) are flagged. Use lang
  strings with placeholders; two messages share a string only when its `{$a}` means the same in both.
- **Timezones:** another user's raw `timezone` field may be `99` ("server default"), and
  `core_date::get_user_timezone(99)` resolves to the viewer's zone (`public/lib/classes/date.php`, 5.3.0); use
  `core_date::get_server_timezone()` for that case. JS that converts wall-clock time by diffing offsets is off by
  the DST amount inside a transition window.
- **"Is X required?" has two authorities:** the core code path (what breaks) and the moodledev.io plugin-type and
  contribution docs (what a reviewer demands). A core plugin omitting something is not a licence to omit it.

## Answering a review

How to reply on the reviewer's issue (naming the fixing release, a reasoned no, checking a suggested fix before
applying it) is in `moodle-plugin-release`. For the code side, two things from the sections above:

- Look for the same mistake elsewhere in the plugin before answering; reviewers report one instance.
- A precise reason for not making a suggested change is an acceptable answer (seen accepted for `PARAM_RAW`
  kept with a stated reason, section 6c, and for data deliberately left out of backup, section 4d).
