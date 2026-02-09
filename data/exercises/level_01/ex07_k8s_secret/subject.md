# Lab: Secrets - Handling Sensitive Data

## 🎯 Objective
Learn how to use Kubernetes Secrets to manage sensitive information like passwords and API keys.

## 📚 Theory

A **Secret** is an object that contains sensitive data such as passwords, OAuth tokens, or SSH keys. Using a Secret means you don't have to include confidential data in your application code.

Key differences from ConfigMaps:
- Secrets are **base64 encoded** (not encrypted by default!)
- Kubernetes provides additional features for Secrets (like mounting as tmpfs)
- RBAC can be applied specifically to Secrets

⚠️ **Important**: Base64 is NOT encryption! For production, enable encryption at rest and consider external secret management (Vault, AWS Secrets Manager, etc.)

Types of Secrets:
- `Opaque` - Arbitrary user-defined data (default)
- `kubernetes.io/dockerconfigjson` - Docker registry credentials
- `kubernetes.io/tls` - TLS certificate and key
- `kubernetes.io/basic-auth` - Basic authentication credentials

```
┌─────────────────────────────────────────────────────────────┐
│                         Secret                               │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  username: YWRtaW4=          (base64: admin)         │   │
│   │  password: cGFzc3dvcmQxMjM=  (base64: password123)   │   │
│   │  api-key: c2VjcmV0a2V5MTIz   (base64: secretkey123)  │   │
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

### 1. `db-secret.yaml`
Create an Opaque Secret named `db-credentials` with:
- `DB_USERNAME`: `admin` (base64 encoded)
- `DB_PASSWORD`: `supersecret123` (base64 encoded)

### 2. `secret-pod.yaml`
Create a Pod that uses the Secret:
- Name: `secret-test-pod`
- Container:
  - Name: `app`
  - Image: `busybox:1.35`
  - Command: `["sh", "-c", "echo Username: $DB_USERNAME && echo Password length: $(echo -n $DB_PASSWORD | wc -c) && sleep 3600"]`
  - Load `DB_USERNAME` and `DB_PASSWORD` from the secret as environment variables

## 📁 Files to Submit

```
~/rendudevops/ex07_k8s_secret/
├── db-secret.yaml
└── secret-pod.yaml
```

## 💡 Hints

<details>
<summary>Click to reveal hint 1</summary>

To encode a value in base64:
```bash
echo -n 'admin' | base64
# Output: YWRtaW4=

echo -n 'supersecret123' | base64
# Output: c3VwZXJzZWNyZXQxMjM=
```
</details>

<details>
<summary>Click to reveal hint 2</summary>

Secret manifest structure:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <secret-name>
type: Opaque
data:
  KEY1: <base64-encoded-value>
  KEY2: <base64-encoded-value>
```
</details>

<details>
<summary>Click to reveal hint 3</summary>

Using Secret in a Pod with individual env vars:
```yaml
env:
- name: MY_SECRET
  valueFrom:
    secretKeyRef:
      name: <secret-name>
      key: <key-in-secret>
```
</details>

## ✅ Validation Criteria

**Secret:**
- Named `db-credentials`
- Type `Opaque`
- Contains `DB_USERNAME` (base64 of 'admin')
- Contains `DB_PASSWORD` (base64 of 'supersecret123')

**Pod:**
- Named `secret-test-pod`
- Uses secret values as environment variables

## 📖 Useful Commands

```bash
# Encode/Decode base64
echo -n 'admin' | base64
echo 'YWRtaW4=' | base64 -d

# Apply secret
kubectl apply -f db-secret.yaml

# List secrets
kubectl get secrets

# Describe secret (values hidden)
kubectl describe secret db-credentials

# View secret data (base64 encoded)
kubectl get secret db-credentials -o yaml

# Decode a secret value
kubectl get secret db-credentials -o jsonpath='{.data.DB_USERNAME}' | base64 -d

# Apply pod
kubectl apply -f secret-pod.yaml

# Check env vars in pod
kubectl exec secret-test-pod -- env | grep DB_
```

## 🔒 Security Best Practices

1. Enable **encryption at rest** for Secrets in etcd
2. Use **RBAC** to restrict access to Secrets
3. Consider using **external secret management** (HashiCorp Vault, AWS Secrets Manager)
4. Avoid committing Secrets to version control
5. Use tools like **sealed-secrets** or **sops** for GitOps workflows

## 🔗 Resources
- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Encrypting Secret Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
