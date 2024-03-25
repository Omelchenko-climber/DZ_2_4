import json
import os
import mimetypes
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread, Event
from urllib.parse import urlparse, unquote_plus


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length')))
        self.send_to_server(data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        match url.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file_path = Path(url.path[1:])
                if file_path.exists():
                    self.send_static(str(file_path))
                else:
                    self.send_html('error.html', 404)

    def send_html(self, html_filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(html_filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, static_filename):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(static_filename, 'rb') as f:
            self.wfile.write(f.read())

    def send_to_server(self, raw_data, ip='127.0.0.1', port=5000):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server = ip, port
        client_socket.sendto(raw_data, server)
        client_socket.close()


def run_socket_server(event: Event, ip='127.0.0.1', port=5000):
    print('Socket is working...')
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)

    while not event.is_set():
        raw_data, address = server_socket.recvfrom(1024)
        data = unquote_plus(raw_data.decode())
        dict_data = {str(datetime.now()): {key: value.strip() for key, value in [el.split('=') for el in data.split('&')]}}
        save_to_json(dict_data)

    server_socket.close()
    print('Stopping socket server...')


def check_existing():
    if not os.path.exists('storage'):
        os.mkdir('storage')
        with open('storage/data.json', 'w') as file:
            json.dump({}, file)


def save_to_json(dict_data: dict):
    check_existing()
    with open('storage/data.json', 'r+', encoding='utf-8') as file:
        json_data = json.load(file)
        json_data.update(dict_data)
        file.seek(0)
        json.dump(json_data, file, indent=4)


def run_web_server(event: Event, server_class=HTTPServer, handler_class=HttpGetHandler):
    print('Web server is working...')
    server_address = ('127.0.0.1', 3000)
    http = server_class(server_address, handler_class)

    while not event.is_set():
        http.handle_request()

    http.server_close()
    print('Stopping web server...')


def main():
    event = Event()
    thread_web_server = Thread(target=run_web_server, args=(event, ))
    thread_socket_server = Thread(target=run_socket_server, args=(event, ))

    try:
        thread_web_server.start()
        thread_socket_server.start()
        thread_web_server.join()
        thread_socket_server.join()
    except KeyboardInterrupt:
        event.set()
        print('Stopping servers...')

    print('End of the program.')


if __name__ == '__main__':
    main()
