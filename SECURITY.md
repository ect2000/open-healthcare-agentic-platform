# Security Policy

## 1. Supported Versions

We provide security updates and patches for active milestone releases:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 0.8.x   | :white_check_mark: | Active (Current M8 Milestone) |
| 0.7.x   | :white_check_mark: | Maintenance |
| < 0.7.0 | :x:                | Unsupported |

---

## 2. Reporting a Vulnerability

We take the security of this platform and healthcare data handling seriously. If you discover a vulnerability, security flaw, or potential privacy leak, **please do NOT file a public GitHub issue.**

Instead, please report the vulnerability privately:
1. **GitHub Security Advisories**: Use the "Report a vulnerability" button under the repository's [Security tab](https://github.com/hastimal/open-healthcare-agentic-platform/security/advisories).
2. **Direct Maintainer Contact**: If the advisory portal is unavailable, contact the maintainer via GitHub at `hastimal@users.noreply.github.com`.

### What to Include:
- A clear description of the potential vulnerability and its impact.
- Step-by-step reproduction instructions or a minimal proof-of-concept.
- Component versions, environment details, or configuration flags involved.

### Our Commitment:
- We will acknowledge receipt of reports within **48 hours**.
- We will provide status updates on remediation and coordinate responsible disclosure.

---

## 3. Security, Privacy & Healthcare Demonstration Considerations

- **No Secrets in Code or Issues**: Never commit credentials, API tokens (e.g. NCBI Entrez API keys, CMS tokens), private keys, or certificates.
- **No Patient Health Information (PHI)**: This platform is designed exclusively for educational, clinical research literature, and provider registry demonstration purposes using public federal databases. **Never transmit, input, or store real Protected Health Information (PHI) or Personally Identifiable Information (PII).**
- **No Claim of HIPAA Compliance**: The platform is an open-source reference architecture and does **NOT** claim HIPAA compliance, SOC2 certification, or medical device certification.
- **Telemetry & Logging Privacy**: OpenTelemetry metrics and traces must never capture raw query text, patient symptoms, or LLM prompt/completion payloads in exported attributes.
- **Sandboxed Execution**: Models run locally or via isolated inference containers. Network policies should restrict outgoing traffic to verified public data APIs (`nih.gov`, `cms.gov`, `hhs.gov`).
