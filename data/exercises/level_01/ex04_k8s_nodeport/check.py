from pathlib import Path
from typing import Tuple
import yaml

def grade(grader, code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex04_k8s_nodeport:
    Validates the webapp-nodeport.yaml manifest
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
    if manifest.get('kind') != 'Service':
        errors.append("kind should be 'Service'")
    
    # Check metadata
    metadata = manifest.get('metadata', {})
    if metadata.get('name') != 'webapp-nodeport':
        errors.append("Service name should be 'webapp-nodeport'")
    
    # Check spec
    spec = manifest.get('spec', {})
    
    # Check type
    if spec.get('type') != 'NodePort':
        errors.append("Service type should be 'NodePort'")
    
    # Check selector
    selector = spec.get('selector', {})
    if selector.get('app') != 'webapp':
        errors.append("selector should have 'app: webapp'")
    
    # Check ports
    ports = spec.get('ports', [])
    if not ports:
        errors.append("No ports defined")
    else:
        port_config = ports[0]
        
        if port_config.get('port') != 80:
            errors.append("Service port should be 80")
        
        if port_config.get('targetPort') != 80:
            errors.append("Target port should be 80")
        
        node_port = port_config.get('nodePort')
        if node_port != 30080:
            errors.append("NodePort should be 30080")
        
        # Validate nodePort range
        if node_port and (node_port < 30000 or node_port > 32767):
            errors.append("NodePort must be in range 30000-32767")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Perfect! Your NodePort Service exposes the webapp to external traffic on port 30080!"
