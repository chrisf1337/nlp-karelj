# [SublimeLinter @python:2]

from __future__ import print_function

import pprint
from enum import Enum
from stanford_corenlp_python import jsonrpc
from simplejson import loads
from dependency import *
from nltk.stem.snowball import SnowballStemmer
from codegen import generate_code
from collections import namedtuple


Line = namedtuple('Line', ['line', 'indent'])


def get_corenlp_result(sentence):
    result = loads(server.parse(sentence))
    # pp = pprint.PrettyPrinter()
    # pp.pprint(result)
    return result


def get_dependencies(result):
    '''Sentence must be a single sentence.'''
    return convert_to_deps(result['sentences'][0]['dependencies'])


def get_words(result):
    return result['sentences'][0]['words']


class ActionType(Enum):
    move = 1
    turn = 2
    dropBeeper = 3
    pickUpBeeper = 4


class Grouping:
    def __init__(self):
        self.verb = None
        self.numbers = []
        self.directions = []
        self.object = None

    def __repr__(self):
        return 'Grouping (verb: {}, obj: {}, nums: {}, dirs: {})'.format(
            self.verb, self.object, self.numbers, self.directions)


class TurnAction:
    def __init__(self, times):
        self.times = times

    def emit(self):
        ret = []
        for _ in range(self.times):
            ret.append(Line('karel.turnLeft()', 0))
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
        if self.object == 'karel':
            ret = []
            for _ in range(self.steps):
                ret.append(Line('karel.move()', 0))
            return ret
        else:
            # Unimplemented!
            return [Line('// Unimplemented!', 0)]

    def __str__(self):
        return 'MoveAction (obj: {}, steps: {})'.format(self.object, self.steps)

# Initialization
# Set up server connection
server = jsonrpc.ServerProxy(jsonrpc.JsonRpc20(),
                             jsonrpc.TransportTcpIp(addr=("127.0.0.1", 8080)))
pp = pprint.PrettyPrinter()
stemmer = SnowballStemmer('english')

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

# # Case 1. No direct object
corenlp_result = get_corenlp_result('Karel should move one space to the left, then turn left three times, then move one space to the right.')
dependencies = get_dependencies(corenlp_result)
words = get_words(corenlp_result)
sorted_deps = sorted(dependencies, key=lambda x: x.index)
pp.pprint(sorted_deps)
root_dep = find_first_dep_with_tag(sorted_deps, 'root')

# First do a naive search, looking for any keyword that we are interested in
verbs = []
nums = []
directions = []
for index, word in enumerate(words):
    if word[0] in verb_mapping:
        verbs.append(dep_at_index(sorted_deps, index + 1))
    elif word[0] in number_mapping:
        nums.append(dep_at_index(sorted_deps, index + 1))
    elif word[0] in relative_dir_mapping:
        directions.append(dep_at_index(sorted_deps, index + 1))

dobj = find_descendants_with_tag(sorted_deps, root_dep.index, 'dobj')

print('verbs: {}'.format(verbs))
print('dobj: {}'.format(dobj))
print('nums: {}'.format(nums))
print('directions: {}'.format(directions))

print()
print('=== NUMS ===')
for dep in nums:
    print('{}: {}'.format(dep, find_closest_ancestor_from(sorted_deps, dep.index, verbs)))
print()
print('=== DIRECTIONS ===')
for dep in directions:
    print('{}: {}'.format(dep, find_closest_ancestor_from(sorted_deps, dep.index, verbs)))


action_groupings = []
for verb in verbs:
    grouping = Grouping()
    grouping.verb = verb
    for dep in nums:
        if find_closest_ancestor_from(sorted_deps, dep.index, verbs) == verb:
            grouping.numbers.append(dep)
    for dep in directions:
        if find_closest_ancestor_from(sorted_deps, dep.index, verbs) == verb:
            grouping.directions.append(dep)
    for dep in dobj:
        if find_closest_ancestor_from(sorted_deps, dep.index, verbs) == verb:
            grouping.object = dep
    action_groupings.append(grouping)
print()
print('=== GROUPINGS ===')
pp.pprint(action_groupings)
print()

actions = []
for group in action_groupings:
    if verb_mapping[group.verb.word] == ActionType.move and (group.object is None or
       group.object.word == 'space' or group.object.word == 'himself' or
       group.object.word == 'itself'):
        # Sometimes, the dependency parser parses 'space' as a dobj(?) For example, try parsing
        # 'Karel should move forward one space.'
        move_action = MoveAction('karel', number_mapping[group.numbers[0].word])
        if len(group.directions) > 0:
            turn_action = TurnAction(relative_dir_mapping[group.directions[0].word])
        else:
            turn_action = None
        if turn_action is not None:
            actions.append(turn_action)
        actions.append(move_action)
        print(turn_action)
        print(move_action)
        print()
    elif verb_mapping[group.verb.word] == ActionType.turn:
        if len(group.directions) > 0:
            if len(group.numbers) > 0:
                times = number_mapping[group.numbers[0].word]
            turn_action = TurnAction(relative_dir_mapping[group.directions[0].word] * times)
        else:
            print('WARNING: No direction specified for TurnAction')
            turn_action = None
        if turn_action is not None:
            actions.append(turn_action)
        print(turn_action)
        print()

generate_code(actions, 'TestRobot.template')
