---
description: Use when building or reviewing Moodle plugin UI for WCAG 2.2 AA - semantic Mustache markup, headings and landmarks, formslib labels, {{#pix}} icon alt text and aria-hidden, accessible names for buttons, row checkboxes and icon links, ARIA only where HTML has no equivalent, live regions and core/toast, focus in core/modal and core/local/aria/focuslock, keyboard support, colour contrast in light and dark colour modes (data-bs-theme, --mds-* tokens), page titles, and the Behat axe steps ("the page should meet accessibility standards", @accessibility, --colourmode=dark, "No data"). Skip when styling a whole theme (moodle-theme-scss) or writing JavaScript mechanics (moodle-amd-javascript).
tools: ['codebase', 'search', 'editFiles', 'runCommands']
---
# Moodle Accessibility (WCAG 2.2 AA)

## Overview

Moodle's accessibility policy targets WCAG 2.2 AA, and core's Behat accessibility step checks WCAG 2.0, 2.1 and 2.2
A and AA by default (`public/lib/tests/behat/behat_accessibility.php`, 5.2 and 5.3). Boost, Bootstrap 5, formslib
and the core output components do most of the work when they are used as intended. This skill gives the markup
recipe, the places where plugins usually break it, and how to prove the result.

Evidence tags: **read** means read in the named version's source or moodledev.io, not run; **run 5.3.0** means
observed on 5.3.0.

## When to Use

- Writing a Mustache template, a renderer, a form, a modal, or any markup built in JavaScript
- Choosing colours in a plugin's `styles.css`, or checking a page in Boost's dark colour mode
- Reviewing a pull request or a Plugins directory submission for accessibility
- Adding `@accessibility` Behat scenarios, or making them pass
- **Skip when:** setting a whole theme's palette, tokens or dark-mode SCSS (`moodle-theme-scss`), testing a theme
  (`moodle-theme-testing-release`), wiring modals, TinyMCE or autocomplete in JavaScript (`moodle-amd-javascript`),
  or writing Behat steps in general (`moodle-behat-testing`).

## The model

1. **Native HTML first, ARIA second.** A `<button>`, `<a href>`, `<label for>`, `<table>` with `<th scope>` and a
   heading hierarchy give screen readers everything. ARIA is for widgets HTML does not have (tabs, tree, combobox),
   and wrong ARIA is worse than none (moodledev.io accessibility policy).
2. **Every interactive element has an accessible name** that a screen reader announces and a voice-control user can
   say: visible text, a `<label for>`, or `aria-label` when there is no room for text. Behat locates fields by id,
   name, `<label>` or placeholder, not by `aria-label`, so a visible or visually hidden `<label>` serves both.
3. **Keyboard is the baseline**: reachable with Tab in reading order, operable with Enter and Space, visible focus,
   and no trap except a modal that Escape closes.
4. **Colour carries no meaning alone**, and text meets 4.5:1 (3:1 for large text), components and focus indicators
   3:1, against whatever surface they end up on in either colour mode. **5.3+:** Boost has a dark colour mode, so a
   literal colour that passes on white can fail on `#1d2125`.
5. **Prove it twice**: axe through Behat catches roughly a third to a half of issues (moodledev.io accessibility
   testing page); keyboard and screen-reader passes catch the rest.

## Default recipe: markup

```mustache
{{!
    @template local_example/attendance

    Example context (json):
    {
        "headingid": "att-h", "sessionname": "Week 1",
        "rows": [{"userid": 3, "fullname": "Ana Lee", "present": true, "checkboxid": "att-3"}]
    }
}}
<section aria-labelledby="{{headingid}}">
    <h3 id="{{headingid}}">{{#str}}attendancefor, local_example, {{sessionname}}{{/str}}</h3>
    <table class="table">
        <caption class="visually-hidden">{{#str}}attendancetable, local_example{{/str}}</caption>
        <thead>
            <tr>
                <th scope="col">{{#str}}fullnameuser, core{{/str}}</th>
                <th scope="col">{{#str}}present, local_example{{/str}}</th>
            </tr>
        </thead>
        <tbody>
            {{#rows}}
            <tr>
                <th scope="row">{{fullname}}</th>
                <td>
                    <input type="checkbox" id="{{checkboxid}}" name="present[{{userid}}]" value="1"
                        {{#present}}checked{{/present}}>
                    <label for="{{checkboxid}}" class="visually-hidden">
                        {{#str}}markpresent, local_example, {{fullname}}{{/str}}
                    </label>
                </td>
            </tr>
            {{/rows}}
        </tbody>
    </table>
    <button type="submit" class="btn btn-primary">{{#str}}savechanges, core{{/str}}</button>
</section>
```

Why each piece is there: the section is named by its heading; the heading level follows the page (an activity
page's content usually starts at `<h3>` under the page's `<h2>`); every row checkbox has its own label naming the
person, so "Mark Ana Lee present" is announced instead of twelve unnamed checkboxes, and Behat's
`I set the field "Mark Ana Lee present" to "1"` finds it; `{{#str}}` keeps every word translatable.

- `visually-hidden` and `visually-hidden-focusable` are the Bootstrap 5 classes. `sr-only` is Bootstrap 4: Boost keeps
  it only in `scss/moodle/bs4-compat.scss` with the `deprecated-styles()` mixin, which outlines it in red on Behat
  sites and in theme designer mode, and a Behat run initialised with `--scss-deprecations` fails every JavaScript
  step on a page that uses it (read in 5.2 and 5.3, not run). `accesshide` still exists in core SCSS.
- A partial is one self-contained element. A template whose root is a bare `<li>` fails CI's HTML validation of the
  example context; put the `<ul>` and its items in the same template, or render the list in the parent. A role
  such as `role="log"` goes on a `<div>` wrapper, not on an `<ol>`, which already has the list role.
- Template structure, example contexts and comment syntax belong to `moodle-theme-layouts-templates`.

## Buttons and links

| Element | Use for |
|---|---|
| `<button type="button">` | An action handled by JavaScript |
| `<button type="submit">` | Submitting a form |
| `<a href="...">` | Going to a URL |

Never `<a href="#">` with a click handler, and never `<div role="button">` unless it also has `tabindex="0"`,
Enter and Space handlers and a focus style; a `<button>` gives all of that for free. Link text says where it goes
("Edit Ana Lee's attendance"), not "click here". Icon-only links and buttons need a name; targets in a row of icons
should be at least 44 by 44 CSS pixels (moodledev.io accessibility policy, Icons).

## Icons

```mustache
{{! An icon on its own: the third argument is the accessible name. }}
<a href="{{editurl}}">{{#pix}}t/edit, core, {{#str}}edituser, local_example, {{fullname}}{{/str}}{{/pix}}</a>

{{! An icon next to text that says the same thing: no third argument, so it is hidden. }}
<button type="button" class="btn btn-secondary">{{#pix}}t/edit, core{{/pix}} {{#str}}edit, core{{/str}}</button>
```

With the Font Awesome icon system (Boost's default) a mapped icon renders as `<i class="icon fa ..." role="img"
aria-label="...">` when it has alt text, and with `aria-hidden="true"` when it has none
(`public/lib/templates/pix_icon_fontawesome.mustache`; `public/lib/classes/output/pix_icon.php:93-95`, read 5.2 and
5.3). Only an icon with no Font Awesome mapping renders as `<img alt>`. So: pass alt text when the icon is the only
content, pass none when text beside it says the same. `{{#pix}}` is sized for icons; use `<img>` with real `alt` for
pictures.

## Forms

- formslib gives every element a `<label for>`, marks required fields with `aria-required="true"`, and points an
  invalid field at its error with `aria-describedby` (`public/lib/form/templates/element-text.mustache:12-17`, read
  5.2 and 5.3). Do not rebuild these by hand; add elements with a label string.
- `placeholder` is not a label. A search box with only a placeholder has no stable accessible name.
- Custom JavaScript form widgets must set `aria-invalid="true"` on an invalid field and associate the message with
  `aria-describedby` (policy page, Forms). Boost's `theme_boost/form-display-errors` does this for formslib.
- `core/form-autocomplete` is keyboard-accessible as shipped; keep its label (`$mform->addElement('autocomplete',
  'x', get_string('label', ...))`) and do not hide its input. Its AJAX handler is in `moodle-amd-javascript`.
- Checkboxes outside an mform can join it with `form="<formid>"`; give each its own label.

## ARIA, live regions and dynamic content

- Prefer a native element or a Bootstrap component that already carries roles (tabs, collapse, dropdown); Boost's
  `theme_boost/aria` adds the missing keyboard support to Bootstrap menus. Patterns for building your own widget
  are in [reference/widget-patterns.md](../moodle-skill-files/moodle-accessibility/reference/widget-patterns.md).
- Status messages after an AJAX action: `core/toast` `add()` writes into a `role="status" aria-live="polite"`
  region (`public/lib/templates/local/toast/wrapper.mustache`). `core/notification` `addNotification()` shows an
  alert in the page. Use `aria-live="assertive"` only for errors that block the user.
- Content that JavaScript replaces (`Templates.replaceNode()`) loses focus if the focused element was inside it.
  Move focus to the new content's heading or the control that replaced the old one.
- `aria-hidden="true"` on anything focusable hides it from screen readers while Tab still reaches it. Remove it from
  the tab order too, or do not hide it.
- `aria-label` on a `<div>` or `<span>` with no role is ignored by most screen readers; give it a role or use text.
- The `hidden` attribute loses to Bootstrap's `d-*` utilities (`!important`): an element with `hidden` and `d-flex`
  stays visible and announced. Toggle `d-none` instead (`moodle-amd-javascript`).

## Modals and overlays

- Use `core/modal` or a subclass. It sets `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing at the
  title (`public/lib/templates/modal.mustache:43`), traps focus while open, closes on Escape, and returns focus to
  `returnElement` or to the element that had focus when it opened.
- The title is a heading: **5.2 only:** `<h5>`; **5.3+:** `<h2 class="modal-title fs-5">`. Headings inside the body
  start at `<h3>` so the outline holds on 5.3 and is harmless on 5.2.
- Always give a modal a title, even a short one: it is the dialog's accessible name.
- Your own overlay (not `core/modal`) uses `core/local/aria/focuslock`:

```javascript
import {trapFocus, untrapFocus} from 'core/local/aria/focuslock';

trapFocus(panel);     // returns nothing; focuses the first focusable element in panel
// ... on close, including Escape:
untrapFocus();        // releases the most recent trap
opener.focus();
```

Traps stack, so every `trapFocus()` needs its `untrapFocus()` on every close path
(`public/lib/amd/src/local/aria/focuslock.js:328,363`, read 5.2 and 5.3). There is no `focusmanager` module and no
release function returned by `trapFocus()`.

## Colour, contrast and colour modes

- A plugin's `styles.css` takes colours from the theme: utility classes (`text-body`, `text-body-secondary`,
  `bg-body`, `bg-body-tertiary`, `border`, `text-bg-*`) or custom properties (`--mds-text-default`,
  `--mds-bg-surface-default`, `--mds-border-default`, `--bs-body-bg`, `--bs-body-color`). These follow the colour
  mode; `bg-white`, `bg-light`, `text-dark` and `#fff` do not (moodledev.io Colour modes guide; `public/lib/UPGRADING.md`
  5.3).
- **5.3+:** where a colour must differ in dark mode, scope it with `[data-bs-theme="dark"] .local-example-x { ... }`,
  never with `@media (prefers-color-scheme: dark)`: the user's or the site's choice overrides the device, so the
  media query applies on the wrong pages. On 5.2 the attribute selector simply never matches, so the same CSS is
  safe on both.
- A colour that carries meaning (status tint, diff highlight) keeps its hue and gets a darker shade for dark mode;
  status shown by colour also gets an icon or text.
- An SVG shown through `<img>` cannot inherit `currentColor` and stays black on a dark page. Render icons with
  `{{#pix}}` or `$OUTPUT->pix_icon()` so a mapped Font Awesome glyph follows the text colour; for your own image,
  choose a mid-tone that has contrast on white and on `#1d2125`, or ship a second file.
- Before checking contrast, confirm the custom property exists: an undefined `var(--x, #fallback)` silently uses the
  fallback on every theme (`getComputedStyle(el).getPropertyValue('--x')` returns `""`).
- SCSS variables (`$primary`, `$danger`) belong to the theme and must be set in pre-SCSS, before Bootstrap compiles;
  setting them in a theme's post-SCSS changes nothing already emitted. Palette and dark-mode SCSS are owned by
  `moodle-theme-scss`.

## Page titles and landmarks

- `$PAGE->set_title()` takes the most specific part first, joined with `moodle_page::TITLE_SEPARATOR`
  (`' | '`, `public/lib/pagelib.php:130`); core appends the site name, so do not add it.

```php
$PAGE->set_title(format_string($cm->name) . ': ' . get_string('report', 'local_example') .
    moodle_page::TITLE_SEPARATOR . format_string($course->fullname));
```

- Landmarks come from the theme's layout. Do not add `<main>` or `role="main"` in plugin output: the page already
  has one, and two fail axe's `landmark-no-duplicate-main`. A plugin `<nav>` or `role="search"` needs a unique
  `aria-label`. `core/search_input_auto` exposes a `{{$searchrole}}` block to drop its `role="search"` when it sits
  inside another search landmark (`public/lib/templates/search_input_auto.mustache:40`; read in 5.3.0 and 5.2.2,
  absent from 5.2.0 and 5.2.1, where the block is ignored and the role stays).

## Testing

```gherkin
@local_example @javascript @accessibility
Scenario: The attendance page meets accessibility standards
  # "local_example > Attendance" is a page type resolved by behat_local_example::resolve_page_instance_url().
  Given I am on the "C1" "local_example > Attendance" page logged in as "teacher1"
  Then the page should meet accessibility standards with "best-practice" extra tests
  And the "region-main" "region" should meet accessibility standards
```

- The step throws a DriverException unless the scenario or feature has `@accessibility`, needs `@javascript`, and
  does nothing at all on a run initialised with `--no-axe` (`behat_accessibility.php:101-111`, read 5.2 and 5.3).
- It loads `/lib/behat/axe/axe.min.js` from the site. A web server rule that denies paths containing `/behat/` makes
  every such step fail with "No data" locally while CI passes; allow `/lib/behat/axe/` on the test vhost.
- **5.3+:** run the suite twice, once plain and once after `php public/admin/tool/behat/cli/init.php --colourmode=dark`;
  do not pin a mode in accessibility scenarios.
- axe does not enter iframes and does not test most non-text contrast (borders, focus rings, icons). Those, keyboard
  operation and screen-reader output are manual checks: [reference/testing.md](../moodle-skill-files/moodle-accessibility/reference/testing.md).

## Common mistakes

| Mistake | What happens | Fix |
|---|---|---|
| `<div onclick>` or `<a href="#">` for an action | Not focusable or announced as a link | `<button type="button">` |
| `{{#pix}}` with no alt as the only content of a link | Link has no accessible name; axe `link-name` | Pass the alt as the third argument |
| `{{#pix}}` with alt next to the same text | Name read twice | Drop the alt |
| Row checkboxes with only `aria-label` | Behat cannot set them by name; voice users cannot say them | `id` plus a `visually-hidden` `<label for>` |
| `sr-only` in new markup | Red deprecation outline on Behat sites; `--scss-deprecations` runs fail | `visually-hidden` |
| Heading levels skipped | Broken outline; axe best-practice `heading-order` | Follow the page's level; modal body starts at `<h3>` |
| `placeholder` as the only label | No stable name | `<label for>` |
| `outline: 0` with no replacement | Focus invisible | Keep Boost's focus style |
| `aria-hidden="true"` on a focusable element | Silent tab stop | Remove from tab order or unhide |
| Literal `#fff` or `bg-white` in plugin CSS | **5.3+:** light island or unreadable text in dark mode | `--mds-*` tokens or `bg-body*` utilities |
| `@media (prefers-color-scheme: dark)` | Applies on the wrong pages | `[data-bs-theme="dark"]` |
| SCSS colour variables set in post-SCSS | No effect | Pre-SCSS, in the theme (`moodle-theme-scss`) |
| Own overlay without `trapFocus()`/`untrapFocus()` | Focus escapes behind it, or stays trapped after close | `core/modal`, or `focuslock` on every close path |
| `import {trapFocus} from 'core/local/aria/focusmanager'` | Module not found | `core/local/aria/focuslock` |
| `@accessibility` steps pass on a `--no-axe` site | Nothing was checked | Check the init options of the run |
| A second `<main>` in plugin output | axe `landmark-no-duplicate-main` | Use `<section>` with a heading |

## Reference files

| File | Read it when |
|---|---|
| [reference/widget-patterns.md](../moodle-skill-files/moodle-accessibility/reference/widget-patterns.md) | Building a custom interactive widget (tabs, disclosure, menu, listbox, tree, drag and drop), a live region, or managing focus after JavaScript replaces content |
| [reference/testing.md](../moodle-skill-files/moodle-accessibility/reference/testing.md) | Writing or debugging `@accessibility` Behat scenarios, running axe outside Behat, or doing the manual keyboard, screen-reader, zoom and colour-mode checks before a release |

## Version notes

| Moodle | File |
|---|---|
| 5.3 | [versions/moodle-5.3.md](../moodle-skill-files/moodle-accessibility/versions/moodle-5.3.md) |

## References

- Accessibility policy: https://moodledev.io/general/development/policies/accessibility
- Accessibility testing: https://moodledev.io/general/development/policies/accessibility/testing
- Colour modes (5.3): https://moodledev.io/docs/5.3/guides/colourmodes
- Templates: https://moodledev.io/docs/guides/templates
- WCAG 2.2: https://www.w3.org/TR/WCAG22/
- WAI-ARIA Authoring Practices: https://www.w3.org/WAI/ARIA/apg/
- Related skills: `moodle-amd-javascript`, `moodle-behat-testing`, `moodle-theme-scss`, `moodle-theme-testing-release`
