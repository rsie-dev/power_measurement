from io import StringIO

from pyinfra.operations import apt, files, systemd, server
from pyinfra import host
from pyinfra.facts.server import Arch
from pyinfra.facts.files import FindFiles

server.hostname(
        name="Set hostname",
        hostname=host.name,
        _sudo=True,
        )

files.file(
    name="Remove check password trigger file",
    path="/var/lib/dietpi/.check_user_passwords",
    present=False,
    _sudo=True,
)

apt.update(
        name="Update apt repositories",
        _sudo=True,
        )

apt.packages(
    name="Install base packages",
    packages=["fish", "vim", "less", "tmux", "iputils-ping", "iptables", "wget", "git", "lm-sensors"],
    no_recommends=True,
    _sudo=True,
)

if host.data.get("install_cpupower", True):
    apt.packages(
        name="Install CPU power util",
        packages=["linux-cpupower"],
        no_recommends=True,
        _sudo=True,
    )

apt.packages(
    name="Install fix for ssh disconnect",
    packages=["libpam-systemd", "dbus"],
    no_recommends=True,
    _sudo=True,
)


apt.packages(
    name="Install network tools",
    packages=["wireless-tools", "netcat-openbsd", "wavemon"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install compression tools",
    packages=["xz-utils", "lzop", "lz4", "bzip2", "bzip3"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install stressor tools",
    packages=["stress-ng"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install python",
    packages=["python3", "python3-venv"],
    no_recommends=True,
    _sudo=True,
)


def install_telegraf():

    def get_telegraf_arch():
        arch = host.get_fact(Arch, )
        if arch == "aarch64":
            return "arm64"
        elif arch == "x86_64":
            return "amd64"
        return arch

    telegraf_version = "1.36.3-1"
    telegraf_package = "telegraf_%s_%s.deb" % (telegraf_version, get_telegraf_arch())
    files.download(
        name="Download telgraf package",
        src="https://dl.influxdata.com/telegraf/releases/%s" % telegraf_package,
        dest="/var/tmp/%s" % telegraf_package,
    )
    apt.deb(
        name="Install telegraf",
        src="/var/tmp/%s" % telegraf_package,
        _sudo=True,
    )
    systemd.daemon_reload(
        name="Reload systemd",
        _sudo=True,
    )
    systemd.service(
        name="Disable telegraf service",
        service="telegraf.service",
        running=False,
        enabled=False,
        _sudo=True,
    )

    drop_in_content = """
[Service]
#CPUSchedulingPolicy=fifo
#CPUSchedulingPriority=80
#IOSchedulingClass=realtime
IOSchedulingPriority=2
Nice=-10
"""
    add_drop_in = files.put(
        name="Create telegraf drop-in configuration",
        src=StringIO(drop_in_content),
        dest="/etc/systemd/system/telegraf.service.d/override.conf",
        _sudo=True,
    )
    systemd.daemon_reload(
        name="Reload systemd config",
        _sudo=True,
        _if=add_drop_in.did_change
    )


def remove_existing_configs():
    config_files = host.get_fact(FindFiles,
                                 path="/etc/telegraf/telegraf.d",
                                 fname="*.conf",
                                 maxdepth=1
                                 )
    for config_file in config_files:
        files.file(
            name=f"Remove telegraf config file: {config_file}",
            path=config_file,
            present=False,
            _sudo=True,
        )


def config_telegraf():
    remove_existing_configs()

    main_content = """
# Empty, look in telegraf.d for content
"""
    files.put(
        name="Empty telegraf configuration",
        src=StringIO(main_content),
        dest="/etc/telegraf/telegraf.conf",
        _sudo=True,
    )

    agent_content = """
[agent]
  ## Default data collection interval for all inputs
  interval = "100ms"
  ## Rounds collection interval to 'interval'
  ## ie, if interval="10s" then always collect on :00, :10, :20, etc.
  #round_interval = true
  round_interval = false

  ## Telegraf will send metrics to outputs in batches of at most
  ## metric_batch_size metrics.
  ## This controls the size of writes that Telegraf sends to output plugins.
  metric_batch_size = 1000

  ## Maximum number of unwritten metrics per output.  Increasing this value
  ## allows for longer periods of output downtime without dropping metrics at the
  ## cost of higher maximum memory usage.
  metric_buffer_limit = 10000

  ## Collection jitter is used to jitter the collection by a random amount.
  ## Each plugin will sleep for a random time within jitter before collecting.
  ## This can be used to avoid many plugins querying things like sysfs at the
  ## same time, which can have a measurable effect on the system.
  collection_jitter = "0s"

  ## Collection offset is used to shift the collection by the given amount.
  ## This can be be used to avoid many plugins querying constraint devices
  ## at the same time by manually scheduling them in time.
  # collection_offset = "0s"

  ## Default flushing interval for all outputs. Maximum flush_interval will be
  ## flush_interval + flush_jitter
  flush_interval = "10s"
  ## Jitter the flush interval by a random amount. This is primarily to avoid
  ## large write spikes for users running a large number of telegraf instances.
  ## ie, a jitter of 5s and interval 10s means flushes will happen every 10-15s
  flush_jitter = "0s"

  ## Collected metrics are rounded to the precision specified. Precision is
  ## specified as an interval with an integer + unit (e.g. 0s, 10ms, 2us, 4s).
  ## Valid time units are "ns", "us" (or "µs"), "ms", "s".
  ##
  ## By default or when set to "0s", precision will be set to the same
  ## timestamp order as the collection interval, with the maximum being 1s:
  ##   ie, when interval = "10s", precision will be "1s"
  ##       when interval = "250ms", precision will be "1ms"
  ##
  ## Precision will NOT be used for service inputs. It is up to each individual
  ## service input to set the timestamp at the appropriate precision.
  precision = "0s"

  ## Flag to skip running processors after aggregators
  ## By default, processors are run a second time after aggregators. Changing
  ## this setting to true will skip the second run of processors.
  skip_processors_after_aggregators = true
"""
    files.put(
        name="Create telegraf agent configuration",
        src=StringIO(agent_content),
        dest="/etc/telegraf/telegraf.d/agent.conf",
        _sudo=True,
    )

    input_cpu_content = """
[[inputs.cpu]]
  ## Whether to report per-cpu stats or not
  percpu = true
  ## Whether to report total system cpu stats or not
  totalcpu = true
  ## If true, collect raw CPU time metrics
  collect_cpu_time = false
  ## If true, compute and report the sum of all non-idle CPU states
  ## NOTE: The resulting 'time_active' field INCLUDES 'iowait'!
  report_active = false
  ## If true and the info is available then add core_id and physical_id tags
  core_tags = false
"""
    files.put(
        name="Create telegraf input CPU configuration",
        src=StringIO(input_cpu_content),
        dest="/etc/telegraf/telegraf.d/input_cpu.conf",
        _sudo=True,
    )

    input_system_content = """
# Read metrics about system load & uptime
[[inputs.system]]
  # no configuration
  fieldinclude = ["load1", "load5", "load15"]
"""
    files.put(
        name="Create telegraf input system configuration",
        src=StringIO(input_system_content),
        dest="/etc/telegraf/telegraf.d/input_system.conf",
        _sudo=True,
    )

    json_format = """
  ## The resolution to use for the metric timestamp.  Must be a duration string
  ## such as "1ns", "1us", "1ms", "10ms", "1s".  Durations are truncated to
  ## the power of 10 less than the specified units.
  json_timestamp_units = "1ms"

  ## The default timestamp format is Unix epoch time, subject to the
  # resolution configured in json_timestamp_units.
  # Other timestamp layout can be configured using the Go language time
  # layout specification from https://golang.org/pkg/time/#Time.Format
  # e.g.: json_timestamp_format = "2006-01-02T15:04:05Z07:00"
  # json_timestamp_format = "2006-01-02T15:04:05Z07:00"
  json_timestamp_format = "2006-01-02T15:04:05.999999999Z07:00"

  ## A [JSONata](https://jsonata.org/) transformation of the JSON in
  ## [standard-form](#examples). Please note that only version 1.5.4 of the
  ## JSONata is supported due to the underlying library used.
  ## This allows to generate an arbitrary output form based on the metric(s). Please use
  ## multiline strings (starting and ending with three single-quotes) if needed.
  #json_transformation = ""

  ## Filter for fields that contain nested JSON data.
  ## The serializer will try to decode matching STRING fields containing
  ## valid JSON. This is done BEFORE any JSON transformation. The filters
  ## can contain wildcards.
  #json_nested_fields_include = []
  #json_nested_fields_exclude = []
"""

#     output_file_content = f"""
# [[outputs.file]]
#   files = ["/tmp/metrics.json"]
#   # use_batch_format = false
#   rotation_max_size = "1MB"
#   # rotation_max_archives = 5
#   data_format = "json"
#
#   {json_format}
# """
#     files.put(
#         name="Create telegraf output file configuration",
#         src=StringIO(output_file_content),
#         dest="/etc/telegraf/telegraf.d/output_file.conf",
#         _sudo=True,
#     )

    server_ip = host.data.get("server_ip")
    server_port = host.data.get("server_port")
    output_http_content = f"""
[[outputs.http]]
  url = "http://{server_ip}:{server_port}/measurement/batch/"

  use_batch_format = true
      
  data_format = "json"
  
  {json_format}
  
  [outputs.http.headers]
  #   ## Should be set manually to "application/json" for json data_format
  #   Content-Type = "text/plain; charset=utf-8"
  Content-Type = "application/json"  
"""
    files.put(
        name="Create telegraf output socket configuration",
        src=StringIO(output_http_content),
        dest="/etc/telegraf/telegraf.d/output_http.conf",
        _sudo=True,
    )


install_telegraf()
config_telegraf()
