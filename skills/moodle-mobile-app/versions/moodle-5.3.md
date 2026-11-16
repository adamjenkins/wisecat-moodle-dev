# Moodle 5.3: app-related changes on the site

What changes for app support on a 5.3 site against the 5.2 baseline. Read it when a plugin with app support must run
on 5.3, or when a script or test logs in through `login/token.php`. Read in the 5.3.0 source and `UPGRADING.md`
files; not run.

## Token endpoint (`public/login/token.php`)

- Username and password are accepted only as POST parameters: a GET with them in the query string throws
  "Username and password can only be sent via POST parameters for security reasons." (`login/token.php:38`). On 5.2
  a GET worked, so test scripts and CI helpers written for 5.2 break.
- The service is checked before the user is authenticated, so an unknown or disabled service fails before any login
  attempt.
- The `appsitecheck` parameter is gone (5.2 answered `{"appsitecheck": "ok"}` before authenticating,
  `login/token.php:39-40` on 5.2).

Source: `public/lib/UPGRADING.md` 5.3, MDL-87010.

## Deep-link auto-login

`tool_mobile/enabledeeplinkautologin` (new, default off) controls whether a deep link that carries a token and
private token logs the user in automatically (`public/admin/tool/mobile/settings.php:577`, MDL-88924; not in the 5.3.0 upgrade notes). A plugin that
generates app deep links for automatic login needs that setting on, and should say so in its documentation.

## Web services returning course modules

Core's course-module web services (`core_course`, forum, H5P activity, assign) now all return the standard module
fields from `\core_course\external\helper_for_get_mods_by_courses::standard_coursemodule_elements_returns()`
(`lang`, `section`, `visible`, `groupmode`, `groupingid`, ...) (`public/course/UPGRADING.md` 5.3, MDL-87241). The
helper exists on 5.2 too; an activity's own `get_<mod>s_by_courses` should use it on both versions so the app gets
the same shape.

## Other web service changes the app uses

- New `mod_forum_set_read_state` (`public/mod/forum/UPGRADING.md`, MDL-87887).
- `gradereport_user_get_grade_items` takes an optional `parentcategoryid` (`public/grade/report/user/UPGRADING.md`,
  MDL-64304).

The full list of 5.3 changes is in `moodle-5-3-changes`.
