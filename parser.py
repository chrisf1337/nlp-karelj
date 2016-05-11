# [SublimeLinter @python:2]

from __future__ import print_function

import pprint
from enum import Enum
from stanford_corenlp_python import jsonrpc
from simplejson import loads
import dependency as dp
from nltk.stem.snowball import SnowballStemmer
from collections import namedtuple
from log import warning
import sys


Line = namedtuple('Line', ['line', 'indent'])


def get_corenlp_result(sentence):
    result = loads(server.parse(sentence))
    # pp = pprint.PrettyPrinter()
    # pp.pprint(result)
    return result


def get_dependencies(result):
    '''Sentence must be a single sentence.'''
    return dp.convert_to_deps(result['sentences'][0]['dependencies'])


def get_words(result):
    ret = []
    for e in result['sentences'][0]['words']:
        e[0] = e[0].lower()
        ret.append(e)
    return ret


class ActionType(Enum):
    move = 1
    turn = 2
    putBeeper = 3
    pickBeeper = 4


class CondType(Enum):
    hasBeepers = 1
    facing = 2


class ActionGrouping:
    def __init__(self, verb):
        self.verb = verb
        self.numbers = []
        self.directions = []
        self.object = None

    def __repr__(self):
        return 'ActionGrouping (verb: {}, obj: {}, nums: {}, dirs: {})'.format(
            self.verb, self.object, self.numbers, self.directions)


class CondGrouping:
    def __init__(self, verb):
        self.verb = verb
        self.condType = cond_verb_mapping[verb.word]
        self.parent = None
        self.direction = None

    def __repr__(self):
        return 'CondGrouping (verb: {}, type: {}, parent: {}, dir: {})'.format(self.verb, self.condType, self.parent, self.direction)


class TurnAction:
    def __init__(self, times, cardinal):
        self.times = times
        self.cardinal = cardinal

    def emit(self, indent=0):
        ret = []
        if self.cardinal is None:
            ret.append(Line('karel.turnLeft({});'.format(self.times), indent))
        elif self.times is None:
            if self.cardinal == 'north':
                ret.append(Line('while (!karel.facingNorth()) {', indent))
            elif self.cardinal == 'south':
                ret.append(Line('while (!karel.facingSouth()) {', indent))
            elif self.cardinal == 'east':
                ret.append(Line('while (!karel.facingEast()) {', indent))
            elif self.cardinal == 'west':
                ret.append(Line('while (!karel.facingWest()) {', indent))
            ret.append(Line('karel.turnLeft();', indent + 4))
            ret.append(Line('}', indent))
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

    def emit(self, indent=0):
        ''':returns: Java string representation of the MoveAction'''
        if self.object == 'karel':
            return [Line('karel.move({});'.format(self.steps), indent)]
        else:
            # Unimplemented!
            return [Line('// Unimplemented!', indent)]

    def __repr__(self):
        return 'MoveAction (obj: {}, steps: {})'.format(self.object, self.steps)


class PickAction:
    def __init__(self, times):
        self.times = times

    def emit(self, indent=0):
        return [Line('karel.pickBeepers({});'.format(self.times), indent)]

    def __repr__(self):
        return 'PickAction (times: {})'.format(self.times)


class PutAction:
    def __init__(self, times):
        self.times = times

    def emit(self, indent=0):
        return [Line('karel.putBeepers({});'.format(self.times), indent)]

    def __repr__(self):
        return 'PutAction (times: {})'.format(self.times)


class BeeperCond:
    def __init__(self, body):
        self.body = body

    def emit(self):
        lines = [Line('if (karel.anyBeepersInBeeperBag()) {', 0)]
        bodyLines = []
        for elem in self.body:
            bodyLines.extend(elem.emit(indent=4))
        lines.extend(bodyLines)
        lines.append(Line('}', 0))
        return lines


class DirCond:
    def __init__(self, direction, body):
        self.direction = direction
        self.body = body

    def emit(self):
        lines = []
        if self.direction == 'north':
            lines.append(Line('if (karel.facingNorth()) {', 0))
        elif self.direction == 'south':
            lines.append(Line('if (karel.facingSouth()) {', 0))
        elif self.direction == 'east':
            lines.append(Line('if (karel.facingEast()) {', 0))
        elif self.direction == 'west':
            lines.append(Line('if (karel.facingWest()) {', 0))
        bodyLines = []
        for elem in self.body:
            bodyLines.extend(elem.emit(indent=4))
        lines.extend(bodyLines)
        lines.append(Line('}', 0))
        return lines


class OrCond:
    def __init__(self, directions, hasBeeper, body):
        self.directions = directions
        self.hasBeeper = hasBeeper
        self.body = body

    def emit(self):
        lines = []
        condLine = ''
        if self.hasBeeper:
            condLine += 'karel.anyBeepersInBeeperBag()'
        for direction in self.directions:
            if len(condLine) > 0:
                condLine += ' || '
            if direction.word == 'north':
                condLine += 'karel.facingNorth()'
            elif direction.word == 'south':
                condLine += 'karel.facingSouth()'
            elif direction.word == 'east':
                condLine += 'karel.facingEast()'
            elif direction.word == 'west':
                condLine += 'karel.facingWest()'
        condLine = Line('if ({}) {{'.format(condLine), 0)
        lines.append(condLine)
        bodyLines = []
        for elem in self.body:
            bodyLines.extend(elem.emit(indent=4))
        lines.extend(bodyLines)
        lines.append(Line('}', 0))
        return lines


class AndCond:
    def __init__(self, directions, hasBeeper, body):
        self.directions = directions
        self.hasBeeper = False
        self.body = body

    def emit(self):
        lines = []
        condLine = ''
        if self.hasBeeper:
            condLine += 'karel.anyBeepersInBeeperBag()'
        for direction in self.directions:
            if len(condLine) > 0:
                condLine += ' && '
            if direction.word == 'north':
                condLine += 'karel.facingNorth()'
            elif direction.word == 'south':
                condLine += 'karel.facingSouth()'
            elif direction.word == 'east':
                condLine += 'karel.facingEast()'
            elif direction.word == 'west':
                condLine += 'karel.facingWest()'
        condLine = Line('if ({}) {{'.format(condLine), 0)
        lines.append(condLine)
        bodyLines = []
        for elem in self.body:
            bodyLines.extend(elem.emit(indent=4))
        lines.extend(bodyLines)
        lines.append(Line('}', 0))
        return lines

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
    'pick': ActionType.pickBeeper,
    'take': ActionType.pickBeeper,
    'put': ActionType.putBeeper,
    'drop': ActionType.putBeeper,
}

cond_verb_mapping = {
    'has': CondType.hasBeepers,
    'facing': CondType.facing
}

number_mapping = {
    'a': 1,
    'the': 1,
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
    corenlp_result = get_corenlp_result(sentence)
    # pp.pprint(corenlp_result)
    dependencies = get_dependencies(corenlp_result)
    words = get_words(corenlp_result)
    sorted_deps = sorted(dependencies, key=lambda x: x.index)
    pp.pprint(sorted_deps)
    print(file=log_file)
    root_dep = dp.find_first_dep_with_tag(sorted_deps, 'root')

    # First do a naive search, looking for any keyword that we are interested in
    verbs = []
    cond_verbs = []
    nums = []
    directions = []
    for index, word in enumerate(words):
        if word[0] in verb_mapping:
            verbs.append(dp.dep_at_index(sorted_deps, index + 1))
        elif word[0] in number_mapping:
            nums.append(dp.dep_at_index(sorted_deps, index + 1))
        elif word[0] in relative_dir_mapping or word[0] in cardinal_dirs:
            directions.append(dp.dep_at_index(sorted_deps, index + 1))
        elif word[0] in cond_verb_mapping:
            cond_verbs.append(dp.dep_at_index(sorted_deps, index + 1))

    dobj = dp.find_descendants_with_tag(sorted_deps, root_dep.index, 'dobj')
    marks = dp.find_descendants_with_tag(sorted_deps, root_dep.index, 'mark')

    for mark in marks:
        closest_anc = dp.find_closest_ancestor_from(sorted_deps, mark.index, verbs)
        print('{}: {}'.format(mark, closest_anc), file=log_file)

    print('verbs: {}'.format(verbs), file=log_file)
    print('cond_verbs: {}'.format(cond_verbs), file=log_file)
    print('dobj: {}'.format(dobj), file=log_file)
    print('nums: {}'.format(nums), file=log_file)
    print('directions: {}'.format(directions), file=log_file)

    print(file=log_file)
    print('=== NUMS ===', file=log_file)
    for dep in nums:
        print('{}: {}'.format(dep, dp.find_closest_ancestor_from(sorted_deps, dep.index, verbs + cond_verbs)), file=log_file)
    print(file=log_file)
    print('=== DIRECTIONS ===', file=log_file)
    for dep in directions:
        print('{}: {}'.format(dep, dp.find_closest_ancestor_from(sorted_deps, dep.index, verbs + cond_verbs)), file=log_file)
    print(file=log_file)

    action_groupings = []
    for verb in verbs:
        grouping = ActionGrouping(verb)
        for dep in nums:
            if dp.find_closest_ancestor_from(sorted_deps, dep.index, verbs + cond_verbs) == verb:
                grouping.numbers.append(dep)
        for dep in directions:
            if dp.find_closest_ancestor_from(sorted_deps, dep.index, verbs + cond_verbs) == verb:
                grouping.directions.append(dep)
        for dep in dobj:
            if dp.find_closest_ancestor_from(sorted_deps, dep.index, verbs + cond_verbs) == verb:
                grouping.object = dep
        action_groupings.append(grouping)

    cond_groupings = []
    for verb in cond_verbs:
        grouping = CondGrouping(verb)
        grouping.parent = dp.find_closest_ancestor_from(sorted_deps, verb.index, verbs)
        if grouping.condType == CondType.facing:
            for dep in directions:
                if dp.find_closest_ancestor_from(sorted_deps, dep.index, cond_verbs) == verb:
                    grouping.direction = dep
                    break
            if grouping.direction is None:
                warning('CondGrouping with type dir does not have a direction')
        cond_groupings.append(grouping)

    print('=== ACTION GROUPINGS ===', file=log_file)
    pp.pprint(action_groupings)
    print(file=log_file)

    print('=== COND GROUPINGS ===', file=log_file)
    pp.pprint(cond_groupings)
    print(file=log_file)

    # Build actions
    actions = []
    for group in action_groupings:
        # if verb_mapping[group.verb.word] == ActionType.move and (group.object is None or
        #    stemmer.stem(group.object.word) == 'space' or group.object.word == 'himself' or
        #    group.object.word == 'itself'):
        if verb_mapping[group.verb.word] == ActionType.move:
            # We'll assume for now that the word 'move' always translates to a move action. This
            # precludes translation of phrases like "Karel should move the beeper one space North"
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
                    if relative_dir_mapping.get(group.directions[0].word, 0) != 0:
                        turn_action = TurnAction(relative_dir_mapping[group.directions[0].word], None)
                    elif group.directions[0].word in cardinal_dirs:
                        turn_action = TurnAction(None, group.directions[0].word)
                    else:
                        turn_action = None
                if turn_action is not None:
                    actions.append(turn_action)
                    print(turn_action, file=log_file)
                actions.append(move_action)
                print(move_action, file=log_file)
        elif verb_mapping[group.verb.word] == ActionType.turn:
            if len(group.directions) == 0:
                warning('No direction specified for TurnAction')
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
        elif verb_mapping[group.verb.word] == ActionType.pickBeeper:
            # Assume that we're picking up a beeper
            if group.object is not None and stemmer.stem(group.object.word) != 'beeper':
                warning('Direct object of the pick action verb was not "beeper"')
            if len(group.directions) != 0:
                warning('Directions in pick action grouping')
            if len(group.numbers) == 0:
                # If no numbers present, assume that we pick up one beeper
                pick_action = PickAction(1)
                print(pick_action, file=log_file)
                actions.append(pick_action)
            else:
                for num in group.numbers:
                    pick_action = PickAction(number_mapping[num.word])
                    print(pick_action, file=log_file)
                    actions.append(pick_action)
        elif verb_mapping[group.verb.word] == ActionType.putBeeper:
            if group.object is not None and stemmer.stem(group.object.word) != 'beeper':
                warning('Direct object of the put action verb was not "beeper"')
            if len(group.directions) != 0:
                warning('Directions in pick action grouping')
            if len(group.numbers) == 0:
                # If no numbers present, assume that we put one beeper
                put_action = PutAction(1)
                print(put_action, file=log_file)
                actions.append(put_action)
            else:
                for num in group.numbers:
                    pick_action = PutAction(number_mapping[num.word])
                    print(pick_action, file=log_file)
                    actions.append(pick_action)
    print(actions, file=log_file)

    # Build conditionals
    if len(cond_groupings) == 0:
        cond = None
    elif len(cond_groupings) == 1:
        grouping = cond_groupings[0]
        if grouping.condType == CondType.hasBeepers:
            cond = BeeperCond(actions)
        elif grouping.condType == CondType.facing:
            cond = DirCond(grouping.dir.word, actions)
    elif len(cond_groupings) > 1:
        cond_type = None
        for grouping in cond_groupings:
            if grouping.verb.tag == 'conj_or':
                cond_type = 'or'
                break
            elif grouping.verb.tag == 'conj_and':
                cond_type = 'and'
                break
        cond_dirs = []
        cond_hasBeeper = False
        for grouping in cond_groupings:
            if grouping.condType == CondType.hasBeepers:
                cond_hasBeeper = True
            elif grouping.condType == CondType.facing:
                cond_dirs.append(grouping.direction)
        if cond_type == 'or':
            cond = OrCond(cond_dirs, cond_hasBeeper, actions)
        else:
            cond = AndCond(cond_dirs, cond_hasBeeper, actions)

    print(cond, file=log_file)
    if cond is not None:
        return [cond]
    else:
        return actions

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        contents = f.read().replace('\n', ' ')
    parse(contents)
