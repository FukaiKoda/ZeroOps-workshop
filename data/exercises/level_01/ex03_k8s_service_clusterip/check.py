from pathlib import Path
from typing import Tuple
import yaml


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex03_k8s_service_clusterip:
    Validates the webapp-service.yaml manifest
    """

    try:
        manifest = yaml.safe_load(code)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []

    if manifest.get("apiVersion") != "v1":
        errors.append("apiVersion should be 'v1'")

    if manifest.get("kind") != "Service":
        errors.append("kind should be 'Service'")

    metadata = manifest.get("metadata", {})
    if metadata.get("name") != "webapp-service":
        errors.append("Service name should be 'webapp-service'")

    spec = manifest.get("spec", {})

    svc_type = spec.get("type", "ClusterIP")
    if svc_type != "ClusterIP":
        errors.append("Service type should be 'ClusterIP'")

    selector = spec.get("selector", {})
    if selector.get("app") != "webapp":
        errors.append("selector should have 'app: webapp'")

    ports = spec.get("ports", [])
    if not ports:
        errors.append("No ports defined")
    else:
        port_config = ports[0]

        if port_config.get("port") != 80:
            errors.append("Service port should be 80")

        if port_config.get("targetPort") != 80:
            errors.append("Target port should be 80")

        protocol = port_config.get("protocol", "TCP")
        if protocol != "TCP":
            errors.append("Protocol should be 'TCP'")

    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    import subprocess
    import json
    import shutil

    if not shutil.which("kubectl"):
        return (
            False,
            "Validation passed, but 'kubectl' is not installed or not in PATH. Cannot verify system state.",
        )

    try:
        cmd = ["kubectl", "get", "service", "webapp-service", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return (
                False,
                f"YAML is valid, but Service 'webapp-service' not found. Did you apply it? (Error: {result.stderr.strip()})",
            )

        svc_data = json.loads(result.stdout)

        svc_type = svc_data.get("spec", {}).get("type", "ClusterIP")
        if svc_type != "ClusterIP":
            return (
                False,
                f"YAML is valid, but Service type is '{svc_type}'. Expected 'ClusterIP'.",
            )

        selector = svc_data.get("spec", {}).get("selector", {})
        if selector.get("app") != "webapp":
            return (
                False,
                f"YAML is valid, but Service selector is incorrect: {selector}. Expected {{'app': 'webapp'}}.",
            )

        cluster_ip = svc_data.get("spec", {}).get("clusterIP")
        if not cluster_ip or cluster_ip == "None":
            return False, "YAML is valid, but Service has no ClusterIP assigned."

    except Exception as e:
        return False, f"System check failed: {e}"

    return (
        True,
        "✅ Well done! Your ClusterIP Service is ready, active, and routing traffic!",
    )
