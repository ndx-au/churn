---
name: okf-renderer
description: "Renders and writes OKF v0.1 compliant bundles: frontmatter with required type, index.md, log.md, concept paths. Ensures ekg sibling compatibility (folder frontmatter hints, link style, section-friendly markdown). Use for bundle output, preview, validation, M004."
---

# OKF Renderer Skill

Produces valid Open Knowledge Format bundles consumable by humans, agents, and the ekg project.

Key requirements from Google OKF SPEC + ekg:
- Every concept .md has `---` frontmatter block containing at minimum `type:`
- Use relative or /bundle-root links.
- Support index.md for progressive disclosure.
- Optional log.md .
- Arbitrary extra frontmatter preserved.
- Bundle dir can be dropped into doctree/.

Provide helpers:
- write_concept(path, frontmatter_dict, body)
- generate_index(root)
- validate_bundle(root) -> report
- preview(bundle) -> rich tree or text

Always test produced bundles by inspection or simulated ekg parse (headings, yaml).
