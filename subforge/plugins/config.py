"""
SubForge Plugin Configuration
Configuration settings for plugin system
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class PluginPermission(Enum):
    """Plugin permission types"""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    NETWORK = "network"
    EXECUTE = "execute"
    DATABASE = "database"
    SYSTEM_INFO = "system_info"
    ENVIRONMENT = "environment"
    PROCESS_SPAWN = "process_spawn"


class PluginLoadStrategy(Enum):
    """Plugin loading strategies"""

    LAZY = "lazy"  # Load plugins on demand
    EAGER = "eager"  # Load all plugins at startup
    SELECTIVE = "selective"  # Load based on configuration


@dataclass
class PluginSecurityConfig:
    """Security configuration for plugins"""

    enable_sandbox: bool = True
    allowed_permissions: List[PluginPermission] = field(
        default_factory=lambda: [
            PluginPermission.FILE_READ,
            PluginPermission.SYSTEM_INFO,
            PluginPermission.ENVIRONMENT,
        ]
    )
    denied_permissions: List[PluginPermission] = field(
        default_factory=lambda: [PluginPermission.EXECUTE, PluginPermission.PROCESS_SPAWN]
    )
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    timeout_seconds: int = 30
    allowed_paths: List[Path] = field(default_factory=list)
    denied_paths: List[Path] = field(default_factory=lambda: [Path("/etc"), Path("/sys")])
    allow_network: bool = False
    allowed_hosts: List[str] = field(default_factory=list)


@dataclass
class PluginConfig:
    """Main plugin configuration"""

    # Paths
    plugin_dir: Path = field(default_factory=lambda: Path.home() / ".subforge" / "plugins")
    cache_dir: Path = field(default_factory=lambda: Path.home() / ".subforge" / "plugin_cache")
    temp_dir: Path = field(default_factory=lambda: Path("/tmp/subforge_plugins"))

    # Loading settings
    load_strategy: PluginLoadStrategy = PluginLoadStrategy.LAZY
    auto_activate: bool = False
    auto_update: bool = True
    check_dependencies: bool = True
    validate_signatures: bool = False

    # Limits
    max_plugins: int = 100
    max_plugin_size_mb: int = 10
    max_dependency_depth: int = 5

    # Security
    security: PluginSecurityConfig = field(default_factory=PluginSecurityConfig)

    # Performance
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    parallel_loading: bool = True
    max_parallel_loads: int = 4

    # Monitoring
    enable_metrics: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"

    # Repository settings
    plugin_repositories: List[str] = field(
        default_factory=lambda: [
            "https://plugins.subforge.io",
            "https://github.com/subforge/plugins",
        ]
    )
    allow_third_party: bool = True
    trusted_authors: List[str] = field(default_factory=lambda: ["SubForge", "Official"])

    def __post_init__(self):
        """Post-initialization setup"""
        # Create directories if they don't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        if not self.temp_dir.exists():
            self.temp_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """
        Validate configuration

        Returns:
            True if configuration is valid
        """
        # Check paths
        if not self.plugin_dir.exists():
            return False

        # Check limits
        if self.max_plugins <= 0:
            return False

        if self.max_plugin_size_mb <= 0:
            return False

        # Check security settings
        if self.security.max_memory_mb <= 0:
            return False

        if self.security.max_cpu_percent <= 0 or self.security.max_cpu_percent > 100:
            return False

        return True

    def to_dict(self) -> dict:
        """Convert configuration to dictionary"""
        return {
            "plugin_dir": str(self.plugin_dir),
            "cache_dir": str(self.cache_dir),
            "temp_dir": str(self.temp_dir),
            "load_strategy": self.load_strategy.value,
            "auto_activate": self.auto_activate,
            "auto_update": self.auto_update,
            "check_dependencies": self.check_dependencies,
            "validate_signatures": self.validate_signatures,
            "max_plugins": self.max_plugins,
            "max_plugin_size_mb": self.max_plugin_size_mb,
            "max_dependency_depth": self.max_dependency_depth,
            "security": {
                "enable_sandbox": self.security.enable_sandbox,
                "allowed_permissions": [p.value for p in self.security.allowed_permissions],
                "denied_permissions": [p.value for p in self.security.denied_permissions],
                "max_memory_mb": self.security.max_memory_mb,
                "max_cpu_percent": self.security.max_cpu_percent,
                "timeout_seconds": self.security.timeout_seconds,
                "allowed_paths": [str(p) for p in self.security.allowed_paths],
                "denied_paths": [str(p) for p in self.security.denied_paths],
                "allow_network": self.security.allow_network,
                "allowed_hosts": self.security.allowed_hosts,
            },
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "parallel_loading": self.parallel_loading,
            "max_parallel_loads": self.max_parallel_loads,
            "enable_metrics": self.enable_metrics,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "plugin_repositories": self.plugin_repositories,
            "allow_third_party": self.allow_third_party,
            "trusted_authors": self.trusted_authors,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PluginConfig":
        """
        Create configuration from dictionary

        Args:
            data: Configuration dictionary

        Returns:
            PluginConfig instance
        """
        # Parse security config
        security_data = data.get("security", {})
        security = PluginSecurityConfig(
            enable_sandbox=security_data.get("enable_sandbox", True),
            allowed_permissions=[
                PluginPermission(p) for p in security_data.get("allowed_permissions", [])
            ],
            denied_permissions=[
                PluginPermission(p) for p in security_data.get("denied_permissions", [])
            ],
            max_memory_mb=security_data.get("max_memory_mb", 512),
            max_cpu_percent=security_data.get("max_cpu_percent", 50),
            timeout_seconds=security_data.get("timeout_seconds", 30),
            allowed_paths=[Path(p) for p in security_data.get("allowed_paths", [])],
            denied_paths=[Path(p) for p in security_data.get("denied_paths", [])],
            allow_network=security_data.get("allow_network", False),
            allowed_hosts=security_data.get("allowed_hosts", []),
        )

        return cls(
            plugin_dir=Path(data.get("plugin_dir", Path.home() / ".subforge" / "plugins")),
            cache_dir=Path(data.get("cache_dir", Path.home() / ".subforge" / "plugin_cache")),
            temp_dir=Path(data.get("temp_dir", "/tmp/subforge_plugins")),
            load_strategy=PluginLoadStrategy(
                data.get("load_strategy", PluginLoadStrategy.LAZY.value)
            ),
            auto_activate=data.get("auto_activate", False),
            auto_update=data.get("auto_update", True),
            check_dependencies=data.get("check_dependencies", True),
            validate_signatures=data.get("validate_signatures", False),
            max_plugins=data.get("max_plugins", 100),
            max_plugin_size_mb=data.get("max_plugin_size_mb", 10),
            max_dependency_depth=data.get("max_dependency_depth", 5),
            security=security,
            enable_caching=data.get("enable_caching", True),
            cache_ttl_seconds=data.get("cache_ttl_seconds", 3600),
            parallel_loading=data.get("parallel_loading", True),
            max_parallel_loads=data.get("max_parallel_loads", 4),
            enable_metrics=data.get("enable_metrics", True),
            enable_logging=data.get("enable_logging", True),
            log_level=data.get("log_level", "INFO"),
            plugin_repositories=data.get("plugin_repositories", []),
            allow_third_party=data.get("allow_third_party", True),
            trusted_authors=data.get("trusted_authors", ["SubForge", "Official"]),
        )