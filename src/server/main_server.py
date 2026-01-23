import socket
import threading
import traceback
import sys
from client_handler import ClientHandler
from game import Game
from game_master import game_master_loop

def handle_client(connection_id, client_socket, addr, game, lock):
    try:
        handler = ClientHandler(connection_id, client_socket, addr, game, lock)
        handler.run()

    except Exception as e:
        print(f"\n=== Exception for client {addr} ===")
        traceback.print_exc()
        print("=== End exception ===\n")

    finally:
        client_socket.close()



def main(port: int, max_connection: int) -> None:
    """
    Accept connections and handle each client in a separate thread
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind(("", port))
    print(f"Binding socket to port {port}")

    server_socket.listen(max_connection)
    print(f"Socket is waiting for connections with a maximum of {max_connection}")

    connection_id = 0

    game_lock = threading.Lock()
    game = Game(dim=1, player_list=[], nb_round=5)

    gm_thread = threading.Thread(
        target=game_master_loop,
        args=(game, game_lock),
        daemon=True
    )
    gm_thread.start()

    try:
        while True:
            client_socket, addr = server_socket.accept()
            print("Got connection from", addr)

            thread = threading.Thread(
                target=handle_client,
                args=(connection_id, client_socket, addr, game, game_lock),
                daemon=True
            )
        
            thread.start()

            connection_id += 1

    except KeyboardInterrupt:
        print("\nServer shutting down")

    finally:
        server_socket.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main_server.py <port> [max_connection]")
        sys.exit(1)

    port = int(sys.argv[1])
    max_connection = int(sys.argv[2]) if len(sys.argv) >= 3 else 20

    main(port, max_connection)
