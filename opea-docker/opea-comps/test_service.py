#!/usr/bin/env python3

"""
Unit tests for the OPEA Components library.

Run with: python -m unittest test_service.py
"""

import unittest
from unittest.mock import patch, MagicMock
from service import MicroService, ServiceOrchestrator, ServiceType

class TestMicroService(unittest.TestCase):
    def setUp(self):
        self.service = MicroService(
            name="test-service",
            host="localhost",
            port=8000,
            endpoint="/api",
            service_type=ServiceType.LLM
        )
    
    @patch('service.requests.post')
    def test_call_success(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call the service
        result = self.service.call({"test": "data"})
        
        # Verify the result
        self.assertEqual(result, {"result": "success"})
        mock_post.assert_called_once_with(
            "http://localhost:8000/api", 
            json={"test": "data"},
            timeout=30
        )
    
    @patch('service.requests.post')
    def test_call_error(self, mock_post):
        # Setup mock to raise an exception
        mock_post.side_effect = Exception("Test error")
        
        # Call the service
        result = self.service.call({"test": "data"})
        
        # Verify error handling
        self.assertIn("error", result)
        self.assertIn("Test error", result["error"])
        self.assertEqual(result["status"], "unknown_error")

class TestServiceOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = ServiceOrchestrator()
        self.service1 = MicroService(name="service1", service_type=ServiceType.LLM)
        self.service2 = MicroService(name="service2", service_type=ServiceType.EMBEDDING)
        
        # Add services to orchestrator
        self.orchestrator.add(self.service1)
        self.orchestrator.add(self.service2)
    
    def test_add_service(self):
        # Verify services were added
        self.assertIn("service1", self.orchestrator.services)
        self.assertIn("service2", self.orchestrator.services)
        
        # Verify flow initialization
        self.assertEqual(self.orchestrator.flow["service1"], [])
        self.assertEqual(self.orchestrator.flow["service2"], [])
    
    def test_flow_to(self):
        # Define a flow
        self.orchestrator.flow_to(self.service1, self.service2)
        
        # Verify flow was created
        self.assertEqual(self.orchestrator.flow["service1"], ["service2"])
    
    @patch.object(MicroService, 'call')
    def test_process(self, mock_call):
        # Setup mock response
        mock_call.return_value = {"processed": "data"}
        
        # Define a flow
        self.orchestrator.flow_to(self.service1, self.service2)
        
        # Process data
        result = self.orchestrator.process("service1", {"input": "data"})
        
        # Verify processing
        self.assertEqual(mock_call.call_count, 2)  # Called for both services
        self.assertEqual(result, {"processed": "data"})
    
    def test_get_services_by_type(self):
        # Get services by type
        llm_services = self.orchestrator.get_services_by_type(ServiceType.LLM)
        embedding_services = self.orchestrator.get_services_by_type(ServiceType.EMBEDDING)
        vision_services = self.orchestrator.get_services_by_type(ServiceType.VISION)
        
        # Verify results
        self.assertEqual(len(llm_services), 1)
        self.assertEqual(llm_services[0].name, "service1")
        self.assertEqual(len(embedding_services), 1)
        self.assertEqual(embedding_services[0].name, "service2")
        self.assertEqual(len(vision_services), 0)

if __name__ == '__main__':
    unittest.main()