# Changelog

All notable changes to `wisecat-moodle-dev` are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This repository started from the `moodle-dev` toolkit by Saad Rahman at its version 0.6.0 (19 skills, 8 commands,
2 agents and the adapter generator). That project's own changelog records its history up to that point; the
entries below are what changed here.

## [Unreleased]

### Added

- Seven theme skills, replacing the single theme skill: `moodle-theme-development` (the entry point: how Moodle
  loads and chooses a theme, `config.php` keys, parents, caches), `moodle-theme-boost-child`, `moodle-theme-scss`,
  `moodle-theme-layouts-templates`, `moodle-theme-renderers-output`, `moodle-theme-settings` and
  `moodle-theme-testing-release`.
- Reference files: each skill keeps detail in `reference/<topic>.md`, listed in the skill with the condition under
  which to read it.
- Version files: what is specific to one Moodle version is in `versions/moodle-X.Y.md`.
  `docs/SUPPORTED_VERSIONS.md` lists the supported versions (5.2 and 5.3) and says how one is added or dropped.
- Commands `/moodle-new-theme` and `/moodle-theme-check`.
- The reviewer agent reviews themes; the scaffolder agent scaffolds a Boost child theme.
- Field rules in every plugin skill: pitfalls that pass the automated checks and fail on a real site or in a
  Plugins directory review, each with its symptom, its fix and its source.
- `moodle-plugin-release` covers the package itself: the licence file in the ZIP root, the ZIP root folder, and
  inspecting the ZIP before upload, which CI never sees.
- `moodle-release-preflight` checks for each kind of feedback that Plugins directory reviewers give.
- Adapters carry the reference and version files (`moodle-skill-files/`) with working links, and Cursor rules
  attach to `.scss` and `.css` files.
- `tests/run.sh` checks the 400-line budget, that directory names match, that every reference and version file is
  listed in its skill, that links resolve, that `adapters/` matches the generator output, and runs the generator's
  unit tests.

### Changed

- The plugin is named `wisecat-moodle-dev`, version 0.1.0.
- All eighteen plugin skills are rebuilt to the skill contract in `CONTRIBUTING.md`, and target Moodle 5.2 and 5.3.
- The former single `reference.md` files are split into `reference/` files by topic.
- The adapter generator rebuilds its output trees from empty on every run, so a removed skill disappears from
  `adapters/`.
- CI treats new and deleted files under `adapters/` as drift.

### Removed

- The `moodle-mcp` server entry in the plugin manifest. Installing the plugin does not download or run a separate
  server.
