# [SublimeLinter @python:2]

from __future__ import print_function

import pprint
from enum import Enum
from stanford_corenlp_python import jsonrpc
from simplejson import loads
from dependency import *
from nltk.stem.snowball import SnowballStemmer


def get_dependencies(sentence):
    '''Sentence must be a single sentence.'''
    result = loads(server.parse(sentence))
    return convert_to_deps(result['sentences'][0]['dependencies'])


class ActionType(Enum):
    move = 1
    turn = 2
    dropBeeper = 3
    pickUpBeeper = 4


class TurnAction:
    def __init__(self, times):
        self.times = times

    def emit(self):
        ret = ''
        for _ in range(self.times):
            ret += 'robot.turn()\n'
        return ret

    def __str__(self):
        return 'TurnAction (times: {})'.format(self.times)


class MoveAction:
    def __init__(self, obj, steps):
        '''
        Initializes a MoveAction
        :param steps: Number of steps the object should be moved
        :param obj: Object of the MoveAction. Can be the robot or a beeper
        :type steps: int
        :type obj: string
        '''
        self.steps = steps
        self.object = obj

    def emit(self):
        ''':returns: Java string representation of the MoveAction'''
        if self.object == 'robot':
            return 'robot.move({})\n'.format(self.steps)
        else:
            # Unimplemented!
            return '// Unimplemented!'

    def __str__(self):
        return 'MoveAction (obj: {}, steps: {})'.format(self.object, self.steps)

# Initialization
# Set up server connection
server = jsonrpc.ServerProxy(jsonrpc.JsonRpc20(),
                             jsonrpc.TransportTcpIp(addr=("127.0.0.1", 8080)))
pp = pprint.PrettyPrinter()
stemmer = SnowballStemmer('english')

# Possibilities for the verb 'move':
# 1. move left three spaces
# 2. move three spaces left
# 3. move the beeper three spaces left
# 4. move the beeper left three spaces

verb_mapping = {
    'move': ActionType.move,
    'go': ActionType.move,
    'advance': ActionType.move,
    'turn': ActionType.turn,
}

number_mapping = {
    'one': 1,
    'once': 1,
    'two': 2,
    'twice': 2,
    'three': 3,
    'thrice': 3,
    'four': 4,
    'five': 5,
}

relative_dir_mapping = {
    'left': 1,
    'backward': 2,
    'right': 3
}

# Notes
# 'Karel should move three spaces to the right.': 'right' is 'prep_to' and 'spaces' is 'dobj'
# 'Karel should move to the right three spaces.': 'right' is 'amod'
# 'Karel should move three spaces right.': 'right' is 'advmod'
# 'Karel should move right three spaces.': 'right' is 'advmod'

# # Case 1. No direct object
dependencies = get_dependencies('Karel should turn to the left twice.')
sorted_deps = sorted(dependencies, key=lambda x: x.index)
pp.pprint(sorted_deps)
root_dep = find_first_dep_with_tag(dependencies, 'root')
dobj = find_descendants_with_tag(dependencies, root_dep.index, 'dobj')
num = find_descendants_with_tag(dependencies, root_dep.index, 'num')
direction = find_descendants_with_tags(dependencies, root_dep.index, ['advmod', 'prep_to'])

# DP tags 'once' and 'twice' as 'advmod', so move those from direction to num
num_in_dir = [x for x in direction if x.word in number_mapping]
direction = [x for x in direction if x.word not in number_mapping]
num.extend(num_in_dir)

print('dobj: {}'.format(dobj))
print('num: {}'.format(num))
print('direction: {}'.format(direction))
if verb_mapping.get(root_dep.word) == ActionType.move and \
   (len(dobj) == 0 or stemmer.stem(dobj[0].word) == 'space') or \
   (len(dobj) == 1 and (dobj[0].word == 'himself' or dobj[0].word == 'itself')):
    # Sometimes, the dependency parser parses 'space' as a dobj(?) For example, try parsing 'Karel
    # should move forward one space.' I think this only happens when the action is a move action on
    # the robot itself, but I'll have to test this out more.
    turn_action = TurnAction(relative_dir_mapping[direction[0].word])
    move_action = MoveAction('robot', number_mapping[num[0].word])
    print(turn_action)
    print(move_action)
elif verb_mapping.get(root_dep.word) == ActionType.turn:
    pass

# # Case 2. No dobj
# result = loads(server.parse("Karel should move three spaces right."))
# dependencies = result['sentences'][0]['dependencies']
# pp.pprint(dependencies)
# print find_dep_with_tag(dependencies, 'dobj')

# # Case 3. Dobj is 'beeper'
# result = loads(server.parse("Karel should move the beeper right three spaces."))
# dependencies = result['sentences'][0]['dependencies']
# pp.pprint(dependencies)
# print find_dep_with_tag(dependencies, 'dobj')

# # Case 4. Dobj is 'beeper'
# result = loads(server.parse("Karel should move the beeper three spaces right."))
# dependencies = result['sentences'][0]['dependencies']
# pp.pprint(dependencies)
# print find_dep_with_tag(dependencies, 'dobj')

# if find_dep_with_tag(dependencies, 'dobj') is None:
#     nSpaces = find_dep_with_tag(dependencies, 'num')
