# Protocol Constants

CMD_FIELD_LENGTH = 16  # Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4  # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10 ** LENGTH_FIELD_LENGTH - 1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages 
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
    "login_msg": "LOGIN",
    "logout_msg": "LOGOUT"
}  # .. Add more commands if needed

PROTOCOL_SERVER = {
    "login_ok_msg": "LOGIN_OK",
    "login_failed_msg": "ERROR"
}  # ..  Add more commands if needed

# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
    """
    Gets command name (str) and data field (str) and creates a valid protocol message
    Returns: str, or None if error occurred
    """

    if type(cmd) == str and len(cmd) <= CMD_FIELD_LENGTH and type(data) == str and len(data) <= MAX_DATA_LENGTH:
        return cmd + (CMD_FIELD_LENGTH - len(cmd)) * ' ' + DELIMITER + (LENGTH_FIELD_LENGTH - len(str(len(data))))*'0'\
            + str(len(data)) + DELIMITER + data
    return ERROR_RETURN


def parse_message(data):
    """
    Parses protocol message and returns command name and data field
    Returns: cmd (str), data (str). If some error occurred, returns None, None
    """

    cmd, msg = ERROR_RETURN, ERROR_RETURN
    if type(data) == str and data.count(DELIMITER) == 2 and MAX_MSG_LENGTH >= len(data) >= MSG_HEADER_LENGTH:
        s_data = data.split(DELIMITER)
        c, l, d = s_data
        """
        s_c = c.split(' ')
        r_s_c = c.split(' ')
        r_s_c.remove(s_c[0])
        if not l.replace(' ', '').isnumeric() or s_c[0] == '' or ''.join(r_s_c) != '' or \
                not c.replace(' ', '').replace('_', '').isupper():
            return cmd, msg
        """
        if not l.replace(' ', '').isnumeric() or not c.replace(' ', '').replace('_', '').isupper():
            return cmd, msg
        if len(c) == CMD_FIELD_LENGTH and len(l) == LENGTH_FIELD_LENGTH and len(d) == int(l.replace(' ', ''))\
                and int(l) <= MAX_DATA_LENGTH:
            cmd = s_data[0].replace(' ', '')
            msg = s_data[2]
    return cmd, msg


def split_data(msg, expected_fields):
    """
    Helper method. gets a string and number of expected fields in it. Splits the string
    using protocol's data field delimiter (|#) and validates that there are correct number of fields.
    Returns: list of fields if all ok. If some error occurred, returns None
    """

    if msg.count(DATA_DELIMITER) == expected_fields:
        return msg.split(DATA_DELIMITER)
    return [ERROR_RETURN]


def join_data(msg_fields):
    """
    Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter.
    Returns: string that looks like cell1#cell2#cell3
    """

    return DATA_DELIMITER.join(map(lambda x: str(x), msg_fields))
