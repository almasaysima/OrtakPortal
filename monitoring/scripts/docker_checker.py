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
            return {
                "name": container_name,
                "status": "NOT_FOUND",
            }

        state = json.loads(result.stdout)

        if state.get("Running"):
            status = "UP"
        else:
            status = "DOWN"

        return {
            "name": container_name,
            "status": status,
            "started_at": state.get("StartedAt"),
            "restarts": state.get("RestartCount", 0),
        }

    except Exception as error:
        return {
            "name": container_name,
            "status": "ERROR",
            "error": str(error),
        }


def check_containers():
    print(
        f"\n[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        "Docker Container Durumları"
    )

    print("-" * 60)

    for container_name in CONTAINERS:
        result = get_container_status(
            container_name
        )

        print(
            f"{result['name']:<20}"
            f"{result['status']:<10}"
            f"Restart: "
            f"{result.get('restarts', '-')}"
        )


if __name__ == "__main__":
    check_containers()