from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex02_k8s_deployment:
    Validates the webapp-deployment.yaml manifest
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
    if manifest.get('kind') != 'Deployment':
        errors.append("kind should be 'Deployment'")
    
    # Check metadata
    metadata = manifest.get('metadata', {})
    if metadata.get('name') != 'webapp-deployment':
        errors.append("Deployment name should be 'webapp-deployment'")
    
    # Check spec
    spec = manifest.get('spec', {})
    
    # Check replicas
    if spec.get('replicas') != 4:
        errors.append("replicas should be 4")
    
    # Check selector
    selector = spec.get('selector', {})
    match_labels = selector.get('matchLabels', {})
    if match_labels.get('app') != 'webapp':
        errors.append("selector.matchLabels should have 'app: webapp'")
    
    # Check template
    template = spec.get('template', {})
    template_metadata = template.get('metadata', {})
    template_labels = template_metadata.get('labels', {})
    
    if template_labels.get('app') != 'webapp':
        errors.append("template.metadata.labels should have 'app: webapp'")
    
    # Check template spec
    template_spec = template.get('spec', {})
    containers = template_spec.get('containers', [])
    
    if not containers:
        errors.append("No containers defined in the Pod template")
    else:
        container = containers[0]
        
        if container.get('name') != 'webapp':
            errors.append("Container name should be 'webapp'")
        
        if container.get('image') != 'nginx:1.22':
            errors.append("Image should be 'nginx:1.22'")
        
        # Check resource limits
        resources = container.get('resources', {})
        limits = resources.get('limits', {})
        
        if not limits:
            errors.append("Resource limits should be defined")
        else:
            if limits.get('memory') != '128Mi':
                errors.append("Memory limit should be '128Mi'")
            if limits.get('cpu') != '250m':
                errors.append("CPU limit should be '250m'")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Excellent! Your Deployment is production-ready with proper resource limits!"
