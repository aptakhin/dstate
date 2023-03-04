# dstate - distributed state machines

[![Test dstate](https://github.com/aptakhin/dstate/actions/workflows/test.yml/badge.svg)](https://github.com/aptakhin/dstate/actions/workflows/test.yml)

dstate library mission to add more clarity and maintainability to distributed applications, which can go  finite state machine approach. It adds persistence and locks on the powerfull [python-statemachine](https://github.com/fgmacedo/python-statemachine). With future releases timers support will be added.

## Install

```bash
./shell/install-local.py
# or
poetry install --with dev --with python-statemachine --with driver
```

## Usage

Pretty unstable. No examples yet.

[Tests file](./tests/test_dstate.py)

## Dev

```bash
./shell/ruff.sh
./shell/black.sh
./shell/pytest-smoke.sh
./shell/flake8.sh
./shell/mypy.sh
```

Also the same set is supported with `pre-commit`:

```bash
pre-commit install
```

Fast smoke pytests with watcher:

```bash
./shell/ptw.sh
```


Full environment tests require `docker compose`:

```bash
./full_tests/shell/beg-mongo.sh
./shell/pytest-full.sh
./full_tests/shell/end-mongo.sh
```
