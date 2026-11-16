# Behat testing: what is specific to Moodle 5.3

Against the 5.2 baseline. Read in the 5.3.0 and 5.2 source, not run for this file. The full 5.3 catalogue is in
`moodle-5-3-changes`; theme suites and dark-mode runs are in `moodle-theme-testing-release`.

## Markup that custom selectors depend on

| What | 5.2 | 5.3 | Source |
|---|---|---|---|
| Modal title element | `<h5 class="modal-title">` | `<h2 class="modal-title fs-5">` | `public/lib/templates/modal.mustache` on each branch |
| Primary and secondary navigation items | Bootstrap `.nav-link`, `.active` (`public/lib/templates/moremenu_children.mustache`) | `.mds-nav-pill`; selected is `.mds-nav-pill--selected` in the primary navigation and `.mds-nav-pill.active` or `aria-current` in the secondary | The React component `public/lib/js/esm/src/nav/Nav.tsx`; `public/theme/boost/tests/behat/behat_theme_boost_behat_navigation.php` shows the selectors core accepts |
| Navbar search | A toggle button that opens the field | An inline field; the "togglesearch" button shows only on small screens | `public/search/tests/behat/behat_search.php`, 5.3.0 |

A custom step or `css_element` locator written against the 5.2 markup (`h5.modal-title`, `.nav-link.active`) finds
nothing on 5.3. Fix: use the named selectors, `"Delete item" "dialogue"` for modals and the link text for navigation,
which work on both; for the selected item use the steps `I should see "Grades" is active in navigation` and
`... is active in secondary navigation`, which Boost's own Behat context implements on each branch. The Mustache
navigation templates still exist on 5.3 as the fallback without JavaScript, so a scenario without `@javascript`
can still see `.nav-link`. A step that must open the search field copies core's check: click "togglesearch" only
when the button is visible.

## Steps and options that exist only on 5.3

- `I set the focus on the "<element>" "<selector>"` (JavaScript only; `public/lib/tests/behat/behat_general.php`).
- `Given the run is not using a colour mode`, which skips the scenario when the site was initialised with
  `init.php --colourmode=<mode>` (`behat_general.php`; `public/lib/behat/lib.php`, `behat_get_colour_mode()`). The
  option and the step are absent from 5.2, so a feature that runs on both branches must not use the step.
- `the course linear navigation should be visible` and `... should not be visible`
  (`public/course/format/tests/behat/behat_courseformat.php`). Course formats that opt in show linear navigation by
  default, so text such as "Next activity" can appear on 5.3 pages and not on 5.2.
- The run banner gains "Colour mode:" under "Run optional tests:" (`public/lib/behat/classes/util.php`).
- The named selector `"<aria-label>" "navigation"`, which matches a `<nav>` or `role="navigation"` element by its
  `aria-label` (`public/lib/behat/classes/partial_named_selector.php`). On 5.2 it is an unknown selector, so scope
  with `"css_element"` or a `"region"` there.

## A step renamed

`I set portfolio instance "X" to "Y"` is deprecated in 5.3 in favour of `I set the portfolio instance "X" to "Y"`
(`public/mod/workshop/tests/behat/behat_mod_workshop_deprecated.php`, `public/portfolio/tests/behat/behat_portfolio.php`,
MDL-89069). On 5.3 the old step throws "Deprecated step, rather than using this step you can:" unless
`$CFG->behat_usedeprecated` is set; on 5.2 the new step does not exist. A feature that must run on both branches
defines its own step in the plugin's `behat_<component>.php` rather than using either.
