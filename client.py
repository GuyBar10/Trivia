import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****

SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678
login_ok = False

# HELPER SOCKET METHODS


def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message.
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    send_msg = chatlib.build_message(code, data)
    conn.send(send_msg.encode())


def recv_message_and_parse(conn):
    """
    Receives a new message from given socket,
    then parses the message using chatlib.
    Parameters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If error occurred, will return None, None
    """
    full_msg = conn.recv(chatlib.MAX_MSG_LENGTH).decode()
    cmd, data = chatlib.parse_message(full_msg)
    return cmd, data


def build_send_recv_parse(conn, cmd, data):
    build_and_send_message(conn, cmd, data)
    return recv_message_and_parse(conn)


def get_score(conn):
    cmd, data = build_send_recv_parse(conn, 'MY_SCORE', '')
    if cmd == 'YOUR_SCORE':
        print('Your score is %s' % data)
    elif cmd == chatlib.PROTOCOL_SERVER['login_failed_msg']:
        error_and_exit(data)
    else:
        print('something went wrong')


def get_highscore(conn):
    cmd, data = build_send_recv_parse(conn, 'HIGHSCORE', '')
    if cmd == 'ALL_SCORE':
        print(data)
    elif cmd == chatlib.PROTOCOL_SERVER['login_failed_msg']:
        error_and_exit(data)
    else:
        print('something went wrong')


def play_question(conn):
    global login_ok
    valid_input = False
    cmd1, data1 = build_send_recv_parse(conn, 'GET_QUESTION', '')
    s_data1 = data1.split(chatlib.DATA_DELIMITER)
    q_num = s_data1[0]
    cmd2, data2 = '', ''
    if cmd1 == 'YOUR_QUESTION':
        print('Q: ' + s_data1[1] + ':\n' + 2 * '\t' + '1. ' + s_data1[2] + '\n' + 2 * '\t' + '2. ' + s_data1[3] +
              '\n' + 2 * '\t' + '3. ' + s_data1[4] + '\n' + 2 * '\t' + '4. ' + s_data1[5])
        while not valid_input:
            answer = input('Please choose an answer [1-4]: ')
            if answer in ['1', '2', '3', '4']:
                cmd2, data2 = build_send_recv_parse(conn, 'SEND_ANSWER', q_num + chatlib.DATA_DELIMITER + answer)
                valid_input = True
            elif answer == '':
                logout(conn)
                login_ok = False
                break
            else:
                print('Not a valid input!')
        if cmd2 == 'CORRECT_ANSWER':
            print('YES!!!!')
        elif cmd2 == 'WRONG_ANSWER':
            print('Nope, correct answer is ' + chatlib.DATA_DELIMITER + data2)
        elif cmd2 == '':
            print()
        else:
            error_and_exit('Error - the expected code was not received')
    elif cmd1 == 'NO_QUESTIONS':
        print('Game Over!')
    elif cmd1 == chatlib.PROTOCOL_SERVER['login_failed_msg']:
        error_and_exit(data1)
    else:
        print('something went wrong')


def get_logged_users(conn):
    cmd, data = build_send_recv_parse(conn, 'LOGGED', '')
    if cmd == 'LOGGED_ANSWER':
        print(data)
    elif cmd == chatlib.PROTOCOL_SERVER['login_failed_msg']:
        error_and_exit(data)
    else:
        print('something went wrong')


def connect():
    con_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con_socket.connect((SERVER_IP, SERVER_PORT))
    print('Connecting to ' + SERVER_IP + ' port ' + str(SERVER_PORT))
    return con_socket


def error_and_exit(error_msg):
    print(error_msg)
    exit()


def login(conn):
    global login_ok
    cmd = ''
    while cmd != chatlib.PROTOCOL_SERVER['login_ok_msg']:
        username = input("Please enter username: \n")
        password = input('Please enter password: \n')
        if username == '' or password == '':
            logout(conn)
            break
        else:
            build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"],
                                   username + chatlib.DATA_DELIMITER + password)
            cmd, data = recv_message_and_parse(conn)
            if cmd == chatlib.PROTOCOL_SERVER['login_ok_msg']:
                print('Logged in !')
                login_ok = True
            elif cmd == chatlib.PROTOCOL_SERVER['login_failed_msg']:
                print(data)
            else:
                error_and_exit('something went wrong')


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], '')


def main():
    global login_ok
    try:
        conn_socket = connect()
        login(conn_socket)
        if not login_ok:
            print('Goodbye !')
            conn_socket.close()
        else:
            option = input('p        Play a trivia question\n'
                           's        Get my score\n'
                           'h        Get high score\n'
                           'l        Get logged users\n'
                           'q        Quit\n'
                           'Please enter your choice: ')
            while option != 'q' and option != '' and login_ok:
                if option == 'p':
                    play_question(conn_socket)
                elif option == 's':
                    get_score(conn_socket)
                elif option == 'h':
                    print('High-Score table:')
                    get_highscore(conn_socket)
                elif option == 'l':
                    get_logged_users(conn_socket)
                else:
                    print('not an option')
                if not login_ok:
                    break
                option = input('p        Play a trivia question\n'
                               's        Get my score\n'
                               'h        Get high score\n'
                               'l        Get logged users\n'
                               'q        Quit\n'
                               'Please enter your choice: ')
            logout(conn_socket)
            print('Goodbye !')
            conn_socket.close()
    except Exception as e:
        error_and_exit(e)


if __name__ == '__main__':
    main()
