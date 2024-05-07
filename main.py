import traceback
from src.argroute import ArgRoute
from collections import namedtuple

def fetch_argv():
  try:
    v = input('> ').split()
  except EOFError:
    raise KeyboardInterrupt()
  return v

class Main:

  def __init__(self):
    self.loop = True
    self.router = ArgRoute(self)

  def h_exit(self, *args, **kwargs):
    self.loop = False

  def boot(self):
    ns_index = namedtuple('Index', ['index'])
    ns_filepath = namedtuple('FilePath', ['filepath'])
    ns_value = namedtuple('Value', ['value'])

    r_0     = self.router.register('configure')
    r_0_0   = self.router.register('appinfo', r_0).set_namespace(ns_filepath)
    r_0_1   = self.router.register('platform', r_0).set_namespace(ns_value)
    r_1     = self.router.register('list')
    r_1_1   = self.router.register('addons', r_1)
    r_1_2   = self.router.register('plugins', r_1)
    r_2     = self.router.register('new')
    r_2_0   = self.router.register('addon', r_2).set_namespace(ns_index)
    r_2_1   = self.router.register('plugin', r_2).set_namespace(ns_index)
    r_2_1_0 = self.router.register('resource', r_2_1).set_namespace(ns_index).set_optional()
    r_3     = self.router.register('edit')
    r_3_0   = self.router.register('addon', r_3).set_namespace(ns_index)
    r_3_1   = self.router.register('plugin', r_3).set_namespace(ns_index)
    r_3_1_0 = self.router.register('resource', r_3_1).set_namespace(ns_index).set_optional()
    r_5     = self.router.register('view')
    r_5_0   = self.router.register('addon', r_5).set_namespace(ns_index)
    r_5_1   = self.router.register('plugin', r_5).set_namespace(ns_index)
    r_5_1_0 = self.router.register('resource', r_5_1).set_namespace(ns_index).set_optional()
    r_6     = self.router.register('save')
    r_7     = self.router.register('install')
    r_8     = self.router.register('exit')

    print(self.router.root.repr_tree(str))

    r_8.set_hook(self.h_exit)
    # print(list(self.router.root.get_child_by_name('list').iter_children()))
    # print(list(self.router.root.get_child_by_name('list').children.get(self.router.DEFAULT_OPT)))
    # print(self.router.root.get_child_by_name('list').get_child_by_name(self.router.DEFAULT_OPT))

    return


  def run(self):
    self.boot()
    while self.loop:
      argv = fetch_argv()
      self.router.root.invoke(argv)
      print()
  def exit(self):
    pass



if __name__ == '__main__':
  main = Main()
  try:
    main.run()
  except KeyboardInterrupt:
    print('KeyboardInterrupt')
  except Exception as e:
    print(traceback.format_exc())

  try:
    main.exit()
  except Exception as e:
    print(traceback.format_exc())
