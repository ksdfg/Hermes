from base64 import b64encode
from os import remove
from os.path import isfile
from time import sleep

import requests
from decouple import config
from webwhatsapi import WhatsAPIDriver


# get all data of all participants from GET call to passed url
def get_data(url, table, headers, ids):
    """
    Get list of names and numbers
    :param url: GET call to this url will return data of all participants from a certain event table
    :param table: the event table from which participant data is to be returned
    :param headers: contain the credentials of currently logged in user as a base64 encoded string in the format
    `username|password`, which is stored in header as the value to the key `Credentials`
    :param ids: list of ids to be contacted
    :return: two lists - first with all the names, second with all the numbers
    """

    names_list = []  # List of all names
    numbers_list = []  # List of all numbers

    # Get data of participants from a certain event table
    api_data = requests.get(url=url, params={'table': table}, headers=headers).json()
    if ids != 'all':
        # select data of only those participants whose id is in the list of ids given as argument
        api_data = [user for user in api_data if user['id'] in ids]

    # Add names and numbers to respective lists
    for user in api_data:
        names_list.append(user['name'])
        numbers_list.append(user['phone'].split('|')[-1])

    return names_list, numbers_list


# Method to start a new session of WhatsApp Web for web app
def start_web_session():
    # create driver object with above options
    driver = WhatsAPIDriver(client="remote", command_executor=config("SELENIUM"))

    # Get the qr code
    qr_image_path = driver.get_qr()
    with open(qr_image_path, 'rb') as image:
        qr = b64encode(image.read()).decode('utf-8')

    if isfile(qr_image_path):
        remove(qr_image_path)

    return driver, qr  # returning the driver object and qr


def wait_till_login(driver):
    # wait till user is logged into whatsapp web
    login_status = False
    while not login_status:
        print("Wait for login...")
        try:
            login_status = driver.wait_for_login()
        except:
            continue


# Method to send a message to someone
def send_message(num: int, name: str, msg: str, driver: WhatsAPIDriver):
    """

    :param num: phone number to which message is to be sent
    :param name: name(s) of participant(s)
    :param msg: the message to be sent
    :param driver: WhatsApidDiver object using which whatsapp web is to be operated
    :return: string with name and link to chat
    """

    print(f"{name} : https://api.whatsapp.com/send?phone=91{num}")

    chat = driver.get_chat_from_phone_number("91" + str(num), createIfNotFound=True)  # get chat with user
    chat.send_message(msg)  # send message

    sleep(2)  # Just so that we can supervise, otherwise it's too fast

    return f"{name} : https://api.whatsapp.com/send?phone=91{num}"
