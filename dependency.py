# [SublimeLinter @python:2]


class Dependency:
    def __init__(self, dep):
        self.tag = dep[0]
        self.parent = dep[1][0]
        self.parent_index = dep[1][1]
        self.word = dep[2][0]
        self.index = dep[2][1]

    def __repr__(self):
        return '({tag}, ({parent}, {parent_index}), ({word}, {index}))'.format(
            tag=self.tag,
            parent=self.parent,
            parent_index=self.parent_index,
            word=self.word,
            index=self.index
        )


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
    Finds the first word with the given tag and returns its dependency info. If
    no word in dependencies has the given tag, returns None.
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
    Finds all words whose dependency pointers point to the word at the given
    index.
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
    Follows the dependency pointer of the word at the given index up to find
    its parent.
    :type dependencies: list
    :type index: int
    :return: Parent's dependency info
    :rtype: list
    '''
    assert index <= len(dependencies)
    # Sort dependencies based on word index
    sorted_deps = sorted(dependencies, key=lambda x: x.index)
    dep = sorted_deps[index - 1]
    parent_index = dep.parent_index
    return sorted_deps[parent_index]


def find_ancestor_with_tag(dependencies, index, tag):
    '''
    Continues following the dependency pointers of the given word's ancestors
    until it finds the first word with the given tag and returns its dependency
    info, or it finds ROOT and returns None.
    :param tag: Word tag to stop at
    :type dependencies: list
    :type index: int
    :type tag: string
    :return: Dependency info of ancestor whose tag is the given tag
    :rtype: list
    '''
    assert index <= len(dependencies)
    # Sort dependencies based on word index
    sorted_deps = sorted(dependencies, key=lambda x: x.index)
    dep = sorted_deps[index - 1]
    if tag == 'root' and dep.tag == 'root':
        return dep
    parent_index = index
    while dep.tag != tag and dep.tag != 'root':
        parent_index = dep.parent_index
        dep = sorted_deps[parent_index - 1]
    if dep.tag == tag:
        return dep
    else:
        return None
