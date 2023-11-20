import requests
import json
import base64
import os
from googletrans import Translator
import re
import pymysql

connection = pymysql.connect(
  host='localhost', 
  port=3306, 
  user='root', 
  password='', 
  db='meta_store',
  cursorclass=pymysql.cursors.DictCursor
  )

"https://developer.wordpress.org/rest-api/reference/posts/"

ABS_FILE_DIR = os.path.dirname(__file__)
ABS_FILE_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

CONFIG_DIR = "Configs"
CONFIG_FILE = "config.json" # -> JSON を使用する場合
#CONFIG_FILE = "config.yaml" # -> YAML を使用する場合
CONFIG_FILE_PATH = os.path.join(ROOT_DIR, CONFIG_DIR, CONFIG_FILE)
CONFIG_HTML_FILE = "base.html"
CONFIG_HTML_FILE_PATH = os.path.join(ROOT_DIR, CONFIG_DIR, CONFIG_HTML_FILE)

TMP_DIR = "tmp"
TMP_DIR_PATH = os.path.join(ROOT_DIR, TMP_DIR)
#TMP_HTML_FILE = "base.html"
#TMP_HTML_FILE_PATH = os.path.join(ROOT_DIR, TMP_DIR, TMP_HTML_FILE)

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

HEADTAIL_PUDDING = '\n'
INNER_PUDDING = '\n\n\n\n'

"Notion のコラム、Status の項目一覧"
STATUS_NO = "NotAssigned"
STATUS_GO = "AutoQueue"
STATUS_ONGOING = "PostQueue"
STATUS_AWAIT = "ReviewAwaiting"
STATUS_FIX = "ChangeQueue"
STATUS_END = "Confirmed"

def read_config(arg):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
  WP_Auth = data["py_WordPress"].keys()
  if arg in WP_Auth:
    return data["py_WordPress"][arg]
  else:
    exit(f"read_config エラー: 引数には {', '.join(WP_Auth)} のいずれかのみ有効")
  
URL = read_config("URL")
USER = read_config("User")
PASSWORD = read_config("Key")

PATH_POSTS = 'wp-json/wp/v2/posts/'
PATH_MEDIA = 'wp-json/wp/v2/media/'

# Create WP Connection
CREDENTIALS = f"{USER}:{PASSWORD}"
# Encode the connection of your website
TOKEN = base64.b64encode(CREDENTIALS.encode())
# Prepare the header of our request
HEADERS = {
  'Authorization': 'Basic ' + TOKEN.decode('utf-8')
  }

def json_to_POST(dict_data:dict) -> list:
  data_list = []
  elements = dict_data["elements"]
  for ele in elements:
    data = {
      'title': ele["Title"],
      'status': 'private',  # publish, draft, private, pending
      'content': '\n'.join(ele["Contents"]), ###整形が必要
      'categories': [], #[5],
      'tags': [], #[189, 148],
      'slug': ele['slug'],
      'featured_media': ele['ImageWPID'][0]
    }
    data_list.append(data)
  return data_list

def set_WP_attribute(post_db:list) -> list:
  attributes = []
  for data in post_db:
    print(data.keys())
    print(data['post_data'])
    data = {
      'title': data["title"],
      'status': 'private',  # publish, draft, private, pending
      'content': data["post_data"], ###整形が必要
      'categories': [], #[5],
      'tags': [], #[189, 148],
      'slug': data['slug'],
      #'featured_media': data['img_WPID']
    }
    attributes.append(data)
  return attributes

def get_sql() -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      # データ読み込み
      sql = "SELECT * FROM `Extracted_Table` WHERE post_bool = 0"
      cursor.execute(sql)
      result = cursor.fetchall()
      result = json.loads(result)
  finally:
    print("get_sql succeeded")
    connection.close()
    return result
  
def jp_en_translate(string):
  translator = Translator()
  if not (string.isalnum() and string.isascii()):
    string = translator.translate(string, dest='en').text
  return string

def wp_create_post_test() -> dict:
  post = {
    'title': 'Hello World',
    'status': 'draft',  # publish',
    'content': 'テスト',
    'categories': [5],
    'tags': [189, 148],
    'slug': 'pre_open',
  }
  api_url = f'{URL}{PATH_POSTS}'
  res = requests.post(api_url, headers=HEADERS, json=post)
  res_dict = res.json()
  with open("./test_post.json", mode='w') as f:
    json.dump(res_dict, f, indent=2, ensure_ascii=False)
  if res.ok:
    print(f"投稿の追加 成功 code:{res.status_code}")
    return json.loads(res.text)
  else:
    error_msg = json.loads(res.content.decode('utf-8'))
    print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")
    return {}

def wp_create_post(posts:list) -> dict:
  api_url = f'{URL}{PATH_POSTS}'
  post_info = {}
  for post in posts:
    print(f"Article Title: {post['title']}")
    res = requests.post(api_url, headers=HEADERS, json=post)
    if res.ok:
      res_content = json.loads(res.content.decode('utf-8'))
      print(f"投稿の追加 成功 code:{res.status_code}")
      
      post_info[post['title']] = {
        'ID': res_content['id'],
        'URL': res_content['link'],
        }
      
    else:
      error_msg = json.loads(res.content.decode('utf-8'))
      print(f"投稿の追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg['message']}")
  return post_info

def replace(match_obj, data):
  key, same = match_obj.group(1), match_obj.group(0)
  value = data.get(key, same)   # キーが存在しない場合は元の文字列を保持
  #print(f"match: {match_obj}")
  #print(f"key: {key}, {match_obj.group()}")
  #print(f"value: {value}")
  return str(value)

def set_POST_data(database):
  post_db = []
  for data in database:
    with open(CONFIG_HTML_FILE_PATH, mode='r') as f:
      post_data = f.read()
    pattern = re.compile('%{(.*?)}%')
    post_data = pattern.sub(lambda match_obj: replace(match_obj, data), post_data)
    """ 
    -> 上の一文で実際に発生する処理の流れ
    1: post_data 内にpatternで指定した文字列が存在する場合はMatchオブジェクトを生成する。
    2: 生成したMatchオブジェクトはラムダ関数に渡される。
    3: ラムダ関数内の処理として、replace()関数を実行する。(replace(match_obj, data)の実行。)
    3: ラムダ関数(に内包されているreplace関数)の戻り値のstrに応じてpost_dataを書き換えた結果を返す

    下記の1文だと、Matchオブジェクトを動的に取得してreplace関数に渡せない為、要件を満たすことができない。
    post_data = pattern.sub(replace_2(data), post_data)
    """
    data['post_data'] = post_data
    post_db.append(data)
  return post_db

def set_explicit_LF(database):
  for data in database:
    post_data = data['blog_sentence']
    post_data = re.sub(r'(.+?)\n', r'<p>\1</p>\n', post_data)
    data['blog_sentence'] = post_data
    return database

def post_articles():
  sql_db = set_explicit_LF(get_sql())
  POST_data = set_POST_data(sql_db)
  WP_attribute = set_WP_attribute(POST_data)
  wp_create_post(WP_attribute)

def main():
  post_articles()

if __name__ == "__main__":
  main()
