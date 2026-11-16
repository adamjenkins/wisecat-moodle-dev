# The release ZIP: building, listing and fixing it

Read this when you build a plugin ZIP by hand (always for a first submission), write `.gitattributes`, declare
bundled code or fonts in `thirdpartylibs.xml`, diff a translation against `lang/en`, or debug a
"rootdirinvalid" or "componentmismatchname" error when installing from a ZIP.

## Why the ZIP is its own deliverable

`moodle-plugin-ci install` copies the git checkout into a Moodle tree. Nothing in CI unpacks a ZIP, so every
property of the package (its root folder, whether `LICENSE` survived `export-ignore`, whether `amd/build` is in
it, whether a stray `node_modules/` came along) is unchecked until a reviewer or an admin unpacks it. Treat
"build the ZIP and list it" as a release step with its own pass condition.

## What core's installer checks, in order

`\core\update\validator::execute()` runs these on the extracted package
(`public/lib/classes/update/validator.php`, read in 5.3.0; the checks are identical in 5.2):

| Check | Message key | What fails it |
|---|---|---|
| At least four files | `filesnumber` | A near-empty archive (core expects at least `version.php` and the English lang file) |
| Every file extracted | `filestatus` | A corrupt or encrypted entry |
| One top-level directory | `onedir` | Files at the archive root, or two root folders (for example a `__MACOSX/` folder next to the plugin) |
| Root name is a valid plugin name | `rootdirinvalid` | Any character `PARAM_PLUGIN` strips: hyphens, dots, capitals. `moodle-local_myplugin-1.4.2` fails |
| `version.php` present and using `$plugin` | `missingversionphp`, `versionphpsyntax`, `missingversion` | No `version.php` in the root folder, or the old `$module->` syntax |
| `requires` not above the site's build | `requiresmoodle` | A 5.3-only build on a 5.2 site |
| `$plugin->component` declared, of the expected type | `missingcomponent`, `componentmismatchtype` | No component line, or uploading a block as a local plugin |
| Root name equals the component's name part | `componentmismatchname` | Root `local_myplugin/` (type prefix kept) for component `local_myplugin` |
| Version not lower than the installed one | `pluginversiontoolow` | Re-uploading an older build |
| English lang file present | `missinglangenfolder`, `missinglangenfile`, `missingexpectedlangenfile` | `lang/en/` export-ignored, or the file not named `<component>.php` (`<name>.php` for an activity module) |

The admin upload page (`public/admin/tool/installaddon/index.php`, 5.3.0) reads the component from
`version.php` inside the ZIP, and the plugin manager then extracts with the plugin's name as the forced root
(`public/lib/classes/update/code_manager.php`, `unzip_plugin_file()` with `$rootdir`). That is why a wrongly
rooted ZIP can install through the UI on one site and fail elsewhere: an admin who unzips into `local/` by hand
gets a directory named `moodle-local_myplugin-1.4.2`, which core does not recognise as the plugin. Read in the
source, not run. Reviewers raise a wrong root on every submission whatever the UI does, so ship the right one.

## Building it

From the release tag, so the ZIP is exactly the tagged tree:

```bash
name=myplugin                      # the component's name part: local_myplugin -> myplugin
tag=v1.4.2
git archive --format=zip --prefix="$name/" -o "../$name.zip" "$tag"
```

`git archive` takes committed content only: an uncommitted `LICENSE` or a freshly built `amd/build/` that was
not committed is not in the ZIP. If you must zip a working directory instead, the directory itself has to carry
the plugin's name:

```bash
cd .. && zip -r myplugin.zip myplugin -x 'myplugin/.git/*' 'myplugin/node_modules/*' 'myplugin/.github/*'
```

Never upload GitHub's "Source code (zip)" asset or a `/archive/refs/tags/...zip` download: its root is
`<repository>-<version>/`.

Releases published by the `moodlehq/moodle-plugin-release` workflow are built by that workflow, not by you. It
checks out the tag, reads `$plugin->component` from `version.php`, strips the type prefix and runs
`git archive --format=zip --prefix="<name>/" -o "<name>.zip" HEAD` (workflow revision 2026091801, read, not
run): the same command as above, so the root folder is right by construction and `export-ignore` applies. It
does not check for `LICENSE`, `amd/build` or stray files. After the first workflow release, download that
version's ZIP from the plugin's page once and list it the same way, so you know what users receive.

## Listing it: the pass condition

```bash
z=../myplugin.zip; name=myplugin
unzip -Z1 "$z" | cut -d/ -f1 | sort -u                     # exactly one line: myplugin
unzip -Z1 "$z" | grep -xE "$name/(LICENSE|version\.php)"   # both lines
unzip -Z1 "$z" | grep -E "^$name/lang/" | cut -d/ -f3 | sort -u   # only: en
unzip -Z1 "$z" | grep -E '(^|/)(node_modules|\.git|\.github|__MACOSX)/|\.DS_Store$|\.log$'   # nothing
unzip -Z1 "$z" | grep -c "^$name/amd/build/"               # > 0 when amd/src exists
```

Then read the full listing by eye once. Look for files that should not ship (local config, screenshots meant
for the listing, test fixtures with personal data, `.upstream` copies of core files) and for files that must
(`thirdpartylibs.xml` when there is bundled code, `db/`, `templates/`, `pix/`, `styles.css`).

`amd/build/` must match `amd/src/`: `moodle-plugin-ci grunt` rebuilds into a copy and fails with "File is
stale and needs to be rebuilt" on any difference (`src/Command/GruntCommand.php`, `validatePluginFiles()`,
moodle-plugin-ci 4.5.11), so a green `grunt` step on the tagged commit is the evidence that the shipped build is
current.

## The licence file

- Name it `LICENSE`, in the repository root, holding the full licence text. Reviewers' findings name
  `LICENSE`; whether `LICENSE.md`, `LICENSE.txt` or `COPYING` satisfy the check is not documented, so do not
  rely on another name.
- The licence must match what the file headers declare. A plugin whose headers say GPL v3 or later ships the
  GPL v3 text:

  ```bash
  curl -fsSL -o LICENSE https://www.gnu.org/licenses/gpl-3.0.txt
  grep -q 'Version 3, 29 June 2007' LICENSE && echo ok
  git check-attr export-ignore -- LICENSE      # must not say "set"
  ```

- The submission guidelines let the provider choose a licence, but require GPL v3 for a plugin that reproduces
  or adapts a substantial part of Moodle's source. A theme built from Boost's layouts and templates, or a plugin
  that copies core classes, is in that case.
- Third-party notices (a `LICENSES/` folder, a licence file next to a bundled font) are in addition to the root
  `LICENSE`, not instead of it.

## `.gitattributes`

`export-ignore` removes paths from `git archive` output, and therefore from every ZIP built from a tag. A
conservative file:

```gitattributes
/.github export-ignore
/.gitattributes export-ignore
/.gitignore export-ignore
```

Excluding `/tests` is a choice: it shrinks the ZIP, but other developers lose the tests when they install from
it. Never export-ignore `LICENSE`, `amd/build`, `lang/en`, `thirdpartylibs.xml` or anything the plugin loads at
runtime. After editing the file, rebuild and re-list the ZIP; the effect is visible only in the listing.

## `thirdpartylibs.xml`

Every bundled library, font, icon set or vendored SCSS/JS folder gets an entry. The guidelines require the
declaration, and `moodle-plugin-ci` skips the listed locations in phplint, phpcs, phpdoc, phpmd and mustache,
so an undeclared library also shows up as hundreds of style errors. Core's Boost declares its fonts this way
(`public/theme/boost/thirdpartylibs.xml`, 5.3.0):

```xml
<?xml version="1.0"?>
<libraries>
  <library>
    <location>fonts/noto-sans</location>
    <name>Noto Sans</name>
    <description>Noto Sans is a global font family by Google.</description>
    <version>2.015</version>
    <license>OFL</license>
    <licenseversion>1.1</licenseversion>
    <repository>https://github.com/notofonts/latin-greek-cyrillic</repository>
    <copyrights>
      <copyright>2022 The Noto Project Authors</copyright>
    </copyrights>
  </library>
</libraries>
```

`location` is relative to the plugin root. The guidelines allow bundled third-party files under any licence as
long as they are declared; the older moodledev "third-party libraries" page still says a library must be GPL
compatible. Follow the guidelines and keep the declared licence accurate. Put a `readme_moodle.txt` in each
library folder with the source URL and the steps to update it
(https://moodledev.io/general/community/plugincontribution/thirdpartylibraries).

## Translations outside the release

Only `lang/en/` ships; other languages go to AMOS after approval. If you maintain translations elsewhere to
contribute them, check each one against `lang/en` at every release, because new English keys silently leave
the translation behind:

```bash
php -r 'define("MOODLE_INTERNAL", 1);
  include "lang/en/local_myplugin.php"; $en = $string; $string = [];
  include "../translations/ja/local_myplugin.php";
  echo count($en), " en, ", count($string), " ja\n";
  echo "missing: ", implode(", ", array_keys(array_diff_key($en, $string))), "\n";
  echo "extra: ", implode(", ", array_keys(array_diff_key($string, $en))), "\n";'
```

Without the `define()`, the lang file's `defined('MOODLE_INTERNAL') || die();` ends PHP silently and prints
nothing, which reads as clean. The command must print the two counts; no output means it did not run.

## Themes

The root folder is the theme's name: `theme_mytheme` ships as `mytheme/`, the same value as `$THEME->name` and
the directory under `theme/`. `pix/screenshot.png` (shown in the site's theme selector) ships in the ZIP and is
a different file from the listing screenshots uploaded to the Plugins directory page. The rest of a theme's
release checks are in `moodle-theme-testing-release`.
