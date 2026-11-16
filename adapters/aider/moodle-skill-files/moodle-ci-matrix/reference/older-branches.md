# Branches before Moodle 5.2

Read this when the matrix includes Moodle 5.1 or earlier, or you need the requirement values for a branch before
5.2.

The skills support 5.2 and later; these rows are for plugins that still test older branches. Recheck each value on
the branch itself before relying on it (main file, section 3).

| Branch | PHP (min to max) | MariaDB min | PostgreSQL min | MySQL min |
|---|---|---|---|---|
| `MOODLE_405_STABLE` (4.5) | 8.1 to 8.3 | 10.6.7 | 13 | 8.0 |
| `MOODLE_500_STABLE` (5.0) | 8.2 to 8.4 | 10.11.0 | 14 | 8.4 |
| `MOODLE_501_STABLE` (5.1) | 8.2 to 8.4 | 10.11.0 | 15 | 8.4 |

How they were read: the minimums from the `<MOODLE version="X.Y">` blocks of `public/admin/environment.xml` in the
5.2 and 5.3.0 trees, which hold a block for every earlier release; the PHP range from core's
`.github/workflows/push.yml` at each branch's `vX.Y.0` tag ("lowest PHP supported" on the MySQL job, "highest PHP
supported" on the PostgreSQL job). A later point release on a branch can raise its highest PHP, so read the
branch head when it matters.

- **The file moved in 5.1.** On 5.0 and earlier it is `admin/environment.xml`; on 5.1 and later
  `public/admin/environment.xml`. A script that reads one path for every branch fails on the other half.
- **Pairs that must never appear:** PHP 8.4 with 4.5 (its highest supported PHP is 8.3); PHP 8.1 with 5.0 or later;
  PHP 8.2 with 5.2 or later.
- **Service images across 4.5 to 5.2** together: `postgres:16` is not the 4.5 minimum (13) but satisfies every
  branch from 4.5 to 5.2; to test each branch at its own minimum, use per-row image values as in the main file.
- **Plugin CLI paths differ.** Before 5.1 there is no `public/` directory: `admin/tool/phpunit/cli/init.php`, not
  `public/admin/tool/phpunit/cli/init.php`. moodle-plugin-ci handles this itself; hand-written steps must not.
- **moodle-cs coverage attributes.** When phpcs knows the branch is below 5.0 (it does in CI, where the plugin sits
  inside the Moodle checkout), `#[CoversClass]` attributes do not count as coverage information (moodle-cs 3.7.0,
  `AbstractTestCaseSniff::shouldCheckTestCaseAttributes()`); a test that must pass phpcs on 4.5 keeps an `@covers`
  docblock tag as well.
