# Theme caches, revisions and the serving scripts

Read this when a change still does not show after the "what picks up a change" table in `SKILL.md`, when a
deployment needs the CSS built before the first request, or when working out what a purge really clears.

Source: `public/theme/styles.php`, `public/theme/styles_debug.php`, `public/theme/image.php`,
`public/lib/outputlib.php`, `public/lib/csslib.php`, `public/lib/classes/output/theme_config.php`,
`public/lib/classes/output/renderer_base.php`, `public/lib/mustache/`, `admin/cli/purge_caches.php`,
`admin/cli/build_theme_css.php`, read in 5.3.0. `styles.php`, `styles_debug.php`, `outputlib.php` and both CLI
scripts are byte-identical in the 5.2 source. The silent SCSS fallback and the `brandcolor` rebuild were run on
5.3.0; the stale first load was seen on a 5.x site; the rest was read.

## Two revision numbers

| Revision | Stored as | Bumped by | Invalidates |
|---|---|---|---|
| Global theme revision | `$CFG->themerev` | `theme_reset_all_caches()`: any purge that includes the theme, a setting with that updated callback, toggling theme designer mode | CSS of every theme, images, fonts, theme JavaScript, the server-side Mustache cache directory |
| Per-theme revision | config `themerev` of the plugin `theme_<name>` | `theme_build_css_for_themes()`, which is what `admin/cli/build_theme_css.php` calls | CSS of that one theme only |

- The stylesheet URL is `/theme/styles.php/<theme>/<themerev>_<per-theme rev>/all`, or `all-rtl` for
  right-to-left, so a change in either number makes the browser fetch a new file.
- The official theme page calls the per-theme value `themesubrev`. The code stores it under the name `themerev` in
  the theme's own plugin config.
- In theme designer mode both functions return `-1`, and the page links `styles_debug.php` URLs instead.

## What happens on a stylesheet request

1. If `localcache/theme/<themerev>/<theme>/css/all_<per-theme rev>.css` exists, it is sent with long-lived cache
   headers before Moodle is fully set up.
2. Otherwise Moodle loads, and the request's revision is compared with the current one. A request for an old
   revision is answered without cache headers.
3. If the theme has `usefallback = true`, a fallback file exists in `$CFG->tempdir/theme/<name>/`, and the
   `core/postprocessedcss` cache has nothing for this theme, the fallback file is sent at once with no-store
   headers. The same request then tries to build the new CSS, waiting at most one second for the build lock, and
   does not send the result.
4. Otherwise the request takes the lock `core_theme_get_css_content`, waiting up to two minutes, builds the CSS,
   stores it in the cache and in localcache, writes the unversioned fallback copy to the temp directory, and
   sends it.

What the build concatenates, in order: every plugin's `styles.css`, then that plugin's `styles_<parent>.css` and
`styles_<theme>.css` if it ships them; the parents' `sheets`, base first; the theme's compiled SCSS; the theme's
own `sheets`. Then `[[pix:...]]` and `[[font:...]]` are replaced, `csspostprocess` runs, the CSS is flipped for
right-to-left when needed, and it is minified.

## Three ways the old or the wrong CSS is served

| What you see | Cause | What to do |
|---|---|---|
| Old design on the first load after a purge, correct on the second | Step 3: the temp-directory fallback survives every purge, because purges clear localcache and the caches, not `$CFG->tempdir` | Load twice before taking a screenshot or a computed-style reading. In development set `$THEME->usefallback = false` in the theme. Boost sets `true`, and a child that restates it has the same behaviour |
| Stock Boost with none of the theme's rules | The SCSS compile threw. `get_css_content_from_scss()` returns false after `debugging('Error while compiling SCSS: ...', DEBUG_DEVELOPER)`, and the build substitutes the `precompiledcsscallback` output, which for a Boost child is Boost's shipped `style/moodle.css`. `styles.php` defines `NO_DEBUG_DISPLAY`, so nothing reaches the browser | Read the PHP error log with debugging at developer level, or compile from the command line with developer debugging on, where the message is printed. The fallback and the printed message were run on 5.3.0 with a small compile script; `build_theme_css.php` reaches the same code but was not itself run |
| A new rule is in the file on disk but not on the page | The revision did not change: a file edit bumps nothing | `php admin/cli/purge_caches.php --theme`, or `build_theme_css.php --themes=<name>` |

Things that fail the compile for the whole theme, each of which looks like the second row: a syntax error in any
SCSS file or in the raw SCSS setting, an `@import` of a file that does not exist on that Moodle version, and a
colour function applied to a variable that holds a `var(...)` value. `moodle-theme-scss` owns these.

## Checking that a rule arrived, then that it applies

```
# 1. Arrival: the rule is in the stylesheet the page links. Use a literal, brace-free pattern.
curl -s "$WWWROOT/" | grep -o 'https\?://[^"]*theme/styles.php[^"]*/all[^"]*' | head -1
curl -s "<that URL>" | grep -cF '.mytheme-banner'
```

```js
// 2. Effect: the browser applies it. Run in the page.
getComputedStyle(document.querySelector('.mytheme-banner')).backgroundColor
```

- Arrival without effect means the rule lost the cascade or its selector matches nothing. A rule in a plugin's
  `styles.css` comes before the theme's SCSS in the file, so at equal specificity Bootstrap and the theme win.
- No arrival means a cache or compile problem; go back to the table above.
- In theme designer mode there is no single `all` URL; the page links one `styles_debug.php` URL per sheet, and
  the theme's SCSS is the one with `type=scss`.
- The page fetched with `curl` uses the site theme. A theme reached through `?theme=` or a course theme needs
  the session or the course URL.

## Purge and build commands

Run from the Moodle root. `admin/cli/` is at the root, not under `public/`.

| Command | Effect |
|---|---|
| `php admin/cli/purge_caches.php` | Everything: caches, theme revision, lang, JavaScript revision, template revision, filters, the cache and localcache directories |
| `php admin/cli/purge_caches.php --theme` | `theme_reset_all_caches()` only |
| `php admin/cli/purge_caches.php --theme --js` | Flags combine. There is no `--template` flag: the browser-side template revision is bumped only by a purge with no flags, by the admin purge page ("Purge all caches", or its Templates box), or by saving the `cachetemplates` setting |
| `php admin/cli/build_theme_css.php --themes=mytheme` | Compiles left-to-right and right-to-left for that theme, stores both in the cache and localcache, bumps the per-theme revision. Without `--themes` it builds every installed theme |
| `php admin/cli/build_theme_css.php --themes=mytheme --direction=ltr --verbose` | One direction. `--verbose` prints the script's progress lines (which themes it found and builds); it prints no timings |

- **Precompile on deploy.** After deploying new theme code, run `build_theme_css.php --themes=<name>` so the
  first visitor does not wait for a compile. It changes only that theme's revision, so other themes' CSS and all
  images stay cached.
- `theme_reset_all_caches()` empties the caches but does not build anything; the next stylesheet request does.
- A full purge also bumps the JavaScript revision, and core's storage wrapper empties the site's browser storage
  when it sees a new revision (`public/lib/amd/src/storagewrapper.js` on 5.2, `public/lib/js/esm/src/Storage.ts` on
  5.3, read). Do not keep durable interface state in `localStorage`; use a user preference.
- From PHP, a setting calls `theme_reset_all_caches` through `set_updatedcallback()`. Calling
  `purge_caches(['theme' => true])` does the same thing by hand.

## Theme designer mode

- Turn on with `$CFG->themedesignermode = true;` in the site's `config.php`, or the checkbox on the "Advanced
  theme settings" page. Toggling the checkbox runs `theme_reset_all_caches()`.
- CSS is linked as one `styles_debug.php` URL per plugin sheet, per parent sheet, one for the compiled SCSS and one
  per theme sheet. Each response is cached for `THEME_DESIGNER_CACHE_LIFETIME` seconds, 10 by default; define the
  constant in the site's `config.php` to change it. A change can therefore take up to that long to appear.
- The scssphp compile cache is kept in `localcache/scsscache-<theme>` in this mode, which makes repeat compiles
  faster; outside designer mode that directory is emptied before each compile.
- Inline source maps are emitted in this mode for left-to-right pages only.
- Images, fonts and theme JavaScript are served without cache headers.
- It does not touch browser-side template caching or AMD caching. Those are `$CFG->cachetemplates` and
  `$CFG->cachejs`.
- Pages are slow in this mode. Never enable it on a production site.

## Mustache: two separate caches

| Rendering | Cache | Invalidation |
|---|---|---|
| In PHP, through a renderer | `localcache/mustache/<themerev>/<theme>/`, one compiled class per template | None needed. Each class is named from a hash of the template's source text and the engine options, and the file is read from disk and located by a fresh directory walk on every request. An edited template, a new override file in a theme, and an edited partial are all picked up on the next request, with theme designer mode on or off |
| In the browser, through `core/templates` | Template source in the browser's storage, keyed by `templaterev` | `templaterev` changes on a full purge. With `$CFG->cachetemplates` off it is `-1` and nothing is cached. Theme designer mode has no effect |

- Old compiled classes stay on disk until the theme revision rises, when directories for lower revisions are
  deleted.
- If an edited template does not change the page, first find out which side renders it. A template included by a
  layout file is PHP-rendered. A dialog, a dynamic list or anything that appears after a click is usually
  browser-rendered.
- **5.3+:** some page parts, the primary and secondary navigation among them, are rendered by React components
  and not by a Mustache template at all. `moodle-theme-layouts-templates` lists them.

## Images and fonts

- Image URLs are `/theme/image.php/<theme>/<component>/<themerev>/<path>`; fonts use `/theme/font.php` the same
  way. Files are copied into `localcache/theme/<themerev>/<theme>/` on first request.
- Extension preference for an image name: `svg` when allowed, then `png`, `gif`, `jpg`, `jpeg`.
- **A missing image is remembered.** The first request for a file that does not exist writes `<name>.error` into
  localcache, and later requests are answered "not found" from that marker without looking again. Adding the file
  afterwards does nothing until the global theme revision changes. Symptom: a new icon or override gives 404
  although the file is in place. Fix: `php admin/cli/purge_caches.php --theme`.
- The same applies to a replaced file: the localcache copy of the old file is served until the revision changes.
- Fonts accepted by `font.php`: `woff2`, `woff`, `ttf`, `otf`, `eot`, `svg`; the script's own header recommends
  shipping WOFF2 only. Sub-directories under `fonts/` are allowed.

## The scripts in `theme/`

| Script | Serves | A theme author needs it |
|---|---|---|
| `styles.php` | The cached, combined stylesheet | Yes: the URL to fetch when checking a rule arrived |
| `styles_debug.php` | Single sheets in theme designer mode | Only when debugging in that mode |
| `image.php` | Images of the theme, core and plugins, with theme overrides applied; the target of `[[pix:component\|name]]` and `$OUTPUT->image_url()` | Yes |
| `font.php` | Fonts; the target of `[[font:component\|name.ext]]` | Yes |
| `javascript.php` | The files named in `$THEME->javascripts` and `javascripts_footer` | Only for themes that still use those keys |
| `jquery.php` | Files from a component's `jquery/` directory when it has `jquery/plugins.php` | Rarely |
| `yui_combo.php`, `yui_image.php` | Legacy YUI assets | No |
| `index.php` | Redirects to the theme selector | No |
| `switchdevice.php` | Stores a per-user device-type preference left over from device themes | No |
