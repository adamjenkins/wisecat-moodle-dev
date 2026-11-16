# Layouts and templates: what is specific to Moodle 5.2

Read this when the theme must run on 5.2, or when a layout or template written against 5.3 has to be made to work
there.

5.2 is the baseline: the rules in `SKILL.md` hold on it unless tagged. This file lists what a 5.2 site has that
5.3 changed, and what a file taken from 5.3 breaks on 5.2. All of it was read in the 5.2 source and compared with
5.3.0 by `diff`. Nothing was run on 5.2.

## What is the same

- The theme engine: layout cascade, layout file lookup, regions, layout options and their readers
  (`public/lib/classes/output/theme_config.php` differs from 5.3.0 in one hunk, about font paths).
- Template lookup, the `!` suffix (new in 5.2), block parents, helpers, the compile cache
  (`mustache_template_finder.php`, the Mustache loaders and the Mustache library are byte-identical).
- Boost's `config.php` and every file in `public/theme/boost/layout/`.
- The drawer ids, toggle attributes and user preferences.
- The Bootstrap 4 compatibility layer and its deprecation outline under Behat and theme designer mode.

## What a 5.3 file breaks on 5.2

| Taken from 5.3 | On 5.2 | Fix |
|---|---|---|
| `{{> core/secondarymoremenu}}` or `{{> core/primarymoremenu}}` | The template does not exist: `filenotfound` exception when the surrounding section renders, so on every page that has that navigation | Choose the partial by the `reactprops` key (see `SKILL.md`, "One copied template for 5.2 and 5.3"), falling back to `{{> core/moremenu}}` |
| `{{$drawercontrols}}` in a `{{< theme_boost/drawer }}` | Unknown block, ignored: the course index controls are missing | Also fill `{{$drawerheadercontent}}` with the same content |
| `{{# output.colour_mode_menu }}` | The method does not exist; the section renders nothing | None needed |
| `{{> core/user_action_menu_item_link}}` and the other split user menu partials, `core/search_input_navbar_inline`, `core/supplementary_sticky_footer`, `theme_boost/colour_mode_menu` | Do not exist: `filenotfound` | Do not copy 5.3's `core/user_menu` or `core/user_action_menu_items` into a theme that supports 5.2 |
| `$PAGE->set_has_sticky_footer()`, `set_show_navigation_footer()`, `set_supplementary_content()` | Undefined method: fatal error | `method_exists()` guard |
| A React mount (`{{#react}}` with a 5.3 component name) | The helper exists on 5.2 and prints the mount point, but 5.2 ships none of the 5.3 components; what the page then shows was not checked | Do not mount 5.3 components on 5.2: put the mount inside the `reactprops` switch |
| `html_writer::react_component()`, `\core\output\react_component_renderable` | Do not exist | `class_exists(\core\output\react_component_renderable::class)` guard |

A missing partial is fatal because core's template finder throws a `moodle_exception`, and the Mustache engine
only swallows its own unknown-template exception. A missing renderer method is silent because Mustache checks
that the method exists before calling it (`method_exists()` in `public/lib/mustache/src/Context.php`).

## Markup that 5.2 has and 5.3 changed

| On 5.2 | Notes |
|---|---|
| Primary and secondary navigation are `core/moremenu` with the `core/moremenu` AMD module | Markup: `nav.moremenu.navigation > ul.nav.more-nav > li.nav-item > a.nav-link(.active)`. Selectors: `.primary-navigation .moremenu`, `.secondary-navigation .moremenu` |
| Core Behat steps "I select ... from primary navigation" look for `.primary-navigation .moremenu.navigation` | On 5.3 they look for `.primary-navigation .navigation.primarynav-navbar`. A theme's own Behat steps that address navigation need a selector per version |
| `theme_boost/drawer` has the block `drawerheadercontent` inside `div.draweractions` | Renamed `drawercontrols` and moved on 5.3 |
| `theme_boost/courseindexdrawercontrols` is a dropdown menu | One toggle button on 5.3 |
| Boost overrides `core/loginform` (`public/theme/boost/templates/core/loginform.mustache`) and has `core_renderer::render_login()` | Both removed from Boost on 5.3; core's template has new markup |
| The edit mode switch is Bootstrap's `.form-switch` | Design-system switch on 5.3 |
| `block_timeline` has `templates/` and `amd/` | Rendered by React on 5.3; template overrides for it apply on 5.2 only |
| The Classic theme is in core (`public/theme/classic`), with `columns.php`, `side-pre` and `side-post` | Removed from core on 5.3 |
| No `data-bs-theme` on `<html>`; no colour mode menu | Bootstrap's dark-mode variables are in the CSS, but nothing sets the attribute |

## Choosing how to support both

- **No copied templates:** one code base with `$plugin->supported = [502, 503];` is realistic. Overrides that
  wrap with `!`, renderer methods and hooks behave the same on both.
- **A copied `drawers.mustache` only:** one code base still works, with the two-block and `reactprops` switches.
- **A copied navbar, user menu or login form, or navigation styling:** each copy has a different original in each
  version. Use one branch per Moodle version, each with its own `.upstream` twins and
  `$plugin->supported = [502, 502];` or `[503, 503];`. The large Boost child themes work this way.

When a version test is needed in PHP, test for the feature, not the number: `class_exists()` or
`method_exists()`. `$CFG->branch` is a stored value that still holds the old branch while an upgrade is running.
