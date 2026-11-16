---
name: moodle-capability-audit
description: Audit a plugin's capabilities — verifies db/access.php declarations match runtime require_capability/has_capability calls, checks risk bitmasks, default archetypes, and lang strings.
argument-hint: "[plugin-path] — defaults to cwd"
---

Audit capability declarations vs. usage for the plugin at the given path.

User's input: $ARGUMENTS

## Procedure

1. Resolve plugin path (default: cwd). Read `version.php` to get the frankenstyle `$plugin->component`.
2. Activate `moodle-security-audit` and `moodle-plugin-development` skills.
3. Parse `db/access.php` — extract declared capabilities into a set.
4. Grep the plugin for runtime capability use:
   - `require_capability\(['"]([^'"]+)['"]`
   - `has_capability\(['"]([^'"]+)['"]`
   - `require_all_capabilities\(\[(.*?)\]`
   - `has_any_capability\(\[(.*?)\]` and `has_all_capabilities\(\[(.*?)\]`
   - In `db/services.php`: `'capabilities' => '...'` (documentation only: core does not enforce it, so the
     function itself must still call `require_capability()`)
   - In `classes/external/`: the same calls inside `execute()`
   - In `amd/src`, templates and `db/` files: capability names passed as strings
5. Cross-reference:
   - **Used but not declared** -> ERROR for a capability in this plugin's own namespace (the check always
     denies, with a debugging notice). A capability of core or of another plugin is not declared here; check
     that it exists there instead.
   - **Declared but never used** -> WARNING (dead capability, or used via JS/dynamic — flag for human check).
   - **Declared with no `riskbitmask`** on a capability that grants write or admin actions -> WARNING.
6. For each declared capability, verify:
   - `captype` is one of `read`/`write`.
   - `contextlevel` is a valid `CONTEXT_*` constant.
   - `archetypes` includes a sensible default (most caps should have `'manager' => CAP_ALLOW` at minimum).
   - `riskbitmask` uses the right combination of `RISK_SPAM | RISK_XSS | RISK_PERSONAL | RISK_CONFIG | RISK_DATALOSS | RISK_MANAGETRUST`.
     A capability whose writes are shown to other users carries `RISK_XSS` (`moodle-release-preflight`).
   - A lang string exists. For `<type>/<name>:<cap>` the key is `<name>:<cap>`, without the plugin type:
     `local/attendance:export` needs `$string['attendance:export']` in `lang/en/local_attendance.php` (an
     activity module's file is `lang/en/<name>.php`). Capabilities have no `_help` string.
7. Check `clonepermissionsfrom`: copying role permissions from a risky capability (for example
   `moodle/site:config`) — flag.
8. If any cap uses `CONTEXT_SYSTEM` and grants write/admin, ensure `RISK_CONFIG` or `RISK_DATALOSS` is set.
9. A page or web service function that calls `require_login()` and no capability, while doing more than showing
   users their own data, is a finding even though no capability is misdeclared (`moodle-release-preflight`).

## Output

```markdown
# Capability audit: <component>

## Summary
- Declared: N | Used: N | Orphan declarations: N | Undeclared usages: N
- Risk-bitmask issues: N | Missing lang strings: N

## Errors
- foo.php:88 — `has_capability('local/example:doit', ...)` but `local/example:doit` not in db/access.php

## Warnings
- db/access.php:42 — `local/example:legacy` declared but no runtime usage (dead?)
- db/access.php:60 — `local/example:writeall` is write/CONTEXT_SYSTEM but no RISK_CONFIG flag

## Missing lang strings
- `local/example:doit` — add `$string['example:doit'] = '...';` to lang/en/local_example.php

## Suggested next steps
1. Add missing declarations to db/access.php, bump version.php
2. Remove dead caps or document why kept (e.g., used by sibling plugin)
3. Add risk bitmasks
4. Run `php admin/cli/upgrade.php --non-interactive` from the Moodle root after the version bump to apply changes
```

## Rules

- Never modify files — report only.
- Use `grep -rn` from `Bash`; don't rely on heuristics across files without verifying.
- If `db/access.php` doesn't exist, say so — the plugin declares no capabilities. Still scan for hardcoded `has_capability` strings.
- Capability strings can be built dynamically (`"$component:" . $action`) — flag these as "manual review needed".
