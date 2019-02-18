import logging
import sys
import threading

from lib.junos_collector import JunosCollector

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

jc_logger = logging.getLogger('lib.junos_collector')
jc_logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)

jc_logger.addHandler(handler)
logger.addHandler(handler)

class Collector(object):
    def __init__(self):
        threads = []
        jc_thread = threading.Thread(name='JunosCollector', target=JunosCollector, args=('config/devices.yaml',))
        threads.append(jc_thread)

        for thread in threads:
            logger.info('Starting Thread: %s', thread.name)
            thread.start()

        for thread in threads:
            logger.info('Joining Thread: %s', thread.name)
            thread.join()

if __name__ == '__main__':
    Collector()
