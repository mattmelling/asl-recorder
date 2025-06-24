import logging
import os
import asyncio
from time import time

class Janitor:

    def __init__(self):
        self._recording_path = os.environ.get('RECORDING_PATH', '/tmp')
        self._recording_ttl = int(os.environ.get('RECORDING_TTL', '3600'))
        self._logger = logging.getLogger('Recorder')

    async def run(self):
        while True:
            await asyncio.sleep(300)
            self._logger.info('Janitor task running')
            now = time()

            for f in os.listdir(self._recording_path):
                fpath = os.path.join(self._recording_path, f)
                stat = os.stat(fpath)

                if now - stat.st_mtime > self._recording_ttl:
                    self._logger.info(f'Deleting {fpath}')
                    os.remove(fpath)
