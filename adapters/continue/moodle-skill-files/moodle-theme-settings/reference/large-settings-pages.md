# Large settings pages, several pages, and themes that have children

Read this when a theme has more than a few dozen settings, needs more than one settings page or its own
capability, is meant to be a parent of other themes, or when you review the settings code of a large theme.

The core facts were read in the 5.2 and 5.3.0 source. The patterns come from reading two large public themes
built on Boost (one a child of Boost with several hundred settings, one a stand-alone theme that builds on Boost's
preset) and a published child of the first. Nothing in this file was run.

## How far the single tabbed page goes

`theme_boost_admin_settingspage_tabs` (the recipe in `SKILL.md`) is enough for a theme with up to a few dozen
settings. It is one HTML form: every tab's fields are drawn and saved together, so a validation error can sit on
a tab the admin is not looking at. Signs that the page is outgrown:

- The page is slow to draw because every tab runs its queries (file areas, course lists) on each load.
- Admins lose their place: after a successful save core redirects to the page URL, which has no `activetab`
  parameter, and the tabs class then opens the first tab (`public/admin/settings.php`,
  `public/theme/boost/classes/admin_settingspage_tabs.php`; read, not run).
- Many dependencies between fields. Each `hide_if()` adds to one JSON blob on the page.

## Keep `settings.php` thin

Whatever the size, the settings read better as one function or static method per tab that returns an
`admin_settingpage`, with `settings.php` only assembling them:

```php
// settings.php
defined('MOODLE_INTERNAL') || die();

if ($ADMIN->fulltree) {
    $settings = new theme_boost_admin_settingspage_tabs('themesettingmytheme', get_string('configtitle', 'theme_mytheme'));
    foreach (['look', 'banner', 'footer'] as $tab) {
        $settings->add(\theme_mytheme\local\settings::{$tab . '_tab'}());
    }
    \theme_mytheme\local\settings::add_dependencies($settings);
}
```

```php
// classes/local/settings.php
namespace theme_mytheme\local;

/** Builds the tabs of the theme settings page. */
class settings {
    /** The Look tab. */
    public static function look_tab(): \admin_settingpage {
        $page = new \admin_settingpage('theme_mytheme_look', get_string('looksettings', 'theme_mytheme'));
        $setting = new \admin_setting_configcolourpicker(
            'theme_mytheme/accent',
            get_string('accent', 'theme_mytheme'),
            get_string('accent_desc', 'theme_mytheme'),
            ''
        );
        $setting->set_updatedcallback('theme_reset_all_caches');
        $page->add($setting);
        return $page;
    }

    /** Dependencies between settings, recorded on the outer page. */
    public static function add_dependencies(\admin_settingpage $settings): void {
        $settings->hide_if('theme_mytheme/bannertext', 'theme_mytheme/bannermode', 'eq', 'none');
    }
}
```

(The sample shows one tab; `banner_tab()` and `footer_tab()` follow the same shape.) Each method returns a complete
tab, which satisfies the rule that a tab is added only after its settings, and the dependencies are recorded in one
place on the outer page, which is where `admin/settings.php` reads them.

Do not let the helper class grow into the place where settings are also read, SCSS is built and files are
imported. Two large themes each carry a single class or file of several thousand lines for that reason, and both
are hard to review.

## Several pages under the theme's own category

When one page is not enough, the theme adds an admin category and puts pages in it. Three things must still hold.

1. **`themesetting<name>` must lead somewhere.** The theme selector's cog always links to
   `admin/settings.php?section=themesetting<name>` (`public/admin/themeselector.php`). Either keep a real page of
   that name (the first of the theme's pages, replacing `$settings` as usual) and add the others to the category,
   or redirect: `settings.php` is included while the admin tree is being built, so a `redirect()` there, guarded by
   `$ADMIN->fulltree && $PAGE->has_set_url()` and a comparison of `$PAGE->url` with that section URL, runs before
   core reports the missing section (the pattern of one large public theme; read, not run). Keeping a real page
   is simpler and has no redirect during tree building.
2. **Pages in the category must exist when the tree is built without settings.** Core builds the tree with
   `$ADMIN->fulltree` false on ordinary pages, to draw the administration navigation and the search index of page
   names. A page that is created only inside `if ($ADMIN->fulltree)` is missing from the navigation. So: create the
   category and each `admin_settingpage` object in both cases, and fill the pages with settings only when
   `$ADMIN->fulltree` is true.
3. **Names are global.** Category and page names share one namespace with every other admin page. Prefix them
   with the component (`theme_mytheme_look`).

```php
defined('MOODLE_INTERNAL') || die();

$ADMIN->add('appearance', new admin_category('theme_mytheme', get_string('pluginname', 'theme_mytheme')));

// The page the theme selector links to. Core adds it under its own "themes" category after this file returns.
$settings = new admin_settingpage('themesettingmytheme', get_string('generalsettings', 'theme_mytheme'));
$lookpage = new admin_settingpage('theme_mytheme_look', get_string('looksettings', 'theme_mytheme'));

if ($ADMIN->fulltree) {
    $settings->add(new admin_setting_configtext(
        'theme_mytheme/bannertext',
        get_string('bannertext', 'theme_mytheme'),
        get_string('bannertext_desc', 'theme_mytheme'),
        '',
        PARAM_TEXT
    ));
    $setting = new admin_setting_configcolourpicker(
        'theme_mytheme/accent',
        get_string('accent', 'theme_mytheme'),
        get_string('accent_desc', 'theme_mytheme'),
        ''
    );
    $setting->set_updatedcallback('theme_reset_all_caches');
    $lookpage->add($setting);
}

$ADMIN->add('theme_mytheme', $lookpage);
```

Core adds `$settings` itself (`public/admin/settings/appearance.php`); the theme adds only its extra pages. Because
`$settings` is created outside the `fulltree` test here, it is also in the navigation tree, as an empty shell.
This layout was read against the core code and not run: check the navigation and both pages in a browser when
using it.

### A capability of its own

An `admin_settingpage` takes a capability as its third constructor argument, so a theme can define
`theme/mytheme:configure` in `db/access.php` and pass it. Know the limit first: core includes theme `settings.php`
files only inside a block that requires site config or one of two other capabilities
(`moodle/my:configsyspages`, `moodle/tag:manage`; `public/admin/settings/appearance.php`, 5.2 and 5.3, read in the
source). A user who holds only the theme's capability never gets the file included, so the pages do not exist for
them. A delegated "theme manager" role needs one of those capabilities as well, or the theme must offer its own
page outside the admin tree.

## Patterns worth copying

- **One name for the function that reads a setting.** A small helper that takes the key and a default, and reads
  `get_config('theme_mytheme', $key)`, keeps the "missing value means default" rule in one place and gives a
  single point to add per-course or per-category overrides later.
- **Read the theme's own settings with `get_config()`, never through `$theme->settings`.** A parent theme's
  callbacks receive the active theme's object, so under a child theme `$theme->settings` holds the child's rows. A
  CI check that rejects `theme->settings->` in a diff keeps the rule in force.
- **String constants for select values.** Define the stored keys once (class constants) and use them in
  `settings.php` and in the reading code, instead of repeating `'yes'` and `'no'` literals.
- **Generated option lists** for sizes, percentages and durations (a helper that returns the array).
- **Settings grouped the way the SCSS is grouped.** One "post" SCSS file with a heading per settings tab makes it
  possible to find the rule a setting controls.
- **Feature includes for layouts.** Each feature that adds template context from settings lives in a small include
  or method that reads its settings and adds its keys; the layout file calls them one after another. JavaScript for
  a feature is requested only when its setting is on.
- **A Behat feature per settings tab**, named after the tab, that sets the setting and asserts the visible effect
  (`moodle-theme-testing-release`).
- **Turn off the CSS fallback right after a settings save.** A theme can set `$THEME->usefallback` to false in
  `config.php` when the referring page is `admin/settings.php`, so an admin who just saved a style setting is not
  shown the previous CSS once. Use `get_local_referer(false)` and compare the base URL.

## Patterns to avoid

| Pattern | Why it hurts | Instead |
|---|---|---|
| Three routes from settings to CSS (pre-SCSS variables, custom properties and a `[[setting:name]]` replacement pass) in one theme | The default of a setting is written in each route and the copies drift; the placeholder files are not valid SCSS, so they cannot be linted or compiled alone; core does not replace such placeholders, so a setting missing from the theme's own table is never substituted | One route per value; fallbacks as `!default` in SCSS |
| Reading settings in `config.php` to decide which block regions exist | Turning the setting off removes the region while blocks are still placed in it, and the theme then needs recovery code for orphaned blocks | Declare the regions always; hide an empty or disabled region in the layout |
| A setting whose value is a Mustache template or raw HTML fragment that replaces a core template | A typing error by an admin breaks every page; no lint, no review, no upgrade path | Template overrides in the theme; settings choose between prepared variants |
| Settings import from an uploaded file that writes config and files directly | A powerful write path that needs the same validation as the settings page and a security review | If needed, run each value through the setting object's `write_setting()` |
| Printing another setting's raw value in a settings description (`nl2br($value)`) | Unescaped admin input on an admin page | `s()` or `format_text()` |
| Hard-coding the theme directory or name in many helpers | Breaks under `$CFG->themedir` and for child themes | `$theme->dir`, `$theme->name`, `core_component::get_plugin_directory()` |
| Hard-coded English in settings code and upgrade messages | Untranslatable; flagged in review | Lang strings |
| A version test such as `$CFG->branch != 502` inside settings code | Wrong on every other supported branch | Compare with `>=`, or use `$plugin->supported` and drop the test |
| `purge_all_caches()` as the updated-callback of ordinary style settings | Every save empties every cache on the site | `theme_reset_all_caches`; a full purge only for a setting that changes the icon map or lang strings |

## When the theme will have child themes

A parent theme must decide, per setting, who owns the value.

- **Owned by the parent** (most settings): read with `get_config('theme_parent', ...)`. A child cannot override the
  value, and the parent's features keep working whatever the child declares.
- **Overridable by the child**: read with `$theme->settings->key ?? get_config('theme_parent', 'key')` in SCSS
  callbacks, and document the key. This is how Boost's `brandcolor`, `scsspre`, `scss`, `backgroundimage` and
  `loginbackgroundimage` behave, except that Boost has no fallback to its own value.

That missing fallback is the grandchild problem: when a child of a Boost child is active, Boost's callbacks read
the grandchild's settings, so the middle theme's `scsspre`, `scss` and `brandcolor` are skipped unless the
grandchild redeclares them or the middle theme adds them itself. One large theme handles it by calling
`theme_boost_get_pre_scss(theme_config::load('<itself>'))` and the extra-SCSS equivalent from its own callbacks
when it detects that a child of it is the active theme. If you write the middle theme, do the same; if you write
the grandchild, read the parent's documentation for which settings to redeclare (`moodle-theme-boost-child`).

Other points for parent themes:

- "Is this theme active" must include children: `$PAGE->theme->name === 'mytheme' ||
  in_array('mytheme', $PAGE->theme->parents)`.
- File settings of the parent are served by the parent's `pluginfile` and built with
  `theme_config::load('mytheme')->setting_file_url()`, not with the `$theme` passed to the callback.
- A child theme adds its page to the parent's admin category with `$ADMIN->add('theme_parent', $page)`. Theme
  settings files are included in alphabetical order of theme name (`core_component::get_plugin_list('theme')`), so
  this works only when the child's name sorts after the parent's; otherwise `add()` emits the debugging message
  "parent does not exist!", returns false, and the page is dropped (read in `admin_category::add()`, 5.2 and
  5.3.0; not run).
- Check each release that the parent does not force children to reimplement a setting: test with a minimal child
  theme active.

## Per-course or per-category values

Theme settings are site-wide. A theme that wants a value per course stores it in its own table (course id, name,
value), reads it through the same helper that reads the global value, caches it, adds the fields to the course
form through the course form hooks, and includes the table in course backup. That is plugin work, covered by
`moodle-plugin-development` and `moodle-hooks-api`; the part that belongs here is the rule that the global setting
remains the default and the helper is the only reader.
