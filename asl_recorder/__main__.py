import asyncio
import logging
import os

from .usrp import USRPController
from .stream import AsyncByteStream
from .record import Recorder
from .janitor import Janitor

log_level = os.environ.get('LOG_LEVEL', 'INFO')
log_format = os.environ.get('LOG_FORMAT', '%(levelname)s:%(name)s:%(message)s')
logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger('__main__')


async def _main():
    loop = asyncio.get_running_loop()

    usrp_out_stream = AsyncByteStream()
    usrp_ptt = asyncio.Event()

    logger.info('Initialising USRP')
    usrp = USRPController(usrp_out_stream, usrp_ptt)

    logger.info('Initiaising Recorder')
    recorder = Recorder(usrp_out_stream, usrp_ptt)

    logger.info('Initialising Janitor')
    janitor = Janitor()

    bind_port = int(os.environ.get('USRP_RXPORT', 0))
    bind_host = os.environ.get('USRP_BIND', '127.0.0.1')
    logger.info(f'Binding to {bind_host}:{bind_port}')
    await asyncio.gather(*[
        recorder.run(),
        janitor.run(),
        loop.create_datagram_endpoint(lambda: usrp,
                                      local_addr=(bind_host, bind_port))
    ])

    loop.run_forever()

def main():
    asyncio.run(_main())

if __name__ == '__main__':
    main()
