# design specification
# command routing
# 
#        <command>
# child  <command> <command> arg
# chain  <command> arg <command>
# chain  <command> arg <command> arg
# 
# fragment <command> <none>
# fragment <command> <opt>
# fragment <command> <arg>

from collections import namedtuple
from functools import wraps
from itertools import chain
from src.node import Node
from src.baseclass import PrintMethods

class ArgNode(Node, PrintMethods):

  def __init__(self, name, parent=None):
    super().__init__(name, parent)
    self._router: 'ArgRouter'  = None
    self._namespace = namedtuple('DefaultArgNamespace', ['node_'])
    self._hook = self._default_hook
    self._f_optional = False

  def _print_pads(self):
    print('\t' * self.depth, end='')

  def _default_hook(self, *args, **kwargs):
    # print(f'{self._hook.__name__}@"{self.name}", {args=}, {kwargs=}')
    return

  def has_namespace(self):
    return not self._namespace is None and \
      hasattr(self._namespace, '_fields')

  @property
  def router(self):
    return self._router

  @property
  def hook(self):
    return self._hook

  @property
  def fields(self):
    if not self.has_namespace():
      print(self, 'no fields')
      return [self]
    return tuple([i for i in self._namespace._fields if not i.endswith('_')])

  @property
  def field_count(self):
    return len(self.fields)

  @property
  def accepts_args(self):
    return self.field_count > 0

  def is_optional(self):
    return self._f_optional

  def child_is_optional(self):
    if self.is_leaf():
      return False
    return all(map(lambda x: x.is_optional(), self.iter_children()))

  def set_namespace(self, namespace):
    self._namespace = namespace
    return self

  def set_hook(self, fn):
    self._hook = fn
    return self

  def set_optional(self):
    self._f_optional = True
    return self

  def repr_help(self):
    return 'usage: {}'.format(self)

  def invoke(self, argv):
    if self.accepts_args:
      if len(argv) >= self.field_count:
        args, argv = argv[:self.field_count], argv[self.field_count:]
        arg_namespace = self._namespace(self, *args)
        _ = self._hook(arg_namespace)
      else:
        # raise error
        self.print_err('"{}" command requires args'.format(self.name))
        self.print(self.repr_help())
    else:
      _ = self._hook(None)

    if self.is_leaf():
      return

    if len(argv) == 0:
      if not self.child_is_optional():
        self.print_err('"{}" command requires args'.format(self.name))
        self.print(self.repr_help())
        return
      else:
        return

    arg = argv.pop(0)

    if self.has(arg):
      node = self.get_child_by_name(arg)
      node.invoke(argv)
    else:
      self.print_err('args did not match: {}'.format(arg))
      self.print(self.repr_help())
    return

  def __repr__(self):
    r = ''
    if self.is_optional():
      r += '['
    r += self.name
    if self.accepts_args:
      r += ' '
      r += '<' + '> <'.join(self.fields) + '>'
    if self.is_optional():
      r += ']'
    return r

class ArgRoute:
  ar_n_root = '_root_'
  ar_n_help = '_leaf_help_'

  def __init__(self, prog):
    self._root: ArgNode = ArgNode(self.ar_n_root)
    self._prog = prog
    self._root._router = self

  @property
  def root(self):
    return self._root

  @property
  def prog(self):
    return self._prog

  def register(self, name, parent=None):
    if parent is None:
      parent = self.root
    arg_node = parent.spawn_child(name)
    # print('registered {} <- {}'.format(arg_node, parent))
    return arg_node

  def route_argv(self, argv):
    root = self._root
    while not root.is_root():
      root = root.parent
    root.invoke(argv)

