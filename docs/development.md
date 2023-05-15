<style>body {text-align: justify}</style>

### Prerequisites

For developing we are using [poetry](https://pre-commit.com/) and [pre-commit](https://pre-commit.com/).
You can install both with [pipx](https://github.com/pypa/pipx):

```
# poetry
pipx install poetry
pipx inject poetry poetry-dynamic-versioning
pipx inject poetry poetry-plugin-export
# pre-commit
pipx install pre-commit
```

### Install dependencies

Just run:

```
make init
```
