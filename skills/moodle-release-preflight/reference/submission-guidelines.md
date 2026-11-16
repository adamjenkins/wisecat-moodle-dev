# The Plugins directory submission guidelines, rule by rule

Read this when the plugin is about to be submitted to the Moodle Plugins directory for the first time, when its
listing, licence, dependencies or bundled libraries change, or when you need to know whether CI already covers a
guideline.

The controlling text is the Moodle Marketplace "Plugin submission guidelines" page,
https://moodle.atlassian.net/wiki/external/ODRhYjAyNTY4NDVmNGJlNjljN2ViMzkwYzdmYmIwMGI. The older checklist at
https://moodledev.io/general/community/plugincontribution/checklist says at its top that it describes the legacy
process; where the two differ (licences of bundled files, the licence file, `thirdpartylibs.xml`, the scope of the
privacy API), apply the guidelines. The page has 74 rules in four groups. Each table below gives the rule, what
in `moodle-plugin-ci` catches it, and a check; checks marked like `[M3]` are commands in the block under the
table, run from the plugin root.

"CI" means the standard `moodle-plugin-ci` workflow (phplint, phpcs and phpdoc with `--max-warnings 0`,
validate, savepoints, mustache, grunt, phpunit, behat). What each command checks was read in the
moodle-plugin-ci 4.5 and moodle-cs 3.7 source, not run. CI fully covers about six of the rules (coding style, PHP
boilerplate and `@copyright`, lang file syntax, a login call after `config.php`, both databases when the matrix
has them) and partly covers about eight. None of the kinds of finding reviewers have raised on real submissions
was caught by CI.

Set the component once:

```bash
c=local_myplugin; type=${c%%_*}; short=${c#*_}
```

## Metadata (the listing and the package)

| Rule | CI | Check |
|---|---|---|
| A meaningful English description: a short one (a sentence or two) and a long one; the same information on the listing and in the README | none | Read the README and the listing side by side |
| Supports at least one Moodle version that is still maintained | none (the matrix proves only the branches it lists) | `[M2]`, compared with the release calendar |
| Repository named `moodle-{plugintype}_{pluginname}` | none | `[M3]` |
| A source URL (public preferred; reviewers may ask for access to a private one) | none | |
| **A public issue tracker; approval is blocked without one** | none | Open the tracker URL logged out; reviewers file their findings there |
| A documentation URL, and screenshots for the listing | none | Listing screenshots are uploaded to the listing; they are not `pix/screenshot.png` |
| The licence stated on the plugin page; GPL v3 when the plugin reproduces or adapts a substantial part of Moodle (a Boost child theme, a fork of a core plugin) | none | |
| **The package includes a licence file** (approval blocker) | none: `validate` requires only `version.php`, the lang file and, for a theme, `config.php` | `[M8]`; the check on the built ZIP is in `moodle-plugin-release` |
| Bundled third-party libraries, fonts and media may use any licence, but are declared in `thirdpartylibs.xml` | none for a missing entry; listed paths are skipped by phplint, phpcs, phpdoc and mustache, so an undeclared library shows only as a flood of phpcs errors | `[M9]` |
| You hold the rights to everything uploaded (code, images, logos, photos) | none | |
| A plugin that needs a paid service of yours is a paid listing; one listed free that needs a purchase elsewhere is removed | none | |
| A third-party service is stated in the description: what it is, what depends on it, what happens without it, how to get and configure credentials; reviewers get demo credentials | none | |

```bash
grep -nE 'requires|supported' version.php                                   # [M2]
git remote get-url origin | grep -q "moodle-$c\(\.git\)\?$" || echo "repository name"   # [M3]
git ls-files --error-unmatch LICENSE                                         # [M8] tracked, at the root
grep -o '<location>[^<]*' thirdpartylibs.xml 2>/dev/null                     # [M9] declared paths, then
find . -path ./node_modules -prune -o \( -name '*.min.js' -o -name '*.woff*' -o -name '*.ttf' \
    -o -name 'LICENSE*' -o -name 'composer.json' \) -print | grep -v '^\./LICENSE$'   # what is bundled
```

## Usability

| Rule | CI | Check |
|---|---|---|
| **Installs from the ZIP through the normal plugin installer** | none: CI installs from the git checkout | The ZIP root folder and contents: `moodle-plugin-release` |
| Non-standard post-installation steps listed in the description and the README | none | |
| Dependencies on other plugins stated in the description and README and declared in `$plugin->dependencies` | none (CI fails only if the dependency is missing from the CI site) | `[U3]`, then compare with `version.php` |
| No Composer or other build step for the administrator; the ZIP works as shipped | none | `[U4]` |
| Tested with developer debugging; no PHP warnings or notices in normal use | partly: PHPUnit and Behat fail on notices in the paths they exercise | Use each page with debugging at DEVELOPER level |
| Works on MySQL and PostgreSQL (a PostgreSQL failure blocks approval), through the DML API | partly: only the SQL the tests run, and only with both databases in the matrix; phpcs flags `AS` on table aliases | `[U6]`, and use the `$DB->sql_*()` helpers |

```bash
grep -rhoE '\b(local|block|mod|tool|filter|qtype|theme|format|report|auth|enrol)_[a-z0-9]+\\' \
    --include='*.php' . | sort -u | grep -v "^$c"                              # [U3] other components named
[ -d amd/src ] && { git ls-files amd/build | head -1; }                       # [U4] prints a file
grep -rnE 'GROUP_CONCAT|IFNULL|ILIKE|::[a-z]+\b|\bLIMIT +[0-9]|NOW\(\)|CONCAT\(' \
    --include='*.php' --exclude-dir={tests,vendor,thirdparty} .                # [U6] engine-specific SQL
```

## Coding

| Rule | CI | Check |
|---|---|---|
| Moodle coding style | phpcs, phpdoc, grunt (eslint, stylelint), mustache | Run them with `--max-warnings 0` |
| English comments, identifiers and strings | none | |
| **Every file** has the GPL boilerplate and an `@copyright` line | phpcs checks PHP files only, and only that the tag exists | `[C3]` |
| Reused or adapted code keeps the original copyright line, with yours added; it is clear which parts are yours | none | For each file copied from core or another plugin, its original `@copyright` line is still there, above yours |
| CSS scoped to the plugin's own pages (`.path-mod-myplugin .content`): every plugin's `styles.css` is served on every page | none (stylelint checks syntax) | `[C5]` |
| **Tables, settings, functions, classes, constants and global variables carry the frankenstyle prefix** (approval blocker) | tables only (`validate`); phpcs checks function names for lower case only | The namespace-collision greps in `SKILL.md` class 6 |
| Settings in `config_plugins`: `get_config('<component>', ...)`, `set_config(..., '<component>')`, `settings.php` names `<component>/<setting>` | none | `[C7]` |
| No hard-coded text: `get_string()` everywhere | none | The `moodle-string-check` command, or grep templates for literal English |
| Only `lang/en/`; translations go through AMOS after approval | none | `ls lang` prints `en` only |
| No reliance on leading or trailing spaces in strings | none | `[C10]` |
| Lang files are data only (`$string['id'] = 'value';`) | phpcs (`moodle.Files.LangFilesOrdering`) | |
| No capitalised titles in `lang/en` ("Course settings", not "Course Settings") | none | `[C12]` |
| **The privacy API, including the metadata provider, for any plugin that processes personal data or integrates with an external system** (approval blocker) | none: core's compliance test is not in the plugin's PHPUnit run | `ls classes/privacy/provider.php`; recipe and checks in `moodle-privacy-gdpr` |
| Personal data processed is described in the plugin description and in the provider | none | |
| No direct superglobals; parameter functions with the right type | none: no sniff flags `$_GET` or `$_REQUEST` | `[C15]` |
| Placeholders in every custom SQL | none | `[C16]` |
| `sesskey` checked before acting on submitted data | none | Each writing branch has `require_sesskey()`, `confirm_sesskey()`, or goes through `moodleform::get_data()` |
| `require_login()` where appropriate | phpcs warning `moodle.Files.RequireLogin` (some login call after `config.php`) | |
| Capabilities checked before showing content or acting | none | `[C19]` |
| No dangerous functions | phpcs flags `eval`, `goto`, backticks, `extract`, `error_log` and others; not `unserialize` or `call_user_func` | `[C20]` |

```bash
X='--exclude-dir=vendor --exclude-dir=thirdparty --exclude-dir=node_modules'
for f in $(git ls-files '*.mustache' '*.js' '*.scss' '*.css' ':!amd/build/*' ':!thirdparty/*'); do
    grep -q 'GNU General Public License' "$f" || echo "no boilerplate: $f"                 # [C3]
done
grep -nE '^[^@ /}][^{]*\{' styles.css 2>/dev/null \
    | grep -vE "path-$type-$short|page-$type-$short|$c|$short"                              # [C5] unscoped
grep -nE "new admin_setting_[a-z_]+\('" settings.php 2>/dev/null | grep -v "'$c/"           # [C7]
grep -rnE "set_config\('[a-z0-9_]+', [^,]+\);" --include='*.php' $X .                       # [C7] core config
grep -nE "= '\s|\s';$" lang/en/*.php                                                        # [C10]
grep -nE "= '([A-Z][a-z]+ )+[A-Z][a-z]+';" lang/en/*.php                                    # [C12]
grep -rnE '\$_(GET|POST|REQUEST|COOKIE)\[' --include='*.php' $X .                           # [C15]
grep -rn 'PARAM_RAW' --include='*.php' $X --exclude-dir=tests .                             # [C15]
grep -rnE 'get_records?_sql|execute\(|get_field_sql|_select\(' --include='*.php' $X . \
    | grep -E '\. *\$|\{\$'                                                                 # [C16]
for f in $(grep -rlE --include='*.php' --exclude-dir={classes,tests,db,lang,backup,vendor,thirdparty} \
        'require_(course_)?login\(' .); do
    grep -qE 'require_capability|has_capability|require_admin|admin_externalpage_setup' "$f" || echo "$f"   # [C19]
done
grep -rnE '\b(unserialize|call_user_func(_array)?|shell_exec|passthru|proc_open|popen)\(' \
    --include='*.php' $X .                                                                  # [C20]
```

Every line printed is a finding or needs a written reason. A grep that printed nothing proves only that the
pattern matched nothing: check that it ran on the right directory.

## Approval blockers

The page lists these as reasons a plugin will not be approved:

1. No public, accessible issue tracker.
2. Fails on PostgreSQL, even if it works on MySQL, without documented limitations.
3. Namespace collisions: missing or wrong frankenstyle prefixes.
4. Not following the Moodle security guidelines (https://moodledev.io/general/development/policies/security).
5. Processes personal data or integrates with an external system without a compliant privacy API.
6. An activity module without backup and restore. `validate` checks no `backup/` folder for a module, so CI
   passes without one: `ls backup/moodle2/backup_*_activity_task.class.php`.
7. Requires payments to the provider outside the Marketplace to access functionality.
8. Advertises paid products on third-party sites, or links to buy products outside the Marketplace.
9. Replicates differentiating functionality unique to a commercial Moodle product (for example Moodle Workplace).
10. Uses Moodle trademarks against the trademark policy.
11. Breaks the moodle.org site policy.

## What each moodle-plugin-ci command checks

| Command | Checks | Does not check |
|---|---|---|
| `phplint` | PHP syntax | Anything else |
| `phpcs` | moodle-cs on `*.php` only: style, boilerplate, `@copyright` and `@license` present, lang file syntax, a login call after `config.php`, forbidden tokens and functions | Non-PHP files, frankenstyle prefixes, capabilities, superglobals, `PARAM_RAW` |
| `phpdoc` | local_moodlecheck's remaining inline-tag rules | Most docblock rules, which moved to phpcs |
| `validate` | Required files, `pluginname` (a filter: `filtername` only), table prefixes, the `xmldb_<component>_upgrade` name, Behat feature tags | Licence file, README, other required strings, backup for a module |
| `savepoints` | `upgrade_plugin_savepoint()` calls in `db/upgrade.php` | Whether the upgrade works on real data |
| `mustache` | Template syntax, an example context, HTML validity of the rendered example | Templates under `templates/mobileapp/` |
| `grunt` | AMD build, eslint, stylelint, gherkinlint, and that `amd/build` matches `amd/src` | CSS scope |
| `phpunit`, `behat` | The plugin's own tests | Core's privacy compliance tests; anything when `tests/` is empty |
| `phpmd` | Reports only: it always exits 0 | Fails nothing |

The guidelines say the Marketplace's automated run uses moodle-plugin-ci, but not which commands, options, branch
or PHP version. Reviewers also run a separate scripted pass, whose messages read "Missing required string
(string_key: ..., component: ...)"; it is how missing `cachedef_*` and `pluginname` strings, missing licence
files, literal `mkdir` modes and `PARAM_RAW` were found. Its full list is not published.

## For a theme

- `validate` also requires `config.php`; it does not ask for `choosereadme`, which the theme selector fetches.
- Bundled fonts, icon sets and vendored SCSS or JS go in `thirdpartylibs.xml`, as Boost declares its fonts
  (`public/theme/boost/thirdpartylibs.xml`, 5.3.0).
- Most theme files are `.scss` and `.mustache`, outside phpcs's boilerplate check: add the GPL header and
  `@copyright` by hand; files copied from Boost keep Boost's copyright line.
- The CSS-scope rule cannot apply literally to a theme, whose job is site-wide CSS, and the guidelines do not say
  how it applies. Scope rules aimed at one plugin's pages to those pages.
- Theme release and listing detail: `moodle-theme-testing-release`.
