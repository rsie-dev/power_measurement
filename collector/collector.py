#!/usr/bin/env python3

import logging.config
import sys
import argparse
from pathlib import Path

from ruamel.yaml import YAML
import ifaddr

from signal_handler import SignalHandler
from csv_measurement_logger import CSVDataLogger

class Collector:
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

    def _server(self, args):
        self._logger.info("start REST server")
        signal_handler = SignalHandler()
        from server import MetricsServer
        metrics_server = MetricsServer()
        signal_handler.add_shutdown_handler(metrics_server)
        try:
            with signal_handler.capture_signals():
                with CSVDataLogger(Path(args.metrics)) as dl:
                    metrics_server.run(args, dl)
        except KeyboardInterrupt:
            pass

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

        parser_srv = subparsers.add_parser('server', help="starts REST server")
        parser_srv.add_argument("--host", default=self._get_default_host(), help="Server listening host" + default)
        parser_srv.add_argument("-p", "--port", type=int, default=10000, help="Server listening port" + default)
        parser_srv.add_argument('-m', '--metrics', default="metrics.csv", help="metrics file name" + default)
        parser_srv.set_defaults(func=self._server)

        args = parser.parse_args()

        self._start_logging(args)
        try:
            args.func(args)
            return 0
        except Exception as e:
            self._logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    collector = Collector()
    sys.exit(collector.main())
