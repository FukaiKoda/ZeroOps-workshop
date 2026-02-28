from pathlib import Path
from typing import Tuple
import yaml


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex01_k8s_replicaset:
    Validates the nginx-replicaset.yaml manifest
    """

    try:
        manifest = yaml.safe_load(code)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []

    if manifest.get("apiVersion") != "apps/v1":
        errors.append("apiVersion should be 'apps/v1'")

    if manifest.get("kind") != "ReplicaSet":
        errors.append("kind should be 'ReplicaSet'")

    metadata = manifest.get("metadata", {})
    if metadata.get("name") != "nginx-replicaset":
        errors.append("ReplicaSet name should be 'nginx-replicaset'")

    spec = manifest.get("spec", {})

    if spec.get("replicas") != 3:
        errors.append("replicas should be 3")

    selector = spec.get("selector", {})
    match_labels = selector.get("matchLabels", {})
    if match_labels.get("app") != "nginx":
        errors.append("selector.matchLabels should have 'app: nginx'")

    template = spec.get("template", {})
    template_metadata = template.get("metadata", {})
    template_labels = template_metadata.get("labels", {})

    if template_labels.get("app") != "nginx":
        errors.append("template.metadata.labels should have 'app: nginx'")

    template_spec = template.get("spec", {})
    containers = template_spec.get("containers", [])

    if not containers:
        errors.append("No containers defined in the Pod template")
    else:
        container = containers[0]

        if container.get("name") != "nginx":
            errors.append("Container name should be 'nginx'")

        if container.get("image") != "nginx:1.21":
            errors.append("Image should be 'nginx:1.21'")

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
        cmd = ["kubectl", "get", "replicaset", "nginx-replicaset", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return (
                False,
                f"YAML is valid, but ReplicaSet 'nginx-replicaset' not found. Did you apply it? (Error: {result.stderr.strip()})",
            )

        rs_data = json.loads(result.stdout)

        ready_replicas = rs_data.get("status", {}).get("readyReplicas", 0)
        if ready_replicas != 3:
            return (
                False,
                f"YAML is valid, but expected 3 ready replicas, found {ready_replicas}.",
            )

    except Exception as e:
        return False, f"System check failed: {e}"

    return (
        True,
        "✅ Great job! Your ReplicaSet is correctly configured AND running with 3 replicas!",
    )
