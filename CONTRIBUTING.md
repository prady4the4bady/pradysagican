# Contributing to PRADYSAGICAN

## Overview

PRADYSAGICAN is a superintelligent agent system. This document outlines how to contribute.

## Development Setup

```bash
# Clone and setup
git clone https://github.com/prady4the4bady/pradysagican.git
cd pradysagican
bash setup.sh

# Run tests
pytest tests/ -v

# Run linters
ruff check .
mypy pradysagican/
```

## Code Quality

- **100% test coverage** for new features
- **Type hints** on all public APIs
- **Ruff** formatting (auto-fixed on commit)
- **Mypy** strict type checking

## Submitting Changes

1. Create a feature branch
2. Write tests first
3. Implement feature
4. Run full test suite: `pytest tests/ -q`
5. Submit PR with clear description

## Key Components

- `pradysagican/core/` — Core runtime and safety systems
- `pradysagican/subsystems/` — 40+ specialized subsystems
- `tests/` — 692 test cases (100% passing)

## Questions?

[Open an issue](https://github.com/prady4the4bady/pradysagican/issues) or see [DEPLOYMENT_REPORT.md](DEPLOYMENT_REPORT.md) for architecture details.
