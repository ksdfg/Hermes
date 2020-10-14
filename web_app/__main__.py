from waitress import serve

from web_app import app

if __name__ == '__main__':
    print("Starting Hermes")
    serve(app=app, host="0.0.0.0", port=8080)
