import pkgutil
import json
import re
import logging
_generated_events = []
# called after the game.json file has been loaded
def after_load_game_file(game_table: dict) -> dict:
    return game_table
# called after the items.json file has been loaded, before any item loading or processing has occurred
# if you need access to the items after processing to add ids, etc., you should use the hooks in World.py
def after_load_item_file(item_table: list) -> list:
    return item_table

# NOTE: Progressive items are not currently supported in Manual. Once they are,
#       this hook will provide the ability to meaningfully change those.
def after_load_progressive_item_file(progressive_item_table: list) -> list:
    return progressive_item_table

# called after the locations.json file has been loaded, before any location loading or processing has occurred
# if you need access to the locations after processing to add ids, etc., you should use the hooks in World.py
def after_load_location_file(location_table: list) -> list:
    package_base_name = re.sub(r'\.hooks\.\w+$', '.Data', __name__)
    global _generated_events
    _generated_events = []
    
    pokemon_types = ["Normal", "Fire", "Water", "Grass", "Electric", "Ice", "Fighting", 
                     "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", 
                     "Dragon", "Dark", "Steel", "Fairy"]
    
    # Extra Locations files
    extra_location_files = ["data/locations/locations_dens.json", "data/locations/locations_types.json", "data/locations/locations_wanderers.json"]
    for file_path in extra_location_files:
        try:
            raw_bytes = pkgutil.get_data(package_base_name, file_path)
            if raw_bytes:
                extra_data = json.loads(raw_bytes.decode("utf-8"))
                location_table.extend(extra_data)
        except Exception as e:
            print(f"Error loading extra hook location file {file_path}: {e}")

# Mastery Type Goal events
    type_to_pokemon_map = {p_type: [] for p_type in pokemon_types}
    for loc in location_table:
        if "Pokemon" in loc.get("category", []):
            for p_type in pokemon_types:
                if p_type in loc.get("category", []):
                    type_to_pokemon_map[p_type].append(loc["name"])

    
    for p_type, pokemon_list in type_to_pokemon_map.items():
        if pokemon_list:  #Only pokemon that have been assigned a type
            event_item = {
                "name": f"Event - {p_type} Type Caught",
                "category": [p_type],
                "copy_location": pokemon_list 
            }
            _generated_events.append(event_item)
            logging.info(f"Generated backend event: '{event_item['name']}' linking to {len(pokemon_list)} pokemon.")
            
    return location_table


# called after the events.json file has been loaded, before any processing has occurred
# If you need access to the events after processing, you should use the hooks in World.py
def after_load_event_file(event_table: list) -> list:
    event_table.extend(_generated_events)
    return event_table


# called after the locations.json file has been loaded, before any location loading or processing has occurred
# if you need access to the locations after processing to add ids, etc., you should use the hooks in World.py
def after_load_region_file(region_table: dict) -> dict:
    return region_table

# called after the categories.json file has been loaded
def after_load_category_file(category_table: dict) -> dict:
    return category_table

# called after the categories.json file has been loaded
def after_load_option_file(option_table: dict) -> dict:
    # option_table["core"] is the dictionary of modification of existing options
    # option_table["user"] is the dictionary of custom options
    return option_table

# called after the meta.json file has been loaded and just before the properties of the apworld are defined. You can use this hook to change what is displayed on the webhost
# for more info check https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/world%20api.md#webworld-class
def after_load_meta_file(meta_table: dict) -> dict:
    return meta_table

# called when an external tool (eg Universal Tracker) ask for slot data to be read
# use this if you want to restore more data
# return True if you want to trigger a regeneration if you changed anything
def hook_interpret_slot_data(world, player: int, slot_data: dict[str, any]) -> dict | bool:
    return False
