---
name: dataforge
description: >
  Router alias for DataForge pipeline. Delegates to df skill.
  Use /dataforge <command> or /df <command> - both work.
user-invokable: true
argument-hint: "<command> [arguments]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
  - Agent
---

# DataForge Router (Alias)

> This is an alias for the `df` skill. Both `/dataforge <command>` and `/df <command>` work identically.

## Usage

All commands work with both prefixes:

```bash
/dataforge run <dataset> <target>
/df run <dataset> <target>

/dataforge analyze <dataset>
/df analyze <dataset>

/dataforge status <project-dir>
/df status <project-dir>
```

## Router Implementation

This skill delegates to the main `df` router. All logic and skills are in the `df` skill.

For full documentation, see `skills/df/SKILL.md` and `skills/df/README.md`.

