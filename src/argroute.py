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
from src.node import Node
from functools import wraps

class ArgNamespace:
  def __init__(self, name, field_names, types):
    self._field_names = field_names
    self._namespace = namedtuple(name, field_names)
    self._types = types

  def to_namedtuple(self):
    @wraps(self._namespace)
    def wrapped(*args, **kwargs):
      for i, type_cast in enumerate(self._types):
        args[i] = type_cast(args[i])
      ret = self._namespace(*args, **kwargs)
      return ret

  @property
  def _fields(self):
    return tuple(self._field_names)

class ArgNode(Node):

  def _print_pads(self):
    print('\t' * self.depth, end='')

  def _default_hook(self, *args, **kwargs):
    print(f'hook@"{self.name}", {args=}, {kwargs=}')
    return True

  def __init__(self, name, parent=None):
    super().__init__(name, parent)
    self._router: 'ArgRouter'  = None
    self._namespace = namedtuple('DefaultArgNamespace', [])
    self._hook = self._default_hook
    self._f_optional = False

  @property
  def router(self):
    return self._router

  def has_namespace(self):
    return not self._namespace is None and \
      hasattr(self._namespace, '_fields')

  @property
  def fields(self):
    if not self.has_namespace():
      print(self, 'no fields')
      return []
    return tuple(self._namespace._fields)

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

  def print_err(self, *msg):
    print('"{}":'.format(self.name), *msg)

  def invoke(self, argv):
    if self.accepts_args:
      if len(argv) >= self.field_count:
        args, argv = argv[:self.field_count], argv[self.field_count:]
        arg_namespace = self._namespace(*args)
        prevent_early_return = self._hook(arg_namespace)
      else:
        # raise error
        self.print_err('command requires arguments')
    else:
      prevent_early_return = self._hook(None)

    if self.is_leaf():
      return

    if len(argv) == 0:
      if not self.child_is_optional():
        self.print_err('command requires args')
        return
      else:
        return

    arg = argv.pop(0)

    if self.has(arg):
      node = self.get_child_by_name(arg)
      node.invoke(argv)
    else:
      self.print_err('args did not match: {}'.format(arg))
    return

  def __repr__(self):
    r = self.name
    if self.accepts_args:
      r += ' '
      r += '<' + '> <'.join(self.fields) + '>'
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
    print('registered {} <= {}'.format(arg_node, parent))
    return arg_node

