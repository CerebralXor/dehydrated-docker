#!/usr/bin/env python3

# This is a simple wrapper around the dehydrated command to support using
# environment variables appended with '_FILE' containing a path
# to a file containing the value.

import logging
import os
import subprocess
import sys
import time

ch = logging.StreamHandler()
ch.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

daemon_logger = logging.getLogger('daemon    ')  # Make all logger names 10 characters long so they're nicely tabulated in the output.
daemon_logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
daemon_logger.addHandler(ch)

dehydrated_logger = logging.getLogger('dehydrated')
dehydrated_logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
dehydrated_logger.addHandler(ch)

for key, value in os.environ.items():
    if key.endswith('_FILE') and os.path.isfile(value):
        daemon_logger.info(f'Using contents of {value} for value of {key.split("_FILE")[0]}')
        with open(value) as f:
            os.environ[key.split('_FILE')[0]] = f.read().strip()

interval = int(os.getenv('INTERVAL', 720))  # Default = 12 hours
if 0 < interval < 60:
    daemon_logger.warning(f'{interval} minutes between checking if certificates need renewing is very short. You should only need to check for certificates once or twice a day.')

cmd = ['/usr/bin/env', 'dehydrated', '--domain', os.environ['DOMAIN']] + sys.argv[1:]
daemon_logger.debug('Dehydrated command will be: ' + ' '.join(cmd))

while True:
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8')
    daemon_logger.info('Starting periodic check for certificate renewal...')

    while True:
        realtime_output = process.stdout.readline()
        if realtime_output == '' and process.poll() is not None:
            break
        if realtime_output:
            dehydrated_logger.info(realtime_output.strip())

    if interval:
        daemon_logger.info(f'Waiting {interval} minutes until next check...')
        time.sleep(interval*60)
    else:
        daemon_logger.info('Exiting because the interval is set to 0.')
        break
