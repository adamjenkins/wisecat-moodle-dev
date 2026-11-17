# moodle-marketplace-package

> Use when asked to prepare a Moodle Plugins directory (Marketplace) submission or listing update - "make the Marketplace package", "publishing docs", listing text, screenshots for the plugin page. Produces one folder per release with listing.txt (every form field ready to paste: name, type, component, short description, full description as HTML, source control URL, bug tracker URL, documentation URL, supported versions, maturity, release notes, screenshot captions), listing.md (where each claim and screenshot came from), the numbered screenshots and the release ZIP. Covers reading the field values from version.php, the git remote and the README, checking the issue tracker is enabled, writing descriptions that make only checked claims, and taking listing screenshots. Skip when building the ZIP, tagging or answering a reviewer (moodle-plugin-release), auditing the code before release (moodle-release-preflight), or making an internal walkthrough report (moodle-walkthrough).

# Moodle Marketplace Package

## Overview

Everything needed to submit a plugin, or a new version, to the Moodle Plugins directory, gathered in one folder so
that submitting is copy, paste and upload. The rules the listing must meet (required tracker, licence, service
disclosure) are owned by `moodle-plugin-release`; this skill produces the files.

## When to Use

- "Make the Marketplace package", "prepare the publishing docs", "write the listing" for a plugin or theme
- A first submission, a new version upload, or a change to the listing text or screenshots
- **Skip when:** building the ZIP itself, tagging or replying to a reviewer (`moodle-plugin-release`), auditing the
  code for review findings (`moodle-release-preflight`), or an internal walkthrough (`moodle-walkthrough`)

## Where the files go

Outside the plugin repository, in the project's notes directory (the project's instructions name it; otherwise
ask once). One folder per release, never overwritten:

```
<notes>/<plugin>/marketplace-<release>/
    listing.txt            every field, ready to paste; open in any text editor
    listing.md             provenance: commit, screenshot site, demo data, how each claim was checked
    01-<what>.png ...      screenshots, in upload order
    <name>-<release>.zip   the release ZIP (built with moodle-plugin-release)
```

For a new version of a plugin already listed, copy the previous folder's text and screenshots forward, change
what the release changed, and say in `listing.md` what was carried over and why it still holds.

## listing.txt

A plain text file (`.txt`, so it opens in any editor) with one labelled block per form field, in the form's order.
The short description is plain text. The full description is HTML, because the directory's description field
takes formatted text; keep to simple tags (`<p>`, `<h3>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<a>`,
`<code>`), no styles, classes or scripts.

```text
PLUGIN NAME
Scribbles

PLUGIN TYPE
Local plugins

COMPONENT
local_scribbles

SHORT DESCRIPTION
Draw on any Moodle page with pen, highlighter, text, box and ellipse tools, then save the annotations or a screenshot.

FULL DESCRIPTION (HTML)
<p>Scribbles lets teachers draw on any Moodle page. ...</p>
<h3>Who it is for</h3>
<p>...</p>
<h3>Features</h3>
<ul>
<li>...</li>
</ul>
<h3>Requirements</h3>
<ul>
<li>Moodle 5.2 or 5.3.</li>
</ul>
<h3>Privacy</h3>
<p>...</p>

SOURCE CONTROL URL
https://github.com/<owner>/moodle-local_scribbles

BUG TRACKER URL
https://github.com/<owner>/moodle-local_scribbles/issues

DOCUMENTATION URL
https://github.com/<owner>/moodle-local_scribbles#readme

SUPPORTED MOODLE VERSIONS
5.2, 5.3

MATURITY
Beta

RELEASE NAME
0.1.1

VERSION
2026110404

RELEASE NOTES
- ...

LICENCE
GNU GPL v3 or later

SCREENSHOTS (upload in this order)
01-annotate-course-page.png
A course page annotated with the pen, highlighter, box and text tools.
02-...
```

Where each value comes from (never from memory):

| Field | Source |
|---|---|
| Plugin name | `pluginname` in `lang/en/<component>.php` (`modulename` for an activity) |
| Type and component | `$plugin->component` in `version.php`; the type is its prefix, named as the directory names it ("Activities", "Blocks", "Local plugins") |
| Supported versions | `$plugin->supported`, checked against `$plugin->requires` and the CI matrix |
| Maturity, release, version | `$plugin->maturity`, `$plugin->release`, `$plugin->version` at the release tag |
| Source control URL | `git remote get-url origin`, written as the `https://` web URL |
| Bug tracker URL | the repository's issues page; check issues are enabled (`gh api repos/<owner>/<repo> --jq .has_issues` is `true`): a tracker is required for approval |
| Documentation URL | the README on the forge (`...#readme`), or the plugin's documentation page if one exists |
| Release notes | this release's section of `CHANGES.md` (or the changelog the repository keeps) |
| Licence | the `LICENSE` file and the file headers |

If the plugin needs an external service, the full description says so, what depends on it, what happens without
it and how to get credentials, and `listing.txt` has a block of demo credentials for the reviewer
(`moodle-plugin-release`, reference `plugins-directory-submission.md`).

## Writing the descriptions

- **Short description:** one or two sentences: what it does and for whom. It shows in search results.
- **Full description:** what it does, who it is for, the features, what administrators set up, limits,
  requirements (Moodle and PHP versions, databases tested, other plugins, services), privacy (what personal
  data it stores and where it is sent). Same facts as the README.
- Every claim is one you checked: a feature you saw on the site, a version CI ran, a capability in
  `db/access.php`. Record the check in `listing.md`. "Works in all browsers" without testing them is not a claim
  to make; say which were tested.
- State limits plainly. A reviewer or an admin finding an unstated limit costs more than the sentence.
- Name settings and labels exactly as they appear in the UI, with the settings path
  (`Site administration > Plugins > Local plugins > Scribbles`).
- No marketing superlatives, no comparisons with other plugins, no Moodle trademark misuse.

## Screenshots

Take them with the `moodle-walkthrough` recipe (demo data, Playwright, read each image), with these listing rules:

- The current release's code, on a stock Boost site, light mode, at least 1280 x 800 (a 1.5x device scale gives
  sharper images). Crop to the plugin's UI where the rest of the page adds nothing.
- Every visible name is demo data chosen for the listing: course, users, site name. Read every proper noun in
  each image. No test leftovers, no other plugins' buttons, no offensive or placeholder text.
- 4 to 10 images, in the order a new user meets the plugin; the first one shows it doing its main job.
- Each has a one-sentence caption in `listing.txt`.

## listing.md

The record a later release, or a reviewer's question, needs:

- the commit and tag the package was made from, and whether CI passed on it;
- the site, Moodle version and theme the screenshots were taken on, and that the deployed code matched the commit;
- the demo data and whether it is still on the site;
- a table of screenshots with captions;
- "How the claims were checked": one line per claim that needed checking.

## The ZIP

Build and inspect it with `moodle-plugin-release`: its root folder is the plugin directory name, `LICENSE` is in
it, `lang/` holds only `en/`. Put the ZIP in the folder so the upload is from the same place.

## Hand it over

Give the folder path and say what to do: on a first submission, create the plugin in the directory and fill each
field from `listing.txt`; on a version, upload the ZIP with the release notes. Submitting is the maintainer's
action: prepare it, do not submit.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Full description as plain text | Paragraphs and lists run together on the plugin page | HTML in `listing.txt`, simple tags only |
| Values typed from memory | The listing's versions or maturity disagree with `version.php` | Read each from the source in the table |
| Issues disabled on the repository | Approval is blocked: the reviewer has nowhere to file | Check `has_issues`, enable it |
| Claims nobody checked | A reviewer or admin finds the plugin does not do what the page says | Record each check in `listing.md` |
| Screenshots from an old build or with test names | The page shows the wrong UI or someone's real data | Current code, demo data, read every image |
| Package folder inside the repository | Screenshots and the ZIP end up in the next release | The notes directory |
| A new version overwrites the last folder | The record of what was submitted is lost | One folder per release |

## References

- https://moodledev.io/general/community/plugincontribution/checklist
- https://moodle.org/plugins
