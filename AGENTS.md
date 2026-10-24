# Project Operating Rules & Standards: AGENTS.md

> **Open Healthcare Agentic Platform**  
> Vendor-neutral, open-source, evidence-grounded healthcare search and agentic AI platform.

---

## Permanent Project Rules

1. **Main Branch Only**:
   - Work directly on the `main` branch only.
   - Never create feature branches.

2. **Milestone Lifecycle Workflow**:
   - Every milestone must strictly follow:
     $$\text{Implement} \rightarrow \text{Test} \rightarrow \text{Verify} \rightarrow \text{Document} \rightarrow \text{Commit} \rightarrow \text{Tag} \rightarrow \text{Push} \rightarrow \text{Verify GitHub CI}$$

3. **Mandatory Testing & Quality Checks**:
   - Run offline unit tests, integration tests, linting, type checks, and applicable live tests.
   - All tests must pass before committing or pushing.

4. **Preserve Existing Functionality**:
   - Never regress, break, or remove previously working features or tests unless explicitly requested.

5. **Milestone Documentation Standard**:
   - Save every milestone's documentation under:
     `docs/antigravity/<milestone>/`
   - Every milestone folder must contain four required documents:
     - `prompt.md`: Complete original instructions and prompt requirements.
     - `commands.md`: Exact terminal commands executed with raw outputs.
     - `implementation.md`: Files created/modified, architectural decisions, and changes made.
     - `verification.md`: Actual tests, coverage metrics, and verification results.

6. **Antigravity Documentation Index**:
   - Maintain `docs/antigravity/README.md` with links and summaries for all milestones.

7. **Truthful Evidence & Integrity**:
   - Never fabricate test results or claim skipped tests passed. Document actual outputs honestly.

8. **Security, Secrets & Data Privacy**:
   - Never commit credentials, API keys, tokens, model weights (`.gguf`, `.safetensors`), or sensitive healthcare data (PHI).

9. **Unified Atomic Commits**:
   - Commit code and milestone documentation together in atomic commits.

10. **Annotated Milestone Tags**:
    - Create an annotated Git tag for every verified milestone and push it to GitHub (e.g., `git tag -a v0.1.0-m01 -m "..."`).

11. **Git History Safety**:
    - Never force-push (`git push --force`) or overwrite/move published Git tags.

12. **Milestone Completion Gate**:
    - Do not declare a milestone complete until required tests, package checks, and GitHub Actions CI pass with recorded verification.
