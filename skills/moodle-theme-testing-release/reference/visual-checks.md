# Proving how the theme looks: computed styles, dark mode, RTL, phones, accessibility, real browsers

Read this when proving a colour, spacing, dark-mode, RTL or phone-width change, writing a computed-style step,
writing light and dark accessibility pairs, or checking theme pages in a real browser or with screenshots.

Evidence: dark mode through `--bs-*` custom properties (computed styles in a browser), the automatic RTL flip (an
RTL build read back) and axe with WCAG 2.0-2.2 A and AA tags (no violations on a course page, light and dark, axe
injected by a browser script) were run on 5.3.0 with a Boost child theme. The Behat steps below and the RTL scenario
were read in the source, not run. Nothing was run on 5.2.

## Arrival is not effect

A theme rule goes through three stages, and each needs its own proof:

1. **In the compiled CSS**: the PHPUnit compile test asserts it.
2. **In the stylesheet the page loads**: fetch the stylesheet URL from a rendered page
   (`/theme/styles.php/<theme>/<revision>_<subrevision>/all`) and search it for a literal, brace-free fragment of the
   rule (`grep -F 'mytheme-banner'`). A fragment with `{` or `:` often differs in the minified output.
3. **Applied to the element**: only the computed value, a geometry check or a picture shows it. A one-class rule on
   an element Bootstrap styles (`.btn`, `.card`) loses to Bootstrap at equal specificity, because the theme's own
   Bootstrap rules are compiled into the same sheet. Set Bootstrap's own variables from a selector that outranks
   it, `.btn.mytheme-cta { --bs-btn-bg: var(--mytheme-accent); }`, then assert the computed colour.

Right after a purge, the first stylesheet request can still be answered with the previous build while the new one
compiles (`$THEME->usefallback`, inherited from Boost). Fetch the stylesheet and check stage 2 before judging stage 3,
and reload once before debugging a selector.

## A computed-style step

A method for the theme's own context, `tests/behat/behat_theme_mytheme.php`: a class `behat_theme_mytheme` that
extends `behat_base`, in a file that starts with `require_once(__DIR__ . '/../../../../lib/behat/behat_base.php');`
and has no `MOODLE_INTERNAL` check. The selector and property go through `json_encode()`, so quotes in them cannot
break the script.

```php
    /**
     * Checks a computed CSS property of the first element that matches a CSS selector.
     *
     * @Then the computed :property of :selector should be :expected
     * @param string $property CSS property name, for example background-color
     * @param string $selector CSS selector
     * @param string $expected The value as getComputedStyle() reports it, for example rgb(18, 52, 86)
     */
    public function the_computed_style_should_be(string $property, string $selector, string $expected): void {
        $this->require_javascript();
        $script = 'return (() => {
            const el = document.querySelector(' . json_encode($selector) . ');
            return el ? window.getComputedStyle(el).getPropertyValue(' . json_encode($property) . ').trim() : null;
        })();';
        $actual = $this->evaluate_script($script);
        if ($actual === null) {
            throw new \Behat\Mink\Exception\ExpectationException(
                "No element matches '{$selector}'", $this->getSession());
        }
        if ($actual !== $expected) {
            throw new \Behat\Mink\Exception\ExpectationException(
                "'{$selector}' has {$property} '{$actual}', expected '{$expected}'", $this->getSession());
        }
    }
```

Use in a `@javascript` scenario:

```gherkin
    Then the computed "background-color" of ".mytheme-banner" should be "rgb(18, 52, 86)"
    And the computed "--bs-primary" of "html" should be "#123456"
```

- Browsers report colours as `rgb()` or `rgba()`, lengths in `px`, and custom properties as the literal text of
  their value after `trim()`. Assert those forms, not the SCSS source.
- A custom property that is not defined returns an empty string. Checking the names the theme reads is the only way
  to catch `var(--name, fallback)` quietly using the fallback: an undefined name looks right on the theme the
  fallback was chosen for and wrong everywhere else. Bootstrap's `--bs-*` names exist on 5.2 and 5.3; the
  design-system names (`--mds-*`) exist only on 5.3 and not inside the editor iframe (`moodle-theme-scss`).
- `animation-fill-mode: both` or `forwards` keeps the last keyframe's values above every later declaration; a
  computed-style check after the animation shows it. Use `backwards` for entrance animations.
- Large Boost-based themes ship similar steps for "has a successfully loaded background image", "should not overlap
  with" and "horizontal gap of N pixels". Write each as above: one `evaluate_script()` that returns a plain value,
  compared in PHP.

## Dark mode (5.3+)

Boost's colour modes exist on 5.3 only; a child of Boost inherits them, because
`theme_boost\colour_mode::is_boost_theme()` accepts any theme with `boost` among its parents
(`public/theme/boost/classes/colour_mode.php`, 5.3.0). The switch and the default are Boost's settings
(`theme_boost/enablecolourmodes`, `theme_boost/defaultcolourmode`); the user's choice is the preference
`theme_boost_colourmode`. On the page, dark mode is `data-bs-theme="dark"` on `<html>`.

Pin a mode in a scenario and check it took effect:

```gherkin
  @javascript @accessibility
  Scenario Outline: The course page meets accessibility standards in <mode> mode
    Given the site is running Moodle version 5.3 or higher
    And the following config values are set as admin:
      | enablecolourmodes | 1 | theme_boost |
    And the following "user preferences" exist:
      | user     | preference             | value  |
      | student1 | theme_boost_colourmode | <mode> |
    When I am on the "Course 1" course page logged in as student1
    Then the "data-bs-theme" attribute of "html" "css_element" should contain "<mode>"
    And the page should meet accessibility standards

    Examples:
      | mode  |
      | light |
      | dark  |
```

- `the site is running Moodle version 5.3 or higher` skips the scenario on 5.2 (it throws a skip, defined in
  `public/lib/tests/behat/behat_general.php` in both versions), so one feature file serves both branches.
- Keep the light example: it is the baseline. A failure only in dark is a colour-mode regression; a failure in both
  is a problem of the page.
- Instead of pinning, a whole run can be made dark with `init.php --colourmode=dark`; a preference set in a scenario
  still wins, and `Given the run is not using a colour mode` skips scenarios that assume no mode. Boost's own
  `public/theme/boost/tests/behat/colour_mode_accessibility.feature` is the model. In CI, a dark run is a second
  initialisation, `php public/admin/tool/behat/cli/util_single_run.php --enable --add-core-features-to-theme
  --scss-deprecations --colourmode=dark` run from the Moodle checkout's root, followed by `moodle-plugin-ci behat` without
  `--scss-deprecations`, because that flag re-initialises and clears the mode (read in moodle-plugin-ci 4.5.11 and
  the 5.3.0 CLI scripts, not run).
- Contrast targets from the colour modes guide: 4.5:1 for text, 3:1 for large text, 3:1 for UI components, focus
  indicators and meaningful graphics. axe checks text contrast, not most of the others.
- Check by eye in dark mode: borders, focus rings, form controls, icons, editor content, and anything with a colour
  set in a setting.
- Icons shown as `<img>` do not follow the text colour. Font Awesome mapped icons are `<i>` and do; an unmapped pix
  icon, including every plugin's and theme's `pix/icon.svg` on `admin/plugins.php`, is an `<img>`. Boost's dark
  mode inverts only `<img>` icons whose URL contains `/t/`, `/e/`, `/a/` or the group icons
  (`public/theme/boost/scss/moodle/icons.scss`, 5.3.0). A dark stroke such as `#212529` is close to invisible on the
  dark page background (`#1d2125`). Read in the source and reasoned, not seen in a browser: use a mid-tone stroke,
  or add `[data-bs-theme="dark"] img.pluginicon { filter: invert(1); }` for single-colour line icons.

## RTL

- RTL CSS is produced by flipping the compiled LTR CSS (`left` becomes `right`, and so on). Run on 5.3.0:
  `border-left` came out as `border-right` with no directive. The directives are in `moodle-theme-scss`.
- The RTL sheet can be fetched whatever the user's language: `/theme/styles.php/<theme>/<revision>_<sub>/all-rtl`.
  From the command line: `php admin/cli/build_theme_css.php --themes=mytheme --direction=rtl`. In PHPUnit:
  `$theme->set_rtl_mode(true)` before `get_css_content()`.
- A page renders RTL when the current language's `thisdirection` string in `core_langconfig` is `rtl`
  (`right_to_left()`, `public/lib/weblib.php`). Behat sites have only English, and the `language packs` generator
  downloads a pack, which core guards with `remote langimport tests are enabled`. A scenario that customises the
  string instead should work, but was not run:

```gherkin
  @javascript
  Scenario: The banner sits on the right in a right-to-left language
    Given the following "language customisations" exist:
      | component       | stringid      | value |
      | core_langconfig | thisdirection | rtl   |
    When I am on the "Course 1" course page logged in as student1
    Then "body.dir-rtl" "css_element" should exist
```

- In Behat only the LTR CSS is built at initialisation; an RTL page compiles its CSS on first request, which is
  slower but not wrong.

## Phones and the fixed navbar

- `I change the viewport size to "mobile"` (or `tablet`, `WxH`) in Behat; in a browser script, a phone-sized viewport.
- Horizontal overflow: `document.documentElement.scrollWidth > window.innerWidth` means the page scrolls sideways.
  A Bootstrap `.row` outside a `.container` keeps its negative gutters and makes the page a few pixels wider than
  the phone; only this check shows it. Fix with `mx-0` or a container.
- "Inside the viewport" is not "visible". Boost's fixed navbar (about 60 px), on-screen keyboards and floating
  buttons such as the course index toggle cover content that a rectangle check passes. Test the element's centre and
  inner corners with `document.elementFromPoint(x, y)` and check the hit is the element or inside it. Code that
  scrolls an element into view on a phone must treat the navbar's bottom as the top of the visible area.
- Content inside `div.no-overflow` (filtered text, wide tables) that is taller than its line is clipped at the top in
  Firefox and barely in Chromium; look in both.

## Accessibility beyond the Behat step

- The Behat axe step and its rules are in SKILL.md. When the step cannot run locally (axe script blocked, "No
  data"), injecting the same axe-core file into the page from a browser script and calling
  `axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag21a', 'wcag22a', 'wcag2aa', 'wcag21aa', 'wcag22aa']}})`
  gives the same rule set. It does not replace the scenario in CI.
- What the policy asks of a theme in particular (https://moodledev.io/general/development/policies/accessibility):
  WCAG 2.2 AA; a visible focus indicator; link and button targets of at least 44 by 44 px; landmark regions with
  unique labels, which is done in the layout files.
- Keyboard: tab through the header, the drawers and the footer in both modes; the focus ring must be visible on
  every control the theme restyled.
- H5P content is in an iframe and gets no theme CSS at all: not the theme's SCSS, not `additionalhtmlhead`, not a
  plugin's `styles.css`. Only the `core_h5p | h5pcustomcss` setting reaches it, and axe does not enter the iframe.

## Real browsers and screenshots

- Check every changed screen in Firefox and in a Chromium browser. Layout, clipping and some APIs differ, and a check
  in one engine has missed defects that the other showed at once.
- Check as each role that sees the change, and also as an administrator: admins see extra controls that change the
  layout.
- On a normal (non-Behat) site, a new user's first dashboard visit opens a user tour that covers the page and
  catches clicks. Mark the tours done for that test user, for each tour id in `tool_usertours_tours`:
  `set_user_preference('tool_usertours_tour_completion_time_' . $tourid, time(), $user);`.
- Close the drawers before a screenshot (`set_user_preference('drawer-open-block', 0, $user)` and
  `drawer-open-index`), or they cover the page content.
- An element screenshot of `#region-main` can slide under the fixed navbar; take the full page and crop.
- A full-page screenshot with the performance footer on (`perfdebug`) is mostly footer; turn it off for pictures.
- On a Boost page "the submit button" is never unique: the drawer toggles, the search and several unlabelled
  buttons come before "Save changes". Select by accessible name, never by `[type=submit]`.
- A screenshot proves what it shows, not what the report says: name the change it should show before taking it, and
  look for that change in the picture.
