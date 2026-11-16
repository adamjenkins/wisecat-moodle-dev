# CI matrix: Moodle 5.2 (`MOODLE_502_STABLE`)

Requirement values for the 5.2 rows. Read in the 5.2.2+ tree, not run for this file; recheck on the branch before
relying on them (main file, section 3).

| What | Value | Source |
|---|---|---|
| PHP | 8.3 minimum, 8.4 highest | `<MOODLE version="5.2">` in `public/admin/environment.xml` (`PHP version="8.3.0"`); `.github/workflows/push.yml` ("lowest PHP supported" 8.3, "highest PHP supported" 8.4) |
| PostgreSQL | 16 minimum | same `environment.xml` block; core's own CI uses `postgres:16` (`push.yml`) |
| MariaDB | 10.11.0 minimum | same block |
| MySQL | 8.4 minimum | same block |
| Node for Grunt | `>=22.11.0 <23` (`.nvmrc`: `lts/jod`) | `package.json` `engines` |

Rows for a plugin supporting 5.2:

```yaml
          - {moodle-branch: MOODLE_502_STABLE, php: '8.3', database: mariadb}
          - {moodle-branch: MOODLE_502_STABLE, php: '8.4', database: pgsql}
```

with the service image defaults `postgres:16` and `mariadb:10.11`, so these rows test the branch at its minimum.

- PHP 8.2 must not appear with 5.2: the install environment check fails ("PHP version must be at least 8.3.0").
- `enablemyhome` defaults to 0 on new 5.2.2+ installs, which a CI site is; Behat features that need site home set
  it themselves (`moodle-behat-testing`).
