import socket
import sys
import threading


def receive_loop(sock):
    """
    Receive messages from the server and print them
    """
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from server")
                break
            print("SERVER >", data.decode().strip())
    except Exception as e:
        print("Receive error:", e)


def send(sock, message):
    """
    Send a protocol-compliant client message
    """
    full_message = f'C"{message}"\n'
    print("CLIENT >", full_message.strip())
    sock.sendall(full_message.encode())


def main():
    if len(sys.argv) < 4:
        print("Usage: python test_client.py <host> <port> <username>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    username = sys.argv[3]

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    print("Connected to server")

    receiver = threading.Thread(target=receive_loop, args=(sock,), daemon=True)
    receiver.start()

    send(sock, f"USERNAME {username}")

    print("Type commands:")
    print("  score <value>")
    print("  GAME")
    print("  quit")

    while True:
        cmd = input("> ").strip()

        if cmd == "quit":
            break

        if cmd == "GAME":
            send(sock, "GAME")
            continue

        if cmd.startswith("score "):
            value = cmd.split(" ", 1)[1]
            send(sock, f"SCORE {value}")
        else:
            print("Unknown command")

    sock.close()


if __name__ == "__main__":
    main()
