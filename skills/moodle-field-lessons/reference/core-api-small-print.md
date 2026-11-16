# Core API and PHP small print, and calling core AI from a plugin

Read this when a core function behaves differently from what its name suggests (users, tokens, enrolments,
tables, page properties), when PHP itself surprises you inside Moodle code, or when a plugin calls the core AI
subsystem.

Samples are valid on Moodle 5.2 and 5.3; source lines were read in 5.3.0 unless marked.

## Users, tokens, enrolment

- **`user_create_user($user, false)` stores the password verbatim** (the second argument is
  `$updatepassword`); pass `true` so it is hashed. **5.3+:** the function is deprecated for
  `\core\user::create_user()` (guard with `method_exists()`, `moodle-plugin-development` version notes).
- **`core_external\util::generate_token()` always inserts a new row**; it never reuses an existing token. Track every
  token you mint so you can revoke it (`moodle-web-services`).
- **Another user's timezone:** if `empty($tz) || $tz == 99`, use `core_date::get_server_timezone()`;
  `get_user_timezone(99)` resolves through the viewer's `$USER->timezone`, not the other user's.
- **The enrolment welcome message throws for a user with no email address** when the enrolment runs outside a
  database transaction: `send_course_welcome_message_to_user()` calls `message_send()`, the email processor
  fails, and the message manager throws `moodle_exception` "Message was not sent."; inside a transaction the
  message is buffered until the commit instead (`public/lib/enrollib.php`,
  `public/lib/classes/message/manager.php`, `send_message_to_processors()`; read in 5.3.0, not run). An importer
  that enrols users without email first sets the enrol instance's `customint1` to `ENROL_DO_NOT_SEND_EMAIL`.
- **`$USER` is cached in the session**: a database change to the current user's record is not visible to sessions
  already logged in.

## Pages, tables and output objects

- **`empty()` and `isset()` on `moodle_page` magic properties** (`$PAGE->cm`, `pagetype`, `url`, ...) are always
  "not set": `moodle_page` has `__get()` but no `__isset()` (`public/lib/pagelib.php`, 5.3.0). Read the property
  into a variable, then test it.

  ```php
  $cm = $PAGE->cm;
  if ($cm) {
      // In an activity.
  }
  ```

- **`sql_table::out($pagesize, $useinitialsbar)` passes its second argument to the initials bar**, overriding an
  earlier `initialbars(false)` (`public/lib/table/classes/sql_table.php:211`): pass `false` there.
- **Core `export_for_template()` results are often `stdClass`, not arrays** (`action_link` gives
  `$data->attributes`): read the method before asserting on it.
- **Core string `datechanged` is deprecated from 5.2** (`public/lang/en/deprecated.txt`, 5.2 and 5.3), and using it
  adds a notice that fails strict test runs; reset status items use the module's own string.

## PHP inside Moodle

- **A throwing `finally` replaces the original exception**; keep cleanup code non-throwing.
- **`end()` and `reset()` take arrays by reference and throw on a `readonly` property**
  ("Cannot modify readonly property"). Use `array_key_last()` and `$array[array_key_last($array)]`, or copy the
  array to a local variable first.
- **Resolve a class's fully qualified name from its `namespace` line**, not from its path; some core classes live
  in a directory that does not match their namespace. `class_exists()` autoloads as a side effect, so probe one
  name per fresh process.
- **Do not use PCRE `\p{Han}` to mean ideographs**: it also matches CJK punctuation such as `、` and `。`. Use
  explicit ranges and print sample matches before trusting counts.
- **Third-party libraries bundled in core have their own small print.** `\Firebase\JWT\JWT::decode($jwt, $keys,
  $headers)` fills `$headers` only when the variable already holds an object, so pass `$headers = new \stdClass();`
  (`public/lib/php-jwt/src/JWT.php`, `decode()`, 5.3.0); a null variable stays null. The `mod_lti` test generator
  sets no `tooldomain` on the tool types it creates (`public/mod/lti/tests/generator/lib.php`), so a test that
  matches tools by domain sets it itself. Read the library code, not its README.
- **Keep `defined('MOODLE_INTERNAL') || die();` only in files that run code at require time**; let phpcs decide,
  and run it at once on code copied from another plugin (siblings carry unfixed warnings).
- **No scaffolding placeholders in file headers**, and one canonical `@copyright` line per author.

## Calling core AI from a plugin

The AI subsystem (`public/ai/classes/manager.php`, present on 5.2 and 5.3) runs actions through providers the admin
configured.

- **Check before calling**: `$manager->is_action_available($actionclass)`, then the user policy
  (`\core_ai\manager::get_user_policy_status($userid)`; show the policy and record acceptance with
  `user_policy_accepted()` if needed), then `$manager->process_action($action)`.

  ```php
  $manager = \core\di::get(\core_ai\manager::class);
  $action = new \core_ai\aiactions\generate_text(
      contextid: $context->id,
      userid: $USER->id,
      prompttext: $prompt,
  );
  if (!$manager->is_action_available(\core_ai\aiactions\generate_text::class)
          || !\core_ai\manager::get_user_policy_status($USER->id)) {
      return null;
  }
  try {
      $response = $manager->process_action($action);
  } catch (\Exception $e) {
      return null;
  }
  ```

- **`process_action()` can throw instead of returning a failed response.** The core providers pass the code of a
  caught HTTP client exception to `\core_ai\error\factory::create()`, which throws `\InvalidArgumentException`
  when the code is 0, as it is for a request that never got an HTTP status (blocked or refused before a response)
  (`public/ai/provider/openai/classes/abstract_processor.php`, `query_ai_api()`;
  `public/ai/classes/error/factory.php:57`; read in 5.2 and 5.3.0, not run). Catch `\Exception`; catching
  `\moodle_exception` misses it.
- **The manager cannot be told to use one provider instance**; it picks among the enabled providers for the action.
  A plugin that must pin a provider calls that provider's processor itself and records the action, which is outside
  the public API.
- **A test needs no `aiprovider_*` plugin**: `create_provider_instance()` checks only that the class exists and is a
  `\core_ai\provider`, and the processor resolves to `<provider top namespace>\process_<action>`
  (`public/ai/classes/manager.php`, `create_provider_instance()` and `process_action()`), so a provider and
  processor class pair inside your plugin's tests runs through the real manager.
- **A placement that returns `generate_text` from `get_actions_available()`** adds a second action select to
  activity forms and turns on the TinyMCE AI button even when the editor placement is off; returning nothing makes
  `is_action_enabled_in_context()` false for your action on saved activities, because a course module's
  `enabledaiactions` lists only declared actions (`public/course/modlib.php`, `public/ai/classes/manager.php`). A
  plugin that is not a placement reads the activity's `enableaitools` setting directly.

## References

- https://moodledev.io/docs/apis/subsystems/ai
- https://moodledev.io/docs/apis/core/user
- https://moodledev.io/docs/apis/plugintypes/ai
