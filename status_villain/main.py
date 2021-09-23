import argparse
import sys
from typing import List, Optional

from rich.console import Console

from status_villain.database import database_connector
from status_villain.tasks.tasks import InitTask, ReportTask

# TODO: allow users to store credentials in a local file so that
# they do not have to authenticate every time they need to add to their standup.
console = Console()

parser = argparse.ArgumentParser(
    prog="status-villain",
    formatter_class=argparse.RawTextHelpFormatter,
    description="The CLI Standup Bot For Engineeers",
)

subparser = parser.add_subparsers(title="Available commands", dest="command")
init_subparser = subparser.add_parser("init", help="Helps you setup")
init_subparser.set_defaults(cls=InitTask, which="init")

report_subparser = subparser.add_parser("report", help="Let's you write your status report.")
init_subparser.set_defaults(cls=InitTask, which="report")


def handle(parser: argparse.ArgumentParser, test_cli_args: Optional[List[str]] = None):
    if test_cli_args is not None:
        cli_args = test_cli_args
    else:
        cli_args = sys.argv[1:]

    parsed_args = parser.parse_args(cli_args)
    if parsed_args.command is None:
        console.print("You need to provide a command to status villain")
        parser.print_help()
        return 1
    if parsed_args.command == "init":
        # print some messages that explain what is going to happen in the
        # init task
        task = InitTask()
        task.run()
    elif parsed_args.command == "report":
        task = ReportTask()
        task.run()
    else:
        print(f"{parsed_args.command} is not implemented")


def main():
    database_connector.connect()
    database_connector.create_models()
    handle(parser=parser)


if __name__ == "__main__":
    exit(main())
