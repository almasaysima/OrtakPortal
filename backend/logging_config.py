import logging
import os


def configure_logging():
    """
    Uygulama genelinde standart log formatını ayarlar.

    LOG_LEVEL environment variable verilmezse INFO kullanılır.
    """

    level_name = os.getenv(
        "LOG_LEVEL",
        "INFO",
    ).upper()

    level = getattr(
        logging,
        level_name,
        logging.INFO,
    )

    logging.basicConfig(
        level=level,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s - "
            "%(message)s"
        ),
    )
