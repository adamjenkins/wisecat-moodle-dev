# Hooks: what is specific to Moodle 5.3

Read this when a plugin uses a hook that exists only on 5.3 or extends the user menu, and must also run on 5.2.

Everything here was read in the 5.3.0 source (`public/lib/classes/hook/`, `public/user/classes/hook/`) and
`UPGRADING.md`, and compared with the 5.2 tree; not run. The hook manager itself is unchanged.

## Hooks added in 5.3

| Hook | What a callback can do | Source |
|---|---|---|
| `\core\hook\email\before_email_to_user` | Change `$hook->email` (`user`, `from`, `subject`, `messagetext`, `messagehtml`, `attachment`, `attachname`, `usetrueaddress`, `replyto`, `replytoname`, `wordwrapwidth`), add a header with `$hook->email->add_additional_header()`, or stop the send with `$hook->email->add_block_reason()`: any reason means the mail is not sent | MDL-69724 |
| `\core\hook\output\before_import_map_config` | Add entries to the ES module import map (`$hook->importmap`, `add_import()`) | the class file; not in `UPGRADING.md` |
| `\core\hook\output\before_requirejs_config` | Map old AMD module names to ESM modules (`add_requirejs_esm_map_entry()`); Boost uses it to keep `theme_boost/bootstrap/*` names working until 7.0 (`public/theme/boost/classes/hook_listener.php`) | the class file; not in `UPGRADING.md` |
| `\core\hook\composer\composer_di` | Configure DI for Composer-installed packages (`configure()`) | the class file; not in `UPGRADING.md` |

Registering any of these in `db/hooks.php` is safe on 5.2: the manager stores the entry under the class name and
never dispatches it (`manager.php` `add_component_callbacks()`). So one `db/hooks.php` serves both versions; only
the callback body must avoid 5.3-only classes, and it is never called on 5.2.

```php
// Blocks mail to a reserved test domain on 5.3; does nothing on 5.2.
public static function before_email(\core\hook\email\before_email_to_user $hook): void {
    if (str_ends_with(strtolower($hook->email->user->email), '@example.invalid')) {
        $hook->email->add_block_reason('local_example: reserved test domain');
    }
}
```

## `extend_user_menu` takes typed items

On 5.3, `\core_user\hook\extend_user_menu::add_navitem()` and `get_navitems()` are deprecated (debugging notice,
MDL-88938) in favour of `add_menu_item()` and `get_menu_items()`, which take
`\core_user\output\user_action_menu\link`, `divider`, `header` or `text` objects. On 5.2 only the old pair exists.
A callback for both:

```php
public static function extend_user_menu(\core_user\hook\extend_user_menu $hook): void {
    $url = new \moodle_url('/local/example/index.php');
    $title = get_string('pluginname', 'local_example');
    if (method_exists($hook, 'add_menu_item')) {
        // 5.3+.
        $hook->add_menu_item(new \core_user\output\user_action_menu\link($url, $title));
    } else {
        // 5.2.
        $hook->add_navitem((object) ['itemtype' => 'link', 'url' => $url, 'title' => $title]);
    }
}
```

`link` takes `(url $url, string $title, ?string $titleattribute = null, ?pix_icon $pixicon = null, ?string $imgsrc =
null, array $classes = [], array $attributes = [])` (`public/user/classes/output/user_action_menu/link.php`,
5.3.0). The 5.3 `add_navitem()` converts `link` and `divider` objects for you, but emits the deprecation notice.

## Boost registers hook callbacks on 5.3

`theme_boost` gained `db/hooks.php` with callbacks for `before_requirejs_config`, `before_html_attributes` and
`before_standard_head_html_generation` (colour modes and the Bootstrap module map). They run for every theme that
has `boost` among its parents. What that means for a child theme: `moodle-theme-renderers-output`.
