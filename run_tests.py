# [SublimeLinter @python:2]

from __future__ import print_function

import subprocess
import parser
from log import info
from codegen import generate_code
import glob
import re
import os

TESTS_DIR = 'tests'


def run_test_number(test_number):
    info('Running test {}'.format(test_number))
    os.chdir(TESTS_DIR)
    with open('test-{}.txt'.format(test_number), 'r') as f, open('test-{}.log'.format(test_number), 'w') as log_file:
        contents = f.read().replace('\n', ' ')
        info('Parsing sentence: {}'.format(contents))
        actions = parser.parse(contents, log_file)
        java_file = 'TestRobot{}.java'.format(test_number)
        generate_code(actions, test_number, 'TestRobot.template', java_file)
    with open('test-{}.log'.format(test_number), 'a') as log_file:
        info('Compiling {}'.format(java_file))
        subprocess.call(['javac', '-cp', '.:KarelJRobot.jar', java_file], stdout=log_file)
        info('Running {}'.format(java_file))
        subprocess.call(['java', '-cp', '.:KarelJRobot.jar', 'TestRobot{}'.format(test_number)], stdout=log_file)

if __name__ == '__main__':
    for file in glob.glob('{}/*.txt'.format(TESTS_DIR)):
        pattern = re.compile(r'.*-(\d+)\.txt')
        test_number = int(re.match(pattern, file).group(1))
        run_test_number(test_number)
