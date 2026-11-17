---
name: moodle-walkthrough
description: Use when asked to "make the walkthrough", walk through a Moodle plugin or theme on a real site, or produce screenshots and a report (usually a PDF) of what each role sees. Covers listing what to cover from the code, deploying and checking the installed version, demo courses and users made for the walkthrough, driving Chromium and Firefox with Playwright as each role at desktop and phone width, user tours and drawers that spoil shots, reading every screenshot before using it, separating plugin problems from harness problems, the report's structure, keeping the Markdown source beside the PDF with relative image links, rendering the PDF and checking it. Skip when writing automated acceptance tests (moodle-behat-testing), checking a task before calling it done (moodle-definition-of-done), or preparing a Plugins directory listing and its screenshots (moodle-marketplace-package).
---

# Moodle Walkthrough

## Overview

A walkthrough uses the plugin on a real Moodle site the way people will: as each role, through every screen,
with a screenshot of each step. The result is a report in two forms that are kept together: the Markdown file,
which is the source and the copy an assistant reads later, and a PDF made from it for people.

## When to Use

- "Make the walkthrough", "do a full walkthrough", "walk me through the plugin with screenshots"
- After a feature or a release candidate is finished, to show and check what each role sees
- When the user later says "in that walkthrough ...": open the Markdown report, not the PDF
- **Skip when:** the goal is a repeatable automated test (`moodle-behat-testing`), the pre-completion checklist
  (`moodle-definition-of-done`), or a Plugins directory listing and its screenshots (`moodle-marketplace-package`)

## Where the files go

Never inside the plugin repository: a walkthrough is about the plugin, not part of it, and screenshots would
end up in the release ZIP. Use the project's notes directory. If the project's instructions (`CLAUDE.md`, a
harness or contributing document) name one, use it, together with the test site, credentials and PDF tool they
name. Otherwise ask once where reports go.

```
<notes>/<plugin>/WALKTHROUGH-YYYY-MM-DD.md          the report: the source, kept permanently
<notes>/<plugin>/walkthrough-YYYY-MM-DD/NN-role-what.png
<notes>/<plugin>/pdf/WALKTHROUGH-YYYY-MM-DD.pdf     made from the .md, never edited on its own
```

- **Both files are kept.** The PDF is for reading; the Markdown is what an assistant opens when the user refers
  to the walkthrough later, because it is text, searchable and cheap to read. Never delete it after rendering,
  and never write the report only into the PDF tool's temporary input.
- **Image links are relative** to the `.md` file (`walkthrough-2026-11-15/03-student-view.png`), so the report
  still works when the folder is copied or read on another machine. An absolute path breaks both.
- A second walkthrough on the same day gets a suffix (`WALKTHROUGH-2026-11-15-mobile.md`), not an overwrite.
- If the notes directory has an index or README for the plugin, add one line linking the new report.

## The recipe

### 1. List what to cover, from the code

Before opening a browser, build the coverage list from the plugin itself, not from memory of what it does:

```bash
ls settings.php db/access.php *.php classes/output templates amd/src 2>/dev/null
grep -n "=> \[" db/access.php | head -40          # capabilities: each one is a role to walk
grep -c "string\['" lang/en/*.php                 # a rough size check for the UI
```

- Every page a user can open, every setting, every capability that changes what a role sees, every mode and
  option (group modes, anonymous and named, empty states, a hidden instance).
- The roles: at least admin (settings), teacher (set-up and the teacher view), student. Add the others the
  capabilities name: a non-editing teacher, a guest, a user with no enrolment.
- Width and theme cases where the plugin has UI: desktop 1280 x 900, phone 390 x 844, dark colour mode on
  Moodle 5.3, a second browser (Firefox), reduced motion if the plugin animates.
- Read the project's notes on the plugin first: an earlier walkthrough, open questions, known problems.

### 2. Prepare the site

- Deploy the current code, run the upgrade and purge caches. Then read the installed version from the site
  (`get_config('<component>', 'version')`) and check it equals `version.php`. A walkthrough of stale code is
  worthless and looks fine.
- Record for the report header: plugin release and version, Moodle version and build, theme, browsers, sizes.
- Take a snapshot of the plugin's settings (`get_config('<component>')`) before changing any, and restore it at
  the end. Compare the two in the final step.

### 3. Make demo data for the walkthrough

- Create courses, users and activities just for it, with names that say so ("Walkthrough: <feature>"). Never
  change existing accounts or courses: other people and other reports rely on them. Never reset an existing
  user's password.
- Give every course a real one-sentence description of what it is for, or none. The data generator writes
  "Test course N" and lorem ipsum when `summary` is not passed (`public/lib/testing/generator/data_generator.php`,
  5.3.0), and that text then shows in the screenshots. Do the same for activity intros.
- Build the data with one CLI script that can be re-run, so the walkthrough can be repeated. Keep the script
  with the screenshots, not in the plugin.
- Give the data a story: students at different stages, a group with members and a student in no group,
  realistic names and submissions. An empty page proves little.
- Questions go in a question bank made for the walkthrough, never a shared or system bank.

### 4. Drive the browser

Use Playwright: the skeleton, login and per-page error capture are in
[reference/playwright-recipes.md](../moodle-skill-files/moodle-walkthrough/reference/playwright-recipes.md).

- Log in through the login form with credentials the project's instructions or the user gave. Do not guess
  passwords, read password hashes or change them. If a credential is missing, stop and say so.
- A new user's first Dashboard visit opens a user tour that covers the page and makes clicks time out. Mark the
  tours done for the walkthrough users only (`tool_usertours_tour_completion_time_<tourid>` preferences),
  never by disabling tours site-wide.
- Close the block and course-index drawers (`drawer-open-block`, `drawer-open-index` preferences) when they
  would cover content.
- Logging in lands on the Dashboard, so anything that fires once per visit has already fired before the first
  explicit visit. Reset it after login if the shot needs it.
- Record console errors and failed requests on every page. A screen that looks right with a JavaScript error
  behind it is a finding.
- Name screenshots `NN-role-what.png` in walk order. Screenshot the area that matters, or the full page when the
  layout is the point.

### 5. Read every screenshot

Open each image and check it shows what its caption will say, before it goes in the report:

- the right user is logged in, the right page, the state the step describes;
- no error notice, debug output, missing-string markers (`[[stringname]]`), spinner or half-loaded page;
- nothing covers the content: a tour, a drawer, a cookie banner, a floating button;
- no placeholder content: lorem ipsum, "Test course 1", a fake-camera test pattern. Use real-looking
  content, or leave the shot out.

Retake any that fails. A walkthrough whose screenshots were not looked at reports what the script hoped for.

### 6. Findings

Sort every problem into one of two kinds and say which in the report:

- **The plugin's problems**: wrong behaviour, missing strings, layout breaks, errors, a role seeing what it
  should not. Each with the screenshot, where it happens and what was expected.
- **The walkthrough's own problems**: tours, stale caches, bad demo data. Fix them and re-shoot; mention them
  briefly so the next run avoids them.

The walkthrough reports; it does not redesign. Fix plugin defects only when the request included fixing, and
then re-run the affected steps and record each fix with its test. A finding about how a feature should work,
or a control that seems unnecessary, is a question for the user, never a change made on the walkthrough's say-so.

### 7. Write the report

```markdown
# <Plugin name> (<component>): walkthrough report

- **Date:** ... **Plugin:** <release> (<maturity>), version <version>
- **Site:** Moodle <version> (Build ...), <theme>
- **Browsers:** ... **Viewports:** ...

## Summary            a table: area, result; the count of problems found
## Problems found     numbered: what, where, screenshot, expected; fixed or open
## Demo data          the courses, users and settings, and that they were left on the site
## 1. <Area>          one section per area in walk order: a sentence or two of what was observed, then the shots
## Not covered        what was not walked or not run, in one line each, and why
## Left on the site   what the walkthrough created or changed and did not undo
```

- Write what was seen, not what the code should do. Every statement comes from the run that took the
  screenshot.
- Each screenshot has alt text saying what it shows: `![Student view, group mode, no group](...)`.
- Quote UI labels exactly as rendered.
- Put any HTML or script payload in a code span. Raw HTML in Markdown is passed through to the PDF renderer, and
  a payload such as `onerror=alert(1)` runs there and can stall the render.

### 8. Render the PDF and check it

Use the project's PDF tool if it names one. Otherwise Markdown to HTML, then headless Chromium:
[reference/playwright-recipes.md](../moodle-skill-files/moodle-walkthrough/reference/playwright-recipes.md) has a short script.

- The HTML must resolve the relative image links from the Markdown file's directory (a `<base href>` or writing
  the HTML beside the `.md`). Rendered from a temporary directory without it, every image is a broken box.
- Check the result, not the exit code: `pdfinfo` for the page count, `pdfimages -list` for the number of images
  (it should equal the screenshots in the report), and open one page to see a picture rendered. Some Chromium
  builds silently cut a long single print at a fixed page count; a page count far below what the report needs
  means the PDF is truncated.

### 9. Hand it over

Give the user both paths, the Markdown and the PDF, and send the PDF if the session can send files. Say in a
few lines: the problems found, what was fixed, what was not covered, and what was left on the site.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Only the PDF is kept | A later "in that walkthrough ..." means reading a PDF, or the report is lost | Keep `WALKTHROUGH-*.md` beside `pdf/`; the PDF is made from it |
| Absolute image paths in the `.md` | Images break when the folder is copied or read elsewhere | Relative paths from the `.md` file |
| Report or screenshots in the plugin repo | They ship in the release ZIP | The project's notes directory |
| Walking stale code | Shots of the old behaviour; fixes "not working" | Deploy, upgrade, purge, compare the installed version |
| Generator placeholders | "Test course 1" and lorem ipsum in every shot | Pass `summary` and `intro` explicitly |
| A user tour on the first visit | Clicks time out; every shot shows the tour | Mark the tours done for the walkthrough users |
| Screenshots not opened | Error notices, wrong user or a tour in the report | Read each image before captioning it |
| Changing existing users or settings | Other work breaks; the site differs after | Dedicated data; snapshot and restore settings |
| A finding treated as an order | A feature removed or redesigned unasked | Report it as a question |
| PDF checked by exit code | A truncated or imageless PDF is delivered | `pdfinfo`, `pdfimages -list`, look at a page |

## Reference files

| File | Read it when |
|---|---|
| [reference/playwright-recipes.md](../moodle-skill-files/moodle-walkthrough/reference/playwright-recipes.md) | Writing the browser script (login, tours, error capture, widths, dark mode, Firefox) or rendering the PDF without a project tool |

## References

- https://playwright.dev/python/docs/intro
- https://moodledev.io/general/development/tools/behat (the same site set-up traps apply)
