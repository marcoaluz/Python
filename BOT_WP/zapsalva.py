from selenium import webdriver
import time
import os
from selenium.webdriver.chrome.options import Options




dir_path = os.getcwd()
chrome_options = Options()
chrome_options.add_argument(r"user-data-dir=" + dir_path + "profile/zap")
driver = webdriver.Chrome(options = chrome_options)
driver.get('https://web.whatsapp.com/')

time.sleep(120)
