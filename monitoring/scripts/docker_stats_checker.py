import json
import subprocess
from datetime import datetime


CONTAINERS = [
    "company-backend",
    "company-frontend",
    "company-postgres",
    "company-redis",
    "company-minio",
]


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
                "name": container_name,
                "status": "ERROR",
                "error": result.stderr.strip(),
            }

        data = json.loads(
            result.stdout.strip()
        )

        return {
            "name": container_name,
            "cpu": data.get("CPUPerc", "-"),
            "memory": data.get("MemUsage", "-"),
            "memory_percent": data.get(
                "MemPerc",
                "-"
            ),
            "network": data.get(
                "NetIO",
                "-"
            ),
            "block_io": data.get(
                "BlockIO",
                "-"
            ),
        }

    except Exception as error:
        return {
            "name": container_name,
            "status": "ERROR",
            "error": str(error),
        }


def check_stats():
    print(
        f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        "Docker Kaynak Kullanımı"
    )

    print("-" * 90)

    for container_name in CONTAINERS:

        result = get_container_stats(
            container_name
        )

        if result.get("status") == "ERROR":
            print(
                f"{container_name:<20} "
                f"ERROR: {result['error']}"
            )
            continue

        print(
            f"{result['name']:<20}"
            f"CPU: {result['cpu']:<8}"
            f"RAM: {result['memory']:<25}"
            f"RAM %: {result['memory_percent']}"
        )


if __name__ == "__main__":
    check_stats()