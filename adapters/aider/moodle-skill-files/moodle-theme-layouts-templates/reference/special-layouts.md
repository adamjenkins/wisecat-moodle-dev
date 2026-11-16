# Maintenance, secure, login, embedded, popup and redirect layouts

Read this when the theme touches the `maintenance`, `secure`, `login`, `embedded`, `popup` or `redirect` layouts,
or when something a theme adds to every page must be kept off them.

Read in `public/theme/boost/layout/`, `public/theme/boost/templates/`, `public/lib/pagelib.php` and
`public/lib/classes/output/` on 5.3.0. The layout files are identical in 5.2. None of these layouts was replaced
and run; treat the recipes as read in the source.

## Why these are different

A theme usually changes the drawers layout and forgets that six other page layouts render through four other
files. Anything added by copying `drawers.mustache` is missing from them; anything added through a hook or
through `theme_boost/footer` is present on some of them. Decide per layout.

| Layout | File and template | Navbar | Footer | Blocks | Used for |
|---|---|---|---|---|---|
| `maintenance` | `maintenance.php`, `theme_boost/maintenance` | none | `theme_boost/footer` | none | Install, upgrade, maintenance mode |
| `secure` | `secure.php`, `theme_boost/secure` | `theme_boost/navbar-secure` (logo, language menu, login info; no links out) | minimal, own markup | `side-pre`, inline beside the content | Quiz attempts in a secure window or Safe Exam Browser |
| `login` | `login.php`, `theme_boost/login` | none | `theme_boost/footer` | none | Login, sign-up, password reset |
| `embedded` | `embedded.php`, `theme_boost/embedded` | none | none | fake blocks only | Pages inside an iframe |
| `redirect` | `embedded.php`, `theme_boost/embedded` | none | none | none | The redirect notice |
| `popup`, `frametop`, `print` | `columns1.php`, `theme_boost/columns1` | none | none | none | Pop-up windows, legacy frames, print views |

## Maintenance

The maintenance layout renders while the site may have no database, no caches and no session.

- **It gets a different renderer.** When the page layout is `maintenance`, `moodle_page::get_renderer()` forces the
  rendering target to maintenance, and the renderer factory tries classes with the `_maintenance` suffix first:
  the theme's, then core's `core_renderer_maintenance`, and only then the theme's plain `core_renderer`
  (`public/lib/classes/output/renderer_factory/theme_overridden_renderer_factory.php`). Core's class exists, so a
  theme's `core_renderer` is not used on this layout.
- **Consequence for templates:** a custom `{{{output.mytheme_method}}}` renders as empty there, with no error,
  because the method does not exist on `core_renderer_maintenance`. To change renderer output on this layout a
  theme ships `theme_mytheme\output\core_renderer_maintenance extends \core_renderer_maintenance`.
- **`core_renderer_maintenance` blanks what needs the database:** `block()`, `blocks()`, `blocks_for_region()`,
  `course_content_header()`, `course_content_footer()`, `course_header()`, `course_footer()`, `custom_menu()`,
  `file_picker()`, `lang_menu()` and `login_info()` all return an empty string
  (`public/lib/classes/output/core_renderer_maintenance.php`).
- **The layout file must make no database or cache call.** Boost's own file calls `format_string($SITE->shortname,
  true, ["escape" => false])` with no context for that reason. In a copied maintenance layout: no
  `get_config()`, no `context_*::instance()`, no `get_user_preferences()`, no `$OUTPUT->blocks()`, no navigation.
- **Hook callbacks and `theme_mytheme_page_init()` still run** on maintenance pages. A callback that reads a
  setting or queries the database can break the upgrade screen. Guard with `during_initial_install()` and
  `$PAGE->pagelayout === 'maintenance'` before doing anything.
- **The theme's `config.php` also runs during install.** A `get_config()` there needs a `during_initial_install()`
  guard (`moodle-theme-development`).

If the theme only restyles, leave this layout alone. Boost's template already prints the page heading and the
content in a plain container, and the theme's SCSS applies to it. Rules can be scoped with `body.pagelayout-maintenance`.

## Secure

- Used for quiz attempts with a secure browser setting. The point of the layout is that nothing leads out of the
  attempt: no primary navigation, no user menu, no breadcrumb, no footer links.
- Blocks in `side-pre` are shown inline in a `[data-region="blocks-column"]` beside `#region-main`, not in a
  drawer. The quiz navigation block is a fake block and appears there.
- The navbar partial is `theme_boost/navbar-secure`. It calls `output.secure_layout_language_menu` and
  `output.secure_layout_login_info`.
- Boost sets `'activityheader' => ['notitle' => false]` in the entry, so the activity title is shown here even
  though `$THEME->activityheaderconfig` hides it elsewhere.
- A theme that adds links, a banner with links, a help widget or a custom menu through a hook must skip this
  layout: `if ($PAGE->pagelayout === 'secure') { return; }`. Symptom when it is not skipped: students can leave a
  secure quiz attempt through the theme's own link.
- If the theme overrides `theme_boost/footer` or `theme_boost/navbar`, the secure layout is not affected: it uses
  neither.

## Login

- `layout/login.php` passes `sitename`, `output`, `bodyattributes` and `leftinstructions` (the formatted
  `$CFG->auth_instructions`, or null) and renders `theme_boost/login`, which includes `core/login_layout`.
- `core/login_layout` and `core/login_panel` exist only in Boost (`public/theme/boost/templates/core/`); core has
  no file of that name. A child overrides them at `templates/core/login_layout.mustache` and
  `templates/core/login_panel.mustache`. `core/login_panel` is the left panel and is the intended place for a
  theme's own welcome content.
- The form itself is `core/loginform`, rendered by `core_renderer::render_login()`.
  **5.2 only:** Boost overrides it at `public/theme/boost/templates/core/loginform.mustache` and has its own
  `render_login()`. **5.3+:** the template lives in core (`public/lib/templates/loginform.mustache`) with changed
  markup, and Boost's `render_login()` is gone. A child's `templates/core/loginform.mustache` wins on both
  versions, but a copy taken from one version must be re-diffed for the other.
- The login page background image is CSS, produced by Boost's extra SCSS callback from the
  `loginbackgroundimage` setting (`moodle-theme-scss`, `moodle-theme-settings`), not markup.
- The footer partial is included, so anything added to `theme_boost/footer` shows on the login page.
- Body class: `pagelayout-login`. Users here are not logged in: `notloggedin` is also set, and
  `get_user_preferences()` returns defaults.

## Embedded and redirect

- `embedded` pages sit inside an iframe or object and need all the space: no navbar, no header, no footer.
  `$CFG->additionalhtmltopofbody`, `additionalhtmlfooter` and `additionalhtmlbottomofbody` are skipped on this
  layout by core.
- `layout/embedded.php` renders `side-pre` with fake blocks only
  (`$OUTPUT->blocks('side-pre', [], 'aside', true)`).
- `redirect` reuses the same file with no regions. It is the page shown between two requests; keep it free of
  anything slow.
- A hook callback that prints HTML at the top of the body or before the footer runs on these layouts too. Skip
  them by layout name, or the theme's banner shows inside every embedded frame.

## Popup, frametop and print

- All three render `theme_boost/columns1`: `#page-wrapper`, `#page`, `#page-content`, `#region-main-box`,
  `#region-main`, no navbar, no footer partial. `standard_end_of_body_html` is printed directly by the template.
- `print` sets `noactivityheader`, which `layout/columns1.php` reads to skip the activity header.
- `popup` and `frametop` set `nofooter`, which nothing reads; the template has no footer in any case.

## A guard for "every page" additions

```php
// classes/hook_callbacks.php (GPL header), in a callback for
// \core\hook\output\before_standard_top_of_body_html_generation.
public static function add_banner(\core\hook\output\before_standard_top_of_body_html_generation $hook): void {
    global $PAGE;

    if (during_initial_install()) {
        return;
    }
    // Only when this theme, or a child of it, is the active theme.
    if ($PAGE->theme->name !== 'mytheme' && !in_array('mytheme', $PAGE->theme->parents, true)) {
        return;
    }
    // Layouts that must stay bare.
    if (in_array($PAGE->pagelayout, ['maintenance', 'secure', 'embedded', 'redirect', 'popup', 'frametop', 'print'], true)) {
        return;
    }
    $hook->add_html(\core\output\html_writer::div(get_string('bannertext', 'theme_mytheme'), 'mytheme-banner'));
}
```

The hook registration, the active-theme guard and the list of output hooks belong to
`moodle-theme-renderers-output`. The layout list is the part that matters here.
