# /moodle-string-check

> Find hard-coded English strings that should use get_string() / Mustache {{#str}}.

You will find untranslated user-facing strings in a Moodle plugin.

User's input: <args>

If empty, ask for a plugin path.

Steps:

1. Walk the plugin directory. Skip `amd/build/`, `tests/`, vendored libraries and `*.upstream` files; read
   JavaScript in `amd/src/`.
2. Read `lang/en/<component>.php` (an activity module: `lang/en/<name>.php`) — list defined keys.
3. For each `.php`, `.mustache`, and `.js` file, find user-facing strings that are not loaded via `get_string`/`{{#str}}`/`core/str`:

   PHP heuristics:
   - String literals passed to:
     - `$mform->addElement('<type>', '<name>', '<literal>')` — the third argument is the label; also option
       texts of selects and radio buttons
     - `new admin_setting_configtext(..., '<literal>', '<literal>')` — title + description
     - `new \html_table_cell('<literal>')`, `html_writer::tag('p', '<literal>')`
     - `\core\notification::success('<literal>')`, `\core\notification::error('<literal>')`
     - `redirect($url, '<literal>')`
     - `throw new moodle_exception('<literal>')` — should be a string KEY, not a sentence
   - Direct `echo` of literals over 3 words

   Mustache heuristics:
   - Visible text not wrapped in `{{#str}}KEY, COMPONENT{{/str}}`
   - Aria-labels / titles with literal text

   JS heuristics:
   - String literals passed to `Notification.alert()`, `Toast.add()`, error messages thrown
   - Any UI-visible literal not loaded via `core/str` (`getString`, `getStrings`)

4. Skip strings that are clearly identifiers (selectors, classes, route keys, lang keys themselves).

5. Check the other direction too, because a missing key prints `[[key]]` or throws on the live page while every
   lint passes:
   - Every key the plugin's code asks for from its own component (`get_string('<key>', '<component>')`,
     `{{#str}}<key>, <component>{{/str}}`, `new lang_string(...)`, `getString('<key>', '<component>')`) is
     defined in the lang file
   - Every string core asks for by convention exists: `pluginname`, one per capability (`<name>:<cap>`), the
     privacy strings, and the others listed in the `moodle-release-preflight` skill for the plugin's type
   - Keys in the lang file are in alphabetical order (a coding-style warning, which fails a CI run that allows none)

6. Output findings as:

```
[FILE]:[LINE] "<literal>"
   → propose key: <lowercase key, no plugin prefix; a colon only in capability strings>
   → in lang/en/<component>.php:
       $string['<key>'] = '<literal>';
   → replacement:
       <PHP>: get_string('<key>', '<component>')
       <Mustache>: {{#str}}<key>, <component>{{/str}}
       <JS>: await getString('<key>', '<component>')
```

7. Optionally, propose adding `lang/en/<component>.php` keys in a single edit and substituting the literals.
   A new string shows only after a cache purge or a version bump, and a placeholder (`{$a}`) is passed as the
   third argument of `get_string()`, never concatenated.

Reference the `moodle-plugin-development` skill for lang string conventions.
