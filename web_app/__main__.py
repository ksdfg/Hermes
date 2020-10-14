from waitress import serve

from web_app import app

if __name__ == '__main__':
    print("Starting Hermes")
    serve(app=app, host="127.0.0.1")
