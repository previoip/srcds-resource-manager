import configparser
from functools import partial
from src.utils import PathUtils

class Config:

  def __init__(self):
    self._parser = configparser.ConfigParser()

  def load(self, path):
    if not PathUtils.isfile(path):
      return
    if PathUtils.stat(path).st_size == 0:
      return
    with open(path, 'r') as fh:
      self._parser.read_file(fh)

  def save(self, path):
    with open(path, 'w') as fh:
      self._parser.write(fh)


  @property
  def info_file(self):
    return self._parser['DEFAULT'].get('appinfo')

  @info_file.setter
  def info_file(self, v):
    v = str(v)
    p = PathUtils.extract_file_type(v)
    if not p.file_extension == 'json':
      v += '.json'
    self._parser['DEFAULT']['appinfo'] = v


  @property
  def platform(self):
    return self._parser['DEFAULT'].get('platform')

  @platform.setter
  def platform(self, v):
    v = str(v)
    self._parser['DEFAULT']['platform'] = v

  @property
  def target_dir(self):
    return self._parser['DEFAULT'].get('tgtdir')

  @target_dir.setter
  def target_dir(self, v):
    v = str(v)
    self._parser['DEFAULT']['tgtdir'] = v