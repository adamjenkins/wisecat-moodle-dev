# Icons and images: the icon map, pix overrides, activity icons

Read this when a theme changes an icon or an image and the short table in `SKILL.md` did not settle it: how the
icon map is built and cached, the order image files are resolved in, activity icons, deprecated icons, the favicon,
and icons in dark mode.

Read in the Moodle 5.3.0 source unless a line says otherwise; nothing in this file was run. Where 5.2 differs it
is tagged. No pix override, icon map callback or icon system subclass was built for this skill.

## Two icon systems

`$THEME->iconsystem` names a class extending `\core\output\icon_system`. The theme's own value is used if it is a
loadable subclass; otherwise the first parent that sets a valid one; otherwise `icon_system::STANDARD`
(`public/lib/classes/output/theme_config.php`, `get_icon_system()`). An invalid class name is skipped without a
message. Boost sets `\core\output\icon_system::FONTAWESOME`, so a child of Boost inherits Font Awesome and need
not restate the key.

| System | An icon in the map | An icon not in the map |
|---|---|---|
| `STANDARD` | `<img>` | `<img>` |
| `FONTAWESOME` | `<i class="icon fa ... fa-fw">` | `<img class="icon">` |

Template: `public/lib/templates/pix_icon_fontawesome.mustache`. The consequence runs through everything below:
for a mapped icon the image file is never requested, and for an unmapped icon no CSS colour applies.

## How the Font Awesome map is built

`icon_system_fontawesome::get_icon_name_map()` (`public/lib/classes/output/icon_system_fontawesome.php`; the
method is identical in 5.2, compared with `diff`):

1. Start from `get_core_icon_map()`: `'core:t/edit' => 'fa-pen'` and so on. Keys are `<component>:<pix path>`.
   The component `theme` means a file in a theme's own `pix/` (`theme:fp/add_file`).
2. Call `<component>_get_fontawesome_icon_map()` from the `lib.php` of every installed plugin, themes included,
   and merge each result with `+=`. With `+=` the existing key wins, so a callback can add keys and can never
   change one that core or an earlier plugin set.
3. Add a family: a value with none of the family classes (`fa-solid`, `fa-regular`, `fa-brands`, ...) gets the
   prefix `fa `. To choose another family write it in the value: `'fa-regular fa-envelope'`.
4. Append ` deprecated deprecated-<key>` to every key returned by `get_deprecated_icons()`.
5. Store the result in the application cache `core/fontawesomeiconmapping` under a key made from the icon system's
   class name, so two themes with different subclasses keep separate maps.

JavaScript uses the same map: `core/icon_system_fontawesome` fetches it with a web service for the current theme
and keeps it in the browser's localStorage, so templates rendered in the browser honour a theme's subclass too.

### Adding mappings for the theme's own icons

```php
// lib.php
function theme_mytheme_get_fontawesome_icon_map() {
    return [
        'theme_mytheme:i/banner' => 'fa-regular fa-image',
    ];
}
```

Rules:

- **Ship `pix/i/banner.svg` as well.** Core's PHPUnit test `icon_system_fontawesome_test::test_svg_fallback`
  asserts that `<component directory>/pix/<name>.svg` exists for every key in the map. A theme that maps a key
  without the file makes core's own test suite fail on any site where the theme is installed, active or not.
  Source: `public/lib/tests/output/icon_system_fontawesome_test.php`, 5.3.0. For keys with the bare component
  `theme` the test looks in Boost's `pix/`, so use `theme_mytheme:` keys for the theme's own icons.
- **Only use keys in the theme's own namespace.** The callback runs for every installed theme whether it is in
  use or not, so its keys land in every theme's map. A `core:` key is ignored anyway (step 2).
- Use the icon with the same component: `$OUTPUT->pix_icon('i/banner', $alt, 'theme_mytheme')` or
  `{{#pix}} i/banner, theme_mytheme, {{#str}} banner, theme_mytheme {{/str}} {{/pix}}`.
- A map that depends on stored data (icons chosen in a setting) must clear the server cache when the data changes:
  `\cache::make('core', 'fontawesomeiconmapping')->purge();`. `icon_system::reset_caches()` does not do this: it
  only drops the in-memory instance. The browser's copy lasts until the next JavaScript revision change (a cache
  purge), so icons drawn by JavaScript can lag behind.

### Changing a core or plugin glyph

Subclass the icon system and set `$THEME->iconsystem` to the subclass, as shown in `SKILL.md`. The Classic theme
shipped with 5.2 is the model (`public/theme/classic/classes/output/icon_system_fontawesome.php`, 5.2; Classic is
not in 5.3). Notes:

- Override `get_core_icon_map()`, call the parent and change entries. To make an icon fall back to its image
  file, `unset()` its key.
- Do not strip the ` deprecated` classes in a subclass: Behat's deprecated-icon check relies on them.
- **5.3+:** the core map gained `core:t/collapseall` and `core:t/expandall`, and `core:i/notifications` and
  `core:t/message` moved to the `fa-regular` family. A subclass that sets those keys should be re-read against the
  5.3 file.
- Font Awesome Free 6.7.2 is shipped in both versions, but it moved. **5.2 only:** the SCSS is in
  `public/theme/boost/scss/fontawesome/` and the webfonts in `public/lib/fonts/`. **5.3+:** both are under
  `lib/bundles/fontawesome/` at the repository root, outside `public/`. Do not read those files by path from PHP
  to list the available glyphs without handling both locations.

## Replacing an image file: resolution order

`theme_config::resolve_image_location($image, $component)` returns the first file found. For each directory it
tries `.svg` (when the browser supports SVG), then `.png`, `.gif`, `.jpg`, `.jpeg`. The method is the same in 5.2.

| Component asked for | Directories searched, in order |
|---|---|
| `core` / `moodle` / empty | theme `pix_core/`; each parent's `pix_core/`, farthest parent first; `$CFG->dataroot/pix/`; core `pix/` |
| `theme` | theme `pix/`; each parent's `pix/`, farthest parent first |
| a plugin, e.g. `mod_forum` | theme `pix_plugins/mod/forum/`; each parent's `pix_plugins/mod/forum/`, farthest first; `$CFG->dataroot/pix_plugins/mod/forum/`; the plugin's own `pix/` |

- The parent walk is reversed on purpose in core (`array_reverse($this->parent_configs)`, comment "Base first, the
  immediate parent last"). With `parents = ['middle', 'boost']`, Boost's file beats `middle`'s. Templates and
  renderers go the other way (nearest parent first). Only a file in the theme itself is certain to win.
- The path under `pix_core/` mirrors core's `pix/`: `pix_core/i/course.svg` replaces `pix/i/course.svg`. The path
  under `pix_plugins/` is `<plugin type>/<plugin name>/<path>`: `pix_plugins/mod/forum/monologo.svg`.
- For a `mod` plugin, asking for `icon` or `monologo` looks for `monologo` first and then `icon`, in every
  directory, and asking for `icon` raises a developer debugging notice. To replace an activity's icon ship
  `pix_plugins/mod/<name>/monologo.svg`.
- The component `theme` always means the theme in use. `image_url('logo', 'theme')` in a parent theme's code
  finds a child's `pix/logo.*` first; `image_url('logo', 'theme_mytheme')` is treated as a plugin request and
  finds `theme/mytheme/pix/logo.*` after any `pix_plugins/theme/mytheme/` override.
- `favicon` is a special case: `resolve_image_location('favicon', 'theme')` returns
  `<current theme>/pix/favicon.ico` without checking that it exists and without looking at parents. A child of
  Boost with no `pix/favicon.ico` serves a broken favicon unless the site's favicon admin setting is set, which
  `core_renderer::favicon()` prefers. Ship the file. Read in `theme_config.php`, `core_renderer.php` and
  `public/theme/image.php` (an unreadable file is answered "not found"), 5.3.0 and 5.2; not run.
- Images are served by `public/theme/image.php` from a per-theme cache keyed by the theme revision. A request for
  a missing image writes an `.error` marker, and later requests return "not found" from the marker until the
  theme caches are purged. After adding or replacing an image file, purge.
- A replacement in `pix_core/` shows only where the icon is drawn as an image. Check the Font Awesome map first:
  if `core:<path>` is a key, the file is never requested. Most of core's `t/`, `i/` and `e/` icons are mapped.

## Activity icons

- A module declares a purpose through `FEATURE_MOD_PURPOSE`: `administration`, `assessment`, `collaboration`,
  `communication`, `content`, `interactivecontent` or `other` (`public/lib/moodlelib.php`).
- Markup: `<div class="activity-icon activityiconcontainer <purpose> [isbranded]"><img class="activityicon icon
  [nofilter]" ...></div>` (`public/course/templates/activity_icon.mustache`).
- The colour is an SVG `feColorMatrix` filter generated from six SCSS variables, not a CSS colour:
  `$activity-icon-administration-bg`, `-assessment-`, `-collaboration-`, `-communication-`, `-content-`,
  `-interactivecontent-` (`public/theme/boost/scss/moodle/variables.scss` and `icons.scss`; the variables exist in
  5.2 too). `other` has no entry and stays uncoloured. Set them in pre-SCSS:

  ```scss
  $activity-icon-assessment-bg: #b3261e;
  ```

- `color:` or `fill:` on `.activityicon` does nothing. To restyle outside the variables, override `filter` at the
  same specificity as Boost's rule (`.activityiconcontainer.<purpose>:not(.isbranded) .activityicon:not(.nofilter)`).
  **5.3+:** dark mode re-applies the filter with a tinted colour, so the override needs a dark twin.
- Only a monologo is recoloured. A module whose `<mod>_is_branded()` callback returns true gets `isbranded` and
  keeps its own colours; an icon served without the filter flag has the class `nofilter`.

## Icons in dark mode

**5.3+** (Boost's colour modes do not exist in 5.2):

- Glyph icons are text and follow `color`. Nothing to do.
- Image icons are inverted only when their URL contains `/t/`, `/e/`, `/a/`, `/i/groupn`, `/i/groups` or
  `/i/groupv` (`public/theme/boost/scss/moodle/icons.scss`). Every other `<img class="icon">` is left as drawn.
- An SVG shown through `<img>` cannot take a colour from the page: `currentColor` inside the file does not follow
  the page's text colour. A monochrome SVG with a near-black stroke is close to invisible on Boost's dark
  background. This applies to the icon the plugins overview page shows for each plugin (`pix/icon.*`, or
  `pix/monologo.*` for an activity module): it is unmapped, so it is an `<img>`.
- Options for a theme's own image icons: map them to a glyph; draw them in a mid-tone that reads on both
  backgrounds; or add a rule of the theme's own:

  ```scss
  [data-bs-theme="dark"] img.icon[src*="theme_mytheme"] {
      filter: invert(1);
  }
  ```

  The selector matches on the component name, which is in both forms of the image URL: the path form
  `theme/image.php/<theme in use>/theme_mytheme/<revision>/<image>` and the query form
  `theme/image.php?theme=...&component=theme_mytheme&image=...` that is used when slash arguments are off or theme
  designer mode is on. Do not match on `/theme_mytheme/` with slashes, which misses the query form. It applies to
  icons requested with the component `theme_mytheme`; an icon requested with the component `theme` has only the
  current theme's name in its URL. Read in `theme_config::image_url()`, 5.3.0; not run. Inverting changes hue, so
  use it only for monochrome icons.

## Deprecated icons

- Core lists deprecated keys in `icon_system_fontawesome::get_deprecated_icons()`; a plugin or theme adds its own
  with a `<component>_get_deprecated_icons()` callback in `lib.php`.
- A deprecated icon still renders, with the extra classes `deprecated deprecated-<key>` on the glyph or the image.
- Behat fails a step when the page contains `.icon.deprecated`, unless the site was initialised with
  `--no-icon-deprecations` (`public/lib/behat/classes/behat_session_trait.php`). A theme template or renderer that
  prints a deprecated core icon therefore fails Behat on every page it appears on. Replace the icon; the policy
  page lists the replacements: https://moodledev.io/general/development/policies/deprecation/icon-deprecation

## `{{#pix}}`, `pix_icon()` and `image_url()`

| Call | Output | Use for |
|---|---|---|
| `$OUTPUT->pix_icon($pix, $alt, $component)` / `{{#pix}} pix, component, alt {{/pix}}` | Through the icon system: glyph or `<img class="icon">` | Icons at icon size |
| `$OUTPUT->image_url($name, $component)` | A URL only (`theme/image.php/...`), resolved as in the table above | Logos, illustrations, backgrounds in a plain `<img>` or inline style |
| `[[pix:component|name]]` in SCSS | The same URL, substituted when the CSS is built | Background images in styles (`moodle-theme-scss`) |

- `{{#pix}}` always emits the `icon` class, and Boost sizes `.icon` to icon dimensions. A full-size picture
  printed through it is shrunk. Pass the URL from PHP in the template context instead.
- Decorative icons take an empty alt text; an icon that is the only content of a link or button needs a real one.
- Do not write tag syntax such as `{{#pix}}` inside a `{{! }}` template comment when documenting it: the comment
  ends at the first `}}` and the rest is printed.
