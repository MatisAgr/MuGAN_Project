from typing import List, Optional
from models.music_item import MusicItem
import database_config
from bson import ObjectId

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
            {'title': search_regex},
            {'composer': search_regex}
        ]
        print(f"[DATABASE CONTROLLER] Searching for: {search}")
    
    items = list(collection.find(query))
    
    music_items = []
    for item in items:
        # Map DB fields to model aliases expected by MusicItem
        if 'title' in item:
            item['canonical_title'] = item.pop('title')
        if 'composer' in item:
            item['canonical_composer'] = item.pop('composer')
        if '_id' in item:
            del item['_id']
        try:
            music_items.append(MusicItem(**item))
        except Exception as e:
            print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")
    
    print(f"[DATABASE CONTROLLER] Returning {len(music_items)} items from raw_data collection")
    
    return music_items

def get_music_by_id(music_id: str) -> Optional[MusicItem]:
    print(f"[DATABASE CONTROLLER] Getting music item with id: {music_id} from MongoDB")

    db = database_config.get_database()
    collection = db.raw_data

    item = None
    # Try ObjectId lookup first
    try:
        oid = ObjectId(music_id)
        item = collection.find_one({'_id': oid})
    except Exception:
        # not a valid ObjectId, try numeric id or filename
        try:
            numeric = int(music_id)
            item = collection.find_one({'id': numeric})
        except Exception:
            item = collection.find_one({'audio_filename': music_id})

    if item:
        if 'title' in item:
            item['canonical_title'] = item.pop('title')
        if 'composer' in item:
            item['canonical_composer'] = item.pop('composer')
        if '_id' in item:
            del item['_id']
        print(f"[DATABASE CONTROLLER] Found: {item.get('canonical_title')}")
        try:
            return MusicItem(**item)
        except Exception as e:
            print(f"[DATABASE CONTROLLER] Error parsing item {item}: {e}")

    print(f"[DATABASE CONTROLLER] Music item {music_id} not found")
    return None
