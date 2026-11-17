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
- `moodle-release-preflight`: every check has its own ID (1a to 7j), and the report is one row per ID in a fixed
  order. Checks that were listed twice (a login-only page; course tables with no backup) have one home each. The
  reference files' sections carry the same IDs. The minor gates and the frankenstyle grep moved to the
  directory-review reference to keep `SKILL.md` under 400 lines.
- Skill `moodle-marketplace-package`: one folder per release with everything a Plugins directory submission
  needs: `listing.txt` with every field (the full description in HTML), `listing.md` with where each claim and
  screenshot came from, the screenshots and the ZIP.
- Skill `moodle-language-pack` and command `/add-language-pack <code>`: a translation of a plugin's strings,
  kept outside the plugin, checked for missing keys and placeholders, and how to view it on a test site.
- Skill `moodle-walkthrough`: a walkthrough of a plugin or theme on a real site as each role, with screenshots,
  a report written in Markdown and a PDF made from it. The Markdown stays beside the PDF, with relative image
  links, so it can be read later.
- README installation section: shell commands, project scope, how to check, update and remove the plugin, the
  clash with the `moodle-dev` plugin, and what to do after `install.sh` for each assistant.
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
