from pathlib import Path
from typing import Tuple
import yaml
import base64

def grade(code: str, exercise_path: Path) -> Tuple[bool, str]:
    """
    Grades ex07_k8s_secret:
    Validates Secret and Pod manifests
    """
    
    try:
        documents = list(yaml.safe_load_all(code))
    except yaml.YAMLError as e:
        return False, f"Invalid YAML syntax: {e}"
    
    errors = []
    secret_found = False
    pod_found = False
    
    for manifest in documents:
        if not manifest:
            continue
            
        kind = manifest.get('kind', '')
        
        if kind == 'Secret':
            secret_found = True
            metadata = manifest.get('metadata', {})
            
            if metadata.get('name') != 'db-credentials':
                errors.append("Secret name should be 'db-credentials'")
            
            if manifest.get('type') != 'Opaque':
                errors.append("Secret type should be 'Opaque'")
            
            data = manifest.get('data', {})
            
            # Check DB_USERNAME
            try:
                username_decoded = base64.b64decode(data.get('DB_USERNAME', '')).decode('utf-8')
                if username_decoded != 'admin':
                    errors.append(f"DB_USERNAME should decode to 'admin', got '{username_decoded}'")
            except Exception:
                errors.append("DB_USERNAME is not valid base64 or missing")
            
            # Check DB_PASSWORD
            try:
                password_decoded = base64.b64decode(data.get('DB_PASSWORD', '')).decode('utf-8')
                if password_decoded != 'supersecret123':
                    errors.append(f"DB_PASSWORD should decode to 'supersecret123', got '{password_decoded}'")
            except Exception:
                errors.append("DB_PASSWORD is not valid base64 or missing")
        
        elif kind == 'Pod':
            pod_found = True
            metadata = manifest.get('metadata', {})
            
            if metadata.get('name') != 'secret-test-pod':
                errors.append("Pod name should be 'secret-test-pod'")
            
            spec = manifest.get('spec', {})
            containers = spec.get('containers', [])
            
            if not containers:
                errors.append("Pod should have at least one container")
            else:
                container = containers[0]
                
                if container.get('name') != 'app':
                    errors.append("Container name should be 'app'")
                
                if container.get('image') != 'busybox:1.35':
                    errors.append("Container image should be 'busybox:1.35'")
                
                # Check environment variables from secret
                env_vars = container.get('env', [])
                env_from = container.get('envFrom', [])
                
                username_from_secret = False
                password_from_secret = False
                
                for env_var in env_vars:
                    value_from = env_var.get('valueFrom', {})
                    secret_ref = value_from.get('secretKeyRef', {})
                    
                    if secret_ref.get('name') == 'db-credentials':
                        if secret_ref.get('key') == 'DB_USERNAME':
                            username_from_secret = True
                        if secret_ref.get('key') == 'DB_PASSWORD':
                            password_from_secret = True
                
                # Also check envFrom
                for source in env_from:
                    if source.get('secretRef', {}).get('name') == 'db-credentials':
                        username_from_secret = True
                        password_from_secret = True
                
                if not username_from_secret:
                    errors.append("DB_USERNAME should be loaded from secret 'db-credentials'")
                if not password_from_secret:
                    errors.append("DB_PASSWORD should be loaded from secret 'db-credentials'")
    
    if not secret_found:
        errors.append("Secret manifest not found")
    
    if not pod_found:
        errors.append("Pod manifest not found")
    
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
        # Check Secret
        cmd_sec = ["kubectl", "get", "secret", "db-credentials", "-o", "json"]
        res_sec = subprocess.run(cmd_sec, capture_output=True, text=True)
        
        if res_sec.returncode != 0:
            return False, "YAML is valid, but Secret 'db-credentials' not found."
            
        # Check Deployment
        cmd_dep = ["kubectl", "get", "deployment", "secret-demo", "-o", "json"]
        res_dep = subprocess.run(cmd_dep, capture_output=True, text=True)
        
        if res_dep.returncode != 0:
             return False, "YAML is valid, but Deployment 'secret-demo' not found."

        dep_data = json.loads(res_dep.stdout)
        
        # Verify envFrom/secretRef
        containers = dep_data.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
        if not containers:
             return False, "YAML is valid, but Deployment has no containers."
        
        env_from = containers[0].get("envFrom", [])
        found_ref = any(e.get("secretRef", {}).get("name") == "db-credentials" for e in env_from)
        if not found_ref:
             return False, "YAML is valid, but active Deployment is not using the 'db-credentials' Secret."

    except Exception as e:
        return False, f"System check failed: {e}"

    return True, "✅ Excellent! You've securely managed sensitive data using Secrets!"
