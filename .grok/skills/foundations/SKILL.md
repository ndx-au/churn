---
name: foundations
description: "Sets up modern Python packaging (pyproject.toml), SourceDriver plugin architecture via entry points, basic Typer+Rich CLI, project layout, ruff/pytest. Use when scaffolding or modifying core package structure, M001 foundations, CLI entrypoints."
---

# Foundations Skill

Implements the M001 foundations for churn.

## Core Responsibilities
- Create and maintain pyproject.toml with [project.entry-points."churn.drivers"]
- Implement churn/drivers/base.py ABC
- Plugin loader using importlib.metadata
- Typer app with rich output for `churn` and subcommands (drivers list etc.)
- Basic config/credential layer (pydantic-settings + env)
- Test layout and CI stubs

## When to use
Any time the package metadata, plugin registration, or CLI skeleton changes.

Always read specs/M001-FOUNDATIONS.md and existing code first.

Output clean, typed, documented Python following churn conventions.

Record progress in .progress/.
