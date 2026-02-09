# 🔬 Lab 03: The Blueprint
## "Building Custom Frontend Artifacts"

## 🔑 Core Concepts

- The `FROM`, `COPY`, `EXPOSE`, and `CMD` instructions.
- Building a versioned image from a Dockerfile.
- Understanding image layers and documentation.

## 🧩 Scenario
In a professional CI/CD pipeline, we don't manually configure servers. We create a "blueprint" (Dockerfile) to produce a custom frontend artifact. You need to create an automated way to package a specific company landing page into an immutable image that any engineer can deploy.

## 🎯 Objective
Write a Dockerfile to bundle a static website and document its networking requirements.

## 📥 Provided

- A local `index.html` file.

## 🛠️ Task List

- Create a file named `Dockerfile`.
- Use `nginx:alpine` as the base.
- `COPY` your `index.html` into `/usr/share/nginx/html/`.
- Add the `EXPOSE 80` instruction to document the intended port.
- Ensure the `CMD` is set to run Nginx in the foreground.
- Build the image with the tag `web-artifact:v1`.

## ⚠️ Constraints

- Do not use a generic "latest" tag; versioning is mandatory (`v1`).

## 🧪 Validation

- Run `docker history web-artifact:v1` to see your `COPY` and `EXPOSE` layers.
- Run a container from this image and verify the custom page loads in your browser.

## 🧠 Hints

- `EXPOSE` doesn't actually open the port to the host; it acts as documentation for other developers. You still need `-p` when running it!
