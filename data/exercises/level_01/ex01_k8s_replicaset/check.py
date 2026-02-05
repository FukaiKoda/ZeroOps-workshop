from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex01_k8s_replicaset:
    Validates the nginx-replicaset.yaml manifest
    """
    
    try:
        manifest = yaml.safe_load(code)
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"
    
    errors = []
    
    # Check apiVersion
    if manifest.get('apiVersion') != 'apps/v1':
        errors.append("apiVersion should be 'apps/v1'")
    
    # Check kind
    if manifest.get('kind') != 'ReplicaSet':
        errors.append("kind should be 'ReplicaSet'")
    
    # Check metadata
    metadata = manifest.get('metadata', {})
    if metadata.get('name') != 'nginx-replicaset':
        errors.append("ReplicaSet name should be 'nginx-replicaset'")
    
    # Check spec
    spec = manifest.get('spec', {})
    
    # Check replicas
    if spec.get('replicas') != 3:
        errors.append("replicas should be 3")
    
    # Check selector
    selector = spec.get('selector', {})
    match_labels = selector.get('matchLabels', {})
    if match_labels.get('app') != 'nginx':
        errors.append("selector.matchLabels should have 'app: nginx'")
    
    # Check template
    template = spec.get('template', {})
    template_metadata = template.get('metadata', {})
    template_labels = template_metadata.get('labels', {})
    
    if template_labels.get('app') != 'nginx':
        errors.append("template.metadata.labels should have 'app: nginx'")
    
    # Check template spec
    template_spec = template.get('spec', {})
    containers = template_spec.get('containers', [])
    
    if not containers:
        errors.append("No containers defined in the Pod template")
    else:
        container = containers[0]
        
        if container.get('name') != 'nginx':
            errors.append("Container name should be 'nginx'")
        
        if container.get('image') != 'nginx:1.21':
            errors.append("Image should be 'nginx:1.21'")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Great job! Your ReplicaSet is correctly configured to maintain 3 nginx replicas!"
