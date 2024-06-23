from srcdsrm.rutil.dl import downloader, new_session
from srcdsrm.rutil.parsers import response_parser
import os

sess = new_session()
# downloader.to_file(sess, 'https://mms.alliedmods.net/mmsdrop/1.11/mmsource-1.11.0-git1155-windows.zip', './dumps')


import tqdm

t = tqdm.tqdm([], rate_fmt='')
# print(t.rate_fmt)