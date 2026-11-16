# Example Prompts

Real prompts that activate this plugin's skills. Drop into Claude Code after installing `wisecat-moodle-dev`.

## Scaffolding

1. **New local plugin**
   > Scaffold `local_announcements` — admins post a banner, users dismiss per-session. Settings page for max length. Capability `local/announcements:manage`.

2. **New activity module**
   > Create `mod_flashcard` — instances hold a deck, students get spaced repetition. Include `mod_form.php`, `view.php`, `lib.php` with `add_instance`/`update_instance`/`delete_instance`, gradebook integration.

3. **New block**
   > Build `block_recent_certificates` showing the user's last 5 issued certificates with download link. Configurable max count, applicable on dashboard + course pages.

4. **New course format**
   > Generate `format_kanban` — sections render as Kanban columns, AJAX drag-drop reorders sections via web service.

5. **New auth plugin**
   > Scaffold `auth_magiclink` — passwordless email login. Includes login form override, token table, scheduled task purging expired tokens.

6. **New question type**
   > Create `qtype_drawing` — student draws on canvas, teacher grades manually. Include `questiontype.php`, `question.php`, `renderer.php`, edit form.

## Database / XMLDB

7. **Add a column**
   > Add a nullable `metadata` LONGTEXT to `local_announcements_posts`, bump version, write the upgrade step.

8. **Add an index**
   > Add a composite index on `(courseid, timecreated)` to `local_attendance_records` table. Update install.xml + upgrade.php.

9. **Rename a field safely**
   > Rename `local_foo.deleted` → `local_foo.is_deleted` across install.xml, upgrade.php, and all PHP usages.

## Capabilities + security

10. **Add capability**
    > Add `local/attendance:export` capability defaulting to allow for `editingteacher` and `manager`. Wire `require_capability` into `cli/export.php`.

11. **Security audit**
    > Audit `public/local/attendance/index.php` — flag missing `require_login`, `require_capability`, `require_sesskey`, raw `$_GET`, SQL injection, XSS.

12. **Add CSRF protection**
    > This POST handler updates DB but doesn't check sesskey. Fix it the Moodle way.

## Privacy / GDPR

13. **Null privacy provider**
    > Add a privacy provider for `local_announcements` — stores no user data.

14. **Full provider**
    > `local_attendance` stores user attendance records keyed by userid. Generate full privacy provider with `get_metadata`, `get_contexts_for_userid`, `get_users_in_context`, `export_user_data`, `delete_data_for_all_users_in_context`, `delete_data_for_user`, `delete_data_for_users`, and a provider test.

15. **Privacy review**
    > Review `classes/privacy/provider.php` against the schema in `db/install.xml` — does it cover all user-identifying columns?

## Web services / AJAX

16. **External function**
    > Add `local_attendance_mark_present` web service — params: `(int sessionid, int userid)`, returns `(bool success, string message)`. Wire `db/services.php`, `classes/external/mark_present.php`, capability `local/attendance:mark`, ajax-callable.

17. **AJAX from AMD**
    > Wire an AMD module `local_attendance/marker` that calls the web service from #16 via `core/ajax`. ES module source in `amd/src/`, built into `amd/build/` with grunt.

18. **REST token**
    > Show how a 3rd party app authenticates to my Moodle and calls `local_attendance_mark_present` over REST.

## Hooks

19. **Listen on a hook**
    > Listen on `\core\hook\output\before_standard_top_of_body_html_generation` and inject a banner from `local_announcements` settings.

20. **Define a custom hook**
    > Define a custom hook `\local_announcements\hook\post_dismissed` and dispatch it when users dismiss a banner.

## Testing

21. **PHPUnit test**
    > Write `tests/manager_test.php` for `\local_attendance\manager::mark_present()`. Use `resetAfterTest`, `getDataGenerator`, assert DB state + raised event.

22. **Data generator**
    > Create `tests/generator/lib.php` for `local_attendance` — methods `create_session()`, `create_record()`.

23. **Behat scenario**
    > Behat scenario: a teacher in course "Maths 101" marks "Alice" as present in a new attendance session, page shows "1 present".

24. **Run tests**
    > How do I run only the PHPUnit suite for `local_attendance` and only one Behat scenario tagged `@local_attendance @critical`?

## AMD / JavaScript

25. **AMD module**
    > Build `local_attendance/marker` AMD module: ES6 source in `amd/src/marker.js`, calls `core/ajax`, displays toast via `core/toast`. Include grunt build instructions.

26. **Mustache + JS**
    > Render `templates/marker.mustache` from PHP with data, hydrate via AMD, add a click handler that POSTs back.

## Performance

27. **Add MUC cache**
    > `local_announcements\manager::get_active()` hits DB on every page. Cache it via MUC application cache, invalidate on settings change.

28. **Slow query**
    > This query is doing a full scan on `mdl_logstore_standard_log`. Suggest index + rewrite using `$DB->get_recordset_sql` to avoid memory blow.

29. **Ad-hoc task**
    > Sending email per record blocks request. Move to ad-hoc task via `\core\task\manager::queue_adhoc_task()`.

## Theme

30. **Boost child theme** (`moodle-theme-boost-child`)
    > Create `theme_campus`, a child of Boost for Moodle 5.2 and 5.3: our orange as the brand colour, rounder cards, a footer note. Keep Boost's brand colour and raw SCSS settings working under the child.

31. **A setting that changes the CSS** (`moodle-theme-settings`)
    > Add an accent colour setting to `theme_campus` with `admin_setting_configcolourpicker`. It must reach the compiled CSS as an SCSS variable, take effect when saved, and not break the site if someone stores a bad value.

32. **The theme looks like plain Boost** (`moodle-theme-scss`)
    > After my last SCSS change `theme_campus` renders as stock Boost and there is no error on the page. Find out why and show me how to see the compile error.

33. **One theme for 5.2 and 5.3** (`moodle-theme-scss`)
    > `theme_campus` has `@import "bootstrap/functions";` and `darken($card-bg, 5%)` in its SCSS. Will that work on Moodle 5.3? Fix it so the same file compiles on 5.2 and 5.3.

34. **Dark mode** (`moodle-theme-scss`)
    > An admin turned on Boost's colour modes on our 5.3 site and my child theme now shows white panels with light text. Make the theme follow the light and dark modes without breaking it on 5.2.

35. **Footer without copying a layout** (`moodle-theme-layouts-templates`)
    > Add a line of text above Boost's footer in `theme_campus` without copying `drawers.mustache`. The text comes from a theme setting.

36. **Own layout for course pages** (`moodle-theme-layouts-templates`)
    > Course pages in `theme_campus` need a banner region above the content. Add a layout file and template for the `course` layout and set them up so I can port them when Boost changes in the next Moodle version.

37. **Renderer override and hook** (`moodle-theme-renderers-output`)
    > In `theme_campus`, add a body class that depends on a setting, and a `theme-color` meta tag in the head. The meta tag must not appear when another theme is active.

38. **React navigation on 5.3** (`moodle-theme-layouts-templates`, `moodle-theme-renderers-output`)
    > My override of `core/moremenu` and my `.primary-navigation .nav-link.active` rule stopped working on Moodle 5.3. What can a theme still change in the primary navigation?

39. **Prove the theme works** (`moodle-theme-testing-release`)
    > Write a PHPUnit test that fails when `theme_campus` does not compile, and a Behat feature that runs in the theme's own suite and checks the banner on a course page as a student.

40. **Ship the theme** (`moodle-theme-testing-release`, `moodle-plugin-release`)
    > `theme_campus` is going to the Moodle Plugins directory. List what the package needs that CI does not check, and build and list the ZIP.

## Mobile app

41. **Mobile remote template**
    > Surface `local_attendance` UI in the Moodle Mobile app via `db/mobile.php` remote templates. Include a sample screen listing today's sessions.

## Upgrade / migration

42. **Cross-version upgrade**
    > My plugin is on Moodle 3.11 conventions. Upgrade it to run on 5.2 and 5.3: replace the bare `external_api` with `core_external\external_api`, move to PSR-4, add Hooks API where applicable, fix deprecated `print_error`, and set `$plugin->requires` and `$plugin->supported`.

43. **Moving to 5.3**
    > `local_attendance` supports 5.2. What does Moodle 5.3 remove or move that it uses, and what must change so one release supports `[502, 503]`?

## Code review

44. **PR review**
    > Review the diff in `public/local/attendance/` against Moodle coding standards — `phpcs`, security, privacy, version bumps, lang strings. Give a file and line for every finding.

45. **Theme review**
    > Review `public/theme/campus` before release: config keys, SCSS that must compile on 5.2 and 5.3, dark mode, hooks, copied templates, settings, tests and the package.

46. **Coding style**
    > Run `phpcs --standard=moodle public/local/attendance` and fix every reported issue.

## CLI

47. **CLI script**
    > Add `cli/recompute.php` for `local_attendance` — accepts `--courseid=N --dry-run`. Use `clilib.php`, exit codes, locks via `\core\lock\lock_config`.

## Slash commands

48. **Scaffold a Boost child theme**
    > `/moodle-new-theme campus "brand colour, rounder cards, a footer note"`

    Asks for anything missing (name, what the theme must change, supported versions, copyright holder), then writes the child theme from the theme skills. It writes files; it does not install or compile them.

49. **Check a theme without running it**
    > `/moodle-theme-check public/theme/campus`

    Reads the theme and reports each finding with `file:line`: restated config keys, import paths and colour functions that fail on one version, dark mode, hook guards, copied layouts, settings plumbing, tests, package files. It ends with what a static check cannot show (the compile, the page, the ZIP).

50. **Lint a theme's template overrides**
    > `/moodle-mustache-lint public/theme/campus/templates`

    For a theme it also checks override paths (`templates/<component>/`), the `!` include, and overrides that no longer have an effect on 5.3.

51. **Scaffold a plugin**
    > `/moodle-new-plugin local attendance`
