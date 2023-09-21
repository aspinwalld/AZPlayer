import logging

'''
Need to make an actual logging handler module at some point and move this crap all into it
'''
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    blue = "\x1b[36m"

    # if args.debug:
    #     format = '%(asctime)s [%(filename)s:%(lineno)d] %(funcName)s [%(levelname)s] %(message)s'
    # else:
    #     format = '%(asctime)s [%(levelname)s] %(message)s'
    #format = '%(asctime)s [%(levelname)s] %(message)s'
    format = '%(asctime)s (%(filename)s:%(lineno)d) [%(levelname)s] %(message)s'

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
        logging.FATAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)