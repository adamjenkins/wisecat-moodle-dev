# Custom widgets, live regions and focus

Read this when building a custom interactive widget (tabs, disclosure, menu, listbox, tree, drag and drop), adding a
live region, or managing focus after JavaScript replaces content. Patterns follow the WAI-ARIA Authoring Practices
(https://www.w3.org/WAI/ARIA/apg/patterns/); Moodle specifics were read in the 5.2 and 5.3.0 source.

## First, look for something that already exists

| Need | Use | Notes |
|---|---|---|
| Tabs | Bootstrap tabs (`data-bs-toggle="tab"`) | Arrow-key handling comes from Bootstrap 5 |
| Show and hide a panel | Bootstrap collapse, or `<details>`/`<summary>` | `aria-expanded` and `aria-controls` are kept in sync by Bootstrap |
| Action menu | `core/action_menu` (PHP `\core\output\action_menu`) or a Bootstrap dropdown | Boost's `theme_boost/aria` adds keyboard support to dropdown menus |
| Dialog | `core/modal` | Labelled, focus-trapped, Escape closes (SKILL.md) |
| Searchable select | `core/form-autocomplete` | Keyboard-accessible combobox |
| Toast or status | `core/toast` | `role="status"`, polite |
| Help popover | `$OUTPUT->help_icon()` / formslib `addHelpButton()` | Button with an accessible name and a popover |
| Sortable list | `core/sortable_list` | Enter on a drag handle opens a "move" dialogue (`sortable_list.js:371-410`); label each handle |

Building your own means implementing every keyboard interaction and every role, state and property listed for that
pattern in the APG; the policy page asks for exactly that check (moodledev.io accessibility policy, Advanced UX
Widgets).

## Tabs (if Bootstrap's do not fit)

```mustache
<div role="tablist" aria-label="{{#str}}sections, local_example{{/str}}">
    <button type="button" role="tab" id="lx-tab-1" aria-controls="lx-panel-1" aria-selected="true">{{#str}}one, local_example{{/str}}</button>
    <button type="button" role="tab" id="lx-tab-2" aria-controls="lx-panel-2" aria-selected="false" tabindex="-1">{{#str}}two, local_example{{/str}}</button>
</div>
<div role="tabpanel" id="lx-panel-1" aria-labelledby="lx-tab-1" tabindex="0">...</div>
<div role="tabpanel" id="lx-panel-2" aria-labelledby="lx-tab-2" tabindex="0" hidden>...</div>
```

- One tab is in the tab order (roving `tabindex`); Left and Right move between tabs, Home and End go to the ends.
- Changing tab updates `aria-selected`, the roving `tabindex` and which panel is hidden.
- Ids must be unique on the page: build them from `{{uniqid}}` or the record id when the template can appear twice.

## Disclosure

```html
<button type="button" aria-expanded="false" aria-controls="lx-more">More details</button>
<div id="lx-more" class="d-none">...</div>
```

Toggle `aria-expanded` and the `d-none` class together. The `hidden` attribute does not hide an element that also
has a `d-flex` or other `d-*` class, because those utilities are `!important`.

## Live regions

- The region must exist in the DOM before the text changes; a region inserted together with its message is often
  not announced.
- `aria-live="polite"` (or `role="status"`) for progress and success; `role="alert"` only for errors the user must
  act on now.
- A chat or activity log: `role="log"` on a `<div>` that contains the list, not on the `<ol>` itself.
- Keep announcements short and do not repeat the whole region: replace the text, do not append to it.
- `core/toast` `add(message, {type})` already does this; its message is HTML, so pass a lang string, not user
  input.

## Focus after JavaScript changes the page

| Change | Move focus to |
|---|---|
| A row was deleted | The next row's first control, or the table's heading when none is left |
| Content replaced by `Templates.replaceNode()` | The replacement's heading or first control, if focus was inside the old node |
| A modal closed | `core/modal` returns it to `returnElement`; pass the trigger when it is not the active element |
| An inline form was saved | The element that shows the saved value |
| Validation failed | The first invalid field (formslib does this with `autofocus`) |

Call `.focus()` on an element that can take it: give a heading `tabindex="-1"` before focusing it.

## Custom overlay without core/modal

`core/local/aria/focuslock` `trapFocus(element)` focuses the first focusable descendant and keeps Tab inside it;
`untrapFocus()` releases the most recent trap; traps stack for nested overlays
(`public/lib/amd/src/local/aria/focuslock.js:328,363`). An overlay also needs: `role="dialog"`, `aria-modal="true"`,
`aria-labelledby` pointing at its heading, Escape to close, and focus returned to the opener on every close path.
`core/modal` provides all of this; write your own only when the overlay is not a dialog.

## Drag and drop

Every drag-and-drop interaction needs a keyboard alternative (move up and down buttons, a "Move to" menu, or
the move dialogue of `core/sortable_list`), and the result must be announced in a live region ("Item moved to position
3"). Pointer-only dragging fails WCAG 2.2 success criterion 2.5.7.

## Images that authors upload

**5.3+:** `core/imagedetails/modal` `getImageDetails(file)` collects alt text, a decorative flag and the display size
for an image a user is about to embed, and resolves with the choices or `null` on cancel
(`public/lib/amd/src/imagedetails/modal.js:61`). On 5.2 build the same fields into your own form: an alt text field
that is required unless a "decorative" checkbox is ticked.
