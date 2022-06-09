#!/usr/bin/env python3

import os
import subprocess
import sys

# This is a simple wrapper around the dehydrated command to support using
# environment variables appended with '_FILE' containing a path
# to a file containing the value.

for key, value in os.environ.items():
    if key.endswith('_FILE') and os.path.isfile(value):
        print(f'Using contents of {value} for value of {key.split("_FILE")[0]}')
        with open(value) as f:
            os.environ[key.split('_FILE')[0]] = f.read().strip()

cmd = ['/usr/bin/env', 'dehydrated', '--domain', os.environ['DOMAIN']] + sys.argv[1:]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')

while True:
    realtime_output = process.stdout.readline()

    if realtime_output == '' and process.poll() is not None:
        break

    if realtime_output:
        print(realtime_output.strip(), flush=True)
