# Dark mode (colour modes) in a Boost-based theme

Read this when a page, component or icon looks wrong in dark mode, or when you need to know how the mode reaches the
page, what Boost's dark palette re-points, and which helpers exist for writing dark corrections.

Colour modes exist from Moodle 5.3. Statements are read in the 5.3.0 source unless marked **run 5.3.0** (observed in a
child theme of Boost). On 5.2 Bootstrap's own `[data-bs-theme=dark]` rules are in the compiled CSS, but nothing in
Boost's PHP, templates or JavaScript sets the attribute, so dark rules are inert there.

## How the mode reaches the page

- The feature is off by default: `theme_boost | enablecolourmodes` on Boost's "Experimental settings" tab, with
  `theme_boost | defaultcolourmode` (default `light`). Both are read from the `theme_boost` component whatever theme
  is active, and the feature applies to Boost and to every theme with `boost` in `$THEME->parents`
  (`public/theme/boost/classes/colour_mode.php`: `is_enabled()`, `is_boost_theme()`). A child theme has no setting of
  its own to turn it off.
- Mode for a request (`colour_mode::get_current_mode()`): not enabled gives light; a logged-in non-guest gets the
  user preference `theme_boost_colourmode` (`light`, `dark` or `auto`); anyone else gets the cookie of the same name
  if present; otherwise the site default.
- What the page gets: `<html data-bs-theme="light|dark" data-colourmode="light|dark|auto">`, written through the
  `before_html_attributes` hook. For `auto` the server writes `light` and an inline head script resolves it against
  `prefers-color-scheme` before the first paint, then follows the device. That script is the only place the media
  query belongs.
- The switcher is `theme_boost\colour_mode::render_menu($output)`, exposed as `output.colour_mode_menu` by Boost's
  renderer and included by Boost's `navbar.mustache`. A theme with its own navbar template must output it, or users on
  a site whose default is dark have no control. Template and renderer details belong to
  `moodle-theme-layouts-templates` and `moodle-theme-renderers-output`.
- To develop in dark mode: enable the setting, set the default to Dark, and pick Dark from the switcher before
  logging out (logged-out pages use the browser's last choice).

## What Boost's dark palette does

`public/theme/boost/scss/moodle/dark.scss` is one `@include color-mode(dark)` block, imported last by
`scss/moodle.scss` so it can re-point everything above it. Bootstrap's mixin emits `[data-bs-theme="dark"] { ... }`
because `$color-mode-type` is `data`.

| Custom property | Dark value | Meaning in dark mode |
|---|---|---|
| `--bs-white` | `$dark-surface-raised` (`$gray-800`) | Raised surface: cards, modals, dropdowns |
| `--bs-gray-100` | `$dark-surface-page` (`$gray-900`) | The page |
| `--bs-gray-200` | `$dark-surface-recessed` (mix of 800 and 900) | Drawers, table stripes, hovered rows |
| `--bs-gray-300`, `--bs-gray-400` | `$gray-700`, `$gray-600` | Borders |
| `--bs-gray-500` | between `$gray-400` and `$gray-500` | Placeholders, input borders |
| `--bs-gray-600` to `--bs-gray-900`, `--bs-black` | `$gray-400` to `$gray-100` | Text |

Also re-pointed: 57 `--mds-*` tokens (surfaces, borders, text, links, feedback tints), the link colours, the five hued
`--bs-*-text-emphasis`, `--bs-focus-ring-color`, `--bs-state-*-bg` and `-border`. Links, the focus ring, primary
borders and feedback tints are derived from `$primary`, `$success`, `$info`, `$warning` and `$danger` with
`dark-readable()`, so they follow a changed brand colour.

The block also carries a few real rules: prose links in `#page-header`, `#region-main`, `#page-footer` and HTML
blocks are underlined (colour alone cannot distinguish a link on a dark page); `.bg-white` means "raised surface" and
`.bg-light` "recessed surface"; `.btn-secondary` is rebuilt because `$secondary` is a compile-time literal; `.card`,
`.dropdown-menu` and `.modal-content` get a visible border because shadows do little on dark surfaces.

Left alone on purpose: the saturated fills (`--mds-bg-feedback-*-default`, `--mds-bg-interactive-*`) and the
`--bs-*-rgb` properties behind `.text-white`, `.text-light` and the `.bg-<colour>` utilities.

The dark CSS is always in the stylesheet, whether or not the feature is enabled.

## Helpers for `post.scss` (5.3 only)

Defined in `public/theme/boost/scss/moodle/colour-mode.scss`, which `scss/moodle.scss` imports before the component
partials. They do not exist on 5.2 or in pre-SCSS.

| Helper | What it does |
|---|---|
| `@include dark-mode { ... }` | Used inside a rule. Emits the content under `[data-bs-theme="dark"]` prefixed to the enclosing selector, so the override keeps that selector's specificity and wins against the rule it corrects (**run 5.3.0**: compiles as described) |
| `@include color-mode(dark) { ... }` | Bootstrap's mixin, both versions. Use at the top level to set custom properties for the whole dark mode. Nested inside a rule it produces a descendant selector, which does not match because the attribute is on `<html>` |
| `dark-readable($color, $background: $dark-surface-raised, $min: $dark-min-contrast)` | Tints `$color` in 5% steps until it reaches the contrast ratio (default 4.6) against the surface. Use it instead of picking a dark value by hand, so the result stays readable when the brand colour changes |
| `$dark-surface-raised`, `$dark-surface-page`, `$dark-surface-recessed`, `$dark-min-contrast` | The dark greyscale and the contrast target, all `!default`, so they can be set in pre-SCSS |

```scss
// 5.3 only.
.mytheme-panel {
    background-color: $gray-100;
    color: $primary;

    @include dark-mode {
        background-color: var(--#{$prefix}gray-200);
        color: dark-readable($primary, $dark-surface-recessed);
    }
}
```

For a theme that also supports 5.2, write the selector by hand. This form was compiled and seen working in a browser
(**run 5.3.0**):

```scss
.mytheme-banner {
    border-left: .5rem solid $mytheme-accent;
    background-color: var(--bs-tertiary-bg);
    color: var(--bs-body-color);
}

[data-bs-theme="dark"] {
    .mytheme-banner {
        border-left-color: lighten($mytheme-accent, 25%);
    }
}
```

`@if mixin-exists(dark-mode) { @include dark-mode { ... } }` as a version switch was not tried; avoid it and use the
plain selector.

## Rules of thumb for theme CSS

1. Set no colour where a Bootstrap component or utility already does the job: `bg-body`, `bg-body-secondary`,
   `bg-body-tertiary`, `text-body`, `text-body-secondary`, `text-body-emphasis`, `text-bg-*`, `border`. Avoid
   `bg-white`, `bg-light`, `text-dark`, `text-white` in templates: they name a colour, not a role. `text-dark` stays
   near black on a dark surface.
2. Otherwise use a custom property that follows the mode (`--bs-body-bg`, `--bs-body-color`, `--bs-secondary-bg`,
   `--bs-tertiary-bg`, `--bs-border-color`, `--bs-emphasis-color`, `--bs-link-color`, or a `--mds-*` token on 5.3).
3. A literal is right only where the colour carries meaning and is legible on both surfaces, or where it comes with a
   `[data-bs-theme="dark"]` correction.
4. Contrast targets (WCAG 2.2 AA): 4.5:1 for text, 3:1 for large text, interface components and focus indicators.
   Automated accessibility checks catch text contrast only; borders, focus rings and icons need a look by eye.
5. A drop shadow that lifts an element off the page needs a border as well in dark mode.
6. Find every colour the theme names for itself before claiming dark mode support:

```bash
grep -rniE '#[0-9a-f]{3,8}\b|rgba?\(|hsla?\(|\b(bg|text)-(white|black|light|dark)\b' scss templates amd/src
```

   Fallbacks inside `var()` and colours in comments are fine.

## Icons and images

- Icons rendered through the icon system as Font Awesome glyphs are text and follow `color`.
- Activity icons are recoloured with an SVG filter, not a CSS colour: `color` or `fill` on `.activityicon` does
  nothing. Set the six `$activity-icon-<purpose>-bg` variables in pre-SCSS
  (`administration`, `assessment`, `collaboration`, `communication`, `content`, `interactivecontent`); Boost re-applies
  the filter with a 30% tint in dark mode (`public/theme/boost/scss/moodle/icons.scss`).
- An icon that reaches the page as `<img class="icon">` keeps its drawn colours. In dark mode Boost inverts only those
  whose URL contains `/t/`, `/e/`, `/a/`, `/i/groupn`, `/i/groups` or `/i/groupv`. Any other image icon, including a
  theme's or plugin's own SVG with a dark stroke, stays dark on a dark page. Options: give the image a mid-tone that
  works on both surfaces, map it to a font icon, or add a rule such as
  `[data-bs-theme="dark"] img.mytheme-lineicon { filter: invert(1); }`, which is safe only for single-colour line art
  (inverting a coloured image changes its hue).
- Check images with a background baked in (a logo on a white plate): they need transparency or a second file.

## Traps

| Trap | Symptom | Fix |
|---|---|---|
| Bare `:root { --bs-x: ...; }` in post or extra SCSS | The dark value of that property is lost: same specificity as the dark block, and later in the sheet (cascade reasoning, not checked in a browser) | Set the SCSS variable in pre-SCSS, or scope with `:root:not([data-bs-theme="dark"])` |
| `$card-bg`, `$state-*-bg`, `$input-border-color` set to a literal | That component stays light in dark mode | Use `var(--bs-...)`, or override the custom property inside `[data-bs-theme="dark"]` too |
| `@include color-mode(dark)` nested inside a rule | Selector `.x [data-bs-theme="dark"]` matches nothing | `@include dark-mode` (5.3) or a top-level `[data-bs-theme="dark"] .x` |
| Brand colour chosen for a white page used as text in dark mode | Fails contrast | `dark-readable($colour)` on 5.3, a lightened literal otherwise |
| Changing `$dark-surface-page` but not `$body-bg-dark` (or the reverse) | Body and surfaces out of step | Set both families together |
| Navbar copied from a 5.2 Boost | No colour mode switcher on 5.3 | Add the `output.colour_mode_menu` block from Boost 5.3's `navbar.mustache` |
| Expecting the editor to follow a mode change | An open TinyMCE keeps the skin it started with | Reload the page; nothing to fix in the theme |
| Judging dark mode on a logged-out page after setting only the user preference | Page is light | Logged-out pages use the cookie or the site default |

## Testing pointers

`php admin/tool/behat/cli/init.php --colourmode=dark` (5.3 only) turns the feature on and renders every scenario in
dark mode; a user preference `theme_boost_colourmode` pins the mode for one scenario. Accessibility scenarios run on
such a site check the same assertions in dark mode. The full recipes are in `moodle-theme-testing-release`.

Source for the official rules: https://moodledev.io/docs/5.3/guides/colourmodes
