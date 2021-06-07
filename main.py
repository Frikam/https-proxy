import logging
import socket
import sys
import traceback
from _thread import *

def main():
    global listen_port, buffer_size, max_conn

    listen_port = 3002
    logging.basicConfig(level=logging.INFO)

    max_conn = 5
    buffer_size = 8192
    try:
        # AF --- AddressFamily, SOCK --- SocketKind
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', listen_port))
        s.listen(max_conn)
        logging.info("[*] Инициализация сокета... Выполнено.")

        logging.info("[*] Сокет успешно связан... Выполнено.")
        logging.info(f'[*] Сервер успешно запущен [{listen_port}]')
    except Exception as e:
        logging.error(e)
        sys.exit(2)

    while True:
        try:

            conn, addr = s.accept()
            data = conn.recv(buffer_size)
            start_new_thread(get_data, (conn, data, addr))
        except KeyboardInterrupt:
            s.close()
            logging.info("\n[*] Выключение сервера")
            sys.exit(1)

    s.close()


def get_data(conn, data, addr):
    try:
        first_line = str(data).split("\n")[0]
        method_name = first_line.split(" ")[0][2:]
        url = first_line.split(" ")[1]

        http_index = url.find("://")
        if http_index == -1:
            temp = url
        else:
            temp = url[(http_index + 3):]


        webserver_end_index = temp.find("/")
        if webserver_end_index == -1:
            webserver_end_index = len(temp)
        webserver = ""

        port_start_index = temp.find(":")
        port = -1

        # если в адресе не указан порт
        if port_start_index == -1 or webserver_end_index < port_start_index:
            port = 80
            webserver = temp[:webserver_end_index]
        else:
            port = int(temp[(port_start_index + 1):][:webserver_end_index - port_start_index - 1])
            webserver = temp[:port_start_index]


        logging.info(f'Метод {method_name}, адрес сервера {webserver}')
        proxy_server(webserver, port, conn, data, method_name)
    except Exception as e:
        logging.error(e)


def proxy_server(webserver, port, conn, data, method):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.send(data)

        if method == 'CONNECT':
            start_https_tunnel(s, conn)
        else:
            start_http_tunnel(s, conn)
    except Exception as e:
        traceback.print_exc()
        s.close()
        conn.close()
        sys.exit(1)

def start_http_tunnel(client, server):
    while True:
        reply = server.recv(buffer_size)

        if len(reply) > 0:
            client.sendall(reply)
        else:
            break
    server.close()
    client.close()

def start_https_tunnel(client, server):
        try:
            reply = "HTTP/1.1 200 Connection established\r\n"
            reply += "ProxyServer-agent: PyProxyServer\r\n\r\n"
            client.sendall(reply.encode())
        except socket.error as err:
            print(err)

        client.setblocking(False)
        server.setblocking(False)
        while True:
            try:
                data = client.recv(buffer_size)
                if not data:
                    client.close()
                    break
                server.sendall(data)
            except socket.error:
                pass
            try:
                reply = server.recv(buffer_size)
                if not reply:
                    server.close()
                    break
                client.sendall(reply)
            except socket.error:
                pass

if __name__ == "__main__":
    main()
