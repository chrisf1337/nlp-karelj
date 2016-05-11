# [SublimeLinter @python:2]
from __future__ import print_function


class Dependency:
    def __init__(self, dep):
        self.tag = dep[0]
        self.parent = dep[1][0].lower()
        self.parent_index = dep[1][1]
        self.word = dep[2][0].lower()
        self.index = dep[2][1]

    def __repr__(self):
        return '({tag}, ({parent}, {parent_index}), ({word}, {index}))'.format(
            tag=self.tag,
            parent=self.parent,
            parent_index=self.parent_index,
            word=self.word,
            index=self.index
        )

    def __eq__(self, other):
        return self.tag == other.tag and self.parent == other.parent and \
            self.parent_index == other.parent_index and self.word == other.word and \
            self.index == other.index


def dep_at_index(dependencies, index):
    '''Returns the dependency whose word index is equal to the given index. If there is no such
    dependency, returns None.'''
    for dep in dependencies:
        if dep.index == index:
            return dep
    return None


def convert_to_deps(dependencies):
    return map(lambda x: Dependency(x), dependencies)


def find_first_dep_with_tag(dependencies, tag):
    '''
    Finds the first dep in the sorted dependency list with the given tag. Returns NONE if no such
    dependency is present.
    '''
    # Sort dependencies based on word index
    for dep in dependencies:
        if dep.tag == tag:
            return dep
    return None


def find_children_with_tag(dependencies, index, tag):
    '''
    Finds the first word with the given tag and returns its dependency info. If no word in
    dependencies has the given tag, returns None.
    :param tag: Tag to search for
    :type tag: string
    '''
    return [dep for dep in find_children(dependencies, index, tag) if dep.tag == tag]


def find_descendants_with_tag(dependencies, index, tag):
    return [dep for dep in find_descendants(dependencies, index) if dep.tag == tag]


def find_descendants_with_tags(dependencies, index, tags):
    '''Like find_descendants_with_tag(), but with a list of tags.'''
    return [dep for dep in find_descendants(dependencies, index) if dep.tag in tags]


def find_children(dependencies, index):
    '''
    Finds all words whose dependency pointers point to the word at the given index.
    :type dependencies: list
    :type index: int
    :return: List of child dependencies
    :rtype: list
    '''
    return [dep for dep in dependencies if dep.parent_index == index]


def find_descendants(dependencies, index):
    descendants = []
    children = find_children(dependencies, index)
    descendants.extend(children)
    if len(children) > 0:
        for child in children:
            child_descendants = find_descendants(dependencies, child.index)
            descendants.extend(child_descendants)
    return descendants


def find_parent(dependencies, index):
    '''
    Follows the dependency pointer of the word at the given index up to find its parent.
    Dependencies must be sorted by increasing word index.
    :type dependencies: list
    :type index: int
    :return: Parent's dependency info
    :rtype: list
    '''
    # We have to do a linear search for a matching index here because punctuation (commas, periods)
    # take up word token indices
    dep = dep_at_index(dependencies, index)
    parent_index = dep.parent_index
    return dependencies[parent_index]


def find_ancestor_with_tag(dependencies, index, tag):
    '''
    Continues following the dependency pointers of the given word's ancestors until it finds the
    first word with the given tag and returns its dependency info, or it finds ROOT and returns
    None. Dependencies must be sorted by increasing word index.
    :param tag: Word tag to stop at
    :type dependencies: list
    :type index: int
    :type tag: string
    :return: Dependency info of ancestor whose tag is the given tag
    :rtype: list
    '''
    return find_ancestor_with_tags(dependencies, index, [tag])


def find_ancestor_with_tags(dependencies, index, tags):
    dep = dep_at_index(dependencies, index)
    if 'root' in tags and dep.tag == 'root':
        return dep
    parent_index = index
    while dep.tag not in tags and dep.tag != 'root':
        parent_index = dep.parent_index
        dep = dep_at_index(dependencies, parent_index)
    if dep.tag in tags:
        return dep
    else:
        return None


def find_closest_ancestor_from(dependencies, index, ancestors):
    dep = dep_at_index(dependencies, index)
    if dep.tag == 'root':
        for ancestor in ancestors:
            if ancestor.tag == 'root':
                return ancestor
        return None
    parent_index = index
    while dep not in ancestors and dep.tag != 'root':
        parent_index = dep.parent_index
        dep = dep_at_index(dependencies, parent_index)
    if dep in ancestors:
        return dep
    else:
        return None
