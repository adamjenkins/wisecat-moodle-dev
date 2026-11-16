# CI matrix: Moodle 5.3 (`MOODLE_503_STABLE`)

What the 5.3 rows need against the 5.2 baseline. Read in the 5.3.0 tree, not run for this file; recheck on the branch
before relying on them (main file, section 3).

| What | 5.3 value | Differs from 5.2 | Source |
|---|---|---|---|
| PHP | 8.3 minimum, 8.4 highest | no | `<MOODLE version="5.3">` in `public/admin/environment.xml`; `.github/workflows/push.yml` |
| PostgreSQL | 17 minimum | yes (5.2: 16) | same block; core's own CI uses `postgres:17` |
| MariaDB | 11.4.0 minimum | yes (5.2: 10.11.0) | same block |
| MySQL | 8.4 minimum | no | same block |
| Node for Grunt | `>=22.11.0 <23` | no | `package.json` `engines` |

Rows for a plugin supporting 5.3, each overriding the 5.2 image defaults of the main file's service block:

```yaml
          - {moodle-branch: MOODLE_503_STABLE, php: '8.3', database: mariadb, mariadb-image: 'mariadb:11.4'}
          - {moodle-branch: MOODLE_503_STABLE, php: '8.4', database: pgsql, pgsql-image: 'postgres:17'}
```

- **The database images are the trap.** A workflow that pinned `postgres:16` and `mariadb:10.11` for 5.2 and only
  adds `MOODLE_503_STABLE` to the branch list fails every 5.3 row at the install environment check. Give the 5.3 rows
  their own image values, or raise the shared pins to `postgres:17` and `mariadb:11.4` and accept that 5.2 is no
  longer tested at its minimum.
- **MariaDB 11.4 has no `mysqladmin`**, so a `mysqladmin ping` health check that worked with 10.11 never turns
  healthy on the 5.3 rows; use `healthcheck.sh --connect --innodb_initialized`.
- Grunt output can differ from 5.2's toolchain even with the same Node range; keep the Grunt step on one branch.
- **5.3+:** `php public/admin/tool/phpunit/cli/util.php --snapshot` and `--restore` can cache an initialised core test
  site between jobs; the options do not exist on 5.2 (`moodle-phpunit-testing`, its 5.3 version notes).
- Behat on 5.3 can also run in dark mode (`init.php --colourmode=dark`); moodle-plugin-ci 4.5.11 has no option for it,
  so a dark-mode row needs its own step (`moodle-theme-testing-release`).
