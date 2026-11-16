# Fonts and images in theme SCSS

Read this when shipping a web font with a theme, replacing Boost's typeface, or using the `[[font:]]` and `[[pix:]]`
placeholders beyond the one-line form: lookup order, allowed file names, caching, licences.

Evidence: read in `public/lib/classes/output/theme_config.php` (`post_process()`, `resolve_font_location()`,
`resolve_image_location()`) and `public/theme/font.php`, 5.3.0, with the 5.2 differences read in the 5.2 source. No
custom font, pix override or preset was built and loaded for this file: the recipes are "read, not run".

## The placeholders

`post_process()` replaces two placeholders in the compiled CSS, in every stylesheet that passes through the theme
(the theme's SCSS, plugin `styles.css`, the editor sheet):

| Placeholder | Becomes | Component part |
|---|---|---|
| `[[pix:<component>\|<path>]]` | a root-relative `theme/image.php` URL | optional; `[a-z0-9_]+`. Omitted or `core` / `moodle` means core's `pix/` |
| `[[font:<component>\|<file>]]` | a root-relative `theme/font.php` URL | same |

```scss
.mytheme-hero {
    background-image: url([[pix:theme|hero]]);                // pix/hero.svg (or .png, .gif, .jpg, .jpeg) in the theme.
}

.mytheme-toggle {
    background-image: url([[pix:t/collapsed]]);               // Core icon pix/t/collapsed.
}

.mytheme-forumicon {
    background-image: url([[pix:mod_forum|monologo]]);        // A plugin's pix file.
}
```

- Give the image name without an extension. SVG is preferred when the browser accepts it, then png, gif, jpg, jpeg.
- There is no `[[setting:name]]` in core. The only other hook is the theme's own `$THEME->csspostprocess` function,
  which receives the CSS after these two replacements and can do its own `str_replace`. Prefer SCSS variables from the
  pre-SCSS callback.
- Never write a path to `lib/fonts/`, `lib/bundles/` or another theme's directory in a `url()`. Core font files moved
  between 5.2 (`public/lib/fonts/`) and 5.3 (`lib/bundles/fontawesome/webfonts/`); `[[font:core|fa-solid-900.woff2]]`
  works on both.
- Stylelint rejects `data:` URLs in theme SCSS (`function-url-scheme-disallowed-list`), so small images go in `pix/`
  too.

## Lookup order

First hit wins. "Parents, base first" means that with `$THEME->parents = ['mid', 'boost']`, Boost is searched before
`mid`. Only the theme itself always wins.

**Images** (`resolve_image_location()`)

| Component | Order |
|---|---|
| `core` (or omitted) | `<theme>/pix_core/`, parents' `pix_core/` (base first), `<dataroot>/pix/`, core `pix/` |
| `theme` | `<theme>/pix/`, parents' `pix/` (base first) |
| `<type>_<plugin>` | `<theme>/pix_plugins/<type>/<plugin>/`, parents' same (base first), `<dataroot>/pix_plugins/<type>/<plugin>/`, the plugin's own `pix/` |

**Fonts** (`resolve_font_location()`)

| Component | Order |
|---|---|
| `core` (or omitted) | `<theme>/fonts_core/`, parents' `fonts_core/` (base first), `<dataroot>/fonts/`, then core's Font Awesome webfonts |
| `theme` | `<theme>/fonts/`, parents' `fonts/` (base first) |
| `<type>_<plugin>` | `<theme>/fonts_plugins/<type>/<plugin>/`, parents' same (base first), `<dataroot>/fonts_plugins/<type>/<plugin>/`, the plugin's own `fonts/` |

Consequences:

- `[[pix:theme|x]]` and `[[font:theme|x]]` written in Boost's SCSS resolve in the child first. A child file
  `fonts/noto-sans/noto-sans-normal-latin.woff2` replaces Boost's file of that name (5.3). Do not reuse Boost's file
  names for a different font by accident.
- An image override in `pix_core/` changes background images written with `[[pix:...]]`. Whether it changes an icon
  drawn by the icon system is a different question (mapped icons are font glyphs); see `moodle-theme-renderers-output`.

## What `font.php` accepts

- Extensions: `.woff2`, `.woff`, `.ttf`, `.otf`, `.eot`, `.svg`. Ship `.woff2`.
- File names: letters, digits, `_` and `-` only, case-insensitive, then the extension. No spaces, no extra dots.
- **5.3+:** the name may include subdirectories (`my-sans/regular.woff2`). On 5.2 the pattern has no `/`, so the same
  URL is answered 404. A theme that supports 5.2 keeps every font file directly in `fonts/`.
- Caching: served with a long-lived immutable cache header when the URL carries the current theme revision, otherwise
  uncached. A missing font is remembered, so later requests 404 quickly: after adding a file that was requested while
  missing, purge the theme cache.
- The moodledev.io fonts page for 5.3 is out of date on three points: it says core fonts are in `/lib/fonts/`, that
  subdirectories are not allowed, and it does not list `.woff2`. The code above is the authority.

## Shipping a font

Works on 5.2 and 5.3 as written (flat `fonts/` directory). Not run.

```scss
// scss/mytheme/pre.scss
$font-family-sans-serif: "My Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
$mds-font-family-base: "My Sans";      // 5.3: design system components and the :lang(ja) stack. Unused on 5.2.
```

```scss
// scss/mytheme/post.scss
@font-face {
    font-family: "My Sans";
    font-style: normal;
    font-weight: 100 900;
    font-display: swap;
    src: url('[[font:theme|mysans-latin.woff2]]') format('woff2');
}
```

Files to ship with it:

- `fonts/mysans-latin.woff2` (one file per subset or style; a variable font keeps the count low).
- The font's licence text beside it (for an OFL font, `fonts/OFL.txt`) and a `fonts/readme_moodle.txt` saying where
  the files came from, which version, and how to refresh them.
- An entry in the theme's `thirdpartylibs.xml`, modelled on Boost's 5.3 file:

```xml
<?xml version="1.0"?>
<libraries>
  <library>
    <location>fonts</location>
    <name>My Sans</name>
    <description>Typeface used by the theme.</description>
    <version>1.000</version>
    <license>OFL</license>
    <licenseversion>1.1</licenseversion>
    <repository>https://example.com/my-sans</repository>
    <copyrights>
      <copyright>2026 The My Sans Project Authors</copyright>
    </copyrights>
  </library>
</libraries>
```

  `thirdpartylibs.xml` also keeps the listed location out of the code checkers. Use a font whose licence allows
  redistribution inside a GPL plugin; the Plugins directory rules are in `moodle-theme-testing-release`.

Things to know:

- **5.3+:** Boost self-hosts Noto Sans (eight variable-font subsets, weights 100 to 900, normal and italic) and Noto
  Sans JP (120 files) under `public/theme/boost/fonts/`, declared in `scss/moodle/fonts.scss` with
  `font-display: swap`. The `@font-face` rules stay in the compiled CSS when a theme changes the typeface; a browser
  downloads a font file only when a rendered character needs it.
- **5.3+:** Japanese content (`:lang(ja)`, excluding Font Awesome elements) takes `$font-family-sans-serif-jp`, which
  starts with `$mds-font-family-base`. The rule sits after Bootstrap in the preset; a theme that sets `font-family` on
  `body` in `post.scss` does not override it, because `:lang(ja)` matches elements directly.
- On 5.2 the default is the system font stack and Boost ships no font files of its own.
- Font Awesome is Free 6.7.2 on both versions. Its `@font-face` rules use `[[font:core|fa-solid-900.woff2]]`, so a
  theme can replace a webfont file by placing one with the same name in `fonts_core/`.
- Loading a font from an external host (a `@import url(...)` or a remote `src`) makes every page depend on that host
  and sends visitor data to it; self-host instead.

## Images in dark mode and RTL

- A background image written with `[[pix:]]` is not adapted to the colour mode. For line art, ship a second file and
  switch it under `[data-bs-theme="dark"]`, or use a mid-tone that works on both surfaces.
- URLs inside `url()` are not changed by the RTL flipper. A directional image needs the remove-and-raw pair:

```scss
.mytheme-hero {
    /*rtl:remove*/
    background-image: url([[pix:theme|hero-ltr]]);
    /*rtl:raw:
    background-image: url([[pix:theme|hero-rtl]]);
    */
    background-repeat: no-repeat;
}
```

- A file uploaded through a theme setting is not a `[[pix:]]` image. Its URL comes from
  `$theme->setting_file_url('<setting>', '<filearea>')` in the extra-SCSS callback, as Boost does for its background
  image, and needs the theme's `pluginfile` function; see `moodle-theme-settings`.

Official pages: https://moodledev.io/docs/5.3/apis/plugintypes/theme/images and
https://moodledev.io/docs/5.3/apis/plugintypes/theme/fonts
