# Purpose of this file

This file describes how the interactions between the client and the server should be.
It is important to follow the conventions defined here to ensure a proper functioning of the two.
The communication is ensured by messages in form of string with variables elements in them. We explain how to read them bellow.

### How to read/write the messages 

A message sent by the client is preceded by a `'C'` while those of the servers while use a `'S'`.
eg. `C"USERNAME 'lamsade is cool'"` means that the client sends the the server the string `"USERNAME 'lamsade is cool'"`. 
We define the following convention :
- Words that are all caps indicates what the message is about. eg. "USERNAME" is used to communicate about the username and "SCORE" about the score.
- `"<arg>"` in a message indicates a mandatory argument in the message.
- `"[arg]"` in a message indicated an optional argument in the message.

## Protocols

### Initial connection

When the client first connects to the server, it needs a username to be identified on the leaderboard.
Here is the protocol for this:

`C"USERNAME <username>"`

If the username is available: `S"USERNAME ok"`
If the username is already taken: `S"USERNAME taken"`

### Game protocol

This section describes all protocols needed for a game to take place

#### Game invite

To join a game the client sends `C"GAME"` answered by `S"GAME ok"` if no issues happen or `S"GAME unavailable` otherwise.
With a `S"GAME ok"` the client waits for the game to start. `S"GAME unavailable` should display an error window for the client.

#### Game start

When the game starts the server sends to all clients in the game `S"GAME start <nb_round>` where `nb_round` is the number of functions to guess.

#### Function communication

When a game starts we need to communicate the function to the client to allow score computation and display for the interface.
Another option is to handle only the function on the server (which is cool the avoid cheater but let's consider that the player are not hackers) but would probably require a lot of computing power on the server side.

The protocol is yet to define. We can either find on over the internet (I guess) or build one ourselves. In any case, we should probably adapt it to how we generate the functions. We could also send just a seed an let the client compute the function but it seems a bit more risky

#### Scoring

When all the steps are done for a function, the concerned client sends `C"SCORE <current_value>` where `current_value` is the function value obtained at the last step (could also be the best one found but it creates a bit of strategy not to).

When all clients have sent their score, the server computes the ranking and sends to each client `S"SCORE <position> <points>` where `position` is the position in the ranking for this function and `points` is the associated number of points gained.

#### Game end

When the game is over or reset we get a `S"GAME over"` from the server and reset the client's display.