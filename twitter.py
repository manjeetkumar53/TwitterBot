import os
import sys
import codecs
import pprint

import unittest
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.ui as ui
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PythonOrgSearch(unittest.TestCase):

 def setUp(self):
  self.driver = webdriver.Firefox()

 def test_search_in_python_org(self):
  driver = self.driver
  driver.get("https://twitter.com/login")

  driver.maximize_window()
  
  username = driver.find_element_by_class_name("js-username-field")
  password = driver.find_element_by_class_name("js-password-field")

  username.send_keys("yours@gmail.com")
  password.send_keys("pass")

  wait = ui.WebDriverWait(driver, 5)
  driver.find_element_by_class_name("EdgeButtom--medium").click()


 def tearDown(self):
  #self.driver.close()
  print("close?")

if __name__ == "__main__":
 unittest.main()