# moodle-ci-matrix

> Use when adding or updating a GitHub Actions workflow that runs moodle-plugin-ci for a Moodle plugin (.github/workflows/ci.yml from gha.dist.yml), choosing its Moodle branch x PHP x database matrix, or when CI fails at "Initialize containers", at moodle-plugin-ci install, with "requires at least PHP", an empty DB in a job, an artifact-name error, "No PHPUnit tests to run, free pass!", or green while the Plugins directory still rejects the plugin. Covers the upstream template and its steps, reading each branch's environment.xml and core push.yml, service image pins and health checks, include/exclude pitfalls, non-blocking rows for main, running the pipeline locally as written, secrets in logs, optional PHP extensions, and what a green run does not check. Skip when running PHPUnit or Behat locally with no workflow involved (moodle-phpunit-testing, moodle-behat-testing) or for theme-specific CI (moodle-theme-testing-release).

# Moodle plugin CI matrix (moodle-plugin-ci on GitHub Actions)

## Overview

`moodlehq/moodle-plugin-ci` runs Moodle's plugin checks (phplint, phpcs, phpdoc, validate, savepoints, mustache,
grunt, PHPUnit, Behat) against a real Moodle checkout, usually from GitHub Actions. The workflow is short; most
breakage comes from the matrix, a Moodle branch paired with a PHP or database version that branch does not support,
and from believing a green run proves more than it does. Verify every combination against a source.

How sure each statement is: the moodle-plugin-ci statements were read in the 4.5.11 source; branch requirements were
read in the 5.2 and 5.3.0 trees (`public/admin/environment.xml`, `.github/workflows/push.yml`); the template's
steps and images are as published with moodle-plugin-ci 4.5.11, so compare them with the file you fetch; the
workflow below was written for a plugin supporting 5.2 and 5.3 and has not been run for this skill. "Seen in
practice" marks failures observed on real plugin workflows.

## When to Use

- Adding `.github/workflows/ci.yml` (or `moodle-ci.yml`) to a plugin repository
- Adding or dropping a Moodle branch, PHP version or database in an existing matrix
- CI fails at "Initialize containers", at `moodle-plugin-ci install`, or with a requirement error such as
  "Moodle 5.2 or later requires at least PHP 8.3.0" (`public/lib/phpminimumversionlib.php`)
- Adding a non-blocking row for Moodle `main` (the next release, in development)
- Deciding whether a green run is enough before a Plugins directory submission
- **Skip when:** running PHPUnit or Behat locally with no workflow involved (`moodle-phpunit-testing`,
  `moodle-behat-testing`); a theme's own suite, stylelint over `scss/` and Mustache lint of overridden templates
  (`moodle-theme-testing-release`); tagging and the release workflow (`moodle-plugin-release`).

## Mental model

1. **The workflow is the upstream template plus a matrix.** Each job checks the plugin out into `plugin/`, installs
   moodle-plugin-ci into `ci/`, runs `moodle-plugin-ci install`, which clones Moodle at `MOODLE_BRANCH`, copies the
   plugin in, installs it on database `DB` and initialises PHPUnit and Behat, then runs one step per check.
2. **Each branch declares its own requirements.** The minimum PHP and database versions are in that branch's
   `environment.xml`; the highest PHP is visible only in core's own CI on that branch. Neighbouring branches differ.
3. **CI tests the checkout, not the ZIP, and only the code the tests reach.** Steps with no input pass: "No PHPUnit
   tests to run, free pass!" and "No Behat features to run, free pass!" (`src/Command/PHPUnitCommand.php`,
   `BehatCommand.php`, moodle-plugin-ci 4.5.11). Licence file, ZIP root, privacy compliance and most security rules
   are checked by nothing in it (reference file below).

## 1. Start from the upstream template

Do not write the workflow from memory, and do not copy an older sibling repository's workflow. Fetch the current
template:

```
https://raw.githubusercontent.com/moodlehq/moodle-plugin-ci/main/gha.dist.yml
```

Keep its job structure and check steps. Change only the matrix, service images, plugin path and triggers. The
template installs the tool with `composer create-project ... moodlehq/moodle-plugin-ci ci ^4`, which is
moodle-plugin-ci 4.x; check its documentation if you pin another major. The steps and the flags that make them strict:

| Step | Command in the template | Fails on |
|---|---|---|
| PHP lint | `moodle-plugin-ci phplint` | PHP syntax errors |
| Mess detector | `moodle-plugin-ci phpmd` with `continue-on-error: true` | Nothing: the command always exits 0, so read its output |
| Code checker | `moodle-plugin-ci phpcs --max-warnings 0` | moodle-cs errors and warnings, PHP files only |
| PHPDoc checker | `moodle-plugin-ci phpdoc --max-warnings 0` | the few inline-tag and argument rules local_moodlecheck still owns |
| Validate | `moodle-plugin-ci validate` | missing required files and strings, table prefixes, Behat tags |
| Savepoints | `moodle-plugin-ci savepoints` | upgrade steps without matching savepoints |
| Mustache | `moodle-plugin-ci mustache` | missing example context, HTML validator and ESLint warnings in templates |
| Grunt | `moodle-plugin-ci grunt --max-lint-warnings 0` | eslint, stylelint, gherkinlint, and any rebuilt `amd/build` file that differs from the committed one |
| PHPUnit | `moodle-plugin-ci phpunit --fail-on-warning` | failures and warnings |
| Behat | `moodle-plugin-ci behat --profile chrome --scss-deprecations` | failures, debugging() output, Bootstrap 4 classes on the page |

Run the same flags locally (`moodle-behat-testing` for `--scss-deprecations`; `moodle-phpunit-testing` for
warnings).

## 2. Decide the Moodle branches

- Test the branches the plugin claims to support: `$plugin->requires` and `$plugin->supported` in `version.php`, or
  the branches the user names. If the user asks for a narrower matrix, a wider `supported` range can stay in
  `version.php`, but say which branches CI covers. `requires` must not sit below the lowest `supported` branch
  (`moodle-plugin-development`).
- A plugin that depends on another plugin needs `moodle-plugin-ci add-plugin owner/repo` (optionally
  `--branch X`) before `install`.

## 3. Verify PHP and database per branch

For each branch, get the requirements from the branch itself:

1. **Minimum PHP and database versions:** that branch's `public/admin/environment.xml` (5.1 and later;
   `admin/environment.xml` on 5.0 and earlier).

   ```bash
   git clone --bare --filter=blob:none https://github.com/moodle/moodle.git moodle.git
   git --git-dir moodle.git show MOODLE_503_STABLE:public/admin/environment.xml \
     | awk '/<MOODLE version="5.3"/{s=1} s && /VENDOR name="(mariadb|mysql|postgres)"|PHP version=/{print} /<\/MOODLE>/{s=0}'
   ```

   The file holds one `<MOODLE version="X.Y">` block per release, including newer ones used for upgrade checks (the
   5.2 tree already has a 5.3 block). Read the block whose version matches the branch, not the last one.
2. **Maximum PHP:** not in `environment.xml`. Read core's `.github/workflows/push.yml` on the same branch: its
   comments mark the "lowest PHP supported" (MySQL job) and "highest PHP supported" (PostgreSQL job). Cross-check
   with the moodledev.io PHP page.
3. If you cannot verify a combination, leave it out and say so. Never infer one branch's requirements from the
   branches next to it.

The values read for each supported branch are in the version files below; branches before 5.2 are in
[reference/older-branches.md](../moodle-skill-files/moodle-ci-matrix/reference/older-branches.md).

## 4. Build the matrix only from verified pairs

The default for a plugin supporting 5.2 and 5.3: each branch's lowest and highest PHP, the databases alternated,
and each row given the database images its branch needs.

```yaml
    services:
      postgres:
        image: ${{ matrix.database == 'pgsql' && (matrix.pgsql-image || 'postgres:16') || '' }}
        env:
          POSTGRES_USER: 'postgres'
          POSTGRES_HOST_AUTH_METHOD: 'trust'
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 3
      mariadb:
        image: ${{ matrix.database == 'mariadb' && (matrix.mariadb-image || 'mariadb:10.11') || '' }}
        env:
          MARIADB_ALLOW_EMPTY_ROOT_PASSWORD: '1'
          MYSQL_CHARACTER_SET_SERVER: "utf8mb4"
          MYSQL_COLLATION_SERVER: "utf8mb4_unicode_ci"
        ports:
          - 3306:3306
        options: --health-cmd="healthcheck.sh --connect --innodb_initialized" --health-interval 10s --health-timeout 5s --health-retries 3

    strategy:
      fail-fast: false
      matrix:
        include:
          # 5.2: PHP 8.3-8.4, PostgreSQL >= 16, MariaDB >= 10.11 (environment.xml, push.yml on MOODLE_502_STABLE).
          - {moodle-branch: MOODLE_502_STABLE, php: '8.3', database: mariadb}
          - {moodle-branch: MOODLE_502_STABLE, php: '8.4', database: pgsql}
          # 5.3: PHP 8.3-8.4, PostgreSQL >= 17, MariaDB >= 11.4 (same files on MOODLE_503_STABLE).
          - {moodle-branch: MOODLE_503_STABLE, php: '8.3', database: mariadb, mariadb-image: 'mariadb:11.4'}
          - {moodle-branch: MOODLE_503_STABLE, php: '8.4', database: pgsql, pgsql-image: 'postgres:17'}
```

**Several branches with different PHP ranges and a full database cross.** Use an object axis, so each branch keeps
its own PHP list and is still crossed with every database:

```yaml
      matrix:
        moodle:
          - {branch: MOODLE_502_STABLE, php: '8.3'}
          - {branch: MOODLE_502_STABLE, php: '8.4'}
          - {branch: MOODLE_503_STABLE, php: '8.3'}
          - {branch: MOODLE_503_STABLE, php: '8.4'}
        database: [pgsql, mariadb]
```

Then read `matrix.moodle.branch` and `matrix.moodle.php` in `setup-php` and in the `install` step's env. If you
cross flat `php:` and `moodle-branch:` axes instead, prune with `exclude:` and give each entry a comment naming the
source.

**`include:` trap.** GitHub first tries to merge an `include` entry into existing combinations. If it cannot merge
without overwriting an original value, it adds the entry as a new job with only the keys it lists. A
`{moodle-branch: X, php: Y}` entry added to a matrix that also has `database` becomes a job with an empty `DB`, and
`install` fails. With no original axes, as above, every `include` entry is its own job. Expand the matrix before
you push: parse the YAML and apply GitHub's documented rules with a short script. Seen in practice.

## 5. Service images

- Pin each database to the lowest version its branch supports. An image that is too new hides breakage at the
  minimum version, and one that is too old fails the newer branch. When one image must serve every row, pin the
  lowest version that satisfies every branch; when branches differ (5.2 and 5.3 do), make the image a matrix value
  with a default, as above.
- The upstream template's `postgres:17` and floating `mariadb:11` images (as published with 4.5.11) are newer
  than the minimum for 5.2. Pin them explicitly.
- **Health check:** MariaDB 11.x images do not ship `mysqladmin`, so `--health-cmd="mysqladmin ping"` never reports
  healthy and the job dies at "Initialize containers". Use `healthcheck.sh --connect --innodb_initialized` (as
  above) or `mariadb-admin ping`. Seen in practice on 11.x; that `mariadb:10.11` ships the same script was not
  re-checked for this skill, so watch the first 5.2 MariaDB row.
- Before changing any matrix key, grep the workflow for every `matrix.` consumer: the service images, `setup-php`,
  the install env and artifact names all read it.

## 6. Non-blocking row for `main`

Add the next Moodle release as an `include:` row that cannot fail the build:

```yaml
jobs:
  test:
    continue-on-error: ${{ matrix.experimental == true }}
    strategy:
      fail-fast: false
      matrix:
        include:
          - {moodle-branch: MOODLE_503_STABLE, php: '8.4', database: pgsql, pgsql-image: 'postgres:17'}
          - {moodle-branch: main, php: '8.4', database: pgsql, pgsql-image: 'postgres:17', experimental: true}
```

- Read `main`'s requirements from the `<MOODLE>` block for the version `main` is building, at the commit you test;
  they change during development and can rise above the newest stable branch's.
- Keep the Grunt step, and any "committed `amd/build` is stale" check, on one stable branch:
  `if: ${{ !cancelled() && matrix.moodle-branch == 'MOODLE_502_STABLE' }}`. Each branch's toolchain can minify and
  lint differently, so a build committed from one branch shows as stale on another.
- **Artifact names:** the template's `Behat Faildump (${{ join(matrix.*, ', ') }})` joins every matrix value, so an
  image value like `postgres:17` puts a `:` in the artifact name, which `actions/upload-artifact` rejects. Name the
  fields: `Behat Faildump (${{ matrix.moodle-branch }}, PHP ${{ matrix.php }}, ${{ matrix.database }})`. Seen in
  practice.

## 7. Propose the matrix before writing it

Show the user a table (branch x PHP x database) with one line on how each axis was checked. Then write the file. A
workflow on the default branch runs on every push, so a wrong matrix is visible at once.

## 8. Make the plugin pass on the first run

CI that fails on its first run teaches everyone to ignore it. Before you finish, run each step locally the way the
workflow runs it; the commands, the work-directory rule and the `.env` checks are in
[reference/running-the-pipeline-locally.md](../moodle-skill-files/moodle-ci-matrix/reference/running-the-pipeline-locally.md). The failures that keep
coming back:

- Every Mustache template in `templates/` needs an `Example context (json):` block in its docblock; a
  `.mustachelintignore` next to the template skips only HTML validation, not the rest.
- Lang strings sorted by key, and no PHP other than `$string['id'] = 'value';` in the lang file (phpcs
  `moodle.Files.LangFilesOrdering`).
- A blank line after the last step, trailing spaces or wrong indentation in a `.feature` file fails gherkinlint in
  the Grunt step (`moodle-behat-testing` has the shape core's `.gherkin-lintrc` enforces).
- Bootstrap 4 class names (`mr-2`, `sr-only`, `font-weight-bold`) in templates or in markup built by JavaScript fail
  every JavaScript Behat step under `--scss-deprecations` on 5.2 and 5.3. Seen in practice.
- `amd/build` rebuilt with the Node version and grunt of the branch the Grunt step runs on (Node `>=22.11.0 <23`
  in `package.json` on 5.2 and 5.3.0).

## 9. Traps outside the matrix

- **Run the pipeline as written.** A flag that looks equivalent tests a different pipeline: an explicit `install
  --extra-plugins <dir>` in place of the workflow's `add-plugin` step overrides the path that `add-plugin` wrote to
  moodle-plugin-ci's `.env` (`EXTRA_PLUGINS_DIR`), and it can fail on the runner with `Failed to run realpath(...)`.
  Keep `add-plugin`, and do not add `--extra-plugins`. Seen in practice.
- **No secret in a URL or an echoed argument.** GitHub masks a secret only where it appears verbatim; a token put
  into a URL, base64-encoded or split, is printed in clear. Pass secrets through `env:` and mask derived values
  before printing anything that contains them:

  ```yaml
      - name: Fetch private dependency
        env:
          TOKEN: ${{ secrets.DEPENDENCY_TOKEN }}
        run: |
          AUTH="$(printf 'x-access-token:%s' "$TOKEN" | base64 -w0)"
          echo "::add-mask::$AUTH"
          git -c http.extraHeader="Authorization: Basic $AUTH" clone https://github.com/owner/dependency.git
  ```

- **A code path behind an optional PHP extension runs only where the extension is loaded.** A runner's PHP can load
  extensions a local site lacks (Imagick, for example), so an `extension_loaded('imagick')` branch that a GD-only
  local site skips runs on CI and fails there first. Seen in practice; which extensions a runner loads by default
  depends on the `setup-php` version and was not checked for this skill. Name the extensions you rely on in
  `setup-php`'s `extensions:` input so every row is explicit, test both paths deliberately (or load the extension
  locally, `moodle-phpunit-testing`), and expect CI-only failures when the local site lacks one.
- **The PostgreSQL rows are the only place PostgreSQL-sensitive tests run.** PHPUnit wraps each test in a
  transaction there and not on MariaDB, so observer, message and log-store tests can pass on one family and fail on
  the other (`moodle-phpunit-testing`). Keep at least one blocking PostgreSQL row per branch.
- **Reruns hide flakes.** `moodle-plugin-ci behat` reruns failed scenarios twice by default (`--auto-rerun`,
  `BehatCommand.php`). A scenario that needs a rerun is flaky; fix it, do not rely on the rerun.
- **Theme plugins:** `behat` picks the theme's own suite by default since moodle-plugin-ci 4.5.11 (older versions ran
  `default` and found no theme features, a green job with zero scenarios); every feature carries `@theme
  @theme_<name>`; stylelint lints the theme's whole `scss/` tree. The rest is in `moodle-theme-testing-release`.

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| Crossing all requested branches with "current" PHP | Unsupported pair; install fails the environment check | Check each branch's `environment.xml` and core `push.yml` |
| Reading the last `<MOODLE>` block in `environment.xml` | Picks up a newer release's minimums | Select `version="X.Y"` for the branch |
| Looking for `admin/environment.xml` on 5.1+ | File not found | `public/admin/environment.xml` |
| `include` entry missing the `database` key | Extra job with an empty `DB` | Use an object axis, or list every key |
| `mysqladmin ping` health check on MariaDB 11 | Containers never become healthy | `healthcheck.sh --connect --innodb_initialized` |
| One floating image (`postgres:17`, `mariadb:11`) for 5.2 rows | Hides breakage at 5.2's minimum | Per-row image values with the branch minimum as default |
| `join(matrix.*)` in the artifact name with image values in the matrix | upload-artifact rejects the name | Name the fields explicitly |
| `main` row without `continue-on-error` | Upstream churn breaks the build | `experimental: true` plus job-level `continue-on-error` |
| Grunt step on every branch | "File is stale and needs to be rebuilt" on the branches you did not build with | Run Grunt on one stable branch |
| Replacing `add-plugin` with `--extra-plugins` | Install fails at `realpath` on the runner | Keep the upstream step order |
| Running `moodle-plugin-ci install` inside the plugin repository | `package.json` and `node_modules/` written into the repository | Run it from a separate work directory |
| No tests, or no features | "free pass!", green job | Add tests; read the step log, not the tick |
| Trusting `phpmd`'s green tick | It always exits 0 | Read its output |
| Token in a clone URL | Secret printed in the log | `env:` plus `::add-mask::` for derived values |
| Treating green CI as Plugins directory ready | Rejected for licence file, ZIP root, strings or prefixes | Walk [reference/what-ci-does-not-check.md](../moodle-skill-files/moodle-ci-matrix/reference/what-ci-does-not-check.md) |

## Reference files

| File | Read it when |
|---|---|
| [reference/running-the-pipeline-locally.md](../moodle-skill-files/moodle-ci-matrix/reference/running-the-pipeline-locally.md) | You reproduce a CI failure locally, run moodle-plugin-ci outside GitHub Actions, or need to know which directory `install` writes to and what `.env` holds |
| [reference/what-ci-does-not-check.md](../moodle-skill-files/moodle-ci-matrix/reference/what-ci-does-not-check.md) | A plugin with green CI is about to be submitted to the Plugins directory, a reviewer raised something CI did not, or you need to know exactly what one moodle-plugin-ci step checks |
| [reference/older-branches.md](../moodle-skill-files/moodle-ci-matrix/reference/older-branches.md) | The matrix includes Moodle 5.1 or earlier, or you need the requirement values for a branch before 5.2 |

## Version notes

| Moodle | File |
|---|---|
| 5.2 | [versions/moodle-5.2.md](../moodle-skill-files/moodle-ci-matrix/versions/moodle-5.2.md) |
| 5.3 | [versions/moodle-5.3.md](../moodle-skill-files/moodle-ci-matrix/versions/moodle-5.3.md) |

## References

- https://moodlehq.github.io/moodle-plugin-ci/ (moodle-plugin-ci documentation)
- https://github.com/moodlehq/moodle-plugin-ci/blob/main/gha.dist.yml (upstream GitHub Actions template)
- https://moodledev.io/general/development/tools/phpunit (PHPUnit in plugins)
- https://moodledev.io/general/releases (release dates and per-version requirements)
- https://moodledev.io/general/development/policies/php (PHP version support policy)
- https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow
  (matrix `include` and `exclude` rules)
- https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions#masking-a-value-in-a-log
  (`::add-mask::`)
- When a new Moodle version is supported, add `versions/moodle-X.Y.md` with the values read from that branch and
  extend the default matrix in section 4.
