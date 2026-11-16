# Moodle 5.3: renderer changes, React-rendered regions and component overrides

Read this when the theme runs on Moodle 5.3 and touches the primary or secondary navigation, the edit-mode switch
or the Timeline block, overrides a `core_renderer` method that changed in 5.3, or considers overriding a React
component.

This file says only what is specific to 5.3 against the 5.2 baseline. Status of the claims: everything here was
read in the 5.3.0 source and the official 5.3 documentation. **No React component override was built, compiled or
loaded in a browser for this skill.** Treat sections 3 to 6 as a map of the source, not as a tested recipe.

## 1. Renderer and PHP changes

| Change in 5.3 | Effect on a theme | Action |
|---|---|---|
| `theme_boost\output\core_renderer::render_login()` removed; `core/loginform` moved from Boost's templates to core | `parent::render_login()` now reaches core's method, which adds no `logourl` or `sitename` to the context | Compute what the login template needs in the theme's own override; re-diff a `core/loginform` template override |
| Boost's renderer gained `search_box()` and `colour_mode_menu()` | A child whose renderer does not extend Boost's has no colour-mode switcher: `{{# output.colour_mode_menu }}` renders nothing | Extend `\theme_boost\output\core_renderer`, or call `\theme_boost\colour_mode::render_menu($this)` from the theme's own method |
| `core_renderer::edit_switch()` passes `elementid` and `reactprops` to `core/editswitch` | An override that builds its own context loses the React switch | Call the parent |
| `user_*()` functions of `user/lib.php` moved to `\core\user` (`user_can_view_profile()` became `\core\user::can_view_profile()`) | Renderer bodies copied from 5.2 (`context_header()`) emit deprecation notices | Wrap the parent instead of copying; the new methods do not exist on 5.2 |
| `block_timeline\output\main` and `block_timeline\output\renderer` removed with no stub | A theme class extending the renderer is a fatal error when requested | Delete the override and any `block_timeline` templates |
| `\core\output\react_component_renderable` and `renderer_base::render_react_component()` added | `$renderer->render()` turns such a widget into a mount point | Nothing, unless the theme overrode `render()` |
| New hooks `\core\hook\output\before_requirejs_config` and `before_import_map_config` | A theme can add ESM import specifiers | Register them; harmless on 5.2 |
| Boost registers three hook callbacks (`before_requirejs_config`, `before_html_attributes`, `before_standard_head_html_generation`) | They run for any theme with `boost` among its parents: when the administrator enables colour modes, a child gets `data-bs-theme` on `<html>` and cannot opt out with a setting of its own | Make the child's colours work in dark mode (`moodle-theme-scss`) |
| Icon map: `core:t/collapseall`, `core:t/expandall` added; `core:i/notifications`, `core:t/message` became `fa-regular` | An icon system subclass that sets those keys may now disagree with core | Re-read the subclass against the 5.3 map |
| The Classic theme was removed from core | `\theme_classic\output\icon_system_fontawesome` and Classic's renderers are gone | A theme that extended them must own the code |

Sources: `public/theme/boost/UPGRADING.md`, `public/lib/UPGRADING.md`, `public/blocks/timeline/UPGRADING.md`,
`public/theme/boost/classes/output/core_renderer.php`, `public/theme/boost/db/hooks.php`, 5.3.0.

Feature tests that work on both versions (prefer them to version numbers; `$CFG->branch` is stale while an
upgrade is running):

```php
$hascolourmodes = class_exists(\theme_boost\colour_mode::class);                 // 5.3 and later.
$hasreactnav = class_exists(\core\output\react_component_renderable::class);     // 5.3 and later.
```

## 2. Which regions React draws, and what still reaches them

Core 5.3.0 has four React mount points.

| Region | Component | Mounted from | Template override | SCSS | Component override |
|---|---|---|---|---|---|
| Primary navigation | `@moodle/lms/core/nav/PrimaryNav` (a re-export of `nav/Nav`) | `core/primarymoremenu`, included by Boost's navbar | Yes | Yes | By hand only; not offered by the wizard |
| Secondary navigation | `@moodle/lms/core/nav/Nav` | `core/secondarymoremenu`, included by Boost's layouts | Yes | Yes | Yes; marked risky |
| Edit-mode switch | `@moodle/lms/core/EditModeSwitch` | `core/editswitch`, rendered by `core_renderer::edit_switch()` | Yes, or a renderer override | Yes | Yes; marked risky |
| Timeline block | `@moodle/lms/block_timeline/Timeline` and its parts | PHP only: `html_writer::react_component()` in the block | No: the block has no templates any more | Yes | Yes; two of its views refuse eject |

Everything else (user menu, language menu, drawers, course index, breadcrumb, footer, tertiary navigation,
activity chooser) is still Mustache and AMD.

How the three template-mounted regions behave:

- The template prints a `{{#react}}` block naming the component and passing a JSON string built in PHP
  (`reactprops`), and inside the mount point a complete server-rendered fallback. React replaces the fallback on
  mount; without JavaScript the fallback is the page.
- The JSON is built by protected methods (`\core\navigation\output\primary::export_react_props()`,
  `\core\navigation\output\more_menu::export_react_props()`), so a subclass can add to it.
- The pre-5.3 path still ships: `core/moremenu` (template and AMD module) is unchanged and its data is still
  exported. A theme template that still includes `{{> core/moremenu}}` renders the legacy menu on 5.3. No core
  template includes it any more. The 5.3 upgrade notes say it was replaced in Boost's navbar and do not deprecate
  it (`grep` of `public/lib/UPGRADING.md` and `public/theme/boost/UPGRADING.md`, 5.3.0).

### Styling without touching React

The component CSS is in the theme stylesheet, not in the JavaScript: Boost's default preset imports the design
system's component styles. So ordinary theme SCSS applies.

```scss
// Post-SCSS: restyle the React navigation.
:root {
    --mds-bg-nav-pill-selected: #{$primary};
}
.primarynav-navbar .mds-nav-pill--selected .mds-nav-pill__label {
    color: $white;
}
```

- Navigation items: `.mds-nav-pill`, `.mds-nav-pill--selected`, `.mds-nav-pill__label`,
  `.mds-nav-pill__indicator`; selected items carry `aria-current="page"`. Mount points:
  `.primary-navigation .navigation.primarynav-navbar`, `.secondary-navigation .navigation.secondarynav-tabbar`.
- Edit switch: `.editmode-switch-form`, `.mds-switch`, `.mds-switch-track`, `.mds-switch-thumb`,
  `.mds-switch-label`.
- Timeline: `div.block-timeline[data-region="timeline"]`, `.timeline-event-list-item`, `.timeline-name`,
  `.timeline-action-button`.
- Old selectors (`.primary-navigation .nav-link`, `.moremenu .nav-link.active`,
  `.secondary-navigation .nav-tabs .nav-link`) match only the no-JavaScript fallback.
- React adds `primarynav-measured` / `secondarynav-measured` to the mount point once the overflow split has
  settled, and Boost keeps the bar at `opacity: 0` under `.jsenabled` until then. A theme that keeps the
  mount-point class but mounts a component that never adds the measured class gets an invisible navigation bar.
- The secondary navigation component renders its own `<nav>` landmark. Do not wrap `core/secondarymoremenu` in
  another `<nav>`.
- A preset that does not import the design system (Boost's `plain` preset) leaves these components unstyled.

### Changing what is mounted with a template override

Copy `core/primarymoremenu.mustache` into the theme's `templates/core/`, keep the `{{#reactprops}}` guard, the
JSON block and the fallback, and change only what is needed: an extra class on the mount point, or a different
component name. Template overrides fall back through parent themes; component overrides do not. The edit-switch
fallback is hand-mirrored from the design system's markup, and core's own comment says the template and the
component must change together; a theme's copy of that template inherits the duty.

## 3. How a component override is found

Read in `public/lib/classes/output/requirements/import_map.php` and
`public/lib/classes/route/controller/esm_controller.php`, 5.3.0. Not run.

- Every page has an import map. Two entries are themable: `@moodle/lms/` and `@moodlehq/design-system`. For a
  themable entry the bare key points at the current theme's URL, and one extra key exists per installed theme plus
  `theme-original`:

  ```text
  "@moodle/lms/"                 -> .../@moodle/lms/theme-mytheme/
  "@moodle/lms/theme-original/"  -> .../@moodle/lms/theme-original/
  "@moodle/lms/theme-boost/"     -> .../@moodle/lms/theme-boost/
  "@moodle/lms/theme-mytheme/"   -> .../@moodle/lms/theme-mytheme/
  ```

- For `@moodle/lms/theme-<T>/<component>/<module>` the server tries exactly two files:
  1. `<theme T>/js/esm/build/overrides/<component>/<module>.js` (skipped when `T` is `original`);
  2. `<component directory>/js/esm/build/<module>.js`.
- **No parent theme is consulted.** A child of a theme that overrides a component gets core's component. The
  official page says the same.
- Files are served under the JavaScript revision with long cache headers; with JavaScript caching off the server
  prefers `<module>.dev.js`. New build files need a cache purge to be seen.

## 4. Writing an override

| | Location |
|---|---|
| Source | `public/theme/<name>/js/esm/src/overrides/<component>/<module>.tsx` (core's component name is `core`: `overrides/core/EditModeSwitch.tsx`) |
| Built | `public/theme/<name>/js/esm/build/overrides/<component>/<module>.js`, plus `.dev.js` and `.dev.js.map` |

Wrap rather than eject when adding around a component (from the official page's pattern; not built here):

```tsx
// public/theme/mytheme/js/esm/src/overrides/core/EditModeSwitch.tsx
import type {ComponentProps} from 'react';
import Original from '@moodle/lms/theme-original/core/EditModeSwitch';

type Props = ComponentProps<typeof Original>;

export default function EditModeSwitch(props: Props) {
    return <span className="mytheme-editswitch"><Original {...props} /></span>;
}
```

Rules:

- Import the component being overridden through `theme-original` (or `theme-<parent>`), never through the bare
  `@moodle/lms/` alias: that is the override itself, a circular import.
- Keep the export shape of the original (default export here). Other modules import it by that shape, and the
  page mounts a module's default export.
- Use `theme-original` only for the one module being wrapped. It is a different URL from the bare alias, so the
  browser loads a second instance of anything imported that way, with its own state.
- A child theme that wants its parent's override re-exports it (derived from the documented parent-import alias;
  not run):

  ```tsx
  // public/theme/child/js/esm/src/overrides/core/nav/Nav.tsx
  export {default} from '@moodle/lms/theme-parent/core/nav/Nav';
  export * from '@moodle/lms/theme-parent/core/nav/Nav';
  ```

- Overriding `core/nav/Nav` also changes the primary navigation, because `PrimaryNav` imports `./Nav` relatively
  and the browser resolves that under the theme prefix. Overriding only `core/nav/PrimaryNav` leaves the secondary
  bar alone. Derived from the built files; not run.
- The wizard: `npm run swizzle` from the Moodle root or from inside `public/theme/<name>`. It is interactive only
  and offers `wrap` (a scaffold that renders the original) or `eject` (a full copy). Each component declares a
  level for each action in its `js/esm/src/swizzle.json`: `safe`, `risky` (asks for confirmation) or `prohibited`
  (refused). The levels gate the wizard only; nothing at build or run time checks them. Core 5.3.0 marks
  `nav/Nav` and `EditModeSwitch` risky for both actions.
- An ejected file stops receiving core fixes at once. The navigation component is several hundred lines of
  overflow and accessibility logic.

For heavy changes, the route a large published Boost child took is not `overrides/` at all: it ships its own
component under its own name (`@moodle/lms/theme_<name>/nav/Nav`), selects it from a template override of
`core/primarymoremenu`, extends the PHP exporter to add data, and keeps an untouched copy of the core source file
next to its modified copy for the next comparison. That route works in child themes, because it is found by
template lookup rather than by the override path.

## 5. Building

- There is no supported build outside a full Moodle checkout. The task needs the root `Gruntfile.js`, the
  `.esbuild/` and `.grunt/` directories and core's `node_modules`, and the wizard needs the theme under
  `public/theme/`. In practice: place the theme inside a 5.3 tree, run `npx grunt esm` (alias `grunt react`), and
  commit the theme's `js/esm/build/` with the source.
- The build is whole-tree: it deletes every `js/esm/build` directory under the Moodle root and rebuilds all of
  them, wherever it is started from. Review `git status` in the theme's repository only, and expect unrelated
  changes in a shared checkout.
- Each source file becomes one output file and import lines survive as written; nothing is bundled and no type
  checking happens.
- Commit both the production file and the `.dev.js` pair. A site with JavaScript caching off is served the
  `.dev.js` file, so updating only one of the two gives developers and production different code.
- `moodle-plugin-ci` (4.5.11) does not build or check `js/esm`: its default Grunt tasks are `amd`, `yui`,
  `gherkinlint` and `stylelint`. A stale or missing ESM build stays green in CI. Whether
  `moodle-plugin-ci grunt -t esm` detects a stale build was derived from its code and not run.
- The documentation on the main branch describes a later toolchain (other task and file names). Follow the 5.3
  page for 5.3: https://moodledev.io/docs/5.3/guides/javascript/react/theming . That page's "Since 5.2" tag is
  wrong: the 5.2 import map has no theme handling (read in the 5.2 source).

## 6. What breaks on the next core update

| The theme has | It breaks when |
|---|---|
| CSS on `.mds-*` classes | The design system renames classes or tokens |
| A template override of a mount-point template | Core changes the props, the fallback markup or the component name |
| A PHP exporter subclass | The JSON shape the component expects changes |
| A wrap | The original's props or export shape change |
| An eject or an own copy of a component | At once: it no longer receives core fixes |
| Any Mustache override of a region | That region moves to React in a later release and the template becomes a dead file |

Record every copied or wrapped core file in the theme's upgrade checklist, with the core path to compare, and keep
the upstream authors' copyright lines on copied code.
