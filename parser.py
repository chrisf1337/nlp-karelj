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
from log import info, warning
import sys


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
    ret = []
    for e in result['sentences'][0]['words']:
        e[0] = e[0].lower()
        ret.append(e)
    return ret


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
    def __init__(self, times, cardinal):
        self.times = times
        self.cardinal = cardinal

    def emit(self):
        ret = []
        if self.cardinal is None:
            ret.append(Line('karel.turnLeft({});'.format(self.times), 0))
        elif self.times is None:
            if self.cardinal == 'north':
                ret.append(Line('while (!karel.facingNorth()) {', 0))
            elif self.cardinal == 'south':
                ret.append(Line('while (!karel.facingSouth()) {', 0))
            elif self.cardinal == 'east':
                ret.append(Line('while (!karel.facingEast()) {', 0))
            elif self.cardinal == 'west':
                ret.append(Line('while (!karel.facingWest()) {', 0))
            ret.append(Line('karel.turnLeft();', 4))
            ret.append(Line('}', 0))
        return ret

    def __repr__(self):
        return 'TurnAction (times: {}, cardinal: {})'.format(self.times, self.cardinal)


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
            return [Line('karel.move({});'.format(self.steps), 0)]
        else:
            # Unimplemented!
            return [Line('// Unimplemented!', 0)]

    def __repr__(self):
        return 'MoveAction (obj: {}, steps: {})'.format(self.object, self.steps)

# Initialization
# Set up server connection
server = jsonrpc.ServerProxy(jsonrpc.JsonRpc20(),
                             jsonrpc.TransportTcpIp(addr=("127.0.0.1", 8080)))
stemmer = SnowballStemmer('english')

verb_mapping = {
    'move': ActionType.move,
    'go': ActionType.move,
    'advance': ActionType.move,
    'turn': ActionType.turn,
    'face': ActionType.turn,
    'pick': ActionType.pickUpBeeper,
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
    'forward': 0,
    'left': 1,
    'backward': 2,
    'right': 3
}

cardinal_dirs = ['north', 'south', 'east', 'west']


def parse(sentence, log_file=None):
    pp = pprint.PrettyPrinter(stream=log_file)
    # # Case 1. No direct object
    corenlp_result = get_corenlp_result(sentence)
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
        elif word[0] in relative_dir_mapping or word[0] in cardinal_dirs:
            directions.append(dep_at_index(sorted_deps, index + 1))

    dobj = find_descendants_with_tag(sorted_deps, root_dep.index, 'dobj')

    print('verbs: {}'.format(verbs), file=log_file)
    print('dobj: {}'.format(dobj), file=log_file)
    print('nums: {}'.format(nums), file=log_file)
    print('directions: {}'.format(directions), file=log_file)

    print(file=log_file)
    print('=== NUMS ===', file=log_file)
    for dep in nums:
        print('{}: {}'.format(dep, find_closest_ancestor_from(sorted_deps, dep.index, verbs)), file=log_file)
    print(file=log_file)
    print('=== DIRECTIONS ===', file=log_file)
    for dep in directions:
        print('{}: {}'.format(dep, find_closest_ancestor_from(sorted_deps, dep.index, verbs)), file=log_file)

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
    print(file=log_file)
    print('=== GROUPINGS ===', file=log_file)
    pp.pprint(action_groupings)
    print(file=log_file)

    actions = []
    for group in action_groupings:
        if verb_mapping[group.verb.word] == ActionType.move and (group.object is None or
           stemmer.stem(group.object.word) == 'space' or group.object.word == 'himself' or
           group.object.word == 'itself'):
            # Sometimes, the dependency parser parses 'space' as a dobj(?) For example, try parsing
            # 'Karel should move forward one space.'
            if len(group.numbers) == 0:
                # No numbers, so we'll assume that we move one space in each specified direction
                for direction in group.directions:
                    if direction.word in relative_dir_mapping:
                        action = TurnAction(relative_dir_mapping[direction.word], None)
                        actions.append(action)
                        print(action, file=log_file)
                    elif direction.word in cardinal_dirs:
                        action = TurnAction(None, direction.word)
                        actions.append(action)
                        print(action, file=log_file)
                    action = MoveAction('karel', 1)
                    actions.append(action)
                    print(action, file=log_file)
            elif len(group.directions) == 0:
                # No directions, so we move forward the specified number of times in the forward
                # direction
                for num in group.numbers:
                    action = MoveAction('karel', number_mapping[num.word])
                    actions.append(action)
                    print(action, file=log_file)
            else:
                move_action = MoveAction('karel', number_mapping[group.numbers[0].word])
                if len(group.directions) == 0:
                    turn_action = None
                else:
                    if group.directions[0].word in relative_dir_mapping:
                        turn_action = TurnAction(relative_dir_mapping[group.directions[0].word], None)
                    elif group.directions[0].word in cardinal_dirs:
                        turn_action = TurnAction(None, group.directions[0].word)
                if turn_action is not None:
                    actions.append(turn_action)
                    print(turn_action, file=log_file)
                actions.append(move_action)
                print(move_action, file=log_file)
        elif verb_mapping[group.verb.word] == ActionType.turn:
            if len(group.directions) == 0:
                warning('WARNING: No direction specified for TurnAction')
                turn_action = None
            else:
                if group.directions[0].word in relative_dir_mapping:
                    if len(group.numbers) > 0:
                        times = number_mapping[group.numbers[0].word]
                    else:
                        times = 1
                    turn_action = TurnAction(relative_dir_mapping[group.directions[0].word] *
                                             times, None)
                elif group.directions[0].word in cardinal_dirs:
                    turn_action = TurnAction(None, group.directions[0].word)
            if turn_action is not None:
                actions.append(turn_action)
                print(turn_action, file=log_file)
    print(actions, file=log_file)
    return actions

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        contents = f.read().replace('\n', ' ')
    parse(contents)
