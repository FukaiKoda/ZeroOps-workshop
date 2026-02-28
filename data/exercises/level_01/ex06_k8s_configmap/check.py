from pathlib import Path
from typing import Tuple
import yaml


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex06_k8s_configmap:
    Validates ConfigMap and Deployment manifests
    """

    try:
        documents = list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []
    configmap_found = False
    deployment_found = False

    for manifest in documents:
        if not manifest:
            continue

        kind = manifest.get("kind", "")

        if kind == "ConfigMap":
            configmap_found = True
            metadata = manifest.get("metadata", {})

            if metadata.get("name") != "app-config":
                errors.append("ConfigMap name should be 'app-config'")

            data = manifest.get("data", {})

            expected_keys = {
                "APP_ENV": "production",
                "APP_DEBUG": "false",
                "DATABASE_HOST": "mysql-service",
                "DATABASE_PORT": "3306",
            }

            for key, expected_value in expected_keys.items():
                actual_value = str(data.get(key, ""))
                if actual_value != expected_value:
                    errors.append(
                        f"ConfigMap key '{key}' should be '{expected_value}', got '{actual_value}'"
                    )

        elif kind == "Deployment":
            deployment_found = True
            metadata = manifest.get("metadata", {})

            if metadata.get("name") != "config-demo":
                errors.append("Deployment name should be 'config-demo'")

            spec = manifest.get("spec", {})

            if spec.get("replicas") != 2:
                errors.append("Deployment should have 2 replicas")

            template = spec.get("template", {})
            template_spec = template.get("spec", {})
            containers = template_spec.get("containers", [])

            if not containers:
                errors.append("Deployment should have at least one container")
            else:
                container = containers[0]

                if container.get("name") != "app":
                    errors.append("Container name should be 'app'")

                if container.get("image") != "busybox:1.35":
                    errors.append("Container image should be 'busybox:1.35'")

                env_from = container.get("envFrom", [])
                configmap_ref_found = False

                for env_source in env_from:
                    cm_ref = env_source.get("configMapRef", {})
                    if cm_ref.get("name") == "app-config":
                        configmap_ref_found = True
                        break

                if not configmap_ref_found:
                    errors.append(
                        "Container should use 'envFrom' with 'configMapRef' pointing to 'app-config'"
                    )

    if not configmap_found:
        errors.append("ConfigMap manifest not found")

    if not deployment_found:
        errors.append("Deployment manifest not found")

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
        cmd_cm = ["kubectl", "get", "configmap", "app-config", "-o", "json"]
        res_cm = subprocess.run(cmd_cm, capture_output=True, text=True)

        if res_cm.returncode != 0:
            return False, "YAML is valid, but ConfigMap 'app-config' not found."

        cmd_dep = ["kubectl", "get", "deployment", "config-demo", "-o", "json"]
        res_dep = subprocess.run(cmd_dep, capture_output=True, text=True)

        if res_dep.returncode != 0:
            return False, "YAML is valid, but Deployment 'config-demo' not found."

        dep_data = json.loads(res_dep.stdout)
        ready_replicas = dep_data.get("status", {}).get("readyReplicas", 0)
        if ready_replicas != 2:
            return (
                False,
                f"YAML is valid, but Deployment has {ready_replicas} ready replicas. Expected 2.",
            )

        containers = (
            dep_data.get("spec", {})
            .get("template", {})
            .get("spec", {})
            .get("containers", [])
        )
        if not containers:
            return False, "YAML is valid, but Deployment has no containers."

        env_from = containers[0].get("envFrom", [])
        found_ref = any(
            e.get("configMapRef", {}).get("name") == "app-config" for e in env_from
        )
        if not found_ref:
            return (
                False,
                "YAML is valid, but active Deployment is not using the 'app-config' ConfigMap.",
            )

    except Exception as e:
        return False, f"System check failed: {e}"

    return (
        True,
        "✅ Great work! You've learned to externalize configuration using ConfigMaps!",
    )
