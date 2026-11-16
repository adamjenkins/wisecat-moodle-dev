---
mode: 'agent'
description: Run phpcs with the Moodle coding standard and fix reported issues.
---
You will lint and fix Moodle coding-style issues.

User's input: ${input:args}

If empty, ask for a path. On Moodle 5.2 and 5.3 plugin directories are under `public/` in the Moodle root.

Steps:

1. Detect the linter, in this order:
   - `moodle-plugin-ci` on PATH: `moodle-plugin-ci phpcs --max-warnings 0 <path>` is what CI runs
   - `phpcs` on PATH with the `moodle` standard installed (`phpcs -i` lists it)
   - `vendor/bin/phpcs` in the Moodle root, if the site added it; core's own `composer.json` in 5.2 and 5.3 does
     not install it

2. Run, keeping the whole output (the findings come first and the summary last, so do not read only the end):
   ```bash
   phpcs --standard=moodle --report=summary <path>
   phpcs --standard=moodle --report=full <path>
   ```
   Some sniffs depend on the Moodle version. Outside a Moodle tree, name the branch:
   `phpcs --standard=moodle --runtime-set moodleBranch 503 <path>`.

3. If `phpcs` is not installed, instruct the user:
   ```bash
   composer global require moodlehq/moodle-cs
   ```
   and do not report the code as clean: say that the check was not run.

4. Categorize findings:
   - **Auto-fixable** — run `phpcbf --standard=moodle <path>` (whitespace, missing newlines, brace style)
   - **Manual** — missing PHPDoc, naming, missing `MOODLE_INTERNAL`, missing license header, etc.

5. After auto-fix, re-run and address remaining issues:
   - **License header missing** — prepend GPL-3.0-or-later header (template from `moodle-plugin-development` skill)
   - **Missing `MOODLE_INTERNAL`** — add after the file docblock in files that run code when included. Not in a
     file that only declares a class under `classes/`: there the check is reported as not needed
   - **Missing PHPDoc on class/method** — generate doc with `@param`, `@return`, `@throws`
   - **Naming** — functions, variables and classes are lower case; functions and classes use underscores, variables
     do not. Rename carefully and check call sites
   - **Line length** — over 132 characters is a warning and over 180 an error; wrap at logical breakpoints
   - **Indent** — convert tabs to 4 spaces
   - **Lang file order** — keys in `lang/en/*.php` in alphabetical order
   - Never edit generated or third-party files to satisfy the linter (`amd/build/`, vendored libraries listed in
     `thirdpartylibs.xml`)

6. After all fixes, re-run `phpcs` and confirm zero errors and zero warnings. CI runs with `--max-warnings 0`,
   so a warning fails the build.

7. Recommend running the same check in CI with `moodle-plugin-ci` (`moodle-ci-matrix` has the workflow):
   ```yaml
   - run: moodle-plugin-ci phpcs --max-warnings 0
   ```

Reference the `moodle-plugin-development` skill for coding standard details and `moodle-definition-of-done` for
reading the gates.
