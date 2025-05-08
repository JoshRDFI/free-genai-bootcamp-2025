#!/usr/bin/env python3

"""
Example usage of the OPEA Components library.

This script demonstrates how to create and orchestrate microservices
using the OPEA Components library.
"""

import os
import json
from service import MicroService, ServiceOrchestrator, ServiceType

def main():
    # Create services
    llm_service = MicroService(
        name="llm",
        host=os.getenv("LLM_HOST", "localhost"),
        port=int(os.getenv("LLM_PORT", "9000")),
        endpoint="/v1/chat/completions",
        service_type=ServiceType.LLM
    )
    
    embedding_service = MicroService(
        name="embedding",
        host=os.getenv("EMBEDDING_HOST", "localhost"),
        port=int(os.getenv("EMBEDDING_PORT", "6000")),
        endpoint="/embed",
        service_type=ServiceType.EMBEDDING
    )
    
    # Create an orchestrator
    orchestrator = ServiceOrchestrator()
    
    # Add services to the orchestrator
    orchestrator.add(llm_service)
    orchestrator.add(embedding_service)
    
    # Check service health
    health_results = orchestrator.health_check_all()
    print("\nService Health Check:")
    for service_name, (is_healthy, message) in health_results.items():
        status = "✅" if is_healthy else "❌"
        print(f"{service_name}: {status} - {message}")
    
    # Example: Call LLM service
    print("\nCalling LLM service...")
    llm_request = {
        "model": "llama3",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ],
        "temperature": 0.7
    }
    
    llm_response = llm_service.call(llm_request)
    print(f"LLM Response:\n{json.dumps(llm_response, indent=2)}\n")
    
    # Example: Call Embedding service
    print("Calling Embedding service...")
    embedding_request = {
        "text": "Paris is the capital of France.",
        "model": "all-MiniLM-L6-v2"
    }
    
    embedding_response = embedding_service.call(embedding_request)
    
    # Truncate the embedding vector for display
    if "embedding" in embedding_response and isinstance(embedding_response["embedding"], list):
        if len(embedding_response["embedding"]) > 5:
            embedding_response["embedding"] = embedding_response["embedding"][:5] + ["..."] 
    
    print(f"Embedding Response:\n{json.dumps(embedding_response, indent=2)}\n")

if __name__ == "__main__":
    main()