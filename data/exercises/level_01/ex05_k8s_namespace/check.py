from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex05_k8s_namespace:
    Validates both namespace and pod manifests
    """
    
    # Parse all YAML documents in the submission
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
            
        kind = manifest.get('kind', '')
        
        if kind == 'Namespace':
            namespace_found = True
            metadata = manifest.get('metadata', {})
            
            if metadata.get('name') != 'development':
                errors.append("Namespace name should be 'development'")
            
            labels = metadata.get('labels', {})
            if labels.get('environment') != 'dev':
                errors.append("Namespace should have label 'environment: dev'")
            if labels.get('team') != 'backend':
                errors.append("Namespace should have label 'team: backend'")
        
        elif kind == 'Pod':
            pod_found = True
            metadata = manifest.get('metadata', {})
            
            if metadata.get('name') != 'dev-nginx':
                errors.append("Pod name should be 'dev-nginx'")
            
            if metadata.get('namespace') != 'development':
                errors.append("Pod namespace should be 'development'")
            
            spec = manifest.get('spec', {})
            containers = spec.get('containers', [])
            
            if not containers:
                errors.append("Pod should have at least one container")
            else:
                container = containers[0]
                if container.get('name') != 'nginx':
                    errors.append("Container name should be 'nginx'")
                if container.get('image') != 'nginx:alpine':
                    errors.append("Container image should be 'nginx:alpine'")
    
    if not namespace_found:
        errors.append("Namespace manifest not found")
    
    if not pod_found:
        errors.append("Pod manifest not found")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Excellent! You've successfully organized resources using namespaces!"
