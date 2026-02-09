# Lab: ConfigMaps - Externalize Configuration

## 🎯 Objective
Learn how to use ConfigMaps to decouple configuration from your application code.

## 📚 Theory

A **ConfigMap** is an API object used to store non-confidential data in key-value pairs. Pods can consume ConfigMaps as environment variables, command-line arguments, or as configuration files in a volume.

Why use ConfigMaps?
- **Separation of concerns** - Keep config separate from code
- **Environment flexibility** - Different configs for dev/staging/prod
- **No rebuilds needed** - Update config without rebuilding images

Ways to use ConfigMaps:
1. **Environment variables** - Inject as env vars in containers
2. **Volume mounts** - Mount as files in a directory
3. **Command arguments** - Use in container commands

```
┌─────────────────────────────────────────────────────────────┐
│                       ConfigMap                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  DATABASE_HOST: mysql.example.com                    │   │
│   │  DATABASE_PORT: "3306"                               │   │
│   │  LOG_LEVEL: info                                     │   │
│   │  app.properties: |                                   │   │
│   │    server.port=8080                                  │   │
│   │    cache.enabled=true                                │   │
│   └─────────────────────────────────────────────────────┘   │
│                            │                                 │
│              ┌─────────────┴─────────────┐                  │
│              ▼                           ▼                  │
│   ┌─────────────────────┐    ┌─────────────────────┐       │
│   │   As Environment    │    │    As Volume Mount  │       │
│   │      Variables      │    │       (Files)       │       │
│   └─────────────────────┘    └─────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Task

Create two files:

### 1. `app-configmap.yaml`
Create a ConfigMap named `app-config` with the following data:
- `APP_ENV`: `production`
- `APP_DEBUG`: `false`
- `DATABASE_HOST`: `mysql-service`
- `DATABASE_PORT`: `3306`

### 2. `app-deployment.yaml`
Create a Deployment that uses the ConfigMap:
- Name: `config-demo`
- Replicas: `2`
- Container:
  - Name: `app`
  - Image: `busybox:1.35`
  - Command: `["sh", "-c", "echo DB=$DATABASE_HOST:$DATABASE_PORT ENV=$APP_ENV && sleep 3600"]`
  - Use ALL keys from `app-config` as environment variables (use `envFrom`)

## 📁 Files to Submit

```
~/rendudevops/ex06_k8s_configmap/
├── app-configmap.yaml
└── app-deployment.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

ConfigMap structure:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <configmap-name>
data:
  KEY1: "value1"
  KEY2: "value2"
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

To inject all ConfigMap keys as environment variables:
```yaml
containers:
- name: app
  envFrom:
  - configMapRef:
      name: <configmap-name>
```
</details>

<details>
<summary>Click to reveal hint 3</summary>

For individual keys as env vars:
```yaml
env:
- name: MY_VAR
  valueFrom:
    configMapKeyRef:
      name: <configmap-name>
      key: <key-name>
```
</details>

## ✅ Validation Criteria

**ConfigMap:**
- Named `app-config`
- Contains all 4 key-value pairs

**Deployment:**
- Named `config-demo`
- 2 replicas
- Uses `envFrom` to load ConfigMap

## 📖 Useful Commands

```bash
# Apply configmap
kubectl apply -f app-configmap.yaml

# List configmaps
kubectl get configmaps
kubectl get cm

# View configmap details
kubectl describe cm app-config

# Apply deployment
kubectl apply -f app-deployment.yaml

# Verify env vars in pod
kubectl exec -it <pod-name> -- env | grep -E 'APP_|DATABASE_'

# View pod logs to see the echo output
kubectl logs <pod-name>
```

## 🔗 Resources
- [Kubernetes ConfigMaps Documentation](https://kubernetes.io/docs/concepts/configuration/configmap/)
