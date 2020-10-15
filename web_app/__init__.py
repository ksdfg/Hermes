import os
import traceback
from functools import wraps
from os.path import join
from threading import Thread
from uuid import uuid4

from decouple import config
from flask import Flask, render_template, session, request
from namesgenerator import get_random_name
from pandas import read_csv

from web_app import whatsapp as meow

# create flask app and set a secret key for it to use to hash session variables
app = Flask(__name__)
app.secret_key = config('secret')

# dictionary to store all the webdriver objects created in each session
driver = {}


def endpoint(func):
    """
    Execute all the code in a safe environment, and tell demons to begone on error
    :param func: The function mapped to the route
    :return: decorated function
    """

    @wraps(func)
    def inner(*args, **kwargs):
        """
        Try to execute an endpoint function, and return rendered error page on exception raise
        :param args: Arguments passed to the endpoint function
        :param kwargs: Keyword Argumentes passed to the endpoint function
        :return: function executing endpoint function safely
        """
        try:
            return func(*args, **kwargs)
        except:
            traceback.print_exc()
            return render_template('begone.html')  # error page

    return inner


@app.route('/')
@endpoint
def home():
    """
    Homepage - shows login details
    :return: rendered index.html
    """
    return render_template('index.html')


@app.route('/form')
@endpoint
def form():
    """
    display message details form
    :return: rendered HTML page of the form
    """
    session['username'] = get_random_name()  # set username for session
    print(session['username'], "logged in")
    return render_template('form.html', **session)


@app.route('/submit', methods=['POST'])
@endpoint
def submit_form():
    """
    Handle form submission
    :return: rendered loading page while driver fetches QR code
    """
    # save uploaded file locally
    filename = f"{uuid4()}.csv"
    request.files['file'].save(join("/Hermes", filename))

    # set info as session variables since they need to be accessed later, and are different for each session
    session['file'] = filename  # path to local csv containing participants' data
    session['ids'] = request.form['ids']  # the ids (space separated) who are to be contacted
    session['log_phone'] = request.form['log_phone']
    session['content'] = request.form['content']

    return render_template('loading.html', target='/qr')  # show loading page while selenium opens whatsapp web


@app.route('/qr')
@endpoint
def qr():
    """
    display QR code to scan
    :return: rendered web page with the QR code
    """
    print('starting driver session for ' + session['username'])  # logging to server terminal

    # store the created WhatsApiDriver object in driver dict
    # key - username of currently logged in user | value - webdriver object
    driver[session['username']], qr_img = meow.start_web_session()

    # the rendered HTML form, qr.html, automatically redirects to /send, which will load only once QR code is scanned,
    # the user is logged into whatsapp web and Hermes starts sending messages on whatsapp
    return render_template('qr.html', qr=qr_img)


@app.route('/send', methods=['POST', 'GET'])
@endpoint
def send():
    """
    start sending messages on whatsapp
    :return: rendered form with the `Sending Messages!` alert
    """
    # wait till user is logged into whatsapp
    meow.wait_till_login(driver[session['username']])
    print(session['username'], "logged into whatsapp")

    # check if log number exists
    if not meow.check_if_number_exists(driver[session['username']], session['log_phone']):
        print(session['username'], "gave invalid phone number for logging")

        # Close driver
        driver[session['username']].close()
        del driver[session['username']]
        print("closed driver for", session['username'])

        # go back to form with error message
        return render_template('form.html', msg="Incorrect number given for logging", **session)

    # start thread that will send messages on whatsapp
    Thread(target=send_messages, kwargs=dict(session)).start()

    # go back to form with a success message
    session['username'] = get_random_name()
    print(session['username'], "logged in")
    return render_template('form.html', msg="Sending Messages!")


def send_messages(content, file, ids, username, log_phone, **kwargs):
    """
    send messages on whatsapp
    :param log_phone: phone number to which results are to be logged
    :param content: The content to be sent as a message
    :param file: path to the CSV file with details
    :param ids: which IDs from that CSV are to be used
    :param username: session username
    :param kwargs: to handle everything else we're getting by dumping session
    """
    messages_sent_to = []  # list to store successes
    messages_not_sent_to = []  # list to store failures

    try:
        # Get data from our uploaded CSV
        api_data = read_csv(file).to_dict(orient='records')
        os.remove(file)  # no need of csv anymore

        # select data of only those participants whose id is in the list of ids given as argument
        if ids != 'all':
            api_data = [user for user in api_data if user['id'] in [int(x) for x in ids.strip().split(' ')]]

        # Send messages to all registrants
        for entry in api_data:
            try:
                print(f"{entry['id']}. {entry['name']} : https://api.whatsapp.com/send?phone=91{entry['phone']}")
                # send message to entry['phone']ber, and then append entry['name'] + whatsapp api link to list of successes
                meow.send_message(entry['phone'], content.replace("{{name}}", entry['name']), driver[username])
                messages_sent_to.append(
                    f"{entry['id']}. {entry['name']} : https://api.whatsapp.com/send?phone=91{entry['phone']}"
                )
            except Exception as e:  # if some error occured
                print("Message could not be sent to", entry['name'])
                print(e)
                # append entry['name'] to list of failures
                messages_not_sent_to.append(
                    f"{entry['id']}. {entry['name']} : https://api.whatsapp.com/send?phone=91{entry['phone']}"
                )

        print(username, "done sending messages!")

    except:  # for general exceptions
        traceback.print_exc()

    finally:
        # log results
        newline = "\n"
        meow.send_message(
            log_phone,
            f"*Messages sent to :*\n{newline.join(messages_sent_to)}\n\n*Messages not sent to :*\n{newline.join(messages_not_sent_to)}",
            driver[username],
        )

        # Close driver
        try:
            driver[username].close()
            del driver[username]
            print("closed driver for", username)
        except:
            pass
