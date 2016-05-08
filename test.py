# [SublimeLinter @python:2]

from __future__ import print_function

import subprocess
import parser
from log import info

sentence = 'Karel should turn left and move forward three steps.'

info('Parsing sentence: {}'.format(sentence))
parser.parse(sentence)
info('Compiling TestRobot.java')
subprocess.call(['javac', '-cp', '.:KarelJRobot.jar', 'TestRobot.java'])
info('Running TestRobot.java')
subprocess.call(['java', '-cp', '.:KarelJRobot.jar', 'TestRobot'])
