# Parameter and return descriptions

Read this when you choose a `PARAM_*` type, describe nested, optional or nullable structures, return warnings, or
need to explain an "Invalid parameter value detected" or "Invalid response value detected" error.

Everything here was read in `public/lib/external/classes/external_api.php` (`validate_parameters()`,
`clean_returnvalue()`) and `public/lib/classes/param.php` (`validate_param()`), 5.3.0; the same code is in 5.2.

## How validation decides

- A scalar is accepted only if `clean_param($value, $type)` returns the same string. Otherwise
  `invalid_parameter_exception` ("Invalid parameter value detected"), or `invalid_response_exception` ("Invalid
  response value detected") for a return value. `debuginfo` names the path (`items => 0 => name => ...`) when the
  site has debugging on.
- `PARAM_BOOL` accepts `true`, `false`, `0`, `1`, `'0'`, `'1'` and is returned as a PHP bool.
- `PARAM_FLOAT` accepts PHP numbers and numeric strings with a dot; `'1,5'` is rejected.
- A single structure rejects keys it does not describe in parameters ("Unexpected keys (x) detected in parameter
  array"), but silently drops undescribed keys in return values.
- A multiple structure is re-indexed from 0 in both directions: string keys are lost.

## Choosing a type

| Value | Type | Notes |
|---|---|---|
| Record id, count, timestamp | `PARAM_INT` | `'12abc'` is rejected, not truncated |
| Yes/no flag | `PARAM_BOOL` | |
| Decimal | `PARAM_FLOAT` | Dot decimal only; `PARAM_LOCALISEDFLOAT` is for form input, not web services |
| Free text from a person (names, messages, answers) | `PARAM_RAW` | Escape at every sink; say why in a comment |
| HTML the caller authored | `PARAM_RAW` plus a format parameter | Clean on output with `format_text()` |
| Machine key, enum value, short code | `PARAM_ALPHANUMEXT` | `a-zA-Z0-9_-` only; drops `.` |
| Component name | `PARAM_COMPONENT` | |
| Plugin or area name | `PARAM_PLUGIN`, `PARAM_AREA` | |
| Capability name | `PARAM_CAPABILITY` | Must exist on the site |
| Language string id | `PARAM_STRINGID` | |
| File name, file path | `PARAM_FILE`, `PARAM_PATH` | |
| Absolute URL | `PARAM_URL` | `PARAM_LOCALURL` for this site only |
| Email | `PARAM_EMAIL` | |
| Username | `PARAM_USERNAME` | Lower-cases; drops characters such as `+` unless `extendedusernamechars` is on |
| Comma list of ints | `PARAM_SEQUENCE` | |
| Base64 blob | `PARAM_BASE64` | |

`PARAM_TEXT` and `PARAM_NOTAGS` strip tags. Text from a person often contains `<` followed by a letter (`a<b`,
`<3`, an HTML example in a forum question), and stripping it changes the value, so the whole call is refused. They
are safe only for values that never contain angle brackets, such as a title you generated.

Deprecated types (emit a deprecation notice on 5.2 and 5.3): `PARAM_CLEAN`, `PARAM_INTEGER`, `PARAM_NUMBER`,
`PARAM_ACTION`, `PARAM_FORMAT`, `PARAM_MULTILANG`, `PARAM_CLEANFILE`.

## Required, optional, default, null

| Constant | In parameters | In returns |
|---|---|---|
| `VALUE_REQUIRED` (default) | Missing key: "Missing required key in single structure: x" | Missing key: invalid response |
| `VALUE_DEFAULT` with a default | Missing key gets the default, validated | Missing key gets the default |
| `VALUE_OPTIONAL` | Allowed inside nested structures; at the top level of `external_function_parameters` it triggers "invalid OPTIONAL value specified" under developer debugging | Key may be absent |

- The `execute()` signature must give a PHP default for every `VALUE_DEFAULT` parameter, in the same order as
  `execute_parameters()`, because `call_external_function()` passes the validated values positionally.
- `external_value` allows `null` by default (`NULL_ALLOWED`, fifth constructor argument): a client can send null
  for a required scalar and validation returns null. If `execute()` has a typed `int $courseid`, PHP then throws a
  `TypeError`. Pass `NULL_NOT_ALLOWED` where null makes no sense. Structures default to `NULL_NOT_ALLOWED`.

## Nested structures

```php
public static function execute_parameters(): external_function_parameters {
    return new external_function_parameters([
        'cmid' => new external_value(PARAM_INT, 'Course module id'),
        'answers' => new external_multiple_structure(
            new external_single_structure([
                'questionid' => new external_value(PARAM_INT, 'Question id'),
                'response'   => new external_value(PARAM_RAW, 'Free text answer, escaped on output'),
                'flagged'    => new external_value(PARAM_BOOL, 'Flagged', VALUE_DEFAULT, false),
            ]),
            'Answers',
            VALUE_DEFAULT,
            []
        ),
    ]);
}
```

## Formatted text and warnings in returns

```php
use core_external\external_format_value;
use core_external\external_warnings;

public static function execute_returns(): external_single_structure {
    return new external_single_structure([
        'id'          => new external_value(PARAM_INT, 'Item id'),
        'name'        => new external_value(PARAM_RAW, 'Name, formatted with format_string'),
        'intro'       => new external_value(PARAM_RAW, 'Intro, formatted with format_text'),
        'introformat' => new external_format_value('intro'),
        'warnings'    => new external_warnings(),
    ]);
}
```

`external_warnings` describes a list of `item`, `itemid`, `warningcode`, `message`. Use it for partial success
("3 of 5 saved") instead of throwing, which stops the whole call.

## Exporters

`core\external\exporter` subclasses build both the description (`get_read_structure()`) and the data
(`export()`), and format text and strings with the context they are given. Use them when a persistent or a template
context and a web service return the same shape.

The course data that `block_myoverview` gets back (fields such as `fullname`) uses numeric entities (`&#60;`) instead
of named ones (`&lt;`) on 5.2.x and 5.3; a client or test that compares the encoded text must expect that. The upgrade
note is filed under `block_myoverview` in `UPGRADING.md` of both branches (MDL-79755); whether other exporters
changed was not checked.
