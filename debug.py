from project_name.user_server import debug
from sys import argv

if __name__ == '__main__':
    if len(argv) < 2:
        # if == 1 means only the script name was given
        raise RuntimeError('Debug must have at least one argument (Database uri)')

    if argv[1] == 'lite':
        debug('sqlite:///'+argv[2])
    else:
        debug(argv[1])
