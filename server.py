##############################################################################
# server.py
##############################################################################

import socket
import select
import random
import json
import requests
import chatlib  # To use chatlib functions or consts, use chatlib.****

# GLOBALS
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
messages_to_send = []

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# Data Loaders #

def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    users_file_object = open(r"C:\Users\GuyBar\PycharmProjects\networkpy\trivia\u4\users.txt", 'r')
    return eval(users_file_object.read())


users = load_user_database()


def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    questions_file_object = open(r"C:\Users\GuyBar\PycharmProjects\networkpy\trivia\u4\questions.txt", 'r')
    return eval(questions_file_object.read())


def load_questions_from_web():
    url = 'https://opentdb.com/api.php'
    params = {'amount': 50, 'type': 'multiple'}
    response = requests.get(url, params)
    if response.status_code == 200:
        data = json.loads(response.text)
        quests = data['results']
        q_dict = {}
        for i in range(1, 51):
            del quests[i - 1]['type']
            del quests[i - 1]['difficulty']
            del quests[i - 1]['category']
            quests[i - 1]['question'] = quests[i - 1]['question'].replace('#039;', '\'')
            quests[i - 1]['question'] = quests[i - 1]['question'].replace('&quot;', '"')
            quests[i - 1]['question'] = quests[i - 1]['question'].replace('&eacute', 'é')
            quests[i - 1]['correct_answer'] = quests[i - 1]['correct_answer'].replace('#039;', '\'')
            quests[i - 1]['correct_answer'] = quests[i - 1]['correct_answer'].replace('&quot;', '"')
            quests[i - 1]['correct_answer'] = quests[i - 1]['correct_answer'].replace('&eacute', 'é')
            quests[i - 1]['incorrect_answers'] = [i.replace('&quot;', '"') for i in quests[i - 1]['incorrect_answers']]
            quests[i - 1]['incorrect_answers'] = [i.replace('#039;', '\'') for i in quests[i - 1]['incorrect_answers']]
            quests[i - 1]['incorrect_answers'] = [i.replace('&eacute', 'é') for i in quests[i - 1]['incorrect_answers']]
            quests[i - 1]['correct'] = quests[i - 1].pop('correct_answer')
            quests[i - 1]['incorrect_answers'].append(quests[i - 1]['correct'])
            quests[i - 1]['answers'] = quests[i - 1].pop('incorrect_answers')
            random.shuffle(quests[i - 1]['answers'])
            quests[i - 1]['correct'] = quests[i - 1]['answers'].index(quests[i - 1]['correct']) + 1
            q_dict[i] = quests[i - 1]
        return q_dict
    else:
        print(f'Error {response.status_code}')
        return None


questions = load_questions_from_web()


def create_random_question(username):
    global users
    global questions
    if [n for n in range(1, len(questions) + 1) if n not in users[username]["questions_asked"]]:
        rand_num = random.choice(
            [n for n in range(1, len(questions) + 1) if n not in users[username]["questions_asked"]])
        return str(rand_num) + chatlib.DATA_DELIMITER + questions[rand_num]["question"] + chatlib.DATA_DELIMITER + \
            chatlib.DATA_DELIMITER.join(questions[rand_num]["answers"])
    else:
        return None


# HELPER SOCKET METHODS


def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    full_msg = chatlib.build_message(code, msg)
    messages_to_send.append((conn, full_msg))


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket,
    then parses the message using chatlib.
    Parameters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occurred, will return None, None
    """
    full_msg = conn.recv(chatlib.MAX_MSG_LENGTH).decode()
    print("[CLIENT] ", full_msg)  # Debug print
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    print('Setting up server...')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.listen()
    print('Listening for clients...')
    return sock


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: None
    """
    build_and_send_message(conn, 'ERROR', error_msg)


def print_client_sockets(client_sockets):
    for c in client_sockets:
        print('\t', c.getpeername())


##### MESSAGE HANDLING


def handle_question_message(conn, username):
    rand_q_num = create_random_question(username)
    if rand_q_num:
        build_and_send_message(conn, 'YOUR_QUESTION', rand_q_num)
    else:
        build_and_send_message(conn, 'NO_QUESTIONS', '')


def handle_answer_message(conn, username, data):
    global questions

    [q_num, a_num] = list(map(lambda x: int(x), data.split(chatlib.DATA_DELIMITER)))
    if q_num in users[username]["questions_asked"]:
        build_and_send_message(conn, 'ERROR', 'Server has caught you!')
    else:
        if questions[q_num]["correct"] == a_num:
            users[username]["score"] += 5
            build_and_send_message(conn, 'CORRECT_ANSWER', '')
        else:
            build_and_send_message(conn, 'WRONG_ANSWER', str(questions[q_num]["correct"]))
    users[username]["questions_asked"].append(q_num)


def handle_getscore_message(conn, username):
    global users

    user_score = str(users[username]["score"])
    build_and_send_message(conn, 'YOUR_SCORE', user_score)


def handle_highscore_message(conn):
    data_list = []
    for user in users:
        data_list.append((user, users[user]['score']))
    data_list.sort(reverse=True, key=lambda x: x[1])
    n_data_list = list(map(lambda x: x[0] + ': ' + str(x[1]), data_list))
    data = '\n'.join(n_data_list)
    build_and_send_message(conn, 'ALL_SCORE', data)


def handle_logged_message(conn):
    data = ', '.join(list(logged_users.values()))
    build_and_send_message(conn, 'LOGGED_ANSWER', data)


def handle_logout_message(conn):
    """
    Closes the given socket (in laster chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: None
    """
    global logged_users

    del logged_users[conn.getpeername()]
    conn.close()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks  user and pass exists and match.
    If not - sends error and finished. If all ok, sends OK message and adds user and address to logged_users
    Recieves: socket, message code and data
    Returns: None (sends answer to client)
    """
    global users  # This is needed to access the same users dictionary from all functions
    global logged_users  # To be used later

    [username, password] = chatlib.split_data(data, 1)
    if username in users:
        if users[username]['password'] == password:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_ok_msg'], '')
            logged_users[conn.getpeername()] = username
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_failed_msg'], 'Error! Password does not match!')
    else:
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER['login_failed_msg'], 'Error! Username does not exist')


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users  # To be used later

    if not conn.getpeername() in logged_users.keys():
        if cmd == 'LOGIN':
            handle_login_message(conn, data)
        else:
            build_and_send_message(conn, 'ERROR', 'Command is not recognized')
    else:
        if cmd == 'LOGOUT':
            print('Connection closed by client handling', conn.getpeername())
            # client_sockets.remove(current_socket)
            handle_logout_message(conn)
            # print_client_sockets(client_sockets)
        elif cmd == 'MY_SCORE':
            handle_getscore_message(conn, logged_users[conn.getpeername()])
        elif cmd == 'HIGHSCORE':
            handle_highscore_message(conn)
        elif cmd == 'LOGGED':
            handle_logged_message(conn)
        elif cmd == 'GET_QUESTION':
            handle_question_message(conn, logged_users[conn.getpeername()])
        elif cmd == 'SEND_ANSWER':
            handle_answer_message(conn, logged_users[conn.getpeername()], data)
        else:
            build_and_send_message(conn, 'ERROR', 'Command is not recognized')


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions

    print("Welcome to Trivia Server!")

    server_socket = setup_socket()
    client_sockets = []
    global messages_to_send
    while True:
        ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])
        for current_socket in ready_to_read:
            if current_socket == server_socket:
                (client_socket, client_address) = current_socket.accept()
                print('New client joined!', client_address)
                client_sockets.append(client_socket)
                print_client_sockets(client_sockets)
            else:
                try:
                    cmd, data = recv_message_and_parse(current_socket)
                    if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"] or cmd is None:
                        print('Connection closed', current_socket.getpeername())
                        client_sockets.remove(current_socket)
                        if not current_socket.getpeername() in logged_users.keys():
                            current_socket.close()
                        else:
                            handle_logout_message(current_socket)
                        print_client_sockets(client_sockets)
                    else:
                        handle_client_message(current_socket, cmd, data)
                except ConnectionError:
                    print('Connection closed', current_socket.getpeername())
                    client_sockets.remove(current_socket)
                    if not current_socket.getpeername() in logged_users.keys():
                        current_socket.close()
                    else:
                        handle_logout_message(current_socket)
                    print_client_sockets(client_sockets)

        for msg in messages_to_send:
            current_socket, data = msg
            if current_socket in ready_to_write:
                current_socket.send(data.encode())
                print("[SERVER] ", data)  # Debug print
                messages_to_send.remove(msg)


if __name__ == '__main__':
    main()
