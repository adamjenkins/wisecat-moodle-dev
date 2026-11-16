# Submitting to the Moodle Plugins directory (Marketplace)

Read this when you submit a new plugin, fill in or change its listing, prepare listing screenshots, or want to
know which review findings CI cannot catch.

The controlling text is the Marketplace "Plugin submission guidelines" page
(https://moodle.atlassian.net/wiki/external/ODRhYjAyNTY4NDVmNGJlNjljN2ViMzkwYzdmYmIwMGI). The moodledev.io
"plugin contribution checklist" is marked by its own banner as the legacy process, not to be used for new
submissions; most of its rules carried over, with the differences listed at the end of this file.

## How a review works

- You upload a ZIP and fill in the listing. A reviewer installs the ZIP, runs automated checks, reads the code,
  and files each finding as an issue on the tracker you gave, with a priority (blocker, high, medium, low) and,
  for some, an "Approval blocker" label.
- The guidelines recommend `moodle-plugin-ci` because it is "the same tool used to run automated tests during
  Moodle Marketplace review". They do not say which commands, options, Moodle branch or PHP version the review
  uses. Run the full set from `moodle-ci-matrix` on every supported branch, with `--max-warnings 0`.
- The review also runs checks `moodle-plugin-ci` does not have: required strings beyond `pluginname`, a licence
  file, unprefixed global functions, a missing `backup/moodle2` for course-scoped tables, literal `mkdir()`
  modes, `PARAM_RAW` use. Its full list is not published.
- Each finding is answered on its issue, by a fix or by a reasoned refusal (`SKILL.md` section 9).

## What CI checks and what it does not

`moodle-plugin-ci` 4.5 (read in its source, not observed in a review):

| Guideline | Checked by CI | Not checked |
|---|---|---|
| Coding style, boilerplate, `@copyright`, `@license` | `phpcs`: PHP files only | Templates, SCSS, CSS, JS headers: add the boilerplate by hand |
| Lang file is data only | `phpcs` (`moodle.Files.LangFilesOrdering`) | Strings that exist but are wrong |
| `require_login()` after `config.php` | `phpcs` warning | Whether a capability is checked |
| Table prefix in `install.xml` | `validate` | Prefix of functions, classes, constants, settings |
| Required files | `validate`: `version.php`, the lang file, `pluginname` (a filter: `filtername`), a theme's `config.php` | `LICENSE`, `README`, `thirdpartylibs.xml`, privacy provider, `backup/` for an activity |
| Works on PostgreSQL and MySQL | Only the SQL the tests run, on the databases in the matrix | Everything untested |
| No PHP notices at developer debugging | Only the paths `phpunit --fail-on-warning` and `behat` reach | Everything else |

A filter passes `validate` with `filtername` but no `pluginname`; the review asks for `pluginname`. Satisfy
both. A plugin with `db/caches.php` needs a `cachedef_<area>` string for each definition, and a theme needs
`choosereadme` (the theme selector's preview fetches it,
`public/admin/amd/src/themeselector/preview_modal.js`, 5.3.0); neither is checked by CI.

## The listing

| Field | Requirement | Notes |
|---|---|---|
| Short description | One or two sentences, English | Shown in search results |
| Full description | English; same information as the README is encouraged | State dependencies, post-install steps, external services and what personal data the plugin processes |
| Supported versions | At least one currently maintained Moodle version | Read from `version.php`; keep the README in step |
| Source code URL | Public preferred; private allowed, reviewers may ask for access | Repository name `moodle-{type}_{name}` |
| Issue tracker | Required for approval; public and accessible | The reviewer files findings there, so issues must be enabled |
| Documentation URL | A place for further documentation | Keep it in step with the README |
| Screenshots | Required: what it looks like and how it works once installed | Used on the plugin page and may be used elsewhere on the Marketplace |
| Licence | Stated on the page, and a licence file in the package | Full text as `LICENSE` in the package root |

The guidelines give no size, number or format for screenshots. Practical rules:

- Show the plugin doing its job on a stock Boost site, with the plugin's own UI in frame and readable.
- Every visible name (course, user, site, organisation) is demo data you chose. Read every proper noun in each
  image before uploading; test leftovers in a public screenshot are the usual slip.
- Real screenshots only: no placeholder images or mock-ups presented as the product.
- For a theme the listing screenshots are the main evidence of what it does; they are separate from
  `pix/screenshot.png`, which the site's theme selector shows (`moodle-theme-testing-release`).

## Commercial and service rules

- A plugin that needs a paid service from its provider is submitted as a paid plugin. Listing it as free while
  requiring a subscription elsewhere is a removal reason, and so are advertising or purchase links for products
  outside the Marketplace.
- A plugin that needs any third-party service says so in the description, explains what depends on it and what
  happens when it is not configured, explains how to get credentials, and gives reviewers demo credentials.
- Replicating functionality unique to a commercial Moodle product (Moodle Workplace is the named example) and
  misuse of Moodle trademarks are approval blockers.

## Approval blockers named by the guidelines

1. No public, accessible issue tracker.
2. Fails on PostgreSQL even if it works on MySQL, without documented limitations.
3. Namespace collisions: missing or wrong frankenstyle prefixes on tables, settings, functions, classes,
   constants or variables.
4. Not following Moodle's security guidelines.
5. Processes personal data or talks to an external system without a compliant privacy provider.
6. An activity module without the backup and restore API.
7. Requires payments to the provider outside the Marketplace.
8. Advertising for paid products on third-party sites, or links to buy them.
9. Replicates differentiating functionality of a commercial Moodle product.
10. Violates the Moodle Trademarks Policy.
11. Violates the moodle.org site policy.

Blockers 3 to 6 are code checks owned by `moodle-release-preflight`; walk it before submitting. The licence
file is not on this list but is raised with priority blocker under "Licensing/IP compliance".

## Findings reviewers raise that CI never sees

Grouped from real review rounds on several plugins. Each has a pre-submission check.

| Finding | Pre-submission check |
|---|---|
| Missing licence file | `unzip -Z1 <zip> \| grep -x '<name>/LICENSE'` |
| ZIP root is not the plugin name | `unzip -Z1 <zip> \| cut -d/ -f1 \| sort -u` prints only `<name>` |
| Missing language strings (`pluginname`, `cachedef_<area>`) | For each key in `db/caches.php`, grep `cachedef_<key>` in the lang file; grep every literal `get_string()` and `{{#str}}` key |
| Global function without the full component prefix | The namespace-collision grep in `moodle-release-preflight` |
| `PARAM_RAW` where a narrower type fits | `grep -rn 'PARAM_RAW' --include=*.php .`; each hit gets a narrower type or a one-line reason |
| `mkdir($dir, 0777, true)` | Use `make_temp_directory()`, `make_request_directory()` or `$CFG->directorypermissions` |
| Pages with `require_login()` but no capability | For each page script, list its `require_capability()`; justify each page without one |
| A rule enforced on one action but not its siblings | For each write action, compare the checks its sibling actions make |
| Per-call DB queries in a hot path (filters, renderers) | Count queries around the path in a PHPUnit test with `$DB->perf_get_queries()` |
| Course-scoped tables with no backup and restore | For each table keyed by course, decide yes or no and write the reason in the README |
| A README caveat missing from the settings page | Repeat it in the setting's description string |

## Theme notes

Nothing in the guidelines is theme-specific. What follows from the general rules:

- A theme scopes CSS it adds for its own pages and settings and does not ship rules aimed at one third-party
  plugin; the namespaced-CSS rule is written for ordinary plugins, and how reviewers apply it to themes is not
  documented.
- A theme that stores a user preference processes personal data and declares it in a privacy provider; one that
  stores nothing ships a `null_provider`.
- Fonts, icon sets and vendored SCSS or JS are declared in `thirdpartylibs.xml`; stock photos and logos need
  rights you hold.
- Files copied from Boost or another theme keep their original `@copyright` line, with yours added below.

## Differences from the legacy checklist

- Licence: the legacy page required GPL v3 for interface files and GPL-compatible third-party files. The current
  guidelines let the provider choose, require GPL v3 only for code that reproduces or adapts a substantial part
  of Moodle, allow bundled files under any licence, and newly require a licence file in the package and a
  `thirdpartylibs.xml` declaration.
- The issue tracker changed from recommended to required.
- Coding style changed from "encouraged" to "follow", with the `moodle-plugin-ci` recommendation added.
- Privacy widened from "integrates with an external system" to "or processes personal data".
- The paid-service, advertising and commercial-product blockers are new or reworded.
