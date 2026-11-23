# Security Policy

## Supported Versions

Only the latest minor release receives security updates. Pin to a tagged release for production use.

| Version | Supported |
|---------|-----------|
| 0.1.x   | yes       |

## Reporting a Vulnerability

**Do not open a public issue, pull request or discussion for security reports.**

Report privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**, or go
straight to <https://github.com/adamjenkins/wisecat-moodle-dev/security/advisories/new>. Only the maintainer sees
the report, and the fix can be discussed and prepared in the same private advisory before anything is published.

If you cannot use GitHub, email **adam@wisecat.net** with the subject `[wisecat-moodle-dev security]` instead.

Include:
- Affected skill / command / agent / adapter file
- Reproduction prompt or steps
- Impact (prompt injection, data exfiltration, malicious code generation, credential exposure, etc.)
- Suggested fix if you have one

You will receive an acknowledgement within **72 hours**. A fix or mitigation is targeted within **14 days** for high-severity issues.

## Scope

In scope:
- Skill / agent / command content that could lead Claude to generate vulnerable Moodle code (missing `require_sesskey`, SQL injection patterns, capability bypass, etc.)
- Prompt-injection vectors inside skill/agent bodies
- Adapter generation script (`scripts/build-adapters.py`) producing unsafe output
- CI workflow misconfigurations leaking secrets
- Dependency vulnerabilities in pinned GitHub Actions

Out of scope:
- Vulnerabilities in Moodle core (report to [Moodle Tracker](https://moodle.atlassian.net/jira/projects))
- Vulnerabilities in Claude Code itself (report to Anthropic)
- Issues that require an attacker to already control the user's editor or shell

## Disclosure

Coordinated disclosure preferred. Once a fix is released, the GitHub security advisory is published, with you
credited in it and in `CHANGELOG.md` and the release notes unless you ask to stay anonymous.
