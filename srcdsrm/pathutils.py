from re import compile as re_compile

regexp_invalid_path_chars = re_compile(r'[\\\/\>\<:"\|\?\*%\x00-\x1f]+')

def validate_path_string(s):
  s = regexp_invalid_path_chars.sub('', s)
  return s
