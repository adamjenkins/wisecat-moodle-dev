# MUC caching: definitions, use, invalidation, testing

Read this when you write or change a `db/caches.php` definition, choose its options, invalidate cached data, or test
code that uses a cache.

Sources: `public/cache/classes/definition.php` (option list in the class docblock), `public/cache/classes/cache.php`,
`public/cache/classes/helper.php`, read on 5.3.0; the same files exist on 5.2. Core's own definitions in
`public/lib/db/caches.php` are the best examples.

## Define

```php
<?php
// (GPL header)
// db/caches.php
defined('MOODLE_INTERNAL') || die();

$definitions = [
    // Shared by all users, invalidated when the data changes.
    'activeitems' => [
        'mode' => cache_store::MODE_APPLICATION,
        'simplekeys' => true,
        'simpledata' => true,
        'staticacceleration' => true,
        'staticaccelerationsize' => 30,
        'invalidationevents' => ['changesinlocalexampleitems'],
    ],
    // One user's computed dashboard, for the length of the session.
    'dashboard' => [
        'mode' => cache_store::MODE_SESSION,
        'simplekeys' => true,
    ],
    // Repeated lookups inside one request.
    'contextconfig' => [
        'mode' => cache_store::MODE_REQUEST,
        'simplekeys' => true,
    ],
];
```

```php
// lang/en/local_example.php
$string['cachedef_activeitems'] = 'Active items per course';
$string['cachedef_contextconfig'] = 'Resolved settings per context, for one request';
$string['cachedef_dashboard'] = 'Dashboard data for the current user';
```

Then bump `$plugin->version` and upgrade: definitions are loaded into the cache configuration on upgrade, and a
missing `cachedef_` string shows as `[[cachedef_x]]` on Site administration > Plugins > Caching > Configuration and
is a Plugins directory review finding.

`cache_store::MODE_*` (the alias that core's own file uses) and `\core_cache\store::MODE_*` are the same constants on
5.2 and 5.3.

## Options

| Option | Use it when | Cost or trap |
|---|---|---|
| `mode` (required) | Always | Application: shared by all users and, with a shared store, all web servers. Session: one user. Request: this request only |
| `simplekeys` | Keys are only `a-zA-Z0-9_` | Keys are not hashed; any other character breaks lookups |
| `simpledata` | Values are scalars or arrays of scalars | The loader skips its handling of objects and references; do not store objects with it on |
| `staticacceleration` (+ `staticaccelerationsize`) | The same keys are read many times in one request | Keeps a PHP array copy per request; memory |
| `requireidentifiers` | The data depends on extra identifiers passed to `make()` | Every `make()` must pass them |
| `datasource` | The cache can load misses itself | Class implements `\core_cache\data_source_interface` |
| `invalidationevents` | The data changes when something happens | Fire the event from every code path that changes the data |
| `ttl` | Data really expires by time (an external feed) | Discouraged in the docblock; stores without native TTL wrap every item |
| `canuselocalstore` | The data has its own revision scheme so each web server may hold a copy | Wrong if a change on one server must be seen on the others |
| `maxsize` | A hint for stores with eviction | Stores may ignore it |
| `sharingoptions`, `defaultsharing` | Almost never | Leave the site default |

## Use

```php
$cache = \core_cache\cache::make('local_example', 'activeitems');

$items = $cache->get($courseid);
if ($items === false) {
    $items = array_values($DB->get_fieldset_select('local_example_items', 'id',
        'courseid = ? AND active = 1', [$courseid]));
    $cache->set($courseid, $items);
}
```

- `get()` returns `false` for a miss, so a cached `false` is indistinguishable from a miss. Cache `0`, `[]` or
  `['value' => false]` instead.
- `get_many()` and `set_many()` take and return arrays keyed by cache key: use them in loops.
- `has()` followed by `get()` is two store round trips; call `get()` and test for `false`.
- `\core_cache\cache::make_from_params($mode, $component, $area)` creates an ad-hoc cache without a definition;
  it cannot be configured or mapped by the admin. Use it only for throwaway request data.
- Never put per-user data in an application cache unless the user id is part of the key, and never cache the
  result of a capability check across users.

## Data source

When a miss can always be filled the same way, let the cache fill it:

```php
// db/caches.php entry
'itemname' => [
    'mode' => cache_store::MODE_APPLICATION,
    'simplekeys' => true,
    'simpledata' => true,
    'datasource' => \local_example\local\itemname_source::class,
],
```

```php
namespace local_example\local;

use core_cache\data_source_interface;
use core_cache\definition;

class itemname_source implements data_source_interface {
    public static function get_instance_for_cache(definition $definition): self {
        return new self();
    }

    public function load_for_cache($key) {
        global $DB;
        return $DB->get_field('local_example_items', 'name', ['id' => $key]);
    }

    public function load_many_for_cache(array $keys) {
        global $DB;
        [$insql, $params] = $DB->get_in_or_equal($keys);
        $names = $DB->get_records_select_menu('local_example_items', "id $insql", $params, '', 'id, name');
        $result = [];
        foreach ($keys as $key) {
            $result[$key] = $names[$key] ?? false;
        }
        return $result;
    }
}
```

`get()` then calls `load_for_cache()` on a miss and stores the result. `load_many_for_cache()` returns one value per
requested key, keyed by that key, with `false` where nothing exists.

## Invalidate

| Call | Effect |
|---|---|
| `$cache->delete($key)` / `delete_many($keys)` | Removes keys from this definition |
| `$cache->purge()` | Empties this definition |
| `\core_cache\helper::invalidate_by_event('changesinlocalexampleitems', [$courseid])` | Invalidates those keys in every definition listing the event, on every server |
| `\core_cache\helper::purge_by_event('changesinlocalexampleitems')` | Purges every definition listing the event |
| `\core_cache\helper::invalidate_by_definition('local_example', 'activeitems', [], [$courseid])` | Invalidates keys of one definition, including identifiers |

Fire the invalidation from every path that changes the data: the form handler, the external function, restore,
course reset, delete, and the privacy provider's delete methods. A missed path shows as stale data that only a purge
of all caches fixes.

## Versioned data

For data where a reader knows which version it needs (core uses it for course modinfo), `set_versioned($key,
$version, $data)` and `get_versioned($key, $requiredversion)` return the cached value only if it is at least that
version; a `datasource` can implement `\core_cache\versionable_data_source_interface` to load newer versions. Use it
when the version number already exists in your data (a revision column); otherwise invalidation is simpler.

## Stores on a site

Core ships the stores `apcu`, `file`, `redis`, `session` and `static` on 5.2 and 5.3 (`public/cache/stores/`).
Without any configuration, application caches go to the file store in `$CFG->cachedir` (shared between web servers
when `dataroot` is shared), session caches to the session store, request caches to the static store. Administrators
map definitions to Redis or APCu in Site administration > Plugins > Caching > Configuration; code must work with any
store, so do not depend on eviction order or on a TTL being honoured.

## Testing cached code

- Every PHPUnit test starts with empty caches: `reset_dataroot()` calls `\core_cache\helper::purge_all()` and resets
  the factory (`public/lib/classes/test/testing_util.php`, 5.3.0).
- Test the hit, not only the miss: call twice and assert that the second call made no queries.

  ```php
  $first = \local_example\items::active($course->id);
  $before = $DB->perf_get_reads();
  $second = \local_example\items::active($course->id);
  $this->assertSame(0, $DB->perf_get_reads() - $before);
  $this->assertSame($first, $second);
  ```

- Test invalidation: change the data through the real API, then assert that the next read sees it.
- A cache only within one test method is not proof across requests; for application caches, `\core_cache\cache::make()`
  again after `\core_cache\factory::reset()` to simulate a new request.
