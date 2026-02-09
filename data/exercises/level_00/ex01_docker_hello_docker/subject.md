# 🔬 Lab 01: The Digital Hello
## "Establishing the Handshake"

## 🔑 Core Concepts

- Pulling and running your first container
- The difference between an Image and a Container
- Reading terminal output for success

## 🧩 Scenario
You’ve just joined the "Grade Me" dev team. Before we touch the complex grading app, the Lead Architect wants to ensure your local environment is set up. Your first task is to prove you can talk to the Docker Engine by pulling down a "test signal" from the cloud.

## 🎯 Objective
Successfully pull the hello-world image and run it to verify Docker is operational.

## 📥 Provided

- A terminal with Docker installed.

## 🛠️ Task List

- Check your Docker version to ensure the engine is running (did you try docker --version!).
- Download and run the official hello-world image from Docker Hub.
- Observe the output provided by the container to understand what Docker did "under the hood."

## ⚠️ Constraints

- Use the official hello-world image only.
- Do not attempt to create any files or folders yet.

## 🧪 Validation

- Run docker images to see the hello-world image in your local library.
- Look for the text: "Hello from Docker! This message shows that your installation appears to be working correctly." in your terminal.

## 🧠 Hints

- If you get a "permission denied" error, you might need to prefix your command with sudo (depending on your OS).
- Docker combines "downloading" and "running" into one single command: run.
