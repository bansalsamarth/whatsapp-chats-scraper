"""
Selenium based scraper to extract data from WhatsApp chats.
"""

import time, csv
import os
from bs4 import BeautifulSoup

import pandas as pd

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


#initial setup
driver = webdriver.Chrome()

#login to WhatsApp web
driver.get("https://web.whatsapp.com/")

#scan QR code from phone
wait = WebDriverWait(driver, 600)


def output_to_csv(data, filename):
    with open(filename, "wb") as f:
        writer = csv.writer(f)
        writer.writerows(data)


def locate_chat(name):
    """Find the chat with a given name in WhatsApp web and
    click on that chat
    """
    x_arg = '//span[contains(@title, '+ '"' +name + '"'+ ')]'
    print(x_arg)
    person_title = wait.until(EC.presence_of_element_located((
        By.XPATH, x_arg)))
    print(person_title)
    person_title.click()


def scroll_to_top():
    """Scrolls to the top of the chat currently open in the WhatsApp Web
    interface
    """
    chats = driver.find_elements_by_class_name("vW7d1")
    third_chat = chats[2].get_attribute('innerHTML')

    #test to identify that program has reached at top of the chat
    while 'Messages you send' not in third_chat:
        print ("Number of chats before scrolling : ", len(chats))

        #scroll to the current top chat in browser
        top = chats[0]
        driver.execute_script("arguments[0].scrollIntoView(true);", top)
        time.sleep(2)

        #get new chat conversations after scrolling to top
        chats = driver.find_elements_by_class_name("vW7d1")
        num_chats_after_scroll = len(chats)

        print ("Number of chats after scrolling : ", len(chats), "\n")
        third_chat = chats[2].get_attribute('innerHTML')

    return chats


def process_chat(chat):
    """Parse the parameter (html for chat message) to extract data
    """

    message_type = ""

    check_image = chat.find('div', class_='_3v3PK')
    check_video = chat.find('div', class_='_1opHa video-thumb')
    check_admin = '_3rjxZ' in chat['class']
    check_deleted_msg = chat.find('div', class_='_1fkCN')
    check_document = chat.find('a', class_='_1vKRe')

    #not unique - same class for deleted message text as well
    check_waiting_message = chat.find('div', class_='_3zb-j ZhF0n _18dOq')


    check_whatsapp_audio_1 = chat.find('div', class_='_3_7SH _17oKL message-in')
    check_whatsapp_audio_2 = chat.find('div', class_='_3_7SH _17oKL message-in tail')

    check_sound_clip_1 = chat.find('div', class_='_3_7SH _1gqYh message-in')
    check_sound_clip_2 = chat.find('div', class_='_3_7SH _1gqYh message-in tail')

    check_gif = chat.find('span', {'data-icon':'media-gif'})

    chat_text = ""

    if check_video:
        message_type = "video"

    elif check_image:
        message_type = "image"
        try:
            chat_text = chat.find('span', class_='selectable-text invisible-space copyable-text').text
        except:
            chat_text = ""

    elif check_admin==True:
        message_type = "admin"
        chat_text =  chat.text

    elif check_deleted_msg:
        message_type = "deleted_message"

    elif check_document:
        message_type = "document"

    elif check_waiting_message:
        chat_text = check_waiting_message.text

    elif check_whatsapp_audio_1 or check_whatsapp_audio_2:
        message_type = 'whatsapp_audio'

    elif check_sound_clip_1 or check_sound_clip_2:
        message_type = 'sound_clip'

    elif check_gif:
        message_type = 'gif'

    else:
        message_type = "text"
        try:
            chat_text = chat.find('div', class_='copyable-text').text
        except:
            print ("error: ", chat, "\n\n\n")
            return chat

    try:
        sender_number = chat.find('span', class_="RZ7GO").text
    except:
        sender_number = "NA"

    try:
        chat_time = chat.find('span', class_='_3EFt_').text
    except:
        chat_time = "NA"


    try:
        chat_datetime = chat.find('div', class_='copyable-text')['data-pre-plain-text']
    except:
        chat_datetime = "NA"

    try:
        chat_msg = chat.find('div', class_='_3zb-j ZhF0n').text
    except:
        chat_msg = "NA"

    try:
        sender_name = chat.find('span', class_='_3Ye_R _1wjpf _1OmDL').text
    except:
        sender_name = "NA"

    try:
        #urls = list(set(re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', str(chat))))
        urls = list(set([a['href'] for a in chat.find_all('a')]))

    except:
        print ("urls extraction issue")
        urls = []

    return [chat.encode('utf-8'), message_type, unicode(chat_text).encode('utf-8'), sender_number, chat_time, chat_datetime, sender_name.encode('utf-8'), str(urls)]

def run_scraper():

    group_data = pd.read_csv('group_details.csv')
    group_data = pd.read_csv('group_details.csv', header=None)
    group_id = len(group_data)+1

    group_data = group_data.values.tolist()

    message_window = driver.find_element_by_id('main')
    data = message_window.get_attribute('innerHTML')

    raw_html_file = open("raw_" + str(group_id) + ".html", "w")
    raw_html_file.write(unicode(data).encode('utf-8'))
    raw_html_file.close()

    soup = BeautifulSoup(data)
    chats = soup.find_all('div', class_='vW7d1')
    print ("chats...", len(chats))


    #get group details
    group_name =  BeautifulSoup(driver.find_element_by_xpath('//*[@id="main"]/header/div[2]/div[1]/div').get_attribute('innerHTML')).find('span')['title']
    #open_group_details
    driver.find_element_by_class_name('_1WBXd').click()
    group_created_at = driver.find_element_by_class_name('Cpiae').get_attribute('innerHTML')
    driver.find_element_by_xpath('//*[@id="app"]/div/div/div[1]/div[3]/span/div/span/div/header/div/div[1]/button/span').click()

    group_details =  [group_name.encode('utf-8'), group_created_at, group_id]
    print (group_details)

    group_data.append(group_details)
    output_to_csv(group_data, 'group_details.csv')

    #process chat data
    chat_data = []
    for i in chats:
        parsed_chat = process_chat(i)
        chat_data.append([group_id, group_name.encode('utf-8'),group_created_at] + parsed_chat)

    print ("chat_data ready...")
    output_to_csv(chat_data, 'scraped_data/' + str(group_id) +  '.csv')
    print ("process complete: ", str(group_id) +  '.csv')
