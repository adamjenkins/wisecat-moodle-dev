---
name: add-language-pack
description: Translate a Moodle plugin's strings into one language and save the pack in the project's notes directory, not the plugin.
argument-hint: "<language code> [plugin path] — e.g. ja, or es public/local/attendance"
---

You will add or update a language pack for a Moodle plugin, following the `moodle-language-pack` skill.

User's input: $ARGUMENTS

1. The first word is the language code. If it is missing, ask for it. If it is not a Moodle code (`pt-BR`, `zh`),
   map it as the skill says and state the code used, or ask when two fit.
2. The plugin is the path given, or else the plugin repository of the current directory (the one holding
   `version.php`). If neither, ask.
3. The pack goes in the project's notes directory as `<notes>/<plugin>/lang-<code>/<file>.php`. Take the notes
   directory from the project's instructions; if they name none, ask once. Never write it inside the plugin.
4. If the pack exists, update it (new, changed and removed keys); otherwise translate every key of `lang/en`.
5. Check it: `php -l`, the key and placeholder diff from the skill. Report the key count, the result of each
   check, the file path, and that the translation is not reviewed by a native speaker unless it was.
6. Do not install it on a site or contribute it to AMOS unless asked.
