# Usage

## Getting help
To get help for the experiment command:
```
venv/bin/experiment -h
```

The complete API informations can be found [here](api.md).

## Getting started
Create this `example.py` experiment script:
```python
from experiment.api import get_experiment_builder

experiment = (get_experiment_builder()
            .on_host("raspi5", "192.168.1.102")
                .measure_with_multimeter("07D1A5642160")
                .measure_runs(2)
                  .execute("sleep 2")
                .done()
            .done()
            .build()
            )
```

Whereas:
```python
experiment = (get_experiment_builder()
              ...
              .build()
             )
```
Creates an instance of the experiment API builder and assigns it to the _experiment_ variable.
The name of the _experiment_ variable is fixed otherwise the experiment cannot be found.

```python
.on_host("raspi5", "192.168.1.102")
...
.done()
```
States that the experiment is to be run on the host _raspi5_ which can be reached with the IP address _192.168.1.102_.

```python
.measure_with_multimeter("07D1A5642160")
```
States that for measurments the multimeter with the serial number 07D1A5642160 is to be used.

```python
.measure_runs(2)
...
.done()
```
States that the experiment is to be run 2 times and measurments to be taken for each run.

```python
.execute("sleep 2")
```
States that the command to be run on _raspi5_ is `sleep 2`, which just sleeps for 2 seconds.


Running  this experiment with:
```
venv/bin/experiment run example.py
```

Would result in the following folder/file structure:
```
resources/
└── example
    ├── example.py
    ├── experiment.log
    └── raspi5
        └── run_001
```
Under _resources_ a folder with the name of the experiment script (_example_) is created.
Also a copy cof the experiment script is placed there, along with the logfile of the experiment.

For each script a separate folder is created which receives the logs of the experiment runs.

Each run_<xxx> folder contains the logfiles of the specified measurments.
In our example:
```
markers.csv
multimeter.csv
```
Wheras _markers.csv_ receives the exact timestamps when the measured program (_sleep_) has been started and when it has finished.
Wheras _multimeter.csv_ receives the recorded multimeter samples.
