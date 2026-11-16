# Verifying a change on a running site

Read this when you are about to verify a change on a running Moodle site: installing it, checking it in a
browser across engines and roles, choosing a success marker, or proving that a CSS change arrived and applies.

## Install, upgrade, purge, permissions

From the Moodle root (the directory that contains `public/` and `admin/cli/` in 5.2 and 5.3.0):

```bash
rsync -a --delete --exclude .git /path/to/repo/ public/local/myplugin/
php admin/cli/upgrade.php --non-interactive
php admin/cli/purge_caches.php
```

- Copy, do not symlink: PHP resolves `__DIR__` to the real path, so a symlinked plugin's
  `require(__DIR__ . '/../../config.php')` looks for `config.php` next to the repository, not in the Moodle
  tree, and the plugin behaves differently from an installed copy.
- `upgrade.php` is needed after any `version.php` bump. Without a bump, a changed `install.xml`, `db/access.php`,
  `db/services.php`, `db/tasks.php` or `db/caches.php` is not re-read.
- The purge rebuilds the class map cached in `$CFG->cachedir/core_component.php`
  (`public/lib/classes/component.php:448`, 5.3.0). A new class file without a purge fails on the site with
  "class not found" while PHPUnit, which builds its own map, is green. The purge also drops compiled theme
  CSS, the language string cache and the template cache.
- The web server user must be able to read every file. Repository files created with mode 0600 give
  "Permission denied" warnings that only appear in the web server log.
- Confirm the installed version is the one you meant: the plugin's row on `admin/plugins.php`, or
  `php admin/cli/cfg.php --component=local_myplugin --name=version`.

## What a browser check proves

A check proves only what its success state uniquely renders.

- Assert a marker that only the destination has: a heading, a form field or a string from the new code, read
  from the source. A check that matches the page header, a loading screen or a generic "Saved" notice passes
  whatever happened.
- A navigation that changes only the `#fragment` of the URL does not reload the page, so a "goto then read" check
  reads the old content. Reload explicitly, or wait for the element the new state renders.
- Name the change the claim predicts and assert it: "saved on leaving" means edit, leave without saving, reopen,
  and read the value; "the setting changes the display" means two screenshots, before and after, that differ
  where predicted. Two identical results prove nothing unless both were expected to change.
- Read the values a settings form shows after saving, not only that the save redirected.
- A test that injects a value into a widget (file picker, editor, date selector) proves the server path only.
  Drive the widget itself once.
- Look at every screenshot you take, as a whole: duplicate headings, wrong navigation, extra or missing items,
  overlapping fixed headers.

## Browsers and roles

- Run every changed page in Firefox and in Chromium. Failures seen only in one engine include APIs that need a
  secure context (`AudioWorkletNode`), media and speech APIs, and promises that never settle in one engine. Race
  browser promises with a timeout in code, so a hang becomes an error.
- Check as each role that sees the UI. A site admin passes every capability check (`has_capability()` with the
  default `$doanything = true`, `public/lib/accesslib.php`, 5.3.0), so admin-only testing cannot find a missing
  capability or a page that over-grants. Check as admin too: admins see extra controls and settings links that
  can break the layout.
- Check with existing data: an activity with its own per-item overrides, a course that already has content, a
  second attempt, two users at once, two tabs, phone width.
- A plugin that alters core forms or pages is also checked on a Moodle with only standard plugins installed.
  Another plugin on a development site can load a library, a string or a JavaScript module that yours relies on
  without declaring it.
- Do not check filtered output while "logged in as" another user. During that session `require_login()` sets
  `$CFG->forceclean` (`public/lib/moodlelib.php:2427-2432`, 5.3.0), so `format_text()` ignores `noclean` and
  strips attributes before filters run, and the page differs from what that user really sees.

## CSS: arrival, then effect

Plugin `styles.css` files are concatenated into the theme's stylesheet first, then the parent themes' sheets,
then the theme's own CSS, which for a Boost-based theme is the compiled SCSS including Bootstrap
(`theme_config::get_css_files()` and `get_css_content()`, `public/lib/classes/output/theme_config.php`,
5.3.0). So at equal specificity the theme and Bootstrap win over a plugin rule. The result is cached until a
purge or a theme revision change. Two levels of evidence:

1. **Arrival**: the rule is in the stylesheet the page actually loads.

   ```bash
   wwwroot=https://moodle.example.com
   css=$(curl -s "$wwwroot/" | grep -o "$wwwroot/theme/styles.php[^\"]*" | head -1)
   curl -s "$css" | grep -F '.local-myplugin-banner'
   ```

   On a page that needs login, fetch the URL with the browser's session instead. Some pages load several
   sheets; check each `styles.php` link.
2. **Effect**: the browser applies it. In the browser console or a test:

   ```js
   getComputedStyle(document.querySelector('.local-myplugin-banner')).backgroundColor
   ```

   or a screenshot of the element. A rule that arrived can still lose to the theme's rules or to Bootstrap at
   equal or higher specificity. To restyle a Bootstrap component, set its own custom properties from a selector
   that outranks it (`.btn.local-myplugin-share { --bs-btn-bg: var(--bs-primary); }`) rather than raising weight.

- The first page load after a purge has been seen to serve the previous stylesheet; reload once before judging.
  The cause was not confirmed from the source.
- A custom property that does not exist on the active theme resolves to its fallback or to nothing:
  `getComputedStyle(document.documentElement).getPropertyValue('--bs-body-bg')` returning `''` means it is
  undefined there.
- Theme stylesheets, SCSS compile checks, dark mode and RTL are covered in `moodle-theme-testing-release`.

## Logs and debugging

- Turn on developer debugging (`php admin/cli/cfg.php --name=debug --set=32767` and `--name=debugdisplay
  --set=1`) for the check, and read the web server's PHP error log for the pages you touched. A notice shown only
  in the log is still a finding: reviewers test with developer debugging on.
- Restore any site setting you changed for the check, and read it back.
