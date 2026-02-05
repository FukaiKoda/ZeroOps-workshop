from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex00_k8s_pods:
    Validates the nginx-pod.yaml manifest
    """
    
    try:
        manifest = yaml.safe_load(code)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"
    
    errors = []
    
    # Check apiVersion
    if manifest.get('apiVersion') != 'v1':
        errors.append("apiVersion should be 'v1'")
    
    # Check kind
    if manifest.get('kind') != 'Pod':
        errors.append("kind should be 'Pod'")
    
    # Check metadata
    metadata = manifest.get('metadata', {})
    if metadata.get('name') != 'nginx-pod':
        errors.append("Pod name should be 'nginx-pod'")
    
    # Check spec
    spec = manifest.get('spec', {})
    containers = spec.get('containers', [])
    
    if not containers:
        errors.append("No containers defined in the Pod spec")
    else:
        container = containers[0]
        
        if container.get('name') != 'nginx-container':
            errors.append("Container name should be 'nginx-container'")
        
        if container.get('image') != 'nginx:1.21':
            errors.append("Image should be 'nginx:1.21'")
        
        ports = container.get('ports', [])
        if not ports:
            errors.append("Container should expose port 80")
        else:
            port_found = any(p.get('containerPort') == 80 for p in ports)
            if not port_found:
                errors.append("Container should expose containerPort 80")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Excellent! Your Pod manifest is correct. You've learned the basics of Kubernetes Pods!"
