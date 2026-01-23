def game_master_loop(game, lock):
    while True:
        cmd = input().strip()

        if cmd == "start":
            with lock:
                if game.started:
                    print("Game already started")
                    continue

                if not game.player_list:
                    print("No players connected")
                    continue

                game.start()
                print("Game started")

        elif cmd == "players":
            with lock:
                for p in game.player_list:
                    print(p)

        elif cmd == "quit":
            print("Shutting down server")
            os._exit(0)
