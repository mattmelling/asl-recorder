import struct
import os
import asyncio
import logging
from datetime import datetime
from pyogg import OpusBufferedEncoder, OggOpusWriter
import samplerate

def unpack_16s(input):
    """
    16 bit signed int to normalized floats
    """
    unpacked = struct.unpack(f'<{int(len(input) // 2)}h', input)
    return [u / 32768.0 for u in unpacked]

def pack_16s(input):
    """
    Normalized floats to 16 bit signed ints
    """
    rescaled = [max(-32768, min(32767, int(round(s * 32768)))) for s in input]
    return struct.pack(f'<{len(rescaled)}h', *rescaled)

class Recorder:

    def __init__(self, stream_in, ptt):
        self._logger = logging.getLogger('Recorder')
        self._stream_in = stream_in
        self._ptt = ptt

        self._encoder = OpusBufferedEncoder()
        self._encoder.set_application('audio')
        self._encoder.set_sampling_frequency(48000)
        self._encoder.set_channels(1)
        self._encoder.set_frame_size(20)

        self._resampler = None
        self._writer = None

    def get_filename(self):
        recording_path = os.environ.get('RECORDING_PATH', '/tmp/')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_path = os.path.join(recording_path, f'{timestamp}.ogg')
        return file_path

    def resample(self, input, end_of_input=False):
        return self._resampler.process(input, ratio=6, end_of_input=end_of_input)

    def write_pcm(self, pcm):
        raw = unpack_16s(pcm)
        resampled = self.resample(raw)
        packed = pack_16s(resampled)
        self._writer.write(bytearray(packed))

    def flush(self):
        flushed = self.resample([], end_of_input=True)
        packed = pack_16s(flushed)
        self._writer.write(bytearray(packed))

    async def run(self):
        recording = False
        file_name = None

        while True:
            await asyncio.sleep(0)

            if not recording and self._ptt.is_set():
                recording = True
                file_name = self.get_filename()

                self._logger.info(f'Opening {file_name}')
                f = open(file_name, 'wb')

                # Init resampler
                self._resampler = samplerate.Resampler(converter_type='sinc_best')

                # Init ogg file writer
                self._writer = OggOpusWriter(f, self._encoder)

            elif recording and not self._ptt.is_set():
                recording = False
                self._logger.info(f'Closing {file_name}')

                self.flush()
                self._writer.close()
                self._resampler = None
                self._writer = None
                continue

            if recording:
                try:
                    pcm = await asyncio.wait_for(self._stream_in.read(640), timeout=1)
                    if len(pcm) == 0:
                        continue
                    self.write_pcm(pcm)
                except asyncio.TimeoutError:
                    continue
