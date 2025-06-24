import asyncio
import logging
import math
import os
import struct

from .stream import AsyncByteStream

USRP_FRAME_SIZE = 352
USRP_HEADER_SIZE = 32
USRP_VOICE_SIZE = USRP_FRAME_SIZE - USRP_HEADER_SIZE

USRP_GAIN_RX_DB = int(os.environ.get('USRP_GAIN_RX_DB', 0))

USRP_TYPE_VOICE = 0


def db_to_linear(db):
    return math.pow(10, db / 10)


def apply_gain(buf, gain):
    # USRP is PCM @ 8kHz, 16 bit signed. We should only ever get 20ms chunks,
    # but safer not to assume so.
    format = f'{int(len(buf) / 2)}h'
    pre_gain = struct.unpack(format, buf)
    return struct.pack(format, *[clamp_short(gain * b) for b in pre_gain])


def clamp_short(sh):
    return int(max(-32768, min(32767, sh)))


class USRPController(asyncio.DatagramProtocol):
    def __init__(self,
                 stream_out: AsyncByteStream,
                 usrp_ptt: asyncio.Event):

        self._stream_out = stream_out

        self._usrp_ptt = usrp_ptt

        self._usrp_gain_rx = db_to_linear(USRP_GAIN_RX_DB)

        self._logger = logging.getLogger('USRPController')
        self._logger.info(f'USRP RX gain: {USRP_GAIN_RX_DB}dB = {self._usrp_gain_rx}')

    def datagram_received(self, data, addr):
        ptt = self._frame_ptt_state(data)
        if not ptt:
            self._usrp_ptt.clear()
            return

        self._usrp_ptt.set()

        loop = asyncio.get_running_loop()
        frame = data[USRP_HEADER_SIZE:]

        if self._usrp_gain_rx != 1:
            frame = apply_gain(frame, self._usrp_gain_rx)

        loop.create_task(self._stream_out.write(frame))

    def _rx_decode_state(self, frame):
        header = frame[4:USRP_HEADER_SIZE]
        seq, mem, ptt, tg, type, mpx, res = struct.unpack('>iiiiiii', header)
        return (seq, mem, ptt, tg, type, mpx, res)

    def _frame_ptt_state(self, frame):
        state = self._rx_decode_state(frame)
        return state[2] == 1
