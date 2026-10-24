# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of this project and healthcare data handling seriously. If you discover a vulnerability or security flaw, please do NOT file a public issue.

Instead, please report the vulnerability privately by emailing:
`security@healthcare-agents.internal` (or contacting the project maintainers via GitHub Security Advisories).

Please include:
- A description of the issue and potential impact
- Detailed reproduction steps or proof-of-concept
- Any relevant logs, versions, or configuration settings

We will acknowledge receipt within 48 hours and work with you on remediation and responsible disclosure.

## Security Practices
- **No Secrets in Code:** Credentials, tokens, and private keys must never be committed.
- **Model Sandboxing:** Model weights and execution environments must be isolated.
- **Data Governance:** No patient health information (PHI) should ever be transmitted without appropriate de-identification and security boundaries.
