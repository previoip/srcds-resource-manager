import sys
import os
import traceback
from srcdsrm.rutil.dl import new_session, downloader


class Main:
  def __init__(self):
    self.sess = new_session()

  def _loop(self):
    while True:
      pass

  def run(self):
    try:
      self._loop()
    except KeyboardInterrupt as e:
      pass
    except Exception as e:
      self.on_error()

  def on_exit(self):
    self.sess.close()

  def on_error(self):
    print(traceback.format_exc(), file=sys.stderr)


if __name__ == '__main__':
  main = Main()
  main.run()
  main.on_exit()