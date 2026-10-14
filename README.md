# Klar.

**Meaning checks for an accessible Swiss web, powered by [Apertus](https://www.apertus-ai.org/), the Swiss open LLM.**

Accessibility scanners check that a link text, a label or a language tag *exists*. They cannot tell whether it *makes sense* to someone using a screen reader. Klar. combines deterministic checks (axe-core) with Apertus to pre-judge the WCAG 2.1 AA / eCH-0059 criteria that normally require a human: link purpose, labels, language of parts, image alternatives, error messages and more. It works in German, French and Italian. Every finding quotes the page and must be validated by a person.

It runs **on-premise or air-gapped** on a single GPU workstation, or in a **sovereign Swiss cloud**. Internal and unpublished pages never leave your organisation.

> The project lives in [`track_2b/`](track_2b/). Start with its `Makefile` and [`technical_report.md`](track_2b/technical_report.md).

## Licence

- Code: [Apache-2.0](LICENSE)
- Documentation and report: CC-BY-4.0
- Datasets: CDLA-Permissive-2.0

Third-party components are listed in [`track_2b/docs/THIRD_PARTY_NOTICES.md`](track_2b/docs/THIRD_PARTY_NOTICES.md). The name "Klar." and its logo are not covered by the Apache licence.

Klar. is a pre-check tool. **It does not certify conformance.**
