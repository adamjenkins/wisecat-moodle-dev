# Moodle 5.2: what the baseline has and lacks for renderers and output

Read this when the theme must run on Moodle 5.2, or when code written against 5.3 is being made to work on 5.2.

5.2 is the baseline, so the body of `SKILL.md` already holds on it. This file lists the points where a developer
who knows 5.3 would otherwise be caught out. Everything here was read in the 5.2 source (5.2.2+); nothing was run
on 5.2.

## Renderers

| Point | On 5.2 |
|---|---|
| Renderer factories and class-name lookup | Identical files to 5.3 (`public/lib/classes/output/renderer_factory/`) |
| `renderer_base::render()` | Same dispatch, without the React renderable step |
| Boost's `core_renderer` methods | `edit_button`, `navbar`, `context_header`, `firstview_fakeblocks`, `render_login`. No `search_box`, no `colour_mode_menu` |
| `render_login()` | Boost's override exists and adds context (`logourl`, `sitename` and more) for Boost's own `core/loginform` template |
| `context_header()` body | Calls `user_can_view_profile()`; `\core\user::can_view_profile()` does not exist |
| `core_renderer` public method signatures | Same as 5.3 for every method that exists in both |
| `block_timeline\output\renderer` | Exists, with Mustache templates; a theme may override both |

A theme method called from a template through `{{# output.method }}` renders nothing where the method does not
exist, so a template shared by 5.2 and 5.3 can call 5.3-only renderer methods safely. PHP code cannot: guard it
with `method_exists()` or `class_exists()`.

## Hooks

- Boost has no `db/hooks.php` on 5.2 and registers no hook callbacks. The pattern of a theme registering hooks is
  the same; only Boost's own example is missing.
- All `\core\hook\output\*` hooks listed in the skill exist except `before_requirejs_config` and
  `before_import_map_config`. Entries for those two in `db/hooks.php` are ignored on 5.2.
- `\core\hook\navigation\primary_extend` and `secondary_extend` exist.

## Icons and images

- The icon map code (`get_icon_name_map()` and everything after it) is identical to 5.3. The core map lacks
  `core:t/collapseall` and `core:t/expandall`, and `core:i/notifications` and `core:t/message` are solid, not
  regular.
- Font Awesome's SCSS is under `public/theme/boost/scss/fontawesome/` and its webfonts under `public/lib/fonts/`.
  The Font Awesome version variable in that SCSS reports an older version than the files shipped; do not use it
  to decide which glyphs exist.
- Image resolution order is the same as 5.3.
- There is no dark colour mode, so no inversion of image icons and no dark twin for activity icon filters.
- The Classic theme is still in core and ships the only core example of an icon system subclass
  (`public/theme/classic/classes/output/icon_system_fontawesome.php`).

## Navigation and headers

- Primary and secondary navigation are the `core/moremenu` template with the `core/moremenu` AMD module. The
  markup is `.moremenu` with `a.nav-link` items and `.active` on the current one. The templates
  `core/primarymoremenu` and `core/secondarymoremenu` do not exist; including one is a fatal error, not a silent
  gap.
- `\core\navigation\output\primary` has no `export_react_props()` or related methods. A subclass written for both
  versions must not call them on 5.2 through `parent::`.
- `$THEME->removedprimarynavitems`, `$THEME->activityheaderconfig` and the layout options for the activity
  header, `activityinfoinheader` included, behave as on 5.3.
- The edit switch is a Bootstrap `.form-switch` rendered wholly by `core/editswitch`; `edit_switch()` passes no
  `reactprops`.

## React

The plumbing exists (an import map, the `{{#react}}` Mustache helper) but no core template uses it, and the import
map has no theme handling: a file placed in `js/esm/build/overrides/` is never looked at. Component overrides
start at 5.3. The official theming page is tagged "Since 5.2"; the 5.2 code does not contain the feature.
