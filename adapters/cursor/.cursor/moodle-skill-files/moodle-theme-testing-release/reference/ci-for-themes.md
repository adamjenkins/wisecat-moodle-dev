# CI for a theme: the workflow, a dark-mode run, and reading failed lint steps

Read this when writing or fixing a theme's GitHub Actions workflow, adding a dark-mode Behat run, or reading a
failed grunt, stylelint, Mustache, validate or phpcs step on a theme.

Evidence: moodle-plugin-ci 4.5.11 was read (`src/Command/*.php`, `src/PluginValidate/`, and the bundled
moodle-local_ci Mustache linter); core's `Gruntfile.js`, `.grunt/tasks/` and `.gherkin-lintrc` were read in 5.2 and
5.3.0. The static gates (phplint, phpcs, phpdoc, validate, core's stylelint over `scss/`, Mustache lint) were run on
5.3.0 against a Boost child theme, and Mustache lint also on a 5.2 tree. No workflow below has run on GitHub; treat
the YAML as read, not run.

## The workflow

The matrix (Moodle branch, PHP, database, service images) comes from `moodle-ci-matrix`, which owns those choices.
The steps for a theme, after the upstream `gha.dist.yml` template:

```yaml
      - name: Install moodle-plugin-ci
        run: moodle-plugin-ci install --plugin ./plugin --db-host=127.0.0.1
        env:
          DB: ${{ matrix.database }}
          MOODLE_BRANCH: ${{ matrix.moodle-branch }}

      - name: PHP Lint
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci phplint

      - name: Moodle Code Checker
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci phpcs --max-warnings 0

      - name: Moodle PHPDoc Checker
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci phpdoc --max-warnings 0

      - name: Validating
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci validate

      - name: Check upgrade savepoints
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci savepoints

      - name: Mustache Lint
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci mustache

      - name: Grunt
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci grunt --max-lint-warnings 0

      - name: PHPUnit tests
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci phpunit --fail-on-warning

      - name: Behat features
        id: behat
        if: ${{ !cancelled() }}
        run: moodle-plugin-ci behat --profile chrome --suite mytheme --scss-deprecations

      - name: Mark cancelled jobs as failed
        if: ${{ cancelled() }}
        run: exit 1
```

Theme-specific points:

- **`--suite mytheme`.** Since 4.5.11, `behat` defaults the suite to the theme's name when the component starts with
  `theme_`; before that it used `default`, where a theme's features do not exist, and the step passed with zero
  scenarios. Naming the suite costs nothing and survives an older pinned version. A workflow that installs
  `moodle-plugin-ci ^4` gets the newest 4.x.
- **`--scss-deprecations`** makes the command run
  `util_single_run.php --enable --add-core-features-to-theme --scss-deprecations` first, then `run.php` with
  `--tags=@theme_mytheme --auto-rerun=2`. The extra core features are filtered out again by the tag.
- **No features means a free pass.** `behat` and `phpunit` with no tests report success. The first green run of a new
  theme proves nothing until there is a feature and a test.
- **`phpmd` cannot fail** (the command returns 0 whatever it finds), so it does not belong in a gating list.
- Behat failure dumps: upload `moodledata/behat_dump` as an artifact on failure (as in the template) to see the
  page HTML and screenshot of the failing step.

### Optional steps

Designer-mode scenarios: make the stylesheet lifetime 0 so a changed SCSS shows at once.

```yaml
      - name: Stylesheet lifetime for designer-mode scenarios
        run: moodle-plugin-ci add-config "define('THEME_DESIGNER_CACHE_LIFETIME', 0);"
```

`add-config` appends a line to the CI site's `config.php` (the command exists in 4.5.11). It looks for Moodle in the
current directory unless `--moodle` or `MOODLE_DIR` says otherwise; check the step's output the first time.

**5.3+:** a second Behat run in dark mode, on the 5.3 rows only:

```yaml
      - name: Behat features in dark mode
        if: ${{ !cancelled() && matrix.moodle-branch != 'MOODLE_502_STABLE' }}
        working-directory: moodle
        run: |
          php public/admin/tool/behat/cli/util_single_run.php --enable --add-core-features-to-theme \
            --scss-deprecations --colourmode=dark
          moodle-plugin-ci behat --moodle=. --profile chrome --suite mytheme
```

- `moodle-plugin-ci behat` has no colour-mode option, and with `--scss-deprecations` it re-initialises and resets the
  mode to the theme default. So the dark run initialises itself and then calls `behat` without that flag.
- The colour modes guide recommends running the suite once by default and once dark, both in CI. Scenarios that
  pin a mode with the `theme_boost_colourmode` preference run the same in both.

**5.3+:** a theme with React overrides in `js/esm/src` must commit its `js/esm/build`, and the default grunt tasks
(`amd`, `yui`, `gherkinlint`, `stylelint`) never build or check it. Asking for it explicitly is derived from the
code, not run: `-t` replaces the defaults, so list them all.

```yaml
        run: moodle-plugin-ci grunt --max-lint-warnings 0 -t amd -t yui -t gherkinlint -t stylelint -t esm
```

## What each gate checks on a theme

### validate

- Required: `version.php`, `lang/en/theme_mytheme.php` with a `pluginname` string, and `config.php`.
- Every `tests/behat/*.feature` must carry both `@theme` and `@theme_mytheme`.
- If `db/upgrade.php` exists, it must define `xmldb_theme_mytheme_upgrade`; tables in `db/install.xml` must start
  with the component prefix.
- Not checked: a licence file, a README, `pix/screenshot.*`, `choosereadme`, `thirdpartylibs.xml`, a privacy
  provider. Those are on the release checklist.

### grunt: stylelint and gherkinlint

- `stylelint` runs as `npx grunt stylelint` inside the plugin when the plugin has any `.css` or `.scss` file. Core's
  Gruntfile then treats the component as a theme only if its path starts with `public/theme/`, which is where
  moodle-plugin-ci installs it. For a theme it lints `scss/*.scss` and `scss/**/*.scss`, or `style/*.css` when there is
  no `scss/`; a root `styles.css` in a theme is never linted. The rules and the disable comments are in
  `moodle-theme-scss`.
- With `--max-lint-warnings 0`, stylelint warnings fail too: upper-case or long hex colours, `0px`, lines over 132
  characters.
- Core's stylelint has the `csstree/validator` rule on 5.2 and 5.3 (`.stylelintrc`, identical in both). Run on
  5.3.0, it rejected `container-type`, `@container` and `clamp()` in `font-size`; append
  `// stylelint-disable-line csstree/validator` to each such line, as core does in
  `public/theme/boost/scss/moodle/modchooser.scss` (5.3.0).
- `gherkinlint` checks every feature file with core's `.gherkin-lintrc`: indentation (Feature 0, Background and
  Scenario 2, steps 4, Examples 4, example rows 6), no trailing spaces, no multiple empty lines, a newline at the end,
  named features and scenarios, unique feature names, no outline without examples.
- After the tasks, the step fails with "File is stale and needs to be rebuilt" if any `*.js`, `*.js.map` or `*.css`
  in the plugin changed. `amd/build` must be committed fresh from `amd/src`. Nothing compiles the theme's SCSS here,
  so a committed precompiled `style/*.css` is never checked against the SCSS.
- Paths listed in `thirdpartylibs.xml` and in a `.stylelintignore` in the theme root (paths relative to the theme)
  are skipped: `grunt ignorefiles`, run at install, merges them into core's ignore files. The environment variables
  `IGNORE_PATHS` and `IGNORE_NAMES` do not apply to grunt.
- A large theme that comments the grunt step out also loses stylelint, gherkinlint and the AMD staleness check.
  Fix the findings instead.

Whether an `amd/build` built with one branch's toolchain passes the staleness check on the other branch was not
established. If a theme has `amd/src` and the check fails on one branch only, rebuild with that branch's Node
toolchain and compare; do not silence it.

### mustache

- Every `*.mustache` in the theme is linted except `templates/mobileapp/`. Overridden core templates under
  `templates/core/` and `templates/<component>/` are linted exactly like the theme's own.
- Partials are resolved first in the theme's `templates/<component>/`, then in the component's own templates.
  Parent themes are not searched. A partial that is not found is not reported: the Mustache library renders it as
  nothing and the linter checks the HTML without it. So lint cannot show that a template copied from 5.3 includes
  a partial that 5.2 lacks; only a page render on that branch does. Read in the linter and its Mustache library
  (moodle-plugin-ci 4.5.11), not run.
- Any warning fails the file: no `@template` docblock, no `Example context (json):`, an HTML validator message on
  the rendered example.
- `{{#js}}` blocks are not linted on 5.2 and 5.3: the linter looks for ESLint in `node_modules/.bin/` under the
  directory moodle-plugin-ci passes as the Moodle base, which is `public/` since 5.1, while `node_modules` is in
  the Moodle root. The step's log then says "ESLint did not run". Read in moodle-plugin-ci 4.5.11
  (`MustacheCommand.php`) and its bundled linter, not run. Lint that JavaScript by keeping it in `amd/src`.
- `*.mustache.upstream` twins (the untouched originals kept beside copies) are not linted: the file glob ends at
  `.mustache`. The same holds for `*.php.upstream` under phpcs and phplint.
- `.mustachelintignore` in the template's directory lists file-name patterns whose HTML validation is skipped. It
  does not skip the docblock or ESLint checks. Quirk of the linter: a line containing `#` after its first character
  is ignored, and a line starting with `#` is read as a pattern, not a comment.
- A template whose root is a bare `<li>`, or that puts `role="log"` on an `<ol>`, fails HTML validation; wrap
  partials in one self-contained element.
- A copied core template that core itself left without an example context fails the theme's CI. Add a context;
  that is cheaper than a baseline mechanism. Large themes either keep a baseline of upstream findings in their own
  workflow or list overridden core templates in `MUSTACHE_IGNORE_NAMES` (per-command form of `IGNORE_NAMES`), which
  drops those templates from all Mustache checks.

### phpcs and phpdoc

- PHP files only. `.mustache`, `.scss` and `.js` boilerplate and `@copyright` lines are not checked by anything.
- A copied core PHP file is checked as the theme's own: Boost's `layout/drawers.php` copied unchanged fails on a
  missing trailing comma (run on 5.3.0).
- Global functions in `lib.php` and in any page or CLI script must start with `theme_mytheme_`. phpcs checks only
  that function names are lower case, not the prefix; a reviewer treats a missing prefix as a blocker.
- `require_login()` presence after `config.php` is a phpcs warning, so with `--max-warnings 0` a theme page script
  without it fails. It is not an authorisation check; the capability check is yours.

### phpunit

- Runs the theme's own test suite only. Core's privacy compliance test is not part of it.
- `--fail-on-warning` turns a PHPUnit warning (for example a data provider problem) into a failure.

## What CI cannot see

- The release ZIP: CI installs from the git checkout. Its root folder, its licence file and what `export-ignore`
  left out are checked by listing the archive.
- How the theme looks: only assertions in tests see it.
- A compile failure, unless a PHPUnit test asserts the theme's own CSS.
- A privacy provider that is missing or wrong.
- A lang string that core asks for but the theme lacks (`choosereadme`, a block region name), unless a test renders
  the page that asks.
- A scenario that is flaky: `--auto-rerun=2` reruns failures, and a rerun pass is green.
