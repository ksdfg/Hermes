import os
import traceback
from base64 import b64encode as bs
from collections import OrderedDict
from threading import Thread

from decouple import config
from flask import Flask, render_template, session, request, url_for, redirect
from requests import get, post

from web_app import whatsapp as meow
from web_app.telegram import TG

# create flask app and set a secret key for it to use to hash session variables
app = Flask(__name__)
app.secret_key = 'messenger_of_the_gods'

# dictionary to store all the webdriver objects created in each session
driver = {}

tg = TG(config('telebot_api_key'))  # Object used to log data to telegram


# Log messages to tg channel
def log(message, doc=None):
    # If a document has been passed to log function, send it with send_document function
    if doc is None:
        tg.send_message(config('log_channel'), f"<b>Hermes</b>:\n{message}")
    else:
        tg.send_document(config('log_channel'), f"<b>Hermes</b>:\n{message}", doc)


# Wrapper - only execute function if user is logged in
def login_required(func):
    def inner(*args, **kwargs):
        if 'username' in session:  # Since on login the username is set as a session variable
            return func(*args, **kwargs)
        else:
            return render_template('begone.html')  # error page

    return inner


# Homepage - shows login details
@app.route('/')
def home():
    return render_template('index.html')


# login user
@app.route('/login', methods=['POST'])
def login():
    # credentials for the API calls needs to be a base-64 encoded string in the format `username|password`
    # the credentials are sent in the header as value to the key `Credentials`
    headers = {
        'Credentials': bs(str(request.form['username'] + '|' + request.form['password']).encode()),
        'User-Agent': "Hermes/1.0",
    }

    # POST call to `login-api` essentially returns status code 200 only if credentials are valid
    if post(url=config('login-api'), headers=headers, allow_redirects=False).status_code == 200:
        # set session variables - username and the header that were verified in above POST call
        session['username'] = request.form['username']  # username
        session['headers'] = headers  # header stored for use in further API calls

        # log info onto terminal and telegram channel
        print('Logged in ', session['username'])
        log(f"<code>{session['username']}</code> logged in")

        return redirect(url_for('form'))  # redirect user to form upon login

    else:  # if credentials were determined as invalid by `login-api` POST call - status code returned not 200
        return render_template('begone.html')  # error page


# display message details form
@login_required
@app.route('/form')
def form(msg=None):
    # get all events accessible by the user, order in ascending value of event name
    events = OrderedDict(
        sorted(get(url=config('events-api'), headers=session['headers']).json().items(), key=lambda x: x[1])
    )

    # events is the list of all the events that the currently logged in user can access
    return render_template('form.html', events=events, msg=msg)


# display loading page while sending messages
@login_required
@app.route('/submit', methods=['POST'])
def submit_form():
    # set info as session variables since they need to be accessed later, and are different for each session
    session['msg'] = request.form['content']
    session['table'] = request.form['table']  # the event table whose participants are to be contacted
    session['path'] = request.form['path']  # path to local csv containing participants' data
    session['ids'] = request.form['ids']  # the ids (space separated) who are to be contacted

    return render_template('loading.html', target='/qr')  # show loading page while selenium opens whatsapp web


# display qr code to scan
@login_required
@app.route('/qr')
def qr():
    # create a webdriver object, open whatsapp web in the resultant browser and
    # display QR code on client side for user to scan

    print('starting driver session for ' + session['username'])  # logging to server terminal

    # store the created webdriver object in driver dict
    # key - username of currently logged in user | value - webdriver object
    driver[session['username']], qr_img = meow.start_web_session()

    # the rendered HTML form, qr.html, automatically redirects to /send, which will load only once QR code is scanned,
    # the user is logged into whatsapp web and Hermes starts sending messages on whatsapp
    return render_template('qr.html', qr=qr_img)


# start sending messages on whatsapp
@login_required
@app.route('/send', methods=['POST', 'GET'])
def send():
    # wait till user is logged into whatsapp
    meow.wait_till_login(driver[session['username']])
    print(session['username'], "logged into whatsapp")

    # start thread that will send messages on whatsapp
    Thread(target=send_messages, kwargs=dict(session)).start()

    # go back to form with a success message
    # events is the list of all the events that the currently logged in user can access
    return form("Sending Messages!")


# send messages on whatsapp
def send_messages(**kwargs):
    messages_sent_to = []  # list to store successes
    messages_not_sent_to = []  # list to store failures

    try:
        # Get data from our API
        # get_data() returns two lists - first containing names and second containing numbers
        if kwargs['ids'] == 'all':
            names, numbers = meow.get_data(
                config('table-api'), kwargs['table'], kwargs['headers'], 'all', kwargs['path']
            )
        else:
            names, numbers = meow.get_data(
                config('table-api'),
                kwargs['table'],
                kwargs['headers'],
                list(map(lambda x: int(x), kwargs['ids'].strip().split(' '))),
                kwargs['path'],
            )

        # Send messages to all registrants
        for num, name in zip(numbers, names):
            try:
                print(f"{name} : https://api.whatsapp.com/send?phone=91{num}")
                # send message to number, and then append name + whatsapp api link to list of successes
                meow.send_message(num, name, kwargs['msg'], driver[kwargs['username']])
                messages_sent_to.append(f"{name} : https://api.whatsapp.com/send?phone=91{num}")
            except Exception as e:  # if some error occured
                print("Message could not be sent to", name)
                print(e)
                # append name to list of failures
                messages_not_sent_to.append(f"{name} : https://api.whatsapp.com/send?phone=91{num}")

    except:  # for general exceptions
        traceback.print_exc()

    finally:
        # Close driver
        driver[kwargs['username']].quit()
        print('closed driver for ' + kwargs['username'])

        # write all successes and failures to a file
        newline = "\n"
        with open('whatsapp_list.txt', 'w') as file:
            file.write(
                f"Messages sent to :\n{newline.join(messages_sent_to)}\n\n"
                f"Messages not sent to :\n{newline.join(messages_not_sent_to)}"
            )

        # log file of all successes and failures to telegram channel
        tg.send_chat_action(config('log_channel'), 'upload document')
        log(
            f"List of people who received and didn't receive WhatsApp messages during run by user "
            f"<code>{kwargs['username']}</code>",
            "whatsapp_list.txt",
        )
        os.remove('whatsapp_list.txt')  # no need for file once it is sent, delete from server

        print(kwargs['username'], "done sending messages!")
