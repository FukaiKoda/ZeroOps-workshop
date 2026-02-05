# Lab: Services - NodePort

## 🎯 Objective
Learn how to expose your application outside the cluster using NodePort Services.

## 📚 Theory

**NodePort** Service exposes the application on each Node's IP at a static port (the NodePort). You can access the service from outside the cluster using `<NodeIP>:<NodePort>`.

```
┌─────────────────────────────────────────────────────────────┐
│                         External                             │
│                                                              │
│              http://192.168.1.10:30080                       │
│                          │                                   │
└──────────────────────────┼───────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────┐
│          Cluster         │                                   │
│                          ▼                                   │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           Node (192.168.1.10)                        │   │
│   │                    :30080                            │   │
│   │                      │                               │   │
│   │            ┌─────────┴──────────┐                    │   │
│   │            ▼                    ▼                    │   │
│   │       ┌─────────┐         ┌─────────┐               │   │
│   │       │  Pod 1  │         │  Pod 2  │               │   │
│   │       │  :80    │         │  :80    │               │   │
│   │       └─────────┘         └─────────┘               │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

Port ranges:
- **NodePort**: 30000-32767
- Traffic flow: `NodePort → Service Port → Target Port (Pod)`

## 📋 Task

Create a NodePort Service manifest file named `webapp-nodeport.yaml` that:

1. Creates a Service named `webapp-nodeport`
2. Type: `NodePort`
3. Selector: `app: webapp`
4. Port configuration:
   - Port: `80`
   - TargetPort: `80`
   - NodePort: `30080`

## 📁 Files to Submit

```
~/rendudevops/ex04_k8s_nodeport/
└── webapp-nodeport.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

NodePort Service structure:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: <service-name>
spec:
  type: NodePort
  selector:
    <key>: <value>
  ports:
  - port: <service-port>
    targetPort: <container-port>
    nodePort: <node-port>
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

Remember: NodePort must be between 30000-32767!
</details>

## ✅ Validation Criteria

- Service named `webapp-nodeport`
- Type is `NodePort`
- Selector matches `app: webapp`
- Correct port mappings (80 → 80 → 30080)

## 📖 Useful Commands

```bash
# Apply the service
kubectl apply -f webapp-nodeport.yaml

# List services with wide output
kubectl get svc -o wide

# Access the service (replace with your node IP)
curl http://<node-ip>:30080

# In minikube
minikube service webapp-nodeport --url

# Get node IPs
kubectl get nodes -o wide
```

## ⚠️ When to Use NodePort

**Good for:**
- Development and testing
- Small clusters
- When you need direct access from outside

**Limitations:**
- One service per port
- Ports must be in range 30000-32767
- If Node IP changes, you need to update clients

## 🔗 Resources
- [NodePort Service Documentation](https://kubernetes.io/docs/concepts/services-networking/service/#type-nodeport)
