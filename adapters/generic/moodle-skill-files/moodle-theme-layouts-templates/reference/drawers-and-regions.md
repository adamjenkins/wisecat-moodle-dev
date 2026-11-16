# Drawers, block regions and the course index

Read this when the theme adds or moves a block region, adds a drawer, changes the course index drawer, or a test
or script must open or close a drawer.

Read in `public/theme/boost/layout/drawers.php`, `public/theme/boost/templates/drawers.mustache`,
`public/theme/boost/templates/drawer.mustache`, `public/theme/boost/amd/src/drawers.js`, `public/lib/blocklib.php`
and `public/lib/classes/output/core_renderer.php` on 5.3.0. The layout file is identical in 5.2; where a template
differs between versions it is said. Adding a block region and adding a drawer were not run: both recipes are
read in the source.

## The page skeleton Boost builds

```text
body#page-<pagetype>.<classes>
  div#page-wrapper
    (top of body html)
    nav.navbar.fixed-top                       theme_boost/navbar
    div#theme_boost-drawers-primary.drawer     mobile primary navigation (theme_boost/primary-drawer-mobile)
    div#theme_boost-drawers-courseindex.drawer.drawer-left     only when there is a course index
    div#theme_boost-drawers-blocks.drawer.drawer-right         only when the page has blocks
    div#page.drawers[data-region="mainpage"]
      div#topofscroll.main-inner
        div.drawer-toggles                      the two open buttons
        header#page-header                      output.full_header (contains #page-navbar)
        div.secondary-navigation
        div#page-content
          div#region-main-box
            div#region-main
              (course content header, activity header, tertiary navigation, main content)
      footer#page-footer                        theme_boost/footer
    (after main region html)
```

Things that follow from the skeleton:

- The drawers are siblings of `#page`, not descendants. `#page .block`, `#region-main ~ aside` and similar
  selectors do not reach blocks.
- The navbar is fixed. `#page.drawers` has `margin-top: $navbar-height`, and drawers start at `top: $navbar-height`
  (`public/theme/boost/scss/moodle/layout.scss`). A banner placed above `#page` slides under the navbar; put it
  inside `#topofscroll`.
- An element can be inside the viewport rectangle and still be covered by the navbar or by a floating button. Code
  that scrolls something into view on a phone should treat the bottom edge of the navbar as the top of the visible
  area. Tests should probe with `document.elementFromPoint()` at the element's centre, not with a rectangle check.
- Either `#page` or the document is the scrolling element, depending on the layout CSS; core's scroll manager
  tests `#page` first (`public/lib/amd/src/scroll_manager.js`). Scripts should ask it instead of assuming `window`.

## The drawer partial

`theme_boost/drawer` is a parent template. A drawer is made by filling its blocks:

| Block | Purpose | Default |
|---|---|---|
| `id` | Element id; the toggle buttons target it | none, required |
| `drawerclasses` | `drawer drawer-left` or `drawer drawer-right`, plus `show` when open on load | none, required |
| `drawercontent` | The content | empty |
| `drawerpreferencename` | User preference written when the drawer is opened or closed | none: state is not remembered |
| `drawerstate` | Class put on `#page` while open: `show-drawer-left` or `show-drawer-right` | none |
| `forceopen` | `1` opens the drawer on load whatever the preference says | `0` |
| `drawercloseonresize` | `1` closes the drawer when the window becomes small | `0` |
| `drawerheading` | Heading area | empty |
| `tooltipplacement` | Tooltip side of the close button | `right` |
| `closebuttontext`, `closebuttonicon` | Close button label and icon | "Close drawer", a cross |
| `drawercontrols` | **5.3+:** controls row under the heading | empty |
| `drawerheadercontent` | **5.2 only:** the same slot under its old name | empty |

A block name the parent does not define is dropped without a message. A theme that supports both versions fills
both `drawercontrols` and `drawerheadercontent` with the same content.

The JavaScript is `theme_boost/drawers`, loaded by the partial itself. Buttons are found by attribute:

```html
<button class="btn btn-icon icon-size-3"
        data-toggler="drawers" data-action="toggle" data-target="theme_boost-drawers-blocks"
        title="{{#str}}opendrawerblocks, core{{/str}}">
```

`data-action` is `toggle`, `opendrawer` or `closedrawer`; `data-target` is the drawer id.

## User preferences behind the drawers

| Preference | Default | Declared in |
|---|---|---|
| `drawer-open-index` | true | `theme_boost_user_preferences()` in `public/theme/boost/lib.php` |
| `drawer-open-block` | false | same |

- The layout file reads them with `get_user_preferences()` and passes `courseindexopen` and `blockdraweropen`.
  Logged-out users always get both closed.
- The JavaScript writes them through the `core_user_set_user_preferences` web service, which accepts only
  preferences that a component has declared. A new drawer with its own preference name needs
  `theme_mytheme_user_preferences()` in `lib.php` returning that name, shaped like Boost's entry:

```php
// lib.php (GPL header)
function theme_mytheme_user_preferences(): array {
    return [
        'theme_mytheme_drawer_open_help' => [
            'type' => PARAM_BOOL,
            'null' => NULL_NOT_ALLOWED,
            'default' => false,
            'permissioncallback' => [core_user::class, 'is_current_user'],
        ],
    ];
}
```

  Symptom when it is missing: the drawer opens and closes, but the state is forgotten on the next page. Nothing
  is shown: the web service returns a warning instead of saving (`core_user_set_user_preferences` in
  `public/user/externallib.php`, read in the source). A preference the theme stores also belongs in its privacy
  provider (`moodle-theme-settings`).
- Do not keep drawer state in raw `localStorage`: Moodle clears the site's storage on each new login and whenever
  the JavaScript revision changes, which every cache purge does.

Under Behat the block drawer is forced open on every page unless the preference `behat_keep_drawer_closed` is 1
(`layout/drawers.php`); the core step is `I keep block drawer closed`. For browser automation outside Behat, close
the drawers for the test user by setting `drawer-open-block` and `drawer-open-index` to 0 before taking
screenshots, since an open drawer overlays content at narrow widths. Each drawer has several toggle buttons, one
per breakpoint, and most are hidden at any one width: select by
`[data-toggler="drawers"][data-action="toggle"][data-target="theme_boost-drawers-blocks"]` and take the visible one.

## The course index

- It is shown when `$THEME->usescourseindex` is true (a child must restate it; see `moodle-theme-boost-child`),
  the page is in a real course, the user can access the course, and the course format's renderer has
  `course_index_drawer()`. `core_course_drawer()` in `public/course/lib.php` returns the HTML or an empty string.
- A script can switch it off for a page with `$PAGE->set_show_course_index(false)`.
- The HTML returned is a placeholder; the course format's JavaScript fills it. A theme changes its look with SCSS
  (`public/theme/boost/scss/moodle/courseindex.scss`) or by overriding `core_courseformat/local/courseindex/*`
  templates, not in the layout.
- The heading and controls above it are Boost partials: `theme_boost/courseindexdrawerheading` and
  `theme_boost/courseindexdrawercontrols`. Both changed in 5.3.0: the controls partial is now one toggle button
  with `data-action="toggleallcourseindexsections"`, handled by Boost's `courseindexdrawercontrols` module. A copy
  of the 5.2 partial calls actions the 5.3 module no longer handles, so include the partials by name instead of
  copying them.

## Adding a block region

Four places must agree on the region name. Use lowercase letters and hyphens.

1. `config.php`: list the region in every layout that shows it.

```php
$THEME->layouts = [
    'course' => [
        'file' => 'course.php',
        'regions' => ['side-pre', 'course-top'],
        'defaultregion' => 'side-pre',
        'options' => ['langmenu' => true],
    ],
];
```

2. `lang/en/theme_mytheme.php`: the name shown in the block's "Region" menu.

```php
$string['region-course-top'] = 'Above the course content';
```

   The string is looked up in the theme, then its parents, then `theme_boost`
   (`theme_config::get_region_name()`). Without it the menu shows `[[region-course-top]]`.

3. The layout file: render the region and say whether it has content.

```php
$coursetophtml = $OUTPUT->blocks('course-top', ['mytheme-course-top'], 'section');
$templatecontext['coursetopblocks'] = $coursetophtml;
$templatecontext['hascoursetopblocks'] = (strpos($coursetophtml, 'data-block=') !== false);
$templatecontext['coursetopaddblock'] = $OUTPUT->addblockbutton('course-top');
```

4. The template: print it where it belongs.

```mustache
{{#hascoursetopblocks}}
    <div class="d-print-none" data-region="mytheme-course-top">
        {{{ coursetopaddblock }}}
        {{{ coursetopblocks }}}
    </div>
{{/hascoursetopblocks}}
```

Facts to rely on:

- `$OUTPUT->blocks($region, $classes, $tag)` returns a wrapper with id `block-region-<region>`,
  `data-blockregion` and a visually hidden heading even when the region is empty. That is why Boost tests the
  HTML for `data-block=` instead of testing for an empty string.
- The default tag is `<aside>`, a complementary landmark. For a region inside the main content pass `'section'`
  as the third argument so the page does not gain a landmark nested in `main`.
- In edit mode the region must be visible even when empty, or blocks cannot be added to it. Show the wrapper
  when `hascoursetopblocks` is true or the add-block button is not empty, as Boost does for `side-pre`.
- A block stored in a region that the current layout does not declare is shown in the layout's `defaultregion`
  (`block_manager::load_blocks()`). Blocks do not disappear when a region is removed, they move.
- `$OUTPUT->blocks()` on a region the layout does not declare returns the empty wrapper, with no error.
- A theme that offers the same region under several names, or regions switched by a setting, must compute the
  region list in one function and use it in `config.php`, the layout file and the settings page, so that the
  three cannot disagree.

Fake blocks (blocks an activity adds for one page, such as quiz navigation) go to the default region. Boost
forces the block drawer open on the first view of an activity that has them
(`theme_boost\output\core_renderer::firstview_fakeblocks()`), passed to the drawer as `forceblockdraweropen`.
A custom layout that moves `side-pre` out of the drawer must still show fake blocks, or the quiz navigation is
unreachable.

## Adding a drawer

```mustache
{{< theme_boost/drawer }}
    {{$id}}theme_mytheme-drawers-help{{/id}}
    {{$drawerclasses}}drawer drawer-right{{#mythemehelpopen}} show{{/mythemehelpopen}}{{/drawerclasses}}
    {{$drawercontent}}{{{ mythemehelpcontent }}}{{/drawercontent}}
    {{$drawerpreferencename}}theme_mytheme_drawer_open_help{{/drawerpreferencename}}
    {{$drawerstate}}show-drawer-right{{/drawerstate}}
    {{$tooltipplacement}}left{{/tooltipplacement}}
    {{$drawercloseonresize}}1{{/drawercloseonresize}}
    {{$closebuttontext}}{{#str}}closehelp, theme_mytheme{{/str}}{{/closebuttontext}}
{{/ theme_boost/drawer}}
```

- Place it beside Boost's drawers, before `#page`.
- Give it a toggle button with `data-toggler="drawers"`, `data-action="toggle"` and `data-target` set to the id.
- Two drawers on the same side share the `show-drawer-right` state class on `#page`, which Boost's layout rules
  use to make room. Opening both at once is not something Boost's CSS plans for; close the other one in your
  own script, or use the other side. Not run.
- Declare the preference (see above) and pass `mythemehelpopen` from the layout file with
  `get_user_preferences('theme_mytheme_drawer_open_help', false)`.
