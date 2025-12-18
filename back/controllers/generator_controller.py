import uuid
from datetime import datetime
from models.generator_request import GeneratorRequest, GeneratorResponse
import database_config


def generate_music(request: GeneratorRequest) -> GeneratorResponse:
    print(f"[GENERATOR CONTROLLER] Received generation request")
    print(f"  - Title: {request.title}")
    print(f"  - Composer: {request.composer}")
    print(f"  - Duration: {request.duration}")
    print(f"  - Temperature: {request.temperature}")

    # Try to select a source document from raw_data collection when possible
    try:
        db = database_config.get_database()
        collection = db.raw_data
        query = {}
        if request.title:
            query['title'] = {'$regex': request.title, '$options': 'i'}
        elif request.composer:
            query['composer'] = {'$regex': request.composer, '$options': 'i'}

        source_doc = None
        if query:
            source_doc = collection.find_one(query)
            print(f"[GENERATOR CONTROLLER] Queried raw_data with {query}, found: {bool(source_doc)}")
        else:
            # no criteria -> sample a random source
            sample = list(collection.aggregate([{'$sample': {'size': 1}}]))
            source_doc = sample[0] if sample else None
            print(f"[GENERATOR CONTROLLER] No criteria provided, sampled random doc: {bool(source_doc)}")

        if source_doc:
            # map fields if present
            src_title = source_doc.get('title')
            src_composer = source_doc.get('composer')
            src_midi = source_doc.get('midi_filename')
            src_audio = source_doc.get('audio_filename')
            print(f"[GENERATOR CONTROLLER] Source -> title: {src_title}, composer: {src_composer}, midi: {src_midi}")
        else:
            print("[GENERATOR CONTROLLER] No source document found in raw_data")
    except Exception as e:
        print(f"[GENERATOR CONTROLLER] Warning: could not query raw_data: {e}")
        source_doc = None

    generation_id = str(uuid.uuid4())

    print(f"[GENERATOR CONTROLLER] Simulating music generation...")
    print(f"[GENERATOR CONTROLLER] Generation ID: {generation_id}")

    # Use source title/composer as base title if request.title not provided
    base_title = None
    if request.title:
        base_title = request.title
    elif source_doc:
        base_title = source_doc.get('title') or source_doc.get('canonical_title')
    else:
        base_title = f"Generated Music {generation_id[:8]}"

    response = GeneratorResponse(
        id=generation_id,
        title=base_title,
        url=f"/api/generated/{generation_id}.mid",
        duration=request.duration,
        created=datetime.now().isoformat()
    )

    print(f"[GENERATOR CONTROLLER] Generation completed: {response.title}")
    return response
