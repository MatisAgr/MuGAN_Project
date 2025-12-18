from typing import List, Optional
from models.music_item import MusicItem
import database_config

def get_all_music(filter_type: Optional[str] = None, search: Optional[str] = None) -> List[MusicItem]:
    print(f"[DATABASE CONTROLLER] Getting music items from MongoDB - filter: {filter_type}, search: {search}")
    
    db = database_config.get_database()
    collection = db.raw_data
    
    query = {}
    
    if filter_type and filter_type != 'all':
        query['split'] = filter_type.lower()
        print(f"[DATABASE CONTROLLER] Filtering by type: {filter_type}")
    
    if search:
        search_regex = {'$regex': search, '$options': 'i'}
        query['$or'] = [
            {'canonical_title': search_regex},
            {'canonical_composer': search_regex}
        ]
        print(f"[DATABASE CONTROLLER] Searching for: {search}")
    
    items = list(collection.find(query))
    
    music_items = []
    for item in items:
        if '_id' in item:
            del item['_id']
        try:
            music_items.append(MusicItem(**item))
        except Exception as e:
            print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")
    
    print(f"[DATABASE CONTROLLER] Returning {len(music_items)} items from raw_data collection")
    
    return music_items

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
