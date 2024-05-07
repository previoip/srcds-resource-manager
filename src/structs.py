import typing as t
from hashlib import sha1

class TSteamAppInfoEntity:

  @staticmethod
  def hash(v):
    return sha1(bytes(str(v), encoding='utf8'), usedforsecurity=False).hexdigest()

  def __init__(self):
    self._uid: str = ''
    self._name: str = str(id(self))
    self.exclude: bool = False
    self._update_uid()

  def _update_uid(self):
    self._uid: str = self.hash(self._name)

  @property
  def name(self):
    return self._name

  @name.setter
  def name(self, v):
    self._name = str(v)
    self._update_uid()

  def to_dict(self) -> dict:
    raise NotImplementedError()

  def from_dict(self, d: t.Dict):
    raise NotImplementedError()
    return self


class TSteamAppInfoEntConfig(TSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.appid: str = ''
    self.appid_ds: str = ''
    self.base_dir: str = ''

  def to_dict(self) -> dict:
    return {
      'name': self.name,
      'appId': self.appid,
      'appIdDedicatedServer': self.appid_ds,
      'baseDir': self.base_dir,
      '_id': self._uid
    }

  def from_dict(self, d: t.Dict):
    self.name = d.get('name')
    self.appid = d.get('appId')
    self.appid_ds = d.get('appIdDedicatedServer')
    self.base_dir = d.get('baseDir')
    self._uid = d.get('_id')
    return self


class TSteamAppInfoEntResource(TSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.platform: str = ''
    self.url: str = ''
    self.rel: str = ''
    self.target_path: str = ''

  def to_dict(self) -> dict:
    return {
      'name': self.name,
      'exclude': self.exclude,
      'platform': self.platform,
      'url': self.url,
      'rel': self.rel,
      'targetPath': self.target_path,
      '_id': self._uid
    }

  def from_dict(self, d: t.Dict):
    self.exclude = d.get('exclude')
    self.name = d.get('name')
    self.rel = d.get('rel')
    self.platform = d.get('platform')
    self.url = d.get('url')
    self.target_path = d.get('targetPath')
    self._uid = d.get('_id')
    return self

  @property
  def url(self):
    return self._url

  @url.setter
  def url(self, v):
    self._url = str(v)
    self._update_uid()

  def _update_uid(self):
    self._uid: str = self.hash(self._url)

class TSteamAppInfoEntPlugin(TSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.rel: str = ''
    self.resources: list[TSteamAppInfoEntResource] = []

  def to_dict(self) -> dict:
    return {
      'name': self.name,
      'exclude': self.exclude,
      'rel': self.rel,
      'resources': [i.to_dict() for i in self.resources],
      '_id': self._uid
    }

  def from_dict(self, d: t.Dict):
    self.exclude = d.get('exclude')
    self.name = d.get('name')
    self.rel = d.get('rel')
    self.resources = [TSteamAppInfoEntResource().from_dict(i) for i in d.get('resources')]
    self._uid = d.get('_id')
    return self


class TSteamAppInfoEntAddon(TSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.type: str = 'workshop'
    self.url: str = ''

  def to_dict(self) -> dict:
    return {
      'name': self.name,
      'exclude': self.exclude,
      'type': self.type,
      'url': self.url,
      '_id': self._uid
    }

  def from_dict(self, d: t.Dict):
    self.exclude = d.get('exclude')
    self.type = d.get('type')
    self.name = d.get('name')
    self.url = d.get('url')
    self._uid = d.get('_id')
    return self


class TSteamAppInfo:
  def __init__(self):
    self.config: TSteamAppInfoEntConfig = TSteamAppInfoEntConfig() 
    self.meta_plugins: list[TSteamAppInfoEntPlugin] = []
    self.plugins: list[TSteamAppInfoEntPlugin] = []
    self.addons: list[TSteamAppInfoEntAddon] = []

  def to_dict(self) -> dict:
    return {
      'config': self.config.to_dict(),
      'metaPlugins': [i.to_dict() for i in self.meta_plugins],
      'plugins': [i.to_dict() for i in self.plugins],
      'addons': [i.to_dict() for i in self.addons],
    }

  def from_dict(self, d: t.Dict):
    self.config.from_dict(d.get('config'))
    self.meta_plugins = [TSteamAppInfoEntPlugin().from_dict(i) for i in d.get('metaPlugins')]
    self.plugins = [TSteamAppInfoEntPlugin().from_dict(i) for i in d.get('plugins')]
    self.addons = [TSteamAppInfoEntAddon().from_dict(i) for i in d.get('addons')]
    return self
