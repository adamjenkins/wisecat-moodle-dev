# Moodle 5.3: markup, templates, CSS and front end

Read this when plugin or theme CSS, a template override, JavaScript selectors or Behat selectors stop matching on
5.3, when a plugin must look right in Boost's dark colour mode, or when a page of yours renders navigation, modals,
notifications or course-format templates.

This file says what changed and what a plugin does about it. Recipes for themes (child-theme layouts, SCSS for
both versions, React overrides) are in the theme skills: `moodle-theme-development` routes to them. Sources: the
5.3.0 root `UPGRADING.md` (sections `core`, `theme`, `theme_boost`, `core_courseformat`, `editor_tiny`) and the
cited files, read, not run, unless stated.

## Dark colour mode reaches every plugin (MDL-68037)

- Boost can render light or dark. The switch is the experimental site setting `theme_boost/enablecolourmodes`
  (default off), with `theme_boost/defaultcolourmode` (default light). When it is on, `data-bs-theme` is written on
  `<html>` for Boost and every theme with `boost` among its parents (`public/theme/boost/classes/colour_mode.php`,
  `is_boost_theme()`); a child theme cannot opt out by itself. The user's choice is a preference mirrored in the
  cookie `theme_boost_colourmode` (`light|dark|auto`).
- A colour written as a literal keeps its value in both modes. A plugin that sets only a background (or only a
  text colour) produces unreadable pairs in dark mode.
- Fix in plugin CSS: take colours from Bootstrap custom properties, which Bootstrap 5.3 emits on 5.2 too, or from
  utilities; put genuine per-mode differences under the attribute selector.

```css
.local_example-status {
    background-color: var(--bs-tertiary-bg);
    color: var(--bs-body-color);
    border: 1px solid var(--bs-border-color);
}
[data-bs-theme="dark"] .local_example-status {
    /* Only what really differs in dark mode. */
}
```

- Utilities that follow the mode: `bg-body`, `bg-body-secondary`, `bg-body-tertiary`, `text-body`,
  `text-body-secondary`, `text-bg-*`, `border`. Avoid `bg-white`, `bg-light`, `text-dark` for surfaces and text.
- `--mds-*` design-token custom properties exist only on 5.3 (none in 5.2's compiled CSS). A plugin that supports
  5.2 writes a fallback: `color: var(--mds-text-default, var(--bs-body-color));`.
- Icons: Font Awesome mapped icons render as `<i>` and follow the text colour. An icon that is not in the Font
  Awesome map, such as a plugin's own `pix/icon.svg`, renders as `<img>` and keeps the colours baked into the SVG,
  so a dark stroke is invisible in dark mode. Map plugin icons to Font Awesome with
  `<component>_get_fontawesome_icon_map()` where one fits, or draw SVGs that read on both backgrounds.
- Plugin PHP that needs the mode calls `\theme_boost\colour_mode::is_enabled()` and `get_current_mode()` (the
  chosen mode: `light`, `dark` or `auto`, not the resolved one); `render_menu(\renderer_base $output)` prints the
  switcher. All 5.3 only: guard with `class_exists(\theme_boost\colour_mode::class)`. A privacy or cookie notice
  lists the `theme_boost_colourmode` cookie.
- Test: Behat with `--colourmode=dark` (5.3 only) runs the whole suite in dark mode.

## Navigation rendered by React components

| Area | 5.2 | 5.3 | MDL |
|---|---|---|---|
| Primary navigation | `core/moremenu`, `a.nav-link.active`, `.moremenu` wrapper | `core/primarymoremenu` mounting `@moodle/lms/core/nav/PrimaryNav`; with JS: `a.mds-nav-pill`, selected `.mds-nav-pill--selected` + `aria-current="page"`, no `.moremenu`; a server-rendered `core/moremenu_children` fallback stays inside the mount point | MDL-89294 |
| Secondary navigation | `core/moremenu`, `.nav-tabs .nav-link` | `core/secondarymoremenu` mounting `@moodle/lms/core/nav/Nav` (props from `\core\navigation\output\more_menu`); the component renders its own `<nav>` landmark, so do not wrap the template in another `<nav>` | MDL-87830 |
| Edit mode switch | Bootstrap `.form-switch` | `core/editswitch` mounts `@moodle/lms/core/EditModeSwitch`, `mds-switch*` classes; `core_renderer::edit_switch()` passes `elementid` and `reactprops` | MDL-89814 |
| Keyboard handling | `core/menu_navigation` | unchanged | |

- Symptom: CSS on `.primary-navigation .nav-link`, `.moremenu .nav-link`, `.secondary-navigation .nav-link` matches
  nothing; Behat steps that click "More" in the old markup fail; JS that queried `.moremenu` finds nothing.
- Fix: retarget to `.primarynav-navbar`, `.secondarynav-tabbar`, `.mds-nav-pill`, `.mds-nav-pill--selected`
  (`public/theme/boost/scss/moodle/primarynavigation.scss`, `secondarynavigation.scss`), or use Behat's
  navigation steps (`I navigate to "X" in current page administration`) instead of raw selectors. A theme that
  supports both versions needs both selector sets.
- `core/moremenu` and `core/moremenu_children` still ship in 5.3 and `more_menu::export_for_template()` still
  exports their data, so a theme template that includes `{{> core/moremenu}}` renders the legacy menu.

## Other core templates and output that changed

| Change | What to do | MDL |
|---|---|---|
| `core/modal` title is `<h2 class="modal-title fs-5">` (was `<h5>`), looks the same | Start headings inside modal bodies at `<h3>`; update selectors on `h5.modal-title`; custom modal headers follow the same pattern | MDL-75699 |
| `core/notification_base` takes an optional `headinglevel` (1-6); default stays `<h3 class="h6 mb-0">` | Pass it where the page outline needs another level | MDL-88458 |
| `core/search_input_auto` wraps its `role="search"` in a `{{$searchrole}}` block | Empty the block when the input already sits in another search landmark: `{{< core/search_input_auto }}{{$searchrole}}{{/searchrole}}{{/ core/search_input_auto }}` (also on the 5.2 branch) | MDL-88833 |
| `core/user_action_menu_items` split into `user_action_menu_item_{link,header,text,divider}` | Re-diff user-menu overrides | MDL-88938 |
| `core/loginform` moved from Boost to `public/lib/templates/loginform.mustache`, new markup (icons in `login-input-wrapper`, OAuth2 block) | A child override at `templates/core/loginform.mustache` still wins; re-diff its content | MDL-89196 |
| `core/toggle` `dataattributes` | Use `extraattributes`; removal in 6.0 | MDL-86619 |
| Icon map: `core:i/notifications` is `fa-regular fa-bell`, `core:t/message` is `fa-regular fa-message`; new `core:t/collapseall`, `core:t/expandall` | Re-check themes that restyle these | MDL-87836 |
| Grade action bars render `core/navigation_action_bar` and `core/action_bar` | Move overrides to the core templates | MDL-81096 |
| Admin notifications page grouped by severity; campaign, support, Marketplace and feedback banners merged into `core_admin/notification_ctas` | Themes that styled the old banners re-test `/admin/index.php` | MDL-89290 |
| `mod_forum/forum_subscription_action` renders `core/tertiary_navigation_selector` from `viewandmanageselectmenu` | Update overrides of the template | MDL-89890 |

## Course formats and the course index

- **Collapse/expand-all toggle** (MDL-89496): rendered once above the section list by
  `core_courseformat/local/content` from `core_courseformat\output\local\content`, which suppresses the old
  per-section markup by overriding the `core_courseformat/local/content/section/collapsemenu` block. The toggle no
  longer has the id `collapsesections`; target `[data-toggle="toggleall"]`. A format or theme overriding
  `core_courseformat/local/content` updates its copy to render the toggle above the section list.
- **Course index subsections** (MDL-88949): the `li[role="treeitem"]` in `core_courseformat/local/courseindex/cm`
  of an activity with a delegated section carries `aria-owns="courseindexcollapse{{number}}"`,
  `aria-labelledby="courseindexsection{{number}}-title"` and `aria-expanded`; `courseindex/section` omits the role
  and those attributes for delegated sections and gives the title `id="courseindexsection{{number}}-title"`. The
  section JS writes `aria-expanded` on the closest `[role="treeitem"]`, so override both templates or neither.
- **Course index drawer** (MDL-89050): one toggle button (`data-action="toggleallcourseindexsections"`) instead of
  a dropdown; in `theme_boost/drawer` the block `{{$drawerheadercontent}}` is replaced by `{{$drawercontrols}}`. A
  template that fills only the old block shows no control on 5.3, silently.
- **Activity chooser** (MDL-87373): `content_item` takes `bool $disabled = false, ?string $disabledreason = null`;
  disabled items are greyed out with the reason as a tooltip.
- **Linear navigation footer** (MDL-87302, MDL-89406): a format whose static `uses_linear_navigation()` returns
  true (`format_topics`, `format_weeks`) gets previous/next activity links in a sticky footer on activity pages
  unless the site setting `format_<name>/enablelinearnav` is 0; a format with no such setting counts as enabled.
  An activity page that shows its own previous/next controls calls `$PAGE->set_show_navigation_footer(false)`; a
  page that renders its own sticky footer calls `$PAGE->set_has_sticky_footer(true)` so a second is not added.
- **Report pages inside an activity**: a wide `flexible_table` on a page with layout `report` was seen sitting under
  the course index drawer on 5.3; choosing the layout is covered in `moodle-theme-layouts-templates`.

## Boost appearance changes a plugin notices

| Change | Effect on plugins | MDL |
|---|---|---|
| Default typeface is self-hosted Noto Sans (latin, latin-ext, cyrillic subsets; Noto Sans JP only for `:lang(ja)`) instead of the system-ui stack | Layouts measured against the system font shift slightly | MDL-88412, MDL-89024 |
| Default preset `$body-bg` is `$gray-100`, `$card-bg` and `$card-border-color` are custom properties | Plugin cards and panels that assumed a white page look different | (Boost `UPGRADING.md`) |
| Centred layout on large screens; drawers anchor to `.main-inner`, no longer overlay the navbar, close on focus loss | Plugin JS that positioned against the viewport or the drawer re-tests | MDL-88411, MDL-89076 |
| Inline navbar search (`core/search_input_navbar_inline`, always visible) | Behat that clicked the search toggle fails | MDL-87834, MDL-89010 |
| YUI dialogue variables (`$dialogue-base-bg` and ten more) default to custom properties | Presets that override them set a colour dark mode can re-point | MDL-89735 |

## Editor

- TinyMCE picks its skin from `data-bs-theme` at editor setup (no live switch until reload) and copies the
  attribute to the editor container, the sink and the content iframe's `<html>`, so `content_css` can respond.
  Moodle toolbar icons (`svg[data-buttonsource="moodle"]`) are lightened by a CSS filter in dark mode, so draw
  monochrome icons dark. Inside the content iframe the `--bs-*` properties hold Bootstrap's defaults and there are
  no `--mds-*` tokens. MDL-68037.
- The bundled `accordion` and `advlist` TinyMCE plugins are enabled; HTMLPurifier allows `<details>`, `<summary>`
  and the `lower-greek` list style. Post-processing of user HTML should expect them. MDL-88618.

## JavaScript and React

- `theme_boost/bootstrap/*` imports are deprecated (MDL-88766). `import {Tooltip} from 'theme_boost/index';` works
  on 5.2 and 5.3 (until 7.0); `import {Tooltip} from 'bootstrap';` is 5.3 only. Rebuild with `grunt amd`.
- React on pages: `html_writer::react_component()`, `\core\output\react_component_renderable`, AMD `core/import`
  and `core/component` are new in 5.3. The `{{#react}}` Mustache helper exists on 5.2 and 5.3
  (`public/lib/classes/output/renderer_base.php`). Theme overrides of React components are 5.3 only
  (`moodle-theme-renderers-output`).
- `window.jQuery` is still attached for Bootstrap's jQuery plugin interface (`$(el).tooltip()`), until 6.0
  (MDL-84465, `public/lib/amd/src/first.js`).

## CSS linting

5.3's stylelint configuration rejects some valid modern CSS in plugin `styles.css` (`container-type`, `@container`,
`clamp()` in `font-size`) through `csstree/validator`, which fails `moodle-plugin-ci grunt`; the rule and its
per-line workaround are in `moodle-theme-scss`.
