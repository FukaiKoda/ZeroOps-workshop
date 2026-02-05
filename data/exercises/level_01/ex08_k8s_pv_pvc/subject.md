# Lab: Persistent Volumes and Claims

## 🎯 Objective
Learn how to persist data in Kubernetes using Persistent Volumes (PV) and Persistent Volume Claims (PVC).

## 📚 Theory

Containers are ephemeral - when they restart, all data is lost. **Persistent Volumes** solve this problem by providing storage that outlives the container lifecycle.

Key concepts:

### Persistent Volume (PV)
- A piece of storage in the cluster provisioned by an administrator
- Cluster-wide resource (not namespaced)
- Describes storage details (size, access modes, storage class)

### Persistent Volume Claim (PVC)
- A request for storage by a user
- Namespaced resource
- Claims a PV that satisfies its requirements

### Access Modes
- `ReadWriteOnce (RWO)` - Single node read-write
- `ReadOnlyMany (ROX)` - Multiple nodes read-only
- `ReadWriteMany (RWX)` - Multiple nodes read-write

```
┌─────────────────────────────────────────────────────────────┐
│                         Cluster                              │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                 Persistent Volume                    │   │
│   │     capacity: 1Gi                                    │   │
│   │     accessModes: ReadWriteOnce                       │   │
│   │     hostPath: /mnt/data                              │   │
│   └───────────────────────┬─────────────────────────────┘   │
│                           │  Bound                           │
│   ┌───────────────────────▼─────────────────────────────┐   │
│   │              Persistent Volume Claim                 │   │
│   │     request: 500Mi                                   │   │
│   │     accessModes: ReadWriteOnce                       │   │
│   └───────────────────────┬─────────────────────────────┘   │
│                           │  Mounted                         │
│   ┌───────────────────────▼─────────────────────────────┐   │
│   │                       Pod                            │   │
│   │     volumeMounts:                                    │   │
│   │       - mountPath: /app/data                         │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Task

Create three files:

### 1. `data-pv.yaml`
Create a Persistent Volume named `data-pv`:
- Capacity: `1Gi`
- Access modes: `ReadWriteOnce`
- Host path: `/mnt/data`
- Storage class: `manual`

### 2. `data-pvc.yaml`
Create a Persistent Volume Claim named `data-pvc`:
- Access modes: `ReadWriteOnce`
- Request storage: `500Mi`
- Storage class: `manual`

### 3. `storage-pod.yaml`
Create a Pod named `storage-pod`:
- Container:
  - Name: `app`
  - Image: `busybox:1.35`
  - Command: `["sh", "-c", "echo 'Hello from PV!' > /app/data/hello.txt && cat /app/data/hello.txt && sleep 3600"]`
  - Mount the PVC at `/app/data`

## 📁 Files to Submit

```
~/rendudevops/ex08_k8s_pv_pvc/
├── data-pv.yaml
├── data-pvc.yaml
└── storage-pod.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

Persistent Volume structure:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: <pv-name>
spec:
  capacity:
    storage: <size>
  accessModes:
    - ReadWriteOnce
  storageClassName: <class-name>
  hostPath:
    path: <host-path>
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

Persistent Volume Claim structure:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <pvc-name>
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: <size>
  storageClassName: <class-name>
```
</details>

<details>
<summary>Click to reveal hint 3</summary>

Mount PVC in a Pod:
```yaml
spec:
  volumes:
  - name: my-storage
    persistentVolumeClaim:
      claimName: <pvc-name>
  containers:
  - name: app
    volumeMounts:
    - name: my-storage
      mountPath: /app/data
```
</details>

## ✅ Validation Criteria

**PV:**
- Named `data-pv`
- 1Gi capacity
- ReadWriteOnce access mode
- hostPath `/mnt/data`

**PVC:**
- Named `data-pvc`
- Requests 500Mi
- ReadWriteOnce access mode

**Pod:**
- Named `storage-pod`
- Mounts the PVC at `/app/data`

## 📖 Useful Commands

```bash
# Apply resources
kubectl apply -f data-pv.yaml
kubectl apply -f data-pvc.yaml
kubectl apply -f storage-pod.yaml

# Check PV status
kubectl get pv

# Check PVC status (should be "Bound")
kubectl get pvc

# Verify the mount in the pod
kubectl exec storage-pod -- ls -la /app/data
kubectl exec storage-pod -- cat /app/data/hello.txt

# Check pod logs
kubectl logs storage-pod
```

## 🔗 Resources
- [Kubernetes Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)
