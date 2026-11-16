---
description: Use when releasing a Moodle plugin or theme, or submitting it to the Moodle Plugins directory (Marketplace): bumping $plugin->version vs $plugin->release, CHANGES.md and changelog entries, the LICENSE file and ZIP root folder a reviewer checks, building and listing the ZIP before upload (rootdirinvalid, "Missing plugin license file", "Use the plugin folder name as the root folder of the ZIP"), staging and tagging an annotated vX.Y.Z, pushing the branch before the tag, the moodle-release.yml workflow, replying to a Plugins directory reviewer's issue, and confirming the version landed. Skip when only bumping version for a schema change (the /moodle-bump-version command) finishing the change itself (moodle-definition-of-done), or auditing the code for what reviewers catch (moodle-release-preflight).
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
# Moodle Plugin Release

## Overview

A release produces three things that are checked by different people: the tagged commit (checked by CI),
the ZIP (checked by the Plugins directory reviewer and by every admin who installs it), and the listing
(read by users). CI installs the plugin from the git checkout and never sees the ZIP, so a green CI run says
nothing about the two package problems reviewers raise most: a missing licence file and a wrong ZIP root
folder. With a tag-triggered release workflow, pushing the tag publishes it, so every step before the push
is read back, not assumed.

## When to Use

- A release has been decided on and the version bump approved
- A first submission to the Moodle Plugins directory, or a resubmission after review
- Setting up tag-triggered publishing, or checking whether a pushed tag actually arrived
- A Plugins directory reviewer opened an issue and you are writing the reply (the code fix itself is
  `moodle-release-preflight`)
- **Skip when:** the change only needs a `$plugin->version` bump for a schema change (`/moodle-bump-version`),
  or QA is still open (walk `moodle-definition-of-done`, and `moodle-release-preflight` for the security and
  approval-blocker classes, first). Theme-specific release checks are in `moodle-theme-testing-release`.

## 0. Preconditions: stop if any fails

- **The bump was asked for.** A release is a decision, not a side effect of other work. Default to a patch
  (`z`) increment; a minor or major bump needs a stated reason.
- **QA is done**: `moodle-definition-of-done` walked for everything going into the release;
  `moodle-release-preflight` walked when the plugin is being submitted or its security surface changed.
- **Every step of the plugin's own CI workflow has been run locally, as written, with its flags**, and each
  exit code and output read. A look-alike local gate is a different gate: phpcs does not run the `phpdoc`
  (moodlecheck) rules, a local `grunt` with other options skips stylelint or gherkinlint, and a missing
  `@param` found by Actions after tagging costs a new release. Read the workflow first:

  ```bash
  grep -n 'moodle-plugin-ci' .github/workflows/*.yml
  ```

  The command-by-command recipe and each command's exit-code traps (`phpmd` always returns 0, which commands
  take `--max-warnings`) are owned by `moodle-definition-of-done`.
- **A gate that runs only after the tag is pushed cannot fix that tag.** Anything that validates the release
  itself (a listing or metadata check, a packaging script, a release preview) runs before tagging.

## 1. `version.php`: two different numbers

```php
$plugin->component = 'local_myplugin';
$plugin->version   = 2026111600;          // YYYYMMDDXX build number: must strictly increase.
$plugin->release   = '1.4.2';             // Human release name: bumped deliberately.
$plugin->requires  = 2026042000;          // Lowest Moodle build: here 5.2.0.
$plugin->supported = [502, 503];          // Range [low, high] of Moodle branches.
$plugin->maturity  = MATURITY_STABLE;
```

| Number | When it changes | Rule |
|---|---|---|
| `version` | Any schema, upgrade, capability, cache-definition or service change must bump it; every release bumps it | Strictly greater than every shipped value |
| `release` | Only when cutting a release | Does not ride along with a schema bump; patch by default |

- `supported` must be a two-integer range, low first. `[502]` throws `coding_exception` "Incorrect syntax in
  plugin supported declaration" when the plugin is loaded; write `[502, 502]` for one branch
  (`\core\plugininfo\base::load_disk_version()`, `public/lib/classes/plugininfo/base.php`, 5.2 and 5.3.0).
- `requires` is not below the lowest branch in `supported`, or the plugin claims a branch it refuses to
  install on. 5.2.0 is build `2026042000` and 5.3.0 is `2026100500` (`$version` in `public/version.php` at the
  `v5.2.0` and `v5.3.0` tags). Use the `x.y.0` build, not the value of the tree you develop on: a 5.2.2 tree
  says `2026042002.01`, which locks out 5.2.0 and 5.2.1 sites.
- The directory reads the release name, maturity and supported versions from the uploaded ZIP; they can be
  overridden per version but default to what `version.php` says
  (https://moodledev.io/general/community/plugincontribution/pluginsdirectory/api, which documents the older
  moodle.org web service).

## 2. Release notes and docs: one consistent story

- `CHANGES.md` (if the plugin uses it): this version's notes only, replacing the previous body. The release
  workflow of section 6 submits the whole file as the version's release notes: it takes, in order, its
  `release_notes` input, the body of the GitHub Release for the tag, then the first of `CHANGES.md`,
  `CHANGES.txt`, `CHANGES.html`, `CHANGES`, `CHANGELOG.md` (and the same variants) or `UPGRADING.md` in the
  repository root (`moodlehq/moodle-plugin-release`, workflow revision 2026091801, read, not run). When neither
  the input nor a GitHub Release supplies the notes, a cumulative changelog with no `CHANGES.md` beside it is
  published in full on every version.
- `changelog.md` / `CHANGELOG.md`: prepend `## [x.y.z] - YYYY-MM-DD` with `### Added / Changed / Fixed /
  Security` (Keep a Changelog). Keep the file name the repository already uses.
- `README.md`: supported Moodle versions match `$plugin->supported`; requirements, settings and
  post-install steps match the code.
- **Write the notes against the previous release, not the previous commit.** A list built from the last
  commit misses everything merged since the last tag. Generate the raw list from the tag:

  ```bash
  prev=$(git describe --tags --abbrev=0 HEAD^)
  git log --oneline "$prev"..HEAD
  git diff --stat "$prev"..HEAD
  ```

- **A note claims only checks that were run**, on this commit, by name ("PHPUnit 42 tests on 5.3.0"), never
  "fully tested".
- **Manuals and translations are release artifacts.** A user manual or help page that names a renamed or
  removed setting, field or page is updated in the same release; a removal is the dangerous case, because the
  doc becomes wrong rather than incomplete. A translation kept outside the release (for AMOS) is diffed against
  `lang/en` at each release; recipe in [reference/zip-package.md](../moodle-skill-files/moodle-plugin-release/reference/zip-package.md).

## 3. The package: what the reviewer checks first

Most review findings on Plugins directory submissions are about the ZIP, not the code, and no CI step can
see them. Build the ZIP, list it, and fix the repository before tagging.

- **A licence file in the plugin root.** The submission guidelines require the package to include a licence
  file; its absence is an approval blocker ("Missing plugin license file", priority blocker). `moodle-plugin-ci
  validate` requires only `version.php`, the lang file and, for a theme, `config.php`, so CI stays green
  without it. Fix: commit the full licence text as `LICENSE` in the repository root (GPL v3 text for a plugin
  that adapts Moodle code, which a Boost child theme does), make sure `.gitattributes` does not
  `export-ignore` it, and push it before the tag. A licence file added after the tag, or committed but not
  pushed, is still missing from the reviewed ZIP.
- **One root folder, named after the plugin without its type.** `local_myplugin` ships as `myplugin/`,
  `mod_forum` as `forum/`, `theme_mytheme` as `mytheme/`. A GitHub source archive has the root
  `moodle-local_myplugin-1.4.2/`. Core's validator requires a single root directory whose name survives
  `clean_param(..., PARAM_PLUGIN)` ("rootdirinvalid" otherwise) and equals the name part of
  `$plugin->component` ("componentmismatchname") (`\core\update\validator::validate_files_layout()` and
  `validate_version_php()`, `public/lib/classes/update/validator.php`, 5.3.0, identical in 5.2). Core's own
  help string names GitHub archives as the usual cause (`public/lang/en/plugin.php`,
  `validationmsg_rootdirinvalid_help`). The admin upload page can rename the
  root while extracting when it detects the component from `version.php`, so a wrong root sometimes installs
  through the UI; it still fails for an admin who unzips into `local/` by hand, and reviewers flag it every
  time.
- **Build it with `git archive` from the tag, then list it**:

  ```bash
  name=myplugin                                   # component local_myplugin
  git archive --format=zip --prefix="$name/" -o "../$name.zip" v1.4.2
  unzip -Z1 "../$name.zip" | cut -d/ -f1 | sort -u                       # prints only: myplugin
  unzip -Z1 "../$name.zip" | grep -xE "$name/(LICENSE|version\.php)"     # prints both
  unzip -Z1 "../$name.zip" | grep -E '(^|/)(node_modules|\.git|\.github)/' # prints nothing
  ```

  Then read the whole listing once: `lang/` holds only `en/`, `amd/build/` is present and current when
  `amd/src/` exists, no build output, logs or editor files. `.gitattributes` `export-ignore` lines decide what
  `git archive` leaves out; full checklist in [reference/zip-package.md](../moodle-skill-files/moodle-plugin-release/reference/zip-package.md).
- **Only `lang/en/` ships.** Other languages reach sites through AMOS after approval, and an installed AMOS
  language pack overrides a plugin's bundled `lang/xx` strings key by key, so a bundled translation is both
  against the guidelines and silently shadowed. The repository-level check is in `moodle-release-preflight`.
- **Bundled third-party code, fonts and icons are declared in `thirdpartylibs.xml`.** The guidelines require
  it; it also takes those paths out of `moodle-plugin-ci`'s analysis commands. Format in
  [reference/zip-package.md](../moodle-skill-files/moodle-plugin-release/reference/zip-package.md).
- **The ZIP works out of the box.** Admins must not need Composer, npm or a build step: compiled `amd/build`
  files are committed, `vendor/` code the plugin needs is shipped and declared.

## 4. Stage by path, commit, read back, tag

Other work may be sitting in the tree. Stage named paths, never `git add -A`, and re-read
`git status --porcelain` just before staging; investigate any file you did not expect rather than sweeping it
in or deleting it. "Everything is new" on a first commit is not an exception, and `.gitignore` is not a
substitute for reading the list.

```bash
git add version.php CHANGES.md CHANGELOG.md README.md
git commit -m "Release 1.4.2: <one-line summary>"
git show --stat HEAD                       # the file list must match the release notes
git tag -a v1.4.2 -m "1.4.2: <one-line summary>"
git describe --tags --exact-match HEAD     # the tag is on the commit you just read
```

If the read-back surprises you before anything is pushed, delete the local tag and fix the commit. Once a
tag or a commit may be on the remote, the rules change: see section 5.

## 5. Push: the branch first, the tag after its CI run is green

1. Push the branch only: `git push origin main`.
2. Wait for that commit's CI run and read its result. A local pass on a development site with extra plugins
   is not the same run: the CI site has only standard plugins, other databases and other PHP versions.
3. Push the one tag: `git push origin v1.4.2`.

- **Tag only a commit whose CI run is green.** If the commit is already pushed and red, fix it in a new
  commit and tag that one.
- **Never move or re-create a tag that may be published.** A tag the release workflow saw has already been
  sent to the Plugins directory, and other clones have it. Read the remote first, over the network, not from
  memory or an old note:

  ```bash
  git ls-remote origin 'refs/tags/v1.4.2*'     # any output: the tag is published
  git fetch origin && git branch -r --contains HEAD   # any output: the commit is pushed, never amend it
  ```

  New work goes into the next version. A failed remote read (authentication, network) is not evidence that the
  tag is absent. Detail in [reference/fixing-a-release.md](../moodle-skill-files/moodle-plugin-release/reference/fixing-a-release.md).
- **Push at most three tags per `git push`.** GitHub creates no push event when one push updates more than
  three tags, so no tag-triggered workflow runs and nothing is published
  (GitHub's "Events that trigger workflows" page, `push` event:
  https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#push).
  Never `git push --tags` for a batch; one tag per push is the safe habit.
- **When someone else runs the push, say what it does**: "pushing tag v1.4.2 publishes it to the Moodle
  Plugins directory". They can then hold the tag back if they meant to push only the branch.

## 6. Publishing with GitHub Actions

Moodle HQ's reusable workflow publishes a release when a `v*` tag is pushed:

```yaml
# .github/workflows/moodle-release.yml
name: Release Plugin version to Moodle Marketplace
on:
  push:
    tags: ['v*']
  workflow_dispatch:
    inputs:
      tag:
        description: 'Tag to be released (e.g. v1.4.0)'
        required: true
jobs:
  release-to-marketplace:
    uses: moodlehq/moodle-plugin-release/.github/workflows/moodle-release.yml@main
    with:
      tag: ${{ inputs.tag }}
    secrets:
      MOODLE_MARKETPLACE_TOKEN: ${{ secrets.MOODLE_MARKETPLACE_TOKEN }}
```

- The plugin must already be approved in the directory. **The first submission is always a hand-built ZIP**
  (section 3), because the workflow can only add versions to an existing plugin.
- **The workflow builds the same ZIP as section 3.** It checks out the tag, reads `$plugin->component` from
  `version.php`, and runs `git archive --format=zip --prefix="<name>/" HEAD` with the type prefix removed
  (workflow revision 2026091801, read, not run). So `.gitattributes` `export-ignore` lines and uncommitted
  files affect the published ZIP exactly as they affect a hand-built one, and a wrong `component` line stops
  the run.
- The token is created on the Moodle Marketplace under "Account Settings > Security"
  (https://marketplace.moodle.com/account/security), shown once, and stored as the repository secret
  `MOODLE_MARKETPLACE_TOKEN` (the workflow's README). The moodledev.io Plugins directory API page still
  describes the older moodle.org "Plugins > API access" token, which this workflow does not use. Never put a
  token in a URL or an echoed argument in a workflow; mask a computed secret with `echo "::add-mask::$value"`
  before using it.
- A red run usually means a missing or expired token secret. Fix the secret, then re-run with
  `workflow_dispatch` and the tag; do not re-tag.
- The tag-push run uses the workflow file in the tagged tree. If that file was broken, fix it on the default
  branch and dispatch the run there with the tag as input; never move the tag. (Reasoned from GitHub's
  documented event behaviour, not run.)

## 7. A pushed tag is not a published release

Confirm ingestion downstream. These are anonymous HTTPS reads; a successful read is evidence, a failed one is
not a "no".

- **Plugins directory**: the release workflow run went green, then the version is in the public plugin list.
  The plugin page fills version numbers in by script, so grepping its HTML finds nothing:

  ```bash
  curl -fsSL https://download.moodle.org/api/1.3/pluglist.php | python3 -c '
  import json, sys
  p = [x for x in json.load(sys.stdin)["plugins"] if x["component"] == "local_myplugin"][0]
  print(sorted((v["version"], v["release"]) for v in p["versions"])[-3:])'
  ```

  The endpoint a site itself asks when it installs or updates the plugin is `pluginfo.php`, which answers 404
  for a version it does not know (`\core\update\api::get_plugin_info()` and `call_pluginfo_service()`,
  `public/lib/classes/update/api.php`, 5.2 and 5.3.0; read, not run for this skill):

  ```bash
  curl -s -o /dev/null -w '%{http_code}\n' \
    'https://download.moodle.org/api/1.3/pluginfo.php?plugin=local_myplugin@2026111600&format=json'   # 200
  ```

- **Packagist** (if the plugin has `composer.json`): the newest version Composer clients will see. Until this
  prints the new tag, no client-side cache clearing helps. Packagist offers only `dev-main` until a tag
  exists whose tree contains `composer.json`.

  ```bash
  curl -s https://repo.packagist.org/p2/<vendor>/<package>.json \
    | python3 -c "import json,sys;d=json.load(sys.stdin);k=list(d['packages'])[0];print(d['packages'][k][0]['version'])"
  ```

- `moodle/composer-installer` places a package by its `type` (`moodle-local`, `moodle-mod`, ...) and knows only
  the plugin types in its own data, so a sub-plugin of a third-party parent stops with "Unable to install
  package of type ..., unknown plugin type ..." until the installer adds that type (read in its
  `src/Composer/MoodleInstaller.php` and `DataProviders/ContribData.php`, not run). Say so in the README.

Record the release as "committed and tagged, push pending" until the push is confirmed, never as pushed.

## 8. The first submission and the listing

The listing is reviewed with the ZIP. What the submission guidelines require, and what nothing automated
checks, is in [reference/plugins-directory-submission.md](../moodle-skill-files/moodle-plugin-release/reference/plugins-directory-submission.md): a public
issue tracker (required for approval), a short and a full description, screenshots, documentation URL, the
licence named on the page, dependencies and post-install steps stated in both the description and the
README, and demo credentials for any external service.

- **Publication material is checked like code.** Every tool or command the text recommends is current;
  every claim about users or sites is one you can support; every screenshot is read for its proper nouns
  (course, user and site names), which must be demo data you chose, not test leftovers.
- **Put a README caveat where admins read it too.** A limitation stated only in the README (for example that a
  feature does not use the site proxy) still gets raised in review; repeat it in the setting's description
  string.

## 9. Answering a Plugins directory reviewer

Reviewers file each finding as an issue on the plugin's tracker, with a priority and sometimes an
"Approval blocker" label. Answer on the issue:

- Name the release and commit that fixes it, say what changed, and say what you found when you looked for the
  same defect elsewhere in the plugin (reviewers report one instance; a second one in a CLI script or a sibling
  action is common).
- **A reasoned no is accepted.** When a suggestion does not fit, say exactly why. Two kinds of refusal have been
  approved without a code change: a narrower `PARAM_*` type that would corrupt valid input (`PARAM_USERNAME`
  strips `+`, `PARAM_ALPHANUMEXT` strips the dot in `5.2`), and course-scoped operational records deliberately
  left out of backup and restore, with the reason written in the README.
- **Verify a suggested fix before applying it.** Test the suggested type or API against real values first.
  Documentation links in reviews often point at an older Moodle version's page; read the page for your
  supported branch.
- Code-level findings (frankenstyle prefixes, `PARAM_RAW`, capabilities, directory permissions, caching) are
  `moodle-release-preflight`'s checks; run them before submitting.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No `LICENSE` in the repository root, or export-ignored | Approval blocked: "Missing plugin license file"; CI green | Commit the full text as `LICENSE`; list the ZIP |
| ZIP from GitHub's "Source code" download | Root `moodle-local_x-1.0.0/`: `rootdirinvalid`, reviewer finding | `git archive --prefix=<name>/` from the tag |
| Licence added after the tag | The reviewed ZIP still lacks it | Push it before tagging; release a new version |
| `release` bumped with every schema change | Release names drift from real releases | Bump `version` for schema; `release` only when releasing |
| Tagging after phpcs alone | CI fails `phpdoc` or stylelint after the tag is public | Run every step of the plugin's CI workflow first |
| `git add -A` for the release commit | Unrelated files shipped and tagged | Stage named paths; read `git show --stat` |
| Tag pushed with the branch | Published before CI ran; a red tag cannot be unpublished | Branch, green CI, then the tag |
| Moving a published tag to add a fix | Clones and the directory disagree on what the version is | New commit, new version |
| `git push --tags` with 4+ new tags | No workflow runs, nothing published | At most three tags per push; one is safer |
| `$plugin->supported = [502]` | `coding_exception` on load | `[502, 502]` |
| Notes written from the last commit | Changes since the previous tag missing | `git log <prevtag>..HEAD` |
| Treating a pushed tag as released | Users cannot see the version; time lost on caches | Workflow run, plugin list API, Packagist p2 JSON |
| Applying a reviewer's suggested type unchecked | Valid input corrupted | Test it; answer with a reasoned no if it does not fit |

## Reference files

| File | Read it when |
|---|---|
| [reference/zip-package.md](../moodle-skill-files/moodle-plugin-release/reference/zip-package.md) | Building the ZIP by hand (first submission), writing `.gitattributes`, declaring bundled libraries or fonts in `thirdpartylibs.xml`, diffing a translation against `lang/en`, or debugging a "rootdirinvalid" or "componentmismatchname" install error |
| [reference/plugins-directory-submission.md](../moodle-skill-files/moodle-plugin-release/reference/plugins-directory-submission.md) | Submitting a new plugin, filling in or changing the listing, preparing screenshots, or deciding what a reviewer will raise that CI does not check |
| [reference/fixing-a-release.md](../moodle-skill-files/moodle-plugin-release/reference/fixing-a-release.md) | A tag already exists and something in that release is wrong, a release workflow run failed, or you are unsure whether a commit or tag is on the remote |

## References

- Version file: https://moodledev.io/docs/apis/commonfiles/version.php
- Third-party libraries: https://moodledev.io/docs/apis/commonfiles/thirdpartylibs.xml
- Plugins directory web service (the older moodle.org API): https://moodledev.io/general/community/plugincontribution/pluginsdirectory/api
- Marketplace API, as linked from the release workflow's README: https://moodledev.io/general/community/plugincontribution/moodlemarketplaceapi
- Release workflow: https://github.com/moodlehq/moodle-plugin-release
- Moodle Marketplace plugin submission guidelines: https://moodle.atlassian.net/wiki/external/ODRhYjAyNTY4NDVmNGJlNjljN2ViMzkwYzdmYmIwMGI
- moodle-plugin-ci: https://moodlehq.github.io/moodle-plugin-ci/
- See also: `moodle-definition-of-done`, `moodle-release-preflight`, `moodle-ci-matrix`, `moodle-theme-testing-release`
