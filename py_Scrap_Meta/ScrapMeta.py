import asyncio
from time import time, sleep
import httpx
import os
import shutil
from argparse import ArgumentParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import subprocess
from time import sleep
import datetime
import re
from concurrent.futures import ThreadPoolExecutor
import json
import itertools
import glob
import sys
import operator
import base64
import zlib
import re
from PIL import Image, UnidentifiedImageError
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib
from googletrans import Translator
import pyperclip
import pymysql
import json
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
os.makedirs(TMP_DIR_PATH, exist_ok=True)

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

IMAGE_CNT = 5
FILE_EXT = ".jpeg"

# トリミング後の縦横比率
WH_RATIO = 40 / 21
Notify_Human_Check_Sound = "Human verification occurring! Please solve the problem and press enter"

def jp_en_translate(string):
  translator = Translator()
  if not (string.isalnum() and string.isascii()):
    string = translator.translate(string, dest='en').text
  return string

def read_config(ele):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
  if ele in data[os.path.basename(ABS_FILE_DIR)].keys():
    return data[os.path.basename(ABS_FILE_DIR)][ele]
  else:
    print(f"read_config エラー: 有効な引数は下記を参照してください。\n{data.keys()}")
    return

URL = read_config("URL")

def scrap_brief():
  large_timer = 60

  "Chrome の起動"
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  options.add_argument('--start-maximized')
  with webdriver.Chrome(service=service, options=options) as BROWSER: # For Mac, Browser version auto-upgrade
    BROWSER.implicitly_wait(large_timer)

    "Meta VR HP画面に遷移"
    sleep(3)
    BROWSER.get(URL)
    sleep(3)

    input("press Enter once you are ready to scraping new titles.")

    game_list = BROWSER.find_elements(by=By.CSS_SELECTOR, value="main#mdc-main-content > div > div > div > main > div > div > ul > li._ank3")
    values = []
    for game in game_list:
      title = game.find_element(by=By.CSS_SELECTOR, value="div > div > div._anhp")
      href = game.find_element(by=By.CSS_SELECTOR, value="div > a._anj6").get_attribute('href')
      values.append({"title": title.text, "href": href})

  return values

def alter_space(string):
    # スペースを "-" に変換
    value = re.sub(r'\s', '-', string)
    # 英数字と"-"以外の文字を削除
    value = re.sub(r'[^a-zA-Z0-9-]', '', value)
    return value

def scrap_detail(titles):
  short_timer = 3
  large_timer = 60
  retry_cnt = 3
  details = []

  "Chrome の起動"
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  options.add_argument('--start-maximized')
  with webdriver.Chrome(service=service, options=options) as BROWSER: # For Mac, Browser version auto-upgrade
    BROWSER.implicitly_wait(large_timer)

    "Meta VR HP画面に遷移"
    sleep(short_timer)
    for target in titles:
      print(target['id'], target['title'])
      BROWSER.get(target['href'])
      sleep(short_timer)
      game_image = BROWSER.find_element(By.CSS_SELECTOR, "#mdc-main-content > div > div > div > main > div > div > div > div._anfv._anfz._anfy")
      game_image.screenshot(f"{TMP_DIR_PATH}/img.png")
      trim_img_path = execute_trim(f"{TMP_DIR_PATH}/img.png", TMP_DIR_PATH)
      base64_img = encode_image(trim_img_path)
      
      info_pointer = BROWSER.find_element(By.CSS_SELECTOR, "#mdc-main-content > div > div > div > main > div > div > div > div._an54 > div._an55 > div > div._an57 > div._an5c > div > div._an1v")
      all_info = info_pointer.find_elements(By.CSS_SELECTOR, "div > div._an30")

      for i in range(len(all_info)):
        if all_info[i].text == "ゲームモード":
          gamemode = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "サポート対象のプラットフォーム":
          platform = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "ジャンル":
          genre = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "言語":
          language = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "リリース日":
          release_date = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "開発者":
          developer = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "パブリッシャー":
          publisher = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        elif all_info[i].text == "必要空き容量":
          storage = info_pointer.find_element(By.CSS_SELECTOR, f"div:nth-child({i+1}) > div._an31").text
        else:
          continue

      description = BROWSER.find_element(By.CSS_SELECTOR, "#mdc-main-content > div > div > div > main > div > div > div > div._an54 > div._an55 > div > div._an57 > div:nth-child(1) > div._an4w > div").text
      slug = alter_space(jp_en_translate(target['title']))
      detail_info = {
        'id': target['id'],
        'gamemode': gamemode,
        'platform': platform,
        'genre': genre,
        'language': language,
        'release_date': release_date,
        'developer': developer,
        'publisher': publisher,
        'storage': storage,
        'description': description,
        'base64_img': base64_img,
        'slug': slug
        }
      
      details.append(detail_info)
  return details

def execute_trim(src_file, dst_dir):
  try:
    img = Image.open(src_file)
    img_ratio = img.width / img.height

    if img_ratio < WH_RATIO:
      # 画像の縦横比がトリミング後の比率よりも大きい場合、上下をトリミング
      new_height = int(img.width / WH_RATIO)
      upper = (img.height - new_height) // 2
      lower = img.height - upper
      img = img.crop((0, upper, img.width, lower))
    else:
      # 画像の縦横比がトリミング後の比率よりも小さい場合、左右をトリミング
      new_width = int(img.height * WH_RATIO)
      left = (img.width - new_width) // 2
      right = img.width - left
      img = img.crop((left, 0, right, img.height))

    dst_file = "trim.png"
    #dst_file = f"trim_{os.path.basename(src_file)}"
    dst_path = os.path.join(dst_dir, dst_file)
    img.save(dst_path)
    return dst_path
  
  except UnidentifiedImageError:
    pass
  except FileNotFoundError:
    pass

def encode_image(img_path):
  with open(img_path, "rb") as f:
    return base64.b64encode(f.read())

def get_element(value, t_list):
  values = []
  for l in t_list:
    values.append(l[value])
  return values

def get_sql() -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      # データ読み込み
      sql = "SELECT * FROM `Extracted_Table`"
      cursor.execute(sql)
      result = cursor.fetchall()
      result = json.loads(result)
  finally:
    print("get_sql succeeded")
    connection.close()
    return result

def get_sql_where() -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      # データ読み込み
      sql = "SELECT base64_img FROM Extracted_Table WHERE id <= 4;"
      cursor.execute(sql)
      result = cursor.fetchall()
      for res in result:
        print(res['base64_img'])
        print()
        with open("image_decode.png", "wb") as fh:
          fh.write(base64.decodebytes(res['base64_img']))
        input()
  finally:
    print("get_sql_where succeeded")
    connection.close()
    input()
    return result

def add_sql(values):
  try:
    connection.ping()
    with connection.cursor() as cursor:
      sql = "INSERT INTO Extracted_Table (title, href) VALUES (%s, %s);"
      cursor.executemany(sql, values)
      connection.commit()

  finally:
    print("Added new game titles to MySQL successfully")
    connection.close()

def update_sql(targets) -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      for target in targets:
        sql = """
              UPDATE Extracted_Table SET 
              gamemode=%(gamemode)s,
              platform=%(platform)s,
              genre=%(genre)s,
              language=%(language)s,
              release_date=%(release_date)s,
              developer=%(developer)s,
              publisher=%(publisher)s,
              storage=%(storage)s,
              description=%(description)s,
              base64_img=%(base64_img)s,
              slug=%(slug)s
              WHERE id=%(id)s;
              """
        cursor.execute(sql, target)
        connection.commit()

  finally:
    print("update_sql succeeded")
    connection.close()
    return

def get_target_titles(titles, scrap_db) -> list:
  targets = []
  for row in scrap_db:
    if row["title"] in titles:
      pass
    else:
      targets.append(tuple(row.values()))
  return targets

def select_sql(col_name, val, database):
  target_db = []
  for i in range(len(database)):
    if database[i][col_name] == val:
      target_db.append(database[i])
  return target_db
  
def add_new_titles():
  existing_db = get_sql()
  ex_titles = get_element("title", existing_db)
  
  scrap_db = scrap_brief()
  new_titles = get_target_titles(ex_titles, scrap_db)
  add_sql(new_titles)
  return

def get_details():
  sql_db = get_sql()
  targets = select_sql("post_bool", 0, sql_db)
  scrap_db = scrap_detail(targets)
  update_sql(scrap_db)

def main():
  add_new_titles()
  get_details()
  return

if __name__ == "__main__":
  main()
  