from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
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
            
        kind = manifest.get('kind', '')
        
        if kind == 'PersistentVolume':
            pv_found = True
            metadata = manifest.get('metadata', {})
            spec = manifest.get('spec', {})
            
            if metadata.get('name') != 'data-pv':
                errors.append("PV name should be 'data-pv'")
            
            capacity = spec.get('capacity', {})
            if capacity.get('storage') != '1Gi':
                errors.append("PV capacity should be '1Gi'")
            
            access_modes = spec.get('accessModes', [])
            if 'ReadWriteOnce' not in access_modes:
                errors.append("PV should have 'ReadWriteOnce' access mode")
            
            if spec.get('storageClassName') != 'manual':
                errors.append("PV storageClassName should be 'manual'")
            
            host_path = spec.get('hostPath', {})
            if host_path.get('path') != '/mnt/data':
                errors.append("PV hostPath should be '/mnt/data'")
        
        elif kind == 'PersistentVolumeClaim':
            pvc_found = True
            metadata = manifest.get('metadata', {})
            spec = manifest.get('spec', {})
            
            if metadata.get('name') != 'data-pvc':
                errors.append("PVC name should be 'data-pvc'")
            
            access_modes = spec.get('accessModes', [])
            if 'ReadWriteOnce' not in access_modes:
                errors.append("PVC should have 'ReadWriteOnce' access mode")
            
            resources = spec.get('resources', {})
            requests = resources.get('requests', {})
            if requests.get('storage') != '500Mi':
                errors.append("PVC should request '500Mi' storage")
            
            if spec.get('storageClassName') != 'manual':
                errors.append("PVC storageClassName should be 'manual'")
        
        elif kind == 'Pod':
            pod_found = True
            metadata = manifest.get('metadata', {})
            spec = manifest.get('spec', {})
            
            if metadata.get('name') != 'storage-pod':
                errors.append("Pod name should be 'storage-pod'")
            
            # Check volumes
            volumes = spec.get('volumes', [])
            pvc_volume_found = False
            pvc_volume_name = None
            
            for volume in volumes:
                pvc = volume.get('persistentVolumeClaim', {})
                if pvc.get('claimName') == 'data-pvc':
                    pvc_volume_found = True
                    pvc_volume_name = volume.get('name')
                    break
            
            if not pvc_volume_found:
                errors.append("Pod should have a volume using PVC 'data-pvc'")
            
            # Check container
            containers = spec.get('containers', [])
            if not containers:
                errors.append("Pod should have at least one container")
            else:
                container = containers[0]
                
                if container.get('name') != 'app':
                    errors.append("Container name should be 'app'")
                
                if container.get('image') != 'busybox:1.35':
                    errors.append("Container image should be 'busybox:1.35'")
                
                # Check volume mounts
                volume_mounts = container.get('volumeMounts', [])
                mount_found = False
                
                for mount in volume_mounts:
                    if mount.get('mountPath') == '/app/data':
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
    
    return True, "✅ Excellent! You've mastered persistent storage in Kubernetes!"
