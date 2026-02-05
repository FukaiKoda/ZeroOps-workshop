# Lab: Services - ClusterIP

## 🎯 Objective
Learn how to expose your application inside the cluster using ClusterIP Services.

## 📚 Theory

A **Service** is an abstraction that defines a logical set of Pods and a policy to access them. Services enable loose coupling between dependent Pods.

**ClusterIP** (default type):
- Exposes the Service on a cluster-internal IP
- Only reachable from within the cluster
- Perfect for internal communication between microservices

```
┌─────────────────────────────────────────────────┐
│                   Cluster                        │
│                                                  │
│   ┌─────────┐      ┌─────────────────────────┐  │
│   │  Pod A  │─────▶│   Service (ClusterIP)   │  │
│   └─────────┘      │      10.96.0.100        │  │
│                    └───────────┬─────────────┘  │
│                                │                 │
│                    ┌───────────┼───────────┐    │
│                    ▼           ▼           ▼    │
│               ┌───────┐  ┌───────┐  ┌───────┐  │
│               │ Pod 1 │  │ Pod 2 │  │ Pod 3 │  │
│               └───────┘  └───────┘  └───────┘  │
│                                                  │
└─────────────────────────────────────────────────┘
```

## 📋 Task

Create a Service manifest file named `webapp-service.yaml` that:

1. Creates a Service named `webapp-service`
2. Type: `ClusterIP` (default)
3. Selector: `app: webapp` (to match our previous deployment)
4. Port configuration:
   - Service port: `80`
   - Target port: `80`
   - Protocol: `TCP`

## 📁 Files to Submit

```
~/rendudevops/ex03_k8s_service_clusterip/
└── webapp-service.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

Basic Service structure:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <service-name>
spec:
  selector:
    <label-key>: <label-value>
  ports:
  - port: <service-port>
    targetPort: <container-port>
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

The `selector` must match the labels of the Pods you want to target. In our case, the Deployment created Pods with label `app: webapp`.
</details>

## ✅ Validation Criteria

- Service named `webapp-service`
- Type is ClusterIP (or omitted, as it's default)
- Selector matches `app: webapp`
- Port 80 mapped to targetPort 80

## 📖 Useful Commands

```bash
# Apply the service
kubectl apply -f webapp-service.yaml

# List services
kubectl get services
kubectl get svc

# Describe service
kubectl describe service webapp-service

# Get endpoints (shows which Pods are behind the service)
kubectl get endpoints webapp-service

# Test the service from inside the cluster
kubectl run test-pod --image=busybox -it --rm -- wget -qO- webapp-service
```

## 🧪 Understanding Service Discovery

Once created, your service will be accessible:
- By IP: `<ClusterIP>:80`
- By DNS: `webapp-service.<namespace>.svc.cluster.local`
- Short form: `webapp-service` (within same namespace)

## 🔗 Resources
- [Kubernetes Services Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
