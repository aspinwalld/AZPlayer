import os
from dotenv import load_dotenv
from azplay import app

load_dotenv()

APP_HOST = os.environ.get('APPHOST', '127.0.0.1')
APP_PORT = int(os.environ.get('APPPORT', 8080))
DEBUG = bool(os.environ.get('DEBUG', False))

print(APP_HOST, APP_PORT, DEBUG)

if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=DEBUG)