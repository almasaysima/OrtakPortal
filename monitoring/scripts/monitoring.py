import csv
import json
import os
import subprocess
import urllib.error
import urllib.request
from datetime import datetime


HEALTH_URL = "http://localhost/api/health"

CONTAINERS = [
    "company-backend",
    "company-frontend",
    "company-postgres",
    "company-redis",
    "company-minio",
]

CPU_WARNING = 80.0
MEMORY_WARNING = 80.0

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

METRICS_FILE = os.path.join(
    BASE_DIR,
    "data",
    "metrics.csv"
)


def check_flask_health():
    try:
        with urllib.request.urlopen(
            HEALTH_URL,
            timeout=5
        ) as response:

            if response.status == 200:
                return "UP"

            return f"DOWN (HTTP {response.status})"

    except urllib.error.URLError:
        return "DOWN"

    except Exception:
        return "ERROR"


def get_container_status(container_name):
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format",
                "{{json .State}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return "NOT_FOUND"

        state = json.loads(
            result.stdout
        )

        if state.get("Running"):
            return "UP"

        return "DOWN"

    except Exception:
        return "ERROR"


def get_container_stats(container_name):
    try:
        result = subprocess.run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{json .}}",
                container_name,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return {
                "cpu": "-",
                "memory": "-",
                "memory_percent": "-",
            }

        data = json.loads(
            result.stdout.strip()
        )

        return {
            "cpu": data.get(
                "CPUPerc",
                "-"
            ),
            "memory": data.get(
                "MemUsage",
                "-"
            ),
            "memory_percent": data.get(
                "MemPerc",
                "-"
            ),
        }

    except Exception:
        return {
            "cpu": "-",
            "memory": "-",
            "memory_percent": "-",
        }


def parse_percentage(value):
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

    cpu_value = parse_percentage(cpu)

    if (
        cpu_value is not None
        and cpu_value >= CPU_WARNING
    ):
        alerts.append(
            f"WARNING: {service} CPU "
            f"kullanımı %{cpu_value:.2f}"
        )

    memory_value = parse_percentage(
        memory_percent
    )

    if (
        memory_value is not None
        and memory_value >= MEMORY_WARNING
    ):
        alerts.append(
            f"WARNING: {service} RAM "
            f"kullanımı %{memory_value:.2f}"
        )

    return alerts


def save_metric(
    timestamp,
    service,
    status,
    cpu="-",
    memory="-",
    memory_percent="-"
):
    os.makedirs(
        os.path.dirname(METRICS_FILE),
        exist_ok=True
    )

    file_exists = os.path.exists(
        METRICS_FILE
    )

    with open(
        METRICS_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        if (
            not file_exists
            or os.path.getsize(
                METRICS_FILE
            ) == 0
        ):
            writer.writerow([
                "timestamp",
                "service",
                "status",
                "cpu",
                "memory",
                "memory_percent",
            ])

        writer.writerow([
            timestamp,
            service,
            status,
            cpu,
            memory,
            memory_percent,
        ])


def run_monitoring():
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    print()
    print("=" * 90)
    print(
        f"OrtakPortal Monitoring - {timestamp}"
    )
    print("=" * 90)

    all_alerts = []

    # ---------------------------------------------------------
    # FLASK HEALTH
    # ---------------------------------------------------------

    flask_health = check_flask_health()

    print()
    print("APPLICATION HEALTH")
    print("-" * 90)

    print(
        f"Flask API: {flask_health}"
    )

    save_metric(
        timestamp=timestamp,
        service="flask-api",
        status=flask_health,
    )

    all_alerts.extend(
        check_alerts(
            service="flask-api",
            status=flask_health,
        )
    )

    # ---------------------------------------------------------
    # DOCKER SERVICES
    # ---------------------------------------------------------

    print()
    print("DOCKER SERVICES")
    print("-" * 90)

    for container_name in CONTAINERS:

        status = get_container_status(
            container_name
        )

        stats = get_container_stats(
            container_name
        )

        print(
            f"{container_name:<20}"
            f"Status: {status:<10}"
            f"CPU: {stats['cpu']:<8}"
            f"RAM: {stats['memory']:<25}"
            f"RAM %: {stats['memory_percent']}"
        )

        save_metric(
            timestamp=timestamp,
            service=container_name,
            status=status,
            cpu=stats["cpu"],
            memory=stats["memory"],
            memory_percent=stats["memory_percent"],
        )

        all_alerts.extend(
            check_alerts(
                service=container_name,
                status=status,
                cpu=stats["cpu"],
                memory_percent=stats[
                    "memory_percent"
                ],
            )
        )

    # ---------------------------------------------------------
    # ALERTS
    # ---------------------------------------------------------

    print()
    print("ALERTS")
    print("-" * 90)

    if all_alerts:

        for alert in all_alerts:
            print(alert)

    else:

        print(
            "NORMAL: Kritik veya yüksek kaynak kullanımı tespit edilmedi."
        )

    print()
    print(
        f"Metrics kaydedildi: {METRICS_FILE}"
    )

    print("=" * 90)


if __name__ == "__main__":
    run_monitoring()