# PHPUnit testing: what is specific to Moodle 5.3

Against the 5.2 baseline. Read in the 5.3.0 source and its `UPGRADING.md`, not run for this skill. The full 5.3
catalogue is in `moodle-5-3-changes`.

## Test tooling

- **`public/admin/tool/phpunit/cli/util.php` gains `--snapshot[=NAME]`, `--snapshot --list`, `--restore=NAME` and
  `--upgrade`.** A CI job can cache an initialised core test site, restore it, and upgrade only the plugin, instead
  of installing from scratch. `--restore` takes the exact name printed by `--snapshot --list`, not the short name
  given to `--snapshot=NAME` (the script's own help text). The "initialised for different version" error also
  offers `util.php --upgrade` on 5.3. The 5.2 `util.php` has `--drop`, `--install`, `--buildconfig`,
  `--buildcomponentconfigs`, `--diag` and `--run` only; a script that passes the new options to 5.2 fails.
- **`advanced_testcase::get_testable_command($name)`** returns a Symfony `CommandTester` for a command registered with
  the new `bin/moodle` console (`\core\cli\application`). Neither exists on 5.2.

## Routed controllers

`\core\tests\router\route_testcase` adds assertions for the 5.3 route scope attributes (`#[scopeset]`,
`#[unscoped_resource]` in `\core\router\scope`): `assert_route_is_unscoped()`, `assert_route_is_scoped()`, `assert_route_required_scopes()`,
`assert_route_authorized_with_scopes()` and `assert_route_not_authorized_with_scopes()`
(`public/lib/tests/classes/router/route_testcase.php`). A test that calls them cannot run on 5.2; put it in a file
that is skipped there, for example by checking `method_exists()` in `setUp()` and calling `markTestSkipped()`.

## Dependency injection you can mock

- Password and authentication functions delegate to `\core\authentication\password` and `\core\authentication`
  (MDL-88580): `get_auth_plugin()`, `is_enabled_auth()`, `exists_auth_plugin()` and the password helpers. Replace them
  in a test with `\core\di::set(\core\authentication::class, $mock)`. On 5.2 they are plain functions and cannot be
  replaced.
- Properties marked `#[\DI\Attribute\Inject]` are filled when the object comes from `\core\di::get()` or
  `\core\di::make()` (MDL-89528). A test that builds the object with `new` gets null properties; build it through
  `\core\di::make()`.

## Admin setting classes

The `admin_settingpage`, `admin_setting_*` and related classes moved out of `public/lib/adminlib.php` into the
`core_admin` component and autoload under their old names (`public/lib/db/legacyclasses.php`). `admin_get_root()`
and the other functions stay in `adminlib.php`, so a test still requires that file.

The numeric-entity change in `block_myoverview` output (MDL-79755) is not 5.3-specific: it is in 5.2.2 too, so it is
in the skill body.
