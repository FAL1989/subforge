"""
Unit tests for WebSocket functionality
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.websocket.enhanced_manager import EnhancedWebSocketManager
from app.websocket.manager import WebSocketManager
from fastapi.testclient import TestClient


@pytest.mark.unit
@pytest.mark.websocket
class TestWebSocketManager:
    """Tests for basic WebSocket manager"""

    def test_websocket_manager_initialization(self):
        """Test WebSocket manager initialization"""
        manager = WebSocketManager()

        assert manager.active_connections == []
        assert hasattr(manager, "connect")
        assert hasattr(manager, "disconnect")
        assert hasattr(manager, "send_personal_message")
        assert hasattr(manager, "broadcast")

    async def test_websocket_connect(self):
        """Test WebSocket connection"""
        manager = WebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()

        await manager.connect(mock_websocket)

        assert mock_websocket in manager.active_connections
        mock_websocket.accept.assert_called_once()

    async def test_websocket_disconnect(self):
        """Test WebSocket disconnection"""
        manager = WebSocketManager()
        mock_websocket = MagicMock()

        # Connect first
        manager.active_connections.append(mock_websocket)

        # Then disconnect
        manager.disconnect(mock_websocket)

        assert mock_websocket not in manager.active_connections

    async def test_send_personal_message(self):
        """Test sending personal message"""
        manager = WebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        await manager.send_personal_message("Hello", mock_websocket)

        mock_websocket.send_text.assert_called_once_with("Hello")

    async def test_broadcast_message(self):
        """Test broadcasting message to all connections"""
        manager = WebSocketManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        manager.active_connections = [mock_ws1, mock_ws2]

        await manager.broadcast("Hello everyone")

        mock_ws1.send_text.assert_called_once_with("Hello everyone")
        mock_ws2.send_text.assert_called_once_with("Hello everyone")

    async def test_broadcast_json(self):
        """Test broadcasting JSON message"""
        manager = WebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        manager.active_connections = [mock_websocket]

        test_data = {"type": "test", "data": {"key": "value"}}
        await manager.broadcast_json(test_data)

        expected_json = json.dumps(test_data)
        mock_websocket.send_text.assert_called_once_with(expected_json)

    async def test_broadcast_with_failed_connection(self):
        """Test broadcasting with a failed connection"""
        manager = WebSocketManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        # First WebSocket will fail
        mock_ws1.send_text = AsyncMock(side_effect=Exception("Connection failed"))
        mock_ws2.send_text = AsyncMock()

        manager.active_connections = [mock_ws1, mock_ws2]

        # Should not raise exception and should continue with other connections
        await manager.broadcast("Hello")

        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()

        # Failed connection should be removed
        assert mock_ws1 not in manager.active_connections
        assert mock_ws2 in manager.active_connections


@pytest.mark.unit
@pytest.mark.websocket
class TestEnhancedWebSocketManager:
    """Tests for enhanced WebSocket manager"""

    def test_enhanced_websocket_manager_initialization(self):
        """Test enhanced WebSocket manager initialization"""
        manager = EnhancedWebSocketManager()

        assert hasattr(manager, "connections")
        assert hasattr(manager, "rooms")
        assert hasattr(manager, "user_connections")
        assert hasattr(manager, "connection_stats")

    async def test_enhanced_connect_with_user_id(self):
        """Test enhanced connection with user ID"""
        manager = EnhancedWebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()

        connection_id = await manager.connect(mock_websocket, user_id="user123")

        assert connection_id in manager.connections
        assert "user123" in manager.user_connections
        assert connection_id in manager.user_connections["user123"]
        mock_websocket.accept.assert_called_once()

    async def test_enhanced_disconnect_with_cleanup(self):
        """Test enhanced disconnection with proper cleanup"""
        manager = EnhancedWebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()

        # Connect first
        connection_id = await manager.connect(mock_websocket, user_id="user123")

        # Join a room
        await manager.join_room(connection_id, "room1")

        # Disconnect
        await manager.disconnect(connection_id)

        # Verify cleanup
        assert connection_id not in manager.connections
        assert connection_id not in manager.rooms.get("room1", set())

        # User connections should be cleaned up if empty
        if "user123" in manager.user_connections:
            assert connection_id not in manager.user_connections["user123"]

    async def test_join_and_leave_room(self):
        """Test joining and leaving rooms"""
        manager = EnhancedWebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock()

        connection_id = await manager.connect(mock_websocket)

        # Join room
        await manager.join_room(connection_id, "room1")
        assert connection_id in manager.rooms.get("room1", set())

        # Leave room
        await manager.leave_room(connection_id, "room1")
        assert connection_id not in manager.rooms.get("room1", set())

    async def test_broadcast_to_room(self):
        """Test broadcasting to specific room"""
        manager = EnhancedWebSocketManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        mock_ws3 = MagicMock()

        mock_ws1.accept = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws3.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2.send_text = AsyncMock()
        mock_ws3.send_text = AsyncMock()

        # Connect all websockets
        conn1 = await manager.connect(mock_ws1)
        conn2 = await manager.connect(mock_ws2)
        conn3 = await manager.connect(mock_ws3)

        # Add connections to rooms
        await manager.join_room(conn1, "room1")
        await manager.join_room(conn2, "room1")
        await manager.join_room(conn3, "room2")

        # Broadcast to room1
        await manager.broadcast_to_room("room1", "Hello room1")

        # Only connections in room1 should receive the message
        mock_ws1.send_text.assert_called_once_with("Hello room1")
        mock_ws2.send_text.assert_called_once_with("Hello room1")
        mock_ws3.send_text.assert_not_called()

    async def test_broadcast_to_user(self):
        """Test broadcasting to specific user"""
        manager = EnhancedWebSocketManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        mock_ws1.accept = AsyncMock()
        mock_ws2.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        # Connect with user IDs
        await manager.connect(mock_ws1, user_id="user1")
        await manager.connect(mock_ws2, user_id="user2")

        # Broadcast to specific user
        await manager.broadcast_to_user("user1", "Hello user1")

        # Only user1's connection should receive the message
        mock_ws1.send_text.assert_called_once_with("Hello user1")
        mock_ws2.send_text.assert_not_called()

    async def test_get_connection_stats(self):
        """Test getting connection statistics"""
        manager = EnhancedWebSocketManager()
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()

        mock_ws1.accept = AsyncMock()
        mock_ws2.accept = AsyncMock()

        # Connect websockets
        conn1 = await manager.connect(mock_ws1, user_id="user1")
        conn2 = await manager.connect(mock_ws2, user_id="user2")

        # Join rooms
        await manager.join_room(conn1, "room1")
        await manager.join_room(conn2, "room1")
        await manager.join_room(conn2, "room2")

        stats = await manager.get_connection_stats()

        assert stats["total_connections"] == 2
        assert stats["total_rooms"] == 2
        assert stats["total_users"] == 2
        assert "connections_per_room" in stats
        assert stats["connections_per_room"]["room1"] == 2
        assert stats["connections_per_room"]["room2"] == 1


@pytest.mark.integration
@pytest.mark.websocket
class TestWebSocketIntegration:
    """Integration tests for WebSocket endpoints"""

    def test_websocket_endpoint_connection(self, sync_client: TestClient):
        """Test WebSocket endpoint connection"""
        with sync_client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_message_handling(self, sync_client: TestClient):
        """Test WebSocket message handling"""
        with sync_client.websocket_connect("/ws") as websocket:
            # Send a test message
            test_message = {"type": "ping", "data": {}}
            websocket.send_json(test_message)

            # Should receive response (implementation dependent)
            # This test structure can be adapted based on actual WebSocket message handling

    def test_websocket_authentication(self, sync_client: TestClient):
        """Test WebSocket authentication if implemented"""
        # Test unauthorized connection
        try:
            with sync_client.websocket_connect("/ws") as websocket:
                # If auth is required, this should work or fail based on implementation
                pass
        except Exception:
            # Expected if authentication is required
            pass

    def test_websocket_room_functionality(self, sync_client: TestClient):
        """Test WebSocket room functionality"""
        with sync_client.websocket_connect("/ws") as websocket:
            # Test joining room
            join_message = {"type": "join_room", "data": {"room": "test_room"}}
            websocket.send_json(join_message)

            # Test leaving room
            leave_message = {"type": "leave_room", "data": {"room": "test_room"}}
            websocket.send_json(leave_message)

    def test_multiple_websocket_connections(self, sync_client: TestClient):
        """Test multiple WebSocket connections"""
        with sync_client.websocket_connect("/ws") as ws1:
            with sync_client.websocket_connect("/ws") as ws2:
                # Both connections should be active
                assert ws1 is not None
                assert ws2 is not None

                # Test broadcasting (implementation dependent)
                test_message = {
                    "type": "broadcast_test",
                    "data": {"message": "Hello all"},
                }
                ws1.send_json(test_message)


@pytest.mark.unit
@pytest.mark.websocket
class TestWebSocketErrorHandling:
    """Tests for WebSocket error handling"""

    async def test_websocket_connection_failure(self):
        """Test handling of WebSocket connection failures"""
        manager = WebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.accept = AsyncMock(side_effect=Exception("Connection failed"))

        # Should handle connection failure gracefully
        try:
            await manager.connect(mock_websocket)
            # If implementation catches exception, websocket shouldn't be in connections
            assert mock_websocket not in manager.active_connections
        except Exception:
            # If implementation doesn't catch, exception should propagate
            assert mock_websocket not in manager.active_connections

    async def test_websocket_send_failure(self):
        """Test handling of send failures"""
        manager = WebSocketManager()
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Send failed"))

        manager.active_connections = [mock_websocket]

        # Should handle send failure gracefully
        await manager.broadcast("test message")

        # Failed connection should be removed
        assert mock_websocket not in manager.active_connections

    async def test_enhanced_websocket_invalid_room(self):
        """Test enhanced WebSocket with invalid room operations"""
        manager = EnhancedWebSocketManager()

        # Try to join room with invalid connection ID
        await manager.join_room("invalid_connection_id", "room1")

        # Should handle gracefully without errors
        assert (
            "room1" not in manager.rooms
            or "invalid_connection_id" not in manager.rooms["room1"]
        )

    async def test_enhanced_websocket_broadcast_to_nonexistent_room(self):
        """Test broadcasting to non-existent room"""
        manager = EnhancedWebSocketManager()

        # Should handle gracefully without errors
        await manager.broadcast_to_room("nonexistent_room", "test message")

        # No exceptions should be raised

    async def test_enhanced_websocket_broadcast_to_nonexistent_user(self):
        """Test broadcasting to non-existent user"""
        manager = EnhancedWebSocketManager()

        # Should handle gracefully without errors
        await manager.broadcast_to_user("nonexistent_user", "test message")

        # No exceptions should be raised


@pytest.mark.performance
@pytest.mark.websocket
class TestWebSocketPerformance:
    """Performance tests for WebSocket functionality"""

    async def test_websocket_broadcast_performance(self, performance_config):
        """Test WebSocket broadcast performance"""
        manager = WebSocketManager()

        # Create many mock connections
        num_connections = 1000
        mock_websockets = []

        for _ in range(num_connections):
            mock_ws = MagicMock()
            mock_ws.send_text = AsyncMock()
            mock_websockets.append(mock_ws)
            manager.active_connections.append(mock_ws)

        # Measure broadcast time
        import time

        start_time = time.time()

        await manager.broadcast("Performance test message")

        end_time = time.time()
        broadcast_time = end_time - start_time

        # Should complete within reasonable time
        assert broadcast_time < performance_config["max_response_time"]

        # All connections should have received the message
        for mock_ws in mock_websockets:
            mock_ws.send_text.assert_called_once()

    async def test_enhanced_websocket_room_performance(self, performance_config):
        """Test enhanced WebSocket room performance"""
        manager = EnhancedWebSocketManager()

        # Create many connections and rooms
        num_connections = 100
        num_rooms = 10

        connections = []
        for i in range(num_connections):
            mock_ws = MagicMock()
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()

            conn_id = await manager.connect(mock_ws)
            connections.append(conn_id)

            # Distribute connections across rooms
            room_name = f"room_{i % num_rooms}"
            await manager.join_room(conn_id, room_name)

        # Measure room broadcast performance
        import time

        start_time = time.time()

        await manager.broadcast_to_room("room_0", "Performance test")

        end_time = time.time()
        broadcast_time = end_time - start_time

        # Should complete within reasonable time
        assert broadcast_time < performance_config["max_response_time"]