# Which theme a page uses: the full selection order

Read this when a page shows the wrong theme, or when the task involves course, category, user or cohort themes,
`?theme=`, `$CFG->themeorder`, the theme usage report or uninstalling a theme.

Source: `moodle_page::resolve_theme()` and `initialise_theme_and_output()` in `public/lib/pagelib.php`,
`public/lib/setup.php`, `public/cohort/lib.php`, `public/admin/settings/appearance.php`,
`public/lib/classes/plugininfo/theme.php`, read in 5.3.0. `resolve_theme()` and the theme selector are identical
in the 5.2 source. Only the `?theme=` route was run, on 5.3.0.

## The order

| Step | Where the name comes from | Switch | Notes |
|---|---|---|---|
| before the order | `$PAGE->force_theme('name')` in the script | none | Must be called before the theme is initialised. Core intends it for the theme selector only |
| course | `course.theme` of the page's course | `allowcoursethemes` | Set in the course settings form, shown only when the switch is on |
| category | the nearest category of the page's course, walking upward, that has a `theme` | `allowcategorythemes` | Applies to course pages; set in the category edit form |
| session | `$SESSION->theme` | `allowthemechangeonurl` | Written by `?theme=name` on any URL. Read without checking the switch |
| user | `user.theme` | `allowuserthemes` | The user's preferred theme |
| cohort | `$USER->cohorttheme` | `allowcohortthemes` | See the cohort rules below |
| site | `$CFG->theme`, else `boost` | none | Chosen in the theme selector or forced in the site's `config.php` |

- All five switches are on the "Advanced theme settings" page under Site administration, Appearance, and are off
  on a new site. A theme name stored in a course, category, user or cohort does nothing while its switch is off.
- **`$CFG->themeorder`** can only be set in the site's `config.php`. It reorders or removes levels, for example
  `$CFG->themeorder = ['user', 'course', 'category', 'session', 'cohort'];` to let a user's accessibility theme
  win. Core always appends `site`.
- A user who arrived through MNet from a peer that forces a theme gets the peer's theme at the user and site
  steps.
- The list of themes offered in the course, user and cohort forms can be limited with the `themelist` setting on
  the same page: a comma-separated list of theme names. Empty means every installed theme.

## When the resolved theme cannot load

`theme_config::load()` tries the requested theme, then `$CFG->theme`, then `boost`. Each step down emits a
`debugging()` message at normal level: "This page should be using theme X which cannot be initialised. Falling
back to the site theme Y". With debugging off there is nothing to see except the wrong look.

A theme cannot be initialised when: its directory or `config.php` is missing; `$THEME->parents` is not an array;
a directly listed parent is missing or itself invalid; or the directory contains a legacy `styles.php`.

## The session theme and `?theme=`

- With `allowthemechangeonurl` on, `?theme=name` loads the theme and, only if it loads under that exact name,
  stores it in `$SESSION->theme`. A name that falls back clears the session theme instead.
- It then applies to every page of that session, above user and cohort themes and below course and category
  themes. It is not cleared by turning the switch off, because the switch is checked only when writing.
- Opening the theme selector page clears it. So does logging out.
- Use it to look at a theme that is installed but is not the site theme (run on 5.3.0). Turn the switch back off
  afterwards on any site other people use: every visitor can change their own theme while it is on.

## Cohort themes

- `$USER->cohorttheme` is filled only by `get_complete_user_data()`, which runs at login, for the guest user and
  on "log in as". It is not recalculated on each page. A changed cohort theme, or a changed membership, reaches a
  user at their next login.
- `cohort_get_user_cohort_theme()` returns a theme only when every one of the user's cohorts that has a theme
  names the same one. Two cohorts with different themes give no cohort theme at all, and the user falls through
  to the site theme. There is no "first cohort wins".

## The theme is fixed on first use

- The theme is resolved lazily, on the first access to `$PAGE->theme`, `$OUTPUT` or anything that renders. Core
  first sets the page's course to the site course if none was set.
- After that, `$PAGE->set_course()`, setting the category, and `$PAGE->force_theme()` throw
  `coding_exception: The theme has already been set up for this page ready for output. Therefore, you can no
  longer change the theme, or anything that might affect what the current theme is, for example, the course.`
  The exception's debug information carries the stack trace of where the theme was first initialised.
- Fix: call `require_login($course)` or `$PAGE->set_course()` and `$PAGE->set_context()` before the first use of
  `$OUTPUT`. Web service requests are exempt, because one request may handle several course contexts.
- An `output_fragment_*` callback runs after the fragment web service has validated the context and set up the
  output, so it must not call `require_login()` or set the course. It only checks capabilities. Calling the
  callback directly from a test does not show this; call it through the fragment web service or a browser test.
- Code that needs another theme's configuration without changing the page uses
  `\core\output\theme_config::load('name')`, which returns an independent object.

## Setting a theme from code

Use the API of the thing that owns the field. Each one clears the theme-usage cache; a direct `$DB` write does
not.

| Field | API |
|---|---|
| `course.theme` | `update_course()` in `public/course/lib.php` |
| `course_categories.theme` | `core_course_category::update()` |
| `cohort.theme` | `cohort_update_cohort()` |
| `user.theme` | `user_update_user()` from `public/user/lib.php`. **5.3+:** `\core\user::update_user()`; the old function is deprecated there |
| Site theme | `set_config('theme', 'name')`, as the theme selector does, after checking that `theme_config::load('name')->name === 'name'` |

- The admin's theme usage report at `/report/themeusage/index.php?themechoice=<name>` and the "used in" link in
  the theme selector come from `\core\output\theme_usage::is_theme_used_in_any_context()`, which counts a level
  only when its switch is on and caches the answer in the `core/theme_usedincontext` cache.

## The theme selector

- Lists every installed theme that loads under its own name, except those with `$THEME->hidefromselector = true`,
  which appear only in theme designer mode.
- Shows `pix/screenshot` and, in the preview dialog, the `choosereadme` string.
- Links to `admin/settings.php?section=themesetting<name>` when the theme has a `settings.php`. A theme that
  replaces the settings page object has to keep that section name or the link breaks; `moodle-theme-settings`
  covers it.
- When `$CFG->theme` is forced in the site's `config.php`, the selector shows a notice and offers no way to change
  the theme.

## Uninstalling

- Boost can never be uninstalled, and neither can the current site theme.
- On uninstall core blanks the theme name in `course`, `course_categories`, `user` and `mnet_host`, and removes
  the theme from `themelist`. Pages that used it fall back to the next level.
  **5.3+:** `cohort.theme` is blanked too; on 5.2 a cohort keeps the name of the removed theme.
- A theme that is another installed theme's dependency cannot be uninstalled until the dependant is removed; that
  is the standard plugin dependency rule driven by `$plugin->dependencies`.

## Device themes no longer exist

Separate themes for mobile, tablet or legacy devices cannot be offered. The `core_useragent` device-theme
functions, `theme_is_device_locked()` and the related settings were removed in 5.2, and `resolve_theme()` has no
device step (root `UPGRADING.md`, 5.2 section). Device detection itself remains. Advice that mentions
`thememobile` or `themetablet` is out of date.
