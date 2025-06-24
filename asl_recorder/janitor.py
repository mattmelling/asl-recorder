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
            self._logger.info('Janitor task running')
            now = time()

            for f in os.listdir(self._recording_path):
                fpath = os.path.join(self._recording_path, f)
                stat = os.stat(fpath)

                if now - stat.st_mtime > self._recording_ttl:
                    self._logger.info(f'Deleting {fpath} (expired)')
                    os.remove(fpath)
                    await asyncio.sleep(0)
                    continue

                if now - stat.st_mtime > 60 and os.path.getsize(fpath) == 0:
                    self._logger.info(f'Deleting {fpath} (trash)')
                    os.remove(fpath)
                    await asyncio.sleep(0)
                    continue

            await asyncio.sleep(300)
