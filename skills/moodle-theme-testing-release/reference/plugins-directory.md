# Shipping a theme: the package, the listing and the Plugins directory review

Read this when preparing a theme's release ZIP or first submission, writing its listing and screenshots, checking
the licences of bundled fonts and images, or answering a Plugins directory reviewer about a theme.

Evidence: the core code cited here was read in the 5.2 and 5.3.0 source (`public/lib/classes/output/theme_config.php`,
`public/admin/themeselector.php`, `public/admin/amd/src/themeselector/preview_modal.js`, `public/admin/renderer.php`,
`public/lib/classes/update/validator.php`, `public/admin/tool/installaddon/index.php`). The rules come from the
Marketplace plugin submission guidelines (linked from https://moodledev.io/general/community/plugincontribution)
and from the kinds of findings Plugins directory reviewers raise. Nothing here was run against the Plugins
directory itself. The general release mechanics (version numbers, notes files, tags, the release workflow) are in
`moodle-plugin-release`; the security checklist is in `moodle-release-preflight`.

## What a theme's ZIP contains

| Path | Needed because | Checked by CI |
|---|---|---|
| `mytheme/` as the only root folder | Install from ZIP; reviewers block any other root | no |
| `LICENSE` | "The plugin package must also include a licence file"; the most frequent blocker | no |
| `version.php` | `component`, `version`, `release`, `requires`, `supported`, `maturity`, `dependencies` on `theme_boost` | `validate` (presence) |
| `config.php` | Required for a theme | `validate` |
| `lang/en/theme_mytheme.php` | `pluginname`, `choosereadme` and every key the theme uses | `validate` (`pluginname` only) |
| `pix/screenshot.png` (or `.svg`, `.gif`, `.jpg`, `.jpeg`) | Theme selector card and preview | no |
| `pix/icon.svg` (or `.png`, `.gif`, `.jpg`) | The theme's row on Site administration > Plugins > Plugins overview | no |
| `classes/privacy/provider.php` | Privacy API: `null_provider`, or metadata plus `user_preference_provider` | no (core's compliance test is not in plugin CI) |
| `thirdpartylibs.xml` | Every bundled font, icon set, image pack or vendored library | no |
| `amd/build/` | Compiled AMD modules; the ZIP must work without a build step | `grunt` (staleness) |
| **5.3+:** `js/esm/build/` | Compiled React overrides | no, unless `grunt -t esm` is asked for |
| `README.md`, `CHANGES.md` | The listing and the README should say the same; release notes | no |

Leave out of the ZIP with `export-ignore`: `/.github`, `/.gitattributes`, `/.gitignore`, `node_modules`,
`*.upstream` twins of copied core files. Leaving out `/tests` is allowed and makes the ZIP smaller, but then the
ZIP cannot run its own tests; either choice is fine. Never `export-ignore` `LICENSE`, `amd/build` or a font
directory.

```gitattributes
/.github export-ignore
/.gitattributes export-ignore
/.gitignore export-ignore
*.upstream export-ignore
```

## Building and checking the ZIP

From the repository root, at the release tag:

```bash
name=mytheme
git archive --format=zip --prefix="$name/" -o "../$name.zip" v1.0.0
unzip -Z1 "../$name.zip" | cut -d/ -f1 | sort -u          # exactly one line: mytheme
for f in LICENSE version.php config.php "lang/en/theme_$name.php"; do
  unzip -Z1 "../$name.zip" | grep -qx "$name/$f" || echo "missing: $f"
done
unzip -Z1 "../$name.zip" | grep -E '^[^/]+/pix/(screenshot|icon)\.' || echo "missing: pix/screenshot or pix/icon"
unzip -Z1 "../$name.zip" | grep -E 'node_modules/|\.upstream$|^[^/]+/\.github/' && echo "development files in the ZIP"
```

- The root folder is the theme's short name: the directory under `public/theme/`, `$THEME->name`, and the part of
  `$plugin->component` after `theme_`. Core's validator requires it to survive `clean_param($rootdir, PARAM_PLUGIN)`
  and to match the component (`public/lib/classes/update/validator.php`, `rootdirinvalid`, 5.2 and 5.3.0). A GitHub
  source archive is rooted at `moodle-theme_mytheme-1.0.0/`, which fails that test on its hyphens and dots.
- The admin upload page detects the component from `version.php` and extracts under the right name before it
  validates (`public/admin/tool/installaddon/index.php`, 5.3.0), so a wrongly rooted ZIP can still install there.
  Reviewers raise the root folder anyway; build it right rather than argue it.
- `git archive` packs the tag's commit, not the working tree: a `LICENSE` added after tagging, or committed but not
  pushed before the tag, is missing from the ZIP the reviewer downloads.
- Installing the ZIP on a test site is the only end-to-end check. The upload page exists only when
  `$CFG->disableupdateautodeploy` is empty (`public/admin/tool/installaddon/settings.php`). Unzipping into
  `public/theme/` and running `php admin/cli/upgrade.php` checks the files but skips the ZIP validator.

## The theme selector: screenshot and description

- The selector shows `/theme/image.php?theme=<name>&image=screenshot&component=theme`
  (`public/admin/themeselector.php`, 5.2 and 5.3.0). For component `theme` the image is looked up in the theme's
  own `pix/`, then in each parent's `pix/` (`theme_config::resolve_image_location()`, extensions in the order svg,
  png, gif, jpg, jpeg). A child with no screenshot silently shows Boost's, so the omission is easy to miss.
- No size is enforced. The card shows the image as a background, 7rem high, `background-size: cover`; the preview
  modal shows it full width (`public/admin/templates/themeselector/theme_card.mustache`,
  `theme_preview_modal.mustache`, 5.3.0). Boost's own screenshot is 1600 by 900 px. A 16:9 image of a real course
  page reads well in both places; keep the important part in the centre, because the card crops it.
- The preview modal fetches `getString('choosereadme', 'theme_<name>')`
  (`public/admin/amd/src/themeselector/preview_modal.js`, 5.2 and 5.3.0). Without the string the preview shows a
  missing-string marker and a reviewer files it as a missing language string. One or two plain sentences.

## The plugin icon on the plugins overview page

`core_admin_renderer::plugins_control_panel()` shows `pix/icon` for every plugin type except `mod`, which uses
`pix/monologo` (`public/admin/renderer.php`, 5.2 and 5.3.0). For `theme_mytheme` the file is
`theme/mytheme/pix/icon.svg` (or `.png`, `.gif`, `.jpg`); without one the row shows a blank spacer.

- It is rendered through `pix_icon()` as an unmapped icon, that is an `<img class="icon pluginicon">`
  (`public/lib/classes/output/icon_system_fontawesome.php`, 5.3.0). `currentColor` inside the SVG does not follow
  the page text colour.
- **5.3+:** Boost's dark mode inverts only core icons whose URL contains `/t/`, `/e/`, `/a/` or the group icons
  (`public/theme/boost/scss/moodle/icons.scss`). A near-black stroke such as `#212529` sits on the dark background
  `#1d2125` and all but disappears. Read in the source and reasoned, not seen in a browser. Use a mid-tone stroke
  that reads on both, such as `#6a737b` (Boost's `$gray-600`), and look at the page once in each mode.
- A 24 by 24 viewBox line icon with no XML prolog and no embedded raster matches core's icon style.

## Fonts, images and other third-party files

The guidelines allow bundled third-party libraries and media under any licence, but they must be declared in
`thirdpartylibs.xml`. (The older devdocs third-party libraries page still says a library must be GPL v3 compatible;
the submission guidelines are the newer, controlling text.) An entry for a bundled font, in the form of Boost's
own font entries (`public/theme/boost/thirdpartylibs.xml`, 5.3.0; on 5.2 that file lists Bootstrap instead):

```xml
<?xml version="1.0"?>
<libraries>
  <library>
    <location>fonts/inter</location>
    <name>Inter</name>
    <description>Variable sans-serif typeface used for body text.</description>
    <version>4.1</version>
    <license>OFL</license>
    <licenseversion>1.1</licenseversion>
    <repository>https://github.com/rsms/inter</repository>
    <copyrights>
      <copyright>2016 The Inter Project Authors</copyright>
    </copyrights>
  </library>
</libraries>
```

- `location` is relative to the theme root. Listed paths are skipped by phplint, phpcs, phpdoc, Mustache lint and,
  after `grunt ignorefiles`, stylelint. Declaring a file you wrote yourself only hides it from the checks.
- Put the licence text beside the files (`fonts/inter/OFL.txt`) and a `readme_moodle.txt` saying where the files
  came from and how to update them.
- Do not bundle what core already ships: Font Awesome, Bootstrap, and on 5.3 the Noto Sans fonts in Boost.
- Images (login background, logos, sample banners): you must hold the rights. Stock images need a licence that
  allows redistribution in a package. The Moodle logo and name fall under the Moodle trademark policy, whose breach
  is an approval blocker.

## Licence and copyright in a theme's files

- A theme that copies or adapts Boost's layouts, templates or `lib.php` functions "reproduces or adapts a substantial
  part of" Moodle, so it is GPL v3 or later. `LICENSE` holds the full GPL v3 text.
- Every file carries the boilerplate and an `@copyright` line. phpcs checks this in PHP files only; add it by hand to
  `.mustache`, `.scss` and `.js` files.
- A file copied or adapted from Boost or from another theme keeps the original `@copyright` line, with yours added
  below it. Nothing checks this; reviewers and the original authors do.

```scss
// This file is part of Moodle - https://moodle.org/
// (rest of the GPL header)

/**
 * Banner styles for theme_mytheme.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
```

```mustache
{{!
    This file is part of Moodle - http://moodle.org/
    (rest of the GPL header)
}}
{{!
    @template theme_mytheme/banner

    The course banner.

    Example context (json):
    {
        "text": "Welcome"
    }
}}
```

Inside a `{{! }}` comment never write Mustache tag syntax or a literal `}}`: the comment ends there and the rest
prints on the page. Describe helpers in words.

## Strings a theme must define

`validate` asks for `pluginname` only. Core and reviewers ask for more:

| Key | Asked for by |
|---|---|
| `pluginname` | Everything |
| `choosereadme` | The theme selector's preview |
| `privacy:metadata`, or one string per stored preference (`privacy:metadata:preference:<name>`) | The privacy provider and its compliance test |
| `region-<name>` for each block region no parent names | `theme_config::get_region_name()`: the theme, then its parents, then `theme_boost`; a region none of them names shows `[[region-<name>]]` in the block settings |
| `configtitle` (by convention) | The title of the theme's settings page, if `settings.php` uses it |
| Every `get_string('x', 'theme_mytheme')` and `{{#str}} x, theme_mytheme }}` key | The page that uses it |

From the theme's root:

```bash
{
  grep -rhoE "get_string\('[a-z0-9_:-]+', *'theme_mytheme'" --include=*.php . | cut -d"'" -f2
  grep -rhoE "[{][{]#str[}][}] *[a-z0-9_:-]+, *theme_mytheme" --include=*.mustache . \
    | sed -E 's/^[{][{]#str[}][}] *([^,]+),.*/\1/'
} | sort -u > used.txt
grep -oE "^.string\['[^']+'\]" lang/en/theme_mytheme.php | cut -d"'" -f2 | sort -u > defined.txt
comm -23 used.txt defined.txt     # keys used but not defined
```

- Keys in the lang file are sorted: phpcs (`moodle.Files.LangFilesOrdering`) warns on a key out of order, which
  fails a `--max-warnings 0` run.
- The grep misses keys built at runtime (`'region-' . $name`, settings that loop over a list). Render every page the
  theme changes once and look for `[[`.
- Only `lang/en` ships. Translations go through AMOS after approval.

## Listing screenshots for a theme

The listing screenshots are uploaded on the plugin page and are separate from `pix/screenshot.png`. The guidelines
give no size, number or format. For a theme they are the main evidence of what it does:

- Show the pages people meet: the dashboard or front page, a course page with real-looking content, an activity,
  the login page, and the theme's settings page. **5.3+:** add a dark-mode view if the theme supports colour modes,
  and one at phone width.
- Real screenshots of the theme as shipped, with realistic course names and text. No mock-ups, no placeholder
  images, no lorem ipsum.
- Read every proper noun in each picture before uploading: course names, user names, site names and test leftovers
  are the usual slips.
- Before taking them: close the drawers, finish or disable user tours for the user, and turn off the performance
  footer, or they cover the page.

## What reviewers raise that applies to themes

Generalised from the kinds of finding Plugins directory reviewers file, in order of how often they block approval.
None of them is caught by moodle-plugin-ci.

| Finding | Theme form of it | Check before submitting |
|---|---|---|
| Missing plugin licence file | No `LICENSE` in the ZIP root | List the ZIP |
| ZIP root folder not the plugin name | A GitHub source archive was uploaded | `cut -d/ -f1 \| sort -u` on the listing |
| Missing language string definitions | `choosereadme`, a region name, a key used in a template | The string check above, and a rendered page with no `[[` |
| Functions not frankenstyle prefixed | A helper in `lib.php`, a page script or a CLI script named `mytheme_x()` or `get_banner()` | Every global function starts `theme_mytheme_`; better, a namespaced class under `classes/` |
| Settings not stored per plugin | `new admin_setting_configtext('mytheme_banner', ...)` | `theme_mytheme/banner`, with the slash |
| Repeated queries on every page | A setting or record read once per context, block or menu item | A request cache, and a PHPUnit query ceiling |
| Unscoped CSS | Rules for one third-party plugin's markup shipped in the theme | Scope the theme's own components under its own class prefix |
| Page scripts without capability checks | A theme page (a preview, an export) that calls only `require_login()` | Name the capability each page requires |
| `PARAM_RAW` where a narrower type fits | Parameters of a theme page or web service | The narrowest `PARAM_*`, or a comment saying why none fits |

Answering a finding: reply on the issue with the commit and the release that fixed it, what was changed, what was
not and why, and any sibling case found while checking. A precise, reasoned "this does not apply because ..." has
been accepted without a change. Check a reviewer's suggested fix before applying it: a suggested `PARAM_*` type can
strip characters the input needs, and the documentation links in findings often point to an older Moodle version
than the one the theme supports. The mechanics of the reply and of a fix release are in `moodle-plugin-release`.

## Release checklist for a theme

1. Tests exist and assert the theme: the compile test, a Behat feature with at least one `@javascript` scenario,
   the privacy compliance test run once by hand.
2. The workflow ran green on every supported branch row with `--suite mytheme` and `--scss-deprecations`, and the
   Behat log shows scenarios, not "No scenarios".
3. `version.php`: `requires` not below the lowest `supported` branch; `dependencies` names `theme_boost` (and any
   other parent) at a version that exists on the lowest branch; `release` bumped as `moodle-plugin-release` says.
4. Strings, `pix/screenshot.*`, `pix/icon.svg`, privacy provider, `thirdpartylibs.xml` and licences of bundled files
   as above.
5. Copied core files: copyright lines kept, `.upstream` twins compared with the new core version's originals, the
   copies updated where core changed.
6. Built files committed fresh: `amd/build`; **5.3+:** `js/esm/build`.
7. The ZIP built with `git archive --prefix=mytheme/` from the tag, listed, and installed once on a clean site of
   the lowest supported branch.
8. The listing: short and full description, supported versions, licence named, issue tracker URL (required for
   approval), source URL, documentation URL, screenshots as above. The README says the same as the listing, including
   post-install steps and any dependency on another plugin.

## What is not known

- Which file names count as "a licence file": reviewers name `LICENSE`; whether `LICENSE.md`, `LICENSE.txt` or
  `COPYING` pass the same check is not documented. Use `LICENSE`.
- The exact commands, options and Moodle branch of the Plugins directory's own automated check: the guidelines say
  only that it uses moodle-plugin-ci. Make the theme pass `--max-warnings 0` and `--max-lint-warnings 0`.
- How the namespaced-CSS rule is applied to a theme, whose job is site-wide CSS. The reading above (scope what the
  theme adds; no rules for one third-party plugin) is an interpretation.
