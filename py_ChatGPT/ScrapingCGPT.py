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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib
from googletrans import Translator
import pyperclip
import pymysql

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
TMP_FILE = "Notion_Pages.json"
TMP_FILE_PATH = os.path.join(ROOT_DIR, TMP_DIR, TMP_FILE)

LOG_DIR = "log"
LOG_FILE = "debug.log"
LOG_FILE_PATH = os.path.join(ROOT_DIR, LOG_DIR, LOG_FILE)

IMAGE_CNT = 5
FILE_EXT = ".jpeg"

Notify_Human_Check_Sound = "Human verification occurring! Please solve the problem and press enter"

def read_config(ele):
  with open(CONFIG_FILE_PATH, mode='r') as f:
    data = json.load(f)
  if ele in data[os.path.basename(ABS_FILE_DIR)].keys():
    return data[os.path.basename(ABS_FILE_DIR)][ele]
  else:
    print(f"read_config エラー: 有効な引数は下記を参照してください。\n{data.keys()}")
    return
    
SignInOption = read_config("SignInOption")
Valid_SignIn_Options = ["email"]
USER = read_config("User")
PASSWORD = read_config("password")
SKIP_LOGIN = read_config("SkipAutoLogIn")
IS_NEW_BROWSER = read_config("IsNewBrowser")
IS_NON_STOP = read_config("NonStop")
ORDER_LIST = read_config("Order")

def set_target_URL():
  urls = [
    "https://chat.openai.com/auth/login",
    "https://auth0.openai.com/u/login/identifier",
    "https://auth0.openai.com/u/login/password",
    "https://chat.openai.com",
    "https://chat.openai.com/c"
  ]
  return urls

URLs = set_target_URL()

def read_NotionObj() -> list:
  info = []
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)
  for d in data["elements"]:
    if d["FullForm"] == "":
      p = {d["Title"]: d["Title"]}
    else:
      p = {d["Title"]: d["FullForm"]}
    info.append(p)
  return info

"def write_NotionObj(notion_obj, l_sentences):"
def write_NotionObj(l_sentences):
  with open(TMP_FILE_PATH, mode='r') as f:
    data = json.load(f)

  for d_sentence in l_sentences:
    title, sentence = list(d_sentence.items())[0]
    for i in range(len(data["elements"])):
      if title == data["elements"][i]["Title"]:
        data["elements"][i]["Contents"] = sentence

  data["checkpoint"] = 2
  with open(TMP_FILE_PATH, mode='w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
  return

def set_order(d_fullform) -> list:
  f_orders = []
  for f in d_fullform:
    title, fullform = list(f.items())[0]
    orders = []
    for order in ORDER_LIST:
      order = re.sub('{Title}', title, order)
      order = re.sub('{Full Form}', fullform, order)
      orders.append(order)
    d_order = {title: orders}
    f_orders.append(d_order)
  return f_orders

def get_order(title, description) -> list:
  orders = []
  for order in ORDER_LIST:
    order = re.sub('{Title}', title, order)
    orders.append(order)
  orders.extend(description)
  return orders

def get_login_screen(browser, cnt, timer):
  "[期待値] ChatGPT ログイン画面に遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      log_in_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div > button:nth-child(1)")))
      log_in_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[1]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_user(browser, cnt, timer):
  "[期待値] email を入力して「次へ」ボタンを押す"
  for i in range(cnt):
    try: #失敗しそうな処理
      user_box = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id='username']")))
      user_box.send_keys(USER)
      next_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='button-login-id']")))
      next_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[2]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_password(browser, cnt, timer):
  "[期待値] password を入力して「サインイン」ボタンを押す"
  for i in range(cnt):
    try: #失敗しそうな処理
      pass_box = WebDriverWait(browser, timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']")))
      pass_box.send_keys(PASSWORD)
      submit_button = WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='button-login-password']")))
      submit_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[3]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_popup(browser, cnt, timer):
  "[期待値] 継続サインイン入力画面から bing ホームページへ遷移"
  for i in range(cnt):
    try: #失敗しそうな処理
      if WebDriverWait(browser, timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#radix-\:rf\: > div.p-4.sm\:p-6.sm\:pt-4 > div > div.flex.flex-row.justify-end > button"))):
        close_button = browser.find_element(by=By.CSS_SELECTOR, value="#radix-\:rf\: > div.p-4.sm\:p-6.sm\:pt-4 > div > div.flex.flex-row.justify-end > button")
        close_button.click()
      WebDriverWait(browser, timer).until(EC.url_matches(URLs[3]))
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def pass_orders(browser, cnt, short_timer, large_timer, orders):
  for i in range(cnt):
    try: #失敗しそうな処理
      print(sys._getframe().f_code.co_name)
      print(orders)
      orders_box = WebDriverWait(browser, short_timer).until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[id='prompt-textarea']")))
      "下記 for loop が失敗する場合の処理"
      "for loop が失敗する場合は上の処理に変更する"
      for order in orders:
        if order == "":
          continue
        orders_box.send_keys(order)
        orders_box.send_keys(Keys.SHIFT + Keys.ENTER)

      submit_button = WebDriverWait(browser, short_timer).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.rounded-xl.shadow-xs.dark\:shadow-xs > button")))
      submit_button.click()
      sleep(short_timer)
      
      sleep(short_timer)
      
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def end_check(browser, cnt, short_timer, large_timer):
  for i in range(cnt):
    try: #失敗しそうな処理
      print(sys._getframe().f_code.co_name)
      gen_message = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "form > div > div.flex.w-full.items-center > div > div > div > div > button"))).get_attribute('aria-label') # --- 2023/11 時点のコード
      while gen_message in ["Stop generating", "Continue generating"]:
        if gen_message == "Continue generating":
          print("continue_button pressed")
          continue_button = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.items-center.md\:items-end > div > button")))
          continue_button.click()

        sleep(short_timer)
        if WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "form > div > div.flex.w-full.items-center > div > button"))).get_attribute('data-testid') == "send-button":
          break
        else:
          gen_message = WebDriverWait(browser, large_timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "form > div > div.flex.w-full.items-center > div > div > div > div > button"))).get_attribute('aria-label') # --- 2023/11 時点のコード
    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def get_sentences(browser, cnt, timer):
  browser.find_element(By.CSS_SELECTOR, 'body').click()
  browser.execute_script('window.scrollTo(0, document.body.scrollHeight);')
      
  for i in range(cnt):
    try: #失敗しそうな処理
      print(sys._getframe().f_code.co_name)
      screen = WebDriverWait(browser, timer).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.flex.flex-grow.flex-col.gap-3 > div > div")))
      screen.click()
      action_chains = ActionChains(browser)
      action_chains.key_down(Keys.COMMAND).key_down(Keys.SHIFT).send_keys("c").key_up(Keys.COMMAND).key_up(Keys.SHIFT).perform()
      copied_texts = pyperclip.paste()
      sentences = []
      for s in copied_texts.split("\n"):
        sentences.append(s)

    except Exception as e: #失敗時の処理(不要ならpass)
      error = e
      print("retrying...")
    else: #失敗しなかった場合は、ループを抜ける
      print(f"success {sys._getframe().f_code.co_name} with {i} retry")
      return copied_texts
  else: #リトライが全部失敗したときの処理
    print(error)
    exit("failed")

def scraping_new_browser(l_descriptions) -> list:
  short_timer = 3
  large_timer = 60
  retry_cnt = 3

  "Chrome の起動"
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  
  "既存ブラウザを使用しない場合"
  service = ChromeService(ChromeDriverManager().install())
  options = webdriver.ChromeOptions()
  options.add_argument('--start-maximized')
  with webdriver.Chrome(service=service, options=options) as BROWSER: # For Mac, Browser version auto-upgrade
    print(BROWSER.current_url)
    BROWSER.implicitly_wait(large_timer)

    "ChatGPT ログイン画面に遷移"
    sleep(10)
    BROWSER.get(URLs[0])
    get_login_screen(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    pass_user(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    sleep(short_timer) #URL遷移が発生しない場合はsleepを入れないと、その後の処理がおかしくなる
    pass_password(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    pass_popup(browser=BROWSER, cnt=retry_cnt, timer=short_timer)

  for i in range(len(BROWSER.window_handles)):
    BROWSER.switch_to.window(BROWSER.window_handles[i])
    if BROWSER.current_url != "https://chat.openai.com/":
      continue
    else:
      break
  l_info = []

  for d_description in l_descriptions:
    title, description = d_description['title'], d_description['description'].splitlines()
    orders = get_order(title, description)
    d_sentences = {}
    pass_orders(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer, orders=orders)
    end_check(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer)
    sentences = get_sentences(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    d_sentences[title] = sentences
    d_info = {
      'id': d_description['id'],
      'blog_sentence': sentences
    }
    l_info.append(d_info)
    sleep(short_timer)

  BROWSER.quit()
  return l_info


def scraping_exist_browser(l_descriptions) -> list:
  short_timer = 3
  large_timer = 60
  retry_cnt = 3

  "Chrome の起動"
  print("For Mac: run the following command in terminal and get pass ChatGPT login. After that, press 'yes' and enter.")
  print('Command: /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --profile-directory="Profile 18"')
  print("Tips: profile-directory can be found under '/Users/<username>/Library/Application Support/Google/Chrome/' folder")
  if not IS_NON_STOP:
    while True:
      if input("Are you ready for Scraping? (yes/no): ").lower() in ["y","yes"]:
        break
  service = ChromeService(executable_path="/Users/satoshi/.wdm/drivers/chromedriver/mac64/119.0.6045.123/chromedriver-mac-arm64/chromedriver")
  options = webdriver.ChromeOptions()
  options.add_argument('--start-maximized')
  options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
  BROWSER = webdriver.Chrome(service=service, options=options)# For Mac, Browser version auto-upgrade
  BROWSER.implicitly_wait(short_timer)

  for i in range(len(BROWSER.window_handles)):
    BROWSER.switch_to.window(BROWSER.window_handles[i])
    if BROWSER.current_url != "https://chat.openai.com/":
      continue
    else:
      break
  l_info = []
  for d_description in l_descriptions:
    title, description = d_description['title'], d_description['description'].splitlines()
    orders = get_order(title, description)
    d_sentences = {}
    pass_orders(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer, orders=orders)
    end_check(browser=BROWSER, cnt=retry_cnt, short_timer=short_timer, large_timer=large_timer)
    sentences = get_sentences(browser=BROWSER, cnt=retry_cnt, timer=short_timer)
    d_sentences[title] = sentences
    d_info = {
      'id': d_description['id'],
      'blog_sentence': sentences
    }
    l_info.append(d_info)
    sleep(short_timer)

  BROWSER.quit()
  return l_info

def get_sql() -> list:
  try:
    connection.ping()
    with connection.cursor() as cursor:
      # データ読み込み
      sql = "SELECT `id`, `title`, `description` FROM `Extracted_Table` WHERE post_bool = 0"
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
              blog_sentence=%(blog_sentence)s
              WHERE id=%(id)s;"""
        
        cursor.execute(sql, target)
        connection.commit()

  finally:
    print("update_sql succeeded")
    connection.close()
    return

def get_blog_contents():
  if SignInOption not in Valid_SignIn_Options:
    print(f"現在対応中の SignInOption は下記の通りです。config ファイルで有効な設定に変更してください。\n{Valid_SignIn_Options}")
    exit()

  sql_db = get_sql()

  if IS_NEW_BROWSER:
    "ブラウザを新しく開く場合(cloudflare 対策無し)"
    sentences_list = scraping_new_browser(sql_db)
  else:
    "既存ブラウザを用いる場合(cloudflare 対策有り)"
    sentences_list = scraping_exist_browser(sql_db)

  print(sentences_list)
  update_sql(sentences_list)
  return

def main():
  get_blog_contents()
  return

if __name__ == "__main__":
  main()
  