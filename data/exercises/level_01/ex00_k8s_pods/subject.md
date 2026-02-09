# Lab: Introduction to Pods

## 🎯 Objective
Learn how to create and manage your first Kubernetes Pod.

## 📚 Theory

A **Pod** is the smallest deployable unit in Kubernetes. It represents a single instance of a running process in your cluster.

Key concepts:
- A Pod can contain one or more containers
- Containers in a Pod share the same network namespace
- Pods are ephemeral - they can be created, destroyed, and recreated

## 📋 Task

Create a Pod manifest file named `nginx-pod.yaml` that:

1. Creates a Pod named `nginx-pod`
2. Uses the `nginx:1.21` image
3. The container should be named `nginx-container`
4. Exposes port `80`

## 📁 Files to Submit

```
~/rendudevops/ex00_k8s_pods/
└── nginx-pod.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

The basic structure of a Pod manifest:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: <pod-name>
spec:
  containers:
  - name: <container-name>
    image: <image-name>
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

To expose a port in a container, use the `ports` field:
```yaml
ports:
- containerPort: 80
```
</details>

## ✅ Validation Criteria

- Pod is named `nginx-pod`
- Container is named `nginx-container`
- Image used is `nginx:1.21`
- Port 80 is exposed

## 📖 Useful Commands

```bash
# Apply a manifest
kubectl apply -f nginx-pod.yaml

# List all pods
kubectl get pods

# Describe a pod
kubectl describe pod nginx-pod

# Delete a pod
kubectl delete pod nginx-pod
```

## 🔗 Resources
- [Kubernetes Pods Documentation](https://kubernetes.io/docs/concepts/workloads/pods/)
