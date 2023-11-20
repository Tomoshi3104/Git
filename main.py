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

last_endpoint = 3

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

  if checkpoint <= 0 and args.end >= 0:
    subprocess.run(["say", "-v", "Daniel", "Scrap Meta.py has begun."])
    "Notion AI のタスク名、AI記事を取得。タスク名は prompt.txt に保存"
    ScrapMeta.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("Reading Database from Notion: Done")

  if checkpoint <= 1 and args.end >= 1:
    subprocess.run(["say", "-v", "Daniel", "Scraping ChatGPT.py has begun."])
    "ChatGPT を利用して自動記事生成"
    ScrapingCGPT.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("Scraping blog sentences from ChatGPT: Done")

  if checkpoint <= 2 and args.end >= 2:
    subprocess.run(["say", "-v", "Daniel", "Upload Image.py has begun."])
    "BingImageCreator を利用して自動画像生成"
    UploadImage.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("Scraping images from BingImageCreator: Done")

  if checkpoint <= 3 and args.end >= 3:
    subprocess.run(["say", "-v", "Daniel", "Post Article.py has begun."])
    "BingImageCreator で取得した画像を縦21:横40の比率にトリミング調整"
    PostArticle.main()
    checkpoint = set_checkpoint(checkpoint + 1)
    print("Trimming images: Done")

  """ 
  if checkpoint <= 4 and args.end >= 4:
    subprocess.run(["say", "-v", "Daniel", "Uploading images to WordPress has begun."])
    "WordPress に画像を投稿"
    sleep(3)
    UploadImage.post_images()
    print("Uploading images to WordPress: Done")

  if checkpoint <= 5 and args.end >= 5:
    subprocess.run(["say", "-v", "Daniel", "Posting articles to WordPress has begun."])
    "WordPress に記事を投稿"
    PostArticle.post_articles()
    print("Posting articles to WordPress: Done")
   """
  if checkpoint == last_endpoint:
    set_checkpoint(0)
  subprocess.run(["say", "-v", "Daniel", "Blog Automation Completed."])
  
if __name__ == "__main__":
  main()
