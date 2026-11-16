# Copying a Boost layout and keeping the copy current

Read this when you are about to copy a Boost layout file or layout template into a theme, add template context in
PHP, or port copied files to the next Moodle version.

Status of what follows: replacing the `course` layout with a copy of Boost's `drawers.php` and `drawers.mustache`
was run on 5.3.0 (browser, Behat, phpcs, Mustache lint). Nothing was run on 5.2; the 5.2 statements were read in
the 5.2 source.

## Before copying: do you need the PHP file?

| You need | Copy |
|---|---|
| Different markup in the frame, same data | Only the template, as `templates/theme_boost/drawers.mustache`. Boost's own layout file keeps rendering `theme_boost/drawers`, which now resolves to your file |
| The same, plus a value from a setting | Only the template; get the value from a renderer method as `{{{output.mytheme_method}}}` |
| Different frame on some page layouts only | Layout file and template, under new names, plus `$THEME->layouts` entries |
| A new block region, or context built from `$PAGE` in ways a renderer method cannot do | Layout file and template |

Every copied file is a file you maintain. Boost's layout template changed between 5.2 and 5.3.0; its layout PHP
files did not.

## The files

```text
theme/mytheme/
    config.php                          $THEME->layouts entry
    layout/course.php                   working copy of theme/boost/layout/drawers.php
    layout/course.php.upstream          the untouched original
    templates/course.mustache           working copy of theme/boost/templates/drawers.mustache
    templates/course.mustache.upstream  the untouched original
    UPGRADE.md                          the list of upstream files to re-diff at each Moodle release
```

The twin has the extension `.upstream`, so phpcs (which reads `*.php`) and the Mustache lint (which reads
`*.mustache`) do not see it. Run on 5.3.0: both gates were clean with the twins in the repository. To keep the
twins out of archives built with `git archive`, add `*.upstream export-ignore` to `.gitattributes`; shipping them
is also fine.

## config.php

```php
$THEME->layouts = [
    'course' => [
        'file' => 'course.php',
        'regions' => ['side-pre'],
        'defaultregion' => 'side-pre',
        'options' => ['langmenu' => true],
    ],
];
```

Copy the entry from `public/theme/boost/config.php` and change only `file`. The entry replaces Boost's entry
whole; nothing is merged. To give several page layouts the new file, repeat the entry for each name.

## The layout file

Keep the body of the copy as close to Boost's as possible, so that the next diff is small. Change three things.

The header: keep the original `@copyright` line as written in Boost's file, add your own below it, and say what
was copied and changed.

```php
/**
 * A drawer based layout for course pages.
 *
 * Copied from theme_boost's layout/drawers.php (Moodle 5.3.0); the untouched original is kept beside this
 * file as course.php.upstream. Modifications compared to the original:
 * - the banner text setting is added to the template context;
 * - the page is rendered with this theme's copy of the drawers template;
 * - a trailing comma after the last template context item.
 *
 * @package   theme_mytheme
 * @copyright 2021 Bas Brands
 * @copyright 2026 Your Name <you@example.com>
 * @license   http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
```

The context: add your keys inside the `$templatecontext` array, in one block, with a comment. Prefix the key
names with the theme name so a later Boost key cannot collide.

```php
$templatecontext = [
    // ... Boost's keys, unchanged ...
    'addblockbutton' => $addblockbutton,
    // Added by theme_mytheme.
    'mythemebanner' => format_string(
        (string) get_config('theme_mytheme', 'bannertext'),
        true,
        ['context' => \core\context\system::instance()],
    ),
];

echo $OUTPUT->render_from_template('theme_mytheme/course', $templatecontext);
```

The last line: render your template name.

Notes:

- Boost's file ends the array with `'addblockbutton' => $addblockbutton` and no trailing comma. phpcs with the
  moodle standard reports that line in a plugin (run on 5.3.0). Add the comma and list it as a modification.
- Use `get_config('theme_mytheme', 'name')`, not `$PAGE->theme->settings->name`. In a child of your theme the
  settings object belongs to the child, so the value is missing there.
- `format_string()` output is already escaped, so the template prints it with triple braces. Text from a rich
  text setting goes through `format_text()` with a context instead.
- When the theme adds many things, put each feature's context code in its own include
  (`layout/includes/banner.php`, each adding keys to `$templatecontext`) and `require_once` them from the layout
  file. The copied file then differs from upstream by a few `require_once` lines. This is how the largest Boost
  child theme keeps a layout with twenty additions mergeable.
- A layout file is included inside a renderer method. `return` at the top level ends the include, not the
  request.

## The template

```mustache
{{!
    @template theme_mytheme/course

    Copied from theme_boost/drawers (Moodle 5.3.0); the untouched original is kept beside this file as
    course.mustache.upstream. Modifications compared to the original:
    * the course banner is shown above the page header when mythemebanner is set.

    Context variables required for this template:
    * (keep the original list here)
    * mythemebanner - Banner text, already formatted; empty for none

    Example context (json):
    {
        "sitename": "Moodle",
        "output": {
            "doctype": "<!DOCTYPE html>",
            "page_title": "Test page",
            "favicon": "favicon.ico",
            "main_content": "<h1>Headings make html validators happier</h1>"
        },
        "bodyattributes": "",
        "sidepreblocks": "<h2>Blocks html goes here</h2>",
        "hasblocks": true,
        "courseindexopen": true,
        "blockdraweropen": true,
        "regionmainsettingsmenu": "",
        "hasregionmainsettingsmenu": false,
        "addblockbutton": "",
        "mythemebanner": "Welcome"
    }
}}
```

and the one addition, placed just above `{{{ output.full_header }}}`:

```mustache
{{#mythemebanner}}
    <div class="mytheme-banner" data-region="mytheme-banner">{{{mythemebanner}}}</div>
{{/mythemebanner}}
```

Rules for the template copy:

- Keep the GPL comment, the `@template` line (with your template name) and the example context. Add your new
  keys to the example context.
- Keep every `output.*` call, every element id and the `{{#js}}` block at the end that loads
  `theme_boost/loader` and `theme_boost/drawer`. Drawers, tooltips and dropdowns are started from there.
- Keep including Boost's partials by name (`theme_boost/head`, `theme_boost/navbar`, `theme_boost/drawer`,
  `theme_boost/footer`). Do not copy them too unless you change them.
- Give new elements a `data-region` attribute. Tests and scripts then have a stable hook that is not a style
  class.
- Do not put Mustache tag syntax or `}}` in a comment.

## Supporting 5.2 and 5.3 with one template

The 5.2 and 5.3.0 versions of `drawers.mustache` differ in two hunks only (`diff` of the two files):

1. The course index controls are passed to `theme_boost/drawer` in the block `drawerheadercontent` on 5.2 and
   `drawercontrols` on 5.3.
2. Secondary navigation is `{{> core/moremenu}}` on 5.2 and `{{> core/secondarymoremenu}}` on 5.3.

A copy that works on both:

```mustache
{{#courseindex}}
    {{< theme_boost/drawer }}
        {{$id}}theme_boost-drawers-courseindex{{/id}}
        {{$drawerheading}}{{> theme_boost/courseindexdrawerheading}}{{/drawerheading}}
        {{$drawerheadercontent}}{{> theme_boost/courseindexdrawercontrols}}{{/drawerheadercontent}}
        {{$drawercontrols}}{{> theme_boost/courseindexdrawercontrols}}{{/drawercontrols}}
        {{! the remaining blocks, unchanged }}
    {{/ theme_boost/drawer}}
{{/courseindex}}
```

```mustache
{{#secondarymoremenu}}
    <div class="secondary-navigation d-print-none">
        {{#reactprops}}{{> core/secondarymoremenu}}{{/reactprops}}
        {{^reactprops}}{{> core/moremenu}}{{/reactprops}}
    </div>
{{/secondarymoremenu}}
```

Why it works, and how sure this is:

- An unknown block name is ignored by the parent template, so each version of `theme_boost/drawer` uses the one
  block it defines.
- `reactprops` is a key of the array returned by `core\navigation\output\more_menu::export_for_template()` on
  5.3.0 (`public/lib/classes/navigation/output/more_menu.php`) and does not exist in 5.2. Inside
  `{{#secondarymoremenu}}` it is therefore truthy on 5.3 and missing on 5.2.
- Mustache compiles a partial to a call that runs only when the surrounding section is rendered, so
  `core/secondarymoremenu` is never looked up on 5.2. Without the switch the finder throws
  `moodle_exception('filenotfound')`, which the Mustache engine does not catch (it catches only its own
  unknown-template exception).
- All of this was read in both sources. It was not run on 5.2. Whether the Mustache lint on a 5.2 checkout
  accepts a template that names a 5.3-only partial inside a false section is not known; check the first CI run.
- If you prefer the switch in PHP, add `'mythemereactnav' => !empty($secondarynavigation['reactprops'])` to the
  context and test that key instead.

Everything else the copied template uses exists under the same name in both versions: the partials
`theme_boost/head`, `theme_boost/navbar`, `theme_boost/drawer`, `theme_boost/footer`,
`theme_boost/courseindexdrawerheading`, `theme_boost/courseindexdrawercontrols`, `core/local/toast/wrapper`,
`core/activity_header`, `core/tertiary_navigation_selector`, and the renderer calls.

A theme that also copies `navbar.mustache` needs the same switch there for `core/primarymoremenu`, and should keep
the 5.3 colour mode block; on 5.2 the method does not exist and the section renders nothing:

```mustache
{{# output.colour_mode_menu }}
    {{{ . }}}
    <div class="divider border-start h-75 align-self-center mx-1"></div>
{{/ output.colour_mode_menu }}
```

When copied files multiply, switch to one branch per Moodle version, each with
`$plugin->supported = [503, 503];` (or `[502, 502]`) in `version.php`, and twins taken from that version.

## At every Moodle release

1. For each `.upstream` file, diff it against the same file in the new Moodle:
   `diff public/theme/boost/templates/drawers.mustache public/theme/mytheme/templates/course.mustache.upstream`
   (run from the Moodle root).
2. No output: nothing to do for that file.
3. Output: apply the same change to the working copy by hand, then replace the `.upstream` file with the new
   original, and update the version named in the header comment.
4. Record it in the change log, one line per file ("Adopt upstream changes to drawers.mustache from 5.3").
5. Search the theme for the phrase used in the header comments ("Copied from") to find copies that have no twin:
   PHP methods copied from a core renderer, SCSS blocks copied from Boost.
6. Check the page types that use the layout in a browser at phone and desktop width, with a course that has
   secondary navigation with an overflow menu, blocks, and an activity with a tertiary navigation selector.
   A missed upstream change usually breaks one of those, on pages the theme's own tests do not visit.

Keep the list of files in `UPGRADE.md` in the theme, so the step does not depend on memory:

```text
Upstream files to compare at each Moodle release
- theme/boost/layout/drawers.php        -> layout/course.php (twin: layout/course.php.upstream)
- theme/boost/templates/drawers.mustache -> templates/course.mustache (twin: templates/course.mustache.upstream)
- lib/templates/notification_info.mustache -> wrapped with "!" in templates/core/notification_info.mustache (no copy)
```

## A template override needs the same care

An override under `templates/core/` or `templates/theme_boost/` that copies markup is a copy too. Give it a twin
(`templates/core/user_menu.mustache.upstream`) and the same header comment. An override that only wraps the
original with `{{> core/name! }}` needs no twin, because it contains none of the original's markup.

Core templates that themes often override and that changed between 5.2 and 5.3.0 (`diff -rq` of
`public/lib/templates`): `user_menu`, `user_action_menu_items`, `loginform`, `modal`, the `notification*`
templates, `block`, `activity_header`, `editswitch`. A copy of any of these taken from 5.2 needs a re-diff for 5.3.
