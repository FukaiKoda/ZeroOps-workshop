from pathlib import Path
from typing import Tuple
import yaml


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex05_k8s_namespace:
    Validates both namespace and pod manifests
    """

    try:
        documents = list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []
    namespace_found = False
    pod_found = False

    for manifest in documents:
        if not manifest:
            continue

        kind = manifest.get("kind", "")

        if kind == "Namespace":
            namespace_found = True
            metadata = manifest.get("metadata", {})

            if metadata.get("name") != "development":
                errors.append("Namespace name should be 'development'")

            labels = metadata.get("labels", {})
            if labels.get("environment") != "dev":
                errors.append("Namespace should have label 'environment: dev'")
            if labels.get("team") != "backend":
                errors.append("Namespace should have label 'team: backend'")

        elif kind == "Pod":
            pod_found = True
            metadata = manifest.get("metadata", {})

            if metadata.get("name") != "dev-nginx":
                errors.append("Pod name should be 'dev-nginx'")

            if metadata.get("namespace") != "development":
                errors.append("Pod namespace should be 'development'")

            spec = manifest.get("spec", {})
            containers = spec.get("containers", [])

            if not containers:
                errors.append("Pod should have at least one container")
            else:
                container = containers[0]
                if container.get("name") != "nginx":
                    errors.append("Container name should be 'nginx'")
                if container.get("image") != "nginx:alpine":
                    errors.append("Container image should be 'nginx:alpine'")

    if not namespace_found:
        errors.append("Namespace manifest not found")

    if not pod_found:
        errors.append("Pod manifest not found")

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
        cmd_ns = ["kubectl", "get", "namespace", "development", "-o", "json"]
        res_ns = subprocess.run(cmd_ns, capture_output=True, text=True)

        if res_ns.returncode != 0:
            return (
                False,
                "YAML is valid, but Namespace 'development' not found. Did you apply it?",
            )

        ns_data = json.loads(res_ns.stdout)
        labels = ns_data.get("metadata", {}).get("labels", {})
        if labels.get("environment") != "dev" or labels.get("team") != "backend":
            return (
                False,
                "YAML is valid, but Namespace is missing required labels (environment=dev, team=backend).",
            )

        cmd_pod = [
            "kubectl",
            "get",
            "pod",
            "dev-nginx",
            "-n",
            "development",
            "-o",
            "json",
        ]
        res_pod = subprocess.run(cmd_pod, capture_output=True, text=True)

        if res_pod.returncode != 0:
            return (
                False,
                "YAML is valid, but Pod 'dev-nginx' not found in namespace 'development'.",
            )

        pod_data = json.loads(res_pod.stdout)
        phase = pod_data.get("status", {}).get("phase")
        if phase != "Running":
            return (
                False,
                f"YAML is valid, but Pod is in '{phase}' state. It should be 'Running'.",
            )

    except Exception as e:
        return False, f"System check failed: {e}"

    return (
        True,
        "✅ Excellent! You've successfully organized resources using namespaces!",
    )
