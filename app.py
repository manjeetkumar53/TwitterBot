import traceback
import sys
from selenium.webdriver.support import ui
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

class TwitterBot:
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.bot = webdriver.Firefox()
    
    def login(self):
        bot = self.bot
        bot.get('https://twitter.com/login')
        bot.maximize_window()
        email = bot.find_element_by_class_name("js-username-field")
        password = bot.find_element_by_class_name("js-password-field")
        
        #email.clear()
        #password.clear()
        empty_val   = ""
        #bot.execute_script('document.getElementsByClassName("js-username-field")[0].value=''')
        email.send_keys(self.username)
        password.send_keys(self.password)
        time.sleep(5)
        bot.find_element_by_class_name("EdgeButtom--medium").click()

    def like_tweet(self,hashtag):
        bot = self.bot
        bot.get('https://twitter.com/search?q='+hashtag+'&src=typeahead_click')
        time.sleep(3)
        for i in range(1,3):
            bot.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            time.sleep(3)
            tweets = bot.find_elements_by_class_name('tweet')
            links = [elem.get_attribute('data-permalink-path') for elem in tweets]
            print(links)
            for link in links:
                print(link)
                bot.get('https://twitter.com/'+link)
                try:
                    bot.find_element_by_class_name('HeartAnimation').click()
                    time.sleep(10)
                except Exception as ex:
                    time.sleep(60)

        
ed = TwitterBot("youemail@mail.com","yourpass")#please provide ur twitter username & password here
ed.login()
#time.sleep(5)
ed.like_tweet("machinelearning")
