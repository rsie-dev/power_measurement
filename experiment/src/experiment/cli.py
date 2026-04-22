import logging.config
import argparse
from pathlib import Path

from ruamel.yaml import YAML
import ifaddr
from usb_multimeter import all_devices, devices_by_vid_pid, devices_by_serial_number
from usb_multimeter.device import Device

from experiment.log_util import get_formatter_info

from ._version import version, commit_id


class ExperimentMain:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def _get_app_folder(self):
        script = Path(__file__).resolve()
        folder = script.parent
        return folder

    def _get_resources_folder(self):
        folder = Path.cwd()
        resources_folder = folder / "resources"
        return resources_folder

    def _start_logging(self, args):
        log_file_name = args.logFile
        num_log_level = 50 - min(4, 2 + args.verbose) * 10
        log_level = logging.getLevelName(num_log_level)

        yaml_config = self._get_logging_config()
        yaml_config['handlers']['console']['level'] = log_level
        if log_file_name:
            yaml_config['handlers']['file']['filename'] = log_file_name
        logging.config.dictConfig(yaml_config)

    def _get_logging_config(self):
        folder = self._get_app_folder()
        config = folder / 'logging.yaml'
        with open(config, "rt", encoding="UTF_8") as f:
            yaml = YAML(typ="safe")
            return yaml.load(f)

    def _split_id(self, id_str):
        tokens = id_str.split(":")
        return int(tokens[0], 16), int(tokens[1], 16)

    def _devices_by_id(self, args):
        if args.id:
            vid, pid = self._split_id(args.id)
            return devices_by_vid_pid(vid, pid)
        if args.serial_number:
            return devices_by_serial_number(args.serial_number)
        return None

    def _get_id_description(self, args):
        if args.id:
            return "vid:pid = %s" % args.id
        if args.serial_number:
            return "serial number = %X" % args.serial_number
        raise RuntimeError("unknown id kind")

    def _find_device(self, args) -> Device:
        devices = self._devices_by_id(args)
        device = next(devices, None)
        if not device:
            raise RuntimeError("No devices found with: %s" % self._get_id_description(args))
        if next(devices, None):
            raise RuntimeError("Too many devices found with: %s" % self._get_id_description(args))
        return device

    def _device_list(self, _args):
        devices = all_devices()
        self._logger.info("Available devices:")
        for device in devices:
            try:
                device.access_check()
                sn = device.serial_number
                product = device.product_name
                manufacturer = device.manufacturer_name
                extra = ""
            except PermissionError as e:
                sn = "n/a"
                product = "n/a"
                manufacturer = "n/a"
                extra = " (%s)" % e
            self._logger.info("- %x:%x %s %s (type: %s SN: %s)%s", device.device_info.vid, device.device_info.pid,
                              manufacturer, product, device.device_info.model.name, sn, extra)

    def _device_show(self, args):
        device = self._find_device(args)
        device.access_check()
        self._logger.info("Vendor ID:     %x", device.device_info.vid)
        self._logger.info("Product ID:    %x", device.device_info.pid)
        self._logger.info("Type:          %s", device.device_info.model.name)
        self._logger.info("Serial number: %s", device.serial_number)
        self._logger.info("Location:      %s", device.location)

    def _run_experiment(self, args):
        from experiment.create import Runner  # pylint: disable=import-outside-toplevel
        resources = self._get_resources_folder()
        log_config = self._get_logging_config()
        formatter_info: tuple[type, dict] = get_formatter_info(log_config)
        runner = Runner(resources, formatter_info)
        runner.run_experiment(args)

    def _get_default_host(self):
        adapters = ifaddr.get_adapters()
        for adapter in adapters:
            if adapter.name != "lo":
                for ip in adapter.ips:
                    return ip.ip
        return "127.0.0.1"

    def _show_version(self, parser: argparse.ArgumentParser):
        self._logger.error("%s v%s (%s)", parser.prog, version, commit_id)

    def main(self):
        parser = argparse.ArgumentParser()
        default = ' (default: %(default)s)'
        parser.add_argument('-v', '--verbose', action='count', default=1, help="set the verbosity level" + default)
        parser.add_argument('-l', '--logFile', help="logfile name")
        parser.add_argument('--version', action='store_true', help="shows version information and exits")

        subparsers = parser.add_subparsers(dest="subcommand", title='subcommands',
                                           description='valid subcommands', help='sub-command help')

        id_parser = argparse.ArgumentParser(add_help=False)
        id_group = id_parser.add_mutually_exclusive_group(required=True)
        id_group.add_argument('--id', help="Device vendorid:productid")
        id_group.add_argument('--serial-number', type=lambda x: int(x, 16), help="Device serial number")

        parser_device = subparsers.add_parser('device', help="device commands")
        device_subparsers = parser_device.add_subparsers(required=True, dest="subcommand", title='subcommands',
                                                         description='valid subcommands', help='sub-command help')
        parser_device_list = device_subparsers.add_parser('list', help="List devices")
        parser_device_list.set_defaults(func=self._device_list)
        parser_device_show = device_subparsers.add_parser('show', parents=[id_parser], help="Show device details")
        parser_device_show.set_defaults(func=self._device_show)

        parser_run = subparsers.add_parser('run', help="runs an experiment")
        parser_run.add_argument("--host", default=self._get_default_host(), help="Server listening host" + default)
        parser_run.add_argument("-p", "--port", type=int, default=10000, help="Server listening port" + default)
        parser_run.add_argument('--system', default="system.csv", help="System data file name" + default)
        parser_run.add_argument('--ssh-user', default="ctest", help="SSH user" + default)
        parser_run.add_argument('--ssh-key', type=Path, help="File from which the private key for is read")
        parser_run.add_argument('--no-shuffle', action='store_true', help="Does not shuffle measurements")
        parser_run.add_argument('--no-progress', action='store_true', help="Disable progress bar")
        parser_run.add_argument('experiment', nargs=1, help="Experiment to execute")
        parser_run.set_defaults(func=self._run_experiment)

        args = parser.parse_args()
        if args.version:
            self._show_version(parser)
            return 0

        if "func" not in args:
            parser.error("the following arguments are required: subcommand")

        self._start_logging(args)
        try:
            args.func(args)
            return 0
        except KeyboardInterrupt:
            self._logger.warning("User cancel")
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.exception("Error: %s", e)
        return 1


def app():
    experiment = ExperimentMain()
    return experiment.main()
