# ![](web_app/static/images/logo.png)

[![Website hermes.ksdfg.me](https://img.shields.io/website-up-down-green-red/http/hermes.ksdfg.me.svg)](https://hermes.ksdfg.me/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://www.github.com/ksdfg/Hermes/graphs/commit-activity)
![GitHub last commit](https://img.shields.io/github/last-commit/ksdfg/hermes)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/ksdfg/hermes)
![GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/ksdfg/hermes)
![GitHub](https://img.shields.io/github/license/ksdfg/hermes)

Web application for sending WhatsApp messages to multiple people at once.

## To setup and run the application

- Set a `secret` as an environment variable, or set in a `.env`.

- Run `docker-compose up --build` to build and start the application.

- The application will be running at `localhost:8080`.

## To send messages

- Click on the __Start__ button to go to the form.

- Fill the form according to the following rules

  - Enter a number to which a list of people who got the message and a 
  list of people who couldn't get the message will be sent. The number must
  be include the country code without the `+`. For example, if your number
  is `987654321` and you're from India (`+91`), then enter `91987654321`.
  
  - Upload a __CSV__ file with three columns (Don't forget to add the cloumn
  headings, which should be exactly as given)
  
    - `id`, which contains a numeric id unique for each entry.
    
    - `name`, which contains the name of the person.
    
    - `phone`, which contains the number to which the message should be sent.
    Follow the same format as the logging phone number.
    
  - Enter which IDs from the CSV you want to send the message to. You can
  either enter the IDs space separated, or just enter `all` to send to all.
  
  - Enter the message you want to send. You can use `{{name}}` as a placeholder
  which will be replaced by the name in the CSV.
  
- Wait for the QR to load on the screen. Once it loads, scan the QR from your
phone. The application will wait till you're logged in, and then start sending
the messages in the background.
