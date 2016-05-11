import argparse
import os
import log

TESTS_DIR = 'tests'

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Makes files for a test number.')
    arg_parser.add_argument('test_numbers', type=int, nargs='*', help='Test number')
    args = arg_parser.parse_args()
    for test_number in args.test_numbers:
        if os.path.exists(os.path.join(TESTS_DIR, 'test-{}.txt'.format(test_number))):
            log.error('test-{}.txt already exists.'.format(test_number))
        else:
            f = open(os.path.join(TESTS_DIR, 'test-{}.txt'.format(test_number)), 'w')
            f.close()
            log.success('Created test-{}.txt'.format(test_number))
        if os.path.exists(os.path.join(TESTS_DIR, 'start-{}.kwld'.format(test_number))):
            log.error('start-{}.kwld already exists.'.format(test_number))
        else:
            f = open(os.path.join(TESTS_DIR, 'start-{}.kwld'.format(test_number)), 'w')
            f.close()
            log.success('Created start-{}.kwld'.format(test_number))
        if os.path.exists(os.path.join(TESTS_DIR, 'end-{}.kwld'.format(test_number))):
            log.error('end-{}.kwld already exists.'.format(test_number))
        else:
            f = open(os.path.join(TESTS_DIR, 'end-{}.kwld'.format(test_number)), 'w')
            f.close()
            log.success('Created end-{}.kwld'.format(test_number))
