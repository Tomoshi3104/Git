""" 
WARNING:
Different version may result in unexpected behavior.
==========
Python             3.11.1
selenium           4.10.0
requests           2.31.0
googletrans        4.0.0rc1
Pillow             10.0.0
PyMySQL            1.1.0
webdriver-manager  4.0.0

2023/11/21
 """

import os
import json
from argparse import ArgumentParser
#from py_Notion import ReadDB
from py_Scrap_Meta import ScrapMeta
from py_ChatGPT import ScrapingCGPT
#from py_ImageGenerate import ScrapingBIC, TrimImage
from py_WordPress import PostArticle, UploadImage
from time import sleep
import subprocess

ABS_FILE_DIR = os.path.dirname(__file__)
ABS_FILE_PATH = os.path.abspath(__file__)
ROOT_DIR = os.path.dirname(__file__)

TMP_DIR = "tmp"
CONFIG_DIR = "Configs"
CONFIG_FILE = "config.json" # -> JSON を使用する場合
#CONFIG_FILE = "config.yaml" # -> YAML を使用する場合
CONFIG_FILE_PATH = os.path.join(ROOT_DIR, CONFIG_DIR, CONFIG_FILE)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(TMP_DIR, exist_ok=True)

last_endpoint = 4

PT_ADD_TITLES = 0
PT_SCRAP_DETAIL = 1
PT_CHATGPT = 2
PT_UPLOAD_IMAGE = 3
PT_WP_POST = 4

def get_position():
  argparser = ArgumentParser()
  argparser.add_argument(
    '-s', '--start_over', 
    action="store_true", 
    help=f'Discard everything in progress and start over from the beginning.'
    )
  argparser.add_argument(
    '-e', '--end', 
    type=int, 
    nargs='?', 
    default=last_endpoint, 
    choices=range(last_endpoint+1), 
    help=f'Specify endpoint number from the below list.\n{list(range(last_endpoint+1))}'
    )
  argparser.add_argument(
    '-c', '--current_checkpoint', 
    action="store_true", 
    help=f'only shows current checkpoint {CONFIG_FILE} contains.'
    )
  return argparser.parse_args()

def get_checkpoint():
  try:
    with open(CONFIG_FILE_PATH, mode='r') as f:
      data = json.load(f)
  except FileNotFoundError as e:
    print(e)
    return 0
  return data["checkpoint"]

def set_checkpoint(num):
  try:
    with open(CONFIG_FILE_PATH, mode='r') as f:
      data = json.load(f)
    data["checkpoint"] = num
    with open(CONFIG_FILE_PATH, mode='w') as f:
      json.dump(data, f, indent=2, ensure_ascii=False)

  except FileNotFoundError as e:
    print(e)
    return 0
  return data["checkpoint"]

def main():
  args = get_position()
  if args.start_over:
    checkpoint = 0
  else:
    checkpoint = get_checkpoint()
  if args.current_checkpoint:
    print(f"Current checkpoint: {checkpoint}")
    exit()

  if checkpoint <= PT_ADD_TITLES and args.end >= PT_ADD_TITLES:
    subprocess.run(["say", "-v", "Daniel", "Scrap Meta.py add new titles has begun."])
    "Meta Store の各ゲームページからゲームの詳細情報を取得"
    ScrapMeta.add_new_titles()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("ScrapMeta.add_new_titles() : Done")

  if checkpoint <= PT_SCRAP_DETAIL and args.end >= PT_SCRAP_DETAIL:
    subprocess.run(["say", "-v", "Daniel", "Scrap Meta.py get details has begun."])
    "Meta Store の各ゲームページからゲームの詳細情報を取得"
    ScrapMeta.get_details()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("ScrapMeta.get_details() : Done")

  if checkpoint <= PT_CHATGPT and args.end >= PT_CHATGPT:
    subprocess.run(["say", "-v", "Daniel", "Scraping ChatGPT.py has begun."])
    "ChatGPT を利用して自動記事生成"
    ScrapingCGPT.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("ScrapingCGPT.main(): Done")

  if checkpoint <= PT_UPLOAD_IMAGE and args.end >= PT_UPLOAD_IMAGE:
    subprocess.run(["say", "-v", "Daniel", "Upload Image.py has begun."])
    "BingImageCreator を利用して自動画像生成"
    UploadImage.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("UploadImage.main(): Done")

  if checkpoint <= PT_WP_POST and args.end >= PT_WP_POST:
    subprocess.run(["say", "-v", "Daniel", "Post Article.py has begun."])
    "BingImageCreator で取得した画像を縦21:横40の比率にトリミング調整"
    PostArticle.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("PostArticle.main(): Done")
  
  if checkpoint == last_endpoint:
    set_checkpoint(0)
  subprocess.run(["say", "-v", "Daniel", "Blog Automation Completed."])
  
if __name__ == "__main__":
  main()
