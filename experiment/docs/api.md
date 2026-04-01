# API Documentation – api.py
This module defines a set of abstract builder interfaces for constructing and executing experiments.
It follows a fluent builder pattern, enabling step-by-step configuration of experiments, hosts,
execution phases, and measurements.

## Overview
The API is structured around several builder classes:

- ExperimentBuilder → top-level entry point
- HostBuilder → per-host configuration
- Execution builders:
  - WarmupExecutionBuilder
  - MeasurementExecutionBuilder
- Command builders:
  - CommandBuilder
  - MeasuredCommandBuilder
- Lifecycle builders:
  - InitializationBuilder
  - ShutdownBuilder

All builders inherit from the abstract base class:

```python
class Builder(ABC)
```

## Core Concepts
- Fluent Interface: All methods return Self or another builder to allow chaining.
- Separation of Concerns:
  - Initialization
  - Execution (warmup & measurement)
  - Shutdown
- Measurement Support: Specialized builders extend functionality for collecting metrics.


## Class Reference
### Builder
Abstract base class for all builders.

### CommandBuilder
Defines how commands are configured before execution.

#### Methods
```python
with_work_dir(folder: str) -> Self
```
Sets the working directory for the command.

```python
done() -> ExecutionBuilder
```
Finalizes command configuration and returns to execution context.

### MeasuredCommandBuilder (extends CommandBuilder)
Adds measurement capabilities to commands.

#### Methods
```python
with_timings() -> Self
```
Enables timing measurements.
Measurements will be written to _timings.csv_ in the run folder.

```python
count_stdout(target: str | Path = None) -> Self
```
Counts occurrences in stdout.
Optional target specifies what to count.
Results will be written to _count_stdout.csv_ in the run folder.

```python
collect_file_stats(path: str) -> Self
```
Collects file statistics for a given path.
Results will be written to _file_stats.csv_ in the run folder.

### ExecutionBuilder
Defines how commands are executed.

#### Methods
```python
execute(command: str) -> Self
```
Executes a command directly.

```python
execute_with(command: str) -> CommandBuilder
```
Starts configuring a command using a CommandBuilder.

### WarmupExecutionBuilder (extends ExecutionBuilder)
Used for warmup execution phase.

#### Methods
```python
done() -> HostBuilder
```
Ends warmup phase and returns to host configuration.

### MeasurementExecutionBuilder (extends ExecutionBuilder)
Used for measurement runs with extended configuration.

#### Methods
```python
with_head_delay(delay: int) -> Self
```
Adds delay before execution starts.

```python
with_tail_delay(delay: int) -> Self
```
Adds delay after execution completes.

```python
execute_with(command: str) -> MeasuredCommandBuilder
```
Starts configuring a measurable command.
Execution markers will be written to _markers.csv_ in the run folder.
Multimeter measurements will be written to _multimeter.csv_ in the run folder.

```python
done() -> HostBuilder
```
Ends measurement phase.

### InitializationBuilder
Handles setup tasks before execution.

#### Methods
```python
upload(local: str | Path, remote: str | Path) -> Self
```
Uploads a file from local to remote.

```python
done() -> HostBuilder
```
Returns to host configuration.

### ShutdownBuilder
Handles teardown tasks after execution.

#### Methods
```python
delete(remote: str | Path) -> Self
```
Deletes a remote file.

```python
download(remote: str | Path, local: str | Path) -> Self
```
Downloads a file from remote to local.

```python
done() -> HostBuilder
```
Returns to host configuration.

### HostBuilder
Configures a host within an experiment.

#### Methods
```python
initialize() -> InitializationBuilder
```
Begins initialization phase.

```python
shutdown() -> ShutdownBuilder
```
Begins shutdown phase.

```python
with_warmup() -> WarmupExecutionBuilder
```
Starts warmup execution configuration.

```python
measure_with_multimeter(serial_number: str) -> Self
```
Enables measurement using a multimeter device.

```python
measure_runs(runs: int, tag: str = None) -> MeasurementExecutionBuilder
```
Configures repeated measurement runs.
Optional tag labels the run set.

```python
done() -> ExperimentBuilder
```
Returns to experiment-level builder.

### ExperimentBuilder
Top-level builder for constructing an experiment.

#### Methods
```python
with_metrics_collection() -> Self
```
Enables global metrics collection.
Metrics measurements will be written to _system.csv_ and _cpu.csv_ in the run folder.

```python
on_host(host_name: str, host: str) -> HostBuilder
```
Adds/configures a host.
- host_name: logical identifier
- host: address or connection string

```python
build() -> Experiment
```
Finalizes and returns an Experiment instance.

## Example Usage
```python
experiment = (
    ExperimentBuilder()
    .with_metrics_collection()
    .on_host("local", "127.0.0.1")
        .initialize()
            .upload("input.txt", "/tmp/input.txt")
        .done()
        .with_warmup()
            .execute("echo warmup")
        .done()
        .measure_runs(5, tag="test")
            .with_head_delay(1)
            .execute_with("python script.py")
                .with_timings()
            .done()
        .done()
    .done()
    .build()
)
```
