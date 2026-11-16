# Setting types for a theme

Read this when choosing an admin setting class for a theme setting, or when a setting saves a value you did not
expect: it lists what each class stores, what it validates and the traps of each.

Constructors and behaviour were read in the 5.3.0 source (`public/admin/classes/setting/setting/<class>.php`) and
in the 5.2 source (`public/lib/adminlib.php`); only the colour picker, select, text and stored-file classes were
put on a page and rendered (on 5.3.0). The class names below are the global names, which exist on 5.2 and 5.3.
**5.3+:** each class also has a namespaced name (`\core_admin\setting\setting\configtext`); a theme that supports
5.2 must not use it.

## What every setting shares

- The first argument is `'theme_<name>/<key>'`. The key becomes the `config_plugins` name. Keep it lower case with
  no underscore prefix games: the key is also the property name on `$theme->settings`.
- Arguments two and three are the visible name and the description. Pass strings from the theme's lang file. The
  description may contain HTML; choice labels may not (see "Select").
- A value is stored as a string. A setting that was never saved has no row: `get_config()` gives `false`.
- `$setting->set_updatedcallback('theme_reset_all_caches')` runs after the admin page saved a value that differs
  from the old one. It does not run for `set_config()`, for `admin/cli/cfg.php`, or when defaults are applied
  during install or upgrade (`admin_apply_default_settings()` calls `write_setting()` only).
- A posted value that fails `validate()` leaves the old value in place and shows the error next to the field.

## Catalogue

| Class | Constructor after name, title, description | Stored value | Notes |
|---|---|---|---|
| `admin_setting_configtext` | `$default, $paramtype = PARAM_RAW, $size = null` | The text | Validation: see "Text patterns" |
| `admin_setting_configtextarea` | `$default, $paramtype = PARAM_RAW, $cols = '60', $rows = '8'` | The text | Same validation as text |
| `admin_setting_confightmleditor` | `$default, $paramtype = PARAM_RAW, $cols, $rows` | HTML | Output with `format_text()`; see "HTML" |
| `admin_setting_configcheckbox` | `$default, $yes = '1', $no = '0'` | `'1'` or `'0'` | Compare as strings or with `!empty()` |
| `admin_setting_configselect` | `$default, $choices` | The chosen key | See "Select" |
| `admin_setting_configmulticheckbox` | `$default, $choices` | Comma-separated keys | Default is an array `['key' => 1]`; read with `explode(',', $value)` |
| `admin_setting_configmultiselect` | `$default, $choices` | Comma-separated keys | Default is an array of keys |
| `admin_setting_configcolourpicker` | `$default, ?array $previewconfig = null, $usedefaultwhenempty = true` | The colour text | See "Colour" |
| `admin_setting_configstoredfile` | `$filearea, $itemid = 0, ?array $options = null` | Path of the first file, such as `/logo.png` | See "Stored file" |
| `admin_setting_scsscode` | `$default, $paramtype = PARAM_RAW` (a textarea) | SCSS text | See "SCSS code" |
| `admin_setting_configthemepreset` | `$default, $choices, $themename` | A preset file name | See "Preset" |
| `admin_setting_configduration` | `$default, $defaultunit = 86400` | Seconds | For a banner timeout or similar |
| `admin_setting_heading` | `$name, $heading, $information` | Nothing | A section title inside a tab; needs a unique name |
| `admin_setting_description` | `$name, $visiblename, $description` | Nothing | Read-only text among the settings |

## Text patterns

`admin_setting_configtext::validate()` has three branches:

1. If the parameter type matches `#^/.*/$#` it is used as a regular expression on the value.
2. If it is `PARAM_RAW`, anything is accepted.
3. Otherwise the value must be unchanged by `clean_param($value, $paramtype)`.

Traps:

- **A pattern with a trailing modifier is not a pattern.** `'/^[\p{L}\p{N}]+$/u'` does not end in `/`, so it falls
  to branch 3 and is passed to `clean_param()` as an unknown type. The symptom is an exception while defaults are
  applied during install or upgrade. Put the modifier inside the pattern: `'/(*UTF)^[\p{L}\p{N}]{3,30}$/'`, or
  `'/(?i)^[a-z]+$/'`.
- **`PARAM_TEXT` and `PARAM_NOTAGS` reject rather than clean.** A value containing a tag is refused with
  "validation error", it is not stripped. That is the right behaviour for a banner text; say so in the description.
- **Use a pattern for anything that goes into CSS.** A length: `'/^\d+(\.\d+)?(px|rem|em|%)$/'`. A font family
  list: `'/^[a-zA-Z0-9 ,\'"-]*$/'`. The pattern on the admin page does not replace the check at the place where the
  value is written into SCSS, because values can also arrive through `set_config()`.
- An empty default with a pattern that does not accept the empty string makes the default itself invalid. Allow
  empty (`*` rather than `+`, or `^$|...`).

## Select

- Keys are strings when read back. Use meaningful keys (`'round'`, `'square'`), not numbers that change meaning
  when an option is inserted.
- **Choice labels are plain text.** Core escapes the label of the default in the "Default:" line and the admin
  search highlights inside labels, so HTML in a label shows as text or is broken. Put markup in the description.
- A posted value that is not among the choices is ignored without an error.
- **A stored value can be outside the current choices** after an option was removed in a new release, or after a
  script wrote it. The reading code needs a final `else` that behaves as the default, and removing an option
  deserves an upgrade step that rewrites the old value.
- For a long generated list (pixel sizes, percentages) build the array with a helper rather than typing it:

```php
$choices = [];
foreach (range(0, 20, 2) as $px) {
    $choices[$px . 'px'] = $px . 'px';
}
```

## Colour

- Accepted: 3 or 6 hex digits with or without `#` (the `#` is added), CSS colour names, `rgb()`, `rgba()`, `hsl()`,
  `hsla()`, `transparent`, `currentColor`, `inherit`. Eight-digit hex is not accepted by the picker.
- **Empty input becomes the default** unless the sixth argument is `false`. With a non-empty default the admin
  cannot clear the field. Two workable designs:
  - Default `''` and the real fallback in SCSS (`$mytheme-accent: #b8410c !default;`). An empty field then means
    "the theme's own colour", and the description says which colour that is. Boost's `brandcolor` works this way.
  - A non-empty default and `new admin_setting_configcolourpicker($name, $title, $desc, '#b8410c', null, false)` when
    empty must be a storable state.
- The fifth argument previews the colour live on the settings page:
  `['selector' => '.navbar', 'style' => 'backgroundColor']`. It affects only the admin page.
- A value such as `inherit` or `currentColor` is valid CSS but makes Sass colour functions (`darken()`, `mix()`,
  `rgba($colour, .5)`) throw, and a compile error means the whole theme falls back to Boost's stock CSS (run on
  5.3.0). If the variable is used in a colour function, accept only hex where the value is written into SCSS.

## Stored file

- Options (the sixth argument) are file manager options: `maxfiles` (default 1), `accepted_types` (default `'*'`;
  use `['web_image']`, or extensions such as `['.svg', '.png']`), `maxbytes`, `subdirs`.
- The files are saved in the system context under the theme's component, in the file area given as the fourth
  argument, at the item id given as the fifth. Keep the item id 0: `theme_config::setting_file_serve()` reads item
  id 0 only.
- The stored value is the path of the first file in the area, or `''` when it is empty. `setting_file_url()`
  returns `null` for an empty value, so test the result before using it.
- **With `maxfiles` above 1 the value names one file only.** To use all the files, read the area:

```php
$fs = get_file_storage();
$files = $fs->get_area_files(context_system::instance()->id, 'theme_mytheme', 'slides', 0, 'filename', false);
foreach ($files as $file) {
    $url = moodle_url::make_pluginfile_url(
        $file->get_contextid(), $file->get_component(), $file->get_filearea(),
        theme_get_revision(), $file->get_filepath(), $file->get_filename()
    );
}
```

  The theme revision sits in the item id position of the URL because `setting_file_serve()` removes the first path
  element as a revision before looking the file up.
- **The updated-callback fires only when the first file changed.** The class compares the content and path hash
  of the file the value names, before and after the save. Adding or replacing a second file leaves the revision
  alone, so cached CSS and cached URLs stay. For a multi-file area, tell admins in the description to purge theme
  caches after changing files, or subclass the setting and call the callback in `post_write_settings()` every
  time.
- The file area must be listed in the theme's `pluginfile` function, or the URL returns 404.

## SCSS code

`admin_setting_scsscode` compiles the text alone and rejects it only for a parser error (an unclosed brace). A
compiler error, such as an undefined variable or mixin, is accepted on purpose, because the text is checked
without the theme's variables. So a saved value can still break the real compile, and the site then shows Boost's
stock CSS with no message unless developer debugging is on. In a Boost child, name the two settings `scsspre` and
`scss` and let Boost's callbacks append them; do not append them again in the child.

## Preset

`admin_setting_configthemepreset` is a select that compiles an uploaded preset with the theme's pre and extra SCSS
before saving. Two facts are hard-coded in it: `default.scss` and `plain.scss` are accepted without compiling, and
the "unchanged, skip validation" test reads `$theme->settings->preset`, so the setting key must be `preset`. The
uploaded files are looked up in the file area `preset` of the theme named in the last argument. How a child theme
offers presets is covered in `moodle-theme-boost-child`.

## HTML

`admin_setting_confightmleditor` stores what the editor produced. Print it with:

```php
$html = format_text((string) get_config('theme_mytheme', 'footnote'), FORMAT_HTML,
    ['noclean' => true, 'context' => context_system::instance()]);
```

`noclean` is appropriate because only users with `moodle/site:config` can change the value. Files embedded through
the editor are not handled by this class: an image pasted into the editor is not saved to a file area. Offer a
separate stored-file setting for images.

## Flags and special cases

- The "advanced" and "locked" flag variants (`..._with_advanced`, `..._with_lock`) are for module defaults. A theme
  has no use for them.
- A custom setting class extends one of the classes above and lives in `classes/` of the theme. Load it with an
  explicit `require_once` at the top of `settings.php`: right after a code update the class autoloader cache can
  still be the old one, and `settings.php` runs during the upgrade (seen as the stated reason in a large Boost
  child theme; not reproduced here).
- `admin_setting_configempty` shows a disabled field; it is used to explain why a setting is unavailable.
