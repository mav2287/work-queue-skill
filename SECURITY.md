# Security Policy

## Reporting a Vulnerability

Please report security issues privately rather than opening a public
issue. Use GitHub's **Report a vulnerability** flow on the repository's
Security tab (Security → Advisories → New draft security advisory).

We aim to acknowledge reports within 5 business days and to ship a fix
or mitigation within 30 days of confirmation, depending on severity.

## Scope

In scope:

- the `validate_queue.py` and `validate_skill.py` scripts and any code
  paths they expose to untrusted input,
- the `work-queue` skill content itself when it could cause an agent to
  take an action the user did not intend (the prompt-injection trust
  model is documented in `work-queue/SKILL.md`).

Out of scope:

- vulnerabilities in third-party agents that load this skill,
- issues that require modifying the skill installation outside its
  documented locations,
- denial-of-service via deliberately malformed queue files (the
  validator is best-effort; report exits or crashes only if they hang
  or leak data).

## Disclosure

Once a fix is released, the advisory is published. Credit is given to
the reporter unless they ask to remain anonymous.
