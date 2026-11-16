# Layout catalogue

Read this when you need to know which layout name a page uses, what Boost's entry for it contains, which layout
option keys are read and by whom, or which body classes a page carries.

All of it was read in `public/theme/boost/config.php`, `public/lib/pagelib.php`,
`public/lib/classes/output/theme_config.php` and `public/lib/classes/output/core_renderer.php` on 5.3.0. Boost's
`config.php` and `layout/*.php` are byte-identical in 5.2, so the tables hold for both versions.

## Boost's layouts

Every theme starts from this table, whether or not Boost is a parent. The only block region Boost declares is
`side-pre`, shown in the right-hand drawer.

| Layout name | File | Regions | Options set by Boost | Used by |
|---|---|---|---|---|
| `base` | `drawers.php` | none | | The default when a script sets nothing; error pages |
| `standard` | `drawers.php` | `side-pre` | | General pages; the fallback for an unknown layout name |
| `course` | `drawers.php` | `side-pre` | `langmenu` | The course main page |
| `coursecategory` | `drawers.php` | `side-pre` | | Category pages, course listing |
| `incourse` | `drawers.php` | `side-pre` | | Activity pages; set by `require_login()` when a course module is passed |
| `frontpage` | `drawers.php` | `side-pre` | `nonavbar` | Site home |
| `admin` | `drawers.php` | `side-pre` | | Site administration; set by `admin_externalpage_setup()` |
| `mycourses` | `drawers.php` | `side-pre` | `nonavbar` | My courses |
| `mydashboard` | `drawers.php` | `side-pre` | `nonavbar`, `langmenu` | Dashboard |
| `mypublic` | `drawers.php` | `side-pre` | | User profile |
| `report` | `drawers.php` | `side-pre` | | Reports |
| `login` | `login.php` | none | `langmenu` | Login, sign-up, forgotten password |
| `popup` | `columns1.php` | none | `nofooter`, `nonavbar`, `activityheader` with `notitle`, `nocompletion`, `nodescription` | Pop-up windows |
| `frametop` | `columns1.php` | none | `nofooter`, `nocoursefooter`, `activityheader` with `nocompletion` | Legacy frames |
| `print` | `columns1.php` | none | `nofooter`, `nonavbar` false, `noactivityheader` | Print views |
| `embedded` | `embedded.php` | `side-pre` | | Pages shown inside an iframe or object |
| `redirect` | `embedded.php` | none | | The redirect notice page, set by `redirect()` |
| `maintenance` | `maintenance.php` | none | | Install, upgrade, maintenance mode |
| `secure` | `secure.php` | `side-pre` | `activityheader` with `notitle` false | Safe Exam Browser and secure-window quiz attempts |

Boost ships a seventh layout file, `columns2.php` with `templates/columns2.mustache`, that no entry in its table
uses. A theme can point a layout at it by name.

Notes for choosing a layout from plugin code, which a theme author meets as bug reports:

- Boost's SCSS has rules keyed on `body.pagelayout-<name>` and on `body.limitedwidth`, so the layout name changes
  width and drawer behaviour, not only the file (for example `body:not(.pagelayout-standard):not(.limitedwidth)`
  in `public/theme/boost/scss/moodle/layout.scss`). A wide table on a page using `report` inside an activity was
  seen once to slide under the course index on 5.3; `incourse` with `$PAGE->activityheader->disable()` fixed it.
  The rule responsible was not identified.
- `limitedwidth` is not set by the layout. Scripts add it with `$PAGE->add_body_class('limitedwidth')`
  (for example `public/course/view.php`, `public/course/modedit.php`).
- A `forcepagelayout` value in `$SESSION` overrides whatever the script asked for
  (`moodle_page::set_pagelayout()`).

## Layout entry keys

| Key | Required | Meaning |
|---|---|---|
| `file` | yes | File name in `layout/`. Searched in the theme, then each parent in `$THEME->parents` order |
| `regions` | yes | Array of block region names; `[]` for none. Read without an `isset` by `get_all_block_regions()` |
| `defaultregion` | when `regions` is not empty | Where new blocks and blocks from unknown regions go. Read without a check in `setup_blocks()` |
| `options` | no | Free array, returned as `$PAGE->layout_options` |
| `theme` | no | Search only this theme's `layout/` directory for `file` |

## Who reads layout options

A search for `layout_options` over all of `public/` in 5.3.0 (PHP, Mustache, JavaScript) finds these readers and
no others. The same search in 5.2 gives the same result.

| Option key | Read by | Effect |
|---|---|---|
| `nonavbar` | `core_renderer::full_header()` | Sets `hasnavbar` false for the `core/full_header` template: no breadcrumb |
| `nocontextheader` | `core_renderer::context_header()` | The heading is rendered visually hidden |
| `noactivityheader` | `core_renderer::header()`; Boost's `layout/columns1.php` and `layout/secure.php` | No activity header; the skip-link target is printed by the header instead |
| `nologinlinks` | `core_renderer::login_info()`, `core_renderer::user_menu()` | Plain text instead of links |
| `activityheader` (array: `notitle`, `nodescription`, `nocompletion`) | `public/lib/classes/output/activity_header.php` | Hides parts of the activity header on that layout. `notitle` falls back to `$THEME->activityheaderconfig['notitle']` |
| `activityinfoinheader` (default true) | `activity_header.php` | Where activity dates and completion are shown |
| `langmenu`, `nofooter`, `nocoursefooter` | nobody | None. Boost sets them; they are inert |

The `'langmenu' => $primarymenu['lang']` line in Boost's layout files is template context taken from the primary
navigation export. It is unrelated to the `langmenu` layout option.

To give a key meaning, read it in your own layout file or renderer:

```php
// layout/course.php (in a copied layout file)
$templatecontext['showfooter'] = empty($PAGE->layout_options['nofooter']);
```

## Body id and classes

`<body>` gets its id and classes from `$OUTPUT->body_attributes()`. The id is `page-` plus the page type
(`page-mod-quiz-view`). Classes added by `moodle_page::initialise_standard_body_classes()`:

| Class | When |
|---|---|
| `path-<a>`, `path-<a>-<b>`, ... | One per leading part of the page type: `path-mod`, `path-mod-quiz` |
| `pagelayout-<name>` | Always; the page layout in use |
| `dir-ltr` or `dir-rtl`, `lang-<code>` | Always |
| `course-<id>`, `context-<id>` | When a course and context are set |
| `cmid-<id>`, `cm-type-<modname>` | On activity pages |
| `category-<id>` | When category themes are allowed |
| `format-<name>` | Course pages (`format-site` on site home) |
| `notloggedin` | Guests and logged-out users |
| `editing` | Edit mode on |
| `userswitchedrole` | The user has switched role in this course |
| `themedesignermode` | Theme designer mode on |
| `behat-site` | Behat test site |
| browser classes, `yui-skin-sam`, `yui3-skin-sam`, a class made from the site URL | Always |

Added elsewhere:

| Class | Added by |
|---|---|
| `limitedwidth` | Individual scripts, through `$PAGE->add_body_class()` |
| `uses-drawers`, `drawer-open-index` | Boost's `layout/drawers.php`, through `$OUTPUT->body_attributes($extraclasses)` |
| `jsenabled` | JavaScript, at page load |

Adding your own:

```php
// lib.php (GPL header). Runs from core_renderer::header() for the theme named here only.
function theme_mytheme_page_init(moodle_page $page): void {
    if ((string) get_config('theme_mytheme', 'compactheader') === '1') {
        $page->add_body_class('mytheme-compactheader');
    }
}
```

`add_body_class()` throws a `coding_exception` once output has started, so it cannot be called from a layout file
after `$OUTPUT->body_attributes()` has been read, nor from a template. In a layout file, pass extra classes to
`body_attributes()` instead. A child of your theme does not get `theme_mytheme_page_init()` called: the callback
name is built from the active theme's own name (`theme_config::init_page()`).

## What a layout file has in scope

`core_renderer::render_page_layout()` defines `$OUTPUT` (the renderer rendering the page), `$PAGE` and `$COURSE`
as locals and declares `$CFG`, `$SITE` and `$USER` global before the `include`. Anything else needs its own
`global` statement or a call.

`$PAGE` properties are served by `__get()` and there is no `__isset()`, so `empty($PAGE->cm)` and
`isset($PAGE->url)` are always "not set". Read the property into a variable first:

```php
$cm = $PAGE->cm;
if ($cm) {
    $templatecontext['modname'] = $cm->modname;
}
```

## Renderer calls a layout template makes

Listed in the order Boost's `drawers.mustache` uses them. The first group is required on every layout.

| Call | Where | Purpose |
|---|---|---|
| `output.doctype` | first line | Doctype; also sets the content type. Missing: a debugging notice |
| `output.htmlattributes` | on `<html>` | `lang`, `dir`, and on 5.3 `data-bs-theme` through a hook |
| `output.page_title`, `output.favicon` | `<head>` | Title and icon |
| `output.standard_head_html` | `<head>` | Stylesheets, the JavaScript configuration, head hooks |
| `bodyattributes` (or `output.body_attributes`) | on `<body>` | Body id and classes |
| `output.standard_top_of_body_html` | first in `<body>` | Top-of-body JavaScript, top-of-body hooks, the maintenance warning |
| `output.main_content` | once | The cut point between header and footer. Missing: `coding_exception` |
| `output.standard_after_main_region_html` | after the page div | After-main hooks |
| `output.standard_footer_html` | footer | Footer hooks |
| `output.standard_end_of_body_html` | last in `<body>` or in the footer | A token the footer replaces with the end-of-body JavaScript. Missing: that script block is never printed |

Usual on a full page:

| Call | Purpose |
|---|---|
| `output.full_header` | Page header: breadcrumb, heading, header actions (`core/full_header`, ids `page-header`, `page-navbar`) |
| `output.course_content_header`, `output.course_content_footer` | Notifications and course format content around the main region |
| `output.activity_navigation` | Previous and next activity links |
| `output.blocks` through the layout file: `$OUTPUT->blocks('side-pre')` | A block region as an `<aside>` with id `block-region-<name>` |
| `output.addblockbutton` through the layout file | The "Add a block" button in edit mode |
| `output.edit_switch`, `output.search_box`, `output.navbar_plugin_output`, `output.page_heading_menu` | Navbar parts, used by `theme_boost/navbar` |
| `output.debug_footer_html`, `output.login_info`, `output.page_doc_link`, `output.supportemail` | Footer parts, used by `theme_boost/footer` |

A method that does not exist on the renderer renders as empty in Mustache, with no error: the context lookup
calls a method only when `method_exists()` is true (`public/lib/mustache/src/Context.php`, identical in 5.2 and
5.3.0). That makes a 5.3-only call such as `output.colour_mode_menu` safe to leave in a template that also runs on
5.2, and it makes a typo in a method name invisible.
