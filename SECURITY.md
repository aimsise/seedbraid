# Security Policy

## Supported Versions
Security fixes are currently provided for:

| Version | Supported |
|---|---|
| 2.0.0 | Yes |
| 1.1.x | Security fixes only |
| <1.1.0 | No (end of life) |

## Reporting a Vulnerability
If you find a security issue, do not open a public issue first.

Preferred path:
1. Use GitHub Security Advisories (private vulnerability report) for this repository.
2. Include reproduction steps, affected commands/files, and impact.
3. If possible, include a minimal proof-of-concept seed/genome pair.

## Response Expectations
- Initial triage target: within 5 business days.
- Status update cadence: at least weekly until resolution.
- Public disclosure: after patch is available, coordinated with reporter.

## Scope Notes
- Third-party tools (`ipfs`, OS package managers, Python runtime) are out of direct code scope.
- Seedbraid-specific issues (seed parsing, integrity verification, encryption/signature handling, CLI behavior) are in scope.
