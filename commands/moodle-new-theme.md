---
name: moodle-new-theme
description: Scaffold a Boost child theme for Moodle 5.2 and 5.3 (asks for the name and what it must change).
argument-hint: "[name] [what it must change] — e.g. campus \"brand colour, rounded cards, a footer note\""
---

You will scaffold a Moodle theme that is a child of Boost.

User's input: $ARGUMENTS

If `$ARGUMENTS` is empty or missing a value, ask the user once:

1. **Theme name** — lowercase letters and digits, starting with a letter, no underscore. The component becomes
   `theme_<name>` and the directory `<name>`.
2. **What it must change** — for example: brand colour, typeface, corner radius, a banner or footer note, the
   login page, a changed page frame, settings an admin can edit. This decides which optional files are written.
3. **Supported Moodle versions** — default 5.2 and 5.3.
4. **Copyright holder** for the file headers.
5. **Moodle root**, if it cannot be found from the current directory (the directory that holds `public/` and
   `admin/cli/`).

If the user wants a theme with no parent, or a child of a theme other than Boost, read the `moodle-theme-development`
skill first: it says when each choice fits, and that a stand-alone theme is not a tested recipe.

Then:

1. Activate the `moodle-theme-boost-child` skill. Its default recipe is the content of every base file; take the
   files from it rather than from memory. Activate `moodle-theme-development` for the engine rules behind it.
2. Create `public/theme/<name>/` under the Moodle root. If the directory exists, stop and ask.
3. Write the base files, as in that recipe:
   - `version.php` — `$plugin->requires = 2026042000;` and `$plugin->supported = [502, 503];` for 5.2 and 5.3
     (`2026100500` and `[503, 503]` for 5.3 only), and `$plugin->dependencies` on `theme_boost` with Boost's build
     for the lowest supported version
   - `config.php` — `$THEME->parents = ['boost'];`, the SCSS closure and callbacks, and the Boost keys a child
     does not inherit
   - `lib.php` — the main SCSS function and the pre and extra SCSS callbacks, emitting only this theme's part
   - `lang/en/theme_<name>.php` — `pluginname`, `choosereadme`, `configtitle`, `privacy:metadata`, in
     alphabetical order
   - `classes/privacy/provider.php` — a null provider
   - `scss/<name>/pre.scss` and `scss/<name>/post.scss`
   - `pix/favicon.ico` (copy Boost's: it is not inherited) and `pix/icon.svg`
   - `LICENSE` — the full GPL v3 text, copied from `COPYING.txt` in the Moodle root
   - `README.md` and a changelog
4. Add only what the stated changes need, each from the skill that owns it:

   | The theme must change | Write | Skill |
   |---|---|---|
   | Colours, type, radius, spacing, component styles | Variables in `pre.scss`, rules in `post.scss` | `moodle-theme-scss` |
   | Something an admin can set | `settings.php`, the setting read and validated in `lib.php` | `moodle-theme-settings` |
   | Boost's brand colour, raw SCSS or background settings kept under the child | The mirrored settings and the `pluginfile` function | `moodle-theme-boost-child` (Boost settings reference) |
   | Extra HTML in the head, at the top of the body or before the footer | A hook callback with an active-theme guard | `moodle-theme-renderers-output` |
   | Navbar, footer or other template markup | A template override under `templates/<component>/` | `moodle-theme-layouts-templates` |
   | The page frame on some page types | An own layout file and template, each with its untouched twin | `moodle-theme-layouts-templates` |
   | What a renderer method returns, icons | `classes/output/core_renderer.php` extending Boost's class | `moodle-theme-renderers-output` |

   Prefer the smallest mechanism that does the job: SCSS before a template override, an override before a copied
   layout. A theme that copies Boost's layout template or navbar has a different upstream on 5.2 and 5.3; say so
   before writing one, and offer one branch per Moodle version instead.
5. Write `tests/lib_test.php`, the compile test from the `moodle-theme-testing-release` skill, asserting a
   selector that only this theme emits. If the theme has a feature worth a browser check, add a Behat feature
   tagged `@theme @theme_<name>` as that skill describes.
6. Rules that hold for every file written:
   - No `@import` into Bootstrap, Font Awesome or the design system; those paths differ between 5.2 and 5.3.
   - Surfaces and text colours from `--bs-*` custom properties; dark exceptions under `[data-bs-theme="dark"]`,
     never `prefers-color-scheme`.
   - The theme's own settings are read with `get_config('theme_<name>', ...)`.
   - GPL header and file docblock on every PHP file; the boilerplate comment on `.scss` and `.mustache` files too.
7. Print a tree of what was created, then the next steps, to run from the Moodle root:
   ```bash
   php admin/cli/upgrade.php --non-interactive
   php admin/cli/build_theme_css.php --themes=<name> --direction=ltr
   php admin/cli/purge_caches.php
   phpcs --standard=moodle public/theme/<name>
   php public/admin/tool/phpunit/cli/init.php
   vendor/bin/phpunit --testsuite theme_<name>_testsuite
   ```
   (`phpcs` with the `moodle` standard comes from `moodlehq/moodle-cs`; core's own Composer file does not
   install it. `moodle-plugin-ci phpcs --max-warnings 0` is the same check as CI runs.)
   and how to look at it: select the theme in the theme selector, or enable `allowthemechangeonurl` and open a
   page with `?theme=<name>`.
8. List what is left for the user: `pix/screenshot.png` (about 500 by 400 px; until it exists the selector shows
   Boost's), real colours and text, and anything marked TODO.

Offer `/moodle-theme-check` as a static check of the result.

Say plainly that the theme was written and not run. A theme whose SCSS does not compile still shows a working
page that looks like plain Boost, so the compile test or the `build_theme_css.php` command above (with developer
debugging on) is what shows whether it works.
