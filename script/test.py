#!/usr/bin/python

# Runs the language tests.
from collections import defaultdict
from os import listdir
from os.path import abspath, dirname, isdir, isfile, join, realpath, relpath, splitext
import re
from subprocess import Popen, PIPE
import sys
from string import strip

MAGPIE_DIR = dirname(dirname(realpath(__file__)))
TEST_DIR = join(MAGPIE_DIR, 'test')

if sys.platform == 'win32':
    MAGPIE_APP = join(MAGPIE_DIR, 'Debug', 'magpie.exe')
    if not isfile(MAGPIE_APP):
        MAGPIE_APP = join(MAGPIE_DIR, 'Release', 'magpie.exe')
    if not isfile(MAGPIE_APP):
        sys.exit('Cannot find magpie.exe!')
elif sys.platform.startswith('linux'):
    MAGPIE_APP = join(MAGPIE_DIR, '1', 'out', 'Debug', 'magpie')
    if not isfile(MAGPIE_APP):
        MAGPIE_APP = join(MAGPIE_DIR, '1', 'out', 'Release', 'magpie')
    if not isfile(MAGPIE_APP):
        sys.exit('Cannot find magpie!')
elif sys.platform.startswith('darwin'):
    MAGPIE_APP = join(MAGPIE_DIR, 'build', 'Debug', 'magpie')
    if not isfile(MAGPIE_APP):
        MAGPIE_APP = join(MAGPIE_DIR, 'build', 'Release', 'magpie')
    if not isfile(MAGPIE_APP):
        sys.exit('Cannot find magpie!')
else:
    sys.exit('System not supported!')

SKIP_PATTERN = re.compile(r'// skip: (.*)')
NONTEST_PATTERN = re.compile(r'// nontest')
EXPECT_PATTERN = re.compile(r'// expect: (.*)')
EXPECT_ERROR_PATTERN = re.compile(r'// expect error')
EXPECT_ERROR_LINE_PATTERN = re.compile(r'// expect error line (\d+)')
ERROR_PATTERN = re.compile(r'\] Error: ')
ERROR_LINE_PATTERN = re.compile(r'(\d+): ')
EXPECT_EXIT_PATTERN = re.compile(r'// expect exit (\d+)')

passed = 0
failed = 0
skipped = defaultdict(int)
num_skipped = 0;

if sys.platform == 'win32':
    class color:
        GREEN = ''
        RED = ''
        DEFAULT = ''
        PINK = ''
        YELLOW = ''
else:
    class color:
        GREEN = '\033[32m'
        RED = '\033[31m'
        DEFAULT = '\033[0m'
        PINK = '\033[91m'
        YELLOW = '\033[33m'

def print_line(line=None):
    # Erase the line.
    print '\033[2K',
    # Move the cursor to the beginning.
    print '\r',
    if line:
        print line,
        sys.stdout.flush()

def walk(dir, callback):
    """ Walks [dir], and executes [callback] on each file. """
    dir = abspath(dir)
    for file in [file for file in listdir(dir) if not file in [".",".."]]:
        nfile = join(dir, file)
        if isdir(nfile):
            walk(nfile, callback)
        else:
            callback(nfile)


def run_test(path):
    global passed
    global failed
    global skipped
    global num_skipped

    if (splitext(path)[1] != '.mag'):
        return

    # Check if we are just running a subset of the tests.
    if len(sys.argv) == 2:
        this_test = relpath(path, join(MAGPIE_DIR, 'test'))
        if not this_test.startswith(sys.argv[1]):
            return

    # Make a nice short path relative to the working directory.
    path = relpath(path)

    # Read the test and parse out the expectations.
    expect_output = []
    expect_error = []
    expect_return = 0

    print_line('Passed: ' + color.GREEN + str(passed) + color.DEFAULT +
               ' Failed: ' + color.RED + str(failed) + color.DEFAULT +
               ' Skipped: ' + color.YELLOW + str(num_skipped) + color.DEFAULT)

    i = 1
    with open(path, 'r') as file:
        for line in file:
            match = SKIP_PATTERN.search(line)
            if match:
                num_skipped += 1
                skipped[match.group(1)] += 1
                return

            match = NONTEST_PATTERN.search(line)
            if match:
                # Not a test file at all, so ignore it.
                return

            match = EXPECT_PATTERN.search(line)
            if match:
                expect_output.append((match.group(1), i))

            match = EXPECT_ERROR_PATTERN.search(line)
            if match:
                expect_error.append(i)
                # If we expect compile errors in the test, it should return
                # exit code 1.
                expect_return = 1

            match = EXPECT_ERROR_LINE_PATTERN.search(line)
            if match:
                expect_error.append(int(match.group(1)))
                # If we expect compile errors in the test, it should return
                # exit code 1.
                expect_return = 1

            match = EXPECT_EXIT_PATTERN.search(line)
            if match:
                expect_return = int(match.group(1))

            i += 1

    # Invoke magpie and run the test.
    proc = Popen([MAGPIE_APP, path], stdout=PIPE, stderr=PIPE)
    (out, err) = proc.communicate()
    (out, err) = out.replace('\r\n', '\n'),  err.replace('\r\n', '\n')

    fails = []

    # Validate that no unexpected errors occurred.
    if expect_return == 1 and err != '':
        lines = err.split('\n')
        while len(lines) > 0:
            line = lines.pop(0)
            match = ERROR_PATTERN.search(line)
            if match:
                next_line = lines.pop(0)
                match = ERROR_LINE_PATTERN.search(next_line)
                if match and float(match.group(1)) in expect_error:
                    # Discard the error highlighting line.
                    lines.pop(0)
                else:
                    fails.append('Unexpected error:')
                    fails.append(next_line)
            elif line != '':
                fails.append('Unexpected output on stderr:')
                fails.append(line)
    else:
        for line in expect_error:
            fails.append('Expected error on line ' + str(line) + ' and got none.')

    # Validate the exit code.
    if proc.returncode != expect_return:
        fails.append('Expected return code {0} and got {1}.'.
            format(expect_return, proc.returncode))

    # Validate the output.
    expect_index = 0

    # Remove the trailing last empty line.
    out_lines = out.split('\n')
    if out_lines[-1] == '':
        del out_lines[-1]

    for line in out_lines:
        if expect_index >= len(expect_output):
            fails.append('Got output "{0}" when none was expected.'.
                format(line))
        elif expect_output[expect_index][0] != line:
            fails.append('Expected output "{0}" on line {1} and got "{2}".'.
                format(expect_output[expect_index][0],
                       expect_output[expect_index][1], line))
        expect_index += 1

    while expect_index < len(expect_output):
        fails.append('Missing expected output "{0}" on line {1}.'.
            format(expect_output[expect_index][0],
                   expect_output[expect_index][1]))
        expect_index += 1

    # Display the results.
    if len(fails) == 0:
        passed += 1
        #print color.GREEN + 'PASS' + color.DEFAULT + ': ' + path
    else:
        failed += 1
        print_line(color.RED + 'FAIL' + color.DEFAULT + ': ' + path)
        print
        for fail in fails:
            print '     ', color.PINK + fail + color.DEFAULT
        print

walk(TEST_DIR, run_test)

print_line()
if failed == 0:
    print 'All ' + color.GREEN + str(passed) + color.DEFAULT + ' tests passed.'
else:
    print (color.GREEN + str(passed) + color.DEFAULT + ' tests passed. ' +
           color.RED + str(failed) + color.DEFAULT + ' tests failed.')

for key in sorted(skipped.keys()):
    print ('Skipped ' + color.YELLOW + str(skipped[key]) + color.DEFAULT +
           ' tests: ' + key)
