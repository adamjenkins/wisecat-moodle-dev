# PHP version changes that affect Moodle plugins

Read this when moving code to a newer PHP version, or when PHP itself (not Moodle) emits the deprecation or error.

The PHP floor is set by Moodle, per branch, in `public/admin/environment.xml`: PHP 8.3.0 for 5.2 and 5.3, with 8.4
also supported (moodledev.io release notes for 5.2 and 5.3). Write code for the lowest PHP of the lowest Moodle
branch in `$plugin->supported`, and test on the highest PHP each branch supports, where new deprecations appear.
The PHP facts below are from the PHP migration guides (https://www.php.net/manual/en/migration84.php and the
earlier ones), not from Moodle.

## PHP 8.4 (supported by Moodle 5.2 and 5.3)

| Change | Symptom | Fix |
|---|---|---|
| Implicitly nullable parameter (`string $x = null`) deprecated | "Implicitly marking parameter $x as nullable is deprecated" | `?string $x = null` |
| `E_STRICT` constant deprecated | Deprecation where the constant is used | Remove it; it has had no effect since PHP 8.0 |
| `trigger_error(..., E_USER_ERROR)` deprecated | Deprecation | Throw an exception |
| `fputcsv()`, `fgetcsv()`, `str_getcsv()` relying on the default `$escape` | Deprecation | Pass `escape: ''` (or the old `'\\'` explicitly) |
| `xml_set_*_handler()` with a method-name string | Deprecation | Pass a callable: `[$this, 'method']` or `$this->method(...)` |
| `DatePeriod` constructed from an ISO 8601 string | Deprecation | `DatePeriod::createFromISO8601String()` |
| `mysqli_ping()`, `mysqli_kill()`, `mysqli_refresh()` deprecated | Deprecation in custom DB code | Use `$DB`; plugins should not call mysqli directly |
| New: `mb_trim()`, `mb_ltrim()`, `mb_rtrim()`, `array_find()`, `array_any()`, `array_all()`, property hooks, asymmetric visibility | Not available on 8.3 | Do not use while 8.3 is the floor |

## PHP 8.3 (floor for Moodle 5.2 and 5.3)

| Change | Symptom | Fix |
|---|---|---|
| `get_class()` and `get_parent_class()` without arguments deprecated | Deprecation | `static::class`, `self::class`, `get_parent_class($this)` |
| New: typed class constants, `#[\Override]`, `json_validate()`, dynamic class constant fetch (`$class::{$name}`) | Usable now | `#[\Override]` on methods that override a parent catches a parent rename at compile time; core uses it |

## PHP 8.2

| Change | Symptom | Fix |
|---|---|---|
| Dynamic properties on a class deprecated | "Creation of dynamic property X::$y is deprecated" | Declare the property, use `\stdClass`, or add `#[\AllowDynamicProperties]` as a last resort |
| `${var}` string interpolation deprecated | Deprecation | `{$var}` |
| `utf8_encode()`, `utf8_decode()` deprecated | Deprecation | `core_text::convert($s, 'ISO-8859-1', 'UTF-8')` or `mb_convert_encoding()` |
| Partially supported callables (`'self::method'`, `[$obj, 'parent::method']`) deprecated | Deprecation | `[self::class, 'method']`, a closure |

## PHP 8.1

| Change | Symptom | Fix |
|---|---|---|
| Passing `null` to a non-nullable parameter of an internal function (`strlen(null)`, `trim(null)`, `str_replace(..., null)`) deprecated | "Passing null to parameter #1 ... is deprecated", often from values read from the DB | Cast or default: `trim((string) $value)`, `$value ?? ''` |
| Return-type mismatch on classes implementing internal interfaces (`Iterator`, `ArrayAccess`, `Countable`, `JsonSerializable`) | "Return type ... should either be compatible" | Declare the return type, or `#[\ReturnTypeWillChange]` while you still support PHP 8.0 |
| Returning by reference from a `void` function deprecated | Deprecation | Remove the `&` |
| `$GLOBALS` cannot be written as a whole | Error | Write individual globals |

## PHP 8.0

| Change | Symptom | Fix |
|---|---|---|
| `each()`, `create_function()` removed | Fatal | `foreach`, closures |
| String-to-number comparison changed (`0 == 'a'` is false) | Logic changes silently | Compare with `===` after explicit casts |
| Arithmetic on non-numeric strings throws `TypeError` | Fatal | Validate input with `PARAM_INT`/`PARAM_FLOAT` |
| Named arguments | Parameter names become part of a function's contract | Core uses named arguments itself (`get_plugins_with_function(function: ..., migratedtohook: true)`); renaming a parameter of a public plugin API is a breaking change |
| Required parameter after an optional one deprecated | Deprecation | Reorder, or make the later one optional too |

## Finding PHP problems before CI does

```bash
# Run PHP's own linter for the target version over the plugin.
find . -name '*.php' -not -path './vendor/*' -print0 | xargs -0 -n1 php8.4 -l | grep -v '^No syntax errors'
# Then the Moodle coding standard:
moodle-plugin-ci phpcs --max-warnings 0
```

Deprecations from PHP appear only when the code path runs; PHPUnit with `DEBUG_DEVELOPER` on the highest PHP of
each Moodle branch is the real check (`moodle-ci-matrix`).
