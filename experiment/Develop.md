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
venv/bin/pylint src/experiment
venv/bin/prospector
```

## Test
```
venv/bin/pytest -v src
```

## Run
```
venv/bin/experiment -h
```

# Release
```
venv/bin/python -m build
venv/bin/twine upload [--repository testpypi] dist/*
```
