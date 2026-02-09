# Lab: Deployments - The Standard Way

## 🎯 Objective
Learn how to create Deployments, the recommended way to manage applications in Kubernetes.

## 📚 Theory

A **Deployment** provides declarative updates for Pods and ReplicaSets. It's the most common way to deploy applications in Kubernetes.

Key advantages over ReplicaSets:
- **Rolling updates** - Update Pods gradually without downtime
- **Rollback** - Easily revert to previous versions
- **Scaling** - Scale up or down with ease
- **Self-healing** - Automatically replaces failed Pods

## 📋 Task

Create a Deployment manifest file named `webapp-deployment.yaml` that:

1. Creates a Deployment named `webapp-deployment`
2. Maintains **4 replicas**
3. Uses labels:
   - Selector: `app: webapp`
   - Pod template labels: `app: webapp`
4. Container specification:
   - Name: `webapp`
   - Image: `nginx:1.22`
   - Port: `80`
5. Add resource limits:
   - Memory limit: `128Mi`
   - CPU limit: `250m`

## 📁 Files to Submit

```
~/rendudevops/ex02_k8s_deployment/
└── webapp-deployment.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

The structure is similar to a ReplicaSet, but the kind is `Deployment`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: <deployment-name>
spec:
  replicas: <number>
  selector:
    matchLabels:
      <key>: <value>
  template:
    ...
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

Resource limits are specified under the container:
```yaml
resources:
  limits:
    memory: "128Mi"
    cpu: "250m"
```
</details>

## ✅ Validation Criteria

- Deployment named `webapp-deployment`
- 4 replicas configured
- Correct labels and selectors
- nginx:1.22 image used
- Resource limits properly set

## 📖 Useful Commands

```bash
# Apply the deployment
kubectl apply -f webapp-deployment.yaml

# Check deployment status
kubectl get deployments
kubectl describe deployment webapp-deployment

# Watch rollout status
kubectl rollout status deployment/webapp-deployment

# View rollout history
kubectl rollout history deployment/webapp-deployment

# Update image (imperative way)
kubectl set image deployment/webapp-deployment webapp=nginx:1.23

# Rollback to previous version
kubectl rollout undo deployment/webapp-deployment
```

## 🧪 Try It Out!

After creating your deployment, try these experiments:
1. Delete a pod and watch it recreate automatically
2. Scale the deployment to 6 replicas
3. Update the image version and observe the rolling update

## 🔗 Resources
- [Kubernetes Deployments Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
