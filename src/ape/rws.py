import websocket
import threading
import json

DEBUG = False

class WSClient:
    def __init__(self, log, host: str = '127.0.0.1', port: int = 8080, protocol: str = 'ws', route: str = 'ws'):
        self.log = log
        self.ws_host = host
        self.ws_port = port
        self.ws_protocol = protocol
        self.ws_route = route
        self.ws_uri = f'{self.ws_protocol}://{self.ws_host}:{self.ws_port}/{self.ws_route}'
        self.connected = False
        
    def send(self, msg: str):
        try:
            msg = json.dumps(msg)
        except:
            self.log.error(f'Msg is not valid json. Aborting msg send.')
            return
        self.log.debug(f'WSMSG: {msg}')
        self.ws.send(msg)

    def connect(self):
        if DEBUG:
            websocket.enableTrace(True)

        self.ws = websocket.WebSocketApp(self.ws_uri,
                                         on_open=self.on_open,
                                         on_close=self.on_close,
                                         on_message=self.on_message,
                                         on_error=self.on_error)
        
        self.log.debug(f'Create WSClient {self.ws}')

        # self.ws.run_forever(dispatcher=rel)
        # rel.signal(2, rel.abort)  # Keyboard Interrupt
        # rel.dispatch()

        self.wst = threading.Thread(target=self.ws.run_forever)
        self.wst.daemon = True
        self.wst.start()

        #self.ws.run_forever()

        self.log.debug('WSClient running')

    def on_open(self, ws):
        self.connected = True
        self.log.debug(f'WebSocket opened: {ws}')

    def on_close(self, ws):
        self.connected = False
        self.log.debug(f'WebSocket closed: {ws}')

    def on_message(self, ws, msg):
        self.log.debug(f'Received WS Msg: [{ws}] {msg}')

    def on_error(self, ws, msg):
        self.log.error(f'WebSocket Error: [{ws}] {msg}')


if __name__ == "__main__":
    wsc = WSClient()
    wsc.connect()
