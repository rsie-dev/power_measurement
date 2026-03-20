# Develop

## Getting help
To get help for the experiment command:
```
venv/bin/experiment -h
```

The complete API informations can be found [here](api.md).

## Getting started
Create this example.py experiment script:
```python
from experiment.api import get_experiment_builder

experiment = (get_experiment_builder()
            .on_host("raspi5", "192.168.1.102")
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

For each host a separate folder is created which receives the logs of the experiment runs.
