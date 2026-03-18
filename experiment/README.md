[![Pylint](https://github.com/rsie-dev/power_measurement/actions/workflows/pylint.yml/badge.svg)](https://github.com/rsie-dev/power_measurement/actions/workflows/pylint.yml)

# Overview
Small framework to collect electrical and system metrics of SBC devices.

# Develop
```
git clone git@github.com:rsie-dev/power_measurement.git
python3 -m venv venv
```

## Install dependencies
```
venv/bin/pip install -e .[dev]
```

## Checks
```
venv/bin/pylint --source-roots . app/
venv/bin/prospector
```

## Test
```
venv/bin/pytest -v app
```

# Releasing
```
venv/bin/python -m build
venv/bin/twine upload [--repository testpypi] dist/*
```
