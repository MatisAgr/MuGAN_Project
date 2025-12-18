import uuid
from datetime import datetime
from models.generator_request import GeneratorRequest, GeneratorResponse

def generate_music(request: GeneratorRequest) -> GeneratorResponse:
    print(f"[GENERATOR CONTROLLER] Received generation request")
    print(f"  - Prompt: {request.prompt}")
    print(f"  - Duration: {request.duration}")
    print(f"  - Temperature: {request.temperature}")
    
    generation_id = str(uuid.uuid4())
    
    print(f"[GENERATOR CONTROLLER] Simulating music generation...")
    print(f"[GENERATOR CONTROLLER] Generation ID: {generation_id}")
    
    response = GeneratorResponse(
        id=generation_id,
        title=request.prompt if request.prompt else f"Generated Music {generation_id[:8]}",
        url=f"/api/generated/{generation_id}.mid",
        duration=request.duration,
        created=datetime.now().isoformat()
    )
    
    print(f"[GENERATOR CONTROLLER] Generation completed: {response.title}")
    return response
