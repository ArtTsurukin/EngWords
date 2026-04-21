import logging


class SafeFormatter(logging.Formatter):
    def format(self, record):
        # Дефолтные значения для отсутствующих полей
        if not hasattr(record, "user_id"):
            record.user_id = "-"
        if not hasattr(record, "status"):
            record.status = "-"
        if not hasattr(record, "details"):
            record.details = ""

        return super().format(record)


def setup_logger():
    logger = logging.getLogger()

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = SafeFormatter(
        fmt="%(asctime)s | %(levelname)s | event: %(message)s, user_id: %(user_id)s status: %(status)s details: %(details)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

