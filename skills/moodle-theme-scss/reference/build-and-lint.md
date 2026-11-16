# Building, linting and the precompiled fallback

Read this when stylelint fails on theme SCSS or a line must be silenced, when setting up or reading a CI lint result
for a theme, when you need to see why the SCSS did not compile, or when you are considering a precompiled fallback
stylesheet for the theme.

Evidence: core's `.stylelintrc`, `Gruntfile.js` and `.grunt/tasks/` were read in 5.2 and 5.3.0 (the stylelint
configuration is identical in both; stylelint 15 with `stylelint-csstree-validator` 3 in both `package.json` files).
moodle-plugin-ci statements are from reading version 4.5.11. Running core's stylelint over a theme's `scss/` and
seeing a rule fire, and the silent compile fallback, were **run on 5.3.0**. The precompiled-fallback recipe was not
run.

## What gets linted

- Core's Gruntfile decides per component. For a theme: if `scss/` exists, `scss/*.scss` and `scss/**/*.scss` are
  linted and no CSS at all; if there is no `scss/`, only `style/*.css`. A `styles.css` in a theme root is never
  linted. For every other plugin type only the root `styles.css` is linted.
- "Is this a theme" is a path test: the component directory must start with `public/theme/`. Lint the theme where it
  is installed in a Moodle checkout; a copy elsewhere is not treated as a theme.
- `moodle-plugin-ci grunt` runs the `stylelint` task whenever the plugin has any `.css` or `.scss` file, with core's
  rules. The upstream workflow template runs it with `--max-lint-warnings 0`, so warnings fail the build.
- Locally, from the Moodle root with Node dependencies installed (Node 22 for both versions):

```bash
npx stylelint "public/theme/mytheme/scss/**/*.scss"
```

- To keep a file out (an intentionally invalid test fixture, vendored SCSS): list it in a `.stylelintignore` in the
  theme root, paths relative to the theme. Core's `grunt ignorefiles` merges it into the root ignore file, together
  with every location named in a `thirdpartylibs.xml`. Lines starting with `#` or `!` are dropped.
- Nothing compiles a third-party theme's SCSS in CI's grunt step: core's `sass` task builds only Boost's default
  preset. A compile error is therefore invisible to the lint step; it takes a PHPUnit compile test to catch it
  (`moodle-theme-testing-release`).

## Rules that trip theme authors

From `.stylelintrc` at the Moodle root. The syntax is `postcss-scss`.

| Rule | Meaning | Typical offence |
|---|---|---|
| `declaration-no-important` | no `!important` | utility overrides |
| `block-opening-brace-newline-after`, `declaration-block-single-line-max-declarations: 1` | no single-line rule blocks; one declaration per line | `.a { color: red; }` |
| `indentation: 4` | four spaces | two-space or tab indentation |
| `function-url-scheme-disallowed-list: ["data"]` | no `data:` URLs | inline SVG backgrounds |
| `time-min-milliseconds: 100` | durations of at least 100 ms | `transition: .05s` |
| `unit-disallowed-list: ["pt"]` | no `pt` | print styles |
| `declaration-block-no-duplicate-properties` | no repeated property in a block | fallback-then-override pairs |
| `declaration-block-no-shorthand-property-overrides` | a shorthand must not follow its longhand | `border-left-color` then `border` |
| `property-no-unknown`, `selector-type-no-unknown`, `selector-pseudo-class-no-unknown`, `unit-no-unknown` | known names only | vendor experiments, typos |
| `csstree/validator` | values must parse as valid CSS for the property | `container-type`, `@container`, `clamp()` in `font-size` were rejected on 5.3 |
| `block-no-empty`, `no-empty-source` | no empty blocks or files | placeholders |
| `color-hex-case: lower`, `color-hex-length: short`, `length-zero-no-unit`, `max-line-length: 132`, `no-extra-semicolons` | warnings | `#FFFFFF`, `0px`, long selectors |
| `selector-list-comma-newline-after` | one selector per line in a list | `.a, .b {` |
| `at-rule-empty-line-before` | blank line before most at-rules that are not inside a block | `@include` at top level directly after a rule |

Shape that passes:

```scss
.mytheme-card,
.mytheme-panel {
    padding: 0 1rem;
    border: 1px solid var(--bs-border-color);
    transition: opacity .2s ease-in-out;
}
```

## Silencing a line

Core does this itself; use the narrowest form.

```scss
.mytheme-force {
    display: none !important; /* stylelint-disable-line declaration-no-important */
}

.mytheme-grid {
    container-type: inline-size; /* stylelint-disable-line */
}

/* stylelint-disable declaration-no-important */
.mytheme-print-only {
    display: block !important;
}
/* stylelint-enable */
```

- For syntax the validator does not know, core writes a bare `/* stylelint-disable-line */`
  (`public/theme/boost/scss/moodle/reportbuilder.scss`, 5.3.0) and, elsewhere, the scoped
  `/* stylelint-disable-line csstree/validator */`. Either silences the line.
- The comment must be `/* */` on the same line as the declaration. In SCSS a `//` comment is also accepted by
  stylelint for directives, and core uses both; `/* */` is the form that works in plain CSS too.
- SCSS returned as a string from a PHP callback is never linted. Keep such strings short and put real rules in files.

## Seeing why the SCSS did not compile

A compile error never reaches the page. `theme_config::get_css_content_from_scss()` catches the exception, calls
`debugging('Error while compiling SCSS: ...', DEBUG_DEVELOPER)` and returns false; `get_css_content()` then uses the
precompiled CSS of the parents. `public/theme/styles.php` defines `NO_DEBUG_DISPLAY`, so in a browser the message
exists only in the PHP error log. Seen on 5.3.0: with a broken `post.scss` the site served stock Boost CSS with none
of the theme's rules; with developer debugging a message named the error; with debugging off there was nothing.

Ways to see the message:

1. Command line, with `$CFG->debug = E_ALL;` and `$CFG->debugdisplay = 1;` in a development `config.php`:
   `php admin/cli/build_theme_css.php --themes=mytheme --direction=ltr` (add `--verbose` for progress). The script
   exists on 5.2 and 5.3. It stores what it built in the cache and raises the theme's sub-revision, including when
   the build was the fallback, so run it again (or purge caches) after the fix.
2. The PHP error log of the web server, after requesting the stylesheet URL.
3. A PHPUnit test that calls `theme_config::load('mytheme')->get_css_content()`: an unexpected `debugging()` call
   fails the test and prints the message, and an assertion on one of the theme's own selectors catches the fallback
   even if debugging is off.
4. For an uploaded preset, the settings page itself: saving compiles the preset and shows the compiler message.

Messages and their usual cause:

| Message contains | Cause |
|---|---|
| "file not found for @import" | An import path that exists on the other Moodle version only, or a file outside the import paths |
| "Undefined variable" | A Bootstrap, Boost or token variable used in pre-SCSS; a 5.3-only variable on 5.2; a `$mds-*` variable on the plain preset |
| "Undefined mixin" | `dark-mode` on 5.2; a mixin used in pre-SCSS |
| an argument "must be a color" or a similar type error | A colour function applied to a variable that holds `var(...)` on 5.3 |
| "Can't import scss file" (a separate debugging message, not a failure) | An import that resolves outside the theme directories (**5.3+:** and outside `lib/bundles`), or without the `.scss` extension; the import is skipped |

The exact wording of the type-error messages was not captured; the first row was seen on 5.3.0.

Other facts about the build:

- `$CFG->pathtosassc` makes core use an external SassC binary instead of scssphp (`public/lib/classes/scss.php`). A
  theme that compiles under one may fail under the other; nothing here was checked with SassC.
- In theme designer mode the SCSS is compiled on request and cached for a few seconds, with source maps in the LTR
  build; in production the compile happens once per theme revision and direction.
- With `$THEME->usefallback` on (Boost sets it, children inherit it), the first stylesheet request after a purge can
  be answered with the previous build while the new one compiles; the next request gets the new one. A theme may set
  `$THEME->usefallback = false;` while it is being developed. Caches and revisions are covered in
  `moodle-theme-development`.

## A precompiled fallback stylesheet: usually not worth it

What the mechanism is:

- `$THEME->precompiledcsscallback` names a function returning CSS. It is used only when the SCSS compile returns
  nothing. The result still goes through `post_process()`, so `[[pix:]]` and `[[font:]]` in it work.
- `theme_config::get_precompiled_css_content()` **concatenates** the output of every parent's callback, base first,
  and then the theme's own (same code in 5.2 and 5.3). A child cannot replace Boost's fallback, only add to it.
- Boost's callback returns `public/theme/boost/style/moodle.css` (about 1.35 MB), built by core's `grunt sass` from the
  default preset with dart Sass and committed with every change to Boost's SCSS.

Consequences for a child theme:

- Doing nothing, a child inherits Boost's fallback: on a compile failure the site looks like stock Boost.
- A child that returns a full compiled stylesheet makes a failing site serve Boost's CSS plus its own, twice the
  size. If a fallback is wanted at all, it should contain only the child's own rules, compiled against Boost's
  variables.
- The fallback is built with a different compiler (dart Sass) from the one the site uses (scssphp 1.12.1). A file
  that builds with one can fail with the other, and the design system ships a separate legacy entry point for that
  reason.
- Nothing in CI checks that a committed fallback matches the SCSS, and settings (brand colour, uploaded images)
  cannot be in it.
- The large Boost-based themes read for this skill ship no precompiled stylesheet. One of them instead turns
  `usefallback` off on admin settings pages, so an admin sees the real result of a setting change.

If you still want one, the shape core's former Classic theme used on 5.2 was: one entry file importing the same
pieces, in the same order, as the `scss` closure concatenates (`pre`, the preset, `post`), compiled with dart Sass
with the child's and Boost's `scss/` directories as load paths, committed as `style/moodle.css`, and returned by the
callback. The command was not run for this file, and whether the CI grunt step then reports the committed CSS as
changed is unknown.

Official pages: https://moodledev.io/general/development/policies/codingstyle/css and
https://moodledev.io/docs/5.3/apis/plugintypes/theme/styles
