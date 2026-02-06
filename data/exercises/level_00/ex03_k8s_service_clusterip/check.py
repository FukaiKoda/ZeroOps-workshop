from pathlib import Path
from typing import Tuple
import yaml

def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex03_k8s_service_clusterip:
    Validates the webapp-service.yaml manifest
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
    if metadata.get('name') != 'webapp-service':
        errors.append("Service name should be 'webapp-service'")
    
    # Check spec
    spec = manifest.get('spec', {})
    
    # Check type (ClusterIP is default, so it can be omitted)
    svc_type = spec.get('type', 'ClusterIP')
    if svc_type != 'ClusterIP':
        errors.append("Service type should be 'ClusterIP'")
    
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
        
        # Protocol is optional, defaults to TCP
        protocol = port_config.get('protocol', 'TCP')
        if protocol != 'TCP':
            errors.append("Protocol should be 'TCP'")
    
    if errors:
        return False, "Validation failed:\n- " + "\n- ".join(errors)
    
    return True, "✅ Well done! Your ClusterIP Service is ready to route traffic to your webapp Pods!"
