import logging.config
import sys
import argparse
from pathlib import Path

from ruamel.yaml import YAML

class Logger:
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
                yaml_config['loggers']['root']['handlers'].append("file")
            else:
                del yaml_config['handlers']['file']
            logging.config.dictConfig(yaml_config)

    def main(self):
        parser = argparse.ArgumentParser(prog="os_install")
        default = ' (default: %(default)s)'
        parser.add_argument('-v', '--verbose', action='count', default=1, help="set the verbosity level" + default)
        parser.add_argument('-l', '--logFile', help="logfile name")

        args = parser.parse_args()

        self._start_logging(args)
        try:
            #args.func(args)
            return 0
        except Exception as e:
            self._logger.exception(f"Error: {e}")
        return 1


if __name__ == "__main__":
    logger = Logger()
    sys.exit(logger.main())
