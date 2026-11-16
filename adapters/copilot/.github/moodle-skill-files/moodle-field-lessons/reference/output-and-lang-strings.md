# Output escaping, text formats and lang strings: the small print

Read this when deciding how to escape a value at an output sink, when imported or stored content is shown by core,
when a filter or `noclean` behaves differently for some users, or when a lang string renders wrongly
(`{$a->x}` left in the text, `[[key]]`, wrong language).

The security checklist for sinks is `moodle-security-audit`; the defect classes reviewers catch are in
`moodle-release-preflight`. Samples are valid on Moodle 5.2 and 5.3.

## Escaping at the sink

- **`html_writer::tag()`, `link()` and `select()` escape attributes, not contents.** Wrap user text in `s()` at the
  sink. Do not `s()` a value that is already `format_string()`-ed (it double-encodes `&`).

  ```php
  echo html_writer::tag('option', s($label), ['value' => $id]);
  ```

- **formslib element labels, `select` option texts and `advcheckbox` texts are printed unescaped** (core templates
  print `{{{label}}}`, `{{{text}}}`): pass `s()` or `format_string()` output, never raw user data.
- **`format_string()` strips tags; `s()` escapes them.** Its `<`/`>` handling depends on the
  `formatstringstriptags` site setting (on by default), so "uses `format_string()`" is not an XSS argument on its
  own, and tests written against `s()` output break after migrating to `format_string()`.
- **`fullname()`, `get_string()` and `html_writer` content escape at no layer**, so wrap the composed value in
  `s()`. `format_string(..., ['escape' => false])` cannot undo entities that were encoded before it; for a
  plain-text sink (an email subject, a CSV cell) use `html_entity_decode(format_string(...))`.
- **Modal titles, toasts, `core/notification` strings and `redirect()` messages are HTML sinks** (`moodle-release-preflight`).
- **JSON in a `data-*` attribute needs `JSON_HEX_AMP | JSON_HEX_QUOT | JSON_HEX_APOS | JSON_HEX_TAG`** (`moodle-release-preflight`).
- **Before calling a template's `{{{ }}}` a sink, read `export_for_template()`**; escaping often happens there.
  Prove a finding with a payload through the real page.
- **Widening who sees a stored field is a new output sink.** A column filled from `$e->getMessage()` is untrusted
  text (it can disclose a server path once shown to non-admins); show only plugin-composed messages, and grep every
  writer of the column before widening its audience.

## Content that core renders for you

- **Content you write into core tables is rendered by core, often with `noclean`** (question text, question
  category info). `clean_text()` skips text with no `<`, `>` or `&`, so a Markdown `[x](javascript:...)` imported
  as `FORMAT_MARKDOWN` survives cleaning and becomes a live link. Clean every imported field yourself and convert
  or clamp the format.
- **`FORMAT_*` constants are strings** (`define('FORMAT_HTML', '1')`, `public/lib/weblib.php`, 5.3.0). A strict
  comparison with an int (`$format === 1`) is always false; compare with the constant, or cast both.
- **"Log in as" forces cleaning for the whole session**: `require_login()` sets `$CFG->forceclean`
  (MDL-63786, `public/lib/moodlelib.php`, `require_login()`, 5.3.0), as the `forceclean` site setting does
  everywhere. `format_text()` then ignores `noclean`, and HTMLPurifier strips `data-*` attributes before any
  filter runs. A filter or renderer that relies on `data-*` in stored HTML must survive that, and a bug report
  from an admin using "Log in as" may not reproduce for the real user.
- **Filters emitting tall inline content** (ruby annotations, maths) inside `div.no-overflow` need top padding in
  `styles.css`; the clipping shows in Firefox and is nearly invisible in Chromium:
  `.no-overflow:has(.filter_myplugin-tall) { padding-top: .75em; }`

## Multilang

- **`format_string()` runs filters only when the filter is set to apply to "Content and headings"**
  (`$CFG->stringfilters`); `format_text()` always runs them. A filter that must reach titles says so in its README
  and release notes.
- **Wrap only inline content in `<span lang>`**, one pair inside each block element: `<div lang>` is ignored, and
  spans around blocks are emptied by HTMLPurifier.

## Lang strings

- **Match `{$a}` against `{$a->prop}` to the argument shape** and test the rendered message; nothing checks the
  agreement, and a scalar argument leaves `{$a->title}` literally in the text.

  ```php
  $sink = $this->redirectMessages();
  // Trigger the notification.
  $this->assertStringNotContainsString('{$a', $sink->get_messages()[0]->subject);
  ```

- **Two messages share a string only when `{$a}` means the same in both.** Admin-facing messages and exception
  texts are strings too; reviewers flag literal English.
- **Prove every referenced key exists**, including keys built at runtime, and assert rendered pages contain no
  `[[`. A missing key passes phpcs, CI and every unit test that does not render the template; give each new
  template a test that renders it. Keep keys sorted and check the order programmatically for the whole file, not
  by eye.
- **A lang file changed by a script gets `php -l`**: one unescaped `'` makes every page that loads the component's
  strings fail.
- **A string that names another UI element** ("Click Save changes") quotes that element's label from its lang
  file, not from a design note, or the instruction names a button that does not exist.
- **`get_string()`'s fourth argument is `$lazyload`, not a language** (`get_string($identifier, $component, $a,
  $lazyload)`, `public/lib/moodlelib.php`, 5.3.0). To get a string in another language, use
  `get_string_manager()->get_string($identifier, $component, $a, $lang)`.
- **Values in International English** (licence, organisation); identifiers keep core's US spelling (`license`).
  An identifier is not evidence about prose.
- **"Is X required?" has two authorities**: core's code path (what breaks) and the moodledev.io plugin-type docs and
  contribution checklist (what a reviewer demands). Filters need both `pluginname` and `filtername`, even though
  some core filters omit one.
- **Renames and re-scopes reach past the class.** Renaming a string key, a state key or a constant (or turning a
  constant into a setting) means grepping the old name in `tests/` (helpers that write `$SESSION` directly) and in
  `amd/src` (a hard-coded literal), then exercising the changed path in a browser, not only its first screen.

## References

- https://moodledev.io/docs/apis/subsystems/output
- https://moodledev.io/docs/apis/core/htmlwriter
- https://moodledev.io/general/development/policies/security/crosssite-scripting
- https://moodledev.io/docs/apis/commonfiles (the `lang/en/<component>.php` section)
