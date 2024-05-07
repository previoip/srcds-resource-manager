import traceback
import json
from functools import wraps
from src.config import Config
from src.structs import *
from src.logger import init_logger
from src.utils import PathUtils

logger = init_logger('main')

class SteamAppResourceManager:

  def __init__(self):
    self._info = TSteamAppInfo()

  @property
  def info(self):
    return self._info

  def save(self, path):
    with open(path, 'w') as fh:
      json.dump(self._info.to_dict(), fh, indent=2)

  def load(self, path):
    is_new = not PathUtils.isfile(path) or PathUtils.stat(path).st_size == 0
    if is_new:
      print('saving new steamapp info: {}'.format(path))
      self.prompt_assign_ent_attr(self._info.config)
      self.save(path)
    else:
      with open(path, 'r') as fh:
        obj = json.load(fh)
        self._info.from_dict(obj)

  def list_ent_attr(self, attr, ent_ls):
    return [getattr(i, attr) for i in ent_ls]

  def list_ent_names(self, ent_ls):
    return self.list_ent_attr('name', ent_ls)

  def get_plugin_index_by_name(self, name):
    plugin_names = self.list_ent_names(self._info.plugins)
    if name in plugin_names:
      return plugin_names.index(name)
    return None

  def get_plugin_by_name(self, name):
    i = self.get_plugin_index_by_name(name)
    if i is None:
      return None
    return self._info.plugins[i]

  def new_entity_plugin(self):
    plugin = TSteamAppInfoEntPlugin()
    self._info.plugins.append(plugin)
    return plugin

  def get_addon_index_by_name(self, name):
    addon_names = self.list_ent_names(self._info.addons)
    if name in addon_names:
      return addon_names.index(name)
    return None

  def get_addon_by_name(self, name):
    i = self.get_addon_index_by_name(name)
    if i is None:
      return None
    return self._info.addons[i]

  def new_entity_addon(self):
    addon = TSteamAppInfoEntAddon()
    self._info.addons.append(addon)
    return addon

  @classmethod
  def recurse_prop(cls, ent, func, lv=0):
    for key, val in ent.to_dict().items():
      yield func(ent, key, val, lv)
      if isinstance(val, list):
        for child_ent in val:
          if not isinstance(child_ent, TSteamAppInfoEntity):
            continue
          yield from cls.recurse_prop(child_ent, func, lv=lv+1)

  @staticmethod
  def map_prop(ent: TSteamAppInfoEntity, func):
    for key, val in ent.to_dict().items():
      yield func(ent, key, val)

  @classmethod
  def repr_ent(cls, ent):
    def _repr(ent, key, val):
      if key.startswith('_'):
        return
      print('    "{}": {}'.format(key, val))
    for _ in cls.map_prop(ent, _repr):
      pass
    return

  def prompt_assign_ent_attr(self, ent):
    def assigner(ent, key, val):
      if key.startswith('_'):
        return
      attr_t = type(val)
      if not attr_t in (int, str, bool, float):
        return
      new_val = input('  >> set "{}": '.format(key))
      if not new_val:
        return
      try:
        if attr_t in (int, bool) and new_val.isnumeric():
          new_val = int(new_val)
        new_val = attr_t(new_val)
      except TypeError as e:
        print('error assigning name, expected type: {}'.format(attr_t))
        return
      setattr(ent, key, new_val)
    print('  current values:')
    self.repr_ent(ent)
    print()
    yield from self.map_prop(ent, assigner)
    print('  properties set for {}'.format(ent.name))
    print()


class Main:
  def __init__(self, print=print):
    self.print = print
    self.manager = SteamAppResourceManager()
    self.config = Config()
    self.config_path = 'conf.ini'

  def _fetch_argv(self):
    try:
      v = input('> ').split()
    except EOFError:
      raise KeyboardInterrupt()
    return v

  def invoke_confirm(self, msg='continue?'):
    self.print()
    while True:
      res = input('  >> {} [Y/n] '.format(msg))
      if res:
        break
    return res == 'Y'

  @staticmethod
  def _validate_arg(validator):
    def _deco(func):
      @wraps(func)
      def w_func(self, *args, **kwargs):
        if not validator(self, *args, **kwargs):
          return
        return func(self, *args, **kwargs)
      return w_func
    return _deco

  def _validator_argc(*callbacks):
    def _v(self, argv):
      isvalid = len(argv) > 0
      if not isvalid:
        for callback in callbacks:
          callback(self)
      return isvalid
    return _v

  def boot(self):
    self.print('loading config: {}'.format(self.config_path))
    self.config.load(self.config_path)
    if self.config.info_file is None:
      self.config.info_file = 'sample.json'
    print(self.config.info_file)
    self.r_configure_info([self.config.info_file])
    self.r_help([])

  def run(self):
    self.boot()
    while True:
      argv = self._fetch_argv()
      if len(argv) == 0:
        continue
      command = argv.pop(0)
      if command == 'exit':
        break
      elif command == 'help':
        self.r_help(argv)
      elif command == 'configure':
        self.r_configure(argv)
      elif command == 'list':
        self.r_list(argv)
      elif command == 'save':
        self.r_save_info(argv)
      elif command == 'new':
        self.r_new(argv)
      elif command == 'edit':
        self.r_edit(argv)
      elif command == 'view':
        self.r_view(argv)
      elif command == 'install':
        self.r_install(argv)
      else:
        self.print('invalid argument: {}'.format(command))
    return

  def hmsg_blank(self):
    self.print()
    return

  def hmsg_usage(self):
    self.print('usage:')
    return

  def hmsg_detail(self):
    self.print('detailed usage:')
    return

  def hmsg_warn_arg_empty(self):
    self.print('invalid args: command requires argument(s)')
    return

  def hmsg_help_save(self):
    self.print('    save')
    return

  def hmsg_help_configure(self):
    self.print('    configure\t[appinfo, platform] <value>')
    return

  def hmsg_help_configure_info(self):
    self.print('    configure\tappinfo <path-to-json>')
    return

  def hmsg_help_configure_platform(self):
    self.print('    configure\tplatform [windows,linux,darwin]')
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_configure,
    hmsg_blank,
    hmsg_detail,
    hmsg_help_configure_info,
    hmsg_help_configure_platform,
    hmsg_blank
  ))
  def r_configure(self, argv):
    param = argv.pop(0)
    if param == 'appinfo':
      self.r_configure_info(argv)
    elif param == 'platform':
      self.r_configure_platform(argv)
    else:
      self.print('unknown param: {}'.format(param))
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_configure_info
  ))
  def r_configure_info(self, argv):
    self.config.info_file = argv[0]
    self.print('using appinfo: {}'.format(self.config.info_file))
    self.manager.load(self.config.info_file)
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_configure_platform
  ))
  def r_configure_platform(self, argv):
    self.config.platform = argv[0]
    self.print('using platform: {}'.format(self.config.platform))
    return

  def r_save_info(self, argv):
    self.manager.save(self.config.info_file)
    self.print('saved appinfo: {}'.format(self.config.info_file))
    return

  def hmsg_help_new(self):
    self.print('    new \t[plugin, addon]')

  def hmsg_help_new_plugin(self):
    self.print('    new \tplugin')

  def hmsg_help_new_addon(self):
    self.print('    new \taddon')

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_new,
    hmsg_detail,
    hmsg_help_new_plugin,
    hmsg_help_new_addon
  ))
  def r_new(self, argv):
    param = argv.pop(0)
    if param == 'plugin':
      self.r_new_plugin(argv)
    elif param == 'addon':
      self.r_new_addon(argv)
    else:
      self.print('unknown param: {}'.format(param))
    return

  def r_new_plugin(self, argv):
    if not self.invoke_confirm('create new plugin entry?'):
      return
    plugin_ent = self.manager.new_entity_plugin()
    for _ in self.manager.prompt_assign_ent_attr(plugin_ent):
      pass
    return

  def r_new_addon(self, argv):
    if not self.invoke_confirm('create new addon entry?'):
      return
    addon_ent = self.manager.new_entity_addon()
    for _ in self.manager.prompt_assign_ent_attr(addon_ent):
      pass

  def hmsg_help_edit(self):
    self.print('    edit\t[plugin, addon] <index>')

  def hmsg_help_edit_plugin(self):
    self.print('    edit\tplugin <index>')

  def hmsg_help_edit_addon(self):
    self.print('    edit\taddon <index>')

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_edit,
    hmsg_detail,
    hmsg_help_edit_addon,
    hmsg_help_edit_plugin
  ))
  def r_edit(self, argv):
    param = argv.pop(0)
    if param == 'plugin':
      self.r_edit_plugin(argv)
    elif param == 'addon':
      self.r_edit_addon(argv)
    else:
      self.print('unknown param: {}'.format(param))
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_edit_plugin
  ))
  def r_edit_plugin(self, argv):
    param = argv.pop(0)
    if not param.isnumeric():
      self.print('argument needs to be integer')
    param = int(param) - 1
    if param >= len(self.manager.info.plugins) or param < 0:
      self.print('index out of bound: {}'.format(param+1))
      return
    ent = self.manager.info.plugins[param]
    for _ in self.manager.prompt_assign_ent_attr(ent):
      pass
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_edit_addon
  ))
  def r_edit_addon(self, argv):
    param = argv.pop(0)
    if not param.isnumeric():
      self.print('argument needs to be integer')
    param = int(param) - 1
    if param >= len(self.manager.info.addons) or param < 0:
      self.print('index out of bound: {}'.format(param+1))
      return
    ent = self.manager.info.addons[param]
    for _ in self.manager.prompt_assign_ent_attr(ent):
      pass
    return

  def hmsg_help_view(self):
    self.print('    view\t[plugin, addon] <index>')

  def hmsg_help_view_plugin(self):
    self.print('    view\tplugin <index>')

  def hmsg_help_view_addon(self):
    self.print('    view\taddon <index>')

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_view,
    hmsg_detail,
    hmsg_help_view_addon,
    hmsg_help_view_plugin
  ))
  def r_view(self, argv):
    param = argv.pop(0)
    if param == 'plugin':
      self.r_view_plugin(argv)
    elif param == 'addon':
      self.r_view_addon(argv)
    else:
      self.print('unknown param: {}'.format(param))
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_view_plugin
  ))
  def r_view_plugin(self, argv):
    param = argv.pop(0)
    if not param.isnumeric():
      self.print('argument needs to be integer')
    param = int(param) - 1
    if param >= len(self.manager.info.plugins) or param < 0:
      self.print('index out of bound: {}'.format(param+1))
      return
    ent = self.manager.info.plugins[param]
    self.manager.repr_ent(ent)
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank,
    hmsg_usage,
    hmsg_help_view_addon
  ))
  def r_view_addon(self, argv):
    param = argv.pop(0)
    if not param.isnumeric():
      self.print('argument needs to be integer')
    param = int(param) - 1
    if param >= len(self.manager.info.addons) or param < 0:
      self.print('index out of bound: {}'.format(param+1))
      return
    ent = self.manager.info.addons[param]
    self.manager.repr_ent(ent)
    return

  @_validate_arg(_validator_argc(
    hmsg_warn_arg_empty,
    hmsg_blank
  ))
  def r_install(self, argv):
    param = argv.pop(0)
    if param == 'all' or param == '*':
      ...
    ...
    return

  def hmsg_help_list(self):
    self.print('    list\t[plugins,addons,]')

  def r_list(self, argv):
    self.hmsg_blank()
    def repr_ent(self, i, ent):
      ent_exclude = '[ ]' if ent.exclude else '[o]'
      self.print('      {} {:>2d}. {}'.format(ent_exclude, i+1, ent.name))
    show_fl = 0
    if len(argv) == 0:
      show_fl = 3
    elif argv[0] == 'plugins':
      show_fl = 1
    elif argv[0] == 'addons':
      show_fl = 2
    else:
      self.hmsg_usage()
      self.hmsg_help_list()
      self.hmsg_blank()
      return
    if show_fl & 2:
      self.print('    available addons:')
      for i, ent in enumerate(self.manager.info.addons):
        repr_ent(self, i, ent)
      self.hmsg_blank()
    if show_fl & 1:
      self.print('    available plugins:')
      for i, ent in enumerate(self.manager.info.plugins):
        repr_ent(self, i, ent)
      self.hmsg_blank()

  def r_help(self, argv):
    if len(argv) == 0:
      self.print(' scds resource manager '.center(45, '-'))
      self.print('  available commands:')
      self.print('    help')
      self.hmsg_help_configure()
      self.hmsg_help_list()
      self.hmsg_help_new()
      self.hmsg_help_edit()
      self.hmsg_help_view()
      self.hmsg_help_save()
      self.print('    exit\tor Ctrl-C to exit')
      self.print(''.center(45, '-'))
      return
    command = argv.pop(0)
    ...
    return

  def exit(self):
    self.config.save(self.config_path)
    self.r_save_info([])
    self.print('exiting program')
    return


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
