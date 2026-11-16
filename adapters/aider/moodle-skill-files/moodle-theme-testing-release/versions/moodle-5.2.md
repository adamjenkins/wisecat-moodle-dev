# Testing and releasing a theme on Moodle 5.2

Read this when the theme supports Moodle 5.2 (`MOODLE_502_STABLE`, `$plugin->supported` including 502), or when one
feature file and one workflow must serve both 5.2 and 5.3.

Evidence: read in the 5.2 source (Moodle 5.2.2+), not run. Nothing in this skill was run on 5.2 apart from Mustache
lint on a 5.2 tree. The Behat suite mechanics, the PHPUnit version and the CLI paths are the same as on 5.3.

## No colour modes

- Boost on 5.2 has no light and dark modes: no `theme_boost/enablecolourmodes` setting, no switcher, no
  `data-bs-theme` attribute written by Boost, no `theme_boost_colourmode` preference that does anything.
- The Behat CLI scripts have no `--colourmode` option (`public/admin/tool/behat/cli/init.php`); passing it is an
  error. The run header lists Accessibility, SCSS deprecations and Icon deprecations only.
- `Given the run is not using a colour mode` does not exist. `Given the site is running Moodle version 5.3 or higher`
  does (`public/lib/tests/behat/behat_general.php`, 5.2 and 5.3): it compares `normalize_version()` of the release
  string and skips the scenario. Put it first in every dark-mode scenario so the file still runs on 5.2 rows.
- A 5.2 and 5.3 theme that writes its own dark rules writes `[data-bs-theme="dark"] .mytheme-banner { ... }` by hand;
  Boost's `dark-mode` mixin and `scss/moodle/colour-mode.scss` exist on 5.3 only (`moodle-theme-scss`). On 5.2 these
  rules simply never match, which no test can tell from "dark mode works".

## axe on 5.2

5.2 bundles axe-core 4.10.3 (`public/lib/behat/axe/axe.min.js`); the step code and the default rule tags are the same
as on 5.3. A scenario green on 5.2 can fail on 5.3's newer axe with no theme change, so run the accessibility
scenarios on both rows.

## Classic is still installed

Classic (`public/theme/classic/`) is a standard theme on 5.2, so a 5.2 site has a `classic` Behat suite next to
`default` and the theme's own. It does not affect the theme's suite. Classic's
`tests/behat/behat_theme_classic_behat_*.php` files are the most complete example of a child of Boost that overrides
core steps because its navigation differs; read them on 5.2, but do not depend on them in a theme that also
supports 5.3, where Classic is gone.

## Templates copied from 5.3

A layout or template copied from 5.3.0 can include partials that 5.2 lacks: Boost's 5.3 `drawers.mustache` uses
`core/secondarymoremenu`, which is not in 5.2's `public/lib/templates/`. Mustache lint does not report it: a partial
the linter cannot find renders as nothing (read in the linter bundled with moodle-plugin-ci 4.5.11 and its Mustache
library, not run). Only a page render on a 5.2 row shows the failure, so the theme's Behat feature must load every
copied layout on 5.2 too, and the copies are made from the lowest supported branch or kept per branch.

## What is the same

- Suites, tags, `blacklist.json`, context overrides, `--scss-deprecations`, `--no-axe` and `--add-core-features-to-theme`:
  identical code in `public/lib/behat/classes/behat_config_util.php`.
- PHPUnit 11.5, `theme_mytheme_testsuite`, the compile fallback in `theme_config::get_css_content()`.
- The ZIP validator (`public/lib/classes/update/validator.php`), the theme selector's screenshot and `choosereadme`,
  and the plugins page icon.
- Boost's `thirdpartylibs.xml` on 5.2 lists Bootstrap, Font Awesome and the design system, not fonts; a theme's own
  entries follow the same format.
