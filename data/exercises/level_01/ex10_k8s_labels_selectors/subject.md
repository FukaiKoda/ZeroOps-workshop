# Lab: Labels and Selectors

## 🎯 Objective
Master the use of labels and selectors to organize and query Kubernetes resources.

## 📚 Theory

**Labels** are key/value pairs attached to objects. They are used to organize and select subsets of objects.

**Selectors** are used to filter resources based on their labels.

### Why Labels Matter
- **Organization** - Group resources logically
- **Selection** - Services use selectors to find Pods
- **Filtering** - Query specific resources with kubectl
- **Scheduling** - Place pods on specific nodes

### Label Syntax
```yaml
metadata:
  labels:
    app: frontend
    environment: production
    team: backend
    version: v1.2.3
```

### Selector Types

**Equality-based:**
```yaml
selector:
  matchLabels:
    app: frontend    # app = frontend
```

**Set-based:**
```yaml
selector:
  matchExpressions:
  - key: environment
    operator: In
    values: [production, staging]
  - key: tier
    operator: NotIn
    values: [frontend]
```

## 📋 Task

Create a file `labeled-pods.yaml` with 3 Pods:

### Pod 1: `web-prod`
- Labels:
  - `app: web`
  - `environment: production`
  - `tier: frontend`
- Image: `nginx:1.21`

### Pod 2: `web-dev`
- Labels:
  - `app: web`
  - `environment: development`
  - `tier: frontend`
- Image: `nginx:1.21`

### Pod 3: `api-prod`
- Labels:
  - `app: api`
  - `environment: production`
  - `tier: backend`
- Image: `nginx:1.21`

## 📁 Files to Submit

```
~/rendudevops/ex10_k8s_labels_selectors/
└── labeled-pods.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

Separate multiple resources in one file with `---`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pod1
  labels:
    key1: value1
spec:
  containers:
  - name: container1
    image: nginx:1.21
---
apiVersion: v1
kind: Pod
metadata:
  name: pod2
# ...
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

Labels are defined in the `metadata` section:
```yaml
metadata:
  name: my-pod
  labels:
    app: web
    environment: production
```
</details>

## ✅ Validation Criteria

- All 3 Pods created with correct names
- Each Pod has all required labels
- All Pods use `nginx:1.21` image

## 📖 Useful Commands

After creating your pods, try these label-based queries:

```bash
# Apply the manifest
kubectl apply -f labeled-pods.yaml

# List all pods with labels
kubectl get pods --show-labels

# Filter by single label
kubectl get pods -l app=web
kubectl get pods -l environment=production

# Filter by multiple labels (AND)
kubectl get pods -l app=web,environment=production

# Set-based selectors
kubectl get pods -l 'environment in (production, staging)'
kubectl get pods -l 'tier notin (frontend)'
kubectl get pods -l 'app'  # Has the label 'app'
kubectl get pods -l '!team'  # Does NOT have label 'team'

# Add a label to existing pod
kubectl label pod web-prod team=frontend

# Remove a label
kubectl label pod web-prod team-

# Overwrite a label
kubectl label pod web-prod environment=staging --overwrite
```

## 🏷️ Label Best Practices

1. **Use meaningful names**: `app`, `environment`, `version`, `tier`
2. **Be consistent**: Same keys across your organization
3. **Recommended labels** (Kubernetes convention):
   - `app.kubernetes.io/name`
   - `app.kubernetes.io/version`
   - `app.kubernetes.io/component`
   - `app.kubernetes.io/part-of`
   - `app.kubernetes.io/managed-by`

## 🔗 Resources
- [Kubernetes Labels and Selectors](https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/)
- [Recommended Labels](https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)
