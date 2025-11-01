[![Pylint](https://github.com/rsie-dev/power_measurement/actions/workflows/pylint.yml/badge.svg)](https://github.com/rsie-dev/power_measurement/actions/workflows/pylint.yml)

## Setup
### Clone
```
git clone [-b branch] --recurse-submodules git@github.com:rsie-dev/power_measurement.git
```

### Install dependencies
```
python -m venv venv
./venv/bin/pip install -r requirements.txt
```

### Test
```
venv/bin/pylint .
```
