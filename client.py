import argparse
import socket
import json

import config


def cmd_pump(args):
    return {
        'command': 'pump',
        'data': {
            'auto': args.auto,
            'duration': args.seconds,
            'pump': 'pump 1',
        }
    }


def cmd_status(args):
    return {'command': 'status'}


def message(packet):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((config.HOST, config.PORT))
        data = json.dumps(packet).encode()
        s.sendall(data)
        data = s.recv(1024)
    return data.decode('utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Water management')
    subparser = parser.add_subparsers(dest='cmd')

    sub_status = subparser.add_parser('status')

    sub_pump = subparser.add_parser('pump')
    sub_pump.add_argument('seconds', nargs='?', default=15)
    
    args = parser.parse_args()

    if 'seconds' in args:
        if args.seconds.isdecimal():
            args.seconds = int(args.seconds)
            args.auto = False
        else:
            args.seconds = 0
            args.auto = True
    
    packet = locals()['cmd_' + args.cmd](args)
    print(message(packet))
