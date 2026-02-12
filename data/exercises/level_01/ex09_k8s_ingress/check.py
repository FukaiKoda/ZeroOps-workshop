from pathlib import Path
from typing import Tuple
import yaml

def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex09_k8s_ingress:
    Validates Deployments, Services, and Ingress manifests
    """
    
    try:
        documents = list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"
    
    errors = []
    
    frontend_deploy_found = False
    frontend_service_found = False
    api_deploy_found = False
    api_service_found = False
    ingress_found = False
    
    for manifest in documents:
        if not manifest:
            continue
            
        kind = manifest.get('kind', '')
        metadata = manifest.get('metadata', {})
        name = metadata.get('name', '')
        spec = manifest.get('spec', {})
        
        if kind == 'Deployment':
            if name == 'frontend-deploy':
                frontend_deploy_found = True
                if spec.get('replicas') != 2:
                    errors.append("frontend-deploy should have 2 replicas")
                
                containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                if containers:
                    container = containers[0]
                    if container.get('name') != 'frontend':
                        errors.append("Frontend container name should be 'frontend'")
                    if container.get('image') != 'nginx:1.21':
                        errors.append("Frontend image should be 'nginx:1.21'")
            
            elif name == 'api-deploy':
                api_deploy_found = True
                if spec.get('replicas') != 2:
                    errors.append("api-deploy should have 2 replicas")
                
                containers = spec.get('template', {}).get('spec', {}).get('containers', [])
                if containers:
                    container = containers[0]
                    if container.get('name') != 'api':
                        errors.append("API container name should be 'api'")
                    if container.get('image') != 'nginx:1.21':
                        errors.append("API image should be 'nginx:1.21'")
        
        elif kind == 'Service':
            if name == 'frontend-service':
                frontend_service_found = True
                svc_type = spec.get('type', 'ClusterIP')
                if svc_type != 'ClusterIP':
                    errors.append("frontend-service type should be 'ClusterIP'")
            
            elif name == 'api-service':
                api_service_found = True
                svc_type = spec.get('type', 'ClusterIP')
                if svc_type != 'ClusterIP':
                    errors.append("api-service type should be 'ClusterIP'")
        
        elif kind == 'Ingress':
            if name == 'webapp-ingress':
                ingress_found = True
                
                rules = spec.get('rules', [])
                if not rules:
                    errors.append("Ingress should have at least one rule")
                    continue
                
                paths = rules[0].get('http', {}).get('paths', [])
                
                frontend_path_found = False
                api_path_found = False
                
                for path_config in paths:
                    path = path_config.get('path')
                    path_type = path_config.get('pathType')
                    backend = path_config.get('backend', {})
                    service = backend.get('service', {})
                    service_name = service.get('name')
                    port = service.get('port', {}).get('number')
                    
                    if path == '/' and service_name == 'frontend-service':
                        frontend_path_found = True
                        if path_type != 'Prefix':
                            errors.append("Path '/' should use pathType: Prefix")
                        if port != 80:
                            errors.append("frontend-service port should be 80")
                    
                    if path == '/api' and service_name == 'api-service':
                        api_path_found = True
                        if path_type != 'Prefix':
                            errors.append("Path '/api' should use pathType: Prefix")
                        if port != 80:
                            errors.append("api-service port should be 80")
                
                if not frontend_path_found:
                    errors.append("Ingress should route '/' to frontend-service")
                
                if not api_path_found:
                    errors.append("Ingress should route '/api' to api-service")
    
    if not frontend_deploy_found:
        errors.append("Deployment 'frontend-deploy' not found")
    
    if not frontend_service_found:
        errors.append("Service 'frontend-service' not found")
    
    if not api_deploy_found:
        errors.append("Deployment 'api-deploy' not found")
    
    if not api_service_found:
        errors.append("Service 'api-service' not found")
    
    if not ingress_found:
        errors.append("Ingress 'webapp-ingress' not found")
    
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
        # Check Ingress
        cmd_ing = ["kubectl", "get", "ingress", "webapp-ingress", "-o", "json"]
        res_ing = subprocess.run(cmd_ing, capture_output=True, text=True)
        if res_ing.returncode != 0:
            return False, "YAML is valid, but Ingress 'webapp-ingress' not found."
            
        ing_data = json.loads(res_ing.stdout)
        # Check rules
        rules = ing_data.get("spec", {}).get("rules", [])
        if not rules:
             return False, "YAML is valid, but active Ingress has no rules."

        # Check Services existence
        for svc_name in ["frontend-service", "api-service"]:
            if subprocess.run(["kubectl", "get", "service", svc_name], capture_output=True).returncode != 0:
                 return False, f"YAML is valid, but Service '{svc_name}' not found in cluster."

        # Check Deployments existence
        for dep_name in ["frontend-deploy", "api-deploy"]:
             if subprocess.run(["kubectl", "get", "deployment", dep_name], capture_output=True).returncode != 0:
                 return False, f"YAML is valid, but Deployment '{dep_name}' not found in cluster."

    except Exception as e:
        return False, f"System check failed: {e}"

    return True, "✅ Fantastic! You've mastered Ingress routing to expose multiple services!"
