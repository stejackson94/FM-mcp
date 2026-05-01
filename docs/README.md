# Documentation

This folder contains architecture and maintenance documentation for the FM MCP project.

## Documents

- [Column Aliases Guide](./column-aliases.md)
  - Where to update raw FM column name normalization and natural-language metric aliases.
  - How to add a new metric safely.
- [App Overview](./app-overview.md)
  - End-to-end explanation of how data moves through the system.
  - Covers both MCP mode and browser UI mode.
- [High-Level Design](./high-level-design.md)
  - System components, runtime boundaries, and design decisions.
- [Operations and Maintenance](./operations-and-maintenance.md)
  - Day-2 operations, troubleshooting, testing, and release checks.

## Quick Start For Maintainers

1. Read [App Overview](./app-overview.md) to understand flow and key modules.
2. Use [Column Aliases Guide](./column-aliases.md) when FM export columns change.
3. Use [Operations and Maintenance](./operations-and-maintenance.md) for runbooks and debugging.
4. Use [High-Level Design](./high-level-design.md) for architecture discussions and larger refactors.
