from pathlib import Path
from typing import Tuple
import yaml


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex00_k8s_pods:
    Validates the nginx-pod.yaml manifest
    """

    try:
        manifest = yaml.safe_load(code)
        if manifest is None:
            return False, "No YAML content found. Please ensure your file is not empty."
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []

    if manifest.get("apiVersion") != "v1":
        errors.append("apiVersion should be 'v1'")

    if manifest.get("kind") != "Pod":
        errors.append("kind should be 'Pod'")

    metadata = manifest.get("metadata", {})
    if metadata.get("name") != "nginx-pod":
        errors.append("Pod name should be 'nginx-pod'")

    spec = manifest.get("spec", {})
    containers = spec.get("containers", [])

    if not containers:
        errors.append("No containers defined in the Pod spec")
    else:
        container = containers[0]

        if container.get("name") != "nginx-container":
            errors.append("Container name should be 'nginx-container'")

        if container.get("image") != "nginx:1.21":
            errors.append("Image should be 'nginx:1.21'")

        ports = container.get("ports", [])
        if not ports:
            errors.append("Container should expose port 80")
        else:
            port_found = any(p.get("containerPort") == 80 for p in ports)
            if not port_found:
                errors.append("Container should expose containerPort 80")

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
        cmd = ["kubectl", "get", "pod", "nginx-pod", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return (
                False,
                f"YAML is valid, but Pod 'nginx-pod' not found in the cluster. Did you apply it? (Error: {result.stderr.strip()})",
            )

        pod_data = json.loads(result.stdout)
        phase = pod_data.get("status", {}).get("phase")

        if phase != "Running":
            return (
                False,
                f"YAML is valid, but Pod 'nginx-pod' is in '{phase}' state. It should be 'Running'.",
            )

        containers = pod_data.get("spec", {}).get("containers", [])
        if not containers or containers[0].get("image") != "nginx:1.21":
            return (
                False,
                "YAML is valid, but the running Pod has the wrong image. Expected 'nginx:1.21'.",
            )

    except Exception as e:
        return False, f"System check failed: {e}"

    return True, "✅ Excellent! Your Pod manifest is correct AND the Pod is running."
