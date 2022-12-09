import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Water management')
    subparser = parser.add_subparsers(dest='cmd')

    cmd_pump = subparser.add_parser('status')
    cmd_pump = subparser.add_parser('pump')
    cmd_pump.add_argument('seconds', type=int, nargs='?', default=15)
    args = parser.parse_args()

    print(args) 
