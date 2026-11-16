# Supported Moodle versions

The skills cover these Moodle versions. A rule in a `SKILL.md` body holds on all of them unless it is tagged.

| Moodle | Branch | `$plugin->supported` value | Role |
|---|---|---|---|
| 5.2 | `MOODLE_502_STABLE` | `502` | **Baseline**: the lowest supported version |
| 5.3 | `MOODLE_503_STABLE` | `503` | Supported |

Earlier versions are mentioned only where a plugin migrating from them needs to know what changed
(`moodle-upgrade-migration`).

## How version-specific content is stored

- A one-line difference is inline in `SKILL.md`, tagged `**5.3+:**` or `**5.2 only:**`.
- Anything longer is in `skills/<name>/versions/moodle-X.Y.md`, listed in that skill's **Version notes** table.
  The file says only what is specific to X.Y against the baseline.
- The upgrade to a version has its own skill: `moodle-5-3-changes` for 5.3.

## Adding a version (for example 6.0)

1. Add a row to the table above.
2. Add `skills/moodle-6-0-changes/` for the upgrade itself: what was removed, moved, deprecated and added.
3. For each skill where 6.0 differs, add `skills/<name>/versions/moodle-6.0.md` and a row in the skill's
   Version notes table. Do not rewrite the body unless a rule stopped being true on every supported version.
4. Extend the CI matrix advice in `moodle-ci-matrix`.
5. Regenerate the adapters and update `CHANGELOG.md`.

## Dropping a version

1. Remove its row. If it was the baseline, the next version becomes the baseline.
2. Delete each `versions/moodle-X.Y.md` for the dropped version. For the new baseline, fold its version file into
   the `SKILL.md` body, since its content is now what holds everywhere.
3. Remove inline tags that have become universal (`**5.3+:**` when 5.3 is the baseline).
