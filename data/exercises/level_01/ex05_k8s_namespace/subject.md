# Lab: Namespaces - Organizing Your Cluster

## 🎯 Objective
Learn how to use Namespaces to organize and isolate resources in your cluster.

## 📚 Theory

**Namespaces** provide a mechanism for isolating groups of resources within a single cluster. They are intended for use in environments with many users spread across multiple teams or projects.

Key benefits:
- **Resource isolation** - Separate environments (dev, staging, prod)
- **Access control** - Apply RBAC policies per namespace
- **Resource quotas** - Limit resource usage per namespace
- **Name scoping** - Same resource names can exist in different namespaces

```
┌────────────────────────────────────────────────────────────┐
│                        Cluster                              │
│                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌───────────┐  │
│   │   namespace:    │  │   namespace:    │  │ namespace:│  │
│   │     dev         │  │    staging      │  │   prod    │  │
│   │                 │  │                 │  │           │  │
│   │  ┌───────────┐  │  │  ┌───────────┐  │  │ ┌───────┐ │  │
│   │  │ webapp    │  │  │  │ webapp    │  │  │ │webapp │ │  │
│   │  │ deployment│  │  │  │ deployment│  │  │ │deploy │ │  │
│   │  └───────────┘  │  │  └───────────┘  │  │ └───────┘ │  │
│   │                 │  │                 │  │           │  │
│   │  ┌───────────┐  │  │  ┌───────────┐  │  │ ┌───────┐ │  │
│   │  │ database  │  │  │  │ database  │  │  │ │db     │ │  │
│   │  └───────────┘  │  │  └───────────┘  │  │ └───────┘ │  │
│   └─────────────────┘  └─────────────────┘  └───────────┘  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

Default namespaces:
- `default` - Default namespace for objects with no namespace
- `kube-system` - For objects created by the Kubernetes system
- `kube-public` - Readable by all users, reserved for cluster usage
- `kube-node-lease` - For node heartbeat data

## 📋 Task

Create two files:

### 1. `development-namespace.yaml`
Create a Namespace named `development` with:
- Label: `environment: dev`
- Label: `team: backend`

### 2. `dev-pod.yaml`
Create a Pod in the `development` namespace:
- Name: `dev-nginx`
- Namespace: `development`
- Container name: `nginx`
- Image: `nginx:alpine`

## 📁 Files to Submit

```
~/rendudevops/ex05_k8s_namespace/
├── development-namespace.yaml
└── dev-pod.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

Namespace manifest structure:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: <namespace-name>
  labels:
    <key>: <value>
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

To put a resource in a specific namespace, add the namespace field:
```yaml
metadata:
  name: <resource-name>
  namespace: <namespace-name>
```
</details>

## ✅ Validation Criteria

**Namespace:**
- Named `development`
- Has label `environment: dev`
- Has label `team: backend`

**Pod:**
- Named `dev-nginx`
- In namespace `development`
- Uses `nginx:alpine` image

## 📖 Useful Commands

```bash
# Create namespace
kubectl apply -f development-namespace.yaml

# List all namespaces
kubectl get namespaces
kubectl get ns

# Create pod in namespace
kubectl apply -f dev-pod.yaml

# List pods in specific namespace
kubectl get pods -n development

# List pods in all namespaces
kubectl get pods --all-namespaces
kubectl get pods -A

# Set default namespace for kubectl
kubectl config set-context --current --namespace=development

# Delete all resources in a namespace
kubectl delete all --all -n development
```

## 🔗 Resources
- [Kubernetes Namespaces Documentation](https://kubernetes.io/docs/concepts/overview/working-with-objects/namespaces/)
