You will scaffold a new Moodle plugin.

User's input: {{{ input }}}

If `{{{ input }}}` is empty or missing required values, ask the user:
1. Plugin type (one of: `local`, `mod`, `block`, `format`, `theme`, `auth`, `enrol`, `report`, `tool`, `qtype`, `filter`, `repository`)
2. Plugin name (lowercase letters and digits, starting with a letter, no underscores in the name part — frankenstyle becomes `<type>_<name>`)
3. Supported Moodle versions (default: 5.2 and 5.3)
4. Whether the plugin will store user data (affects privacy provider choice)
5. The copyright holder for the file headers

If the type is `theme`, use `/moodle-new-theme` instead: a theme has its own file set and rules.

Then:

1. Activate the `moodle-plugin-development` skill for conventions.
2. Create the directory under the Moodle root. On Moodle 5.2 and 5.3 plugin directories are under `public/`:
   `public/local/<name>/`, `public/mod/<name>/`, `public/blocks/<name>/`, `public/course/format/<name>/`,
   `public/question/type/<name>/`, `public/admin/tool/<name>/`. The directory for every type is in the plugin
   types reference of that skill. If the Moodle root (the directory that holds `public/` and `admin/cli/`) is
   unknown, ask. Never overwrite an existing directory.
3. Generate the minimum required files for the chosen plugin type using the plugin types reference of the
   `moodle-plugin-development` skill.
4. Always include:
   - `version.php` with the frankenstyle component, today's date as version (`YYYYMMDD00`), and `requires` and
     `supported` as a matching pair: `$plugin->requires = 2026042000;` and `$plugin->supported = [502, 503];` for
     5.2 and 5.3; `2026100500` and `[503, 503]` for 5.3 only. `supported` is always two branch numbers
   - `LICENSE` in the plugin root with the full GPL v3 text, copied from `COPYING.txt` in the Moodle root. The
     Plugins directory blocks approval without it and no CI step checks it (`moodle-plugin-release`)
   - `lang/en/<component>.php` (an activity module: `lang/en/<name>.php`) with at least `pluginname`, keys in
     alphabetical order
   - `classes/privacy/provider.php` — `null_provider` if no user data, otherwise scaffold the full provider per the `moodle-privacy-gdpr` skill
   - GPL-3.0-or-later license header and a file docblock with `@package`, `@copyright` and `@license` on every PHP file
   - `defined('MOODLE_INTERNAL') || die();` after the docblock in files that run code when included
     (`version.php`, `lib.php`, `db/*.php`, `settings.php`, the lang file); not in class files under `classes/`
   - `README.md` naming the supported Moodle versions, and a changelog
5. If the plugin type has type-specific required files (e.g., `mod_form.php` for activity modules, `block_<name>.php` for blocks), include them.
6. Print a summary of what was created and the next steps the user should take: from the Moodle root run
   `php admin/cli/upgrade.php --non-interactive`, then review the capabilities and write tests. Say that the
   skeleton was written and not installed or tested.

Coding standards: 4-space indent, no closing `?>`, lower-case names with underscores for functions and classes
(`local_attendance_get_sessions()`, `session_manager`), variables in lower case without underscores.

For a larger skeleton (tests, backup code for an activity, a settings page) hand the brief to the
`moodle-scaffolder` agent. If a Moodle version difference matters, state the rule for 5.2 and for 5.3; the
`moodle-5-3-changes` skill lists what 5.3 changed.
