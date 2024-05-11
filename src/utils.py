import typing as t
import requests
import os
import shutil
import tempfile
import tarfile
import functools
import re
from zipfile import ZipFile
from io import IOBase
from src.logger import init_logger
from urllib.parse import urlparse, parse_qs
from collections import namedtuple, deque
from time import time

logger = init_logger('utils')

class PathUtils:

  join = os.path.join
  basename = os.path.basename
  dirname = os.path.dirname

  @staticmethod
  def isdir(path):
    return os.path.exists(path) and os.path.isdir(path)

  @staticmethod
  def isfile(path):
    return os.path.exists(path) and os.path.isfile(path)

  @classmethod
  def stat(cls, path):
    return os.stat(path)

  @classmethod
  def ensure_dir(cls, path):
    if not cls.isdir(path):
      os.makedirs(path)
      return path
    return None

  @staticmethod
  def mkdtemp():
    temp_dir = tempfile.mkdtemp()
    logger.info('creating tempdir: {}'.format(temp_dir))
    def destructor(p):
      logger.info('destroying tempdir: {}'.format(p))
      return shutil.rmtree(p)
    return temp_dir, functools.partial(destructor, temp_dir)

  @staticmethod
  def extract_file_type(s):
    extracted_file_type_t = namedtuple('ExtractedFileType', ['origin', 'file_name', 'file_extension'])
    splits = s.split('.')
    ext = ''
    file_name = s
    if len(splits) > 2 and splits[-2] == 'tar':
      ext = '.'.join(splits[-2:])
      file_name = '.'.join(splits[:-2])
    elif len(splits) > 1:
      ext = splits[-1]
      file_name = '.'.join(splits[:-1])
    s = '.'.join(splits)
    return extracted_file_type_t(s, file_name, ext)

  @staticmethod
  def delete_file(path):
    return os.unlink(path)

  @staticmethod
  def rmtree_d(path):
    for root, dirs, files in os.walk(path):
      for f in files:
        os.unlink(os.path.join(root, f))
      for d in dirs:
        shutil.rmtree(os.path.join(root, d))

  @classmethod
  def copy2(cls, src, dst):
    cls.ensure_dir(os.path.dirname(dst))
    return shutil.copy2(src, dst)

  @classmethod
  def copy2_r(cls, src, dst):
    for root, dirs, files, in os.walk(src):
      rel_dest = os.path.join(dst, os.path.relpath(root, src))
      for d in dirs:
        dst_dir = os.path.join(rel_dest, d)
        d_dst = cls.ensure_dir(dst_dir)
        if not d_dst is None:
          print(') {}'.format(dst_dir))
      for f in files:
        dst_file = os.path.join(rel_dest, f)
        d_dst = cls.copy2(os.path.join(root, f), dst_file)
        if not d_dst is None:
          print('> {}'.format(d_dst))

  @classmethod
  def archive_extract_zip(cls, path, dst, tmpdir=None):
    if tmpdir is None:
      zip_tempdir, d_zip_tempdir = cls.mkdtemp()
    else:
      d_zip_tempdir = lambda: None
      zip_tempdir = tmpdir
    with ZipFile(path) as zh:
      zh.extractall(zip_tempdir)
      cls.copy2_r(zip_tempdir, dst)
    if tmpdir is None:
      d_zip_tempdir()
    else:
      cls.rmtree_d(zip_tempdir)

  @classmethod
  def archive_extract_tar(cls, path, dst, tmpdir=None):
    if tmpdir is None:
      tar_tempdir, d_tar_tempdir = mkdtemp()
    else:
      d_tar_tempdir = lambda: None
      tar_tempdir = tmpdir
    with tarfile.open(path, mode='r') as th:
      th.extractall(tar_tempdir)
      cls.copy2_r(tar_tempdir, dst)
    if tmpdir is None:
      d_tar_tempdir()
    else:
      cls.rmtree_d(tar_tempdir)


class HTTPUtils:

  class RetryableConnectionError(requests.exceptions.HTTPError): pass

  file_info_t = namedtuple("FileInfo", field_names=['file_name', 'file_type',  'file_size', 'content_disposition', 'content_type'])
  
  @staticmethod
  def new_session(request_headers=None) -> requests.Session:
    session = requests.Session()
    if request_headers:
      session.headers.update(request_headers)
    logger.info('instantiating new session.')
    return session

  @staticmethod
  def url_basename(url) -> str:
    r = urlparse(url)
    return r.path.rstrip('/').split('/')[-1]

  @classmethod
  def http_request(cls, session: requests.Session, method, url, max_retry=3, force_retry=False, max_depth=10, **kwargs) -> t.Optional[requests.Response]:
    logger.info('{} {}'.format(method, url))
    for i_retry in range(1, max_retry + 1):
      for i_depth in range(max_depth):
        try:
          resp = session.request(method, url, **kwargs)
          if resp.status_code == 301 or resp.status_code == 302:
            url = resp.headers.get('location')
            if url is None:
              url = resp.url
            logger.info('redirecting connection: {} {}'.format(i_depth, url))
            continue
          elif resp.status_code == 200:
            logger.info('{} ok'.format(method))
            return resp
          elif force_retry:
            raise cls.RetryableConnectionError('{} {} forcing retry attempt'.format(resp.status_code, resp.reason))
          else:
            raise requests.ConnectionError('cannot establish connection: {} {}'.format(resp.status_code, resp.reason))
        except (requests.Timeout, cls.RetryableConnectionError):
          logger.warning('retrying connection {}'.format(i_retry))
          sleep(2.5)
          break
        except Exception as e:
          logger.error('error occured: {}'.format(e))
          return None
    return None

  @staticmethod
  def stream_to_buf(resp: requests.Response, buf: IOBase, chunk_size=4096, content_length=0, update_stdout_sec=5) -> bool:
    total_l = 0
    dl = 0
    dt = 0
    t0 = time()
    tn = t0
    speed = 0
    speed_avg = 0
    speed_rec = deque(list(), maxlen=5)

    if content_length == 0:
      content_length = int(resp.headers.get('content-length', 0))
    try:
      for b in resp.iter_content(chunk_size):
        buf.write(b)
        bl = len(b)
        total_l += bl
        dl += bl
        dt = time() - tn
        if content_length > 0 and dt > update_stdout_sec:
          ratio = total_l / content_length
          speed = dl/max(dt, 0.01)
          speed_rec.append(speed)
          speed_avg = sum(speed_rec) / len(speed_rec)
          est_s = (content_length - total_l) / speed_avg

          est_m, est_s = divmod(est_s, 60)
          est_h, est_m = divmod(est_m, 60)
          print('downloading: {:>7.02%} | {:>12.02f} kb/s | est {:>3d}:{:>02d}:{:>02d}.{:<02d}'.format(ratio, speed_avg/1000, int(est_h), int(est_m), int(est_s), min(int(est_s%1*100), 99)))
          dl = 0
          tn = time()
        elif dt > update_stdout_sec:
          speed = dl/max(dt, 1e-8)
          speed_rec.append(speed)
          speed_avg = sum(speed_rec) / len(speed_rec)
          dl = 0
          tn = time()
          print('downloading {:>7.02f}kb/s | {:g}kb'.format(speed_avg, total_l/1000))
    except Exception as e:
      logger.error('error ocurred during fetch stream: {}'.format(e))
      return False
    logger.info('download finished')
    return True

  @staticmethod
  def parse_headers_file_name(headers):
    content_disposition = headers.get('content-disposition', '')
    file_name = ''
    if not re.search(r'filename=(.+)', content_disposition) is None:
      file_name = re.findall(r'filename=(.+)', content_disposition)[0].strip('"')
    elif not re.search(r'filename\*=(.+)', content_disposition) is None:
      file_name = re.findall(r'filename\*=(.+)', content_disposition)[0].strip('"')
      # RFC 6266 - attfn2231
      if file_name.lower().startswith('utf-8'):
        file_name = file_name[7:]
    return file_name.strip('\'\\".;)*\ ')

  @staticmethod
  def parse_headers_content_length(headers):
    content_length = headers.get('content-length', '0')
    if content_length.isnumeric():
      content_length = int(content_length)
    else:
      content_length = 0
    return content_length

  @staticmethod
  def parse_headers_content_type(headers):
    return headers.get('content-type', '')

  @classmethod
  def parse_file_info(cls, headers, url):
    content_disposition = headers.get('content-disposition', '')
    file_name = cls.parse_headers_file_name(headers)
    if not file_name:
      file_name = cls.url_basename(url)
    _, _, file_type = PathUtils.extract_file_type(file_name)
    content_type = cls.parse_headers_content_type(headers)
    content_length = cls.parse_headers_content_length(headers)
    return cls.file_info_t(file_name, file_type, content_length, content_disposition, content_type)

  @classmethod
  def parse_workshop_ids(cls, string):
    if string.isnumeric():
      return [string]
    parsed_url = urlparse(string)
    if not parsed_url.query:
      logger.warning('cannot parse url: {}'.format(string))
      return None
    parsed_query = parse_qs(parsed_url.query)
    ids = parsed_query.get('id')
    if ids is None or len(ids) == 0:
      logger.warning('missing query id on url: {}'.format(string))
    return list(ids)

  @classmethod
  def download_file(cls, session, url, dst_dir, file_name='', chunk_size=4096, head_err_max_retry=5):
    logger.info('retrieving file info: {}'.format(url))

    skip_get_request = False
    resp = cls.http_request(session, 'HEAD', url, allow_redirects=False, force_retry=False)
    if resp is None:
      logger.warning('cannot retrieve HEAD, changing method to GET')
      resp = cls.http_request(session, 'GET', url, allow_redirects=False, stream=True)
      if resp is None:
        logger.error('unable to retrieve GET request')
        return False, None, None
      skip_get_request = True

    PathUtils.ensure_dir(dst_dir)

    file_info = cls.parse_file_info(resp.headers, url)
    dst_path = os.path.join(dst_dir, file_info.file_name)
    if PathUtils.isfile(dst_path):
      if os.path.getsize(dst_path) != file_info.file_size:
        logger.info('file size did not match, redownloading: {}'.format(dst_path))
        os.unlink(dst_path)
      else:
        logger.info('file already exists: {}'.format(dst_path))
        resp.close()
        return True, dst_path, file_info

    if not skip_get_request:
      resp = cls.http_request(session, 'GET', url, stream=True, allow_redirects=False)

    if resp is None:
      logger.error('unable to retrieve GET request')
      return False, dst_path, file_info
    
    logger.info('downloading to {}'.format(dst_path))
    with open(dst_path, 'wb') as fh:
      status = cls.stream_to_buf(resp, fh, content_length=file_info.file_size)
    resp.close()

    return status, dst_path, file_info

  @classmethod
  def download_steam_workshop(cls, session, dst_dir, workshop_id):
    db_hostname = 'https://db.steamworkshopdownloader.io'
    db_api_path = 'prod/api/details/file'
    data = bytes(f'[{workshop_id}]', 'utf8')

    db_resp = cls.http_request(session, 'POST', url='{}/{}'.format(db_hostname, db_api_path), data=data)
    if db_resp is None:
      logger.warning('cannot retrieve workshop info: {}'.format(workshop_id))
      return
    try:
      workshop_db_res = db_resp.json()
    except requests.exceptions.JSONDecodeError as e:
      logger.error(e)
      return

    for workshop_ent in workshop_db_res:
    
      result = workshop_ent.get('result')
      file_url = workshop_ent.get('file_url')
      preview_url = workshop_ent.get('preview_url')
      file_name = workshop_ent.get('filename')
      is_collection = workshop_ent.get('show_subscribe_all', False)
      is_collection = is_collection and not workshop_ent.get('can_subscribe', False)

      logger.info('downloading workshop: {}'.format(file_name))

      if result: 
        if is_collection:
          logger.info('workshop collection found instead, processing children')
          for workshop_child_ent in workshop_ent.get('children'):
            workshop_child_id = workshop_child_ent.get('publishedfileid')
            if not workshop_child_id is None:
              cls.download_steam_workshop(session, dst_dir, workshop_child_id)
        else:
          workshop_resource_urls = [file_url, preview_url]
          for workshop_resource_url in workshop_resource_urls:
            if not workshop_resource_url is None:
              export_dir = dst_dir
              PathUtils.ensure_dir(export_dir)
              status, download_file_path, file_info = cls.download_file(session, workshop_resource_url, export_dir)
              if not status and not download_file_path is None:
                logger.warning('destroying unfinished addon file')
                PathUtils.delete_file(download_file_path)
