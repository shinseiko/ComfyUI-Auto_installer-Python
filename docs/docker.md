# Docker

The installer includes a fully configured Docker setup for containerized ComfyUI installations.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) (for GPU support)

## Quick Start

```bash
docker-compose up -d
```

Access ComfyUI at `http://localhost:8188`.

## Architecture

The Docker setup uses **bind mounts** to persist user data on the host:

```yaml
volumes:
  - ./docker_data/models:/app/models
  - ./docker_data/output:/app/output
  - ./docker_data/input:/app/input
  - ./docker_data/custom_nodes:/app/custom_nodes
```

The first boot seamlessly clones any missing components into the host-mounted `./docker_data` folders.

## Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `COMFYUI_EXTRA_ARGS` | Extra arguments passed to ComfyUI | `--listen 0.0.0.0` |

## Rebuilding

```bash
docker-compose build --no-cache
docker-compose up -d
```
