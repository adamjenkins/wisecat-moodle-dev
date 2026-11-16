# Data stored through core subsystems

Read this when the plugin stores files, comments, ratings, tags, favourites, question attempts or plagiarism data
through core, and you are writing their export and delete calls.

A subsystem link in `get_metadata()` only declares the use. Each subsystem below gives the plugin static helper
methods to find, export and delete its data; the plugin calls them from its own provider methods, with its own
component name and area. Signatures were read in the 5.3.0 source; the providers are identical in 5.2
(`diff` of each `classes/privacy/provider.php`, read, not run).

## Declaring the link

```php
$collection->add_subsystem_link('core_comment', [], 'privacy:metadata:core_comment');
```

Core's `test_metadata_provider` checks that the name is a real core subsystem
(`core_component::is_core_subsystem()`), and that the summary string exists. The subsystems in
`lib/components.json` (5.3.0) that hold user data for plugins include `core_files`, `core_comment`,
`core_rating`, `core_tag`, `core_favourites`, `core_question`, `core_plagiarism`, `core_portfolio`, `core_grades`
and `core_completion`. There is no `core_log`: events reach the logs through log store plugins, which have their
own providers.

## Files (`core_files`)

`\core_files\privacy\provider` does not export or delete a plugin's files; it covers only private-key data in the
user context (`public/files/classes/privacy/provider.php`). The plugin does both:

| Step | Call |
|---|---|
| Find contexts | Join your own rows; if files are the only trace, join `{files}` on `component`, `filearea`, `userid` |
| Export | `writer::with_context($context)->export_area_files($subcontext, $component, $filearea, $itemid)` |
| Text that embeds files | `writer::with_context($context)->rewrite_pluginfile_urls($subcontext, $component, $filearea, $itemid, $text)` before `export_data()` |
| Activity intro files | `\core_privacy\local\request\helper::export_context_files($context, $user)` (module contexts) |
| Delete a context | `get_file_storage()->delete_area_files($context->id, $component, $filearea)` |
| Delete one item | `get_file_storage()->delete_area_files($context->id, $component, $filearea, $itemid)` |
| Delete a set | `get_file_storage()->delete_area_files_select($context->id, $component, $filearea, $insql, $params)` |

Key each area by an item id that belongs to one user (the row id), or one user's erasure has nothing to delete
by except the whole area.

## Comments (`core_comment`)

`\core_comment\privacy\provider` (`public/comment/classes/privacy/provider.php`):

```php
use core_comment\privacy\provider as comments;

comments::export_comments($context, 'mod_example', 'entry', $itemid, $subcontext);          // Only this user's by default.
comments::delete_comments_for_all_users($context, 'mod_example', 'entry');                 // Area, optional itemid.
comments::delete_comments_for_user($approvedcontextlist, 'mod_example', 'entry');
comments::delete_comments_for_users($approveduserlist, 'mod_example', 'entry');
comments::get_users_in_context_from_sql($userlist, 'c', 'mod_example', 'entry', $context->id);
```

`export_comments()` takes `$onlyforthisuser = true` as its last argument; pass false to export every comment on an
item the user owns. For contexts, join `{comments}` on
`component`, `commentarea`, `userid` in `get_contexts_for_userid()`.

## Ratings (`core_rating`)

`\core_rating\privacy\provider` (`public/rating/classes/privacy/provider.php`):

```php
use core_rating\privacy\provider as ratings;

$join = ratings::get_sql_join('r', 'mod_example', 'entry', 'e.id', $userid);   // ->join, ->params, ->userwhere
ratings::export_area_ratings($userid, $context, $subcontext, 'mod_example', 'entry', $itemid, $onlyuser);
ratings::delete_ratings($context, 'mod_example', 'entry');                      // Optional itemid.
ratings::delete_ratings_select($context, 'mod_example', 'entry', $itemidstest, $params);
ratings::get_users_in_context_from_sql($userlist, 'r', 'mod_example', 'entry', $insql, $params);
```

Use the join in `get_contexts_for_userid()` to find items the user rated: `"... {$join->join} WHERE {$join->userwhere}"`
with `$join->params` merged in. On one user's erasure, delete the ratings on that user's own items only. Ratings
by others on shared items are aggregate data; core's forum deletes only the ratings on the erased user's posts
(`public/mod/forum/classes/privacy/provider.php`).

## Tags (`core_tag`)

`\core_tag\privacy\provider` (`public/tag/classes/privacy/provider.php`):

```php
use core_tag\privacy\provider as tags;

tags::export_item_tags($userid, $context, $subcontext, 'mod_example', 'example_entries', $itemid);
tags::delete_item_tags($context, 'mod_example', 'example_entries');             // Optional itemid, userid.
tags::delete_item_tags_select($context, 'mod_example', 'example_entries', $itemidstest, $params);
```

`$itemtype` is the table name the tags attach to, as used in `core_tag_tag::set_item_tags()`.

## Favourites (`core_favourites`)

`\core_favourites\privacy\provider` (`public/favourites/classes/privacy/provider.php`):

| Step | Call |
|---|---|
| Contexts | `add_contexts_for_userid($contextlist, $userid, $component, $itemtype)` |
| Users | `add_userids_for_context($userlist, $itemtype)` |
| Export | `get_favourites_info_for_user($userid, $context, $component, $itemtype, $itemid)`, then `export_data()` |
| Delete context | `delete_favourites_for_all_users($context, $component, $itemtype, $itemid = 0)` |
| Delete users | `delete_favourites_for_userlist($approveduserlist, $itemtype, $itemid = 0)` |
| Delete user | `delete_favourites_for_user($approvedcontextlist, $component, $itemtype, $itemid = 0)` |

## Question attempts (`core_question`)

A plugin that runs question usages (a quiz-like activity) declares `core_question` and exports and deletes through
the question engine (`public/question/classes/privacy/provider.php`):

- Find usages: `\core_question\privacy\provider::get_related_question_usages_for_user($prefix, 'mod_example',
  'a.uniqueid', $userid)` returns a `\qubaid_join` for your SQL.
- Export: `\core_question\privacy\provider::export_question_usage($userid, $context, $subcontext, $usageid,
  $displayoptions, $isowner)`.
- Delete: `\question_engine::delete_questions_usage_by_activities($qubaids)` with a `\qubaid_join` or
  `\qubaid_list`, before deleting your attempt rows.

`public/mod/quiz/classes/privacy/provider.php` is the worked example.

## Plagiarism (`core_plagiarism`)

An activity that calls the plagiarism API declares `core_plagiarism` and forwards each request so every installed
plagiarism plugin handles its own data (`public/plagiarism/classes/privacy/provider.php`):

```php
\core_plagiarism\privacy\provider::export_plagiarism_user_data($userid, $context, $subcontext, $linkarray);
\core_plagiarism\privacy\provider::delete_plagiarism_for_context($context);
\core_plagiarism\privacy\provider::delete_plagiarism_for_user($userid, $context);
\core_plagiarism\privacy\provider::delete_plagiarism_for_users($userids, $context);
```

A plagiarism plugin itself implements `\core_plagiarism\privacy\plagiarism_provider` (and
`plagiarism_user_provider` for userlists) instead of `request\plugin\provider`.

## Grades and completion

Grades written through `grade_update()` belong to `core_grades`, whose provider exports and deletes them in the
course context for every grade item of the course (`public/grade/classes/privacy/provider.php`); the plugin
declares the link and does nothing else. Activity completion in a module context
is removed by core's `request\helper` after the plugin's delete methods run
(`public/privacy/classes/local/request/helper.php`). A plugin that writes grade items outside the gradebook API,
or completion rows itself, owns that data.
