# Python Container + MCP Stdio Integration

This folder contains a **Dockerized version of a terminal server** that integrates with MCP using **standard input/output (stdio)**.

The goal of this setup is to run the terminal server inside a **Docker container** while keeping file operations synced with your local machine.

---

## How It Works

- The terminal server runs **inside a Docker container**
- Your local folder `mcp/workspace` is **mounted into the container**
- Any files created inside the container are written to the mounted workspace
- These files immediately appear on your host machine


## Dockerfile Overview

The Dockerfile performs the following steps:

1. Uses the **Python 3.11 slim** base image  
2. Sets `/app` as the container working directory  
3. Copies the terminal server code into the container  
4. Installs dependencies from `requirements.txt`  
5. Exposes port `5000`  
   - (Only relevant if your server actually listens on a network port)  
6. Runs `terminal_server.py` when the container starts  

---

## MCP Docker Configuration

```json
"terminal_docker": {
  "command": "docker",
  "args": [
    "run",
    "-i",
    "--rm",
    "--init",
    "-e",
    "DOCKER_CONTAINER=true",
    "-v",
    "/Users/himanshu/github_himanshu/Model-Context-Protocol-MCP-/mcp/workspace:/root/mcp/workspace",
    "terminal_server_docker"
  ]
}


## Argument Breakdown
docker run

Starts a new container.

-i

Runs the container in interactive mode (stdin stays open).
Required for MCP stdio communication.

--rm

Automatically deletes the container when it exits.

--init

Adds a minimal init process for better signal handling and cleanup.

-e DOCKER_CONTAINER=true

Sets an environment variable inside the container.
Useful for conditional logic in your code.

-v <host_path>:<container_path>

Mounts your local workspace into the container.

terminal_server_docker

The Docker image name.


## Building the Docker Image

Run this command from the folder containing the Dockerfile:

docker build -t terminal_server_docker .