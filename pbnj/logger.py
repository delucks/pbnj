"""a custom logging formatter that colors the messages based on the severity
of the log level. Created to help my eyes whilst debugging"""
import logging

FORMAT = "%(asctime)s %(levelname)s [%(module)s] %(message)s"


class Colors:
    esc = "\033"
    black = esc + "[0;30m"
    red = esc + "[0;31m"
    green = esc + "[0;32m"
    yellow = esc + "[0;33m"
    blue = esc + "[0;34m"
    purple = esc + "[0;35m"
    cyan = esc + "[0;36m"
    white = esc + "[0;37m"
    reset = esc + "[0m"
    level_map = {
        "WARNING": yellow,
        "INFO": green,
        "DEBUG": white,
        "CRITICAL": red,
        "ERROR": red,
    }


class ColorFormatter(logging.Formatter):
    def __init__(self, msg=FORMAT, color_enabled=True):
        logging.Formatter.__init__(self, msg)
        self.color_enabled = color_enabled

    def format(self, record):
        level = record.levelname
        if self.color_enabled and level in Colors.level_map:
            color_msg = Colors.level_map[level] + record.msg + Colors.reset
            record.msg = color_msg
        return logging.Formatter.format(self, record)
