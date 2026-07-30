## Dockerized MCP Server

This folder shows how to run an MCP server **inside a Docker container**. The server communicates via STDIO (same as [01-mcp-basics](../01-mcp-basics/)), but runs in an isolated container instead of on your host machine.

---

### Why Docker?

| Benefit | Details |
|---------|---------|
| **Isolation** | Commands run inside the container, not on your host |
| **Portability** | Anyone with Docker can run your server — no Python setup needed |
| **Safety** | Container is destroyed after each session (`--rm`) |
| **Volume mounting** | Workspace files are synced between container and host |

---

### How It Works

```
Cursor/Client → STDIO → Docker container → terminal_server.py → /workspace
                                                                     ↕
                                                           Host folder (mounted)
```

- The MCP client (Cursor, or a Python client) launches Docker instead of Python directly
- Docker starts the container, which runs `terminal_server.py`
- STDIO is used for communication (`-i` flag keeps stdin open)
- The host's workspace folder is mounted into the container with `-v`

---

### Files

| File | Purpose |
|------|---------|
| `terminal_server.py` | The MCP server (same `run_command` tool, but workspace-aware for Docker) |
| `Dockerfile` | Builds the container image with Python + MCP SDK |

---

### How to Run

> All commands run from the **repo root**.

#### 1. Build the Docker image

```bash
docker build -t terminal_server_docker learning/04-docker/
```

#### 2. Test it manually (verify the container works)

```bash
docker run -i --rm --init \
  -e DOCKER_CONTAINER=true \
  -v "$(pwd)/learning/01-mcp-basics/workspace:/workspace" \
  terminal_server_docker
```

This starts the server in STDIO mode inside the container. You won't see output (it's waiting for MCP protocol messages). Press `Ctrl+C` to stop.

#### 3. Test with MCP Inspector

```bash
uv run mcp dev learning/04-docker/terminal_server.py
```

This runs the server **locally** (not in Docker) using the Inspector — useful for verifying the tool works before containerizing.

#### 4. Use with Cursor

Add this to Cursor → Settings → MCP:

```json
{
  "mcpServers": {
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
        "<ABSOLUTE_PATH_TO_REPO>/learning/01-mcp-basics/workspace:/workspace",
        "terminal_server_docker"
      ]
    }
  }
}
```

> Replace `<ABSOLUTE_PATH_TO_REPO>` with the actual path to your cloned repository.

Now when Cursor calls the `run_command` tool, it runs inside Docker, and any files created appear in your local `workspace/` folder.

---

### Key Differences from 01-mcp-basics

| Aspect | 01-mcp-basics | 04-docker |
|--------|--------------|-----------|
| Server runs on | Host machine (Python) | Docker container |
| Client launches | `python terminal_server.py` | `docker run ... terminal_server_docker` |
| Workspace | Local folder | Mounted volume (`-v`) |
| Dependencies | Installed via `uv sync` | Baked into Docker image |
| Isolation | Process-level | Container-level |

---

### Docker Args Explained

| Arg | Purpose |
|-----|---------|
| `-i` | Interactive mode — keeps stdin open for MCP STDIO |
| `--rm` | Auto-delete container when it exits |
| `--init` | Adds init process for clean signal handling |
| `-e DOCKER_CONTAINER=true` | Env var so the server uses `/workspace` inside the container |
| `-v host:container` | Mounts local workspace into the container |
