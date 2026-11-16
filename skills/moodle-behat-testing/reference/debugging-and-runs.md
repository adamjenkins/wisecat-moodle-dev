# Behat runs and debugging

Read this when a run gives a result you do not trust (scenarios missing, a change not picked up, a failure only in
CI), when you set up the WebDriver or parallel runs, when you need failure dumps, or when you drive Moodle with
Playwright or a similar tool outside Behat.

Sources are the 5.2 and 5.3.0 trees and moodle-plugin-ci 4.5.11, paths relative to the Moodle root; read in the
source and not run for this file unless a line says "seen in practice".

## Ways to run

```bash
# Through Moodle's wrapper, which knows about parallel runs and theme suites.
php public/admin/tool/behat/cli/run.php --tags=@local_example
php public/admin/tool/behat/cli/run.php --tags=@local_example --name="Teacher marks a student present"
php public/admin/tool/behat/cli/run.php --feature="$PWD/public/local/example/tests/behat/mark.feature"
php public/admin/tool/behat/cli/run.php --tags=@local_example --stop-on-failure --verbose

# Straight to Behat, with the config init.php wrote (single run only).
vendor/bin/behat --config /path/to/behat_dataroot/behat/behat.yml --tags=@local_example
vendor/bin/behat --config /path/to/behat_dataroot/behat/behat.yml public/local/example/tests/behat/mark.feature:23
```

- `run.php` passes any option it does not know to Behat (`--name`, `--stop-on-failure`, `--format=progress`), so an
  init-time option such as `--scss-deprecations` given to `run.php` reaches Behat and fails with "option does not
  exist" (`public/admin/tool/behat/cli/run.php`, 5.2 and 5.3). Init-time options belong to `init.php`.
- `--feature` takes an absolute path.
- **Parallel:** `init.php --parallel=3` builds three sites; `run.php` then runs them all and merges the result.
  There is no separate parallel binary. Re-init with `--parallel` again after changing the number.
- **Reruns hide flakes.** `moodle-plugin-ci behat` runs with `--auto-rerun=2` by default (`BehatCommand.php`), so a
  scenario that fails once and then passes is reported green. Run it locally without reruns before trusting it.

## WebDriver

`@javascript` scenarios need a WebDriver server. The default profile talks to `http://localhost:4444/wd/hub`. Start
one, for example a Selenium container matching your browser, or chromedriver on that port:

```bash
docker run -d -p 4444:4444 --shm-size=2g selenium/standalone-chrome:4
```

`moodle-plugin-ci behat --profile chrome` starts the same image, `selenium/standalone-chrome:4`
(`BehatCommand.php`, 4.5.11), so this matches CI. Name other browsers or hosts in `config.php` with
`$CFG->behat_profiles` and select one with `--profile=<name>` on `run.php` (`config-dist.php`, the commented
`behat_profiles` example). Avoid `latest`: it can pair a browser with a driver the Behat extension does not handle,
and the failure looks like a test bug.

## When the result looks wrong

| Symptom | Likely cause | Check or fix |
|---|---|---|
| Fewer scenarios than the repository has | The site runs an older installed copy, or a new `.feature` is not in `behat.yml` | Compare with `grep -c '^ *Scenario' tests/behat/*.feature`; copy the plugin again and re-run `init.php` |
| An edited scenario runs the old steps | Gherkin cache keyed on file modification time; a copy that preserved old timestamps | `touch` the copied feature files, or re-init. Seen in practice |
| "Undefined step" for a step you wrote | New context file, or class not named `behat_<component>` | Re-init; check the class name |
| `the following "x > y" exist` says the entity is unknown | Entity declared outside `tests/generator/behat_<component>_generator.php`, or no re-init | Move it there; re-init |
| Green locally, red in CI on every JavaScript step | Local site not initialised with `--scss-deprecations` | `init.php --scss-deprecations`; read the "Run optional tests" banner |
| Red in CI with "debugging() message/s found" | A deprecated call reached the page; developer debugging is on in CI | Fix the call; the message names it (`look_for_exceptions()` in `behat_session_trait.php`) |
| Red only on the PostgreSQL row | SQL that MySQL accepts (ordering, `GROUP BY`, text comparison) | Run the scenario on PostgreSQL, or read the query (`moodle-phpunit-testing` covers the transaction side) |
| Site home steps land on the dashboard or login page | `enablemyhome` is 0 on new 5.2.2+ and 5.3 sites | Set it in the Background (main file) |
| A changed SCSS or `styles.css` has no effect | Theme CSS is built at init and restored per scenario | Re-init |
| Accessibility step fails with "No data" | The server denies `/lib/behat/axe/axe.min.js` | Allow `/behat/` paths on the Behat site's virtual host. Seen in practice |
| Accessibility step passes on a page that cannot pass | Site initialised with `--no-axe`: the step does nothing | Re-init without it; the banner says "Accessibility: No" |

## Failure dumps

Set `$CFG->behat_faildump_path = '/path/to/faildumps';` in `config.php` (`config-dist.php`). Each failed step writes
the page HTML and, for JavaScript scenarios, a screenshot. Read them before re-running: a debugging() message, an
open modal, a user tour or the wrong page is usually visible at once. In CI, `moodle-plugin-ci behat --dump` prints
the HTML dumps into the log (`BehatCommand.php`, `--dump`), and the upstream workflow template uploads the faildump
directory as an artifact.

## Debugging a single step

- `And I pause` (also `I pause scenario execution`) stops the run until you press Enter in the terminal, with the
  browser left on the page (`behat_general::i_pause_scenario_execution()`, 5.2 and 5.3). Remove it before
  committing.
- `$CFG->behat_pause_on_fail = true;` in `config.php` pauses at every failed step instead, after the dump is written
  (`public/lib/tests/behat/behat_hooks.php`; `config-dist.php`). Use it for local runs only.
- `--verbose` (passed through to Behat) prints the full exception, including the locator Mink tried.
- When a step matches the wrong element, test the locator in the browser console on the dump's HTML:
  `document.querySelectorAll('label')` for field locators, or the XPath of a named selector from
  `public/lib/behat/classes/partial_named_selector.php`.

## Driving Moodle outside Behat (Playwright and similar)

Scripts that drive a real Moodle site for walkthroughs, screenshots or smoke checks meet traps that Behat's own
steps handle for you. Each was seen in practice.

- **User tours cover the page on a user's first visit.** The tour backdrop blocks clicks and appears in screenshots.
  Behat disables tours; a script must mark the tours complete for its test users first, or close the tour.
- **Wait for network idle before typing a password.** Core's `togglesensitive` module replaces the password input
  through `outerHTML` after load, discarding anything typed earlier. Assert the field's value before submitting.
- **Select buttons by role and name.** `page.getByRole('button', {name: 'Save changes'})`; "the submit button" is
  never unique on a Moodle page.
- **Read a form's action with `getAttribute('action')`.** `form.action` is shadowed when the form has a hidden input
  named `action`, which many Moodle forms do.
- **Quiz answer radios have no `label[for]`**; locate them by their `name` and `value` attributes.
- **Visibility is measured with `document.elementFromPoint()`, not a bounding-rectangle test.** Boost's navbar is
  fixed at the top and the block drawer sits outside `#page`, so an element can be inside the viewport and still be
  covered.
- **Scripts that create data use the generators through a PHPUnit or Behat run, never a CLI script against the
  site.** A script that requires `config.php` writes to the live database.
