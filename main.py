import traceback
from collections import namedtuple
from requests import Session
from src.argroute import ArgRoute
from src.config import Config
from src.appinfo import SteamAppInfo, sSteamAppInfoEntAddon, sSteamAppInfoEntPlugin, sSteamAppInfoEntResource
from src.utils import PathUtils, HTTPUtils

def fetch_argv():
  try:
    v = input('rsrcman > ').split()
  except EOFError:
    raise KeyboardInterrupt()
  return v

class Main:
  config_file = './conf.ini'
  download_dir = './download'
  working_dir = PathUtils.dirname(__file__)

  def __init__(self):
    self.loop = True
    self.router = ArgRoute(self)
    self.config = Config()
    self.appinfo = SteamAppInfo()
    self.session = Session()
    self.stack = list()
    
    temp_dir, temp_dir_destructor = PathUtils.mkdtemp()
    self.temp_dir = temp_dir
    self._temp_dir_destroy = temp_dir_destructor

  @staticmethod
  def confirm():
    ret = input('rsrcman >> Continue? [Y/n] ') == 'Y'
    print()
    return ret

  @staticmethod
  def filter_fields(d):
    return [i for i in d.keys() if not (i.startswith('_') or i.endswith('_')) and not isinstance(d[i], (tuple, list))]

  @classmethod
  def print_fields(cls, ent):
    d = ent.to_dict()
    fields = cls.filter_fields(d)
    print()
    print('current values:')
    for field in fields:
      print('  {} : {}'.format(field, d.get(field)))
    print()

  @classmethod
  def resolve_path(cls, path):
    return PathUtils.join(cls.working_dir, path)

  @classmethod
  def stdin_form_ent(cls, ent):
    d = ent.to_dict()
    fields = cls.filter_fields(d)
    cls.print_fields(ent)
    for field in fields:
      value = input('rsrcman >> {} : '.format(field))
      if value:
        d[field] = value
    for field, value in d.items():
      print('  {}: {}'.format(field, value))
    if cls.confirm():
      ent.from_dict(d)

  @staticmethod
  def eval_index(ns):
    signed = ns.index[0] == '-'
    if not ns.index.isnumeric() and not (signed and ns.index[1:].strip().isnumeric()):
      ns.node_.print_err('arg should be numeric: {}'.format(ns.index))
      ns.node_.print(ns.node_.repr_help())
      return
    index = int(ns.index)
    return index

  def clear_temp_dir(self):
    PathUtils.rmtree_d(self.temp_dir)

  def h_exit(self, ns):
    self.loop = False
    return

  def h_save(self, ns):
    self.save_appinfo()
    self.config.save(self.config_file)
    return

  def h_configure_appinfo(self, ns):
    self.config.info_file = ns.filepath
    self.h_edit_config(None)

  def h_configure_platform(self, ns):
    self.config.platform = ns.value

  def print_addons(self, addons, exclude_excluded=False):
    for n, ent in enumerate(addons):
      if exclude_excluded and ent.exclude:
        continue
      print('{:>02d}    | - [{}] {}'.format(n, ' ' if ent.exclude else 'x', ent.name))

  def print_plugins(self, plugins, exclude_excluded=False, with_resources=True):
    for n, ent in enumerate(plugins):
      if exclude_excluded and ent.exclude:
        continue
      print('{:>02d}    | - [{}] {}'.format(n, ' ' if ent.exclude else 'x', ent.name))
      if with_resources:
        for m, rsc in enumerate(ent.resources):
          if exclude_excluded and rsc.exclude:
            continue
          if exclude_excluded and rsc.platform != '*':
            if rsc.platform != self.config.platform:
              continue
          print('{:>02d} {:>02d} |   - [{}] ({}) {}'.format(n, m, ' ' if rsc.exclude else 'x', rsc.platform, rsc.url))

  def h_list_addons(self, ns):
    print('available addons:')
    self.print_addons(self.appinfo.addons)
    print()

  def h_list_plugins(self, ns):
    print('available plugins:')
    self.print_plugins(self.appinfo.plugins)
    print()

  def h_new_addon(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    addon = sSteamAppInfoEntAddon()
    self.stdin_form_ent(addon)
    self.appinfo.addons.append(addon)

  def h_new_plugin(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.plugins) or index < 0:
      plugin = sSteamAppInfoEntPlugin()
      self.stdin_form_ent(plugin)
      self.appinfo.plugins.append(plugin)
    else:
      plugin = self.appinfo.plugins[index]
      self.stack.append(plugin)

  def h_new_plugin_resource(self, ns):
    index = self.eval_index(ns)
    if len(self.stack) == 0:
      ns.node_.print_err('temp stack is empty')
      return
    plugin = self.stack.pop(0)
    if index >= len(plugin.resources) or index < 0:
      resource = sSteamAppInfoEntResource()
      self.stdin_form_ent(resource)
      plugin.resources.append(resource)
    else:
      resource = plugin.resources[index]
      self.stdin_form_ent(resource)

  def h_edit_config(self, ns):
    self.stdin_form_ent(self.appinfo.config)

  def h_edit_addon(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.addons):
      ns.node_.print_err('index out of bound: {}'.format(index))
      return
    addon = self.appinfo.addons[index]
    self.stdin_form_ent(addon)

  def h_edit_plugin(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.plugins):
      ns.node_.print_err('index out of bound: {}'.format(index))
    else:
      plugin = self.appinfo.plugins[index]
      self.stdin_form_ent(plugin)
      self.stack.append(plugin)

  def h_edit_plugin_resource(self, ns):
    index = self.eval_index(ns)
    if len(self.stack) == 0:
      ns.node_.print_err('temp stack is empty')
      return
    plugin = self.stack.pop(0)
    if index >= len(plugin.resources):
      ns.node_.print_err('index out of bound: {}'.format(index))
      return
    resource = plugin.resources[index]

  def h_view_config(self, ns):
    self.print_fields(self.appinfo.config)

  def h_view_addon(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.addons):
      ns.node_.print_err('index out of bound: {}'.format(index))
      return
    addon = self.appinfo.addons[index]
    self.print_fields(addon)

  def h_view_plugin(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.plugins):
      ns.node_.print_err('index out of bound: {}'.format(index))
    else:
      plugin = self.appinfo.plugins[index]
      self.stack.append(plugin)
      self.print_fields(plugin)

  def h_view_plugin_resource(self, ns):
    index = self.eval_index(ns)
    if len(self.stack) == 0:
      ns.node_.print_err('temp stack is empty')
      return
    plugin = self.stack.pop(0)
    if index >= len(plugin.resources):
      ns.node_.print_err('index out of bound: {}'.format(index))
      return
    resource = plugin.resources[index]
    self.print_fields(resource)

  def h_remove_addon(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.addons):
      ns.node_.print_err('index out of bound: {}'.format(index))
      return
    addon = self.appinfo.addons.pop(index)

  def h_remove_plugin(self, ns):
    index = self.eval_index(ns)
    if index is None:
      return
    if index >= len(self.appinfo.plugins):
      ns.node_.print_err('index out of bound: {}'.format(index))
    else:
      plugin = self.appinfo.plugins.pop(index)
      self.stack.append((index, plugin))

  def h_remove_plugin_resource(self, ns):
    index = self.eval_index(ns)
    if len(self.stack) == 0:
      ns.node_.print_err('temp stack is empty')
      return
    plugin_index, plugin = self.stack.pop(0)
    if index >= len(plugin.resources):
      ns.node_.print_err('index out of bound: {}'.format(index))
      return
    resource = plugin.resources.pop(index)
    self.appinfo.plugins.insert(plugin_index, plugin)

  def print_stats(self):
    print('using appinfo    : {}'.format(self.config.info_file))
    print('using platform   : {}'.format(self.config.platform))

  def print_appinfo_stats(self):
    print('installation dir : {}'.format(self.appinfo.config.base_dir))
    print('workshop dir     : {}'.format(self.appinfo.config.workshop_dir))

  def auto_download_file(self, url, target_path):
    status, download_path, file_info = HTTPUtils.download_file(self.session, url, self.download_dir)
    if not status and not download_path is None:
      print('destroying unfinished file')
      PathUtils.delete_file(download_path)
      return
    if file_info.content_type == 'application/zip' or file_info.file_type == 'zip':
      print('extracting zip: {}'.format(file_info.file_name))
      PathUtils.archive_extract_zip(download_path, target_path, self.temp_dir)
    elif file_info.content_type == 'application/x-xz' or file_info.file_type.startswith('tar'):
      print('extracting {}: {}'.format(file_info.file_type, file_info.file_name))
      PathUtils.archive_extract_tar(download_path, target_path, self.temp_dir)
    else:
      print('copying file: {}'.format(file_info.file_name))
      PathUtils.copy2(download_path, PathUtils.join(target_path, file_info.file_name))
    self.clear_temp_dir()

  def auto_download_addon(self, value, need_confirm=True):
    workshop_ids = HTTPUtils.parse_workshop_ids(value)
    if workshop_ids is None or len(workshop_ids) == 0:
      print('failed to parse workshop id')
      return
    print('found workshop ids:')
    for workshop_id in workshop_ids:
      print('  - {}'.format(workshop_id))
    if need_confirm and not self.confirm():
      return
    for workshop_id in workshop_ids:
      HTTPUtils.download_steam_workshop(self.session, self.resolve_path(self.appinfo.config.workshop_dir), workshop_id)

  def h_install(self, ns):
    print()
    print('installing all')
    self.print_stats()
    self.print_appinfo_stats()
    print()
    print('selected plugins:')
    self.print_plugins(self.appinfo.plugins, exclude_excluded=True, with_resources=False)
    print()
    print('selected addons:')
    self.print_addons(self.appinfo.addons, exclude_excluded=True)
    print()
    if not self.confirm():
      return
    for plugin in self.appinfo.plugins:
      if plugin.exclude:
        print('skipping plugin {}'.format(plugin.name))
        continue
      print('installing plugin {}'.format(plugin.name))
      for resource in plugin.resources:
        if resource.exclude:
          print('skipping plugin resource {}'.format(resource.url))
          continue
        if resource.platform != '*':
          if resource.platform != self.config.platform:
            print('skipping plugin resource {}'.format(resource.url))
            continue
        print('downloading plugin resource {}'.format(resource.url))
        url = resource.url
        target_path = resource.target_path
        target_path = PathUtils.join(self.resolve_path(self.appinfo.config.base_dir), target_path)
        self.auto_download_file(url, target_path)

    for addon in self.appinfo.addons:
      if addon.exclude:
        print('skipping addon {}'.format(addon.name))
        continue
      self.auto_download_addon(addon.url, need_confirm=False)

  def h_install_workshop(self, ns):
    print()
    print('installing workshop {}'.format(ns.value))
    self.print_stats()
    self.print_appinfo_stats()
    print()
    self.auto_download_addon(ns.value)

  def boot_router(self):
    ns_index = namedtuple('Index', ['node_', 'index'])
    ns_filepath = namedtuple('FilePath', ['node_', 'filepath'])
    ns_value = namedtuple('Value', ['node_', 'value'])

    r_0     = self.router.register('configure')
    r_0_0   = self.router.register('appinfo', r_0).set_namespace(ns_filepath).set_hook(self.h_configure_appinfo)
    r_0_1   = self.router.register('platform', r_0).set_namespace(ns_value).set_hook(self.h_configure_platform)

    r_1     = self.router.register('list')
    r_1_1   = self.router.register('addons', r_1).set_hook(self.h_list_addons)
    r_1_2   = self.router.register('plugins', r_1).set_hook(self.h_list_plugins)

    r_2     = self.router.register('new')
    r_2_0   = self.router.register('addon', r_2).set_namespace(ns_index).set_hook(self.h_new_addon)
    r_2_1   = self.router.register('plugin', r_2).set_namespace(ns_index).set_hook(self.h_new_plugin)
    r_2_1_0 = self.router.register('resource', r_2_1).set_namespace(ns_index).set_optional().set_hook(self.h_new_plugin_resource)

    r_3     = self.router.register('edit')
    r_3_0   = self.router.register('config', r_3).set_hook(self.h_edit_config)
    r_3_1   = self.router.register('addon', r_3).set_namespace(ns_index).set_hook(self.h_edit_addon)
    r_3_2   = self.router.register('plugin', r_3).set_namespace(ns_index).set_hook(self.h_edit_plugin)
    r_3_2_0 = self.router.register('resource', r_3_2).set_namespace(ns_index).set_optional().set_hook(self.h_edit_plugin_resource)

    r_4     = self.router.register('view')
    r_4_0   = self.router.register('config', r_4).set_hook(self.h_view_config)
    r_4_1   = self.router.register('addon', r_4).set_namespace(ns_index).set_hook(self.h_view_addon)
    r_4_2   = self.router.register('plugin', r_4).set_namespace(ns_index).set_hook(self.h_view_plugin)
    r_4_2_0 = self.router.register('resource', r_4_2).set_namespace(ns_index).set_optional().set_hook(self.h_view_plugin_resource)

    r_5     = self.router.register('remove')
    r_5_0   = self.router.register('addon', r_5).set_namespace(ns_index).set_hook(self.h_remove_addon)
    r_5_1   = self.router.register('plugin', r_5).set_namespace(ns_index).set_hook(self.h_remove_plugin)
    r_5_1_0 = self.router.register('resource', r_5_1).set_namespace(ns_index).set_optional().set_hook(self.h_remove_plugin_resource)

    r_6     = self.router.register('save').set_hook(self.h_save)
    r_7     = self.router.register('install').set_hook(self.h_install)
    r_8     = self.router.register('installworkshop').set_namespace(ns_value).set_hook(self.h_install_workshop)
    r_9     = self.router.register('exit').set_hook(self.h_exit)

    print(self.router.root.repr_tree(str))
    return

  def boot_config(self):
    self.config.load(self.config_file)
    return

  def boot_sess(self):
    self.session.headers.update({
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    })

  def boot_dirs(self):
    PathUtils.ensure_dir(self.download_dir)

  def load_appinfo(self):
    import json
    invoke_edit_config = False
    if self.config.info_file is None:
      self.config.info_file = 'appinfo.json'
      invoke_edit_config = True
    with open(self.config.info_file, 'r') as fh:
      self.appinfo.from_dict(json.load(fh))
    if invoke_edit_config:
      self.h_edit_config(None)

  def save_appinfo(self):
    import json
    if self.config.info_file is None:
      self.config.info_file = 'appinfo.json'
    with open(self.config.info_file, 'w') as fh:
      json.dump(self.appinfo.to_dict(), fh, indent=2)

  def run(self):
    self.boot_config()
    self.boot_router()
    self.boot_sess()
    self.boot_dirs()
    self.load_appinfo()
    while self.loop:
      argv = fetch_argv()
      self.router.route_argv(argv)
      self.stack.clear()
      self.save_appinfo()

  def exit(self):
    self.save_appinfo()
    self.config.save(self.config_file)
    self.stack.clear()
    self.session.close()
    self._temp_dir_destroy()

if __name__ == '__main__':
  main = Main()
  try:
    main.run()
  except KeyboardInterrupt:
    print('interrupt: KeyboardInterrupt')
  except Exception as e:
    print(traceback.format_exc())

  try:
    print('exiting app...')
    main.exit()
  except Exception as e:
    print(traceback.format_exc())
