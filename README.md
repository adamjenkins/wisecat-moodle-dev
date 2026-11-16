# wisecat-moodle-dev

Skills, slash commands and subagents that teach an AI coding assistant to build Moodle **plugins and themes** for
Moodle 5.2 and 5.3. A native plugin for [Claude Code](https://code.claude.com/docs), with generated adapters for
Cursor, GitHub Copilot, Aider, Continue and a paste-anywhere bundle.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](CHANGELOG.md)
[![Moodle](https://img.shields.io/badge/Moodle-5.2%20%7C%205.3-orange.svg)](docs/SUPPORTED_VERSIONS.md)

## What it is for

A capable model already knows PHP and the outline of Moodle. What it gets wrong is the detail that passes a code
check and fails on a real site: a child theme that silently loses its renderer overrides, an SCSS error that
quietly serves stock Boost, a release that CI passes and a Plugins directory reviewer sends back for a missing
licence file. These skills carry that detail: the rule, what you see when it is ignored, the fix, and where in
Moodle's source it comes from.

- **25 skills** that load themselves when the task matches.
- **10 slash commands** for common jobs.
- **2 subagents**: a reviewer and a scaffolder.

## How the skills are built

- Each `SKILL.md` is at most 400 lines and holds what most tasks need.
- Detail lives in `reference/` files beside it. Each one is listed with the condition under which to read it, so
  the model opens it only then.
- What is specific to one Moodle version lives in `versions/moodle-X.Y.md`. Adding a Moodle version means adding
  files, not rewriting skills: see [docs/SUPPORTED_VERSIONS.md](docs/SUPPORTED_VERSIONS.md).
- A claim says how it was obtained where that matters: run on a real site, or read in the source.

The full contract is in [CONTRIBUTING.md](CONTRIBUTING.md).

## Install

### Claude Code

```
/plugin marketplace add adamjenkins/wisecat-moodle-dev
/plugin install wisecat-moodle-dev@wisecat-moodle-dev
```

From a local clone:

```
/plugin marketplace add /absolute/path/to/wisecat-moodle-dev
/plugin install wisecat-moodle-dev@wisecat-moodle-dev
```

Check with `/plugin list`. After pulling new commits, run `/reload-plugins`.

### Other assistants

```
./install.sh <cursor|copilot|aider|continue|generic> [--dest <path>]
```

The default destination is the current directory. Each target also receives `moodle-skill-files/`: the reference
and version files the skills link to.

| Assistant | What is installed |
|---|---|
| Cursor | `.cursor/rules/*.mdc`: each skill is a rule attached to PHP, Mustache, JavaScript, SCSS and CSS files |
| GitHub Copilot | `.github/copilot-instructions.md`, a chat mode per skill, a prompt file per command |
| Aider | `CONVENTIONS.md`, with skills and commands under `.aider/` to load with `/read-only` |
| Continue | `.continue/config.yaml`, rules and prompts |
| Anything else | `MOODLE_PROMPTS.md`: one file with every skill, agent and command |

## Skills

### Themes

| Skill | Use it for |
|---|---|
| `moodle-theme-development` | Start here. How Moodle loads and chooses a theme, `config.php` keys, parents, caches, and which sibling skill to use |
| `moodle-theme-boost-child` | Building a child of Boost, or a grandchild such as a child of Boost Union |
| `moodle-theme-scss` | SCSS, Bootstrap variables, design tokens, dark mode, right-to-left, fonts, editor styles |
| `moodle-theme-layouts-templates` | Layouts, block regions, Mustache overrides, and the parts of 5.3 that React renders |
| `moodle-theme-renderers-output` | Renderer overrides, hooks from a theme, icons and images |
| `moodle-theme-settings` | The theme settings page, and settings that feed SCSS and templates |
| `moodle-theme-testing-release` | PHPUnit and Behat for a theme, accessibility checks, CI, packaging and submission |

### Plugins

| Skill | Use it for |
|---|---|
| `moodle-plugin-development` | Creating or changing any plugin type |
| `moodle-field-lessons` | Pitfalls that pass the checks and break on a real site |
| `moodle-web-services` | External functions and web services |
| `moodle-hooks-api` | Hooks: listening, dispatching, replacing `lib.php` callbacks |
| `moodle-amd-javascript` | JavaScript modules, modals, templates, the editor |
| `moodle-accessibility` | WCAG 2.2 AA in plugin UI |
| `moodle-mobile-app` | Moodle app support |
| `moodle-performance` | Caching, queries, background tasks |
| `moodle-privacy-gdpr` | The privacy provider |
| `moodle-security-audit` | Security review of plugin code |

### Testing, release and upgrades

| Skill | Use it for |
|---|---|
| `moodle-phpunit-testing` | PHPUnit tests |
| `moodle-behat-testing` | Behat acceptance tests |
| `moodle-ci-matrix` | A `moodle-plugin-ci` workflow with a checked Moodle, PHP and database matrix |
| `moodle-definition-of-done` | The checklist before calling work complete |
| `moodle-release-preflight` | The defects that reviews catch after CI is green |
| `moodle-plugin-release` | Versions, release notes, the package, tagging and the Plugins directory |
| `moodle-upgrade-migration` | Moving a plugin to a newer Moodle or PHP |
| `moodle-5-3-changes` | What Moodle 5.3 removed, moved, deprecated and added |

## Slash commands

| Command | What it does |
|---|---|
| `/moodle-new-plugin` | Scaffold a plugin |
| `/moodle-new-theme` | Scaffold a Boost child theme |
| `/moodle-theme-check` | Check a theme against the theme skills' common mistakes |
| `/moodle-bump-version` | Bump `version.php` and add an upgrade step |
| `/moodle-privacy-audit` | Check the privacy provider against the schema |
| `/moodle-security-review` | Run the security checklist on a file or plugin |
| `/moodle-capability-audit` | Compare `db/access.php` with the capability checks in the code |
| `/moodle-string-check` | Find hard-coded English |
| `/moodle-codestyle` | Run `phpcs` with the Moodle standard and fix what it reports |
| `/moodle-mustache-lint` | Lint Mustache templates, including theme overrides |

## Subagents

| Agent | Use it for |
|---|---|
| `moodle-reviewer` | A review of a plugin, theme or diff: standards, security, privacy, strings, versions, tests |
| `moodle-scaffolder` | A complete plugin or Boost child theme skeleton from a short brief |

Example prompts: [EXAMPLES.md](EXAMPLES.md).

## Moodle versions

Moodle 5.2 and 5.3. Earlier versions appear only where a plugin moving up from them needs to know what changed.
[docs/SUPPORTED_VERSIONS.md](docs/SUPPORTED_VERSIONS.md) explains how a version is added or dropped.

## Repository layout

```
.claude-plugin/              plugin and marketplace manifests
skills/<name>/SKILL.md       the skill
skills/<name>/reference/     detail, read on a stated condition
skills/<name>/versions/      what is specific to one Moodle version
agents/  commands/           subagents and slash commands
adapters/                    generated for other assistants: never edit by hand
scripts/build-adapters.py    regenerates adapters/
tests/run.sh                 structural checks; run before committing
docs/                        supported versions, adapter authoring
```

To change something: edit under `skills/`, `agents/` or `commands/`, run `python3 scripts/build-adapters.py`, then
`tests/run.sh`, and commit both the source and `adapters/`.

## Licence

MIT: see [LICENSE](LICENSE). Code written with these skills for Moodle should itself be GPL v3 or later, as the
Moodle Plugins directory requires.

## Credits

This repository started from [moodle-dev](https://github.com/SaadRahman01/claude-moodle-dev) by Saad Rahman (MIT),
whose skills, commands, agents and adapter generator are its foundation. The theme skills, the reference and
version file structure, and the field rules were added here by Adam Jenkins.

Built on the [Moodle Developer Documentation](https://moodledev.io) and the Moodle source.
