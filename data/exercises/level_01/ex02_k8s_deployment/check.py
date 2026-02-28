from pathlib import Path
from typing import Tuple
import yaml


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex02_k8s_deployment:
    Validates the webapp-deployment.yaml manifest
    """

    try:
        manifest = yaml.safe_load(code)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []

    if manifest.get("apiVersion") != "apps/v1":
        errors.append("apiVersion should be 'apps/v1'")

    if manifest.get("kind") != "Deployment":
        errors.append("kind should be 'Deployment'")

    metadata = manifest.get("metadata", {})
    if metadata.get("name") != "webapp-deployment":
        errors.append("Deployment name should be 'webapp-deployment'")

    spec = manifest.get("spec", {})

    if spec.get("replicas") != 4:
        errors.append("replicas should be 4")

    selector = spec.get("selector", {})
    match_labels = selector.get("matchLabels", {})
    if match_labels.get("app") != "webapp":
        errors.append("selector.matchLabels should have 'app: webapp'")

    template = spec.get("template", {})
    template_metadata = template.get("metadata", {})
    template_labels = template_metadata.get("labels", {})

    if template_labels.get("app") != "webapp":
        errors.append("template.metadata.labels should have 'app: webapp'")

    template_spec = template.get("spec", {})
    containers = template_spec.get("containers", [])

    if not containers:
        errors.append("No containers defined in the Pod template")
    else:
        container = containers[0]

        if container.get("name") != "webapp":
            errors.append("Container name should be 'webapp'")

        if container.get("image") != "nginx:1.22":
            errors.append("Image should be 'nginx:1.22'")

        resources = container.get("resources", {})
        limits = resources.get("limits", {})

        if not limits:
            errors.append("Resource limits should be defined")
        else:
            if limits.get("memory") != "128Mi":
                errors.append("Memory limit should be '128Mi'")
            if limits.get("cpu") != "250m":
                errors.append("CPU limit should be '250m'")

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
        cmd = ["kubectl", "get", "deployment", "webapp-deployment", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            return (
                False,
                f"YAML is valid, but Deployment 'webapp-deployment' not found. Did you apply it? (Error: {result.stderr.strip()})",
            )

        dep_data = json.loads(result.stdout)

        ready_replicas = dep_data.get("status", {}).get("readyReplicas", 0)
        if ready_replicas != 4:
            return (
                False,
                f"YAML is valid, but expected 4 ready replicas, found {ready_replicas}.",
            )

        containers = (
            dep_data.get("spec", {})
            .get("template", {})
            .get("spec", {})
            .get("containers", [])
        )
        if containers:
            limits = containers[0].get("resources", {}).get("limits", {})
            if limits.get("memory") != "128Mi" or limits.get("cpu") != "250m":
                return (
                    False,
                    "YAML is valid, but live Deployment resource limits do not match requirements.",
                )

    except Exception as e:
        return False, f"System check failed: {e}"

    return (
        True,
        "✅ Excellent! Your Deployment is production-ready, running, and correctly scaled!",
    )
