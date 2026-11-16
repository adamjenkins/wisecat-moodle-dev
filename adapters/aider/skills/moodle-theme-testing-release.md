# moodle-theme-testing-release

> Use when testing, linting, packaging or submitting a Moodle theme - a PHPUnit test that compiles the theme, the theme's own Behat suite (--suite=<theme>, @theme_<name> tags, behat_theme_<name>_behat_*.php overrides, blacklist.json), computed-style and axe checks, dark mode (--colourmode, 5.3) and RTL checks, --scss-deprecations, stylelint and Mustache lint of overridden core templates, moodle-plugin-ci for themes, and Plugins directory rules for themes (LICENSE file, ZIP root folder, screenshot, choosereadme, thirdpartylibs.xml for fonts); also for "0 scenarios" from a theme feature, a core feature that fails only under the theme, or CI that stays green while the theme's SCSS does not compile. Skip when writing the theme itself (start at moodle-theme-development), for Behat, PHPUnit, CI and release mechanics that are not theme-specific (moodle-behat-testing, moodle-phpunit-testing, moodle-ci-matrix, moodle-plugin-release), or for the axe steps (moodle-accessibility).

# Moodle Theme Testing and Release

## Overview

How to prove that a theme works on Moodle 5.2 and 5.3 and how to ship it: which tests catch which failure, how
Behat runs a theme, what the CI gates check and miss, and what the Plugins directory asks of a theme. "Run on 5.3.0"
means it was observed with a Boost child theme on Moodle 5.3.0; "read in the source" means read, not run. Nothing
here was run on 5.2: 5.2 statements are read in the 5.2 source.

## When to Use

- Adding the first tests to a theme, or a theme change needs a test that would fail without it
- A theme feature reports zero scenarios, or a core feature fails only under the theme
- Proving a colour, spacing, dark-mode or RTL change, or running accessibility checks on theme pages
- Writing or fixing a theme's GitHub Actions workflow, or reading a failed lint step
- Building the release ZIP, submitting a theme to the Plugins directory, or answering a reviewer
- **Skip when:** the task is building the theme (`moodle-theme-development` routes to the right sibling); Behat or
  PHPUnit in general (`moodle-behat-testing`, `moodle-phpunit-testing`); the CI version matrix
  (`moodle-ci-matrix`); version numbers, tags and the release workflow (`moodle-plugin-release`); the security
  checklist before a release (`moodle-release-preflight`); WCAG rules for markup (`moodle-accessibility`)

## Mental model: four layers, each caught by one kind of test

| Layer | What breaks | What catches it | What does not |
|---|---|---|---|
| Compile | An import, variable or mixin missing on one version; a bad setting value in SCSS | A PHPUnit test asserting one of the theme's own selectors in `get_css_content()` | Lint, Behat without assertions on style, CI's grunt step (it never compiles a third-party theme) |
| Page | A layout, template or renderer override not used; a missing string | Behat in the theme's own suite; a PHPUnit test that renders the template | PHPUnit renderer tests from the CLI renderer |
| Effect | A rule reached the stylesheet but loses the cascade; dark mode or RTL wrong | Computed-style steps in a JavaScript scenario; axe | Grepping the served CSS (that proves arrival only) |
| Package | No licence file, wrong ZIP root, undeclared fonts, missing `choosereadme` | Listing the built ZIP; a checklist | Every CI step: CI installs from the git checkout, never from the ZIP |

A compile failure is silent: `theme_config::get_css_content()` falls back to the parents' precompiled CSS, so the
site looks like stock Boost and nothing errors on screen (run on 5.3.0; `public/lib/classes/output/theme_config.php`
`get_css_content()`, 5.2 and 5.3). The only cheap guard is the compile test below. Seeing the compiler message is
covered in `moodle-theme-scss`.

## Default recipe

Files, beside the theme's code:

```
tests/
  lib_test.php                   compile test and setting-to-SCSS tests (PHPUnit)
  behat/
    mytheme.feature              @theme @theme_mytheme, runs in the "mytheme" suite
    behat_theme_mytheme.php      the theme's own steps, only if it needs any
LICENSE                          full GPL v3 text, in the root, shipped in the ZIP
```

### 1. The compile test (PHPUnit)

This pattern was run on 5.3.0. PHPUnit is 11.5 on both versions, so the attributes work on 5.2 too.

```php
<?php
// (GPL header)

namespace theme_mytheme;

/**
 * Tests of the theme's SCSS.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
#[\PHPUnit\Framework\Attributes\CoversFunction('theme_mytheme_get_pre_scss')]
final class lib_test extends \advanced_testcase {
    public function test_the_theme_compiles(): void {
        $this->resetAfterTest();
        set_config('accent', '#123456', 'theme_mytheme');
        $theme = \theme_config::load('mytheme');
        $theme->force_svg_use(true);
        $theme->set_rtl_mode(false);

        $css = $theme->get_css_content();

        // The fallback CSS is Boost's and contains none of these, so this fails on any compile error.
        $this->assertStringContainsString('.mytheme-banner', $css);
        $this->assertMatchesRegularExpression('/\.mytheme-banner\{[^}]*#123456/', $css);
    }

    public function test_a_value_that_is_not_a_colour_is_left_out(): void {
        $this->resetAfterTest();
        set_config('accent', 'red; } body { display: none', 'theme_mytheme');
        $theme = \theme_config::load('mytheme');
        $this->assertStringNotContainsString('mytheme-accent', theme_mytheme_get_pre_scss($theme));
    }
}
```

- `theme_config::load()` includes the theme's and its parents' `lib.php`, so functions from `lib.php` can be called
  after it (`theme_config.php` constructor, 5.2 and 5.3).
- A compile error also calls `debugging('Error while compiling SCSS: ...')`, which fails an `advanced_testcase` with
  "Unexpected debugging() call detected" and prints the message. The selector assertion still catches the fallback
  when debugging is quiet.
- Match the compiled form: on 5.3.0 the output had no space before `{`, as the regular expression above expects.
- Run it: `vendor/bin/phpunit --testsuite theme_mytheme_testsuite` from the Moodle root, after
  `php public/admin/tool/phpunit/cli/init.php` (the suite name is generated into `phpunit.xml`).
- More tests (rendering a template, a renderer, the privacy compliance test): [reference/phpunit-for-themes.md](../moodle-skill-files/moodle-theme-testing-release/reference/phpunit-for-themes.md).

### 2. The theme's Behat feature

Run on 5.3.0: after `init.php` the generated `behat.yml` has a suite named after the theme, and these scenarios pass
with `--suite=mytheme`.

```gherkin
@theme @theme_mytheme
Feature: The theme's banner and body class
  In order to brand the site
  As an administrator
  I need the banner and the corner style to reach course pages

  Background:
    Given the following "courses" exist:
      | fullname | shortname |
      | Course 1 | C1        |
    And the following "users" exist:
      | username | firstname | lastname |
      | student1 | Student   | One      |
    And the following "course enrolments" exist:
      | user     | course | role    |
      | student1 | C1     | student |

  Scenario: The banner text set by the administrator is shown on course pages
    Given the following config values are set as admin:
      | bannertext | Welcome | theme_mytheme |
    When I am on the "Course 1" course page logged in as student1
    Then I should see "Welcome" in the "[data-region='mytheme-banner']" "css_element"

  Scenario: The corner style setting reaches the body class
    Given the following config values are set as admin:
      | cornerstyle | square | theme_mytheme |
    When I am on the "Course 1" course page logged in as student1
    Then "body.mytheme-corners-square" "css_element" should exist
```

Run it locally from the Moodle root, the directory that holds `public/` (read in the source for both versions):

```bash
php public/admin/tool/behat/cli/init.php --scss-deprecations
php public/admin/tool/behat/cli/run.php --suite=mytheme --tags=@theme_mytheme
```

### 3. CI

Start from the upstream `moodle-plugin-ci` template (`moodle-ci-matrix` owns the matrix). Theme specifics, read in
moodle-plugin-ci 4.5.11: `behat` picks the suite named after the theme by itself (older versions ran `default`,
where a theme's features do not exist, and passed with zero scenarios; pass `--suite mytheme` if unsure); keep
`--scss-deprecations`; `grunt` lints the whole `scss/` tree with core's stylelint; `mustache` lints every
overridden core template. A complete workflow, a dark-mode Behat run and the lint traps are in
[reference/ci-for-themes.md](../moodle-skill-files/moodle-theme-testing-release/reference/ci-for-themes.md).

### 4. Release

Follow `moodle-plugin-release`: it owns the version and tag steps, building the ZIP with
`git archive --prefix=mytheme/`, listing it, the root-folder rule and the licence file. What a theme adds to that
(screenshot, plugin icon, `choosereadme`, fonts, copied core files) is in
[reference/plugins-directory.md](../moodle-skill-files/moodle-theme-testing-release/reference/plugins-directory.md).

## Behat runs a theme through its suite

Read in `public/lib/behat/classes/behat_config_util.php` `get_behat_suites()`, identical in 5.2 and 5.3.0.

- Every installed theme that the selector can show gets a suite named after it. Boost, the default theme, is the
  suite `default`. A theme with `$THEME->hidefromselector = true` gets no suite, so its features never run.
- A theme's suite holds only that theme's features, unless Behat was initialised with `-a` /
  `--add-core-features-to-theme` (all themes, or a comma list). Theme features are removed from `default`.
- Before each scenario in a non-default suite, Behat sets the site theme to the suite name
  (`public/lib/tests/behat/behat_hooks.php`). Never set the theme in a feature.
- `moodle-plugin-ci validate` fails a feature without both `@theme` and `@theme_mytheme` tags.
- Step definitions: every `tests/behat/behat_*.php` of the theme is a context of its suite only; the class name
  must equal the file name. A theme first inherits its nearest parent's contexts, so a Boost child already runs with
  `behat_theme_boost_behat_navigation`. A class that extends a core context replaces it in the suite.
- `tests/behat/blacklist.json` removes `features`, `contexts` or `tags` from the theme's suite. An existing file that
  is empty or not valid JSON stops Behat initialisation with "blacklist.json is empty".

Theme CSS on a Behat site is built once, at `--enable` or `init.php`, left-to-right only, with default settings, and
put back into the cache before each JavaScript scenario (`public/lib/behat/classes/util.php` `build_themes()`,
`restore_saved_themes()`, 5.2 and 5.3). Two consequences, read in the source, not run:

- After editing SCSS, initialise again (`init.php` or `util_single_run.php --enable`) or the run tests the old CSS.
- `the following config values are set as admin` is a plain `set_config()` and does not reset theme caches
  (`public/admin/tests/behat/behat_admin.php`). A setting that feeds the SCSS needs the scenario to save it on the
  settings page (the setting's `theme_reset_all_caches` callback runs) or a theme step that calls
  `theme_reset_all_caches()`. Settings read by templates or renderers, as in the feature above, work either way.

`--scss-deprecations` makes Behat fail any step after which an element shows Boost's "Deprecated style in use"
marker, such as Bootstrap 4 classes (`ml-2`, `float-right`, `badge-primary`, `sr-only`, `font-weight-bold`), also
when the class was added by JavaScript or sits in a core page the step only visits
(`public/lib/behat/classes/behat_session_trait.php` `look_for_deprecated_styles()`, 5.2 and 5.3). Three things
decide whether it runs:

- It is a run option set at `init.php` or `util_single_run.php --enable`. `run.php` has no such option and Behat
  rejects it as unknown. The header Behat prints must say `SCSS deprecations: Yes`.
- It checks only JavaScript scenarios. A feature with no `@javascript` scenario never exercises it; give the theme at
  least one.
- Deprecated icons (`.icon.deprecated`) fail the same way unless the run was set up with `--no-icon-deprecations`.

Full suite mechanics, override recipes, selectors and the element ids core steps depend on:
[reference/behat-theme-suite.md](../moodle-skill-files/moodle-theme-testing-release/reference/behat-theme-suite.md).

## Proving the effect, not the arrival

- A rule can be in the served stylesheet and still lose to Bootstrap or a later rule. Assert the computed value in a
  JavaScript scenario with a theme step (recipe in [reference/visual-checks.md](../moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md)), or
  assert a visible consequence, as large themes do: a raw SCSS rule that hides `#page-header h1`, then
  `I should not see "Course 1" in the "#page-header .page-header-headings" "css_element"`.
- `var(--name, fallback)` with an undefined property silently uses the fallback; only a computed-value check on the
  page shows it. Check the names your SCSS reads in the browser: `getComputedStyle(document.body).getPropertyValue('--bs-primary')`.
- Name the change the claim predicts and assert that change, in the role and the state users will meet it: a
  setting checked only on a course that does not use it, or only as admin, proves nothing.
- Phones: `I change viewport size to "mobile"`; check `document.documentElement.scrollWidth` is not larger than
  the viewport (a `.row` outside a container overflows by its negative gutters), and test "visible" with
  `document.elementFromPoint()` at the element's centre, because Boost's fixed navbar (about 60 px) covers content
  that is inside the viewport.
- Dark mode (**5.3+:** `data-bs-theme="dark"` on `<html>`) and RTL (`body.dir-rtl`) recipes:
  [reference/visual-checks.md](../moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md).

## Accessibility checks (axe)

Read in `public/lib/tests/behat/behat_accessibility.php` (5.2 bundles axe-core 4.10.3, 5.3.0 bundles 4.13.0; the
code is otherwise identical).

```gherkin
  @javascript @accessibility
  Scenario: A course page with the banner meets accessibility standards
    Given the following config values are set as admin:
      | bannertext | Welcome | theme_mytheme |
    When I am on the "Course 1" course page logged in as student1
    Then the page should meet accessibility standards
    And the "region-main" "region" should meet accessibility standards with "best-practice" extra tests
```

- The step throws unless the scenario or feature is tagged `@accessibility`, and needs `@javascript`.
- It passes without checking anything when Behat was initialised with `--no-axe` (axe is on by default).
- "No data" means the axe script never loaded: the step injects `/lib/behat/axe/axe.min.js` from the site, and a web
  server that denies `/lib/behat/` paths makes every accessibility step fail locally while CI passes.
- Default rules: WCAG 2.0, 2.1 and 2.2 A and AA, Section 508, `cat.aria`, `cat.sensory-and-visual-cues`, `wcag134`.
  Naming `wcag2aa` as an extra adds nothing; `best-practice` adds the landmark and heading rules.
- **5.3+:** core's own course page fails `best-practice` (`landmark-unique`) in both colour modes, as Boost's
  `colour_mode_accessibility.feature` notes; run `best-practice` on regions the theme owns, plain rules on the page.
- axe does not look inside iframes (H5P, embedded editors) and does not judge most non-text contrast: borders, focus
  rings and icons need a look by eye. Light and dark pairs, and what else to check by hand:
  [reference/visual-checks.md](../moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md).

## Lint gates and what they miss

- **stylelint** lints `scss/*.scss` and `scss/**/*.scss` of a theme with core's rules; `style/*.css` is linted only
  when there is no `scss/`, and a root `styles.css` in a theme never. The rules and how to silence a line are in
  `moodle-theme-scss`. SCSS returned as a string from a PHP callback is never linted.
- **Mustache lint** (`moodle-plugin-ci mustache`) checks every `*.mustache`, including overridden core templates
  under `templates/core/`, and fails on any warning: no `@template` docblock, no `Example context (json):`, HTML
  validator messages. A `*.mustache.upstream` twin is not linted. A `.mustachelintignore` beside the template skips
  the HTML validator only. Run on 5.3.0 and on a 5.2 tree: an override that wraps the original with
  `{{> core/name! }}` passes. Two gaps, read in the linter bundled with moodle-plugin-ci 4.5.11, not run: a partial
  it cannot find renders as nothing and is not reported, and `{{#js}}` blocks are not linted on 5.2 and 5.3, because
  it looks for ESLint under `public/node_modules`, which does not exist (the log says "ESLint did not run").
- An example context must not contain `}}`: it closes the comment and prints the rest of the docblock on the page,
  while lint and PHPUnit stay green. Write `} }` inside JSON.
- **phpcs** applies to a copied core file as to your own: Boost's `layout/drawers.php` copied unchanged fails the
  code checker on a missing trailing comma (run on 5.3.0). Fix the copy; keep the untouched original as
  `drawers.php.upstream`, which no checker reads.
- **gherkinlint** (inside `grunt`) checks feature indentation (`Background`/`Scenario` 2, steps 4, `Examples` 4,
  rows 6), trailing spaces, a newline at the end, and that feature names are unique (`.gherkin-lintrc`, identical
  in 5.2 and 5.3).

What no gate catches, so a test or a checklist must: a compile failure; a missing `{{#str}}` or `get_string()` key
(it prints `[[key]]` or throws on the live page; render each new template in PHPUnit and assert no `[[`); a template
override that is not used; a theme with no privacy provider (core's compliance test is not part of plugin CI); the
ZIP's root folder and licence file; a stale `js/esm/build` (**5.3+**, see the version notes).

## Plugins directory rules that apply to themes

The Marketplace plugin submission guidelines (linked from https://moodledev.io/general/community/plugincontribution)
replace the legacy checklist. What a theme must have, with what checks it:

| Rule | Checked by | How to satisfy it |
|---|---|---|
| A licence file in the package | nothing in CI; the most common review blocker | `LICENSE` in the root, in the ZIP; the rule and its checks are in `moodle-plugin-release` |
| Installs from the ZIP | nothing in CI | Root folder = the theme name (`mytheme/`), not `moodle-theme_mytheme-1.0.0/` (`rootdirinvalid`); building and listing the ZIP is in `moodle-plugin-release` |
| GPL v3 when the plugin reproduces or adapts a substantial part of Moodle | review | A Boost child that copies Boost layouts or templates is in that case: GPL v3 or later |
| Third-party files declared | nothing (the file only hides paths from CI) | Each bundled font, icon set or vendored library in `thirdpartylibs.xml`, its licence text beside it |
| Boilerplate and `@copyright` in every file | phpcs, PHP files only | Add them by hand to `.mustache`, `.scss`, `.js`; a file copied from core or another theme keeps the original `@copyright` line above yours |
| Strings core asks for | `validate` checks `pluginname` only | Also `choosereadme` (the theme selector's preview reads it), `privacy:metadata` or the preference strings, `region-<name>` for a block region no parent names |
| Settings stored as `theme_mytheme/<name>` | nothing | Use the slash form in `settings.php` |
| CSS scoped so it does not affect other pages | nothing | For a theme: scope the theme's own components with its own class prefix; do not ship rules for one third-party plugin |
| Screenshots on the listing page | nothing | Separate from `pix/screenshot.png`; show the theme on real pages, light and dark if supported |
| Privacy API when personal data is stored | nothing in plugin CI | Run core's compliance test for the theme ([reference/phpunit-for-themes.md](../moodle-skill-files/moodle-theme-testing-release/reference/phpunit-for-themes.md)) |

The full release checklist, the ZIP checks, `pix/screenshot` and plugin icon facts, and how reviewers raise and
close findings: [reference/plugins-directory.md](../moodle-skill-files/moodle-theme-testing-release/reference/plugins-directory.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| No test asserts the theme's own CSS | A compile error ships; the site looks like plain Boost and every gate is green | The compile test above |
| Asserting `assertNotEmpty($css)` | Passes on the fallback CSS | Assert a selector only the theme emits |
| Theme feature run with `--suite=default` or an old moodle-plugin-ci | Zero scenarios, green job | `--suite=mytheme`; moodle-plugin-ci 4.5.11 or later |
| Only `@theme_mytheme` on the feature | `moodle-plugin-ci validate` fails | `@theme @theme_mytheme` |
| Setting the theme inside a feature (`theme` in a config values table, or `set_config('theme', ...)` in a step) | Fights the suite; the feature tests a different theme in other suites | Let the suite set the theme |
| `$THEME->hidefromselector = true` | The theme has no Behat suite at all | Leave it false in a theme that has features |
| `I change the viewport size to "mobile"` | Undefined step: core's step has no "the" | `I change viewport size to "mobile"` |
| SCSS-fed setting set with `the following config values are set as admin` | The page keeps the CSS built at init; the assertion fails or passes for the wrong reason | Save it on the settings page in the scenario, or a step calling `theme_reset_all_caches()` |
| SCSS edited, Behat not re-initialised | Scenarios test the old CSS | `init.php` (or `util_single_run.php --enable`) again |
| `run.php --scss-deprecations` | `run.php` hands the option to Behat, which stops with "option does not exist" | Pass it to `init.php`; read the "SCSS deprecations: Yes" line |
| No `@javascript` scenario | The SCSS deprecation and axe checks never run | At least one JavaScript scenario that loads a themed page |
| Accessibility step without `@accessibility` | DriverException | Tag the scenario or feature |
| "No data" from axe treated as a theme bug | Time lost on a server rule | Allow `/lib/behat/` on the test web server |
| Bootstrap 4 class in a template or in JS-built markup | Fails CI Behat with `--scss-deprecations`, passes a local run without it | Bootstrap 5 names (`ms-2`, `float-end`, `visually-hidden`, `fw-bold`) |
| `hidden` attribute on an element with a `d-flex` class | Still shown: Bootstrap's `d-*` uses `!important` | Toggle `d-none`; assert with `I should not see` for each mode |
| Grepping the served CSS as proof | The rule arrived but loses the cascade | A computed-style assertion |
| Copied core template without its docblock or example context | Mustache lint fails the theme's CI | Keep `@template` and `Example context (json):` |
| `}}` inside an example context | The rest of the docblock prints on the page | `} }` |
| Release ZIP with the wrong root folder or without `LICENSE` | A reviewer blocks it; core's validator can reject the root with `rootdirinvalid` | Build and list the ZIP as `moodle-plugin-release` says |
| No `choosereadme` string | The theme selector preview asks for a missing string | Add it to `lang/en/theme_mytheme.php` |
| No `pix/screenshot.*` | The selector silently shows the parent's screenshot | Ship one |
| No `pix/icon.svg` | A blank spacer instead of an icon on the plugins overview page (`public/admin/renderer.php`) | Ship a line icon with a stroke that also reads in dark mode |
| A 5.3-only step (`the run is not using a colour mode`) in a feature that runs on 5.2 | The 5.2 row cannot run that step | A separate feature with its own tag, excluded on 5.2 rows (version notes) |

## Reference files

| File | Read it when |
|---|---|
| [reference/behat-theme-suite.md](../moodle-skill-files/moodle-theme-testing-release/reference/behat-theme-suite.md) | Writing the theme's Behat features or step definitions, overriding or blacklisting a core or Boost context, running core features under the theme, or a theme feature runs zero scenarios |
| [reference/visual-checks.md](../moodle-skill-files/moodle-theme-testing-release/reference/visual-checks.md) | Proving a colour, spacing, dark-mode, RTL or phone-width change; writing a computed-style step; light and dark accessibility pairs; checking pages in a real browser or taking screenshots |
| [reference/phpunit-for-themes.md](../moodle-skill-files/moodle-theme-testing-release/reference/phpunit-for-themes.md) | Writing PHPUnit tests beyond the compile test: setting-to-SCSS callbacks, rendering a template or a renderer as the theme, RTL build, the privacy compliance test, query counts |
| [reference/ci-for-themes.md](../moodle-skill-files/moodle-theme-testing-release/reference/ci-for-themes.md) | Writing or fixing the theme's GitHub Actions workflow, adding a dark-mode Behat run, reading a failed grunt, stylelint, Mustache or validate step |
| [reference/plugins-directory.md](../moodle-skill-files/moodle-theme-testing-release/reference/plugins-directory.md) | Preparing a release ZIP or a first submission, writing the listing, checking licences of fonts and images, or answering a Plugins directory reviewer |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](../moodle-skill-files/moodle-theme-testing-release/versions/moodle-5.2.md): no colour modes or `--colourmode`, so dark-mode scenarios must skip; axe 4.10.3; Classic still installed; templates copied from 5.3 that need partials 5.2 lacks |
| 5.3 | [versions/moodle-5.3.md](../moodle-skill-files/moodle-theme-testing-release/versions/moodle-5.3.md): `--colourmode` runs and the run header, `data-bs-theme` and `data-colourmode`, which themes get colour modes, Boost's 5.3 test files, axe 4.13.0 and `best-practice` on core pages, keeping 5.3-only steps off 5.2 rows, React/ESM builds that CI does not check, Classic gone |

## References

- https://moodledev.io/general/development/tools/behat/running
- https://moodledev.io/general/development/tools/behat/writing
- https://moodledev.io/docs/5.3/guides/colourmodes
- https://moodledev.io/general/development/policies/accessibility
- https://moodledev.io/general/development/policies/codingstyle/css
- https://moodledev.io/general/community/plugincontribution
- https://moodledev.io/docs/5.3/apis/commonfiles
- https://github.com/moodlehq/moodle-plugin-ci
- Core source, relative to the Moodle root: `public/lib/behat/classes/behat_config_util.php`,
  `public/lib/behat/classes/util.php`, `public/lib/behat/classes/behat_session_trait.php`,
  `public/lib/tests/behat/behat_accessibility.php`, `public/lib/tests/behat/behat_hooks.php`,
  `public/theme/boost/tests/`, `public/lib/classes/update/validator.php`
