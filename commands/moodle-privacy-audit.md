---
name: moodle-privacy-audit
description: Audit a Moodle plugin's privacy provider for completeness against its DB schema, preferences, files and external services.
argument-hint: "[plugin path] — e.g. public/local/attendance"
---

You will audit the privacy provider of a Moodle plugin.

User's input: $ARGUMENTS

Activate the `moodle-privacy-gdpr` skill for context. Its rules decide each check below; do not judge from memory.

Steps:

1. Locate the plugin directory. If unclear, ask.
2. Read `db/install.xml` (or `db/upgrade.php` if no install.xml) — list every table and column.
3. Identify what the plugin holds about users:
   - Columns: `userid`, `user_id`, `createdby`, `modifiedby`, `usermodified`, `relateduserid`
   - Free-text fields a user authored (`content`, `comment`, `description`, `note`)
   - Files in the plugin's file areas (item ids that point at the plugin's rows)
   - Identifiers from external systems linked to a user
   - User preferences: `grep -rnE "set_user_preference|user_preferences\b|setUserPreference" --include='*.php' --include='*.js' .`
     (also the `get_user_preferences` callback in `lib.php`)
   - Data sent to another system: `grep -rnE "new \\\\?curl\b|curl_init|->post\(|->get\(" --include='*.php' .`,
     then read what each request carries
4. Read `classes/privacy/provider.php`. If it does not exist, that is the first finding: every plugin needs a
   provider, and the plugin's own CI run does not report a missing one.
5. For each user-identifying column, check:
   - It is declared in `get_metadata()` via `add_database_table` with a lang string
   - The column has an entry in the plugin's lang file of the form `privacy:metadata:<table>:<column>`
   - `get_contexts_for_userid` returns contexts where the user has data
   - `get_users_in_context` returns users who have data in a given context
   - `export_user_data` exports the data per context
   - `delete_data_for_user` and `delete_data_for_users` delete only the named users' rows and files
   - `delete_data_for_all_users_in_context` checks the context level, and for a module that the cm is its own
   - The table names the request methods query are the current ones (after a rename, grep
     `classes/privacy/` for the old name)
6. Check for subsystem usage:
   - If plugin attaches files via the Moodle Files API, `add_subsystem_link('core_files', ...)` must be present,
     and the provider itself must export and delete the files: the link only declares them
   - Same for `core_comment`, `core_rating`, `core_tag` if used
7. Preferences and external services:
   - Every preference the plugin sets is declared with `add_user_preference()` and exported in
     `export_user_preferences()` (interface `user_preference_provider`)
   - Every destination that receives personal data is declared with `add_external_location_link()`
8. If plugin stores no user data, check it implements `null_provider` correctly (`get_reason` returns lang string key, `privacy:metadata` lang string defined). A `null_provider` on a plugin that sets a preference or sends
   personal data out is a finding.
9. Look for `tests/privacy/provider_test.php` and whether it exercises the request methods on generated rows.
10. Output findings, each with `file:line`:
   - GREEN: present and correct
   - YELLOW: present but incomplete / missing lang strings
   - RED: missing entirely

State what was not checked: nothing was run, so the export and the deletion were read, not observed, and core's
compliance test (`public/privacy/tests/privacy/provider_test.php`) was not run for the plugin.

Propose a fixed `provider.php` and the missing lang strings if there are issues. Don't write the changes without user confirmation if the plugin is non-trivial.
