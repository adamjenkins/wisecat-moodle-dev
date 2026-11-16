# PHPUnit for a theme: beyond the compile test

Read this when writing PHPUnit tests for a theme beyond the compile test in SKILL.md: the SCSS callbacks, an RTL
build, rendering a template or a renderer as the theme, the privacy compliance test, or a query count.

Evidence: the compile test and two callback tests were run on 5.3.0. The rest was read in the 5.2 and 5.3.0 source
(`public/lib/classes/output/theme_config.php`, `public/lib/pagelib.php`,
`public/lib/classes/output/renderer_factory/renderer_factory_base.php`,
`public/lib/classes/output/mustache_template_finder.php`, `public/privacy/tests/privacy/provider_test.php`) and not
run. PHPUnit is 11.5 on both versions.

## What to unit-test in a theme

Logic, not looks: the SCSS callbacks (what each setting value turns into, and what an invalid value turns into),
the compile itself, template and renderer output that the theme changes, the privacy provider, and any class with
real behaviour (navigation builders, observers, a backup of course-level data). Leave "does it look right" to Behat
and the browser.

Core's own theme tests are the reference: `public/theme/boost/tests/` (`scss_test.php`, `boostnavbar_test.php`,
`privacy/provider_test.php`; **5.3+:** `colour_mode_test.php`, `fonts_test.php`).

## The SCSS callbacks

Call the callback with a loaded theme; `theme_config::load()` includes the theme's and its parents' `lib.php`.

```php
    public function test_pre_scss_turns_the_radius_setting_into_a_variable(): void {
        $this->resetAfterTest();
        $theme = \theme_config::load('mytheme');

        set_config('cornerstyle', 'round', 'theme_mytheme');
        $this->assertStringNotContainsString('mytheme-radius', theme_mytheme_get_pre_scss($theme));

        set_config('cornerstyle', 'square', 'theme_mytheme');
        $this->assertStringContainsString('$mytheme-radius: 0;', theme_mytheme_get_pre_scss($theme));
    }
```

- `theme_config::load()` reads the settings when it is called and builds a new object each time. After
  `set_config()`, load the theme again before calling `get_css_content()`, or the old object still holds the old
  values in `$theme->settings`. A callback that calls `get_config()` itself sees the
  new value at once, as in the test above.
- For a Boost child, Boost's callbacks run with the child's settings. A test that sets `brandcolor` under
  `theme_mytheme` and finds the colour in the compiled CSS proves the inheritance (run on 5.3.0).
- Test the rejected values too: a colour setting that receives `red; } body { display: none` must not reach the
  SCSS, because one bad value breaks the whole compile and the site falls back to stock Boost.
- If the theme offers presets, compile once per preset it ships. A preset that uses design-system `$mds-*`
  variables does not compile on Boost's plain preset.

## The compile, per direction

```php
    public function test_the_rtl_build_flips_the_banner_border(): void {
        $this->resetAfterTest();
        $theme = \theme_config::load('mytheme');
        $theme->force_svg_use(true);
        $theme->set_rtl_mode(true);

        $css = $theme->get_css_content();

        $this->assertMatchesRegularExpression('/\.mytheme-banner\{[^}]*border-right:/', $css);
    }
```

A compile error inside `get_css_content()` calls `debugging()`, and `advanced_testcase` fails the test with
"Unexpected debugging() call detected" plus the compiler message. Core's `scss_test` additionally compiles with SassC
when `PHPUNIT_PATH_TO_SASSC` is defined; a site that sets `$CFG->pathtosassc` compiles with SassC instead of scssphp,
and a theme can pass one and fail the other.

## Rendering as the theme

In PHPUnit `CLI_SCRIPT` is true, so two defaults hide the theme's output:

- `$PAGE->theme` is the site theme (Boost on a test site), so templates resolve through Boost's overrides.
- `get_renderer()` without a target picks the CLI target, so it returns `core_renderer_cli`, never the theme's
  `core_renderer`.

Set the theme before anything touches `$PAGE->theme`, and ask for the general target:

```php
    public function test_the_notification_override_wraps_cores_markup(): void {
        global $PAGE;
        $this->resetAfterTest();
        $PAGE->force_theme('mytheme');
        $output = $PAGE->get_renderer('core', null, RENDERER_TARGET_GENERAL);

        $html = $output->render_from_template('core/notification_info', [
            'message' => 'Hello',
            'closebutton' => false,
            'announce' => false,
        ]);

        $this->assertStringContainsString('mytheme-notice', $html);
        $this->assertStringContainsString('Hello', $html);
        $this->assertStringNotContainsString('[[', $html);
    }
```

- `force_theme()` throws if the theme is already set on the page; call it first in the test. `advanced_testcase`
  gives each test a fresh `$PAGE`.
- Use the page's renderer (`$PAGE->get_renderer()`), not the global `$OUTPUT`, and do not depend on the order tests
  run in.
- The `[[` assertion catches a `{{#str}}` key that is missing from the lang file. `get_string()` with an unknown
  key also calls `debugging()`, so the test fails either way, whereas the live page prints `[[key]]` or throws while
  lint and Behat without that page stay green. Render every new or overridden template once.
- The context keys of a core template are in its docblock and its `Example context (json)`. Some core
  `export_for_template()` results contain `stdClass` objects, not arrays (for example `action_link` attributes);
  read the method before asserting on its shape.
- Do not name a context variable `uniqid`: the JavaScript template renderer overwrites it, so the PHP test passes
  and the browser-rendered template differs.

Whether a renderer method of the theme is used at all (the `rendererfactory` question) is best proved in Behat, by
a body class or a `data-region` the override adds; the PHPUnit path above shows only that the method works when
called.

## The privacy compliance test

Core has one test that every component must pass: `core_privacy\privacy\provider_test::test_all_providers_compliant`
in `public/privacy/tests/privacy/provider_test.php` (5.2 and 5.3). Its data sets are every plugin of every type,
themes included. A theme passes when it implements `null_provider`, or a metadata provider together with a request
provider (a theme with user preferences: `user_preference_provider`). The same class checks that the
`privacy:metadata...` strings exist.

`moodle-plugin-ci phpunit` runs only the theme's own tests, so this test never runs in plugin CI. Run it yourself on
a site with the theme installed, from the Moodle root:

```bash
vendor/bin/phpunit --filter 'theme_mytheme' public/privacy/tests/privacy/provider_test.php
```

The data sets are named by component, so the filter selects the theme's rows of every test in that file. Writing
the provider is covered in `moodle-theme-settings` (user preferences) and `moodle-theme-boost-child`.

## Query counts on hot paths

Anything the theme runs on every page (a navigation builder, a setting lookup per context, a hook callback) is
worth a ceiling:

```php
        global $DB;
        $before = $DB->perf_get_queries();
        $output->render_from_template('theme_mytheme/footer', $context);
        $this->assertLessThanOrEqual(2, $DB->perf_get_queries() - $before);
```

Plugins directory reviewers do count queries: a configuration lookup repeated for every context on a page is a
known finding, fixed with a request cache. The same applies to a theme that reads course or category settings for
every block or menu item.

## Running

```bash
php public/admin/tool/phpunit/cli/init.php
vendor/bin/phpunit --testsuite theme_mytheme_testsuite
vendor/bin/phpunit --filter 'theme_mytheme\\lib_test'
```

`init.php` writes a `theme_mytheme_testsuite` entry into the root `phpunit.xml` for every installed theme with a
`tests/` directory. Setup, generators and the general rules are in `moodle-phpunit-testing`.
