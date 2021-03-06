# [SublimeLinter @python:2]

from __future__ import print_function, division

import sys
import subprocess32 as subprocess
import kjr_parser
from log import info, success, error
from codegen import generate_code
import glob
import re
import os
from collections import namedtuple
import argparse
import traceback

TESTS_DIR = 'tests'
TIMEOUT_LENGTH = 5  # in seconds
BeeperPos = namedtuple('BeeperPos', ['x', 'y', 'num'])
RobotPos = namedtuple('RobotPos', ['x', 'y', 'direction', 'beepers'])


def run_test_number(test_number):
    info('Running test {}'.format(test_number))
    with open('test-{}.txt'.format(test_number), 'r') as f, open('test-{}.log'.format(test_number), 'w') as log_file, open('start-{}.kwld'.format(test_number)) as start_kwld:
        contents = f.read().replace('\n', ' ')
        info('Parsing sentence: {}'.format(contents))
        try:
            actions = kjr_parser.parse_sentences(contents, log_file)
        except Exception:
            error('Exception while parsing sentence')
            traceback.print_exc()
            return 0
        robot_pattern = re.compile(r'robot (\d+) (\d+) (\w+) (\d+)')
        robot = None
        for line in start_kwld:
            if 'robot' in line:
                match = re.match(robot_pattern, line)
                y = int(match.group(1))
                x = int(match.group(2))
                direction = match.group(3)
                beepers = int(match.group(4))
                robot = RobotPos(x=x, y=y, direction=direction, beepers=beepers)
        java_file = 'TestRobot{}.java'.format(test_number)
        if robot is not None:
            generate_code(actions, test_number, 'TestRobot.template', java_file,
                          street=robot.y, avenue=robot.x, direction=robot.direction,
                          beepers=robot.beepers)
        else:
            generate_code(actions, test_number, 'TestRobot.template', java_file)

    with open('test-{}.log'.format(test_number), 'a') as log_file:
        info('Compiling {}'.format(java_file))
        ret = subprocess.call(['javac', '-cp', '.:KarelJRobot.jar', java_file], stdout=log_file, stderr=log_file)
        if ret == 0:
            info('Compiliation succeeded')
        else:
            error('Compilation failed. See test-{}.log for details'.format(test_number))
            return 0
        info('Running {}'.format(java_file))
        try:
            ret = subprocess.call(['java', '-cp', '.:KarelJRobot.jar', 'TestRobot{}'.format(test_number)], stdout=log_file, timeout=TIMEOUT_LENGTH)
        except subprocess.TimeoutExpired:
            error('TestRobot{} timed out'.format(test_number))
            return 0
        if ret == 0:
            info('TestRobot{} returned with code {}'.format(test_number, ret))
        else:
            error('TestRobot{} returned with code {}'.format(test_number, ret))
            return 0
    score = evaluate('end-{}-test.kwld'.format(test_number), 'end-{}.kwld'.format(test_number))
    if score == 1:
        success('Test {} passed'.format(test_number))
    else:
        error('Test {} failed'.format(test_number))
    return score


# For now, we'll just evaluate on an all-or-nothing scale: if the two world states match, then 1
# point is given; otherwise, 0 points are given.
def evaluate(test_kwld, ref_kwld):
    with open(test_kwld) as test_file, open(ref_kwld) as ref_file:
        test_lines = [line for line in test_file]
        ref_lines = [line for line in ref_file]
    beeper_pattern = re.compile(r'beepers (\d+) (\d+) (\d+)')
    robot_pattern = re.compile(r'robot (\d+) (\d+) (\w+) (\d+)')
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
            beepers = int(match.group(4))
            test_robot = RobotPos(x=x, y=y, direction=direction, beepers=beepers)
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
            beepers = int(match.group(4))
            ref_robot = RobotPos(x=x, y=y, direction=direction, beepers=beepers)
    test_beepers = sorted(test_beepers, key=lambda e: (e.x, e.y))
    ref_beepers = sorted(ref_beepers, key=lambda e: (e.x, e.y))
    if len(test_beepers) != len(ref_beepers) or test_robot != ref_robot:
        return 0
    for index, beeper in enumerate(test_beepers):
        if beeper != ref_beepers[index]:
            return 0
    return 1

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Runs tests.')
    arg_parser.add_argument('tests', type=int, nargs='*', help='Test numbers to run')
    args = arg_parser.parse_args()
    os.chdir(TESTS_DIR)
    score = 0
    total = len(glob.glob('*.txt'))
    successful_tests = []
    failed_tests = []
    if len(args.tests) == 0:
        for file in glob.glob('*.txt'):
            pattern = re.compile(r'.*-(\d+)\.txt')
            test_number = int(re.match(pattern, file).group(1))
            test_score = run_test_number(test_number)
            score += test_score
            if test_score == 1:
                successful_tests.append(test_number)
            else:
                failed_tests.append(test_number)
        print('Score: {} / {} ({}%)'.format(score, total, score / total * 100))
        print('Successful tests: {}'.format(sorted(successful_tests)))
        print('Failed tests: {}'.format(sorted(failed_tests)))
    else:
        for test in args.tests:
            run_test_number(test)
