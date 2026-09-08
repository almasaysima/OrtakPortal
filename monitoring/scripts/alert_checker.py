import re


CPU_WARNING = 80.0
MEMORY_WARNING = 80.0


def parse_cpu(value):
    if not value or value == "-":
        return None

    try:
        return float(
            value.replace("%", "").strip()
        )
    except ValueError:
        return None


def parse_memory_percent(value):
    if not value or value == "-":
        return None

    try:
        return float(
            value.replace("%", "").strip()
        )
    except ValueError:
        return None


def check_alerts(
    service,
    status,
    cpu="-",
    memory_percent="-"
):
    alerts = []

    if status in [
        "DOWN",
        "NOT_FOUND",
        "ERROR",
    ]:
        alerts.append(
            f"CRITICAL: {service} durumu {status}"
        )

    cpu_value = parse_cpu(cpu)

    if (
        cpu_value is not None
        and cpu_value >= CPU_WARNING
    ):
        alerts.append(
            f"WARNING: {service} CPU kullanımı "
            f"%{cpu_value:.2f}"
        )

    memory_value = (
        parse_memory_percent(
            memory_percent
        )
    )

    if (
        memory_value is not None
        and memory_value >= MEMORY_WARNING
    ):
        alerts.append(
            f"WARNING: {service} RAM kullanımı "
            f"%{memory_value:.2f}"
        )

    return alerts


if __name__ == "__main__":

    test_alerts = check_alerts(
        service="company-backend",
        status="UP",
        cpu="85.20%",
        memory_percent="82.10%",
    )

    if test_alerts:

        for alert in test_alerts:
            print(alert)

    else:
        print("ALERT: Sistem normal.")