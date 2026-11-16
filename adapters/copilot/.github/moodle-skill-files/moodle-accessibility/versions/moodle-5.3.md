# Moodle 5.3: accessibility specifics

What 5.3 adds or changes against the 5.2 baseline. Read it when the plugin supports 5.3 and has its own markup,
styles or Behat accessibility scenarios. Read in the 5.3.0 source and its `UPGRADING.md` files; not run unless
tagged.

## Dark colour mode

- Boost can render in a dark colour mode, set on `<html data-bs-theme="dark">`. It is off until a site enables
  `theme_boost | enablecolourmodes` (experimental tab), and applies to Boost and any theme with `boost` in its
  parents. On 5.2 none of this exists, and `[data-bs-theme="dark"]` rules simply never match.
- Plugin styles must take colours from `--bs-*` / `--mds-*` custom properties or the `bg-body*` / `text-body*`
  utilities (`public/lib/UPGRADING.md` 5.3, MDL-68037). The page background in dark mode is `#1d2125`, raised
  surfaces `#343a40` (moodledev.io Colour modes guide).
- TinyMCE takes the dark skin and repeats `data-bs-theme` in its content iframe, but the iframe has Bootstrap's stock
  palette, so `--mds-*` tokens are undefined there: editor content rules need literal colours with a dark override.
- Behat: `--colourmode=dark` on `init.php` / `util.php --enable`; the step `Given the run is not using a colour mode`
  (`public/lib/tests/behat/behat_general.php`); user preference `theme_boost_colourmode`.
- A course page whose custom styles used only tokens and utilities had no axe violations in light or in dark mode
  (run on 5.3.0, axe injected by browser automation with the WCAG 2.0-2.2 A/AA tags).

## Changed markup

- Modal titles are `<h2 class="modal-title fs-5 text-truncate">` (were `<h5>`; `public/lib/templates/modal.mustache:49`,
  MDL-75699). Start modal body headings at `<h3>`; selectors on `h5.modal-title` match nothing.
- `core/notification_base` takes `headinglevel` (1-6, default 3) for its title
  (`public/lib/templates/notification_base.mustache:35,60`, MDL-88458). Pass the level that fits where the
  notification sits.
- Primary and secondary navigation are React (`core/nav/PrimaryNav`, `core/nav/Nav`); the component renders its own
  `<nav>` landmark, so do not wrap `core/secondarymoremenu` in another one (`moodle-theme-layouts-templates`).
- Course index: when an activity has a delegated section (a subsection), the `li[role="treeitem"]` of
  `core_courseformat/local/courseindex/cm` carries `aria-owns`, `aria-labelledby` and `aria-expanded`, and
  `core_courseformat/local/courseindex/section` no longer sets them for delegated sections. A format or theme that
  overrides one of the two templates must override both (`public/course/format/UPGRADING.md`, MDL-88949).

## New tools

- Behat step `I set the focus on the "<element>" "<selector>"` moves keyboard focus without activating the element
  (`public/lib/tests/behat/behat_general.php:494`, MDL-84065); use it to test focus styles and focus-triggered
  behaviour.
- `core/imagedetails/modal` collects alt text and a decorative flag for an uploaded image
  (`public/lib/amd/src/imagedetails/modal.js`, MDL-89214).
- Behat bundles axe-core 4.13.0 (5.2: 4.10.3; banner of `public/lib/behat/axe/axe.min.js`); newer axe rules can fail
  scenarios that passed on 5.2.
