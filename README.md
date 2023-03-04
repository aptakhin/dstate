# dstate - distributed state machines

[![Test dstate](https://github.com/aptakhin/dstate/actions/workflows/test.yml/badge.svg)](https://github.com/aptakhin/dstate/actions/workflows/test.yml)

## Install

```bash
./shell/install-local.py
# or
poetry install --with dev
```

## Usage

Pretty unstable. No examples yet.

[Tests file](./tests/test_dstate.py)

## Dev

```bash
./shell/ruff.sh
./shell/black.sh
./shell/pytest.sh
./shell/flake8.sh
./shell/mypy.sh
```

Also the same set is supported with `pre-commit`:

```bash
pre-commit install
```

Pytest files with watcher:

```bash
./shell/ptw.sh
```
