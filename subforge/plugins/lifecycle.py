"""
SubForge Plugin Lifecycle Manager
Manages plugin installation, activation, deactivation, and removal
"""

import asyncio
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from subforge.core.context.exceptions import ContextError
from subforge.plugins.config import PluginConfig
from subforge.plugins.plugin_manager import PluginMetadata, SubForgePlugin


class PluginState(Enum):
    """Plugin lifecycle states"""

    NOT_INSTALLED = "not_installed"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    INSTALLED = "installed"
    ACTIVATING = "activating"
    ACTIVE = "active"
    DEACTIVATING = "deactivating"
    INACTIVE = "inactive"
    UPDATING = "updating"
    UNINSTALLING = "uninstalling"
    ERROR = "error"
    DISABLED = "disabled"


class PluginEvent(Enum):
    """Plugin lifecycle events"""

    INSTALL_STARTED = "install_started"
    INSTALL_COMPLETED = "install_completed"
    INSTALL_FAILED = "install_failed"
    ACTIVATE_STARTED = "activate_started"
    ACTIVATE_COMPLETED = "activate_completed"
    ACTIVATE_FAILED = "activate_failed"
    DEACTIVATE_STARTED = "deactivate_started"
    DEACTIVATE_COMPLETED = "deactivate_completed"
    DEACTIVATE_FAILED = "deactivate_failed"
    UPDATE_STARTED = "update_started"
    UPDATE_COMPLETED = "update_completed"
    UPDATE_FAILED = "update_failed"
    UNINSTALL_STARTED = "uninstall_started"
    UNINSTALL_COMPLETED = "uninstall_completed"
    UNINSTALL_FAILED = "uninstall_failed"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class PluginStateInfo:
    """Information about plugin state"""

    plugin_id: str
    state: PluginState
    previous_state: Optional[PluginState] = None
    last_updated: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    metadata: Optional[PluginMetadata] = None
    instance: Optional[SubForgePlugin] = None
    installation_path: Optional[Path] = None
    version: Optional[str] = None
    dependencies_installed: bool = False
    health_check_passed: bool = False


class PluginLifecycleError(ContextError):
    """Raised for plugin lifecycle errors"""


class IPluginStore:
    """Interface for plugin storage"""

    async def save_plugin(self, plugin_id: str, plugin_data: bytes) -> Path:
        """Save plugin to storage"""
        raise NotImplementedError

    async def load_plugin(self, plugin_id: str) -> bytes:
        """Load plugin from storage"""
        raise NotImplementedError

    async def delete_plugin(self, plugin_id: str) -> bool:
        """Delete plugin from storage"""
        raise NotImplementedError

    async def plugin_exists(self, plugin_id: str) -> bool:
        """Check if plugin exists in storage"""
        raise NotImplementedError


class LocalPluginStore(IPluginStore):
    """Local filesystem plugin storage"""

    def __init__(self, storage_dir: Path):
        """
        Initialize local plugin store

        Args:
            storage_dir: Directory for plugin storage
        """
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_plugin(self, plugin_id: str, plugin_data: bytes) -> Path:
        """Save plugin to local storage"""
        plugin_path = self.storage_dir / f"{plugin_id}.plugin"
        plugin_path.write_bytes(plugin_data)
        return plugin_path

    async def load_plugin(self, plugin_id: str) -> bytes:
        """Load plugin from local storage"""
        plugin_path = self.storage_dir / f"{plugin_id}.plugin"
        if not plugin_path.exists():
            raise PluginLifecycleError(f"Plugin {plugin_id} not found in storage")
        return plugin_path.read_bytes()

    async def delete_plugin(self, plugin_id: str) -> bool:
        """Delete plugin from local storage"""
        plugin_path = self.storage_dir / f"{plugin_id}.plugin"
        if plugin_path.exists():
            plugin_path.unlink()
            return True
        return False

    async def plugin_exists(self, plugin_id: str) -> bool:
        """Check if plugin exists in local storage"""
        plugin_path = self.storage_dir / f"{plugin_id}.plugin"
        return plugin_path.exists()


class PluginLifecycle:
    """
    Manages plugin lifecycle operations
    """

    def __init__(self, plugin_store: IPluginStore, config: Optional[PluginConfig] = None):
        """
        Initialize plugin lifecycle manager

        Args:
            plugin_store: Plugin storage implementation
            config: Plugin configuration
        """
        self.plugin_store = plugin_store
        self.config = config or PluginConfig()

        # Plugin state tracking
        self.plugins: Dict[str, PluginStateInfo] = {}

        # Event listeners
        self.event_listeners: Dict[PluginEvent, List[callable]] = {
            event: [] for event in PluginEvent
        }

        # State transition rules
        self.valid_transitions = {
            PluginState.NOT_INSTALLED: [PluginState.DOWNLOADING, PluginState.INSTALLING],
            PluginState.DOWNLOADING: [PluginState.INSTALLING, PluginState.ERROR],
            PluginState.INSTALLING: [PluginState.INSTALLED, PluginState.ERROR],
            PluginState.INSTALLED: [
                PluginState.ACTIVATING,
                PluginState.UPDATING,
                PluginState.UNINSTALLING,
                PluginState.DISABLED,
            ],
            PluginState.ACTIVATING: [PluginState.ACTIVE, PluginState.ERROR, PluginState.INACTIVE],
            PluginState.ACTIVE: [
                PluginState.DEACTIVATING,
                PluginState.UPDATING,
                PluginState.ERROR,
                PluginState.DISABLED,
            ],
            PluginState.DEACTIVATING: [PluginState.INACTIVE, PluginState.ERROR],
            PluginState.INACTIVE: [
                PluginState.ACTIVATING,
                PluginState.UNINSTALLING,
                PluginState.UPDATING,
                PluginState.DISABLED,
            ],
            PluginState.UPDATING: [PluginState.INSTALLED, PluginState.ERROR],
            PluginState.UNINSTALLING: [PluginState.NOT_INSTALLED, PluginState.ERROR],
            PluginState.ERROR: [
                PluginState.INSTALLING,
                PluginState.UNINSTALLING,
                PluginState.DISABLED,
            ],
            PluginState.DISABLED: [PluginState.INSTALLED, PluginState.UNINSTALLING],
        }

    def add_event_listener(self, event: PluginEvent, listener: callable):
        """
        Add an event listener

        Args:
            event: Event to listen for
            listener: Callback function
        """
        self.event_listeners[event].append(listener)

    async def _emit_event(self, event: PluginEvent, plugin_id: str, **kwargs):
        """
        Emit a lifecycle event

        Args:
            event: Event to emit
            plugin_id: Plugin ID
            **kwargs: Additional event data
        """
        for listener in self.event_listeners[event]:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(plugin_id, event, **kwargs)
                else:
                    listener(plugin_id, event, **kwargs)
            except Exception as e:
                print(f"Error in event listener: {e}")

    def _can_transition(self, current_state: PluginState, new_state: PluginState) -> bool:
        """
        Check if state transition is valid

        Args:
            current_state: Current plugin state
            new_state: Desired new state

        Returns:
            True if transition is valid
        """
        return new_state in self.valid_transitions.get(current_state, [])

    async def _update_state(
        self, plugin_id: str, new_state: PluginState, error_message: Optional[str] = None
    ):
        """
        Update plugin state

        Args:
            plugin_id: Plugin ID
            new_state: New state
            error_message: Error message if applicable
        """
        if plugin_id not in self.plugins:
            self.plugins[plugin_id] = PluginStateInfo(
                plugin_id=plugin_id, state=new_state, last_updated=datetime.now()
            )
        else:
            state_info = self.plugins[plugin_id]
            state_info.previous_state = state_info.state
            state_info.state = new_state
            state_info.last_updated = datetime.now()
            if error_message:
                state_info.error_message = error_message

    async def install(
        self, plugin: SubForgePlugin, plugin_id: Optional[str] = None
    ) -> bool:
        """
        Install a plugin

        Args:
            plugin: Plugin to install
            plugin_id: Optional plugin ID

        Returns:
            True if installation successful

        Raises:
            PluginLifecycleError: If installation fails
        """
        metadata = plugin.get_metadata()
        plugin_id = plugin_id or metadata.name

        # Check if already installed
        if plugin_id in self.plugins and self.plugins[plugin_id].state not in [
            PluginState.NOT_INSTALLED,
            PluginState.ERROR,
        ]:
            raise PluginLifecycleError(f"Plugin {plugin_id} is already installed")

        try:
            # Update state
            await self._update_state(plugin_id, PluginState.INSTALLING)
            await self._emit_event(PluginEvent.INSTALL_STARTED, plugin_id)

            # Validate plugin
            if not plugin.validate():
                raise PluginLifecycleError(f"Plugin {plugin_id} validation failed")

            # Check dependencies
            if self.config.check_dependencies and metadata.dependencies:
                missing_deps = await self._check_dependencies(metadata.dependencies)
                if missing_deps:
                    raise PluginLifecycleError(
                        f"Missing dependencies for {plugin_id}: {missing_deps}"
                    )

            # Initialize plugin
            if not plugin.initialize(metadata.config):
                raise PluginLifecycleError(f"Plugin {plugin_id} initialization failed")

            # Save plugin metadata
            plugin_data = json.dumps(
                {
                    "metadata": {
                        "name": metadata.name,
                        "version": metadata.version,
                        "author": metadata.author,
                        "description": metadata.description,
                        "type": metadata.type,
                        "dependencies": metadata.dependencies,
                        "config": metadata.config,
                    },
                    "installed_at": datetime.now().isoformat(),
                }
            ).encode()

            installation_path = await self.plugin_store.save_plugin(plugin_id, plugin_data)

            # Update state info
            self.plugins[plugin_id].metadata = metadata
            self.plugins[plugin_id].instance = plugin
            self.plugins[plugin_id].installation_path = installation_path
            self.plugins[plugin_id].version = metadata.version
            self.plugins[plugin_id].dependencies_installed = True

            # Update state
            await self._update_state(plugin_id, PluginState.INSTALLED)
            await self._emit_event(PluginEvent.INSTALL_COMPLETED, plugin_id)

            print(f"✅ Plugin {plugin_id} installed successfully")
            return True

        except Exception as e:
            await self._update_state(plugin_id, PluginState.ERROR, str(e))
            await self._emit_event(PluginEvent.INSTALL_FAILED, plugin_id, error=str(e))
            raise PluginLifecycleError(f"Failed to install plugin {plugin_id}: {e}")

    async def activate(self, plugin_id: str) -> bool:
        """
        Activate an installed plugin

        Args:
            plugin_id: Plugin ID

        Returns:
            True if activation successful
        """
        if plugin_id not in self.plugins:
            raise PluginLifecycleError(f"Plugin {plugin_id} not found")

        state_info = self.plugins[plugin_id]

        # Check current state
        if state_info.state == PluginState.ACTIVE:
            return True

        if state_info.state not in [PluginState.INSTALLED, PluginState.INACTIVE]:
            raise PluginLifecycleError(
                f"Cannot activate plugin {plugin_id} from state {state_info.state}"
            )

        try:
            # Update state
            await self._update_state(plugin_id, PluginState.ACTIVATING)
            await self._emit_event(PluginEvent.ACTIVATE_STARTED, plugin_id)

            # Health check
            if state_info.instance:
                state_info.health_check_passed = state_info.instance.validate()
                if not state_info.health_check_passed:
                    raise PluginLifecycleError(f"Plugin {plugin_id} health check failed")

            # Update state
            await self._update_state(plugin_id, PluginState.ACTIVE)
            await self._emit_event(PluginEvent.ACTIVATE_COMPLETED, plugin_id)

            print(f"✅ Plugin {plugin_id} activated successfully")
            return True

        except Exception as e:
            await self._update_state(plugin_id, PluginState.INACTIVE, str(e))
            await self._emit_event(PluginEvent.ACTIVATE_FAILED, plugin_id, error=str(e))
            raise PluginLifecycleError(f"Failed to activate plugin {plugin_id}: {e}")

    async def deactivate(self, plugin_id: str) -> bool:
        """
        Deactivate an active plugin

        Args:
            plugin_id: Plugin ID

        Returns:
            True if deactivation successful
        """
        if plugin_id not in self.plugins:
            raise PluginLifecycleError(f"Plugin {plugin_id} not found")

        state_info = self.plugins[plugin_id]

        # Check current state
        if state_info.state == PluginState.INACTIVE:
            return True

        if state_info.state != PluginState.ACTIVE:
            raise PluginLifecycleError(
                f"Cannot deactivate plugin {plugin_id} from state {state_info.state}"
            )

        try:
            # Update state
            await self._update_state(plugin_id, PluginState.DEACTIVATING)
            await self._emit_event(PluginEvent.DEACTIVATE_STARTED, plugin_id)

            # Cleanup plugin resources
            if state_info.instance:
                state_info.instance.cleanup()

            # Update state
            await self._update_state(plugin_id, PluginState.INACTIVE)
            await self._emit_event(PluginEvent.DEACTIVATE_COMPLETED, plugin_id)

            print(f"✅ Plugin {plugin_id} deactivated successfully")
            return True

        except Exception as e:
            await self._update_state(plugin_id, PluginState.ERROR, str(e))
            await self._emit_event(PluginEvent.DEACTIVATE_FAILED, plugin_id, error=str(e))
            raise PluginLifecycleError(f"Failed to deactivate plugin {plugin_id}: {e}")

    async def uninstall(self, plugin_id: str) -> bool:
        """
        Uninstall a plugin

        Args:
            plugin_id: Plugin ID

        Returns:
            True if uninstallation successful
        """
        if plugin_id not in self.plugins:
            raise PluginLifecycleError(f"Plugin {plugin_id} not found")

        state_info = self.plugins[plugin_id]

        # Deactivate if active
        if state_info.state == PluginState.ACTIVE:
            await self.deactivate(plugin_id)

        try:
            # Update state
            await self._update_state(plugin_id, PluginState.UNINSTALLING)
            await self._emit_event(PluginEvent.UNINSTALL_STARTED, plugin_id)

            # Cleanup plugin resources
            if state_info.instance:
                state_info.instance.cleanup()

            # Remove from storage
            await self.plugin_store.delete_plugin(plugin_id)

            # Remove from registry
            del self.plugins[plugin_id]

            await self._emit_event(PluginEvent.UNINSTALL_COMPLETED, plugin_id)

            print(f"✅ Plugin {plugin_id} uninstalled successfully")
            return True

        except Exception as e:
            await self._update_state(plugin_id, PluginState.ERROR, str(e))
            await self._emit_event(PluginEvent.UNINSTALL_FAILED, plugin_id, error=str(e))
            raise PluginLifecycleError(f"Failed to uninstall plugin {plugin_id}: {e}")

    async def update(self, plugin_id: str, new_version: str) -> bool:
        """
        Update a plugin to a new version

        Args:
            plugin_id: Plugin ID
            new_version: New version to install

        Returns:
            True if update successful
        """
        if plugin_id not in self.plugins:
            raise PluginLifecycleError(f"Plugin {plugin_id} not found")

        state_info = self.plugins[plugin_id]

        # Deactivate if active
        was_active = state_info.state == PluginState.ACTIVE
        if was_active:
            await self.deactivate(plugin_id)

        try:
            # Update state
            await self._update_state(plugin_id, PluginState.UPDATING)
            await self._emit_event(PluginEvent.UPDATE_STARTED, plugin_id, version=new_version)

            # TODO: Implement actual update logic
            # This would involve downloading new version, backing up old version,
            # installing new version, and migrating data if needed

            # Update version
            state_info.version = new_version

            # Update state
            await self._update_state(plugin_id, PluginState.INSTALLED)
            await self._emit_event(PluginEvent.UPDATE_COMPLETED, plugin_id, version=new_version)

            # Reactivate if was active
            if was_active:
                await self.activate(plugin_id)

            print(f"✅ Plugin {plugin_id} updated to version {new_version}")
            return True

        except Exception as e:
            await self._update_state(plugin_id, PluginState.ERROR, str(e))
            await self._emit_event(PluginEvent.UPDATE_FAILED, plugin_id, error=str(e))
            raise PluginLifecycleError(f"Failed to update plugin {plugin_id}: {e}")

    async def _check_dependencies(self, dependencies: List[str]) -> List[str]:
        """
        Check plugin dependencies

        Args:
            dependencies: List of required dependencies

        Returns:
            List of missing dependencies
        """
        missing = []
        for dep in dependencies:
            # Check if dependency is installed
            if dep not in self.plugins or self.plugins[dep].state not in [
                PluginState.INSTALLED,
                PluginState.ACTIVE,
            ]:
                missing.append(dep)
        return missing

    def get_plugin_state(self, plugin_id: str) -> Optional[PluginState]:
        """
        Get current plugin state

        Args:
            plugin_id: Plugin ID

        Returns:
            Current plugin state or None
        """
        if plugin_id in self.plugins:
            return self.plugins[plugin_id].state
        return None

    def get_all_plugins(self) -> Dict[str, PluginStateInfo]:
        """
        Get all registered plugins

        Returns:
            Dictionary of plugin IDs and state info
        """
        return self.plugins.copy()

    def get_active_plugins(self) -> List[str]:
        """
        Get list of active plugins

        Returns:
            List of active plugin IDs
        """
        return [
            plugin_id
            for plugin_id, info in self.plugins.items()
            if info.state == PluginState.ACTIVE
        ]