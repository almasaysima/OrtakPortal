import time
import urllib.request
import urllib.error
from datetime import datetime


HEALTH_URL = "http://localhost/api/health"
CHECK_INTERVAL = 10


def check_health():
    try:
        with urllib.request.urlopen(HEALTH_URL, timeout=5) as response:

            if response.status == 200:
                print(
                    f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                    "FLASK: UP"
                )
                return True

            print(
                f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
                f"FLASK: DOWN - HTTP {response.status}"
            )
            return False

    except urllib.error.URLError as error:

        print(
            f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
            f"FLASK: DOWN - {error.reason}"
        )
        return False

    except Exception as error:

        print(
            f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
            f"FLASK: DOWN - {error}"
        )
        return False


if __name__ == "__main__":

    print("OrtakPortal Monitoring başlatıldı.")
    print(f"Kontrol edilen adres: {HEALTH_URL}")
    print(f"Kontrol aralığı: {CHECK_INTERVAL} saniye")
    print("-" * 50)

    while True:

        check_health()

        time.sleep(CHECK_INTERVAL)