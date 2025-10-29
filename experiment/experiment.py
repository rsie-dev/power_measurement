#!/usr/bin/env python3

import logging.config
import sys
import argparse
from pathlib import Path

from ruamel.yaml import YAML
import ifaddr

from usb_meter import all_devices, devices_by_vid_pid, devices_by_serial_number
from usb_meter.device import Device

class Experiment:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def _start_logging(self, args):
        log_file_name = args.logFile
        num_log_level = 50 - min(4, 2 + args.verbose) * 10
        log_level = logging.getLevelName(num_log_level)

        script = Path(__file__).resolve()
        folder = script.parent
        config = folder / 'logging.yaml'

        with open(config, "rt", encoding="UTF_8") as f:
            yaml = YAML(typ="safe")
            yaml_config = yaml.load(f)
            yaml_config['handlers']['console']['level'] = log_level
            if log_file_name:
                yaml_config['handlers']['file']['filename'] = log_file_name
                yaml_config['loggers']['']['handlers'].append("file")
                yaml_config['loggers']['uvicorn.access']['handlers'].append("file")
            else:
                del yaml_config['handlers']['file']
            logging.config.dictConfig(yaml_config)

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
            sn = device.serial_number
            product = device.product_name
            manufacturer = device.manufacturer_name
            self._logger.info("- %x:%x %s %s (type: %s SN: %s)", device.device_info.vid, device.device_info.pid,
                              manufacturer, product, device.device_info.model.name, sn)

    def _device_show(self, args):
        device = self._find_device(args)
        self._logger.info("Vendor ID:     %x", device.device_info.vid)
        self._logger.info("Product ID:    %x", device.device_info.pid)
        self._logger.info("Type:          %s", device.device_info.model.name)
        self._logger.info("Serial number: %s", device.serial_number)

    def _run_experiment(self, args):
        device = self._find_device(args)
        from experiment_runner import Runner  # pylint: disable=import-outside-toplevel
        runner = Runner()
        runner.run_experiment(device, args)

    def _get_default_host(self):
        adapters = ifaddr.get_adapters()
        for adapter in adapters:
            if adapter.name != "lo":
                for ip in adapter.ips:
                    return ip.ip
        return "127.0.0.1"

    def main(self):
        parser = argparse.ArgumentParser(prog="collector")
        default = ' (default: %(default)s)'
        parser.add_argument('-v', '--verbose', action='count', default=1, help="set the verbosity level" + default)
        parser.add_argument('-l', '--logFile', help="logfile name")
        subparsers = parser.add_subparsers(required=True, dest="subcommand", title='subcommands',
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

        parser_run = subparsers.add_parser('run', parents=[id_parser], help="runs an experiment")
        parser_run.add_argument("--host", default=self._get_default_host(), help="Server listening host" + default)
        parser_run.add_argument("-p", "--port", type=int, default=10000, help="Server listening port" + default)
        parser_run.add_argument('--system', default="system.csv", help="System data file name" + default)
        parser_run.add_argument('--electrical', default="electrical.csv", help="Electrical data file name" + default)
        parser_run.add_argument("--latest-only", action="store_true",
                                help="Only log the latest electrical measurement per batch")
        parser_run.add_argument('experiment', nargs=1, help="Experiment to execute")
        parser_run.set_defaults(func=self._run_experiment)

        args = parser.parse_args()

        self._start_logging(args)
        try:
            args.func(args)
            return 0
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.exception("Error: %s", e)
        return 1


if __name__ == "__main__":
    experiment = Experiment()
    sys.exit(experiment.main())
