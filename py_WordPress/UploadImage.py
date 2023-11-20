import os
import shutil
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
import subprocess
from time import sleep
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
import json
import itertools
import glob
import requests
import json
import base64
import os
import pymysql
from googletrans import Translator

connection = pymysql.connect(
  host='localhost', 
  port=3306, 
  user='root', 
  password='', 
  db='meta_store',
  cursorclass=pymysql.cursors.DictCursor
  )

ABS_FILE_DIR = os.path.dirname(__file__)
ABS_FILE_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

CONFIG_DIR = "Configs"
CONFIG_FILE = "config.json" # -> JSON を使用する場合
#CONFIG_FILE = "config.yaml" # -> YAML を使用する場合
CONFIG_FILE_PATH = os.path.join(ROOT_DIR, CONFIG_DIR, CONFIG_FILE)

TMP_DIR = "tmp"
TMP_DIR_PATH = os.path.join(ROOT_DIR, TMP_DIR)
TMP_FILE = "Notion_Pages.json"
TMP_FILE_PATH = os.path.join(ROOT_DIR, TMP_DIR, TMP_FILE)

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

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

def read_json():
  with open(TMP_FILE_PATH, mode='r') as f:
    s = json.load(f)
  return s

def json_to_IMAGE(dict_data:dict) -> list:
  data_list = []
  elements = dict_data["elements"]
  for ele in elements:
    data = {
      'Title': ele["Title"],
      'Images': ele["Images"],
      #'CustomURL': ele["CustomURL"],
      #'status': 'publish',  # publish, draft
      #'content': html_mix, ###整形が必要
      #'categories': [], #[5],
      #'tags': [], #[189, 148],
      #'slug': ele['Title'],
    }
    data_list.append(data)
  return data_list

def get_file_type(filename):
  # Content-Typeの指定
  print(filename)
  file_extention = filename.split('.')[-1].lower()
  if file_extention in ['jpg', 'jpeg']:
      contentType = 'image/jpg'
  elif file_extention == 'png':
      contentType = 'image/png'
  elif file_extention == 'gif':
      contentType = 'image/gif'
  elif file_extention == 'bmp':
      contentType = 'image/bmp'
  elif file_extention == 'mp4':
      contentType = 'movie/mp4'
  else:
      print(f'not supported [{file_extention}]')
      exit()
  return contentType

def upload_image(database:list) -> dict:
  api_url = f'{URL}{PATH_MEDIA}'
  new_db = []
  for d_img in database:
    print(d_img.keys())
    print(d_img['title'])
    file_path = f"{TMP_DIR_PATH}/{d_img['slug']}.png"
    with open(file_path, "wb") as fh:
      fh.write(base64.decodebytes(d_img['base64_img']))
    file_name = os.path.basename(file_path)
    file_type = get_file_type(file_name)
    data = {
      "slug": d_img['slug'],
      "title": d_img['title'],
      }
    headers = {
      'Authorization': 'Basic ' + TOKEN.decode('utf-8'),
      }
    
    with open(file_path, mode='rb') as f:
      files = {'file': (file_path, f, file_type)}  # ファイル名とコンテンツタイプを設定
      res = requests.post(url=api_url, headers=headers, files=files, data=data)
    if res.ok:
      print(f"メディアの追加 成功 code:{res.status_code}")
      res_content = json.loads(res.content.decode('utf-8'))
      d_img['img_WPID'] = res_content['id']
      d_img['img_href'] = res_content['guid']['rendered']
      print(d_img['img_href'])
      new_db.append(d_img)
    else:
      error_msg = json.loads(res.content.decode('utf-8'))
      print(f"メディアの追加 失敗 code:{res.status_code} reason:{res.reason} msg:{error_msg}")
    os.remove(file_path)
  return new_db

def get_sql() -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      # データ読み込み
      sql = "SELECT `id`, `title`, `base64_img`, `slug` FROM `Extracted_Table` WHERE post_bool = 0"
      cursor.execute(sql)
      result = cursor.fetchall()
      result = json.loads(result)
  finally:
    print("get_sql succeeded")
    connection.close()
    return result

def update_sql(targets) -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      for target in targets:
        sql = """UPDATE Extracted_Table SET 
              img_WPID=%(img_WPID)s,
              img_href=%(img_href)s
              WHERE id=%(id)s;"""
        cursor.execute(sql, target)
        connection.commit()

  finally:
    print("update_sql succeeded")
    connection.close()
    return
  
def post_images():
  sql_db = get_sql()
  img_WPID = upload_image(sql_db)
  update_sql(img_WPID)

def main():
  post_images()
  pass

if __name__ == "__main__":
  main()
