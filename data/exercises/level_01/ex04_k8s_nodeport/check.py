from pathlib import Path
from typing import Tuple
import yaml

def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
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

    # ---------------------------------------------------------
    # System Check (Verification Phase)
    # ---------------------------------------------------------
    import subprocess
    import json
    import shutil

    if not shutil.which("kubectl"):
        return False, "Validation passed, but 'kubectl' is not installed or not in PATH. Cannot verify system state."

    try:
        # Check if the service exists
        cmd = ["kubectl", "get", "service", "webapp-nodeport", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return False, f"YAML is valid, but Service 'webapp-nodeport' not found. Did you apply it? (Error: {result.stderr.strip()})"
        
        svc_data = json.loads(result.stdout)
        
        # Check Type
        svc_type = svc_data.get("spec", {}).get("type")
        if svc_type != "NodePort":
             return False, f"YAML is valid, but Service type is '{svc_type}'. Expected 'NodePort'."

        # Check NodePort assignment
        ports = svc_data.get("spec", {}).get("ports", [])
        if not ports:
             return False, "YAML is valid, but no ports are defined in the live Service."
             
        node_port = ports[0].get("nodePort")
        if node_port != 30080:
             return False, f"YAML is valid, but NodePort is {node_port}. Expected 30080."

    except Exception as e:
        return False, f"System check failed: {e}"

    return True, "✅ Perfect! Your NodePort Service is active and exposing port 30080!"
