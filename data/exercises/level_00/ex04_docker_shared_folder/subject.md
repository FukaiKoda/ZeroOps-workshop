# 🔬 Lab 04: The Shared Folder
## "Development Workflows & Bind Mounts"

## 🔑 Core Concepts

- Bind mounts vs. static copies (`COPY`).
- Live editing ("hot reload") while a container keeps running.
- Why bind mounts are for local development (not production).

## 🧩 Scenario
Rebuilding an image for every tiny HTML/CSS change is slow.

For local development, you can **mount a host folder into the container** so that edits on your machine instantly appear inside the running container.

> In production, you should use the immutable image approach (`COPY`).

## 🎯 Objective
Run an official Nginx container with a bind mount so that editing a local `index.html` immediately updates what Nginx serves—without rebuilding or restarting the container.

## 📁 Workspace

Create your submission folder:

```
~/rendudevops/ex04_docker_shared_folder/
└── site-content/
    └── index.html
```

## 🛠️ Task List

- Create `site-content/index.html` (any valid HTML is fine).
- Start an **official** `nginx` container in detached mode.
- (Recommended) Name the container: `shared_site`.
- Publish a port so you can view it in a browser (example: `-p 8080:80`).
- Bind-mount your host folder into the container:

  - Host: `$(pwd)/site-content`
  - Container: `/usr/share/nginx/html`

- Edit `site-content/index.html` on your host.
- Refresh the browser and confirm changes appear.

## ⚠️ Constraints

- The container must **NOT** be restarted or rebuilt to see changes.
- The mount must be a **bind mount** (use `-v` or `--mount type=bind`).

## 🧪 Validation

- `docker inspect <container>` shows a mount to `/usr/share/nginx/html`.
- The mount source points to your `site-content` folder.
- `docker exec <container> cat /usr/share/nginx/html/index.html` matches your host `site-content/index.html`.
- Your `site-content/index.html` must be modified **after** the container starts (this is how we prove live updates).

## 🧠 Hints

- Use `$(pwd)` to avoid relative-path issues.
- Keep the container running; otherwise `docker exec` won’t work.
