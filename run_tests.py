# [SublimeLinter @python:2]

from __future__ import print_function

import subprocess
import parser
from log import info, success, error
from codegen import generate_code
import glob
import re
import os
from collections import namedtuple

TESTS_DIR = 'tests'
BeeperPos = namedtuple('BeeperPos', ['x', 'y', 'num'])
RobotPos = namedtuple('RobotPos', ['x', 'y', 'direction'])


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
    score = evaluate('end-{}-test.kwld'.format(test_number), 'end-{}.kwld'.format(test_number))
    if score == 1:
        success('Test {} passed'.format(test_number))
    else:
        error('Test {} failed'.format(test_number))


# For now, we'll just evaluate on an all-or-nothing scale: if the two world states match, then 1
# point is given; otherwise, 0 points are given.
def evaluate(test_kwld, ref_kwld):
    with open(test_kwld) as test_file, open(ref_kwld) as ref_file:
        test_lines = [line for line in test_file]
        ref_lines = [line for line in ref_file]
    beeper_pattern = re.compile(r'beepers (\d+) (\d+) (\d+)')
    robot_pattern = re.compile(r'robot (\d+) (\d+) (\w+)')
    test_beepers = []
    test_robot = None
    ref_beepers = []
    ref_robot = None
    for line in test_lines:
        if 'beepers' in line:
            match = re.match(beeper_pattern, line)
            y = int(match.group(1))
            x = int(match.group(2))
            num = int(match.group(3))
            test_beepers.append(BeeperPos(x=x, y=y, num=num))
        elif 'robot' in line:
            match = re.match(robot_pattern, line)
            y = int(match.group(1))
            x = int(match.group(2))
            direction = match.group(3)
            test_robot = RobotPos(x=x, y=y, direction=direction)
    for line in ref_lines:
        if 'beepers' in line:
            match = re.match(beeper_pattern, line)
            y = int(match.group(1))
            x = int(match.group(2))
            num = int(match.group(3))
            ref_beepers.append(BeeperPos(x=x, y=y, num=num))
        elif 'robot' in line:
            match = re.match(robot_pattern, line)
            y = int(match.group(1))
            x = int(match.group(2))
            direction = match.group(3)
            ref_robot = RobotPos(x=x, y=y, direction=direction)
    test_beepers = sorted(test_beepers, key=lambda e: (e.x, e.y))
    ref_beepers = sorted(ref_beepers, key=lambda e: (e.x, e.y))
    if len(test_beepers) != len(ref_beepers) or test_robot != ref_robot:
        return 0
    for index, beeper in enumerate(test_beepers):
        if beeper != ref_beepers[index]:
            return 0
    return 1

if __name__ == '__main__':
    for file in glob.glob('{}/*.txt'.format(TESTS_DIR)):
        pattern = re.compile(r'.*-(\d+)\.txt')
        test_number = int(re.match(pattern, file).group(1))
        run_test_number(test_number)
