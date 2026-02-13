import logging
import importlib


def get_formatter_info(config: dict, kind=None) -> tuple[type, dict]:
    config = config.copy()
    log_type = kind if kind else "file"
    config_formatter = config["formatters"][log_type]
    config_formatter["fmt"] = config_formatter.pop("format")
    formatter_class = _get_formatter_class(config_formatter)
    return formatter_class, config_formatter


def _get_formatter_class( config: dict) -> type:
    if "()" in config:
        cls_path = config.pop("()")
        module_path, class_name = cls_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        formatter_class = getattr(module, class_name)
        return formatter_class
    return logging.Formatter
