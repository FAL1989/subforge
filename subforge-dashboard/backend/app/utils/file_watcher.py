"""
File watcher for monitoring SubForge directory changes
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from ..core.config import settings
from ..websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


class SubForgeFileHandler(FileSystemEventHandler):
    """
    File system event handler for SubForge files
    """

    def __init__(self, debounce_seconds: float = 1.0):
        super().__init__()
        self.debounce_seconds = debounce_seconds
        self._pending_events = {}

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification events"""
        if not event.is_directory:
            self._schedule_event_broadcast("file_modified", event)

    def on_created(self, event: FileSystemEvent):
        """Handle file creation events"""
        if not event.is_directory:
            self._schedule_event_broadcast("file_created", event)

    def on_deleted(self, event: FileSystemEvent):
        """Handle file deletion events"""
        if not event.is_directory:
            self._schedule_event_broadcast("file_deleted", event)

    def on_moved(self, event: FileSystemEvent):
        """Handle file move events"""
        if not event.is_directory:
            self._schedule_event_broadcast("file_moved", event)

    def _schedule_event_broadcast(self, event_type: str, event: FileSystemEvent):
        """Schedule event broadcast with debouncing"""
        file_path = event.src_path

        # Cancel existing timer for this file
        if file_path in self._pending_events:
            self._pending_events[file_path].cancel()

        # Schedule new broadcast
        loop = asyncio.get_event_loop()
        timer = loop.call_later(
            self.debounce_seconds,
            lambda: asyncio.create_task(self._broadcast_event(event_type, event)),
        )
        self._pending_events[file_path] = timer

    async def _broadcast_event(self, event_type: str, event: FileSystemEvent):
        """Broadcast file system event via WebSocket"""
        try:
            file_path = Path(event.src_path)
            relative_path = file_path.relative_to(Path.cwd())

            # Determine file category
            file_category = self._categorize_file(file_path)

            event_data = {
                "type": "file_system_event",
                "event_type": event_type,
                "data": {
                    "file_path": str(relative_path),
                    "absolute_path": str(file_path),
                    "file_category": file_category,
                    "file_name": file_path.name,
                    "file_size": file_path.stat().st_size if file_path.exists() else 0,
                },
            }

            await websocket_manager.broadcast_json(event_data)

            # Clean up pending event
            if event.src_path in self._pending_events:
                del self._pending_events[event.src_path]

            logger.debug(f"Broadcasted {event_type} event for {relative_path}")

        except Exception as e:
            logger.error(f"Error broadcasting file event: {e}")

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize file based on its location and type"""
        try:
            relative_path = file_path.relative_to(Path.cwd())
            path_parts = relative_path.parts

            if ".claude" in path_parts:
                if "agents" in path_parts:
                    return "agent_config"
                return "claude_config"

            elif ".subforge" in path_parts:
                if "PRPs" in path_parts:
                    return "prp"
                elif "workflows" in path_parts:
                    return "workflow"
                return "subforge_data"

            elif file_path.suffix == ".py":
                return "python_code"

            elif file_path.suffix in [".json", ".yaml", ".yml"]:
                return "config_file"

            elif file_path.suffix in [".md", ".txt"]:
                return "documentation"

            else:
                return "other"

        except ValueError:
            return "external"


class FileWatcher:
    """
    File watcher for monitoring SubForge directories
    """

    def __init__(self):
        self.observer: Optional[Observer] = None
        self.is_running = False
        self.watched_paths = []

    def start(self):
        """Start the file watcher"""
        if not settings.ENABLE_FILE_WATCHER:
            logger.info("File watcher disabled by configuration")
            return

        if self.is_running:
            logger.warning("File watcher is already running")
            return

        try:
            self.observer = Observer()
            event_handler = SubForgeFileHandler(
                debounce_seconds=settings.WATCHER_DEBOUNCE_SECONDS
            )

            # Watch SubForge directories
            paths_to_watch = [
                settings.CLAUDE_DIR,
                settings.SUBFORGE_DIR,
                Path.cwd() / "subforge",  # Main subforge module
            ]

            for path in paths_to_watch:
                if path.exists() and path.is_dir():
                    self.observer.schedule(event_handler, str(path), recursive=True)
                    self.watched_paths.append(str(path))
                    logger.info(f"Watching directory: {path}")
                else:
                    logger.warning(f"Directory not found, skipping: {path}")

            if self.watched_paths:
                self.observer.start()
                self.is_running = True
                logger.info(
                    f"File watcher started, watching {len(self.watched_paths)} directories"
                )
            else:
                logger.warning(
                    "No valid directories to watch, file watcher not started"
                )

        except Exception as e:
            logger.error(f"Failed to start file watcher: {e}")

    def stop(self):
        """Stop the file watcher"""
        if not self.is_running or not self.observer:
            return

        try:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.is_running = False
            self.watched_paths.clear()
            logger.info("File watcher stopped")

        except Exception as e:
            logger.error(f"Error stopping file watcher: {e}")

    def get_status(self) -> dict:
        """Get file watcher status"""
        return {
            "is_running": self.is_running,
            "watched_paths": self.watched_paths,
            "observer_alive": self.observer.is_alive() if self.observer else False,
        }


# Global file watcher instance
file_watcher = FileWatcher()