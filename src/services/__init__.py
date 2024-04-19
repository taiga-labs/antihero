import logging

logging.basicConfig(format='%(asctime)s | %(name)s | %(message)s',
                    datefmt='%m-%d %H:%M')
processor_logger = logging.getLogger("ANTIHERO_PROCESSOR")
processor_logger.setLevel(logging.INFO)
