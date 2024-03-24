import json
import mimetypes
import socket
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from threading import Thread
from urllib.parse import urlparse, unquote_plus


class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers.get('Content-Length')))
        self.send_to_server(data)
        self.send_response(302)
        self.send_header('Location', '/message')
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


def run_socket_server(ip='127.0.0.1', port=5000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            raw_data, address = server_socket.recvfrom(1024)
            if raw_data:
                data = unquote_plus(raw_data.decode())
                dict_data = {str(datetime.now()): {key: value.strip() for key, value in [el.split('=') for el in data.split('&')]}}
                save_to_json(dict_data)
            else:
                break
    except KeyboardInterrupt:
        print('Stopping socket server...')
    finally:
        server_socket.close()


def save_to_json(dict_data: dict):
    with open('storage/data.json', 'r+', encoding='utf-8') as file:
        json_data = json.load(file)
        json_data.update(dict_data)
        file.seek(0)
        json.dump(json_data, file, indent=4)


def run_server(server_class=HTTPServer, handler_class=HttpGetHandler):
    server_address = ('127.0.0.1', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        print('Stopping http app...')
    finally:
        http.server_close()


# def main():
#     thread_socket_server = Thread(target=run_socket_server)
#     thread_http_server = Thread(target=run_server)
#     thread_socket_server.start()
#     thread_http_server.start()
#
#     try:
#         thread_socket_server.join()
#         thread_http_server.join()
#     except KeyboardInterrupt:
#         print('KeyboardInterrupt: Stopping servers...')
#         thread_socket_server.join(timeout=1)
#         thread_http_server.join(timeout=1)
#         print('End of the program.')


if __name__ == '__main__':
    # main()
    # thread_socket = Thread(target=run_socket_server)
    # thread_socket.start()
    # run_socket_server()
    # run_server()

    thread_socket_server = Thread(target=run_socket_server)
    thread_http_server = Thread(target=run_server)

    try:
        thread_socket_server.start()
        thread_http_server.start()
    except KeyboardInterrupt:
        print('KeyboardInterrupt: Stopping servers...')
        thread_socket_server.join(timeout=1)
        thread_http_server.join(timeout=1)
        print('End of the program.')
