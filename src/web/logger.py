import logging

logging.basicConfig(format='%(asctime)s | %(name)s | %(message)s',
                    datefmt='%m-%d %H:%M')
web_logger = logging.getLogger("ANTIHERO_WEB")
web_logger.setLevel(logging.INFO)
