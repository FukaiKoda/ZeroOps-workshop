import os
import socket


def get_username():
    return os.getlogin()


def get_hostname():
    return socket.gethostname()


def get_current_directory():
    return os.getcwd()
