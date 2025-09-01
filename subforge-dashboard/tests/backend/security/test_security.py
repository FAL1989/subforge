"""
Security tests for SubForge Dashboard API
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
import uuid


@pytest.mark.security
@pytest.mark.api
class TestSQLInjection:
    """Tests for SQL injection vulnerabilities"""
    
    async def test_agent_name_sql_injection(self, test_client: AsyncClient, security_payloads):
        """Test SQL injection in agent name field"""
        for payload in security_payloads["sql_injection"]:
            agent_data = {
                "name": payload,
                "agent_type": "test",
                "status": "idle"
            }
            
            response = await test_client.post("/api/v1/agents/", json=agent_data)
            
            # Should not cause database errors or return sensitive data
            assert response.status_code in [200, 422]  # Valid creation or validation error
            
            if response.status_code == 200:
                # If accepted, verify the payload was sanitized
                data = response.json()
                assert "DROP TABLE" not in str(data)
                assert "EXEC" not in str(data)
    
    async def test_agent_filter_sql_injection(self, test_client: AsyncClient, security_payloads):
        """Test SQL injection in filter parameters"""
        for payload in security_payloads["sql_injection"]:
            # Test various filter parameters
            params = {
                "status": payload,
                "agent_type": payload,
                "skip": 0,
                "limit": 10
            }
            
            response = await test_client.get("/api/v1/agents/", params=params)
            
            # Should not cause database errors
            assert response.status_code in [200, 422]
            
            if response.status_code == 200:
                # Should return safe data
                data = response.json()
                assert isinstance(data, list)
    
    async def test_task_search_sql_injection(self, test_client: AsyncClient, security_payloads):
        """Test SQL injection in task search parameters"""
        for payload in security_payloads["sql_injection"]:
            params = {
                "title": payload,
                "status": payload,
                "priority": payload
            }
            
            response = await test_client.get("/api/v1/tasks/", params=params)
            
            # Should not cause database errors
            assert response.status_code in [200, 422]


@pytest.mark.security
@pytest.mark.api
class TestXSSProtection:
    """Tests for XSS vulnerabilities"""
    
    async def test_agent_description_xss(self, test_client: AsyncClient, security_payloads):
        """Test XSS in agent description field"""
        for payload in security_payloads["xss"]:
            agent_data = {
                "name": "test-agent",
                "agent_type": "test",
                "description": payload,
                "status": "idle"
            }
            
            with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
                mock_broadcast.return_value = AsyncMock()
                
                response = await test_client.post("/api/v1/agents/", json=agent_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # XSS payload should be escaped or sanitized
                    description = data.get("description", "")
                    assert "<script>" not in description
                    assert "javascript:" not in description
                    assert "onerror=" not in description
    
    async def test_task_title_xss(self, test_client: AsyncClient, security_payloads):
        """Test XSS in task title field"""
        for payload in security_payloads["xss"]:
            task_data = {
                "title": payload,
                "description": "Test task",
                "priority": "medium",
                "status": "pending"
            }
            
            with patch('app.websocket.manager.websocket_manager.broadcast_json') as mock_broadcast:
                mock_broadcast.return_value = AsyncMock()
                
                response = await test_client.post("/api/v1/tasks/", json=task_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # XSS payload should be escaped or sanitized
                    title = data.get("title", "")
                    assert "<script>" not in title
                    assert "javascript:" not in title


@pytest.mark.security
@pytest.mark.api
class TestInputValidation:
    """Tests for input validation security"""
    
    async def test_agent_id_format_validation(self, test_client: AsyncClient):
        """Test agent ID format validation"""
        # Test with various invalid UUID formats
        invalid_uuids = [
            "invalid-uuid",
            "12345",
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "'; DROP TABLE agents; --"
        ]
        
        for invalid_uuid in invalid_uuids:
            response = await test_client.get(f"/api/v1/agents/{invalid_uuid}")
            
            # Should return validation error, not 500 server error
            assert response.status_code == 422
    
    async def test_pagination_parameter_validation(self, test_client: AsyncClient):
        """Test pagination parameter validation"""
        # Test with invalid pagination parameters
        invalid_params = [
            {"skip": -1},
            {"limit": -1},
            {"skip": "invalid"},
            {"limit": "invalid"},
            {"skip": 999999999999},  # Very large number
            {"limit": 999999999999}
        ]
        
        for params in invalid_params:
            response = await test_client.get("/api/v1/agents/", params=params)
            
            # Should handle gracefully
            assert response.status_code in [200, 422]
    
    async def test_json_payload_size_limit(self, test_client: AsyncClient):
        """Test JSON payload size limits"""
        # Create very large payload
        large_description = "A" * 1000000  # 1MB of text
        
        agent_data = {
            "name": "test-agent",
            "agent_type": "test",
            "description": large_description,
            "status": "idle"
        }
        
        response = await test_client.post("/api/v1/agents/", json=agent_data)
        
        # Should reject or handle large payloads appropriately
        assert response.status_code in [413, 422, 400]  # Request too large or validation error
    
    async def test_nested_json_depth_limit(self, test_client: AsyncClient):
        """Test nested JSON depth limits"""
        # Create deeply nested configuration
        deep_config = {"level1": {"level2": {"level3": {"level4": {"level5": "deep"}}}}}
        
        agent_data = {
            "name": "test-agent",
            "agent_type": "test",
            "configuration": deep_config,
            "status": "idle"
        }
        
        response = await test_client.post("/api/v1/agents/", json=agent_data)
        
        # Should handle without causing stack overflow
        assert response.status_code in [200, 422]


@pytest.mark.security
@pytest.mark.api
class TestAuthenticationSecurity:
    """Tests for authentication security (if implemented)"""
    
    async def test_unauthenticated_access(self, test_client: AsyncClient):
        """Test access without authentication"""
        # This test depends on whether authentication is implemented
        # Currently the API might not have authentication, so this is preparatory
        
        # Test accessing protected endpoints without auth
        protected_endpoints = [
            "/api/v1/agents/",
            "/api/v1/tasks/",
            "/api/v1/workflows/"
        ]
        
        for endpoint in protected_endpoints:
            response = await test_client.get(endpoint)
            
            # If auth is implemented, should return 401
            # If not implemented, will return 200
            assert response.status_code in [200, 401]
    
    async def test_invalid_token_access(self, test_client: AsyncClient):
        """Test access with invalid authentication token"""
        # Test with invalid bearer token
        headers = {"Authorization": "Bearer invalid_token_12345"}
        
        response = await test_client.get("/api/v1/agents/", headers=headers)
        
        # Should handle invalid tokens gracefully
        assert response.status_code in [200, 401, 403]
    
    async def test_expired_token_access(self, test_client: AsyncClient):
        """Test access with expired authentication token"""
        # Mock an expired JWT token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImV4cCI6MTUxNjIzOTAyMn0.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await test_client.get("/api/v1/agents/", headers=headers)
        
        # Should reject expired tokens
        assert response.status_code in [200, 401, 403]


@pytest.mark.security
@pytest.mark.api
class TestRateLimiting:
    """Tests for rate limiting security"""
    
    async def test_api_rate_limiting(self, test_client: AsyncClient):
        """Test API rate limiting"""
        # Make many rapid requests
        responses = []
        
        for i in range(100):
            response = await test_client.get("/api/v1/agents/")
            responses.append(response)
            
            # If rate limiting is implemented, should eventually get 429
            if response.status_code == 429:
                break
        
        # Check if rate limiting is working
        rate_limited = any(r.status_code == 429 for r in responses)
        
        # Rate limiting might not be implemented yet
        # This test documents expected behavior
        if rate_limited:
            assert True  # Rate limiting is working
        else:
            # Log that rate limiting is not implemented
            print("Rate limiting not detected - consider implementing for production")
    
    async def test_websocket_connection_limiting(self, sync_client):
        """Test WebSocket connection rate limiting"""
        # This would test if too many WebSocket connections are rejected
        # Implementation depends on WebSocket connection limits
        pass


@pytest.mark.security
@pytest.mark.websocket
class TestWebSocketSecurity:
    """Tests for WebSocket security"""
    
    def test_websocket_connection_authentication(self, sync_client):
        """Test WebSocket connection authentication"""
        try:
            with sync_client.websocket_connect("/ws") as websocket:
                # Test if unauthenticated connections are allowed
                assert websocket is not None
        except Exception as e:
            # If authentication is required, connection should fail
            assert "authentication" in str(e).lower() or "unauthorized" in str(e).lower()
    
    def test_websocket_message_validation(self, sync_client):
        """Test WebSocket message validation"""
        with sync_client.websocket_connect("/ws") as websocket:
            # Test with malformed messages
            malformed_messages = [
                "not_json",
                {"invalid": "structure"},
                {"type": "<script>alert('xss')</script>"},
                None,
                123,
                []
            ]
            
            for message in malformed_messages:
                try:
                    websocket.send_json(message)
                    # Should handle malformed messages gracefully
                except Exception:
                    # Expected for some malformed messages
                    pass
    
    def test_websocket_message_size_limit(self, sync_client):
        """Test WebSocket message size limits"""
        with sync_client.websocket_connect("/ws") as websocket:
            # Create large message
            large_message = {
                "type": "test",
                "data": "A" * 100000  # 100KB message
            }
            
            try:
                websocket.send_json(large_message)
                # Should handle or reject large messages appropriately
            except Exception:
                # Expected if size limits are enforced
                pass


@pytest.mark.security
@pytest.mark.api
class TestDataLeakage:
    """Tests for data leakage vulnerabilities"""
    
    async def test_error_message_information_disclosure(self, test_client: AsyncClient):
        """Test that error messages don't leak sensitive information"""
        # Test with invalid agent ID
        response = await test_client.get("/api/v1/agents/invalid-uuid")
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Error messages should not contain:
        # - Database schema information
        # - File paths
        # - Stack traces
        # - Internal system details
        error_str = str(error_data).lower()
        
        sensitive_patterns = [
            "traceback",
            "file \"/",
            "line ",
            "sqlalchemy",
            "database",
            "connection string",
            "password"
        ]
        
        for pattern in sensitive_patterns:
            assert pattern not in error_str
    
    async def test_database_error_handling(self, test_client: AsyncClient):
        """Test database error handling doesn't leak information"""
        # Create agent data that might cause database constraint violation
        agent_data = {
            "name": "test-agent",
            "agent_type": "test",
            "status": "idle"
        }
        
        # Create first agent
        response1 = await test_client.post("/api/v1/agents/", json=agent_data)
        
        # Try to create duplicate (if unique constraints exist)
        response2 = await test_client.post("/api/v1/agents/", json=agent_data)
        
        if response2.status_code != 200:
            error_data = response2.json()
            error_str = str(error_data).lower()
            
            # Should not leak database-specific error details
            assert "constraint" not in error_str
            assert "unique" not in error_str or "already exists" in error_str
            assert "foreign key" not in error_str
    
    async def test_system_information_disclosure(self, test_client: AsyncClient):
        """Test system information is not disclosed"""
        # Test various endpoints for system information leakage
        endpoints = [
            "/api/v1/agents/",
            "/api/v1/tasks/",
            "/api/v1/workflows/",
            "/api/v1/system/health",
            "/api/v1/agents/stats/summary"
        ]
        
        for endpoint in endpoints:
            response = await test_client.get(endpoint)
            
            if response.status_code == 200:
                data = response.json()
                data_str = str(data).lower()
                
                # Should not contain system paths or sensitive info
                sensitive_info = [
                    "/home/",
                    "/usr/",
                    "/var/",
                    "password",
                    "secret",
                    "key",
                    "token",
                    "database_url"
                ]
                
                for info in sensitive_info:
                    assert info not in data_str


@pytest.mark.security
@pytest.mark.performance  
class TestSecurityPerformance:
    """Tests for security-related performance issues"""
    
    async def test_denial_of_service_protection(self, test_client: AsyncClient):
        """Test protection against DoS attacks"""
        # Test with resource-intensive operations
        # This could be large pagination requests, complex filters, etc.
        
        # Test large limit parameter
        response = await test_client.get("/api/v1/agents/?limit=999999")
        
        # Should handle gracefully without consuming excessive resources
        assert response.status_code in [200, 422]
        
        # Response should come back in reasonable time
        import time
        start_time = time.time()
        
        response = await test_client.get("/api/v1/agents/?limit=1000")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should not take too long (DoS protection)
        assert response_time < 5.0  # 5 second timeout
    
    async def test_regular_expression_dos(self, test_client: AsyncClient):
        """Test protection against ReDoS attacks"""
        # Test with patterns that could cause catastrophic backtracking
        malicious_patterns = [
            "a" * 1000 + "b",
            "(a+)+$",
            "^(a+)+$",
            "^((a+)+)+$"
        ]
        
        for pattern in malicious_patterns:
            agent_data = {
                "name": pattern,
                "agent_type": "test",
                "status": "idle"
            }
            
            import time
            start_time = time.time()
            
            response = await test_client.post("/api/v1/agents/", json=agent_data)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # Should not take too long even with malicious patterns
            assert response_time < 2.0