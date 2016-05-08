# [SublimeLinter @python:2]

from __future__ import print_function
from colorama import Fore, Style


def info(string):
    print(Fore.CYAN + '[INFO] {}'.format(string) + Style.RESET_ALL)


def warning(string):
    print(Fore.YELLOW + '[WARNING] {}'.format(string) + Style.RESET_ALL)


def error(string):
    print(Fore.RED + '[ERROR] {}'.format(string) + Style.RESET_ALL)
