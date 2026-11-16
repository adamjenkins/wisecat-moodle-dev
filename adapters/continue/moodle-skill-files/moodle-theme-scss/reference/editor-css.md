# Editor content CSS

Read this when content inside the TinyMCE editor must be styled by the theme (typeface, link colour, dark mode), or
when the editor lost its Bootstrap styles after a theme change.

Evidence: read in `public/lib/classes/output/theme_config.php` (`editor_css_url()`, `editor_css_files()`,
`editor_scss_to_css()`, `get_css_content_editor()`), `public/lib/editor/tiny/` and `public/theme/boost/scss/editor.scss`
on 5.3.0, with Boost's 5.2 `editor.scss` read for comparison. **Nothing in this file was run**: no theme editor sheet
was built or loaded for it.

## How the editor gets its styles

1. `editor_tiny` passes `$PAGE->theme->editor_css_url()` to TinyMCE as its only `content_css`. The content area is an
   iframe, a separate document: nothing from the page's main stylesheet reaches it, and no theme `post.scss` rule
   applies inside it.
2. The URL is `/theme/styles.php/<theme>/<rev>/editor` (or `editor-rtl`); in theme designer mode
   `styles_debug.php?theme=...&type=editor`.
3. The sheet is built by `get_css_content_editor()` by concatenating, in this order:
   - every editor plugin's and editor sub-plugin's `editor_styles.css`;
   - each parent theme's `$THEME->editor_sheets` (`<parent>/style/<name>.css`), base parent first;
   - this theme's `editor_sheets`;
   - the compiled `$THEME->editor_scss`.
   The result goes through `post_process()`, so `[[pix:]]`, `[[font:]]`, `csspostprocess` and the RTL flip apply. It is
   not minified.
4. `editor_scss` is resolved differently from `editor_sheets`: the theme's own list if it sets one, otherwise the
   list of the first parent that has one, searching from the base parent towards the nearest (with
   `$THEME->parents = ['mid', 'boost']`, Boost's list wins over `mid`'s), **and the files are read from the directory
   of whichever theme supplied the list** (`editor_scss_to_css()`).
5. The editor SCSS is compiled with a bare compiler: no pre-SCSS callback, no extra-SCSS callback, no theme settings,
   and only the directory of the file as import path. A compile error is only a developer debugging message
   ("Error while compiling editor SCSS").

What Boost's `scss/editor.scss` contains:

| 5.2 | 5.3 |
|---|---|
| `$code-color`, all of Bootstrap (`@import "bootstrap/bootstrap"`), a table border reset, an inline-code rule | design system token variables (no custom properties, no component CSS), `moodle/font-stack`, `moodle/fonts` (Noto), `$code-color`, all of Bootstrap from `lib/bundles`, `moodle/font-stack-lang`, `moodle/colour-mode`, the same two rules, then `moodle/dark` last |

Neither imports `moodle.scss` or a preset. So inside the editor iframe:

- Bootstrap's stock palette applies, not the site's brand colour or the preset's variable overrides.
- **5.3+:** `--mds-*` custom properties are not defined, and `--bs-*` hold Bootstrap's own values (the official
  colour modes guide records this as a known limitation). A rule for editor content needs a literal or a `--bs-*`
  property, with a `[data-bs-theme="dark"]` correction where needed.

## The default: leave it alone

A child of Boost that does not mention `editor_scss` gets Boost's `editor.scss`, compiled from Boost's directory. That
is the right choice unless the theme must change how content looks while it is being edited.

## Recipe: add to Boost's editor styles

Read in the source, not run: no child editor sheet was built for this recipe.

```php
// config.php
$THEME->editor_scss = ['editor'];
```

```scss
// scss/editor.scss in the child theme.
@import "../../boost/scss/editor";          // Bootstrap, and on 5.3 the fonts and the dark palette.

body.mce-content-body {
    font-family: "My Sans", system-ui, sans-serif;
}

[data-bs-theme="dark"] body.mce-content-body a {
    color: var(--bs-link-color);
}
```

- The relative import works when the theme is installed beside Boost in `public/theme/`. A theme installed in an
  alternative theme directory (`$CFG->themedir`) is not beside Boost, and the path does not resolve.
- A custom font also needs its `@font-face` rule in this file; the main stylesheet's rule is not in the iframe.
  `[[font:theme|...]]` works here.
- Small static additions can instead go in a plain `style/editor.css` named in `$THEME->editor_sheets = ['editor'];`.
  Parents' editor sheets and Boost's `editor_scss` are still included, so nothing is lost.
- The file is linted with the rest of `scss/`.

## Dark mode in the editor (5.3)

- The mode is read once from `data-bs-theme` on the page's `<html>` when the editor is created. It selects the
  TinyMCE skin (`oxide` or `oxide-dark`) and is copied onto the editor container and the iframe's root element. The
  page's `lang` is copied to the iframe root too, which is what makes `:lang(ja)` font rules work inside the editor.
- Switching the page's colour mode afterwards does not re-skin an open editor; a reload does.
- `public/lib/editor/tiny/editor_styles.css` hard-codes light colours and adds `[data-bs-theme="dark"]` counterparts
  that use `--bs-*` properties.
- On 5.2 the skin is always the light one and nothing sets the attribute.

## Traps

| Trap | Symptom | Fix |
|---|---|---|
| `$THEME->editor_scss = ['editor'];` in a child that ships no `scss/editor.scss` | The list comes from the child, so the file is looked for in the child's directory; nothing is compiled and editor content is left with only the editor plugins' static CSS: no Bootstrap, and on 5.3 no Noto font and no dark palette | Remove the line, or ship the file |
| Expecting a brand colour or font setting to show in the editor | Editor content keeps Bootstrap's defaults: the editor SCSS is compiled without the pre and extra callbacks | Write the value into `scss/editor.scss`, or substitute a placeholder in the theme's `csspostprocess` function, which does run on editor CSS |
| `var(--mds-...)` in a rule meant for editor content | Undefined inside the iframe | A `--bs-*` property or a literal with a dark correction |
| Styling `.mce-content-body` from `post.scss` | No effect: that selector lives in the iframe | Put the rule in the editor SCSS |
| Copying Boost's `editor.scss` into the child instead of importing it | The copy carries version-specific import paths (`bootstrap/bootstrap` on 5.2, `lib/bundles` on 5.3) and fails on the other version | Import Boost's file by relative path |
| Checking editor styles without purging | The editor sheet is cached under the theme revision like the main sheet | Purge theme caches, or use theme designer mode |

Related: dialogues, modals and drawers that an editor plugin adds sit on the main page and are styled by the main
stylesheet as usual.

Official note on the iframe palette: https://moodledev.io/docs/5.3/guides/colourmodes (section "Editor content").
