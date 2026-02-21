# 🔬 Lab 03: The Environment Room
## "Using Environment Variables"

## 🔑 Core Concepts

- Setting a default value with `ENV` in a Dockerfile.
- Overriding configuration at runtime with `docker run -e`.
- Building one image that behaves differently depending on its environment.

## 🧩 Scenario
The "Grade Me" service needs to change behavior depending on where it runs (dev vs prod). You must **not** hardcode that configuration into the image.

Instead, you will bake a **default** value into the image, and then override it **at runtime** for a second container.

## 🎯 Objective
Build an image that uses an environment variable, then prove you can override it with `-e` when running a container.

## 📁 Workspace

expected submission folder:

```
~/rendudevops/ex03_docker_environment_room/
└── Dockerfile
```

## 🛠️ Task List

- Create a `Dockerfile` based on Alpine.
- Add a default environment variable: `APP_COLOR=blue`.
- Add a `CMD` that prints the value and keeps the container alive:

	Example (you can format it differently):

	```dockerfile
	CMD sh -c 'echo "APP_COLOR is: $APP_COLOR" && sleep infinity'
	```

- Build your image with the name grademe-config with exact tag v1.

- Run **two** containers from the same image:
	- One container with the default value (no overrides).
	- One container overriding the variable to red using `-e APP_COLOR=red`.

- Verify inside the "red" container:

	```bash
	docker exec <container> printenv APP_COLOR
	```

## ⚠️ Constraints

- Do **not** rebuild the image to change the color to red.
- The override must happen at runtime using `-e`.

## 🧪 Validation

- `docker image inspect grademe-config:v1` shows the image exists.
- `docker inspect <container>` shows one container has `APP_COLOR=blue` and another has `APP_COLOR=red`.
- `docker exec <red-container> printenv APP_COLOR` prints `red`.

## 🧠 Hints

- `ENV` in a Dockerfile sets a **default**.
- `-e` in `docker run` overrides that default for a specific container.
- If your container exits immediately, you won't be able to `docker exec` into it—use `sleep infinity`.