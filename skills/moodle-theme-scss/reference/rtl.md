# Right-to-left (RTL) styles

Read this when the theme must look right in a right-to-left language, when a rule must not be flipped or must differ
in RTL, or when you need an RTL build to inspect.

Evidence: the flipper is `public/lib/classes/rtlcss.php` plus the vendored library in `public/lib/rtlcss/` (version
1.0.1); both are identical in 5.2 and 5.3 and were read, with the cases in `public/lib/tests/rtlcss_test.php`. That a
plain `border-left` comes out as `border-right` in a theme's RTL build with no directive was **run on 5.3.0**. No RTL
page was looked at in a browser for this file.

## How it works

- Direction is a property of the current language pack: `right_to_left()` is
  `get_string('thisdirection', 'langconfig') === 'rtl'` (`public/lib/weblib.php`). Nothing else decides it.
- An RTL page links the `all-rtl` sheet instead of `all` (and `editor-rtl` instead of `editor`), gets `dir="rtl"` on
  `<html>` and the body class `dir-rtl`.
- There is one stylesheet source. `theme_config::post_process()` parses the compiled CSS and flips it with
  `core_rtlcss` only for the RTL build. Flipping runs after `[[pix:]]`, `[[font:]]` and `csspostprocess`, and before
  minification, so comments are still present. Both builds are cached side by side.
- Only declarations in a served stylesheet are touched. Selectors and class names are not: Bootstrap's `ms-*`, `me-*`,
  `float-start` work in RTL because their declarations (`margin-left`, ...) are flipped.

## What is flipped

Checks run in this order; the first match wins (`RTLCSS::processRule()`).

| Order | Property test | Change |
|---|---|---|
| 1 | name ends in `direction` | `ltr` and `rtl` swapped in the value |
| 2 | name contains `left` | name: `left` becomes `right` (`margin-left`, `padding-left`, `border-left-*`, `left`, `border-top-left-radius`) |
| 3 | name contains `right` | name: `right` becomes `left` |
| 4 | `transition`, `transition-property` | `left` / `right` swapped in the value |
| 5 | name contains `float`, `clear` or `text-align` | `left` / `right` swapped in the value |
| 6 | exactly `margin`, `padding`, `border-color`, `border-style`, `border-width` | 4-value form only: 2nd and 4th values swapped |
| 7 | name contains `border-radius` | 2 values reversed; `a b c` becomes `b a b c`; `a b c d` becomes `b a d c` |
| 8 | `transform-origin` | `left` / `right` keyword swapped; a percentage x becomes `100% - x`; `0` becomes `100%` |
| 9 | `background`, `background-position`, `background-position-x` | `left` / `right` keywords swapped; a `%` or unitless x position becomes `100 - x` |
| 10 | name contains `cursor` | `e` and `w` swapped in the `*-resize` values |

## What is not flipped

Each of these is wrong in RTL until corrected by hand.

- `transform` functions: `translateX()`, `rotate()`, `skew()`, `matrix()`. An off-canvas panel moved with
  `translateX(-100%)` slides the wrong way.
- `box-shadow` and `text-shadow` x offsets.
- Gradient angles and directions, and every `background-image` value; `calc()` background positions.
- `border-radius` written with a slash.
- `inset: a b c d` (not in the shorthand list, so the 2nd and 4th values stay). 2- and 3-value shorthands are
  symmetric and need nothing.
- Anything outside a served stylesheet: inline `style=""`, styles set from JavaScript, SVG content, URLs inside
  `url()`. A template with `style="margin-left: ..."` or JavaScript that sets `el.style.left` needs its own RTL branch
  (test the `dir-rtl` body class or `document.dir`).
- Logical properties and values (`margin-inline-start`, `padding-inline-end`, `inset-inline-start`,
  `text-align: start`, `float: inline-start`): no pattern matches them, and they need no flipping because the browser
  resolves them from `dir="rtl"`. Prefer them in new code.

## Comment directives: the complete list

The comment must start (after spaces or `*`) with `rtl:` or `!rtl:`. Seven forms exist (`RTLCSS::parseComments()`).
There is no `rtl:rename`, `rtl:options`, `rtl:config` or value-level directive; those belong to the JavaScript tool of
the same name, not to this library.

| Directive | Effect |
|---|---|
| `/*rtl:ignore*/` | Do not flip the next node: a whole rule when placed before a selector, one declaration when placed inside a rule |
| `/*rtl:begin:ignore*/` ... `/*rtl:end:ignore*/` | Do not flip anything between them |
| `/*rtl:remove*/` | Delete the next node from the RTL sheet |
| `/*rtl:begin:remove*/` ... `/*rtl:end:remove*/` | Delete everything between them from the RTL sheet |
| `/*rtl:raw: <css>*/` | Insert `<css>` only in the RTL sheet, before the next node: whole rules when outside a rule, declarations when inside one |

Spaces inside the comment are accepted (`/* rtl:ignore */`); Boost uses `ignore`, `remove` and `raw` in more than
forty places (for example `public/theme/boost/scss/moodle/forms.scss`, `filemanager.scss`, `core.scss`).

## The patterns in one example

```scss
.mytheme-card {
    padding-inline-start: 1rem;      // Logical: nothing to flip.
    text-align: start;
}

.mytheme-card__badge {
    margin-left: .5rem;              // Flipped automatically.
    float: right;
}

.mytheme-code {
    /*rtl:ignore*/
    text-align: left;                // Code samples stay left-aligned in RTL.
    color: inherit;
}

.mytheme-arrow {
    transform: translateX(4px) rotate(45deg);
    /*rtl:raw:
    transform: translateX(-4px) rotate(-45deg);
    */
    display: inline-block;           // A declaration must follow the directive.
}

.mytheme-hero {
    /*rtl:remove*/
    background-image: url([[pix:theme|hero-ltr]]);
    /*rtl:raw:
    background-image: url([[pix:theme|hero-rtl]]);
    */
    background-repeat: no-repeat;
}
```

The example follows the directive forms in core's tests; it was not compiled for this file.

## Traps

| Trap | Symptom | Fix |
|---|---|---|
| A directive that is the last thing in a rule or file | Nothing happens: directives are read from the comments attached to the next node | Put a real declaration after it |
| `rtl:ignore` written inside a declaration (`left: 10px /*rtl:ignore*/;`) | Not supported; the declaration is flipped | Put the comment on the line before |
| A `begin:ignore` or `begin:remove` block whose `end:` comment is the last thing before a closing brace | The state leaks into the following rule, which is then wrongly ignored or removed | Put the `end:` comment before a real declaration in the same rule |
| `//` comment used for a directive | It never reaches the CSS | Use `/* */` |
| Directive placed before a nested rule, a mixin include or an `@extend` | The compiler may move or drop the comment, so the directive lands elsewhere (not tested where) | Put it directly before a plain declaration and check the compiled RTL sheet |
| A selector containing `.dir-rtl` | The whole rule is left untouched, which means "exactly this, in RTL". In a selector list (`.x, .dir-rtl .y { ... }`) it switches flipping off for `.x` too | Keep `.dir-rtl` rules separate, or drop them and let the flipper work |
| A custom property named with `left` or `right` (`--mytheme-left-gap`) | Property names are matched by substring, so it may be renamed in the RTL sheet (read, not run) | Name custom properties `start` / `end` |
| One-sided shadow, `translateX()`, gradient, `inset` shorthand | Silently unflipped | `rtl:raw` with the mirrored value |
| Assuming an RTL check needs an RTL user | Skipped testing | Use one of the builds below |

## Getting an RTL build to inspect

- By URL, whatever the language: `/theme/styles.php/<theme>/<rev>/all-rtl` (copy the `all` URL from a page and change
  the last segment). In theme designer mode the `styles_debug.php` URLs take `rtl=1`.
- From the command line, at the Moodle root: `php admin/cli/build_theme_css.php --themes=mytheme --direction=rtl`.
- In PHPUnit: `$theme = theme_config::load('mytheme'); $theme->set_rtl_mode(true); $css = $theme->get_css_content();`
  then assert on the flipped declaration. This is the form that was run on 5.3.0.
- A whole RTL page needs a right-to-left language pack installed and selected. Behat builds both directions of every
  theme's CSS at init, so an RTL page costs no extra compile, but core's own features install the language pack by
  download and skip unless remote language import tests are enabled. A scenario that sets the direction without a
  download was not found in core and not tried; `moodle-theme-testing-release` covers what is proven.
- RTL builds have no source maps, also in designer mode.

Official wording on directives (it lists fewer than the code accepts):
https://moodledev.io/general/development/policies/codingstyle/css
