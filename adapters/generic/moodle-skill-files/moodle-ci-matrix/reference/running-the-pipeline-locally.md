# Running the pipeline locally

Read this when you reproduce a CI failure locally, run moodle-plugin-ci outside GitHub Actions, or need to know which
directory `install` writes to and what its `.env` holds.

Read in the moodle-plugin-ci 4.5.11 source (`src/`, `bin/moodle-plugin-ci`), not run for this file unless a line says
"seen in practice".

## The commands, as the template runs them

Work in a directory of its own, outside the plugin repository, with the plugin checked out (or copied) beside it:

```bash
mkdir -p work && cd work
git clone https://github.com/you/moodle-local_example.git plugin
composer create-project -n --no-dev --prefer-dist moodlehq/moodle-plugin-ci ci ^4
export PATH="$PWD/ci/bin:$PWD/ci/vendor/bin:$PATH"

DB=pgsql MOODLE_BRANCH=MOODLE_503_STABLE moodle-plugin-ci install --plugin ./plugin --db-host=127.0.0.1
moodle-plugin-ci phplint
moodle-plugin-ci phpmd
moodle-plugin-ci phpcs --max-warnings 0
moodle-plugin-ci phpdoc --max-warnings 0
moodle-plugin-ci validate
moodle-plugin-ci savepoints
moodle-plugin-ci mustache
moodle-plugin-ci grunt --max-lint-warnings 0
moodle-plugin-ci phpunit --fail-on-warning
moodle-plugin-ci behat --profile chrome --scss-deprecations
```

- Every step except `phpmd` must exit 0; `phpmd` always returns 0 (`src/Command/MessDetectorCommand.php`), so read
  what it prints.
- `--max-warnings` exists only on `phpcs` and `phpdoc` (`CodeCheckerCommand.php`, `PHPDocCommand.php`); Grunt's
  equivalent is `--max-lint-warnings`. Passing `--max-warnings` to another step fails with an unknown option.
- Use the flags of the plugin's own workflow, not a look-alike. A local run without `--scss-deprecations`, without
  `--max-warnings 0`, or with a different Grunt invocation is a different gate, and its green says nothing about the
  CI step. Seen in practice.
- Read the step's last lines, not only its exit code. "No PHPUnit tests to run, free pass!", "No Behat features to
  run, free pass!" and "No relevant files found to process, free pass!" all exit 0.

## Where `install` writes

- **The current directory.** `install` runs `npm install --no-progress grunt` with no working directory set
  (`src/Installer/VendorInstaller.php`), so `package.json`, `package-lock.json` and `node_modules/` land wherever
  you ran it. Its `--moodle` (default `moodle`) and `--data` (default `moodledata`) options are relative paths too
  (`src/Command/InstallCommand.php`). Run inside the plugin repository and all of these end up in the repository,
  where they are committed by accident or make later lint runs scan `node_modules/`. Seen in practice.
- **The `.env` next to the tool.** `install` records `MOODLE_DIR` and `PLUGIN_DIR` in `ci/.env`
  (`bin/moodle-plugin-ci` defines `ENV_FILE`; `MoodleInstaller.php`, `PluginInstaller.php`), and every later step
  reads them, which is why later steps take no plugin argument. A failed `install` can leave `MOODLE_DIR` pointing at
  the previous tree, and later steps then test the wrong code without saying so. Check `ci/.env` after each install.
  Seen in practice.
- `add-plugin` also writes to `.env` (`EXTRA_PLUGINS_DIR`); do not pass `--extra-plugins` as well (main file).

## Install options that matter locally

| Option or variable | Effect |
|---|---|
| `DB`, `MOODLE_BRANCH` (env) or `--db-type`, `--branch` | Database driver (`pgsql`, `mariadb`, `mysqli`) and Moodle branch |
| `--db-host`, `--db-user`, `--db-pass`, `--db-name` (`DB_USER`, `DB_PASS`, `DB_NAME`) | Where the database server is |
| `--repo` (`MOODLE_REPO`) | Clone Moodle from a local mirror instead of GitHub |
| `--no-init` | Skip PHPUnit and Behat initialisation, for lint-only runs |
| `--node-version` (`NODE_VERSION`) | Override the branch's `.nvmrc` (`lts/jod` on 5.2 and 5.3.0) |
| `IGNORE_PATHS`, `IGNORE_NAMES`, `<COMMAND>_IGNORE_PATHS` (env) | Exclude files from the analysis steps; not honoured by Grunt |

`moodle-plugin-ci add-config 'define("THEME_DESIGNER_CACHE_LIFETIME", 0);'` appends a line to the installed site's
`config.php` (`src/Command/AddConfigCommand.php`); use it after `install` for settings a test run needs.

## Reproducing one CI row

1. Use the same branch, PHP version and database family as the failing row; a local MariaDB says nothing about a
   PostgreSQL row.
2. Use the same database server version as the row's service image when the failure is in SQL or an install
   environment check.
3. Run only the failing step after `install`, with the workflow's flags, then the steps after it: steps share the
   installed site, so a later step can depend on an earlier one's side effects (Grunt rebuilding `amd/build`).
4. For Behat, start the WebDriver the profile expects; `moodle-plugin-ci behat --start-servers` starts PHP's built-in
   web server on port 8000 and a Selenium container through the `docker` command (`selenium/standalone-chrome:4`
   for the `chrome` profile, `BehatCommand.php`), so Docker must be available.
