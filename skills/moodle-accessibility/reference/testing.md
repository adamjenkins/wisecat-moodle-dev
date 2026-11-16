# Accessibility testing: Behat axe steps, axe outside Behat, manual checks

Read this when writing or debugging `@accessibility` Behat scenarios, running axe outside Behat, or doing the manual
keyboard, screen-reader, zoom and colour-mode checks before a release. Behat facts were read in
`public/lib/tests/behat/behat_accessibility.php` and `public/admin/tool/behat/cli/util.php` (5.2 and 5.3.0);
manual-check guidance is from moodledev.io's accessibility testing page.

## The Behat steps

| Step | Checks |
|---|---|
| `the page should meet accessibility standards` | Whole page, default tag set |
| `the page should meet accessibility standards with "best-practice" extra tests` | Default set plus axe best-practice rules (heading order, landmarks, region) |
| `the page should meet "wcag131, wcag412" accessibility standards` | Only the listed axe tags |
| `the "<element>" "<selector>" should meet accessibility standards` (and the two variants) | One region, for UI you added to a page you do not own |

Default tags: `wcag2a`, `wcag21a`, `wcag22a`, `wcag2aa`, `wcag21aa`, `wcag22aa`, `section508`, `cat.aria`,
`cat.sensory-and-visual-cues`, `wcag134` (`get_axe_config_for_tags()`). Colour contrast (`color-contrast`, tagged
`wcag2aa`) is in the set.

Requirements and silent passes:

- `@accessibility` on the scenario or feature, or the step throws "Accessibility tests using Axe must have the
  @accessibility tag on either the scenario or feature."
- `@javascript`: the step calls `require_javascript()`.
- A run initialised with `--no-axe` makes every step return without checking (axe is on by default). A green result
  from such a run proves nothing; check how the site was initialised.
- The step injects `/lib/behat/axe/axe.min.js` from the site under test. If the web server denies paths containing
  `/behat/` (a common hardening rule), the script 404s and every step fails with "No data" while CI, which has no such
  rule, passes. Allow that one path on the Behat vhost rather than skipping the steps.
- The config line `'type' > 'tag'` in `get_axe_config_for_tags()` is a typo for `=>`; axe receives no `type`, treats
  the list as tags, and the filter works as intended (axe-core's `runOnly` normalisation, read in the bundled
  `axe.min.js`).

Scope: run `best-practice` on pages and regions your plugin owns; on a core page you only add to, check your region,
since best-practice failures in core markup are not yours to fix.

## Colour modes in Behat (5.3+)

- `php admin/tool/behat/cli/init.php --colourmode=dark` (also `util.php --enable`) turns colour modes on and sets
  dark for every scenario of that run. A user preference still wins over it.
- Do not pin a mode in accessibility scenarios: run the suite once as installed (light, since colour modes start off)
  and once initialised with `--colourmode=dark`, both in CI.
- A scenario that asserts a specific mode pins it with a user preference:

```gherkin
Given the following "user preferences" exist:
  | user     | preference             | value |
  | student1 | theme_boost_colourmode | dark  |
```

- A scenario about the colour-mode settings themselves skips itself with `Given the run is not using a colour mode`.
- Core's model is `public/theme/boost/tests/behat/colour_mode_accessibility.feature`.

## axe outside Behat

For a quick check while developing, run axe in the browser: the axe DevTools extension, or Lighthouse's
accessibility audit. In browser automation (Playwright, Puppeteer), inject the same `axe.min.js` the site ships and
call `axe.run()` with the default tag set above, once with `data-bs-theme="light"` and once with `"dark"` on the
`html` element. A page checked this way on 5.3.0 in both modes is the strongest automated evidence short of the
Behat steps.

Command-line tools such as `@axe-core/cli` and `pa11y --standard WCAG2AA <url>` work only on pages that need no login,
unless you script a session; for plugin pages the Behat steps are simpler.

## What automated checks miss

axe covers roughly 30 to 50 percent of issues (moodledev.io testing page). It does not enter iframes (H5P, the
TinyMCE content area, embedded media) and does not judge most non-text contrast. Check these by hand:

- **Keyboard.** Tab and Shift+Tab through the page: every control reachable in reading order, Enter and Space
  activate buttons, Enter follows links, custom widgets work with the keys their APG pattern lists, nothing traps
  focus except a modal that Escape closes, and the focus indicator is Boost's, visible and not covered by the sticky
  footer or the fixed navbar.
- **Screen reader.** At least two of: NVDA or JAWS with Firefox or Chrome on Windows, VoiceOver with Safari on macOS
  or iOS, TalkBack with Chrome on Android. Navigate by headings, landmarks and form fields; check every control's
  name and state is announced, and that status messages after AJAX actions are read.
- **Zoom and reflow.** At 1280 CSS pixels wide and 200 percent zoom no content or function is lost (WCAG 1.4.4); at
  320 CSS pixels wide, or 400 percent zoom, nothing scrolls horizontally except tables and media (WCAG 1.4.10).
- **Non-text contrast.** Borders of inputs, focus rings, icons and chart lines at 3:1 against their surface, in both
  colour modes on 5.3.
- **Colour alone.** Errors, statuses and required fields also have text or an icon with a name.
- **Reduced motion.** Animations respect `@media (prefers-reduced-motion: reduce)`.

## Release checklist

1. Every page the plugin adds has an `@accessibility` scenario with `best-practice`; every region it adds to a core
   page has a region scenario.
2. The suite passes on a run without `--no-axe`, and **5.3+:** also on a `--colourmode=dark` run.
3. Keyboard pass and one screen-reader pass done on the main user task.
4. Zoom and reflow checked on a phone-width viewport.
5. No literal colours left in `styles.css` that fail in dark mode (grep `#[0-9a-f]{3,8}`, `bg-white`, `text-dark`).
