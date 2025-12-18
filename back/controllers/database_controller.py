from typing import List, Optional
from models.music_item import MusicItem
import database_config

def get_all_music(filter_type: Optional[str] = None, search: Optional[str] = None) -> List[MusicItem]:
    print(f"[DATABASE CONTROLLER] Getting music items from MongoDB - filter: {filter_type}, search: {search}")
    
    db = database_config.get_database()
    music_items = []
    
    search_regex = None
    if search:
        search_regex = {'$regex': search, '$options': 'i'}
        print(f"[DATABASE CONTROLLER] Searching for: {search}")
    
    # Si filter_type est 'generated', chercher dans generated_music
    if filter_type and filter_type.lower() == 'generated':
        collection = db.generated_music
        query = {}
        if search_regex:
            query['$or'] = [
                {'canonical_title': search_regex},
                {'canonical_composer': search_regex},
                {'title': search_regex},
                {'composer': search_regex}
            ]
        
        items = list(collection.find(query))
        for item in items:
            if '_id' in item:
                del item['_id']
            try:
                music_items.append(MusicItem(**item))
            except Exception as e:
                print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")
        
        print(f"[DATABASE CONTROLLER] Returning {len(music_items)} items from generated_music collection")
    else:
        # Sinon, chercher dans raw_data
        collection = db.raw_data
        query = {}
        
        if filter_type and filter_type != 'all':
            query['split'] = filter_type.lower()
            print(f"[DATABASE CONTROLLER] Filtering by type: {filter_type}")
        
        if search_regex:
            query['$or'] = [
                {'canonical_title': search_regex},
                {'canonical_composer': search_regex},
                {'title': search_regex},
                {'composer': search_regex}
            ]
        
        items = list(collection.find(query))
        for item in items:
            if '_id' in item:
                del item['_id']
            try:
                music_items.append(MusicItem(**item))
            except Exception as e:
                print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")
        
        # Si filter_type est 'all' ou None, aussi chercher dans generated_music
        if not filter_type or filter_type == 'all':
            gen_collection = db.generated_music
            gen_query = {}
            if search_regex:
                gen_query['$or'] = [
                    {'canonical_title': search_regex},
                    {'canonical_composer': search_regex},
                    {'title': search_regex},
                    {'composer': search_regex}
                ]
            
            gen_items = list(gen_collection.find(gen_query))
            for item in gen_items:
                if '_id' in item:
                    del item['_id']
                try:
                    music_items.append(MusicItem(**item))
                except Exception as e:
                    print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")
        
        print(f"[DATABASE CONTROLLER] Returning {len(music_items)} items from raw_data + generated_music collections")
    
    return music_items


def get_generated_music() -> List[MusicItem]:
    """
    Get all generated music from the generated_music collection.
    """
    print(f"[DATABASE CONTROLLER] Getting generated music from MongoDB")
    
    db = database_config.get_database()
    collection = db.generated_music
    
    items = list(collection.find())
    
    music_items = []
    for item in items:
        if '_id' in item:
            del item['_id']
        try:
            music_items.append(MusicItem(**item))
        except Exception as e:
            print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")
    
    print(f"[DATABASE CONTROLLER] Returning {len(music_items)} generated items")
    return music_items


def get_generated_music_count() -> int:
    """
    Get the count of generated music items.
    """
    db = database_config.get_database()
    collection = db.generated_music
    return collection.count_documents({})

def get_music_by_id(music_id: int) -> Optional[MusicItem]:
    print(f"[DATABASE CONTROLLER] Getting music item with id: {music_id} from MongoDB")
    
    db = database_config.get_database()
    collection = db.raw_data
    
    item = collection.find_one({'id': music_id})
    
    if item:
        if '_id' in item:
            del item['_id']
        print(f"[DATABASE CONTROLLER] Found: {item['title']}")
        return MusicItem(**item)
    
    print(f"[DATABASE CONTROLLER] Music item {music_id} not found")
    return None
