import typing as t
from hashlib import sha1

class sSteamAppInfoEntity:

  @staticmethod
  def hash(v):
    return sha1(bytes(str(v), encoding='utf8'), usedforsecurity=False).hexdigest()

  def __init__(self):
    self._uid: str = ''
    self._name: str = str(id(self))
    self._exclude: bool = False
    self._update_uid()


  @property
  def exclude(self):
    return self._exclude

  @exclude.setter
  def exclude(self, v):
    if isinstance(v, str):
      try:
        v = eval(v)
      except Exception as e:
        print('invalid boolean value: {}'.format(v))
        v = True
    self._exclude = bool(v)

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


class sSteamAppInfoEntConfig(sSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.appid: str = ''
    self.appid_ds: str = ''
    self.base_dir: str = ''
    self.workshop_dir: str = ''

  def to_dict(self) -> dict:
    self._update_uid()
    return {
      '_id': self._uid,
      'name': self.name,
      'appId': self.appid,
      'appIdDedicatedServer': self.appid_ds,
      'baseDir': self.base_dir,
      'workshopDir': self.workshop_dir,
    }

  def from_dict(self, d: t.Dict):
    self.name = d.get('name')
    self.appid = d.get('appId')
    self.appid_ds = d.get('appIdDedicatedServer')
    self.base_dir = d.get('baseDir')
    self.workshop_dir = d.get('workshopDir')
    # self._uid = d.get('_id')
    self._update_uid()
    return self


class sSteamAppInfoEntResource(sSteamAppInfoEntity):
  def __init__(self):
    self._url: str = ''
    super().__init__()
    self.platform: str = ''
    self.rel: str = ''
    self.target_path: str = ''

  def to_dict(self) -> dict:
    self._update_uid()
    return {
      '_id': self._uid,
      'name': self.name,
      'exclude': self.exclude,
      'platform': self.platform,
      'url': self.url,
      'rel': self.rel,
      'targetPath': self.target_path,
    }

  def from_dict(self, d: t.Dict):
    self.exclude = d.get('exclude')
    self.name = d.get('name')
    self.rel = d.get('rel')
    self.platform = d.get('platform')
    self.url = d.get('url')
    self.target_path = d.get('targetPath')
    # self._uid = d.get('_id')
    self._update_uid()
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

class sSteamAppInfoEntPlugin(sSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.rel: str = ''
    self.resources: list[sSteamAppInfoEntResource] = []

  def to_dict(self) -> dict:
    self._update_uid()
    return {
      '_id': self._uid,
      'name': self.name,
      'exclude': self.exclude,
      'rel': self.rel,
      'resources': [i.to_dict() for i in self.resources],
    }

  def from_dict(self, d: t.Dict):
    self.exclude = d.get('exclude')
    self.name = d.get('name')
    self.rel = d.get('rel')
    self.resources = [sSteamAppInfoEntResource().from_dict(i) for i in d.get('resources')]
    # self._uid = d.get('_id')
    self._update_uid()
    return self


class sSteamAppInfoEntAddon(sSteamAppInfoEntity):
  def __init__(self):
    super().__init__()
    self.url: str = ''

  def to_dict(self) -> dict:
    self._update_uid()
    return {
      '_id': self._uid,
      'name': self.name,
      'exclude': self.exclude,
      'url': self.url,
    }

  def from_dict(self, d: t.Dict):
    self.exclude = d.get('exclude')
    self.name = d.get('name')
    self.url = d.get('url')
    # self._uid = d.get('_id')
    self._update_uid()
    return self


class SteamAppInfo:
  def __init__(self):
    self.config: sSteamAppInfoEntConfig = sSteamAppInfoEntConfig() 
    self.plugins: list[sSteamAppInfoEntPlugin] = []
    self.addons: list[sSteamAppInfoEntAddon] = []

  def to_dict(self) -> dict:
    return {
      'config': self.config.to_dict(),
      'plugins': [i.to_dict() for i in self.plugins],
      'addons': [i.to_dict() for i in self.addons],
    }

  def from_dict(self, d: t.Dict):
    self.config.from_dict(d.get('config'))
    self.plugins = [sSteamAppInfoEntPlugin().from_dict(i) for i in d.get('plugins')]
    self.addons = [sSteamAppInfoEntAddon().from_dict(i) for i in d.get('addons')]
    return self
