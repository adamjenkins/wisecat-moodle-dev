# Writing and overriding Mustache templates in a theme

Read this when you are writing a new template or a larger override and need the lookup rules in full, the helper
list, block and partial rules, the docblock the lint expects, or the complete list of markup traps.

Read in `public/lib/classes/output/mustache_template_finder.php`, `public/lib/classes/output/renderer_base.php`,
`public/lib/mustache/src/` and `public/lib/amd/src/local/templates/renderer.js` on 5.3.0. The finder, the loaders
and the Mustache library are byte-identical in 5.2. Where a rule was seen running it says "run on 5.3.0".

## Where a template name resolves

A name is `<component>/<path>`. For a page rendered with theme `child` whose `config.php` has
`$THEME->parents = ['parent', 'boost'];`, `core/modal` is searched in this order and the first file wins:

```text
theme/child/templates/core/modal.mustache
<themedir>/child/templates/core/modal.mustache      only if $CFG->themedir is set
theme/parent/templates/core/modal.mustache
<themedir>/parent/templates/core/modal.mustache
theme/boost/templates/core/modal.mustache
<themedir>/boost/templates/core/modal.mustache
lib/templates/modal.mustache                        the component's own directory
```

(paths relative to `public/`.)

| Template | Component directory | Override path in a theme |
|---|---|---|
| `core/modal` | `lib/templates/` | `templates/core/modal.mustache` |
| `core/local/toast/wrapper` | `lib/templates/local/toast/` | `templates/core/local/toast/wrapper.mustache` |
| `core_form/element-text` | `lib/form/templates/` | `templates/core_form/element-text.mustache` |
| `core_course/activitychooser` | `course/templates/` | `templates/core_course/activitychooser.mustache` |
| `core_courseformat/local/content/section` | `course/format/templates/local/content/` | `templates/core_courseformat/local/content/section.mustache` |
| `mod_forum/discussion_list` | `mod/forum/templates/` | `templates/mod_forum/discussion_list.mustache` |
| `block_myoverview/main` | `blocks/myoverview/templates/` | `templates/block_myoverview/main.mustache` |
| `theme_boost/navbar` | `theme/boost/templates/` | `templates/theme_boost/navbar.mustache` |
| the theme's own `theme_mytheme/banner` | `theme/mytheme/templates/` | not an override: `templates/banner.mustache` |

- The component must be a real one: an unknown component throws `coding_exception` "Component was not valid".
- No file anywhere: `moodle_exception('filenotfound')`. In a partial this is a fatal error for the page, not an
  empty include.
- The search is a `file_exists()` walk on every request. Nothing about template locations is cached, so adding an
  override file takes effect on the next PHP render.
- Boost itself overrides `core/sticky_footer`, and adds templates in the core namespace that have no core file:
  `core/login_layout`, `core/login_panel`, `core_form/element-float`, `core_form/element-float-inline`. For those,
  the "original" is Boost's file.
- A theme cannot override a lang string through templates or any other theme mechanism; the string manager has
  no theme hook. Changing wording means overriding the template that prints it, or a site language customisation.

## Including the original: the `!` suffix

`{{> core/notification_info! }}` loads the component's own file and skips every theme, including parents.
Available from 5.2. Run on 5.3.0 in a PHP render and in a browser-side render; the Mustache lint accepted it on a
5.2 checkout.

```mustache
{{!
    @template theme_mytheme/core/notification_info

    The core information notice, wrapped. The original is included with the "!" suffix,
    which skips theme overrides, so this file does not copy core's markup.

    Context variables required for this template:
    * message A cleaned string to display.
    * extraclasses Additional classes to apply to the notification.
    * closebutton Whether a close button should be displayed.
    * announce Whether the notification should be announced to screen readers.

    Example context (json):
    { "message": "Your grades were saved.", "closebutton": 1, "announce": 1, "extraclasses": "" }
}}
<div class="mytheme-notice">
    {{> core/notification_info! }}
</div>
```

- Use it whenever the change is "something around the original". The override then never goes stale.
- Without the `!`, an override that includes its own name includes itself and recurses until PHP runs out of
  stack.
- For a template that Boost overrides, `!` goes to the component's file and so skips Boost's version too. That
  is rarely what a Boost child wants for `core/sticky_footer`.
- The same suffix works in PHP: `$OUTPUT->render_from_template('core/notification_info!', $context)`.

## Parent templates and blocks

```mustache
{{< theme_boost/drawer }}
    {{$id}}theme_mytheme-drawers-help{{/id}}
    {{$drawercontent}}...{{/drawercontent}}
{{/ theme_boost/drawer }}
```

- `{{< name }}` renders the named template with the `{{$block}}` sections replaced. Only `{{$...}}` sections
  inside the parent tag count; other text there is ignored.
- A block the parent does not define is dropped without a message. This is how a renamed block in a new Moodle
  version fails: silently. It is also what lets one file fill both the old and the new name.
- The parent name goes through the same theme lookup, so a child can override the parent template too.

## Helpers

Available in PHP and browser renders unless noted (`renderer_base::get_mustache()`; `renderer.js`, `addHelpers()`):

| Helper | Use | Note |
|---|---|---|
| `{{#str}} key, component {{/str}}` | Lang string | A third part is the `$a` value: a variable `{{name}}` or a quoted JSON object. Output is not escaped beyond what the string contains |
| `{{#cleanstr}} key, component {{/cleanstr}}` | Lang string, cleaned | For strings placed in attributes |
| `{{#quote}}...{{/quote}}` | JSON-quotes its content | Use for a `{{#str}}` argument that may contain quotes |
| `{{#pix}} key, component, alt text {{/pix}}` | An icon | Always icon-sized; not for images |
| `{{#js}}...{{/js}}` | Page JavaScript | Queued and printed at the end of the body. Cannot be nested inside another helper |
| `{{#shortentext}} 30, {{text}} {{/shortentext}}` | Shorten text | |
| `{{#userdate}} {{time}}, {{#str}}strftimedate, core_langconfig{{/str}} {{/userdate}}` | Format a timestamp | |
| `{{uniqid}}` | An id unique to this render | Use for element ids: `id="menu-{{uniqid}}"` |
| `{{#react}}{...json...} fallback html{{/react}}` | A React mount point | Registered in 5.2 and 5.3; no core template uses it before 5.3 |
| `{{config.wwwroot}}`, `{{config.homeurl}}` | Site values | PHP renders only. In browser renders the same data is at `{{globals.config.wwwroot}}` |
| `{{output.method}}` | A renderer method | Only where the context passes `output`, which layout files do. Not available in browser renders |

In a browser render these names are written onto the context object: `uniqid`, `str`, `cleanstr`, `pix`, `js`,
`react`, `quote`, `shortentext`, `userdate`, `globals`, `currentTheme`. A context variable with one of those names
is overwritten there and keeps its value in PHP, so the two renders differ.

## The docblock

```mustache
{{!
    This file is part of Moodle - http://moodle.org/
    (GPL header)
}}
{{!
    @template theme_mytheme/banner

    One-line description.

    Context variables required for this template:
    * text - Banner text, already formatted
    * dismissible - Show a close button

    Example context (json):
    {
        "text": "Welcome",
        "dismissible": true
    }
}}
```

- `@template` names the template. For an override the pattern that passed lint (run on 5.3.0) is
  `theme_mytheme/<component>/<name>`.
- `Example context (json):` is required by the Mustache lint, and the JSON is used to render the template for
  HTML validation. Without it the lint fails.
- The example context must not contain `}}`. Two closing braces end the Mustache comment; everything after them
  is printed on the page as text, and lint and PHPUnit stay green. Nested objects that close together are written
  `} }`.
- The same applies to prose: writing a tag such as a pix helper inside a comment ends the comment at its closing
  braces and leaves an unclosed section. Describe helpers in words.
- A lint ignore file (`.mustachelintignore`) silences HTML validation for the listed files only. It does not
  excuse a missing example context. The lint commands and their limits are in `moodle-theme-testing-release`.

## Markup rules that fail quietly

**One root, valid on its own.** The lint validates each template as a document fragment. A partial rooted in a
bare `<li>` or `<tr>` fails HTML validation; so does an ARIA role on an element that cannot carry it
(`role="log"` on an `<ol>`). Wrap list items in their list, or move the role to a `<div>`.

**Bootstrap 5 names only.** Boost on 5.2 and 5.3 is Bootstrap 5.3. The Bootstrap 4 names still work through
Boost's compatibility layer (`public/theme/boost/scss/moodle/bs4-compat.scss`, identical in both versions, marked
for removal in 6.0). Under Behat with `--scss-deprecations`, and in theme designer mode, an element using a
deprecated class gets a red dotted outline and a "Deprecated style in use" label, and the Behat step fails. That
includes classes added by JavaScript.

| Bootstrap 4 | Write |
|---|---|
| `sr-only`, `sr-only-focusable` | `visually-hidden`, `visually-hidden-focusable` |
| `ml-*`, `mr-*`, `pl-*`, `pr-*` | `ms-*`, `me-*`, `ps-*`, `pe-*` |
| `float-left`, `float-right`, `text-left`, `text-right` | `float-start`, `float-end`, `text-start`, `text-end` |
| `font-weight-bold` | `fw-bold` |
| `badge-primary`, `badge-pill` | `text-bg-primary`, `rounded-pill` |
| `form-group`, `custom-select`, `custom-control` | `mb-3`, `form-select`, `form-check` |
| `data-toggle`, `data-dismiss`, `data-target` (Bootstrap's) | `data-bs-toggle`, `data-bs-dismiss`, `data-bs-target` |
| `media`, `media-body` | `d-flex`, `flex-grow-1` |

Boost's drawer buttons use their own `data-toggler`, `data-action` and `data-target` attributes; those are not
Bootstrap's and keep their names.

**`hidden` against display utilities.** Bootstrap's `d-flex`, `d-block` and the other `d-*` classes are declared
with `!important`, so the `hidden` attribute does not hide an element that has one. Toggle `d-none`, and in a
template that switches between modes give each mode a test that the other modes' fields are not shown.

**Grid rows.** A `.row` has negative side margins that a `.container` or `.container-fluid` ancestor absorbs.
Without one the page becomes a few pixels wider than the viewport; only a check of `document.documentElement.scrollWidth`
at phone width shows it. Add the container or `mx-0`.

**`{{#pix}}` is icon-only.** It calls `pix_icon()`, and the result carries the `icon` class, which Boost sizes as
an icon. For an illustration, resolve the URL in PHP (`$OUTPUT->image_url('name', 'theme_mytheme')->out(false)`)
and print a plain `<img>` with your own class.

**Icons and colour modes.** A pix icon that is mapped to Font Awesome is rendered as an `<i>` element and follows
the text colour. One that is not mapped is an `<img>` and keeps its own colours in dark mode. Icon mapping belongs
to `moodle-theme-renderers-output`.

**`{{#js}}` is queued at render time.** Rendering a template whose HTML is then thrown away still queues its
script, which runs and fails to find its elements. Take data from `export_for_template()` instead of rendering.

**Arrays.** A PHP array with gaps in its keys is not a list to Mustache: pass `array_values($items)`. A test for
"has items" must be a boolean in the context: `{{#items.0}}` works only in PHP and `{{#items.length}}` only in
the browser.

**`export_for_template()` results are often objects.** Core exporters return `stdClass` in many places
(`action_link` gives `$data->attributes`). A layout file or renderer that edits exported data before rendering
must read the method first, not assume an array.

**Escaping.** `{{name}}` is escaped with `s()`. `{{{name}}}` is raw: use it only for HTML that PHP has already
produced through `format_string()`, `format_text()` or a renderer. A setting value printed with triple braces
without formatting is an injection point for whoever can edit the setting.

**Missing strings pass every gate.** A `{{#str}}` key that does not exist gives `[[key]]` on the page and a
debugging notice; lint and unit tests that do not render the template stay green. Render each new template once
in a PHPUnit test and assert the output contains no `[[`.

**Long inline content in `div.no-overflow`.** Core wraps formatted text in `.no-overflow`, which clips. Tall
inline content at the top of the box (a ruby annotation, a tall inline image) is cut off in Firefox and barely
in Chromium. Give the element top padding, and check both engines.

## Caches

| What changed | Seen after |
|---|---|
| A template rendered in PHP | The next request. Compiled templates are stored per theme revision but keyed by a hash of the source text, so an edit gives a new compiled class. Theme designer mode makes no difference |
| A new override file | The next request |
| A template rendered by `core/templates` in the browser | A cache purge, or at once with `$CFG->cachetemplates = false;` in `config.php`. The browser stores template source in localStorage under the template revision. Theme designer mode does not turn this off |
| A lang string used by `{{#str}}` | A purge of the language cache, unless string caching is off |
| A layout PHP file | The next request, once OPcache revalidates the file |

For theme work on a development site: `$CFG->cachetemplates = false; $CFG->cachejs = false;` and theme designer
mode on. The CSS side of caching is in `moodle-theme-development`.

## Finding which template prints something

1. Inspect the element and note a `data-region` value or a distinctive class.
2. Search for it under `public/` in `*.mustache` files. Search `public/theme/boost/templates/` first: if Boost
   overrides the template, that file is the one in use.
3. If nothing matches, the markup comes from PHP (`html_writer` in a renderer) or, on 5.3, from a React
   component. Neither can be changed by a template override; see `moodle-theme-renderers-output`.
4. A renderer fetched in a command-line script is the CLI renderer, so a theme's templates and renderer cannot be
   checked from the command line. Check in a browser, or in a PHPUnit test that sets the theme and calls
   `$PAGE->get_renderer('core')`.
