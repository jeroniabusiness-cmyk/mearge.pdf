import os
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    # This message will show when you visit the Render URL
    return "Bot is running and staying alive!"

def run():
    # CRITICAL: Render gives a dynamic port. 
    # This line prevents the "Failed to bind to port" error.
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()