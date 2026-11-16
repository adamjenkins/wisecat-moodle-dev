# Navigation, the breadcrumb, page headers and the activity header from PHP

Read this when a theme changes primary or secondary navigation data, the breadcrumb, the context header, the
activity header or the edit switch from PHP rather than by restyling or by a template override.

Read in the Moodle 5.3.0 and 5.2 source; nothing in this file was run. What React draws on 5.3 is summarised at
the end, as far as PHP is concerned; overriding the components themselves is a separate subject.

## Who builds what

| Region | Data built by | Turned into template context by | Printed by |
|---|---|---|---|
| Primary navigation (navbar) | `\core\navigation\views\primary` | `\core\navigation\output\primary::export_for_template()` | Boost's layout file puts it in the context as `primarymoremenu`; `theme_boost/navbar` prints it |
| Secondary navigation | `\core\navigation\views\secondary` (`$PAGE->secondarynav`) | `\core\navigation\output\more_menu` | The layout file (`secondarymoremenu`) |
| Breadcrumb | `$PAGE->navbar` | `\theme_boost\boostnavbar` | `core_renderer::navbar()` in Boost's renderer, template `core/navbar` |
| Page header | `core_renderer::full_header()` | Template `core/full_header` | `{{{ output.full_header }}}` |
| Context header (title, user picture) | `core_renderer::context_header()` | Boost's renderer overrides it | Inside `full_header` |
| Activity header | `\core\output\activity_header` (`$PAGE->activityheader`) | Its `export_for_template()` | The layout file (`headercontent`) |
| Edit switch | `core_renderer::edit_switch()` | Template `core/editswitch` | Boost's navbar |
| User menu | `\core\navigation\output\primary::get_user_menu()` | Templates `core/user_menu` and its item partials | Boost's navbar |

The layout file is the junction: Boost's `layout/drawers.php` writes `new core\navigation\output\primary($PAGE)`
by name. A theme that needs a different exporter class has to own that layout file. Everything that can be done
without owning it is listed first.

## Without a layout copy

### Remove primary navigation items

```php
// config.php. Not inherited from the parent theme.
$THEME->removedprimarynavitems = ['courses', 'siteadminnode'];
```

| Key | Removes |
|---|---|
| `home` | The site home item |
| `myhome` | The dashboard item |
| `courses` | "My courses" (the node's own key is `mycourses`; the config key is `courses`) |
| `siteadminnode` | "Site administration" |

Unknown keys are ignored without a message. Source: `public/lib/classes/navigation/views/primary.php`, identical
in 5.2 and 5.3 (compared with `diff`). Removing the item does not remove access: the pages stay reachable by URL
and from the user menu. Site settings decide the rest (`enablemyhome` for the home item, `enabledashboard`,
`enablemycourses`): a fresh 5.2 or 5.3 site has the site home item switched off by `enablemyhome`, which is not a
theme defect.

### Add primary navigation items

Register `\core\hook\navigation\primary_extend` with an active-theme guard and call `add()` on
`$hook->get_primaryview()`. For secondary navigation use `\core\hook\navigation\secondary_extend`. Both hooks are
in 5.2 and 5.3. Items an administrator should be able to edit belong in the site's custom menu setting instead.

### The activity header

`\core\output\activity_header` decides what appears above an activity's content: the title, the description, the
completion and dates information.

| Where | Key | Effect |
|---|---|---|
| `$THEME->activityheaderconfig` | `notitle` | `true`: do not print the activity name as a heading (Boost's value, because the page header already shows it). The only key core reads from this array |
| Layout `options` → `activityheader` | `notitle` | Same, for one layout; wins over the theme value |
| Layout `options` → `activityheader` | `nodescription` | Do not print the activity description |
| Layout `options` → `activityheader` | `nocompletion` | Do not print completion and dates |
| Layout `options` | `noactivityheader` | The layout does not print the activity header at all (Boost's `columns1.php` and `secure.php` test it, and `core_renderer::header()` then adds the skip-link target itself) |
| Layout `options` | `activityinfoinheader` | `false`: keep completion and dates out of the page header actions |

- `activityheaderconfig` is not inherited. A child of Boost that omits it prints the activity name twice: once in
  the page header and once in the activity header.
- The heading level of the first heading inside an activity depends on this setting:
  `activity_header::get_heading_level()` returns one level deeper when the title is shown. A theme that turns the
  title back on changes the heading outline of every activity page; check it with an accessibility run.
- A page can switch the header off for itself with `$PAGE->activityheader->disable()`. That is the plugin's
  decision, not the theme's, and it explains why a theme change "does nothing" on some activity pages. A module can
  also supply its own subclass, `mod_<name>\output\activity_header`, which `$PAGE` uses instead of core's.
- A plugin page that shows a wide table inside a course has been reported to sit better on the `incourse` layout
  with the activity header disabled than on `report`, where on 5.3 the table ran under the course index drawer.
  This is a field report, not explained by the source: Boost's `config.php` gives both layouts the same file
  (`drawers.php`) and the same region on 5.3.0 and 5.2. Reproduce it on the page in question before changing a
  layout because of it.

Source: `public/lib/classes/output/activity_header.php`, `public/theme/boost/config.php`,
`public/lib/pagelib.php` (`magic_get_activityheader()`).

### Other `config.php` switches read by renderers

| Key | Read by | Effect | Inherited |
|---|---|---|---|
| `haseditswitch` | `core_renderer::edit_button()` | `true`: the old "Turn editing on" button is not printed, because the navbar has the switch | no |
| `usescourseindex` | `core_renderer` (activity navigation) and the course format | `true`: the theme shows the course index drawer | no |
| `iconsystem` | `icon_system::instance()` | Which icon system renders `pix_icon` | yes |
| `rendererfactory` | `theme_config::get_renderer()` | Whether theme renderers are looked up at all | no |

A child of Boost that omits `haseditswitch` gets both the switch (from Boost's navbar template) and the legacy
button.

## With a renderer override

### The breadcrumb

Boost's `core_renderer::navbar()` wraps `$PAGE->navbar` in `\theme_boost\boostnavbar`, which removes nodes that
are already in the primary or secondary navigation, course category nodes, and more, and hides the breadcrumb
entirely when one item is left. To change the rules, subclass `boostnavbar` and return it from the theme's
`navbar()`:

```php
// classes/output/core_renderer.php, in the theme's core_renderer
public function navbar(): string {
    $navbar = new \theme_mytheme\mythemenavbar($this->page);
    return $this->render_from_template('core/navbar', $navbar);
}
```

```php
// classes/mythemenavbar.php
namespace theme_mytheme;

class mythemenavbar extends \theme_boost\boostnavbar {
    protected function prepare_nodes_for_boost(): void {
        parent::prepare_nodes_for_boost();
        // Further changes, using the protected helpers remove(), get_item(), item_count().
    }
}
```

Read in the source, not run. Core's Behat steps find the breadcrumb as `nav[aria-label=<breadcrumb string>]/ol/li`
inside `#page-navbar`; keep that structure if the template is changed as well.

### The context header and the page header

- `core_renderer::full_header()` reads the layout option `nonavbar` to decide whether the breadcrumb is printed,
  then renders `core/full_header`. To add data, call the parent's building blocks rather than copying the method,
  or override the template.
- Boost's `context_header()` is a long method. **5.3+:** its body calls `\core\user::can_view_profile()`;
  **5.2 only:** it calls `user_can_view_profile()`. A theme that copied the 5.2 body emits deprecation notices on
  5.3, and the 5.3 body is a fatal error on 5.2. This is the standing reason to wrap `parent::context_header()`
  instead of copying it.
- Other `user_*()` functions from `user/lib.php` moved to `\core\user` in 5.3 the same way. Renderer code copied
  from 5.2 core that calls `user_get_user_navigation_info()` or `user_count_login_failures()` needs the same care.

### The login page

**5.2 only:** Boost's renderer has `render_login()`, which adds `logourl`, `sitename` and more to the context of
Boost's own `core/loginform` template. **5.3+:** that method is gone from Boost and the template moved to core;
core's `render_login()` renders `core/loginform` without those extras. A child renderer that calls
`parent::render_login()` therefore gets different context on the two versions. Compute anything the login
template needs in the theme's own override and do not rely on what the parent adds.

## With a layout copy: changing the exporter

When the navigation data itself must change (extra fields per item, items computed by the theme), subclass the
exporter and create the subclass in the theme's own copy of the layout file. `moodle-theme-layouts-templates`
covers copying a layout and keeping it current.

```php
// classes/output/navigation/primary.php
namespace theme_mytheme\output\navigation;

class primary extends \core\navigation\output\primary {
    #[\Override]
    protected function get_custom_menu(\core\output\renderer_base $output): array {
        $nodes = parent::get_custom_menu($output);
        // Change or add nodes here.
        return $nodes;
    }
}
```

```php
// layout/drawers.php (the theme's copy): one line differs from Boost's.
$primary = new \theme_mytheme\output\navigation\primary($PAGE);
```

- The protected methods available in both versions are `get_primary_nav()`, `get_custom_menu()`,
  `merge_primary_and_custom()`, `flag_active_nodes()`, plus the public `get_user_menu()`. **5.3+:** there are also
  `export_react_props()`, `export_nodes_for_react()`, `export_node_for_react()` and three helpers; a subclass that
  adds fields for a React component extends those and calls the parent.
- **5.3+:** fields added to the Mustache context alone do not reach the navigation the user sees, because the
  visible items come from the JSON in `reactprops`. Add the field in both places, or it shows only with
  JavaScript off.
- Every layout file that prints the navbar creates the exporter, so the same line changes in each copied layout.
- Read in the source and in a published Boost child theme that does this; not run here.

## What React draws on 5.3

**5.3+:** with JavaScript on, the primary navigation, the secondary navigation and the edit switch are drawn by
React components mounted from `core/primarymoremenu`, `core/secondarymoremenu` and `core/editswitch`. Each template
also prints a server-rendered fallback inside the mount point, which React replaces.

- PHP changes that go through the exporters above reach both the fallback and the component.
- CSS and JavaScript written for the old markup match only the fallback: `.primary-navigation .nav-link`,
  `.moremenu .nav-link.active` and `.secondary-navigation .nav-tabs .nav-link` match nothing once React has
  mounted. Looking at the page with JavaScript disabled is therefore misleading. The current hooks are
  `.primarynav-navbar`, `.secondarynav-tabbar`, `.mds-nav-pill` and `.mds-nav-pill--selected`; selected items
  carry `aria-current="page"`.
- `core_renderer::edit_switch()` has the same signature in both versions; on 5.3 it also passes `elementid` and
  `reactprops` to the template. An override that builds its own context must pass them through, so call the
  parent.
- **5.2 only:** the same regions are the `core/moremenu` template with the `core/moremenu` AMD module, and the
  edit switch is a Bootstrap `.form-switch`.
