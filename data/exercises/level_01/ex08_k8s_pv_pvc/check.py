from pathlib import Path
from typing import Tuple
import yaml
import shutil
import json
import subprocess


def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex08_k8s_pv_pvc:
    Validates PV, PVC, and Pod manifests
    """

    try:
        documents = list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"

    errors = []
    pv_found = False
    pvc_found = False
    pod_found = False

    for manifest in documents:
        if not manifest:
            continue

        kind = manifest.get("kind", "")

        if kind == "PersistentVolume":
            pv_found = True
            metadata = manifest.get("metadata", {})
            spec = manifest.get("spec", {})

            if metadata.get("name") != "data-pv":
                errors.append("PV name should be 'data-pv'")

            capacity = spec.get("capacity", {})
            if capacity.get("storage") != "1Gi":
                errors.append("PV capacity should be '1Gi'")

            access_modes = spec.get("accessModes", [])
            if "ReadWriteOnce" not in access_modes:
                errors.append("PV should have 'ReadWriteOnce' access mode")

            if spec.get("storageClassName") != "manual":
                errors.append("PV storageClassName should be 'manual'")

            host_path = spec.get("hostPath", {})
            if host_path.get("path") != "/mnt/data":
                errors.append("PV hostPath should be '/mnt/data'")

        elif kind == "PersistentVolumeClaim":
            pvc_found = True
            metadata = manifest.get("metadata", {})
            spec = manifest.get("spec", {})

            if metadata.get("name") != "data-pvc":
                errors.append("PVC name should be 'data-pvc'")

            access_modes = spec.get("accessModes", [])
            if "ReadWriteOnce" not in access_modes:
                errors.append("PVC should have 'ReadWriteOnce' access mode")

            resources = spec.get("resources", {})
            requests = resources.get("requests", {})
            if requests.get("storage") != "500Mi":
                errors.append("PVC should request '500Mi' storage")

            if spec.get("storageClassName") != "manual":
                errors.append("PVC storageClassName should be 'manual'")

        elif kind == "Pod":
            pod_found = True
            metadata = manifest.get("metadata", {})
            spec = manifest.get("spec", {})

            if metadata.get("name") != "storage-pod":
                errors.append("Pod name should be 'storage-pod'")

            volumes = spec.get("volumes", [])
            pvc_volume_found = False

            for volume in volumes:
                pvc = volume.get("persistentVolumeClaim", {})
                if pvc.get("claimName") == "data-pvc":
                    pvc_volume_found = True
                    volume.get("name")
                    break

            if not pvc_volume_found:
                errors.append("Pod should have a volume using PVC 'data-pvc'")

            containers = spec.get("containers", [])
            if not containers:
                errors.append("Pod should have at least one container")
            else:
                container = containers[0]

                if container.get("name") != "app":
                    errors.append("Container name should be 'app'")

                if container.get("image") != "busybox:1.35":
                    errors.append("Container image should be 'busybox:1.35'")

                volume_mounts = container.get("volumeMounts", [])
                mount_found = False

                for mount in volume_mounts:
                    if mount.get("mountPath") == "/app/data":
                        mount_found = True
                        break

                if not mount_found:
                    errors.append("Container should mount volume at '/app/data'")

    if not pv_found:
        errors.append("PersistentVolume manifest not found")

    if not pvc_found:
        errors.append("PersistentVolumeClaim manifest not found")

    if not pod_found:
        errors.append("Pod manifest not found")

    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)

    if not shutil.which("kubectl"):
        return (
            False,
            "Validation passed, but 'kubectl' is not installed or not in PATH. Cannot verify system state.",
        )

    try:
        cmd_pv = ["kubectl", "get", "pv", "data-pv", "-o", "json"]
        res_pv = subprocess.run(cmd_pv, capture_output=True, text=True)
        if res_pv.returncode != 0:
            return False, "YAML is valid, but PersistentVolume 'data-pv' not found."

        cmd_pvc = ["kubectl", "get", "pvc", "data-pvc", "-o", "json"]
        res_pvc = subprocess.run(cmd_pvc, capture_output=True, text=True)
        if res_pvc.returncode != 0:
            return (
                False,
                "YAML is valid, but PersistentVolumeClaim 'data-pvc' not found.",
            )

        pvc_data = json.loads(res_pvc.stdout)
        phase = pvc_data.get("status", {}).get("phase")
        if phase != "Bound":
            return (
                False,
                f"YAML is valid, but PVC is in '{phase}' state. It should be 'Bound'.",
            )

        cmd_pod = ["kubectl", "get", "pod", "storage-pod", "-o", "json"]
        res_pod = subprocess.run(cmd_pod, capture_output=True, text=True)
        if res_pod.returncode != 0:
            return False, "YAML is valid, but Pod 'storage-pod' not found."

        pod_data = json.loads(res_pod.stdout)
        volumes = pod_data.get("spec", {}).get("volumes", [])
        found_vol = any(
            v.get("persistentVolumeClaim", {}).get("claimName") == "data-pvc"
            for v in volumes
        )
        if not found_vol:
            return False, "YAML is valid, but Pod is not using the 'data-pvc' claim."

    except Exception as e:
        return False, f"System check failed: {e}"

    return True, "✅ Fantastic! You've set up persistent storage using PV and PVC!"
