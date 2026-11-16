# Per-user choices: user preferences and the privacy provider

Read this when a theme stores anything per user (an open drawer, a density or display mode, a dismissed banner),
sets a preference from JavaScript, or needs its `classes/privacy/provider.php` written or reviewed.

Read in the 5.2 and 5.3.0 source: `public/lib/classes/user.php` (preference definitions), `public/user/externallib.php`,
`public/user/amd/src/repository.js`, `public/theme/boost/lib.php`, `public/theme/boost/classes/privacy/provider.php`,
`public/privacy/tests/privacy/provider_test.php`. The null provider was installed with a theme on 5.3.0; the
preference code below was read, not run.

## Admin setting or user preference

An admin setting is one value for the site, in `config_plugins`. A user preference is one value per user, in
`user_preferences`, and it is personal data. Use a preference only for what each user chooses. The usual shape is
both: an admin setting gives the site default, and a preference overrides it for one user:

```php
$default = get_config('theme_mytheme', 'density') ?: 'comfortable';
$density = get_user_preferences('theme_mytheme_density', $default);
```

## Declaring a preference

A preference that JavaScript may write must be declared in the theme's `lib.php`:

```php
/**
 * The user preferences this theme lets the browser set.
 *
 * @return array[]
 */
function theme_mytheme_user_preferences(): array {
    return [
        'theme_mytheme_density' => [
            'type' => PARAM_ALPHA,
            'null' => NULL_NOT_ALLOWED,
            'default' => 'comfortable',
            'choices' => ['comfortable', 'compact'],
            'permissioncallback' => [core_user::class, 'is_current_user'],
        ],
    ];
}
```

- **Prefix the name with the component.** Preference names are global: core merges the arrays from every
  installed plugin (`core_user::fill_preferences_cache()`), including themes that are installed and not active.
  Boost's own names (`drawer-open-index`, `drawer-open-block`) predate the convention; do not copy their shape.
- **An undeclared preference cannot be written from the browser.** The web service asks
  `core_user::can_edit_preference()`, which returns false for an unknown name; the call answers with a
  `nopermission` warning and saves nothing. The symptom is a choice that is forgotten on the next page.
- **`choices` and `default` protect the value.** A value outside `choices` is replaced by `default` when it is
  written through the web service (`core_user::clean_preference()`), so pick a default that is safe.
- **The list of plugins that have this callback is cached.** After adding the function to an installed theme,
  purge caches (or bump the version and upgrade), or the preference stays unknown.
- **Guests and logged-out visitors cannot store a preference** (`can_edit_preference()` returns false for them).
  For them the choice lasts for the page view, or use a cookie the theme sets itself.
- `permissioncallback` receives the user and the preference name. `[core_user::class, 'is_current_user']` is the
  right answer for a personal display choice.

## Reading and writing

PHP:

```php
$density = get_user_preferences('theme_mytheme_density', 'comfortable');
set_user_preference('theme_mytheme_density', 'compact');
unset_user_preference('theme_mytheme_density');
```

JavaScript (an AMD module of the theme):

```javascript
import {setUserPreference} from 'core_user/repository';

export const init = () => {
    document.addEventListener('click', async(e) => {
        const button = e.target.closest('[data-action="theme_mytheme/density"]');
        if (!button) {
            return;
        }
        const density = button.dataset.value;
        document.body.classList.toggle('mytheme-compact', density === 'compact');
        await setUserPreference('theme_mytheme_density', density);
    });
};
```

- **Apply the choice on the server on the next request**, as a body class or template context value, so the page
  is right before any JavaScript runs. The JavaScript only changes the current page and saves.
- **Do not rely on writing `null` to remove a preference from the browser.** With `NULL_NOT_ALLOWED` the cleaned
  value becomes the default and is stored. Give "no choice" an explicit value in `choices`, or make the default the
  neutral state.
- **A one-shot flag must be removed by the code that acts on it.** A preference or config value meaning "do this on
  the next request" (purge something, show a notice once) that is read and not cleared makes the action happen on
  every page load: with a cache purge as the action, the site purges on every request.

## Why not localStorage

Moodle clears the whole origin's `localStorage` when the JavaScript revision changes (every cache purge) and when
a different login is detected, with the browser's `Storage.clear()`. That removes keys a theme wrote directly with
`window.localStorage` too. A display choice kept there is lost at unpredictable moments and never follows the user
to another device. Use a user preference. **5.3+:** the same clearing also applies to `sessionStorage` on a login
change (`public/lib/js/esm/src/Storage.ts`); on 5.2 the code is `public/lib/amd/src/storagewrapper.js` and
`public/lib/amd/src/storage_validation.js`.

## The privacy provider

Every plugin needs `classes/privacy/provider.php`, themes included. Core's test
`core_privacy\privacy\provider_test::test_all_providers_compliant` runs over every installed plugin of every type
and fails for a theme without one. `moodle-plugin-ci` runs only the plugin's own tests, so this failure appears
only in a full core PHPUnit run on a site with the theme installed, or in a Plugins directory review.

### A theme that stores nothing per user

```php
<?php
// (GPL header)

namespace theme_mytheme\privacy;

/**
 * Privacy provider: this theme stores no personal data.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class provider implements \core_privacy\local\metadata\null_provider {
    /**
     * The lang string that says why no data is stored.
     *
     * @return string
     */
    public static function get_reason(): string {
        return 'privacy:metadata';
    }
}
```

```php
$string['privacy:metadata'] = 'This theme does not store any personal data.';
```

Admin settings are not personal data: a theme with only admin settings uses this provider.

### A theme with user preferences

```php
<?php
// (GPL header)

namespace theme_mytheme\privacy;

use core_privacy\local\metadata\collection;
use core_privacy\local\request\writer;

/**
 * Privacy provider: this theme stores display preferences.
 *
 * @package    theme_mytheme
 * @copyright  2026 Your Name <you@example.com>
 * @license    http://www.gnu.org/copyleft/gpl.html GNU GPL v3 or later
 */
class provider implements
    \core_privacy\local\metadata\provider,
    \core_privacy\local\request\user_preference_provider {
    /** The display density preference. */
    const DENSITY = 'theme_mytheme_density';

    /**
     * Describes the stored data.
     *
     * @param collection $items
     * @return collection
     */
    public static function get_metadata(collection $items): collection {
        $items->add_user_preference(self::DENSITY, 'privacy:metadata:preference:density');
        return $items;
    }

    /**
     * Exports the preferences of one user.
     *
     * @param int $userid
     */
    public static function export_user_preferences(int $userid) {
        $density = get_user_preferences(self::DENSITY, null, $userid);
        if ($density !== null) {
            writer::export_user_preference(
                'theme_mytheme',
                self::DENSITY,
                $density,
                get_string('privacy:metadata:preference:density', 'theme_mytheme')
            );
        }
    }
}
```

```php
$string['privacy:metadata:preference:density'] = 'Whether you chose the comfortable or the compact display.';
```

Rules:

- **The two interfaces together are a complete provider.** `user_preference_provider` is a request provider, so no
  context or delete methods are needed for preferences: core deletes a user's preferences itself.
- **A null provider in a theme that sets a preference is a defect.** The export leaves the preference out, and a
  Plugins directory reviewer will flag it. Change the provider in the same commit that adds the first preference.
- **One `add_user_preference()` per preference name.** There is no wildcard. For numbered preferences
  (`theme_mytheme_banner1dismissed`, `...2dismissed`) loop over the possible numbers in both methods.
- **Every string named in the provider must exist** in the theme's lang file. The same core test checks the reason
  string of a null provider and the strings of each metadata item.
- **A child theme does not declare its parent's preferences.** Boost declares `drawer-open-index`,
  `drawer-open-block` and, on 5.3, its colour mode preference in its own provider; they belong to `theme_boost`.
- **Per-user data that is not a preference** (a row in a table of the theme, an uploaded per-user file) needs the
  full plugin provider with contexts, export and delete. That is covered in `moodle-privacy-gdpr`.

## Preferences Boost already keeps

| Preference | Meaning | Version |
|---|---|---|
| `drawer-open-index` | Course index drawer open | 5.2 and 5.3 |
| `drawer-open-block` | Block drawer open | 5.2 and 5.3 |
| `theme_boost_colourmode` | The user's light or dark choice | 5.3+ |

A child theme reads these with `get_user_preferences()` if it needs them and does not redefine them. A test that
needs a known starting state sets them for its user before the page loads, for example
`set_user_preference('drawer-open-block', 0, $user)`.
