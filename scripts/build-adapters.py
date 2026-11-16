#!/usr/bin/env python3
"""Generate per-agent adapter files from canonical prompts.

Source of truth: skills/<name>/SKILL.md, agents/<name>.md, commands/<name>.md
(Claude Code plugin layout — works as-is for Claude.)

This script regenerates equivalents for:
  - Cursor    -> adapters/cursor/.cursor/rules/*.mdc
  - Copilot   -> adapters/copilot/.github/copilot-instructions.md
                 adapters/copilot/.github/chatmodes/*.chatmode.md
  - Aider     -> adapters/aider/CONVENTIONS.md + slash commands as plain MD
  - Continue  -> adapters/continue/config.yaml + rules/*.md
  - Generic   -> adapters/generic/PROMPTS.md (one big file, copy/paste friendly)

Frontmatter is parsed from each source file. Body is reused verbatim, except that
links to a skill's own extra files are rewritten.

A skill may carry extra files beside SKILL.md (reference/<topic>.md,
versions/moodle-X.Y.md). They are copied into every adapter tree under
moodle-skill-files/<skill>/, and the links to them in the skill body are
rewritten to point at the copies.

Every run deletes the generated trees first, so a removed skill or file
disappears from adapters/ too.
"""
from __future__ import annotations
import json
import re
import shutil
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"
COMMANDS = ROOT / "commands"
ADAPTERS = ROOT / "adapters"

FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)

# Generated trees. Each is deleted and rebuilt on every run.
TARGETS = ("cursor", "copilot", "aider", "continue", "generic")
# Directory, inside each adapter tree, that holds the skills' extra files.
EXTRAS_DIR = "moodle-skill-files"
# A Markdown link to one of a skill's own extra files: (reference/x.md), (versions/moodle-5.3.md#a), (reference.md).
EXTRA_LINK_RE = re.compile(r"\]\(((?:reference|versions)/[^)\s#]+|reference\.md)(#[^)\s]*)?\)")
# File globs a skill's Cursor rule attaches to.
CURSOR_GLOBS = ["**/*.php", "**/*.mustache", "**/amd/src/**/*.js", "**/*.scss", "**/*.css"]


def manifest() -> dict:
    return json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())


def skill_extras(skill_dir: Path) -> list[Path]:
    """Every file in a skill directory other than SKILL.md, as paths relative to it, sorted."""
    return sorted(p.relative_to(skill_dir) for p in skill_dir.rglob("*")
                  if p.is_file() and p.name != "SKILL.md")


def rewrite_extra_links(body: str, prefix: str, name: str) -> str:
    """Point links to a skill's extra files at the copies under <prefix>/<EXTRAS_DIR>/<name>/."""
    base = f"{prefix}{EXTRAS_DIR}/{name}/"
    return EXTRA_LINK_RE.sub(lambda m: f"]({base}{m.group(1)}{m.group(2) or ''})", body)


def copy_extras(data, dest: Path) -> None:
    """Copy every skill's extra files to <dest>/<EXTRAS_DIR>/<skill>/."""
    for _, _, name in data["skills"]:
        for rel in skill_extras(SKILLS / name):
            target = dest / EXTRAS_DIR / name / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(SKILLS / name / rel, target)
            print(f"  wrote {target.relative_to(ROOT)}")


def parse(path: Path) -> tuple[dict, str]:
    text = path.read_text()
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm_raw, body = m.group(1), m.group(2)
    fm: dict = {}
    key = None
    for line in fm_raw.splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            key = k.strip()
            fm[key] = v.strip().strip('"').strip("'")
        elif key:
            fm[key] += " " + line.strip()
    return fm, body.lstrip("\n")


def load_all() -> dict[str, list[tuple[dict, str, str]]]:
    out = {"skills": [], "agents": [], "commands": []}
    for p in sorted(SKILLS.glob("*/SKILL.md")):
        fm, body = parse(p)
        out["skills"].append((fm, body, p.parent.name))
    for p in sorted(AGENTS.glob("*.md")):
        fm, body = parse(p)
        out["agents"].append((fm, body, p.stem))
    for p in sorted(COMMANDS.glob("*.md")):
        fm, body = parse(p)
        out["commands"].append((fm, body, p.stem))
    return out


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  wrote {path.relative_to(ROOT)}")


def build_cursor(data) -> None:
    print("Cursor...")
    base = ADAPTERS / "cursor" / ".cursor" / "rules"
    for fm, body, name in data["skills"]:
        front = dedent(f"""\
            ---
            description: {fm.get('description', name)}
            globs: {json.dumps(CURSOR_GLOBS)}
            alwaysApply: false
            ---
            """)
        write(base / f"{name}.mdc", front + rewrite_extra_links(body, "../", name))
    copy_extras(data, base.parent)
    for fm, body, name in data["agents"]:
        front = dedent(f"""\
            ---
            description: {fm.get('description', name)}
            alwaysApply: false
            ---
            """)
        write(base / f"agent-{name}.mdc", front + body)
    for fm, body, name in data["commands"]:
        # Cursor doesn't have slash commands — surface as on-demand rules
        front = dedent(f"""\
            ---
            description: {fm.get('description', name)} (invoke by typing: @{name})
            alwaysApply: false
            ---
            """)
        write(base / f"cmd-{name}.mdc", front + body.replace("$ARGUMENTS", "{user_input}"))


def build_copilot(data) -> None:
    print("Copilot...")
    base = ADAPTERS / "copilot" / ".github"
    lines = ["# Moodle Development Instructions", ""]
    lines.append("This repo follows Moodle plugin conventions. Apply the relevant skill below to any Moodle-related task.\n")
    for fm, _, name in data["skills"]:
        lines.append(f"- **{name}** — {fm.get('description', '')}")
    write(base / "copilot-instructions.md", "\n".join(lines) + "\n")

    for fm, body, name in data["skills"]:
        front = dedent(f"""\
            ---
            description: {fm.get('description', name)}
            tools: ['codebase', 'search', 'editFiles', 'runCommands']
            ---
            """)
        write(base / "chatmodes" / f"{name}.chatmode.md", front + rewrite_extra_links(body, "../", name))
    copy_extras(data, base)
    for fm, body, name in data["agents"]:
        front = dedent(f"""\
            ---
            description: {fm.get('description', name)}
            tools: ['codebase', 'search']
            ---
            """)
        write(base / "chatmodes" / f"{name}.chatmode.md", front + body)
    # Commands -> prompt files
    for fm, body, name in data["commands"]:
        front = dedent(f"""\
            ---
            mode: 'agent'
            description: {fm.get('description', name)}
            ---
            """)
        write(base / "prompts" / f"{name}.prompt.md", front + body.replace("$ARGUMENTS", "${input:args}"))


def build_aider(data) -> None:
    print("Aider...")
    base = ADAPTERS / "aider"
    conv = ["# Moodle Conventions for Aider", "",
            "Use the skill that matches the task. Each lives in `skills/` of the source repo;",
            "load with `/read-only skills/<name>/SKILL.md` before working on related code.",
            ""]
    for fm, _, name in data["skills"]:
        conv.append(f"- `{name}` — {fm.get('description', '')}")
    conv.append("\n## Hard rules\n")
    conv.append("- 4-space indent, no closing `?>`, snake_case functions, PascalCase classes")
    conv.append("- Every PHP file: GPL-3.0-or-later header + `defined('MOODLE_INTERNAL') || die();` (skip `classes/` PSR-4)")
    conv.append("- Every schema change: bump `version.php` + add `db/upgrade.php` step with savepoint")
    conv.append("- Never hard-code user-facing English — use `get_string()` + `lang/en/<component>.php`")
    write(base / "CONVENTIONS.md", "\n".join(conv) + "\n")
    # Skills/commands as plain MD aider can /read-only
    for fm, body, name in data["skills"]:
        write(base / "skills" / f"{name}.md",
              f"# {name}\n\n> {fm.get('description', '')}\n\n{rewrite_extra_links(body, '../', name)}")
    copy_extras(data, base)
    for fm, body, name in data["commands"]:
        write(base / "commands" / f"{name}.md", f"# /{name}\n\n> {fm.get('description', '')}\n\n{body.replace('$ARGUMENTS', '<args>')}")


def build_continue(data) -> None:
    print("Continue...")
    base = ADAPTERS / "continue"
    rules = []
    for fm, body, name in data["skills"]:
        rules.append({"name": name, "desc": fm.get("description", "")})
        write(base / "rules" / f"{name}.md",
              f"---\nname: {name}\ndescription: {fm.get('description', '')}\n---\n\n"
              f"{rewrite_extra_links(body, '../', name)}")
    copy_extras(data, base)
    meta = manifest()
    yaml_lines = [f"name: {meta['name']}", f"version: {meta['version']}", "schema: v1", "rules:"]
    for r in rules:
        yaml_lines.append(f"  - uses: ./rules/{r['name']}.md")
    yaml_lines.append("prompts:")
    for fm, _, name in data["commands"]:
        yaml_lines.append(f"  - name: {name}")
        yaml_lines.append(f"    description: {fm.get('description', name)}")
        yaml_lines.append(f"    prompt: ./prompts/{name}.md")
    write(base / "config.yaml", "\n".join(yaml_lines) + "\n")
    for fm, body, name in data["commands"]:
        write(base / "prompts" / f"{name}.md", body.replace("$ARGUMENTS", "{{{ input }}}"))


def build_generic(data) -> None:
    print("Generic...")
    out = ["# Moodle Development Prompts (agent-agnostic)", "",
           "Drop these into any LLM coding assistant. Links to `moodle-skill-files/` are files beside this one:",
           "open one only when the skill says its condition applies.",
           ""]
    out.append("## Skills (load on relevant tasks)\n")
    for fm, body, name in data["skills"]:
        out.append(f"### {name}\n")
        out.append(f"> {fm.get('description', '')}\n")
        out.append(rewrite_extra_links(body, "", name))
        out.append("\n---\n")
    copy_extras(data, ADAPTERS / "generic")
    out.append("## Agents (specialized review/scaffolding)\n")
    for fm, body, name in data["agents"]:
        out.append(f"### {name}\n")
        out.append(f"> {fm.get('description', '')}\n")
        out.append(body)
        out.append("\n---\n")
    out.append("## Commands (one-shot workflows)\n")
    for fm, body, name in data["commands"]:
        out.append(f"### /{name}\n")
        out.append(f"> {fm.get('description', '')}\n")
        out.append(body.replace("$ARGUMENTS", "<args>"))
        out.append("\n---\n")
    write(ADAPTERS / "generic" / "PROMPTS.md", "\n".join(out))


def main() -> None:
    data = load_all()
    print(f"Loaded {len(data['skills'])} skills, {len(data['agents'])} agents, {len(data['commands'])} commands.\n")
    for target in TARGETS:
        shutil.rmtree(ADAPTERS / target, ignore_errors=True)
    build_cursor(data)
    build_copilot(data)
    build_aider(data)
    build_continue(data)
    build_generic(data)
    print("\nDone. Commit the regenerated files under adapters/, including new and deleted ones.")


if __name__ == "__main__":
    main()
