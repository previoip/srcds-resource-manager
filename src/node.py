import typing as t
from collections import OrderedDict

class Node:

  def __repr__(self):
    return f'{self.__class__.__name__}::[{self.name}] <- [{self.parent.name if not self.parent is None else "None"}]'

  def __init__(self, name=None, parent=None):
    self._name = name if not name is None else id(self)
    self.parent = parent
    self.children = OrderedDict()
    if not parent is None:
      parent.append_child(self)

  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, name):
    self._name = name

  @property
  def rank(self) -> int:
    return len(self.children)

  @property
  def depth(self) -> int:
    if self.is_root():
      return 0
    return len(list(self.iter_parent_node()))

  @property
  def nchild(self) -> int:
    return len(self.children)

  @property
  def atindex(self) -> int:
    if self.parent is None:
      return 0
    return tuple(self.parent.children.keys()).index(self.name)

  def is_leaf(self) -> bool:
    return len(self.children) == 0

  def is_root(self) -> bool:
    return self.parent is None

  def is_on_beginning(self) -> bool:
    return self.atindex == 0

  def is_on_end(self) -> bool:
    if self.is_root():
      return False
    return self.atindex == (self.parent.nchild - 1)

  def has(self, name):
    return name in self.children

  def spawn_child(self, name=None) -> "Node":
    child = self.__class__(name=name, parent=self)
    return child

  def append_child(self, node) -> "Node":
    if node.name in self.children:
      print('child name conflict:', node.name)
      return
    self.children[node.name] = node

  def iter_children(self) -> t.Generator["Node", None, None]:
    for node in self.children.values():
      yield node

  def recurse_children_node(self) -> t.Generator["Node", None, None]:
    yield self
    for node in self.iter_children():
      if not node.is_leaf():
        yield from node.recurse_children_node()
      else:
        yield node

  def iter_parent_node(self) -> t.Generator["Node", None, None]:
    a = self
    while not a.is_root():
      yield a
      a = a.parent

  def get_child_by_name(self, name) -> "Node":
    return self.children.get(name, None)

  def get_child_by_index(self, _index) -> "Node":
    return self.get_child_by_name(list(self.children.keys())[_index])

  def repr_tree(self, repr_callback=lambda x: x.name, stop_at_depth=None):
    r = ''
    r += '□ ' if self.is_leaf() else '■ '
    r += repr_callback(self)
    r += '\n'

    if not stop_at_depth is None and self.depth > stop_at_depth - 1:
      return r

    for child in self.iter_children():
      spaces = list(
          map(lambda x: int(x.is_on_end()),
              filter(lambda y: not y.is_root() and y.name != child.name, child.iter_parent_node())
          )
      )
      for space in reversed(spaces):
        if space == 0:
          r += ' ┆   '
        else:
          r += '     '
      if child.is_on_beginning() and not child.is_root() and child.parent.nchild == 1:
        r += '└───▸'
      elif child.is_on_beginning():
        r += '└┬──▸'
      elif child.is_on_end():
        r += ' └──▸'
      else:
        r += ' ├──▸'
      r += child.repr_tree(repr_callback=repr_callback, stop_at_depth=stop_at_depth)

    return r
