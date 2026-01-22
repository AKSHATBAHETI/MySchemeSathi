from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "I am alive! Bot is running."

def run():
    # Render expects the server to listen on port 0.0.0.0
    # It will assign a port via the PORT environment variable, usually 10000
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()