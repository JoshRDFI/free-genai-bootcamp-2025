# OPEA Components Library

A Python library for building and orchestrating microservices in the OPEA (Open Platform for Educational AI) ecosystem.

## Overview

The OPEA Components library provides a standardized way to define, connect, and orchestrate AI microservices. It's designed to simplify the creation of complex AI pipelines for educational applications.

## Installation

```bash
pip install opea-comps
```

Or install from source:

```bash
git clone https://github.com/opea-project/opea-comps.git
cd opea-comps
pip install -e .
```

## Usage

### Creating a Microservice

```python
from opea_comps import MicroService, ServiceType

# Define a language model service
llm_service = MicroService(
    name="llm-service",
    host="localhost",
    port=9000,
    endpoint="/v1/chat/completions",
    service_type=ServiceType.LLM
)

# Call the service
response = llm_service.call({
    "model": "llama3",
    "messages": [{"role": "user", "content": "Hello, world!"}]
})

print(response)
```

### Orchestrating Multiple Services

```python
from opea_comps import MicroService, ServiceOrchestrator, ServiceType

# Create an orchestrator
orchestrator = ServiceOrchestrator()

# Define services
llm = MicroService(name="llm", port=9000, service_type=ServiceType.LLM)
embedding = MicroService(name="embedding", port=6000, service_type=ServiceType.EMBEDDING)
guardrails = MicroService(name="guardrails", port=9400, service_type=ServiceType.GUARDRAILS)

# Add services to orchestrator
orchestrator.add(llm).add(embedding).add(guardrails)

# Define processing flow
orchestrator.flow_to(guardrails, llm)

# Process data through the flow
result = orchestrator.process("guardrails", {
    "text": "Please translate this to French: Hello, how are you?"
})

print(result)
```

## Service Types

The library supports various service types through the `ServiceType` enum:

- `LLM`: Large Language Model services
- `EMBEDDING`: Vector embedding services
- `VISION`: Image/vision processing services
- `TTS`: Text-to-Speech services
- `ASR`: Automatic Speech Recognition services
- `GUARDRAILS`: Content moderation/safety services
- `AGENT`: Autonomous agent services

## Health Checks

You can check the health of services:

```python
# Check a single service
is_healthy, message = llm_service.health_check()
print(f"LLM Service: {message}")

# Check all services in an orchestrator
health_status = orchestrator.health_check_all()
for service_name, (is_healthy, message) in health_status.items():
    status = "✅" if is_healthy else "❌"
    print(f"{service_name}: {status} - {message}")
```

## Error Handling

The library provides detailed error information when service calls fail:

```python
response = llm_service.call({"invalid": "request"})
if "error" in response:
    print(f"Error: {response['error']}")
    print(f"Status: {response['status']}")
```

## License

MIT