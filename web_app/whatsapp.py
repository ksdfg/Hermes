from base64 import b64encode
from os import remove
from os.path import isfile
from typing import Tuple

from decouple import config

from webwhatsapi import WhatsAPIDriver


def start_web_session() -> Tuple[WhatsAPIDriver, str]:
    """
    Method to start a new session of WhatsApp Web for web app
    :return: returning the driver object and qr
    """
    # create driver object with above options
    driver = WhatsAPIDriver(client="remote", command_executor=config("SELENIUM"))

    # Get the qr code
    qr_image_path = driver.get_qr()
    with open(qr_image_path, 'rb') as image:
        qr = b64encode(image.read()).decode('utf-8')

    if isfile(qr_image_path):
        remove(qr_image_path)

    return driver, qr


def wait_till_login(driver: WhatsAPIDriver):
    """
    wait till user is logged into whatsapp web
    :param driver: WhatsApiDriver object in which user is trying to login
    """
    login_status = False
    while not login_status:
        print("Wait for login...")
        try:
            login_status = driver.wait_for_login(timeout=5)
        except:
            continue


def send_message(num: int, msg: str, driver: WhatsAPIDriver):
    """
    Method to send a message to someone
    :param num: phone number to which message is to be sent
    :param msg: the message to be sent
    :param driver: WhatsApidDiver object using which whatsapp web is to be operated
    :return: string with name and link to chat
    """
    # get chat with user
    chat = driver.get_chat_from_phone_number(str(num), createIfNotFound=True)

    chat.send_message(msg)  # send message
