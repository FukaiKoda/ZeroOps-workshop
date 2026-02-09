# Lab: ReplicaSets - Scaling Your Pods

## 🎯 Objective
Learn how to use ReplicaSets to maintain a stable set of replica Pods.

## 📚 Theory

A **ReplicaSet** ensures that a specified number of pod replicas are running at any given time. It's the mechanism that allows Kubernetes to maintain high availability.

Key concepts:
- ReplicaSets use **selectors** to identify which Pods to manage
- **Labels** are key-value pairs attached to objects like Pods
- If a Pod fails, the ReplicaSet will automatically create a new one

## 📋 Task

Create a ReplicaSet manifest file named `nginx-replicaset.yaml` that:

1. Creates a ReplicaSet named `nginx-replicaset`
2. Maintains **3 replicas**
3. Uses the label `app: nginx` as selector
4. Creates Pods with:
   - Label `app: nginx`
   - Container named `nginx`
   - Image `nginx:1.21`
   - Port `80` exposed

## 📁 Files to Submit

```
~/rendudevops/ex01_k8s_replicaset/
└── nginx-replicaset.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

The basic structure of a ReplicaSet:
```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: <replicaset-name>
spec:
  replicas: <number>
  selector:
    matchLabels:
      <key>: <value>
  template:
    metadata:
      labels:
        <key>: <value>
    spec:
      containers:
      - name: <container-name>
        image: <image>
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

The `selector.matchLabels` must match the labels in `template.metadata.labels`!
</details>

## ✅ Validation Criteria

- ReplicaSet is named `nginx-replicaset`
- Replicas set to 3
- Selector uses `app: nginx`
- Pod template has matching labels
- Container uses `nginx:1.21` image

## 📖 Useful Commands

```bash
# Apply the manifest
kubectl apply -f nginx-replicaset.yaml

# List ReplicaSets
kubectl get replicasets
kubectl get rs

# Watch pods being created
kubectl get pods -w

# Scale a ReplicaSet (imperative way)
kubectl scale rs nginx-replicaset --replicas=5

# Delete one pod and watch it recreate
kubectl delete pod <pod-name>
```

## 🔗 Resources
- [Kubernetes ReplicaSet Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/replicaset/)
