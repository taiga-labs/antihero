import logging

logging.basicConfig(format='%(asctime)s | %(name)s | %(message)s',
                    datefmt='%m-%d %H:%M')
logger = logging.getLogger("ANTIHERO_BOT")
logger.setLevel(logging.INFO)
