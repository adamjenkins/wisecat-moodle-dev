---
description: Use when about to tag a Moodle plugin release, submit it to the Moodle Plugins directory, fix a code finding a Plugins directory reviewer raised, or send the plugin for an external security review. A pre-release audit of the defect classes reviews caught in shipped plugins despite green CI: client-trusted ids and limits, require_login() without a capability, sibling actions that skip a rule, frozen form fields, unescaped output sinks, inline-served uploads, unclean restore and imports, settings read by name, privacy drift, reset and uninstall gaps, vacuous tests, missing frankenstyle prefixes, missing lang strings, PARAM_RAW, mkdir 0777, raw cURL, and an extended checklist (unserialize, IDOR, CSRF, noclean, SSRF, group leaks). Skip when writing new feature code (moodle-plugin-development), reviewing code for security with no release at stake (moodle-security-audit), finishing an ordinary task (moodle-definition-of-done), or building the ZIP, tagging and replying to the reviewer (moodle-plugin-release).
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
# Moodle Release Preflight

## Overview

A pre-release self-audit of the defect classes that Plugins directory reviewers and external security reviews
have repeatedly found in shipped Moodle plugins after `moodle-plugin-ci` passed. The goal is to find the next
instance before a reviewer does. It is narrower than `moodle-security-audit` and empirical: each class was seen
in a review, and each comes with a check and a fix. Run both before a release; they overlap at the sinks.

## When to Use

- Before tagging a release or uploading a version to the Moodle Plugins directory
- Before sending a plugin to an external security or code review
- When a Plugins directory reviewer has opened an issue and you are fixing the code and looking for the same
  defect elsewhere (how to reply is in `moodle-plugin-release`)
- Checking a change that touches request handling, uploads, output, restore, privacy or course reset before it
  goes into a release
- **Skip when:** writing new feature code (`moodle-plugin-development`), doing a broad security review
  (`moodle-security-audit`), or building, tagging and uploading the release itself (`moodle-plugin-release`)

## What green CI does not prove

`moodle-plugin-ci` tests the git checkout with the plugin's own tests. None of these is caught by it (read in
the moodle-plugin-ci 4.5 and moodle-cs 3.7 source, not run):

- **The ZIP.** CI installs from the checkout. The licence file and the ZIP's root folder, the two most common
  review findings, are never seen. Check the built ZIP with `moodle-plugin-release`.
- **Most required strings.** `validate` asks for `pluginname` (a filter: `filtername` only; an activity:
  `modulename` or `pluginname`, plus `<name>:addinstance`). `cachedef_*`, other capability strings and message
  provider strings are not checked.
- **Frankenstyle prefixes.** `validate` checks table names; `phpcs` checks global function names for lower case
  only. A missing prefix is an approval blocker.
- **Authorisation and parameter types.** `phpcs` checks that a login call follows `config.php`, not that a
  capability is required; no sniff flags `$_GET`, `$_REQUEST` or `PARAM_RAW`.
- **Privacy compliance.** Core's `test_all_providers_compliant` is not part of the plugin's PHPUnit run, so a
  missing provider passes CI (`moodle-privacy-gdpr`).
- **Empty tests.** `phpunit` and `behat` over an empty `tests/` pass. `phpmd` always exits 0.

## How to run it

Scope to the changed files, or the whole plugin for a release. The audit has seven classes, and every check in
them has its own ID (`1a` to `7j`), listed in order under **Report format**. For each check: run it, report pass,
fail or N/A with a reason, and cite evidence (file:line, grep output, a test name). "Looks fine" is not a pass.
The deliverable is the report; do not fix unless asked.

**Triage by plugin shape first,** from the file tree, not the prefix:

- **Editor (`tiny_`, `atto_`), filter, block, theme**: usually no request handlers, uploads, restore or stored
  data. Classes 1 and 3 are typically N/A, and so are 2b, 4b, 4c and 4d; focus on 2a, 4a, 5a and class 6. Prove
  N/A with a grep; do not assume.
- **`mod_`, `assignsubmission_`, `assignfeedback_`, anything with an upload endpoint, external functions or its
  own tables**: run classes 1 to 6, then 7.
- **`local_`, `tool_`, `report_`**: a `local_` with an AJAX endpoint and a table is activity-shaped (run all); a
  passive one is editor-shaped. A tool whose admins author content or import files that other users see runs 3b.

```bash
grep -rlnE "required_param|optional_param|send_(stored_)?file" --include='*.php' . ; ls backup db/install.xml 2>/dev/null
```

The positive model for classes 1 and 2b: one shared helper per plugin that loads the instance from the URL id,
calls `require_login()` and `require_capability()` (or `validate_context()` in a web service), and re-scopes every
client-supplied id to that instance.

## 1. Trust boundary: never trust what the client sends

### 1a. Submitted ids and values are re-validated

**Seen in reviews:** a report plugin took the target course from a hidden form field, and its async grade-push
task never re-checked the capability: a cross-course gradebook write. An activity trusted a client-sent "type".
Another left one id in a `<select>` un-revalidated against the menu that built it.

Check:
- Grep for request values that drive authorisation, storage or a privileged action: `required_param`,
  `optional_param`, `addElement('hidden'`, `$data->` fields from a form, external-function parameters.
- Is authorisation derived from the URL or context id, not the submitted one?
- Is every submitted id re-validated against the allowed set: the records that built the select, or an
  instance-scoped query?
- Is the capability re-checked at the async sink (scheduled or adhoc task, service call)? A tampered stored
  value executes later.

```php
$cm = get_coursemodule_from_id('myplugin', $cmid, 0, false, MUST_EXIST);
$context = context_module::instance($cm->id);
require_login($cm->course, false, $cm);
require_capability('mod/myplugin:grade', $context);

$options = $DB->get_records_menu('myplugin_accounts', ['instanceid' => $cm->instance], '', 'id, name');
if (!array_key_exists($data->accountid, $options)) {
    throw new moodle_exception('invalidaccount', 'mod_myplugin');
}
```

### 1b. `require_login()` is not authorisation

**Seen in reviews:** share and upload pages, and the web service behind them, called only `require_login()`, so
any account could upload files that a task then parsed. Each page and web service function that does more than
show users their own data names the capability it requires, with a `riskbitmask`, and the UI hides the link
without it. Command and fix: [reference/directory-review-checks.md](../moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md)
section 1b.

### 1c. Sibling actions make the same checks as the main action

**Seen in reviews:** sending a message applied blocking and contacts-only privacy; reacting to and pinning a
message on the same conversation checked only membership. A blocked user could still react, and the other user
saw it with their name. No grep finds this: for each write action, list the checks its siblings make on the same
object and compare. Where the main action calls a shared check, every sibling calls it, and a PHPUnit test per
action covers the denied case.

### 1d. Client-side-only limits are advisory

**Seen in reviews:** maximum duration and size enforced only in the browser; a direct POST ignored both. For
each limit (size, duration, count, rate) grep the server endpoint for a matching guard. If the only enforcement
is in `amd/src/*.js`, it is bypassable. Enforce it on the server: `get_user_max_upload_file_size()`, a duration
probe, a `$DB->count_records()` gate.

### 1e. Two roles writing the same state value into one column

**Seen in reviews:** an owner-facing visibility toggle reused the status value moderators used for a takedown,
so authors could silently undo moderation. The readers of the column had been checked; the writers had not.

For every status, enum or flag column the change starts writing, grep every other writer:
`grep -rnE "set_field\(.*'status'|update_record|'status' *=>" --include='*.php' .`. If two privilege levels can
put a row into the same state, give each actor a distinct value (`hidden_by_moderator`, which the author setter
refuses to touch) or store the actor on the row, and confirm the privileged action is still reversible in the UI.

### 1f. Building a core form's data in code skips its freezes

**Seen in reviews:** a plugin read a core form's defaults, overlaid its own values and saved without posting the
form. Core had `hardFreeze()`d capability-gated fields for that user (`course_edit_form` freezes `visible` and
`downloadcontent`, `public/course/edit_form.php`, 5.3.0), and the overlay set them anyway; `create_course()` checks
no capability of its own. Wherever code fills a core form's data itself, skip every element where
`$mform->getElement($name)->isFrozen()` and take the pinned value from `_constantValues`. Test with a user who
lacks the gating capability.

### 1g. The question engine processes every slot the post names

`$quba->process_all_actions($timenow, $postdata)` processes the slots named in `$postdata['slots']`, or every
slot in the usage if that key is absent (`public/question/engine/questionusage.php`, 5.3.0), so a client-shaped
`$postdata` can grade every question in one request. Filter `$postdata` to the allowed slots'
`$quba->get_field_prefix($slot)` keys and set `$postdata['slots']` yourself. A regression test must include
`:sequencecheck` plus a hostile `-submit`, or it passes vacuously.

## 2. Output: escape at the sink, force-download uploads

### 2a. Escape at the output sink

**Seen in reviews:** a label built with `html_writer::tag('span', $label)` (tag content is not escaped), then
assigned through `innerHTML`: stored XSS.

Check:
- `grep -rnE "html_writer::(tag|div|span|link|select)\(" --include='*.php' .`: is the content argument a stored
  or user value without `s()`, `format_string()` or `format_text()`? Attributes are escaped; content is not.
  `html_writer::select()` option labels go into tag content too (`select_option()`,
  `public/lib/classes/output/html_writer.php`, 5.3.0). Assert on the `>label</option>` position in a test, not on
  a page substring.
- **Formslib prints labels as HTML:** element labels, `select` option texts and `advcheckbox` texts reach core's
  form templates as `{{{label}}}`, `{{{text}}}` and `{{{.}}}` (`public/lib/form/templates/`, 5.3.0). Stored or
  authored text passed to any of them needs `s()`.
- **Messages are HTML:** `core/modal` titles (`setTitle()` uses `.html()`, `public/lib/amd/src/modal.js`), toasts,
  `core/notification` strings, and `redirect($url, $message)`, whose message is rendered by
  `notification_base.mustache` as `{{{ message }}}` (5.3.0). Pass lang strings; put user data through `s()` on the
  server or `textContent` in JS.
- `grep -rnE "innerHTML|insertAdjacentHTML|outerHTML|dom\.create\(|setContent\(" amd/src`, then trace what feeds
  the sink. HTML from `Templates.renderForPromise()` of a template using `{{ }}` is a pass; string-concatenated
  HTML is a fail. In TinyMCE plugins `editor.dom.create('div', {}, html)` is a sink.
- `fullname()`, `get_string()` and `html_writer` escape at no layer: wrap a user's name in `s()`.
- **JSON in a data attribute:** `s()` keeps numeric entities (`public/lib/weblib.php`), so encode with
  `json_encode($data, JSON_HEX_AMP | JSON_HEX_QUOT | JSON_HEX_APOS | JSON_HEX_TAG)` before `s()`.

Fix: escape at the point of output (`s($label)`), which neutralises the payload however it entered the DB.

**Probing a sink:** names are often tag-stripped on save, so a `<script>` payload proves nothing. Store an entity
payload such as `Theo &amp; <b>` and assert the escaped form appears. Write the attacker-shaped data inside a
PHPUnit test with `$this->resetAfterTest()`: a CLI script that includes `config.php` writes to the live database.

**Content written into core tables is rendered by core, sometimes `noclean`.** Question text and
question-category info render without cleaning, and `clean_text()` skips HTMLPurifier when
`is_purify_html_necessary()` finds no `<`, `>` or `&` (or only simple tags), so a `FORMAT_MARKDOWN` link like
`[x](javascript:...)` survives as a live `javascript:` href (`public/lib/weblib.php`, 5.3.0). For imported or
untrusted fields, clean every field yourself and convert or clamp `FORMAT_MARKDOWN`. Prove "no sink" by grepping
core's output code, not just the plugin.

### 2b. Uploaded files: force-download unless proven media

**Seen in reviews:** student files served inline with no content-type validation: stored XSS in the grader's
session. Another plugin with the same gap was protected only because it forced download.

Check:
- `grep -rnE "send_(stored_)?file\(" --include='*.php' .`: both serve inline unless told otherwise. The 4th
  argument of `send_stored_file()` is `$forcedownload`; for student files it is true unless the MIME type is a
  validated audio or video type.
- The upload endpoint validates type or extension against an allowlist before storing, not just `PARAM_FILE` on
  the name. The `pluginfile` callback allowlists `$filearea`.
- **Validating one draft file does not validate what is stored.** `file_save_draft_area_files()` with
  `subdirs => 0` skips files outside `/` (`public/lib/filelib.php`, 5.3.0), so a valid image in `/sub/` can vouch
  for a root-level HTML file. Require exactly one file, at `/`, and decide inline serving by its mimetype.

```php
$mimetype = $file->get_mimetype();
$ismedia = in_array($mimetype, ['audio/webm', 'audio/ogg', 'video/webm', 'video/mp4'], true);
send_stored_file($file, 0, 0, $forcedownload || !$ismedia, $options);
```

## 3. Restored, imported and authored data is input

### 3a. Backup and restore

**Seen in reviews:** the forms cleaned a label (`PARAM_TEXT` plus `validation()`), but the restore step's
`process_*()` wrote it verbatim: the only injection path. Every `process_*()` in `backup/moodle2/restore_*`
applies the same `clean_param()` or allowlist as the interactive form before `insert_record()`. Where a unique
index exists, restore upserts.

```php
protected function process_myplugin_override($data) {
    global $DB;
    $data = (object) $data;
    $data->label = clean_param($data->label, PARAM_TEXT);
    $data->courseid = $this->get_courseid();
    $DB->insert_record('local_myplugin_override', $data);
}
```

### 3b. Authored definitions and imports that reach other users

**Seen in reviews:** admins wrote content definitions that teachers used. A default could name a site setting
(`config:<plugin>/<name>`), resolved with `get_config()` for any name, so `config:core/dbpass` came back filled
into a form field. An import in "replace" mode kept the replaced item enabled, so an untrusted file went live.

For any plugin whose stored definitions, templates or imports are shown to other users:
- **Settings read by name:** limit the names to an allowlist of what they are for. Never values from
  `config.php` (`$CFG->config_php_settings`, `$CFG->forced_plugin_settings`), never names like
  `pass|secret|key|token|salt`. Apply the same rule at every entry path (editor, JSON editor, import, AI proposal)
  and in the runtime resolver for rows stored before the rule existed.
- **Imports land as drafts:** new, copied and replaced items wait for a review step.
- **The authoring capability carries `RISK_XSS`.**

Fix: one allow-rule shared by validator and resolver, tested with a forbidden name in a stored row; set the
draft status explicitly in every import branch.

## 4. Data lifecycle: privacy, backup, reset, uninstall

**Seen in reviews:** a privacy provider queried pre-rename table names, so export and erasure threw
`dml_exception`; another declared a field in `get_metadata()` but never exported or deleted it. An activity had
`<modname>_reset_userdata()` without the reset form definition and defaults, so the reset option never
appeared. Plugins writing core grade items had no `db/uninstall.php`. Course-keyed tables had no backup code.

Checks (data-storing plugins):

- **4a. Privacy.** Every table, field, preference and file area in `get_metadata()` appears in an export path
  and in every delete path; after a table rename, grep `classes/privacy/` for the old name. A
  `tests/privacy/provider_test.php` exercises all six methods against generated rows. Recipes and traps:
  `moodle-privacy-gdpr`.
- **4b. Course reset.** Reset is the full triad, `<modname>_reset_course_form_definition()`,
  `<modname>_reset_course_form_defaults()` and `<modname>_reset_userdata()`, with no `mod_` prefix
  (`public/course/reset_form.php`, 5.3.0), including the gradebook reset.
- **4c. Uninstall and course deletion.** `db/uninstall.php` exists if the plugin writes outside its own tables.
  Core's uninstall does not delete the plugin's user preferences (`uninstall_plugin()`,
  `public/lib/adminlib.php`, 5.3.0); details in `moodle-definition-of-done`.
- **4d. Backup and restore coverage.** Each course-keyed table (`grep -n 'NAME="courseid"' db/install.xml`) is
  either backed up (and round-trips every field, remapping cross-activity ids in `after_restore()`) or left out
  for a reason written in the README. An activity without backup and restore is an approval blocker. What the
  restore code does with the data is 3a.

## 5. Tests

### 5a. Tests exist and cover the sinks

**Seen in reviews:** plugins ran `moodle-plugin-ci phpunit` and `behat` over an empty `tests/` directory: green,
and vacuous. `find tests -name '*_test.php' -o -name '*.feature'`: are there real tests, and do they cover the
paths this audit touched (upload, capability, privacy)? A security regression test is evidence only after it was
seen failing with the fix reverted, at the exact sink. If CI runs test steps over an empty `tests/`, say so.

## 6. Plugins directory review checks

These are the code findings reviewers raise that no CI step catches. Each row's command, fix and accepted
answer are in [reference/directory-review-checks.md](../moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md), under the same ID;
every other guideline, with what CI covers, is in
[reference/submission-guidelines.md](../moodle-skill-files/moodle-release-preflight/reference/submission-guidelines.md). Two review findings have their home in
earlier classes and are not repeated here: pages that need only a login (1b) and course tables with no backup
(4d).

| ID | Check | Detect with | Priority seen |
|---|---|---|---|
| 6a | Every string core or the code asks for exists (`pluginname`; `filtername` for a filter; `cachedef_<area>`; `<name>:<cap>`; `messageprovider:<name>`) | the lang-key script in the reference | high |
| 6b | Global functions, classes and constants carry the frankenstyle prefix | the greps below | high, blocker |
| 6c | Narrowest `PARAM_*` type, or a stated reason for `PARAM_RAW` | `grep -rn PARAM_RAW --include='*.php' .` | medium |
| 6d | Directories via `make_temp_directory()`, `make_request_directory()` or `$CFG->directorypermissions`, never `0777` | `grep -rnE '\bmkdir\(' --include='*.php' .` | medium, low |
| 6e | Outbound HTTP through `\curl` (proxy, blocked hosts), or the setting says the proxy is not used; every caveat the README states is also in the setting's description | `grep -rn curl_init --include='*.php' .` | medium |
| 6f | No per-call queries on a hot path (a filter's `setup()` runs on every `format_text()` call; a block's `get_content()` on every page that shows it) | a query-count test | medium |
| 6g | The minor gates below | the greps they name | low |

**6b blocks approval.** Every global function, global class and `define()`d constant takes the frankenstyle
prefix, including helpers in top-level pages and `cli/` scripts, where they hide. The two greps, the names core
dictates, and the pass condition are in the reference, section 6b.

**Release files** (the `LICENSE` file, the ZIP's root folder, only `lang/en/` in the package) are checked on the
built ZIP: `moodle-plugin-release`.

### 6g. Minor gates

One row in the report; name each gate that fails. The gates (`error_log()`, scaffolding in headers,
`requires` against `supported`, test helpers in production code, literal English messages, timezones) are in
[reference/directory-review-checks.md](../moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md) section 6g.

## 7. Extended security checklist

Classes 1 to 6 come from reviews of submitted plugins. Static audits of widely installed third-party plugins
found more: SQL from mobile `$args`, `unserialize()` of restored data, IDOR and client-supplied `userid`,
GET-without-sesskey writes, `noclean` on student or LLM text, SSRF through PDF
renderers, SEPARATEGROUPS leaks. For any plugin with request entry points, walk
[reference/extended-security-checklist.md](../moodle-skill-files/moodle-release-preflight/reference/extended-security-checklist.md) after classes 1 to 6 and
report each line; where they overlap, report a finding once. Its `riskbitmask` line includes `RISK_XSS` on any
capability whose writes are rendered for other users (3b). The checklist's ten groups are checks 7a to 7j.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Capability checked on the submitted course or cm id | Attacker picks the context | Derive context from the URL id; re-validate submitted ids |
| Page or web service with `require_login()` only | Any account can act | A capability with a risk flag, on the page and in the service |
| A rule enforced on the main action only | Sibling actions bypass it | Every sibling calls the shared check; one denied-case test each |
| Capability checked only at request time | A task runs a tampered stored value | Re-check at the sink |
| Limit enforced only in `amd/src` | A direct POST bypasses it | Mirror every limit on the server |
| `send_stored_file(..., false, ...)` for student files | Stored XSS in the grader's session | Force download unless validated media |
| `html_writer::tag('span', $userval)`, a formslib label, a modal title or a `redirect()` message with user data | All print HTML | `s()` or a lang string at the sink |
| Reporting every `innerHTML` grep hit | Template-rendered HTML is already escaped | Trace the feed before reporting |
| Probing escaping with `<script>` | Names are tag-stripped on save; the probe proves nothing | An entity payload in a `resetAfterTest()` test |
| Restore writes fields verbatim | An `.mbz` is attacker input | The form's `clean_param()` in `process_*()` |
| Data can name any setting for `get_config()` | `config:core/dbpass` reaches a form field | Allowlist by purpose at every entry path |
| A replace-import keeps the item live | Untrusted content reaches users without review | Every import lands as a draft |
| Overlaying values on a core form's defaults | Frozen, capability-gated fields get set | Skip frozen elements; use core's constant |
| Reset hook without form definition and defaults | The reset option never shows | Implement the full triad |
| "CI is green" as evidence | Empty `tests/` passes; CI never sees the ZIP | List the tests per sink; check the ZIP |
| Unprefixed helper in a top-level page or `cli/` script | Namespace collision: an approval blocker | `<component>_<name>()`, or a class under `classes/` |
| Relying on `validate` for strings | A filter passes with `filtername` and no `pluginname`; `cachedef_*` is never checked | Run the lang-key script |
| `mkdir($dir, 0777, true)` | Ignores the site's directory permissions | `make_temp_directory()` or `$CFG->directorypermissions` |
| Applying a reviewer's suggested `PARAM_*` type unchecked | `PARAM_USERNAME` strips `+`, `PARAM_ALPHANUMEXT` strips `.` | Test the type on real values, or keep the reason |

## Report format

One table, one row per check ID, every ID in this order, each exactly once:

| Class | IDs |
|---|---|
| 1 Trust boundary | 1a submitted ids, 1b login is not authorisation, 1c sibling actions, 1d client-side limits, 1e two roles one state, 1f frozen core form fields, 1g question engine slots |
| 2 Output | 2a escaping at the sink, 2b uploaded files |
| 3 Input from data | 3a backup and restore, 3b authored definitions and imports |
| 4 Data lifecycle | 4a privacy, 4b course reset, 4c uninstall and course deletion, 4d backup coverage |
| 5 Tests | 5a tests exist and cover the sinks |
| 6 Directory review | 6a strings, 6b frankenstyle prefixes, 6c `PARAM_*` types, 6d directories, 6e outbound HTTP, 6f hot-path queries, 6g minor gates |
| 7 Extended | 7a entry points and authorisation, 7b client-supplied ids, 7c CSRF, 7d injection, 7e output, 7f backup, restore and import, 7g outbound and secrets, 7h messaging and visibility, 7i resource use, 7j lifecycle and privacy |

Columns: ID, check (the short name above), result (pass, fail or N/A), evidence. An N/A row keeps its line and
gives the reason, so the reader sees every check was considered. A finding that fits two checks is reported under
the first ID and referred to by ID in the other row. After the table, list each fail with its ID, file:line,
severity and the fix pattern. Do not fix unless asked.

```markdown
| ID | Check | Result | Evidence |
|---|---|---|---|
| 1a | Submitted ids | Pass | `overview.php:28` takes the course from the block instance, not the request |
| 1b | Login is not authorisation | Pass | `overview.php:35` `require_capability('block/x:viewoverview', ...)` |
| 2b | Uploaded files | N/A | no `send_file`, `send_stored_file` or file areas (grep) |
| 6f | Hot-path queries | Fail | ~28 queries per uncached student in `get_content()`; see below |
```

## Extending this checklist

When a Plugins directory or security review finds a defect class not listed here, add it in the same shape (what
was seen, described generically; the check; the fix) so the next release is audited against it. A code finding
that a command can detect goes in class 6 and the directory-review reference; a trust-boundary or output defect
goes in classes 1 to 3. Give it the next free ID in its class and add it to the Report format table; never reuse
or renumber an ID, so old reports stay readable.

## Reference files

| File | Read it when |
|---|---|
| [reference/directory-review-checks.md](../moodle-skill-files/moodle-release-preflight/reference/directory-review-checks.md) | The plugin is about to be submitted to the Plugins directory, a reviewer has opened an issue on it, or you need the command for a class 6 row |
| [reference/submission-guidelines.md](../moodle-skill-files/moodle-release-preflight/reference/submission-guidelines.md) | The plugin is going to the Plugins directory for the first time, or its listing, licence, dependencies or bundled libraries changed, or you need to know whether CI covers a guideline |
| [reference/extended-security-checklist.md](../moodle-skill-files/moodle-release-preflight/reference/extended-security-checklist.md) | The plugin has request entry points (pages, AJAX, external functions, mobile, dynamic forms, `pluginfile`, restore, tasks) and classes 1 to 6 are done |

## References

- https://moodle.atlassian.net/wiki/external/ODRhYjAyNTY4NDVmNGJlNjljN2ViMzkwYzdmYmIwMGI (Plugin submission guidelines)
- https://moodledev.io/general/community/plugincontribution/checklist (legacy checklist)
- https://moodledev.io/general/development/policies/security
- https://moodledev.io/general/development/policies/codingstyle/frankenstyle
- https://moodledev.io/docs/apis/subsystems/privacy
- https://moodledev.io/docs/apis/subsystems/output
- https://moodledev.io/docs/apis/subsystems/files
- https://moodledev.io/docs/apis/subsystems/backup
