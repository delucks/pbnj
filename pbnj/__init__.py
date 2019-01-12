"""
       |          _)
 __ \  __ \  __ \  |
 |   | |   | |   | |
 .__/ _.__/ _|  _| |
_|             ___/

"""
import sys

__version__ = "0.3.1"
__author__ = "James Luck <me@jamesluck.com>"
__title__ = "pbnj"
__license__ = "GNU GPLv3"


def default_argparser(arguments=sys.argv[1:], docstring=None, override=None):
    """this is a default argument parser for quickly creating a configured bot
    override: a pbnj.bot.Bot object that will be configured with these arguments
    docstring: override the docstring of the argument parser
    arguments: override the args being parsed
    """
    import argparse
    import logging
    from pbnj.logger import ColorFormatter

    log = logging.getLogger("pbnj")
    color_formatter = ColorFormatter()
    sh = logging.StreamHandler()
    sh.setFormatter(color_formatter)
    log.addHandler(sh)
    p = argparse.ArgumentParser(description=docstring)
    p.add_argument("-n", "--nick", default=__title__, help="specify nickname to use")
    p.add_argument(
        "-d", "--debug", action="store_true", help="increase logging verbosity to DEBUG"
    )
    p.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="decrease logging verbosity to WARNING",
    )
    p.add_argument(
        "--no-color", action="store_true", help="disable coloration of logging output"
    )
    p.add_argument(
        "--network", default="127.0.0.1", help="FQDN of IRC network to connect to"
    )
    p.add_argument(
        "--port",
        type=int,
        default=6667,
        help="specify different port for the connection",
    )
    p.add_argument(
        "-s",
        "--ssl",
        action="store_true",
        help="use SSL in your connection to the network",
    )
    p.add_argument(
        "-c",
        "--channels",
        default="",
        help="comma-separated channels to connect to when joining",
    )
    p.add_argument(
        "--user-name",
        dest="username",
        default=__title__,
        help="specify different name to use",
    )
    p.add_argument(
        "--real-name",
        dest="realname",
        default=__title__,
        help="specify different realname to use",
    )
    p.add_argument(
        "-v", "--version", help="show version of this program", action="store_true"
    )
    args = p.parse_args(arguments)
    log_lvl = (
        logging.DEBUG if args.debug else logging.WARNING if args.quiet else logging.INFO
    )
    color_formatter.color_enabled = not args.no_color
    log.setLevel(log_lvl)
    if args.version:
        print(__title__ + " version " + __version__)
        return True
    if override:
        override.nick = args.nick
        override.username = args.username
        override.realname = args.realname
        override.ssl = args.ssl
        override.connect(args.network, args.port)
        override.channels = override._channelify(args.channels.split(","))
    return args
