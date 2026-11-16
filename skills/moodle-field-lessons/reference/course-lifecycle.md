# Backup, restore, course reset, uninstall, privacy and stored dates

Read this when a plugin stores course- or user-scoped data and you are writing or reviewing its backup, restore,
reset, uninstall or privacy code, when a restored or reset course shows wrong data, or when stored dates or times
move across a DST change.

The privacy provider recipe is `moodle-privacy-gdpr`; the definition-of-done walk over the lifecycle is
`moodle-definition-of-done`. Samples are valid on Moodle 5.2 and 5.3.

## Plan the whole lifecycle

- **Plan all of it for any plugin that stores data**: `backup/moodle2/`, the reset triad
  (`<component>_reset_course_form_definition()`, `<component>_reset_course_form_defaults()`,
  `<component>_reset_userdata()`) plus the gradebook reset, and `db/uninstall.php` for data outside your own
  tables (core's uninstall leaves user preferences behind). With only `_reset_userdata()` there is no checkbox on
  the reset form, so the deletion branch is unreachable.
- **Restore input is attacker input**: a crafted `.mbz` reaches every `process_*()` step. Apply the same
  `clean_param()` and allowlists there as the forms and settings do.
- **A restore overwrites the target course's settings, including `visible`.** Code that restores into an existing
  course and then expects its own state re-asserts the end state after the restore
  (`course_change_visibility($id, false)`), and a test checks it.

## Restore file areas

- **`add_related_files($component, $filearea, 'user')` restores nothing for a user-keyed module file area.**
  `send_files_to_pool()` joins the mapping on `parentitemid = contextid`, and the `user` mapping does not store the
  module context there (`public/backup/util/dbops/restore_dbops.class.php`, `send_files_to_pool()`, 5.3.0). Call
  the pool directly with `$skipparentitemidctxmatch = true`:

  ```php
  \restore_dbops::send_files_to_pool($this->get_basepath(), $this->get_restoreid(),
      'mod_myplugin', 'userfiles', $this->task->get_old_contextid(), $this->task->get_userid(),
      'user', null, null, true);
  ```

- **Availability condition plugins have no backup structure hook**: only the condition's JSON travels with the
  activity. A condition that refers to ids (a group, a grouping, another activity) remaps them in its own
  `update_after_restore()` and stores nothing else that must survive.
- **Do not name a nested backup element after a column of its parent record** (an element `items` under a record
  that has an `items` column): the names collide and every backup of the activity fails. PHPUnit tests that do not
  run the backup controller never see it; duplicating the activity once on a site runs the full backup and restore.

## Dates and times that restore and reset move

- **Restore's `apply_date_offset()` and reset's `timeshift` move timestamps by fixed seconds.** Across a DST change,
  09:00 lands at 08:00 local time and a stored midnight lands at 23:00 the day before. For wall-clock data (a
  timetable slot, a due day), round the offset to whole days and move in the right timezone.

  ```php
  $days = (int) round(($this->apply_date_offset(1) - 1) / DAYSECS);
  $new = (new \DateTimeImmutable('@' . $ts))->setTimezone($tz)
      ->modify("+{$days} days")->getTimestamp();
  ```

- **Read the civil date of a stored midnight at midnight plus 12 hours**, so an hour of DST drift either way still
  gives the right day: `userdate($ts + 12 * HOURSECS, '%Y-%m-%d', $tz)`.
- **Comparing two stored timestamps? List every path that writes or shifts each one**: insert, restore offset,
  reset timeshift. A restore shifts date fields but not snapshot times (`timecreated`, a "taken at" column), so a
  comparison between the two reads a restored row as a different kind of row.
- **Tell legacy rows apart by a property only legacy rows have**, not by a date comparison, and state what each row
  shape (legacy, new, restored) feeds into any old function you reuse.

## Test backups

- **Build test `.mbz` files with core's packer** (`get_file_packer('application/vnd.moodle.backup')`), not
  `tar -czf`: a missing `.ARCHIVE_INDEX` fails with a misleading "missing moodle_backup.xml", so a negative test
  passes for the wrong reason.
- **`create_new_course()` has no enrolment instances**; use `role_assign()` in restore tests (`moodle-phpunit-testing`).

## Privacy provider drift

- **Every table in `get_metadata()` must be found by both discovery methods** (`get_contexts_for_userid()`,
  `get_users_in_context()`), exported by `export_user_data()`, and deleted by all three delete methods, with a test
  on generator rows. Grep the provider after any table or column rename: nothing else fails when it drifts.

## References

- https://moodledev.io/docs/apis/subsystems/backup
- https://moodledev.io/docs/apis/subsystems/backup/restore
- https://moodledev.io/docs/apis/subsystems/privacy
