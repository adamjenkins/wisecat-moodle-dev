---
name: moodle-theme-layouts-templates
description: Use when changing page structure in a Moodle theme - $THEME->layouts, layout/*.php files, block regions, layout options, copying Boost's drawers.php or drawers.mustache, overriding Mustache templates under templates/<component>/, the "!" include, drawers and the course index, body classes, the maintenance, secure and login layouts, or working out which 5.3 navigation parts are React-rendered; also for "Can not find layout file", "does not contain the main content placeholder", a filenotfound error on core/secondarymoremenu, or a template override that is ignored. Skip when the change is CSS only (moodle-theme-scss), a PHP renderer or React component override (moodle-theme-renderers-output), or the theme's config and caches (moodle-theme-development).
---

# Moodle Theme Layouts and Templates

## Overview

A theme decides page structure in two places: the `$THEME->layouts` table, which maps a page layout name to a PHP
file and its block regions, and Mustache templates, which a theme can override per component. This skill gives the
smallest change that works for each need, and the way to keep copied Boost files working on 5.2 and 5.3.

## When to Use

- Adding, moving or removing something in the page frame: banner, footer, navbar item, block region, drawer
- Replacing a layout for some page types, or adding a layout file
- Overriding a core, plugin or Boost template from a theme
- A theme that must run on 5.2 and 5.3 with a copied layout template
- Finding out whether a 5.3 part is still reachable by a template override
- **Skip when:** the change is colour, spacing or type only (`moodle-theme-scss`); you are changing what a renderer
  method returns or overriding a React component (`moodle-theme-renderers-output`); you need `config.php` keys,
  theme selection or cache purging (`moodle-theme-development`); you are building the child theme's base files
  (`moodle-theme-boost-child`)

## How a page gets its frame

1. The script calls `$PAGE->set_pagelayout('incourse')` (default `base`; `require_login()` with a course module sets
   `incourse`; `admin_externalpage_setup()` sets `admin`).
2. `core_renderer::header()` calls `theme_<name>_page_init($PAGE)` if the active theme defines it, then asks the
   theme for the layout file of that page layout and `include`s it with `$OUTPUT`, `$PAGE`, `$COURSE`, `$CFG`,
   `$SITE`, `$USER` in scope (`public/lib/classes/output/core_renderer.php`, `header()` and
   `render_page_layout()`, 5.3.0; same in 5.2).
3. The layout file builds a context array and echoes `$OUTPUT->render_from_template('theme_boost/drawers', $context)`.
4. Core cuts the output at the token printed by `$OUTPUT->main_content()`: what is before it is the header, what
   is after it is the footer. The script's own output goes between them.
5. Every template named in that render, and every partial inside it, is looked up in the active theme, then each
   parent in the order of `$THEME->parents`, then the owning component.

So there are three levers: the layouts table (which file, which regions), the layout file (what data), and the
templates (what markup). Most changes need only the third.

## Pick the smallest change

| Need | Do this | Cost at the next Moodle version |
|---|---|---|
| Restyle or hide something | SCSS (`moodle-theme-scss`) | none |
| Add HTML at the top of the body, before the footer, in `<head>` | A hook callback or a renderer method (`moodle-theme-renderers-output`) | none |
| Wrap a core template in extra markup | Override it and include the original with `!` | none |
| Change the navbar or footer markup | Override the Boost partial: `templates/theme_boost/navbar.mustache`, `templates/theme_boost/footer.mustache` | re-diff one partial |
| Change the frame on every drawers page | Override Boost's layout template only: `templates/theme_boost/drawers.mustache` | re-diff one template |
| Change the frame on some page layouts, add a region or new context data | Own `layout/<file>.php` plus own template, entry in `$THEME->layouts` | re-diff two files |
| Change text or structure inside React navigation (5.3) | See [versions/moodle-5.3.md](versions/moodle-5.3.md) first | high |

A child of Boost that sets no `$THEME->layouts` gets all 19 Boost layouts and needs no `layout/` directory.

## The layouts table

```php
// config.php (GPL header)
$THEME->layouts = [
    // Only the entries that differ from the parent. Each entry replaces the parent's entry whole.
    'course' => [
        'file' => 'course.php',            // Looked up in this theme's layout/, then each parent's.
        'regions' => ['side-pre'],         // Always present, even when empty.
        'defaultregion' => 'side-pre',     // Required when regions is not empty.
        'options' => ['langmenu' => true], // Not merged with the parent's options: restate them.
    ],
];
```

- **Layouts cascade.** The table starts from Boost's, then each parent's entries are laid over it from the farthest
  to the nearest, then the theme's own. An empty entry is skipped, so it cannot remove an inherited layout
  (`public/lib/classes/output/theme_config.php`, constructor, 5.3.0; same code read in 5.2).
- **An entry is replaced, not merged.** A child entry with only `'file'` loses the parent's `regions` and `options`.
  Symptom: blocks vanish from that page type, or a PHP warning from `get_all_block_regions()`, which reads
  `regions` of every layout without a check. Fix: copy the whole parent entry, then edit it.
- **Regions without `defaultregion`** give a PHP warning in `setup_blocks()` and blocks with no home
  (`theme_config.php`, `setup_blocks()`, 5.3.0).
- **Stand-alone themes start from Boost's table too.** Every layout the theme does not redefine still points at
  `drawers.php`, and only the theme and its declared parents are searched for the file. Symptom:
  `coding_exception` "Can not find layout file for: X (drawers.php)". Fix: define all layout names, or list `boost`
  in `parents`. Read in the source, not run.
- **`'theme' => 'boost'`** in an entry limits the file search to that one theme's `layout/` directory.
- **An unknown page layout name** falls back to `standard` with a debugging notice.
- **Only six option keys are read by core**: `nonavbar`, `nocontextheader`, `noactivityheader`, `nologinlinks`,
  `activityheader` (array of `notitle`, `nodescription`, `nocompletion`) and `activityinfoinheader`. Boost's config
  also sets `langmenu`, `nofooter` and `nocoursefooter`, which nothing in core or Boost reads (grep of
  `layout_options` over 5.3.0 and 5.2). A key of your own works only if your layout file reads
  `$PAGE->layout_options['key']`.

The layout names, their files, regions, options and which pages use them are in
[reference/layout-catalogue.md](reference/layout-catalogue.md).

## Recipe 1: change markup without copying a layout

Template overrides reach Boost's own templates, because the lookup is by component and Boost is a component.

```mustache
{{!
    @template theme_mytheme/theme_boost/footer

    Boost's footer with a line of text above it. The original is included with the "!" suffix,
    which skips theme overrides, so this file holds none of Boost's markup.

    Example context (json):
    { "output": { "mytheme_footnote": "Maintained by the learning team" } }
}}
{{#output.mytheme_footnote}}
    <div class="mytheme-footnote container-fluid py-2">{{{output.mytheme_footnote}}}</div>
{{/output.mytheme_footnote}}
{{> theme_boost/footer! }}
```

Save it as `templates/theme_boost/footer.mustache` in the theme. Data that Boost's layout file does not pass comes
from a public, argument-free method on the theme's renderer, reached as `output.<method>`:

```php
// classes/output/core_renderer.php (GPL header)
namespace theme_mytheme\output;

/**
 * Renderer overrides for theme_mytheme.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class core_renderer extends \theme_boost\output\core_renderer {
    /**
     * The footnote setting, formatted for output.
     *
     * @return string
     */
    public function mytheme_footnote(): string {
        $text = (string) get_config('theme_mytheme', 'footnote');
        return $text === '' ? '' : format_string($text, true, ['context' => \core\context\system::instance()]);
    }
}
```

- The renderer is used only if `config.php` restates `$THEME->rendererfactory = 'theme_overridden_renderer_factory';`
  (it is not inherited; see `moodle-theme-boost-child`). Symptom without it: the section renders nothing, because
  Mustache calls a method only if `method_exists()` says it is there, and otherwise treats the name as empty
  (`public/lib/mustache/src/Context.php`, same file in 5.2).
- The `!` suffix is 5.2 and later (`public/lib/classes/output/mustache_template_finder.php`, identical in 5.2 and
  5.3.0). Wrapping `core/notification_info` this way was run on 5.3.0, in PHP and in a browser-side render;
  wrapping a `theme_boost` partial uses the same code path and was read, not run.
- To change the frame itself, copy `public/theme/boost/templates/drawers.mustache` to
  `templates/theme_boost/drawers.mustache` and edit it. Boost's `drawers.php` then renders your copy on all 11
  layouts that use it. Follow the copy rules in recipe 2.

## Recipe 2: own layout file and template, with upstream twins

Use this when only some page layouts change, or the template needs data that a renderer method cannot give.

1. Copy `public/theme/boost/layout/drawers.php` to `layout/course.php` and
   `public/theme/boost/templates/drawers.mustache` to `templates/course.mustache`.
2. Copy both again, untouched, with the suffix `.upstream` (`layout/course.php.upstream`,
   `templates/course.mustache.upstream`). These are the record of what was copied.
3. In each working copy keep the original author's `@copyright` line, add yours under it, and add a header comment
   that names the source, the Moodle version, and every modification.
4. Edit: add keys to `$templatecontext`, change the last line to
   `echo $OUTPUT->render_from_template('theme_mytheme/course', $templatecontext);`, and edit the template.
5. Point the layouts at the file (the entry in "The layouts table" above).
6. At each Moodle release: `diff` the new core file against your `.upstream` copy. Apply what changed to the
   working copy, replace the `.upstream` copy, and record it in the change log.

This was run on 5.3.0 with the `course` layout. Two things found there: phpcs with the moodle standard reports
Boost's own `drawers.php` (no trailing comma after the last context item), so fix that line in the copy; and the
`.upstream` extension keeps the twins out of phpcs and the Mustache lint (moodle-plugin-ci selects `*.php` and
`*.mustache` by name). The full worked files, the header
comment wording and the per-release checklist are in [reference/copying-a-layout.md](reference/copying-a-layout.md).

What a layout template must print, in this order, or the page breaks: `output.doctype`, `output.htmlattributes`
on `<html>`, `output.standard_head_html` in `<head>`, the body attributes, `output.standard_top_of_body_html`,
`output.main_content`, `output.standard_after_main_region_html`, `output.standard_footer_html` and
`output.standard_end_of_body_html`. Boost prints the first three through the `theme_boost/head` partial and the
last two through `theme_boost/footer`.

- No `main_content`: `coding_exception` "page layout file ... does not contain the main content placeholder".
- No `doctype`: a debugging notice "The page layout file did not call $OUTPUT->doctype()".
- No `standard_end_of_body_html`: the page's end-of-body JavaScript is never printed, with no error (the footer
  replaces a token that method prints; read in the source).
  (`public/lib/classes/output/core_renderer.php`, `header()` and `footer()`, 5.3.0.)

## One copied template for 5.2 and 5.3

Boost's `layout/*.php` files are byte-identical in 5.2 and 5.3.0 (`diff -r`), so a copied layout file works on
both. `drawers.mustache` differs in exactly two places, and a copy of either version fails on the other:

| In the copy | On the other version | Symptom |
|---|---|---|
| 5.3's `{{> core/secondarymoremenu}}` | 5.2 has no such template | `filenotfound` exception on every page with secondary navigation (read in the 5.2 source, not run) |
| 5.3's `{{$drawercontrols}}` block | 5.2's `theme_boost/drawer` has only `drawerheadercontent` | course index expand and collapse control missing, no error |
| 5.2's `{{> core/moremenu}}` | still ships in 5.3 | legacy menu markup; core Behat navigation steps and Boost's 5.3 styles target the new markup |
| 5.2's `{{$drawerheadercontent}}` block | removed from 5.3's `theme_boost/drawer` | same control missing, no error |

A template that works on both fills both blocks (each parent uses only the one it defines) and chooses the partial
by a key that only 5.3's navigation export contains:

```mustache
{{$drawerheadercontent}}{{> theme_boost/courseindexdrawercontrols}}{{/drawerheadercontent}}
{{$drawercontrols}}{{> theme_boost/courseindexdrawercontrols}}{{/drawercontrols}}
```

```mustache
{{#secondarymoremenu}}
    <div class="secondary-navigation d-print-none">
        {{#reactprops}}{{> core/secondarymoremenu}}{{/reactprops}}
        {{^reactprops}}{{> core/moremenu}}{{/reactprops}}
    </div>
{{/secondarymoremenu}}
```

- Mustache loads a partial only when the section around it is rendered (`public/lib/mustache/src/Compiler.php`,
  partial code is emitted inside the section closure; same file in 5.2), so the 5.3-only name is never looked up
  on 5.2. `reactprops` is set by `core\navigation\output\more_menu::export_for_template()` on 5.3.0 and absent in
  5.2. Read in both sources; not run on 5.2.
- The same switch works in a copied `navbar.mustache` with `core/primarymoremenu`, inside `{{#primarymoremenu}}`.
- If the theme copies more than the drawers template (navbar, user menu, login), one branch per Moodle version is
  less work than switches; the large child themes do that. Details per version are in the Version notes files.

## Template overrides

- **Path:** `templates/<component>/<name>.mustache` in the theme, component in frankenstyle: `core`, `core_form`,
  `core_course`, `mod_forum`, `block_myoverview`, `theme_boost`. Subdirectories follow the template name:
  `core/local/toast/wrapper` is `templates/core/local/toast/wrapper.mustache`.
- **Order:** active theme, each parent in `$THEME->parents` order, then the component's own `templates/`
  (`mustache_template_finder.php`, `get_template_directories_for_component()`). The nearest theme wins. Boost
  itself overrides core this way (`public/theme/boost/templates/core/`), so check there before copying from
  `public/lib/templates/`.
- **A theme's own templates** sit directly in `templates/` and are named `theme_mytheme/<name>`.
- **`{{> core/name! }}`** includes the component's original and ignores every theme override. Use it to wrap
  instead of copy. It cannot change markup inside the original. An override that includes its own name without
  the `!` includes itself.
- **`{{< theme_boost/drawer }}...{{/ theme_boost/drawer }}`** fills named `{{$block}}`s of a parent template. A block
  name the parent does not define is ignored without a warning.
- **Overrides apply to browser-rendered templates too**: `core/templates` fetches the source through the same
  finder for the current theme.
- **Keep the override's docblock**: `@template`, the context description and `Example context (json):`. The
  Mustache lint in `moodle-plugin-ci` fails without them, also for files copied unchanged from core
  (`moodle-theme-testing-release`).

Caches, as far as templates go:

| Rendered by | Edit seen after | Why |
|---|---|---|
| PHP (`render_from_template`) | the next request, no purge, designer mode on or off | compiled templates are keyed by a hash of the source text (`public/lib/mustache/src/Engine.php`, `getTemplateClassName()`, 5.3.0) |
| JavaScript (`core/templates`) | a purge, or `$CFG->cachetemplates = false;` | the browser keeps the source in localStorage under the template revision; theme designer mode does not change this (`public/lib/classes/output/requirements/page_requirements_manager.php`, 5.3.0) |

A layout file edit is PHP: with OPcache validating timestamps it shows on the next request.

## Writing template markup

Each of these passes lint and unit tests and fails only in a browser, unless noted.

| Rule | Symptom when ignored | Fix |
|---|---|---|
| A `{{! }}` comment ends at the first `}}` | Tag syntax or JSON with `}}` inside a comment or example context ends the comment; the rest prints on the page or gives "Unclosed section" | Describe helpers in prose; write `} }` in example JSON |
| `{{#pix}}` is for icons | The image is forced to icon size by Boost's `.icon` class | For a full-size image pass a URL in the context and write `<img>` |
| `uniqid` is taken | A context variable named `uniqid` is overwritten in browser renders (`public/lib/amd/src/local/templates/renderer.js`, 5.3.0), so PHP and browser output differ | Use another name |
| `{{#js}}` is queued when the template renders | Rendering a template and discarding the HTML still runs its JavaScript, which then fails to find its elements | Do not render templates for their data; call `export_for_template()` |
| Bootstrap 4 class names | `.sr-only`, `.ml-2`, `.float-right`, `.badge-primary`, `data-toggle` work only through Boost's compatibility layer, planned for removal in 6.0; Behat with `--scss-deprecations` fails on them | `visually-hidden`, `ms-2`, `float-end`, `text-bg-primary`, `data-bs-toggle` |
| The `hidden` attribute loses to `d-flex` and other `d-*` utilities | The element stays visible | Toggle the `d-none` class |
| A `.row` needs a `.container` or `.container-fluid` ancestor | The page is a few pixels wider than a phone screen | Add the container, or `mx-0` on the row |
| A partial must be one valid HTML block | Lint HTML validation fails on a partial rooted in a bare `<li>`, or `role="log"` on an `<ol>` | Wrap in the list element; put the role on a `<div>` |
| A missing `{{#str}}` key | Prints `[[key]]` or throws on the live page while every gate is green | Render each new template in a PHPUnit test and assert no `[[` (`moodle-theme-testing-release`) |

## Page structure to keep

Core JavaScript, Behat steps and plugins address the page by these names. A custom layout keeps them:

- Ids: `page-wrapper`, `page` (read by the drawers, sticky footer, scroll manager and message drawer modules),
  `page-content`, `region-main` (notifications and core Behat steps), `region-main-box`, `page-header`,
  `page-navbar`, `page-footer`. Behat's `"page" "region"` selector is an element with that id.
- Navigation wrappers: `.primary-navigation` and `.secondary-navigation` (core Behat steps
  "I select ... from primary navigation" look inside them).
- Drawers: ids `theme_boost-drawers-courseindex`, `theme_boost-drawers-blocks`, `theme_boost-drawers-primary`;
  toggles are `[data-toggler="drawers"][data-action="toggle"][data-target="<drawer id>"]`.
- In Boost the drawers are siblings of `#page`, not inside it. A selector such as `#page .block` matches no block
  in the block drawer.
- The navbar is `nav.navbar.fixed-top`. Content starts `$navbar-height` below the viewport top; anything a theme
  makes sticky, and any script that scrolls an element into view, must allow for it.
- Body classes come from `$PAGE` (`pagelayout-<name>`, `path-<...>`, `dir-rtl`, `limitedwidth`, `editing`,
  `format-<name>`) and from the layout file (`uses-drawers`, `drawer-open-index`). Add your own with
  `$OUTPUT->body_attributes(['myclass'])` in the layout file, or `$page->add_body_class('myclass')` inside
  `theme_mytheme_page_init(moodle_page $page)` in `lib.php`, which runs for that theme only, not for its children.

The full lists, the drawer preferences and how to add a block region or a drawer are in
[reference/drawers-and-regions.md](reference/drawers-and-regions.md).

## What 5.3 renders with React

**5.3+:** four parts are mounted as React components: primary navigation, secondary navigation, the edit mode
switch and the Timeline block. The first three are mounted from Mustache templates (`core/primarymoremenu`,
`core/secondarymoremenu`, `core/editswitch`) that a theme can still override to change the wrapper, the classes or
the no-JavaScript fallback. The items inside them are not template markup any more: selectors such as
`.primary-navigation .nav-link.active` match nothing once JavaScript has run. The Timeline block has no template
at all. Everything else (user menu, drawers, course index, breadcrumb, footer, activity chooser) is Mustache on
both versions. Read in the 5.3.0 source; no React override was built. See [versions/moodle-5.3.md](versions/moodle-5.3.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Child layout entry with only `'file'` | Regions and options of the parent entry are gone; blocks disappear on that page type | Copy the parent's whole entry, then change `file` |
| Copying 5.3's `drawers.mustache` into a theme that supports 5.2 | `filenotfound` for `core/secondarymoremenu` on 5.2 | The `reactprops` switch above, or one branch per version |
| Filling `drawerheadercontent` on 5.3, or `drawercontrols` on 5.2 | Course index controls missing, no message | Fill both blocks |
| Wrapping `{{> core/secondarymoremenu}}` in a `<nav>` | **5.3+:** two navigation landmarks; the component renders its own | Wrap in a `<div class="secondary-navigation">` only |
| Override saved as `templates/drawers.mustache` to replace Boost's | Ignored: that name is `theme_mytheme/drawers` | `templates/theme_boost/drawers.mustache` |
| Copying a core template that Boost also overrides, from `public/lib/templates/` | Boost's changes are lost in the child | Copy from `public/theme/boost/templates/core/` |
| Copying a layout with no `.upstream` twin | The next Moodle version changes Boost's file and nobody knows what to merge; pages break in places no test visits | Keep the twin and diff it at each release |
| Setting `'options' => ['nofooter' => true]` and expecting core to act | Nothing changes | Read `$PAGE->layout_options['nofooter']` in your layout file |
| Calling a custom `output.<method>` in the `maintenance` layout | Renders empty: that layout uses `core_renderer_maintenance`, not the theme's `core_renderer` | Keep the maintenance template free of theme methods; see [reference/special-layouts.md](reference/special-layouts.md) |
| `empty($PAGE->cm)` or `isset($PAGE->pagetype)` in a layout file | Always "not set": `moodle_page` has no `__isset()` | Read the property into a variable first |
| Choosing a page layout for its name | Boost keys width and drawer rules on `pagelayout-<name>` and `limitedwidth`; a wide table on a `report` layout page sat under the course index (seen once on 5.3; the rule responsible was not identified) | For a page inside an activity use `incourse`; check at phone and desktop width |
| Judging a template change through a browser-rendered template with designer mode on | No change seen | `$CFG->cachetemplates = false;` or purge |
| Styling 5.3 navigation by looking at the page with JavaScript off | The fallback markup is the legacy one, so old selectors seem to work | Inspect with JavaScript on |

## Reference files

| File | Read it when |
|---|---|
| [reference/layout-catalogue.md](reference/layout-catalogue.md) | You need to know which layout name a page uses, what Boost's entry for it contains, which option keys are read and by whom, or the body classes a page carries |
| [reference/copying-a-layout.md](reference/copying-a-layout.md) | You are about to copy a Boost layout file or layout template, add template context in PHP, or port copied files to the next Moodle version |
| [reference/drawers-and-regions.md](reference/drawers-and-regions.md) | The theme adds or moves a block region, adds a drawer, changes the course index drawer, or a test must open or close a drawer |
| [reference/special-layouts.md](reference/special-layouts.md) | The theme touches the `maintenance`, `secure`, `login`, `embedded`, `popup` or `redirect` layouts |
| [reference/template-authoring.md](reference/template-authoring.md) | You are writing a new template or a larger override and need the helper list, block and partial rules, the docblock the lint expects, or the full list of markup traps |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](versions/moodle-5.3.md) |

## References

- https://moodledev.io/docs/5.3/apis/plugintypes/theme/layout
- https://moodledev.io/docs/5.3/guides/templates
- https://moodledev.io/docs/5.3/apis/plugintypes/theme
- https://moodledev.io/docs/5.3/guides/javascript/react/theming
- Core: `public/lib/classes/output/theme_config.php`, `public/lib/classes/output/mustache_template_finder.php`,
  `public/lib/classes/output/core_renderer.php`, `public/theme/boost/config.php`, `public/theme/boost/layout/`,
  `public/theme/boost/templates/` (5.2 and 5.3.0)
