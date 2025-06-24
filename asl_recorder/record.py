import os
import asyncio
import logging
from datetime import datetime
from pyogg import OpusBufferedEncoder, OggOpusWriter


class Recorder:

    def __init__(self, stream_in, ptt):
        self._logger = logging.getLogger('Recorder')
        self._stream_in = stream_in
        self._ptt = ptt

        self._encoder = OpusBufferedEncoder()
        self._encoder.set_application('voip')
        self._encoder.set_sampling_frequency(8000)
        self._encoder.set_channels(1)
        self._encoder.set_frame_size(20)

    def get_filename(self):
        recording_path = os.environ.get('RECORDING_PATH', '/tmp/')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_path = os.path.join(recording_path, f'{timestamp}.ogg')
        return file_path

    async def run(self):
        recording = False
        writer = None
        file_name = None
        while True:
            await asyncio.sleep(0)

            if not recording and self._ptt.is_set():
                recording = True
                file_name = self.get_filename()
                self._logger.info(f'Opening {file_name}')
                f = open(file_name, 'wb')
                writer = OggOpusWriter(f, self._encoder)

            elif recording and not self._ptt.is_set():
                recording = False
                self._logger.info(f'Closing {file_name}')
                writer.close()
                continue

            if recording:
                try:
                    pcm = await asyncio.wait_for(self._stream_in.read(640), timeout=1)
                    if len(pcm) == 0:
                        continue
                    writer.write(bytearray(pcm))
                except asyncio.TimeoutError:
                    continue
