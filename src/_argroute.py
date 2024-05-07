from functools import wraps
from src.node import Node





class ArgNode(Node):
  def __init__(self, name, parent=None):
    super().__init__(name=name, parent=parent)
    self._router: 'ArgRoute' = None
    self._arg_repr = ''
    self._hook = lambda prog, node, arg: print('hook is not set: {} | {} | {} | {}'.format(prog, node.name, arg, node.parent))

  @property
  def router(self):
    return self._router

  @property
  def arg_repr(self):
    return self._arg_repr

  def set_router(self, router):
    self._router = router
    return self

  def set_arg_repr(self, arg_repr):
    self._arg_repr = str(arg_repr)
    return self

  @property
  def hook(self):
    return self._hook

  def set_hook(self, fn):
    self._hook = fn

  def has_command(self, name):
    return name in self.children

  def get_command_node(self, name):
    return self.get_child_by_name(name)

  def get_command_node_opt(self):
    return self.get_command_node(self.router.DEFAULT_OPT)
  
  def get_command_node_help(self):
    return self.get_command_node(self.router.DEFAULT_HELP)

  def invoke(self, argv):
    if len(argv) == 0:
      if self.has_command(self.router.DEFAULT_OPT):
        node = self.get_command_node_opt()
        return node.hook(self.router.prog, node, None)
      else:
        node = self.get_command_node_help()
        return node.hook(self.router.prog, node, None)
    arg = argv.pop(0)
    if self.has_command(self.router.DEFAULT_OPT):
      print('opt invoked {}'.format(arg))
      node = self.get_command_node_opt()
      return node.hook(self.router.prog, node, arg)
    elif arg in self.children:
      print('children invoked: {}'.format(arg))
      return self.get_command_node(arg).invoke(argv)
    elif not self.has_command(self.router.DEFAULT_OPT):
      print('hook invoked {}'.format(arg))
      self.hook(self.router.prog, self, arg)
    else:
      print('help invoked {}'.format(arg))
      node = self.get_command_node_help()
      return node.hook(self.router.prog, node, arg)



    # elif self.router.DEFAULT_OPT in self.children and len(argv) > 0:
    #   return self.get_child_by_name(self.router.DEFAULT_OPT).invoke(argv)
    # elif self.router.DEFAULT_HELP in self.children:
    #   return self.get_child_by_name(self.router.DEFAULT_HELP).invoke(argv)


class ArgRoute:
  
  DEFAULT_ROOT = '_root_'
  DEFAULT_OPT = '_opt_'
  DEFAULT_HELP = '_help_'

  def __init__(self, prog):
    self._root = ArgNode(self.DEFAULT_ROOT)
    self._prog = prog
    self._hook = None
    self._root.set_router(self)
    self.register_command(self.DEFAULT_HELP, self._root)

  @classmethod
  def repr_help(cls, node):
    child_names = [i.name for i in node.iter_children() if not i.name.startswith("_")]
    is_opt = False
    if not node.parent is None:
      is_opt = not node.get_child_by_name(cls.DEFAULT_OPT) is None
    r = node.name
    if len(child_names) > 0:
      r += ' '
      r += '[' if is_opt else '('
      r += '' if is_opt else ' '
      r += ' | '.join(child_names)
      r += '' if is_opt else ' '
      r += ']' if is_opt else ')'
    r += (' ' + node.arg_repr) if node.arg_repr else ''
    return r

  @property
  def prog(self):
    return self._prog

  @property
  def root(self):
    return self._root

  def register_command(self, command, parent=None):
    if parent is None:
      parent = self.root
    command = str(command)
    node = parent.spawn_child(command)
    node.set_router(self)
    if command != self.DEFAULT_HELP and command != 'help':
      self.register_command(self.DEFAULT_HELP, node)
    return node

  def register_optional(self, parent):
    return self.register_command(self.DEFAULT_OPT, parent)