# Lab: Ingress - HTTP Routing

## 🎯 Objective
Learn how to expose multiple services through a single entry point using Ingress.

## 📚 Theory

**Ingress** exposes HTTP and HTTPS routes from outside the cluster to services within the cluster. It provides:
- **Load balancing**
- **SSL/TLS termination**
- **Name-based virtual hosting**
- **Path-based routing**

Unlike NodePort or LoadBalancer, Ingress is a single entry point that can route to multiple services based on rules.

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Internet                                   │
│                              │                                       │
│               ┌──────────────┴──────────────┐                       │
│               │     Ingress Controller      │                       │
│               │      (nginx, traefik)       │                       │
│               └──────────────┬──────────────┘                       │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
┌──────────────────────────────┼───────────────────────────────────────┐
│              Cluster         │                                       │
│               ┌──────────────┴──────────────┐                       │
│               │          Ingress            │                       │
│               │                             │                       │
│               │  Rules:                     │                       │
│               │  /api  → api-service        │                       │
│               │  /web  → web-service        │                       │
│               │  /     → frontend-service   │                       │
│               └──────────────┬──────────────┘                       │
│                              │                                       │
│        ┌─────────────────────┼─────────────────────┐                │
│        ▼                     ▼                     ▼                │
│   ┌─────────┐         ┌─────────┐         ┌─────────────┐          │
│   │   API   │         │   Web   │         │  Frontend   │          │
│   │ Service │         │ Service │         │   Service   │          │
│   └─────────┘         └─────────┘         └─────────────┘          │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 📋 Task

Create a complete setup with Ingress routing:

### 1. `frontend-deployment.yaml`
Create a Deployment and Service for frontend:
- Deployment: `frontend-deploy` with 2 replicas
- Container: `frontend`, image `nginx:1.21`
- Service: `frontend-service`, ClusterIP, port 80

### 2. `api-deployment.yaml`
Create a Deployment and Service for API:
- Deployment: `api-deploy` with 2 replicas
- Container: `api`, image `nginx:1.21`
- Service: `api-service`, ClusterIP, port 80

### 3. `webapp-ingress.yaml`
Create an Ingress named `webapp-ingress`:
- Path `/` routes to `frontend-service` on port 80
- Path `/api` routes to `api-service` on port 80
- Use `pathType: Prefix`

## 📁 Files to Submit

```
~/rendudevops/ex09_k8s_ingress/
├── frontend-deployment.yaml
├── api-deployment.yaml
└── webapp-ingress.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

You can combine Deployment and Service in one file using `---` separator:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend-deploy
# ... deployment spec ...
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
# ... service spec ...
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

Ingress manifest structure:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: <ingress-name>
spec:
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: <service-name>
            port:
              number: 80
```
</details>

<details>
<summary>Click to reveal hint 3</summary>

For the `/api` path, remember to define the more specific path first or use proper pathType to avoid routing conflicts.
</details>

## ✅ Validation Criteria

**Frontend:**
- Deployment `frontend-deploy` with 2 replicas
- Service `frontend-service` (ClusterIP)

**API:**
- Deployment `api-deploy` with 2 replicas
- Service `api-service` (ClusterIP)

**Ingress:**
- Named `webapp-ingress`
- Routes `/` to frontend-service
- Routes `/api` to api-service
- Uses `pathType: Prefix`

## 📖 Useful Commands

```bash
# Apply all resources
kubectl apply -f frontend-deployment.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f webapp-ingress.yaml

# Check ingress
kubectl get ingress
kubectl describe ingress webapp-ingress

# Enable ingress addon in minikube
minikube addons enable ingress

# Get minikube IP
minikube ip

# Test routes (after ingress is ready)
curl http://$(minikube ip)/
curl http://$(minikube ip)/api
```

## ⚠️ Prerequisites

An **Ingress Controller** must be installed in your cluster:
- minikube: `minikube addons enable ingress`
- Kind: Install nginx-ingress
- Cloud providers: Usually pre-installed

## 🔗 Resources
- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
