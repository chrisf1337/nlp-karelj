# [SublimeLinter @python:2]

from __future__ import print_function

import pprint
from enum import Enum
from stanford_corenlp_python import jsonrpc
from simplejson import loads
from dependency import *
from nltk.stem.snowball import SnowballStemmer


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
corenlp_result = get_corenlp_result('Karel should move forward one space, then turn left.')
dependencies = get_dependencies(corenlp_result)
words = get_words(corenlp_result)
sorted_deps = sorted(dependencies, key=lambda x: x.index)
pp.pprint(sorted_deps)
root_dep = find_first_dep_with_tag(sorted_deps, 'root')

# DP tags the non-root verbs in sentences with multiple verbs like
#     'Karel should move left two spaces, then he should turn right once, and finally he should
#     turn left twice.'
# with either 'conj_and' or 'parataxis'. In this case, the first 'turn' in the 'then' clause is
# tagged with 'parataxis', and the second 'turn' in the 'and finally' clause is tagged with
# 'conj_and'.

# DP tags the second 'turn' and 'move' in
#    'Karel should turn left twice, turn right twice, then move forward two spaces.'
# with 'ccomp' and 'dep', respectively.

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

# other_verbs = find_descendants_with_tags(sorted_deps, root_dep.index,
#                                          ['conj_and', 'parataxis', 'ccomp', 'dep'])
# nums = find_descendants_with_tag(sorted_deps, root_dep.index, 'num')
# directions = find_descendants_with_tags(sorted_deps, root_dep.index,
#                                         ['advmod', 'prep_to', 'acomp'])

# DP tags 'once' and 'twice' as 'advmod', so move those from direction to num.
# num_in_dir = [x for x in directions if x.word in number_mapping]
# DP also tags 'then' as 'advmod', so remove those from direction
# directions = [x for x in directions if x.word in relative_dir_mapping]
# nums.extend(num_in_dir)

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

# for group in grouping:
#     if verb_mapping.get(group[0]) == ActionType.move and \
#     ((len(dobj) == 0 or stemmer.stem(dobj[])))


if verb_mapping.get(root_dep.word) == ActionType.move and \
   ((len(dobj) == 0 or stemmer.stem(dobj[0].word) == 'space') or
   (len(dobj) == 1 and (dobj[0].word == 'himself' or dobj[0].word == 'itself'))):
    # Sometimes, the dependency parser parses 'space' as a dobj(?) For example, try parsing 'Karel
    # should move forward one space.' I think this only happens when the action is a move action on
    # the robot itself, but I'll have to test this out more.
    if len(directions) > 0 and directions[0].word in relative_dir_mapping:
        turn_action = TurnAction(relative_dir_mapping[directions[0].word])
    else:
        turn_action = None
    move_action = MoveAction('robot', number_mapping[nums[0].word])
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
