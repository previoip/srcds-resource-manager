import typing as t
import os
import io
import tarfile
from zipfile import ZipFile, is_zipfile
from collections import namedtuple

class FileTree:

  t_scan_info = namedtuple('ScanInfo', ['isdir', 'path', 'size'])

  class ModeEnum:
    folder = 1
    zip = 2
    tar = 3


  @staticmethod 
  def walk(path):
    yield from os.walk(path)

  @classmethod
  def scan_dir(cls, path):
    for root, dirs, files in cls.walk(path):
      for d in dirs:
        yield cls.t_scan_info(True, os.path.join(root, d),  0)
      for f in files:
        fpath = os.path.join(root, f)
        yield cls.t_scan_info(False, fpath, os.stat(fpath).st_size)

  @classmethod
  def scan_zip_file(cls, filelike: t.Union[t.AnyStr, t.IO[bytes]]):
    zh = ZipFile(filelike)
    for zi in zh.filelist:
      yield cls.t_scan_info(zi.is_dir(), zi.filename, zi.file_size)
    zh.close()

  @classmethod
  def scan_tar_file(cls, filelike: t.Union[t.AnyStr, t.IO[bytes]]):
    if isinstance(filelike, io.IOBase):
      th = tarfile.open(fileobj=filelike)
    else:
      th = tarfile.open(filelike)
    for ti in th.getmembers():
      yield cls.t_scan_info(ti.isdir(), ti.name, ti.size)
    th.close()

  def __init__(self, mode):
    self._modes = [self.ModeEnum.folder, self.ModeEnum.zip, self.ModeEnum.tar]
    self.mode = mode
    self.list = list()

  def set_mode(mode):
    if not mode in self._modes:
      raise ValueError('invalid scan mode: {}'.format(self.mode))
    self.mode = mode

  def scan(self, path, mode=None):
    if not mode is None:
      self.set_mode(mode)
    if self.mode == self.ModeEnum.folder:
      scanner = self.scan_dir
    elif self.mode == self.ModeEnum.zip:
      scanner = self.scan_zip_file
    elif self.mode == self.ModeEnum.tar:
      scanner = self.scan_tar_file
    self.list.clear()
    for scan_info in scanner(path):
      self.list.append(scan_info)

  def save_str(self):
    r = ''
    for scan_info in self.list:
      isdir, path, size = scan_info
      r += str(int(isdir)) + '"'
      r += path + '"'
      r += str(size)
      r += '\n'