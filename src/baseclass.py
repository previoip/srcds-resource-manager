class PrintMethods:
  _level = 0

  @classmethod
  def print(cls, *args, **kwargs):
    print(*args, **kwargs)

  @classmethod
  def print_err(cls, *args, **kwargs):
    print('ERROR:', *args, **kwargs)

  @classmethod
  def print_dbg(cls, *args, **kwargs):
    print('DEBUG:', *args, **kwargs)
