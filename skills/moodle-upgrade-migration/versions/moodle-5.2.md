# Moodle 5.2: what a port has to know

Read this when the plugin's supported range starts at 5.2 (the baseline) or you are moving a plugin up from 5.1
or earlier.

Read in the 5.2 source (a 5.2.2+ build, `public/version.php`), its `public/admin/environment.xml` and the `## 5.2`
section of the root `UPGRADING.md`; not run unless stated.

## Release facts

| Item | Value |
|---|---|
| Branch | `502`, `MOODLE_502_STABLE` |
| 5.2.0 `$version` | `2026042000`, so `$plugin->requires = 2026042000;` |
| PHP | 8.3.0 minimum; 8.4 supported |
| Databases | PostgreSQL 16, MySQL 8.4, MariaDB 10.11, SQL Server 2019 (15.0); no Oracle (since 5.0) |
| Upgrade from | 4.4 or later |

## Removed or changed in 5.2 that a 5.1 CI matrix never shows

| Change | Symptom | Fix | Source |
|---|---|---|---|
| `ASSIGN_ATTEMPT_REOPEN_METHOD_NONE` removed | `Error: Undefined constant` | Use the remaining `ASSIGN_ATTEMPT_REOPEN_METHOD_*` constants; guard with `defined()` if you still support 5.1 | MDL-87425 |
| `course_delete_module()`, `duplicate_module()`, `moveto_module()` deprecated | "has been deprecated" debugging; Behat steps fail on it | `\core_courseformat\formatactions::cm($courseid)->delete($cmid)`, `->duplicate($cmid)`, `->move_before($cmid, $beforecmid)`, `->move_end_section($cmid, $sectionid)` | MDL-86856, MDL-86858, MDL-86854; `public/course/lib.php` |
| `qbank_helper::get_question_structure()` returns `qtype = null` for random slots (was `'random'`), with `->random = true` | Random slots treated as missing questions | Test `!empty($slot->random)` | `public/mod/quiz/classes/question/bank/qbank_helper.php` |
| AMD `core/modal_factory`, `core/modal_registry` removed | The module fails to load in the browser | `core/modal` and subclasses' `create()` | MDL-79182 |
| `moodle-core-notification-confirm` YUI module removed | JS error | `core/notification` `saveCancelPromise()` or `core/modal_save_cancel` | `UPGRADING.md` 5.2 |
| `M.util.set_user_preference()` removed | JS error | `core_user/repository` `setUserPreference()` | MDL-87425 |
| `mod/assign/renderer.php` removed | Fatal on `require_once` of it | `\mod_assign\output\renderer` autoloads | MDL-87425 |
| Core string `datechanged` deprecated | Debugging when a course reset status uses it | Use your module's own string | deprecated since 4.5: listed in `lang/en/deprecated.txt` at the 4.5.0 tag, not at 4.4.0 |
| Fresh installs have `enablemyhome = 0` (existing sites get 1 by an upgrade step) | `/` sends logged-in users to their start page; Behat "I am on site homepage" lands elsewhere | `set_config('enablemyhome', 1)` in the test or site setup when the site home is needed | `public/admin/settings/appearance.php`, `public/lib/db/upgrade.php` step `2026022700.01` |

The fixes above are valid on 5.2 and 5.3. The `cmactions` methods `delete()`, `duplicate()`, `move_before()` and
`move_end_section()` are new in 5.2: at the 5.1.0 tag the class has only `rename()`, `set_visibility()` and
`set_groupmode()`. A plugin that also supports 5.1 guards each call with
`method_exists(\core_courseformat\local\cmactions::class, 'delete')`.

## The 5.2 functions a 5.3 port deprecates

Code that is right on 5.2 and emits notices on 5.3 (the `user/lib.php` functions, `get_return_section()`,
`theme_boost/bootstrap/*` imports and more) is listed in `moodle-5-3-changes`. While 5.2 is in the supported range,
keep the 5.2 call behind a `method_exists()` / `class_exists()` test for the 5.3 replacement.
