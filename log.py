# [SublimeLinter @python:2]

from __future__ import print_function
from colorama import Fore, Style
import sys


def info(string):
    print(Fore.CYAN + '[INFO] {}'.format(string) + Style.RESET_ALL, file=sys.stderr)


def warning(string):
    print(Fore.YELLOW + '[WARNING] {}'.format(string) + Style.RESET_ALL, file=sys.stderr)


def error(string):
    print(Fore.RED + '[ERROR] {}'.format(string) + Style.RESET_ALL, file=sys.stderr)


def success(string):
    print(Fore.GREEN + '[SUCCESS] {}'.format(string) + Style.RESET_ALL, file=sys.stderr)
