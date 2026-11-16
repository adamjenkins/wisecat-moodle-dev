# From a setting to the CSS

Read this when a theme setting must change how the site looks and you have to choose how the value travels: an
SCSS variable, a CSS custom property, a rule in extra SCSS, or a body class. It also covers values with units,
fonts, images, dark mode and what a theme setting cannot reach.

The compile order was read in `theme_config::get_css_content_from_scss()`, `get_pre_scss_code()` and
`get_extra_scss_code()` (`public/lib/classes/output/theme_config.php`, 5.2 and 5.3). The variable route and the
image rule were run on 5.3.0 in a Boost child theme; the custom-property and body-class routes are standard CSS
and were read, not run, as written here.

## The order everything is compiled in

1. Pre-SCSS callbacks: every parent's, farthest parent first (Boost before a child of Boost), then the active
   theme's. Each one receives the active theme's `theme_config`.
2. The main SCSS (`$THEME->scss`): for a Boost child, usually the theme's own "pre" file, Boost's preset, then the
   theme's "post" file.
3. Extra-SCSS callbacks, in the same parent-first order.

Consequences:

- A variable assigned in a pre-SCSS callback beats every `!default` assignment in the main SCSS, because it is
  already set when those lines are reached. Boost's preset declares its variables with `!default`
  (`$primary: $blue !default;` in `public/theme/boost/scss/preset/default.scss`).
- When Boost's callback and the child's both assign the same variable without `!default`, the child's wins: it
  runs later.
- A variable assigned in an extra-SCSS callback is too late to change anything compiled before it. Extra SCSS is
  for rules.
- A custom-property declaration works wherever it is emitted, because the browser resolves it.

## Choosing the route

| Route | Use it for | Cost | Dark mode |
|---|---|---|---|
| SCSS variable from the pre-SCSS callback | Changing Bootstrap or Boost variables (`$primary`, `$border-radius`, `$font-family-sans-serif`), and any value used in a Sass function | Needs a recompile: the setting carries the updated-callback | The compiled result is fixed; a second value for dark needs its own rule |
| CSS custom property in a `:root` rule from the extra-SCSS callback | The theme's own colours and sizes used in its own rules through `var(--mytheme-x)` | Needs a recompile too (the rule is in the compiled CSS), but no Sass function can use the value | Can be redeclared under the dark selector |
| A rule from the extra-SCSS callback | A background image URL, or one rule that exists only when a setting is on | Needs a recompile | Write the dark variant as a second rule |
| Body class from PHP, with both variants in the SCSS | On/off and "variant A or B" settings | No recompile and no callback: the class changes on the next request | Independent |

Pick one route for each value and keep to it across the theme. A theme that sends the same settings through
variables, custom properties and a text-replacement pass ends up with the default written in each of them, and the
copies drift apart: one large theme shows two different fallback colours for one setting for that reason.

## SCSS variables: the map pattern

For more than two or three settings, a map keeps the callback short and puts the validation in one place:

```php
/** SCSS variables from this theme's settings, placed before the main SCSS. */
function theme_mytheme_get_pre_scss($theme) {
    $colour = '/^#([0-9a-fA-F]{3}){1,2}$/';
    $length = '/^\d+(\.\d+)?(px|rem|em|%)$/';
    // Setting key => [pattern, SCSS variables to set].
    $map = [
        'accent' => [$colour, ['mytheme-accent']],
        'linkcolour' => [$colour, ['link-color']],
        'radius' => [$length, ['border-radius', 'card-border-radius']],
    ];
    $scss = '';
    foreach ($map as $key => [$pattern, $targets]) {
        $value = get_config('theme_mytheme', $key);
        if ($value === false || $value === '' || !preg_match($pattern, $value)) {
            continue;
        }
        foreach ($targets as $target) {
            $scss .= '$' . $target . ': ' . $value . ";\n";
        }
    }
    return $scss;
}
```

Rules that go with it:

- **Skip an empty or invalid value; never emit a variable with nothing after the colon.** `$primary: ;` is a parse
  error, the compile fails, and the site is served Boost's stock CSS (run on 5.3.0).
- **Every variable the theme invents has a `!default` line in the theme's SCSS**, so it is defined when the
  setting is empty. An undefined variable is a compile error with the same result.
- **Prefix the theme's own variables** (`$mytheme-accent`). Unprefixed names collide with Bootstrap's and Boost's
  now or in a later version.
- Boost uses the same pattern with one entry, `brandcolor` to `$primary` (`theme_boost_get_pre_scss()` in
  `public/theme/boost/lib.php`). In a Boost child that declares a `brandcolor` setting, do not map it again.
- To let a child theme of yours override a value under its own component, read `$theme->settings->{$key} ?? null`
  instead of `get_config()` for that key, and document the key.

## Values with units, numbers and fonts

- Store the unit with the value (a select whose keys are `'0'`, `'.25rem'`, `'.5rem'`, or a text setting with a
  length pattern). A bare number that PHP later joins to `px` cannot become `rem` without an upgrade step.
- A percentage or opacity: store `0`-`100` from a select and emit `$mytheme-overlay-opacity: 0.35;` computed in
  PHP with `number_format($value / 100, 2, '.', '')`. Do not rely on the locale for the decimal point.
- A font family: accept letters, digits, spaces, commas, quotes and hyphens only, and emit the list as typed:
  `$font-family-sans-serif: "Inter", system-ui, sans-serif;`. Shipping the font files themselves is covered in
  `moodle-theme-scss`.

## Images

```php
/** SCSS built from this theme's settings, placed after the main SCSS. */
function theme_mytheme_get_extra_scss($theme) {
    $scss = '';
    $url = theme_config::load('mytheme')->setting_file_url('bannerimage', 'bannerimage');
    if (!empty($url)) {
        $scss .= ".mytheme-banner { background-image: url('$url'); background-size: cover; }\n";
    }
    return $scss;
}
```

- `setting_file_url()` returns `null` when no file is set, and a protocol-relative URL (`//host/pluginfile.php/...`)
  otherwise, with each path part URL-encoded, so it is safe inside `url('...')`.
- The URL contains the theme revision. The compiled CSS therefore holds a URL for one revision; that is fine,
  because a new upload resets the caches (through the updated-callback) and the CSS is rebuilt with the new URL.
- An image used in an `<img>` tag does not belong in SCSS: put the URL in the template context instead.
- In a Boost child, the settings `backgroundimage` and `loginbackgroundimage` are already turned into rules by
  Boost's extra-SCSS callback. Declare the settings and serve the two file areas; do not write the rules again.

## CSS custom properties

```php
$accent = get_config('theme_mytheme', 'accent');
if (!empty($accent) && preg_match('/^#([0-9a-fA-F]{3}){1,2}$/', $accent)) {
    $scss .= ":root { --mytheme-accent: $accent; }\n";
}
```

```scss
.mytheme-banner {
    border-color: var(--mytheme-accent, #{$mytheme-accent});
}
```

- Prefix the property (`--mytheme-`). `--bs-*` belongs to Bootstrap and, on 5.3, `--mds-*` to Moodle's design
  tokens; setting those from a theme setting is a re-brand technique described in `moodle-theme-scss`.
- The fallback inside `var()` covers the empty setting, so the PHP side needs no default.
- **5.3+:** to give a different value in dark mode, emit a second rule under `[data-bs-theme="dark"]` from a
  second setting, or derive it in SCSS. A single colour setting chosen against a light background often fails
  contrast on a dark one; the dark mode rules are in `moodle-theme-scss`.

## Body class

For a setting that switches a variant, compile both variants and let PHP choose:

```scss
body.mytheme-corners-square {
    .card,
    .btn {
        border-radius: 0;
    }
}
```

The class is added where the theme builds the body attributes. In a layout file the theme owns:

```php
$extraclasses[] = 'mytheme-corners-' . (get_config('theme_mytheme', 'corners') === 'square' ? 'square' : 'round');
$bodyattributes = $OUTPUT->body_attributes($extraclasses);
```

A theme that inherits Boost's layouts adds the class in its `core_renderer::body_attributes()` override instead
(`moodle-theme-renderers-output`). Build the class name from a fixed list as above, never by concatenating the raw
setting value into the attribute.

Advantages: the setting needs no updated-callback, takes effect on the next request, and can later vary by page or
user without a second stylesheet. Limits: it cannot change a Bootstrap variable, and the CSS for every variant is
always sent.

## Raw SCSS from the admin

Two text boxes for admins, one before and one after the main SCSS, are a Boost convention: settings `scsspre` and
`scss` of type `admin_setting_scsscode`. In a Boost child, declare them with exactly those names and nothing else:
Boost's callbacks append them (they read the active theme's settings). The setting accepts text that parses even
when it cannot compile, so an admin can save SCSS that sends the whole site back to stock Boost CSS; say in the
description that the look should be checked after saving.

## What a theme setting does not reach

- **H5P content.** It is drawn in an iframe that loads none of the theme's CSS. The only route is the site
  setting `h5pcustomcss` of `core_h5p` (`public/h5p/classes/file_storage.php`, 5.2 and 5.3).
- **Editor content.** The text inside TinyMCE is styled by the theme's editor SCSS, not by the main stylesheet
  (`moodle-theme-scss`).
- **The Moodle mobile app.** It has its own styling setting and does not load the theme.
- **Pages rendered under another theme.** Course, category, user and cohort themes can replace the site theme on
  some pages when the site allows them (`moodle-theme-development`).

## Checking the plumbing

A unit test can call the callback directly after `set_config()` and assert on the returned string, including that
a hostile value (`'red; } body { display: none'`) is left out. A full compile test and the browser checks are in
`moodle-theme-testing-release`. When checking by hand: save, then reload twice before judging, because one request
after a cache reset can still be answered with the previous CSS.
