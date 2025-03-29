from enum import Enum, auto
import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Enum defining different types of microservices in the OPEA ecosystem."""
    LLM = auto()        # Large Language Model services
    EMBEDDING = auto()  # Vector embedding services
    VISION = auto()     # Image/vision processing services
    TTS = auto()        # Text-to-Speech services
    ASR = auto()        # Automatic Speech Recognition services
    GUARDRAILS = auto() # Content moderation/safety services
    AGENT = auto()      # Autonomous agent services

class MicroService:
    """Represents a microservice in the OPEA ecosystem.
    
    This class provides a standardized interface for interacting with various
    microservices, handling communication details and error management.
    """
    def __init__(self, 
                 name: str, 
                 host: str = "localhost", 
                 port: int = 8000, 
                 endpoint: str = "/", 
                 use_remote_service: bool = False,
                 service_type: Optional[ServiceType] = None,
                 timeout: int = 30):
        """Initialize a microservice connection.
        
        Args:
            name: Unique identifier for the service
            host: Hostname or IP address of the service
            port: Port number the service is listening on
            endpoint: API endpoint path
            use_remote_service: Whether this service is hosted remotely
            service_type: The type of service (from ServiceType enum)
            timeout: Request timeout in seconds
        """
        self.name = name
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.use_remote_service = use_remote_service
        self.service_type = service_type
        self.timeout = timeout
        self.url = f"http://{host}:{port}{endpoint}"
        
    def call(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Call the microservice with the provided data.
        
        Args:
            data: Dictionary containing the request payload
            
        Returns:
            Dictionary containing the service response or error information
        """
        try:
            logger.debug(f"Calling {self.name} service at {self.url}")
            response = requests.post(self.url, json=data, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            error_msg = f"Timeout calling {self.name} service after {self.timeout}s"
            logger.error(error_msg)
            return {"error": error_msg, "status": "timeout"}
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error calling {self.name} service: {e}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "connection_error"}
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling {self.name} service: {e}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "request_error"}
        except Exception as e:
            error_msg = f"Unexpected error calling {self.name} service: {e}"
            logger.error(error_msg)
            return {"error": error_msg, "status": "unknown_error"}
            
    def health_check(self) -> Tuple[bool, str]:
        """Check if the service is healthy and responding.
        
        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            response = requests.get(f"http://{self.host}:{self.port}/health", timeout=5)
            if response.status_code == 200:
                return True, "Service is healthy"
            return False, f"Service returned status code {response.status_code}"
        except Exception as e:
            return False, f"Health check failed: {str(e)}"

class ServiceOrchestrator:
    """Orchestrates the flow of data between multiple microservices.
    
    This class manages service registration, flow definition, and execution
    of processing pipelines across multiple services.
    """
    def __init__(self):
        """Initialize a new service orchestrator."""
        self.services: Dict[str, MicroService] = {}
        self.flow: Dict[str, List[str]] = {}
        
    def add(self, service: MicroService) -> 'ServiceOrchestrator':
        """Add a service to the orchestrator.
        
        Args:
            service: The MicroService instance to add
            
        Returns:
            Self for method chaining
        """
        self.services[service.name] = service
        self.flow[service.name] = []
        return self
    
    def flow_to(self, from_service: MicroService, to_service: MicroService) -> 'ServiceOrchestrator':
        """Define a flow from one service to another.
        
        Args:
            from_service: Source service where data processing starts
            to_service: Destination service to receive output from source
            
        Returns:
            Self for method chaining
        """
        if from_service.name not in self.services:
            self.add(from_service)
        if to_service.name not in self.services:
            self.add(to_service)
            
        self.flow[from_service.name].append(to_service.name)
        return self
    
    def process(self, service_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through a service and its flow.
        
        Args:
            service_name: Name of the service to start processing with
            data: Input data for the service
            
        Returns:
            Dictionary containing the final processing result or error information
        """
        if service_name not in self.services:
            error_msg = f"Service {service_name} not found"
            logger.error(error_msg)
            return {"error": error_msg, "status": "service_not_found"}
            
        # Call the current service
        service = self.services[service_name]
        result = service.call(data)
        
        # Check for errors before proceeding
        if "error" in result:
            logger.warning(f"Error in service {service_name}: {result['error']}")
            return result
        
        # If there are downstream services, call them
        for next_service_name in self.flow[service_name]:
            next_result = self.process(next_service_name, result)
            result = next_result
            
            # If an error occurred in the downstream service, stop processing
            if "error" in result:
                break
            
        return result
    
    def get_service(self, service_name: str) -> Optional[MicroService]:
        """Get a service by name.
        
        Args:
            service_name: Name of the service to retrieve
            
        Returns:
            The MicroService instance or None if not found
        """
        return self.services.get(service_name)
    
    def get_services_by_type(self, service_type: ServiceType) -> List[MicroService]:
        """Get all services of a specific type.
        
        Args:
            service_type: Type of services to retrieve
            
        Returns:
            List of MicroService instances matching the specified type
        """
        return [s for s in self.services.values() if s.service_type == service_type]
        
    def health_check_all(self) -> Dict[str, Tuple[bool, str]]:
        """Check the health of all registered services.
        
        Returns:
            Dictionary mapping service names to (is_healthy, message) tuples
        """
        results = {}
        for name, service in self.services.items():
            results[name] = service.health_check()
        return results