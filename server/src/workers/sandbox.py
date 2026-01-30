"""
Sandbox: Security configuration and resource limits for Docker containers.

This module ensures that student code cannot:
- Access the host network
- Consume excessive resources (CPU, RAM)
- Break out of the container
- Run indefinitely
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SandboxConfig:
    """
    Security and resource configuration for a sandbox container.
    
    Based on best practices from:
    - Docker security documentation
    - 42 School Moulinette sandboxing
    - CTF/Competitive programming sandboxes
    """

    # ==========================================
    # Network Isolation
    # ==========================================
    network_mode: str = "none"  # ❌ No network access (no internet, no host network)
    """
    Options:
    - "none": Most secure (no network)
    - "bridge": Default (can be restricted)
    - "host": Dangerous (allows access to host network)
    """

    # ==========================================
    # Resource Limits
    # ==========================================
    memory_limit: str = "256m"  # 256 MB RAM
    memory_swap_limit: str = "256m"  # No swap (prevent disk I/O DoS)
    cpu_limit: float = 1.0  # 1 CPU core max
    
    # ==========================================
    # Disk I/O Limits (Optional, requires `docker run --pids-limit`)
    # ==========================================
    pids_limit: int = 50  # Max 50 processes (prevent fork bomb)

    # ==========================================
    # File System
    # ==========================================
    read_only_rootfs: bool = False  # Allow writes to /tmp, /student
    # (Set to True for maximum security, False for practical grading)
    
    # ==========================================
    # User & Permissions
    # ==========================================
    user: str = "1000:1000"  # Non-root user (UID:GID)
    # If the container doesn't have UID 1000, the container startup may fail
    # In that case, use user="nobody" or create the user in the Dockerfile

    # ==========================================
    # Capabilities (what root-level operations are allowed)
    # ==========================================
    cap_drop: list = None  # Drop dangerous capabilities
    cap_add: list = None   # Add specific capabilities

    def __post_init__(self):
        """Set default capabilities."""
        if self.cap_drop is None:
            self.cap_drop = [
                "NET_ADMIN",      # Prevent network config
                "SYS_ADMIN",      # Prevent system admin ops
                "SYS_PTRACE",     # Prevent process tracing
                "DAC_OVERRIDE",   # Prevent permission override
            ]
        if self.cap_add is None:
            self.cap_add = []  # No additional capabilities


class SandboxPresets:
    """Pre-configured sandbox profiles for different use cases."""

    @staticmethod
    def python_safe() -> SandboxConfig:
        """
        Sandbox for running untrusted Python code.
        
        Restrictions:
        - No network
        - 256 MB RAM
        - 1 CPU core
        - Non-root user
        """
        return SandboxConfig(
            network_mode="none",
            memory_limit="256m",
            memory_swap_limit="256m",
            cpu_limit=1.0,
            pids_limit=50,
            user="1000:1000",
        )

    @staticmethod
    def c_safe() -> SandboxConfig:
        """
        Sandbox for running untrusted C code.
        
        Slightly more permissive than Python (for compilation):
        - No network
        - 512 MB RAM (for compilation)
        - 2 CPU cores (for faster compilation)
        - Non-root user
        """
        return SandboxConfig(
            network_mode="none",
            memory_limit="512m",
            memory_swap_limit="512m",
            cpu_limit=2.0,
            pids_limit=100,
            user="1000:1000",
        )

    @staticmethod
    def strict() -> SandboxConfig:
        """
        Maximum security: minimal resources and capabilities.
        
        Use for truly untrusted code.
        """
        return SandboxConfig(
            network_mode="none",
            memory_limit="128m",
            memory_swap_limit="128m",
            cpu_limit=0.5,
            pids_limit=20,
            user="nobody",
            read_only_rootfs=True,
        )


def get_sandbox_config(image_type: str) -> SandboxConfig:
    """
    Retrieve appropriate sandbox config based on docker image type.

    Args:
        image_type: "python-runner", "c-runner", "bash-runner", or "strict"

    Returns:
        SandboxConfig object
    """
    configs = {
        "python-runner": SandboxPresets.python_safe(),
        "python": SandboxPresets.python_safe(),
        "c-runner": SandboxPresets.c_safe(),
        "c": SandboxPresets.c_safe(),
        "bash-runner": SandboxPresets.c_safe(),
        "bash": SandboxPresets.c_safe(),
        "strict": SandboxPresets.strict(),
    }
    return configs.get(image_type, SandboxPresets.python_safe())


# ==========================================
# Docker API Kwargs Builder
# ==========================================

def sandbox_config_to_docker_kwargs(config: SandboxConfig) -> dict:
    """
    Convert SandboxConfig to docker.client.containers.run() kwargs.

    Usage:
        config = get_sandbox_config("python-runner")
        kwargs = sandbox_config_to_docker_kwargs(config)
        container = client.containers.run(..., **kwargs)

    Args:
        config: SandboxConfig object

    Returns:
        Dict of kwargs for docker.client.containers.run()
    """
    return {
        "network_mode": config.network_mode,
        "mem_limit": config.memory_limit,
        "memswap_limit": config.memory_swap_limit,
        "cpus": config.cpu_limit,
        "pids_limit": config.pids_limit,
        "user": config.user,
        "cap_drop": config.cap_drop,
        "cap_add": config.cap_add,
        "read_only": config.read_only_rootfs,
    }


if __name__ == "__main__":
    # Quick test: Print sandbox configs
    print("🔒 Python Sandbox:")
    print(SandboxPresets.python_safe())
    print("\n🔒 C Sandbox:")
    print(SandboxPresets.c_safe())
    print("\n🔒 Strict Sandbox:")
    print(SandboxPresets.strict())
