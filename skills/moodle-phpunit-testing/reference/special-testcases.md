# Special test cases

Read this when you test an external function, a routed controller (`route_testcase`), a privacy provider, admin
settings pages, a moodleform, an HTTP client call, a hook listener, or core AI actions.

Sources are the 5.2 and 5.3.0 trees, paths relative to the Moodle root; "seen in practice" marks behaviour observed
on real plugins. 5.3-only additions are in the skill's `versions/moodle-5.3.md`.

## External functions

- Base class: `\core_external\tests\externallib_testcase` (`public/lib/external/tests/classes/externallib_testcase.php`,
  autoloaded in tests on 5.2 and 5.3). The old global `externallib_advanced_testcase` was replaced in 5.1.
- Call `execute()` as the user under test, then `clean_returnvalue()` against `execute_returns()`. Without the clean,
  a field the structure does not declare, or a wrong type, passes the test and fails the real web service call.
- Test the parameter side too: `validate_parameters()` rejects a value that cleaning would change, so free text
  declared `PARAM_TEXT` fails for input with tags. Assert the exception for a bad value and success for a good one.
- One positive test per capability gate and one negative test as a user without it, asserting
  `\required_capability_exception` (not just "an exception").
- A `db/services.php` change is invisible until the plugin version is bumped. In a test, assert the function is
  registered: `$this->assertNotFalse(\core_external\external_api::external_function_info('local_example_get_items',
  IGNORE_MISSING));`.

## Routed controllers (`route_testcase`)

Base class `\core\tests\router\route_testcase` (`public/lib/tests/classes/router/route_testcase.php`, 5.2 and 5.3).

- **Pass `''` as the group path** to `add_class_routes_to_route_loader($class, '')` for page routes. Passing
  `ROUTE_GROUP_PAGE` builds a pattern starting `//` that never matches, so every expected-404 test passes for the
  wrong reason; `null` makes the test case guess the group from the namespace. Always include one 200 case that
  proves the route matched. Seen in practice.
- **A notification queued before `header()` never reaches the response body.** A controller that calls
  `\core\notification::success()` and redirects has nothing to find in the body. Fix: read the queue,
  `$notifications = \core\notification::fetch();`, and assert on its messages. Seen in practice.
- A green `route_testcase` does not prove a routed POST works from a browser: form encoding, sesskey and
  `$CFG->routerconfigured` are outside it. Make one real request.

## Privacy providers

- Base class `\core_privacy\tests\provider_testcase` (`public/privacy/classes/tests/provider_testcase.php`).
- Build data with the plugin generator for two users, then assert for each provider method: the contexts found
  for user A, the export for A contains A's rows and not B's, delete for A leaves B's rows.
- `contextlist::get_contextids()` returns numeric strings, and `assertContains()` is strict, so
  `assertContains($context->id, $ids)` fails. Fix: `assertContains((string) $context->id, $ids)` or
  `array_map('intval', $ids)`. Seen in practice.
- Every table in `get_metadata()` should be exported and deleted by some method; a provider test that covers only one
  table does not show the drift. The provider rules themselves are in `moodle-privacy-gdpr`.

## Admin settings

- `admin_settingpage` autoloads, but `admin_get_root()` and the setting classes in `lib/adminlib.php` do not. A test
  that builds settings passes inside the full suite (another file loaded `adminlib.php`) and fails alone. Fix: require
  it in `setUp()`. Seen in practice.
- Render every settings page in a test. Some settings fail only when rendered (`admin_setting_filetypes` needs
  `lang_string` labels; a `admin_setting_configtext` regex paramtype with a trailing modifier aborts install):

  ```php
  #[\Override]
  protected function setUp(): void {
      global $CFG;
      parent::setUp();
      require_once($CFG->libdir . '/adminlib.php');
      $this->resetAfterTest();
  }

  public function test_settings_page_renders(): void {
      $this->setAdminUser();
      $page = admin_get_root(true, true)->locate('local_example_settings');
      $this->assertInstanceOf(\admin_settingpage::class, $page);
      $this->assertStringNotContainsString('[[', $page->output_html());
  }
  ```

- New settings reach the test site only after a version bump and re-init, like schema changes.
- `admin_setting_configmulticheckbox` is unticked until first saved: `get_config()` returns `false` before then and
  `''` after an admin unticks everything. Test both.

## Forms

- `moodleform::mock_submit($data, $files)` replaces `$_POST` (or `$_GET`) and `$_FILES` (`public/lib/formslib.php`,
  5.2). Restore both after the test when later code in the same test reads them, or the next form sees stale input.
- `mock_submit()` adds `sesskey` and `_qf__<formclass>`, but not what the browser would send for disabled or hidden
  elements: `hideIf()` also disables the element, and disabled fields are not posted. Build the data like one real
  browser post, not from the full element list.
- A `\core_form\dynamic_form` is smoke-tested through `\core_form\external\dynamic_form::execute()`, which runs the
  same access checks as the modal; calling the form class directly skips them.

## HTTP clients

```php
$history = [];
['mock' => $mock] = $this->get_mocked_http_client($history);
$mock->append(new \GuzzleHttp\Psr7\Response(200, ['Content-Type' => 'application/json'], '{"ok":true}'));

(new \local_example\remote\client())->send('payload');

$this->assertCount(1, $history);
$this->assertSame('POST', $history[0]['request']->getMethod());
```

- The history is filled only through the by-reference argument, and only when it is an array: the helper adds the
  history middleware when `$history !== null` (`advanced_testcase::get_mocked_http_client()`). An unset variable is
  null, so nothing is recorded and `assertCount(1, $history)` fails on null. Initialise it to `[]`. Seen in practice.
- The mock is installed in the DI container, so the code under test must obtain the client with
  `\core\di::get(\core\http_client::class)`. A `new \core\http_client()` in production code bypasses it and makes a
  real request from the test.

## Hooks

- `$this->redirectHook(\core\hook\output\before_footer_html_generation::class, fn($hook) => $called = true);`
  replaces every listener for that hook during the test; `stopHookRedirections()` ends it.
- To prove the plugin's own listener is registered, do not redirect: dispatch the hook with
  `\core\di::get(\core\hook\manager::class)->dispatch($hook)` and assert the listener's effect. A unit test of the
  callback method alone passes even when `db/hooks.php` is wrong or the version was not bumped.

## Core AI actions

- A fake provider needs no `aiprovider_*` plugin. `\core_ai\manager::create_provider_instance()` checks only that
  the class exists and is a `\core_ai\provider` (`public/ai/classes/manager.php`, 5.3.0), and the processor is
  resolved as `<first namespace segment of the provider class>\process_<action>` (`call_action_provider()`, same
  file). A class pair in your plugin, `local_example\fake_provider` extending `\core_ai\provider` and
  `local_example\process_generate_text` extending `\core_ai\process_base` with `query_ai_api()` returning the
  response data, runs through the real manager. Because the processor must be in the top namespace, it lives in
  `classes/` or in a fixture file you `require_once`; `tests/classes/` autoloads only `local_example\tests\`.
  Read in the source; the pattern was seen working in practice in PHPUnit and in Behat.
- `process_action()` can throw instead of returning a failed response (`\core_ai\error\factory::create()` throws
  `\InvalidArgumentException` for error code 0, which a blocked request carries; `public/ai/classes/error/factory.php`,
  5.3.0). Catch `\Exception`, and test that path.
