# Layouts and templates: what is specific to Moodle 5.3

Read this when the theme targets 5.3, when a template copied on 5.2 must be ported, or when you need to know what
a template override can still reach in the React-rendered parts.

Everything here was read in the 5.3.0 source and compared with 5.2 by `diff`. The layout copy and the `!` include
were run on 5.3.0; no React component was built or overridden, so every statement about React behaviour is
"read in the source, not run".

## Boost files that changed from 5.2

`layout/*.php` and `config.php` did not change. Templates:

| Boost template | Change in 5.3.0 | What a copy taken from 5.2 does on 5.3 |
|---|---|---|
| `drawers.mustache` | Course index controls go in block `drawercontrols` (was `drawerheadercontent`); secondary navigation partial is `core/secondarymoremenu` (was `core/moremenu`) | Renders, with the legacy secondary menu and without the course index expand and collapse control |
| `columns2.mustache` | Same partial swap | Renders with the legacy menu |
| `navbar.mustache` | Primary navigation partial is `core/primarymoremenu` (was `core/moremenu`); a divider after the search box removed; new `{{# output.colour_mode_menu }}` block | Renders with the legacy menu and no colour mode switcher. If the site default is dark or follows the system, users have no control to change it |
| `drawer.mustache` | New wrapper `drawerheadertop`; block `drawerheadercontent` removed; block `drawercontrols` added in a new `div.drawercontrols` | A child that fills `drawerheadercontent` gets nothing there, with no error |
| `courseindexdrawercontrols.mustache` | The dropdown became one toggle button, `data-action="toggleallcourseindexsections"` | The old actions are no longer handled by Boost's `courseindexdrawercontrols` module |
| `courseindexdrawerheading.mustache` | Classes changed, `role="button"` dropped | Cosmetic |
| `footer.mustache` | `bg-secondary` became `text-bg-secondary` on the popover button | Cosmetic |
| `core/sticky_footer.mustache` | `h-100` dropped | Cosmetic |
| `core/loginform.mustache` | Removed from Boost. The template is now core's `public/lib/templates/loginform.mustache`, with new markup (icons in `login-input-wrapper`, an OAuth2 client block) | A child override at `templates/core/loginform.mustache` still wins, with the 5.2 markup: re-diff it |
| `colour_mode_menu.mustache`, `core/supplementary_sticky_footer.mustache` | New | Not present on 5.2 |

Boost's renderer changed with them: `search_box()` and `colour_mode_menu()` were added, `render_login()` was
removed (core's `render_login()` renders `core/loginform` and no longer adds `logourl`, `sitename` or
`hasauthinstructions` to the context). A child renderer that calls `parent::render_login()` expecting Boost's
context keys gets core's.

## Core templates that changed

From `diff -rq` of `public/lib/templates` between 5.2 and 5.3.0. An override that copies one of these from 5.2
needs a re-diff:

| Template | Change |
|---|---|
| `core/editswitch` | Mounts a React component; fallback markup uses `mds-switch*` classes instead of Bootstrap's `.form-switch` |
| `core/modal` | The title is `<h2 class="modal-title fs-5">` |
| `core/notification`, `core/notification_base`, `core/notification_info`, `core/notification_success`, `core/notification_warning`, `core/notification_error` | Optional `headinglevel` |
| `core/user_menu`, `core/user_action_menu_items` | Items split into `core/user_action_menu_item_link`, `_header`, `_text`, `_divider` |
| `core/loginform` | New markup; `core/local/login_form/*` partials added |
| `core/block`, `core/activity_header`, `core/filemanager_page_generallayout`, `core/local/toast/message`, `core/local/choicelist`, `core/local/dropdown/dialog` | Changed |
| `core/external_content_banner` | Deprecated, to be removed in 6.0 |
| New: `core/primarymoremenu`, `core/secondarymoremenu`, `core/search_input_navbar_inline`, `core/supplementary_sticky_footer`, `core/action_bar`, `core/navigation_action_bar` | Not present on 5.2 |

`core/moremenu` and `core/moremenu_children` are unchanged and still shipped.

## New `moodle_page` methods a layout may meet

`$PAGE->set_has_sticky_footer()`, `$PAGE->set_show_navigation_footer()` and `$PAGE->set_supplementary_content()`
exist only from 5.3 (`public/lib/pagelib.php`). Calling them from a layout file or renderer that also runs on 5.2
needs a `method_exists($PAGE, 'set_has_sticky_footer')` guard.

## What React renders, and what a template can still reach

Four mount points exist in core 5.3.0 (search for the `react` helper and `html_writer::react_component()` over
`public/`):

| Part | Mounted from | Template override reaches | Does not reach |
|---|---|---|---|
| Primary navigation | `core/primarymoremenu`, included by `theme_boost/navbar` inside `div.primary-navigation` | The wrapper, the mount point's classes, which component is mounted, the no-JavaScript fallback | The items, the "More" overflow logic, the dropdown markup |
| Secondary navigation | `core/secondarymoremenu`, included by `theme_boost/drawers` and `theme_boost/columns2` inside `div.secondary-navigation` | The same | The same |
| Edit mode switch | `core/editswitch`, rendered by `core_renderer::edit_switch()` | The form wrapper, the fallback switch markup | The mounted switch |
| Timeline block | PHP: `html_writer::react_component()` in `public/blocks/timeline/block_timeline.php` | Nothing. The block has no `templates/` directory any more | Everything |

Everything else is Mustache and AMD on 5.3 as on 5.2: user menu, language menu, drawers, course index,
breadcrumb, footer, tertiary navigation, activity chooser, course content.

How the three templates work:

```mustache
{{#reactprops}}
{{#react}}
{
    "component": "@moodle/lms/core/nav/Nav",
    "class": "secondarynav-tabbar navigation",
    "props": {{{reactprops}}}
}
<nav class="moremenu navigation"{{#navlabel}} aria-label="{{.}}"{{/navlabel}}>
    (server-rendered fallback built from core/moremenu_children)
</nav>
{{/react}}
{{/reactprops}}
```

- The `react` helper prints one `<div>` with `data-react-component`, `data-react-props` and every other JSON key
  as an attribute (so `"class"` becomes the class of the mount point). The text after the JSON is the content of
  that div: the fallback (`public/lib/classes/output/mustache_react_helper.php`).
- On page load the fallback is replaced by the component. Without JavaScript the fallback is all there is.
- `reactprops` is a JSON string built in PHP: `core\navigation\output\more_menu::export_react_props()` for
  secondary navigation and `core\navigation\output\primary::export_react_props()` for primary. Both are
  `protected`, so a subclass can add to them (`moodle-theme-renderers-output`).

Rules for a theme template around them:

- **Do not wrap `core/secondarymoremenu` in a `<nav>`.** The component renders the navigation landmark itself,
  and the fallback renders the same one. An extra `<nav>` gives two nested landmarks. The template's own comment
  says so.
- **Keep the mount point classes.** Boost hides the bar with `opacity: 0` under `.jsenabled` until the component
  adds `primarynav-measured` or `secondarynav-measured` to the mount point
  (`public/theme/boost/scss/moodle/primarynavigation.scss`, `secondarynavigation.scss`). A template that keeps
  `primarynav-navbar` but mounts a component that never adds the measured class leaves the navigation invisible.
- **Keep `div.primary-navigation` and `div.secondary-navigation` around them.** Core's Behat steps "I select ...
  from primary navigation" and "... from secondary navigation" look for
  `.primary-navigation .navigation.primarynav-navbar` and `.secondary-navigation .navigation.secondarynav-tabbar`
  (`public/lib/tests/behat/behat_navigation.php`). A theme that drops the wrapper, or keeps the legacy
  `core/moremenu` partial, fails those steps in every plugin's Behat suite run under the theme.
- **The legacy partial still works as a stop-gap.** `core/moremenu` is still shipped and the exporters still fill
  `nodecollection`, `nodearray` and `moremenuid`, so a navbar that says `{{> core/moremenu}}` renders the old
  markup on 5.3. No core template uses it any more, Boost's `moremenu.scss` changed, and how it looks was not
  checked in a browser. Treat it as temporary.
- **A copy of `core/editswitch` copies a duty.** Its fallback markup mirrors the design system's Switch by hand;
  core's comment says template and component must change together.

## Class names and selectors

With JavaScript on, navigation items are design-system nav pills, not Bootstrap nav links:

| 5.2 selector | 5.3 with JavaScript |
|---|---|
| `.primary-navigation .moremenu` | `.primary-navigation .navigation.primarynav-navbar` |
| `.primary-navigation .nav-link` | `.primarynav-navbar .mds-nav-pill` |
| `.nav-link.active` | `.mds-nav-pill--selected`, also `[aria-current="page"]`; on tab-list pages the selected state is Bootstrap's `.active` |
| `.secondary-navigation .moremenu` | `.secondary-navigation .navigation.secondarynav-tabbar` |
| `.form-switch` in the edit switch | `.mds-switch`, `.mds-switch-input`, `.mds-switch-control`, `.mds-switch-track`, `.mds-switch-thumb`, `.mds-switch-label` |

Structure that stayed Bootstrap: `ul.nav.more-nav`, `li.nav-item`, `li.dropdownmoremenu`, `.dropdown-menu`,
`.dropdown-item`, `.dropdown-divider`.

- The old selectors still match the fallback, so a look at the page with JavaScript disabled is misleading.
- The pill styles are in the theme stylesheet, not in the JavaScript: Boost's default preset imports the design
  system's component styles. A theme compiled from a preset without them gets unstyled navigation
  (`moodle-theme-scss`).
- Colour and shape changes need no template work: set the design tokens (`--mds-bg-nav-pill-selected`,
  `--mds-bg-nav-pill-hover`) or style `.mds-nav-pill` from SCSS.

## Order of tools for changing React navigation

1. Tokens and SCSS (`moodle-theme-scss`).
2. A template override of the mounting template: wrapper, classes, fallback.
3. A PHP subclass of the navigation exporter to add data (`moodle-theme-renderers-output`).
4. A component override or the theme's own component (`moodle-theme-renderers-output`). Component overrides do
   not fall back through parent themes, unlike template overrides.

A template the theme carried for `block_timeline` is a dead file on 5.3, and a renderer override of
`block_timeline\output\renderer` must be deleted: the class no longer exists, and a class extending a missing
parent is a fatal error when it is loaded.

## Other 5.3 facts for layouts

- **Colour modes reach every Boost child.** When the site administrator enables colour modes, Boost's hook puts
  `data-bs-theme` on `<html>` for any theme with `boost` in its parents; the child cannot opt out with a setting
  of its own. A layout template with hard-coded light backgrounds (`bg-white`, inline colours) shows unreadable
  pairs in dark mode. Use `bg-body`, `text-body` and `border` utilities in layout markup.
- **A custom navbar needs the colour mode menu.** Copy the `{{# output.colour_mode_menu }}` block from Boost's
  `navbar.mustache`. It needs the theme's renderer to extend `theme_boost\output\core_renderer`.
- **Classic is gone from core.** A theme with `classic` in its parents cannot load on a stock 5.3 site. What
  Classic provided and such a theme must now own: the `columns.php` layout with `side-pre` and `side-post`
  regions, `contentonly.php`, its navbar template, and `activityinfoinheader => false` on `incourse`.
- **Docs lag.** The 5.3 React theming page on moodledev.io says theme overrides of components exist since 5.2;
  the 5.2 source has no such code. Its examples also name the Classic theme.

## Announced for 6.0

Read in the 5.3.0 source and upgrade notes; no 6.0 tree was read.

- The Bootstrap 4 compatibility layer (`scss/moodle/bs4-compat.scss` and the `theme_boost/bs4-compat` script that
  rewrites `data-toggle` to `data-bs-toggle`) is marked for removal in 6.0. Templates that still use Bootstrap 4
  names work on 5.2 and 5.3 only because of it.
- `core/external_content_banner` and the `dataattributes` key of `core/toggle` (use `extraattributes`) are marked
  for removal in 6.0.
- 5.3 moved four regions to design-system React components. Nothing read here lists which come next, but a later
  release can turn another template override into a dead file in the same way. Keep the list of overridden
  templates in the theme's upgrade checklist.
