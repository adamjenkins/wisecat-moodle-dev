# moodle-language-pack

> Use when asked to translate a Moodle plugin's strings into another language, "add a language pack" (es, ja, pt_br, zh_tw ...), update an existing translation after lang/en changed, or try a translation on a test site. Covers the file name per plugin type (lang/<code>/<component>.php, an activity's <modname>.php), Moodle's language codes, keeping every key and only the keys of lang/en, placeholders ({$a}, {$a->name}) and HTML kept intact, _help strings, PHP quoting, checking a pack with php -l and a key and placeholder diff, keeping packs outside the plugin repository (the package ships lang/en only), installing a pack as a local customisation (<code>_local under $CFG->langlocalroot) to view it with ?lang=, and contributing it through AMOS. Skip when adding or renaming English strings (moodle-plugin-development) or finding hard-coded English (the /moodle-string-check command).

# Moodle Language Pack

## Overview

A translation of a plugin's strings into one language, as a file that Moodle can load. It is kept outside the
plugin repository, because a plugin's package ships only `lang/en/` and other languages reach sites through the
Moodle language packs (AMOS). Keeping the file lets you view it on a test site and contribute it.

## When to Use

- "Add a language pack for ja", `/add-language-pack es`, "translate the plugin into Portuguese (Brazil)"
- `lang/en` changed and the existing packs need the new and changed strings
- Viewing a translation on a test site, or preparing it for AMOS
- **Skip when:** adding or changing English strings (`moodle-plugin-development`) or finding hard-coded English
  (`/moodle-string-check`)

## Where the files go

In the project's notes directory, never inside the plugin repository: the Plugins directory review expects only
`lang/en/` in the package, and a non-English file in `lang/` ships with every release. Use the notes directory the
project's instructions name; otherwise ask once.

```
<notes>/<plugin>/lang-<code>/<file>.php
```

`<file>` is the same file name as in `lang/en/`: `<type>_<name>.php` (`local_forumcare.php`), except an activity
module, whose file is `<name>.php` without `mod_` (`public/lib/classes/string_manager_standard.php`, 5.3.0). Several
plugins of one project each get their own `lang-<code>/` under their own notes folder.

## Language codes

Moodle's codes are lower case with an underscore: `es`, `ja`, `de`, `pt_br`, `zh_cn`, `zh_tw`, `es_mx`, `fr_ca`.
`es` is international Spanish and `es_mx` a child of it; a child pack holds only what differs. The list of codes is
at https://download.moodle.org/langpack/5.3/. If the user's code is not one of them (`pt-BR`, `zh`), map it to the
Moodle code and say which was used, or ask when two fit (`zh`: `zh_cn` or `zh_tw`).

## The recipe

1. **Read the English file** `lang/en/<file>.php` from the repository at its current commit. Count the keys.
2. **If the pack exists**, read it: keep every translation whose English text is unchanged, translate new keys,
   retranslate keys whose English changed (compare with `git log -p lang/en/<file>.php` since the pack's date), and
   drop keys no longer in English.
3. **Translate each string.**
   - Keep the placeholders exactly: `{$a}`, `{$a->name}`, and the same set in each string. Their order in the
     sentence may change.
   - Keep HTML tags and Markdown in `_help` strings; translate only the text.
   - Keep the meaning of the UI: a button label stays short; a menu item matches how core translates the same word
     in that language. Read core's pack for the language where one is installed
     (`$CFG->dataroot/lang/<code>/moodle.php`) and reuse its terms ("course", "activity", "grade").
   - Product and plugin names stay as they are unless the plugin's own English string translates them.
   - Quote with single quotes and escape `'` as `\'`. Keep the file's sort order.
4. **Write the file** with the plugin's licence header, a docblock naming the language
   (`Japanese strings for local_forumcare.`) and the copyright holder of the translation, then the strings:

   ```php
   <?php
   // This file is part of Moodle - http://moodle.org/
   // ... the GPL header as in lang/en ...

   /**
    * Japanese strings for local_forumcare.
    *
    * @package    local_forumcare
    * @copyright  2026 <translation's copyright holder>
    * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
    */

   defined('MOODLE_INTERNAL') || die();

   $string['pluginname'] = 'フォーラムケア';
   $string['reportpost'] = 'この投稿を報告';
   ```

5. **Check it** (below), then add a line to the plugin's notes: language, key count, date, the commit of
   `lang/en` it matches, and who translated it ("machine translation, not reviewed by a native speaker" when that
   is the case).

## Checking a pack

```bash
php -l <notes>/<plugin>/lang-ja/local_forumcare.php
php -r '
  define("MOODLE_INTERNAL", 1);
  $string = []; include $argv[1]; $en = $string;
  $string = []; include $argv[2]; $xx = $string;
  echo "missing: ", implode(", ", array_keys(array_diff_key($en, $xx))) ?: "none", "\n";
  echo "extra: ", implode(", ", array_keys(array_diff_key($xx, $en))) ?: "none", "\n";
  foreach ($en as $k => $v) {
      if (!isset($xx[$k])) { continue; }
      preg_match_all("/\{\\\$a(->\w+)?\}/", $v, $a); preg_match_all("/\{\\\$a(->\w+)?\}/", $xx[$k], $b);
      sort($a[0]); sort($b[0]);
      if ($a[0] !== $b[0]) { echo "placeholders differ: $k\n"; }
  }' -- lang/en/local_forumcare.php <notes>/<plugin>/lang-ja/local_forumcare.php
```

Pass: `php -l` clean, missing and extra both `none`, no "placeholders differ" line. Then read the translated file
once for strings left in English.

## Viewing it on a test site

Moodle loads a plugin's strings in a language from the plugin's `lang/<code>/`, then
`$CFG->langotherroot/<code>/`, then local customisations in `$CFG->langlocalroot/<code>_local/` (both default to
`$CFG->dataroot/lang`; `public/lib/classes/string_manager_standard.php`, 5.3.0). To view a pack without touching
the plugin or the installed language pack:

1. The language itself must be installed on the site (Site administration > Language > Language packs).
2. Copy the file to `$CFG->dataroot/lang/<code>_local/<file>.php`, readable by the web server user.
3. Purge caches (`php admin/cli/purge_caches.php`), then open a page with `?lang=<code>`.

The `_local` copy overrides the official translation on that site. Remove it when done, and say in the notes if it
is left in place.

## Contributing it

Once the plugin is in the Plugins directory, its English strings are imported into AMOS (https://lang.moodle.org),
and translations reach sites through the language packs. Contribute the pack there: log in, import the file into
your AMOS stage, and submit the staged strings to the language pack maintainers (described in the AMOS
documentation, not run here). A plugin not yet in the directory has nothing in AMOS to translate.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| The pack put in the plugin's `lang/<code>/` | It ships in the release; reviewers ask for `lang/en` only | Keep it in the notes directory |
| `mod_<name>.php` for an activity | The file is never loaded | `<name>.php` |
| A placeholder translated or dropped | `{$a}` shows literally, or a value is missing from the sentence | Keep the same placeholder set; check with the diff |
| An apostrophe not escaped | Parse error: every string of the plugin fails in that language | `\'`, and `php -l` |
| Keys missing after `lang/en` grew | Those strings fall back to English | Re-run the key diff on every update |
| A code that is not Moodle's (`pt-BR`) | The directory name matches no language | `pt_br` |
| Copying into `<code>/` instead of `<code>_local/` | The next language pack update overwrites it | `<code>_local/` |
| A machine translation presented as reviewed | Users trust wording no speaker checked | Say who translated it |

## References

- https://moodledev.io/docs/5.3/apis/core/string
- https://docs.moodle.org/en/AMOS
- https://download.moodle.org/langpack/5.3/
