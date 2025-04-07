import os
from opea_comps import MicroService, ServiceOrchestrator, ServiceType

EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = int(os.getenv("EMBEDDING_SERVICE_PORT", 6000))
LLM_SERVICE_HOST_IP = os.getenv("LLM_SERVICE_HOST_IP", "0.0.0.0")
LLM_SERVICE_PORT = int(os.getenv("LLM_SERVICE_PORT", 8008))  # Updated to match Ollama's port
WAIFU_DIFFUSION_HOST_IP = os.getenv("WAIFU_DIFFUSION_HOST_IP", "0.0.0.0")
WAIFU_DIFFUSION_PORT = int(os.getenv("WAIFU_DIFFUSION_PORT", 9500))

class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/embed",  # Updated endpoint to reflect our embeddings microservice
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        llm = MicroService(
            name="llm",
            host=LLM_SERVICE_HOST_IP,
            port=LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",  # Targeting the hosted Ollama LLM service
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        waifu_diffusion = MicroService(
            name="waifu-diffusion",
            host=WAIFU_DIFFUSION_HOST_IP,
            port=WAIFU_DIFFUSION_PORT,
            endpoint="/generate",  # Endpoint for image generation
            use_remote_service=True,
            service_type=ServiceType.IMAGE_GENERATION,
        )
        self.megaservice.add(embedding).add(llm).add(waifu_diffusion)
        self.megaservice.flow_to(embedding, llm)