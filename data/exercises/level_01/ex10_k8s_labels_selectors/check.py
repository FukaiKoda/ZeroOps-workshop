from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex10_k8s_labels_selectors:
    Validates labeled pods manifest
    """
    
    try:
        documents = list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"
    
    errors = []
    
    expected_pods = {
        'web-prod': {
            'app': 'web',
            'environment': 'production',
            'tier': 'frontend'
        },
        'web-dev': {
            'app': 'web',
            'environment': 'development',
            'tier': 'frontend'
        },
        'api-prod': {
            'app': 'api',
            'environment': 'production',
            'tier': 'backend'
        }
    }
    
    found_pods = set()
    
    for manifest in documents:
        if not manifest:
            continue
            
        kind = manifest.get('kind', '')
        
        if kind != 'Pod':
            continue
        
        metadata = manifest.get('metadata', {})
        name = metadata.get('name', '')
        labels = metadata.get('labels', {})
        
        if name in expected_pods:
            found_pods.add(name)
            expected_labels = expected_pods[name]
            
            for label_key, label_value in expected_labels.items():
                if labels.get(label_key) != label_value:
                    errors.append(f"Pod '{name}' should have label '{label_key}: {label_value}'")
            
            # Check image
            spec = manifest.get('spec', {})
            containers = spec.get('containers', [])
            
            if not containers:
                errors.append(f"Pod '{name}' should have at least one container")
            else:
                image = containers[0].get('image', '')
                if image != 'nginx:1.21':
                    errors.append(f"Pod '{name}' should use image 'nginx:1.21'")
    
    # Check for missing pods
    for pod_name in expected_pods:
        if pod_name not in found_pods:
            errors.append(f"Pod '{pod_name}' not found")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Perfect! You've mastered labels and selectors for organizing Kubernetes resources!"
