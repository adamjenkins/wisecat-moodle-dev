# Testing and releasing a theme on Moodle 5.3

Read this when the theme supports Moodle 5.3 (`MOODLE_503_STABLE`, `$plugin->supported` including 503): colour-mode
runs, Boost's 5.3 test models, React override builds, and what changed in the test tooling against 5.2.

Evidence: read in the 5.3.0 source (`public/admin/tool/behat/cli/*.php`, `public/lib/behat/lib.php`,
`public/lib/behat/classes/util.php`, `public/lib/tests/behat/behat_general.php`,
`public/theme/boost/classes/colour_mode.php`, `public/theme/boost/classes/hook_listener.php`,
`public/theme/boost/tests/`, `.grunt/tasks/esm.js`) unless marked run. A Boost child theme's Behat suite, compile
test and an axe run in light and dark were run on 5.3.0.

## Colour modes in Behat

- `init.php`, `util.php --enable` and `util_single_run.php --enable` take `--colourmode=light|dark`. The value is
  stored as a run option; `behat_get_colour_mode()` (`public/lib/behat/lib.php`) returns it and Boost treats it as
  the site default for the whole run. A `theme_boost_colourmode` user preference set in a scenario still wins.
- The run header prints `Colour mode: dark` (or `Theme default`) under "Run optional tests". Read it: a dark CI job
  whose header says `Theme default` ran in light.
- `Given the run is not using a colour mode` skips a scenario when the run was started with `--colourmode`. Use it on
  scenarios that assert the mode switcher or the site default, as Boost's `colour_mode.feature` does.
- On the page, Boost writes two attributes on `<html>` from the first byte: `data-bs-theme` (`light` or `dark`, what
  Bootstrap's CSS reads) and `data-colourmode` (the chosen mode, which can be `auto`). For `auto`, `data-bs-theme`
  starts as `light` and a small inline script resolves it from `prefers-color-scheme`
  (`public/theme/boost/classes/hook_listener.php`). Assert `data-bs-theme` for what is shown, `data-colourmode` for
  what was chosen.
- The colour mode switch is in the user menu, `#colourmode-action-menu`, with buttons named Light, Dark and Auto;
  Boost's `colour_mode.feature` clicks them.

## Which themes get colour modes

`theme_boost\colour_mode::is_boost_theme()` is true when the page's theme is Boost or has `boost` in
`$THEME->parents`. A child of Boost passes. A grandchild (a child of a theme `middle` that is itself a child of
Boost) passes only if its `$THEME->parents` lists every ancestor, `['middle', 'boost']`; with `['middle']` alone it
gets no colour modes and no switcher. A dark-mode scenario that asserts `data-bs-theme="dark"` catches this at once.

## Boost's 5.3 test files as models

| File | Use it for |
|---|---|
| `public/theme/boost/tests/behat/colour_mode_accessibility.feature` | Light and dark accessibility pairs; the comment explaining why the course page runs without `best-practice` |
| `public/theme/boost/tests/behat/colour_mode.feature` | Switching modes in the user menu; `the run is not using a colour mode` |
| `public/theme/boost/tests/behat/drawer_dismiss.feature`, `editmode_switch.feature` | Drawer and edit-mode steps on the 5.3 header |
| `public/theme/boost/tests/colour_mode_test.php` | PHPUnit of the mode resolution and preference |
| `public/theme/boost/tests/fonts_test.php` | PHPUnit of the bundled fonts |

## axe on 5.3

- 5.3.0 bundles axe-core 4.13.0 (`public/lib/behat/axe/axe.min.js`), against 4.10.3 on 5.2. Newer axe versions add
  and tighten rules, so a page can pass on 5.2 and fail on 5.3 with no theme change.
- Core's own course page fails `best-practice` (`landmark-unique`) in both modes on 5.3.0, because the primary
  navigation's more menu has no accessible name of its own. Run `best-practice` on regions the theme owns, and the
  default rules on whole core pages.

## A dark-mode CI run

A second initialisation and Behat run on the 5.3 rows only, from the Moodle checkout's root (read in moodle-plugin-ci
4.5.11 and the 5.3.0 CLI scripts, not run on GitHub):

```yaml
      - name: Behat features in dark mode
        if: ${{ !cancelled() && matrix.moodle-branch != 'MOODLE_502_STABLE' }}
        working-directory: moodle
        run: |
          php public/admin/tool/behat/cli/util_single_run.php --enable --add-core-features-to-theme \
            --scss-deprecations --colourmode=dark
          moodle-plugin-ci behat --moodle=. --profile chrome --suite mytheme
```

`moodle-plugin-ci behat --scss-deprecations` re-initialises the site and resets the colour mode, so the dark run
does its own initialisation and calls `behat` without that flag.

## Features that use 5.3-only steps

`the run is not using a colour mode` does not exist on 5.2. Whether Behat on 5.2 still reports such a step as
undefined after an earlier `the site is running Moodle version 5.3 or higher` step skipped the scenario was not
established. The safe layout: put 5.3-only scenarios in their own feature with an extra tag, and leave that tag out
on 5.2 rows:

```gherkin
@theme @theme_mytheme @theme_mytheme_colourmodes
Feature: The theme's colour modes
```

```yaml
      - name: Behat features
        run: |
          if [ "${{ matrix.moodle-branch }}" = "MOODLE_502_STABLE" ]; then
            moodle-plugin-ci behat --profile chrome --suite mytheme --scss-deprecations \
              --tags '@theme_mytheme&&~@theme_mytheme_colourmodes'
          else
            moodle-plugin-ci behat --profile chrome --suite mytheme --scss-deprecations
          fi
```

The `--tags` option of `moodle-plugin-ci behat` replaces its default `@theme_mytheme` filter (read in 4.5.11, not
run).

## React overrides and ESM builds

- A theme can override React components (`js/esm/src/`, compiled to `js/esm/build/`). This exists on 5.3 only.
- The ZIP must contain `js/esm/build`; Moodle does not compile it at runtime.
- moodle-plugin-ci's default grunt tasks (`amd`, `yui`, `gherkinlint`, `stylelint`) do not build or check it, so a
  stale or missing build passes CI. Ask for the task explicitly; `-t` replaces the defaults, so list them all (derived
  from the code, not run):

```yaml
        run: moodle-plugin-ci grunt --max-lint-warnings 0 -t amd -t yui -t gherkinlint -t stylelint -t esm
```

- Prove an override is used in Behat (a class or `data-region` it adds), on a 5.3 row; a PHPUnit render cannot see
  React-rendered parts.

## Classic is gone

Classic is removed from 5.3. A theme whose `version.php` depends on `theme_classic` cannot be installed; one that
only lists `classic` in `$THEME->parents` loses that parent silently, because `theme_config` skips a parent it cannot
load (`public/lib/classes/output/theme_config.php`, 5.3.0), and its SCSS, layouts and renderers with it. A
`blacklist.json` entry naming a Classic feature path stops initialisation with "Blacklisted feature ... not found",
and a context file that `require_once`s a `behat_theme_classic_*` file fails to load. Classic's step overrides on
5.2 remain a useful reading model for a child whose navigation differs from Boost's, but nothing can depend on
them on 5.3.

## stylelint on 5.3

Run on 5.3.0, core's stylelint rule `csstree/validator` rejected `container-type`, `@container` and `clamp()` in
`font-size`. Add `// stylelint-disable-line csstree/validator` to each such line; core uses the same comment in
`public/theme/boost/scss/moodle/modchooser.scss` (5.3.0). The rule is configured identically on 5.2 (`.stylelintrc`
and the plugin version in `package.json` are the same), so expect the same findings there; that was not run. The
rules themselves are in `moodle-theme-scss`.
