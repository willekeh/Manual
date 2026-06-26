# Object classes from AP core, to represent an entire MultiWorld and this individual World that's part of it
from worlds.AutoWorld import World
from BaseClasses import MultiWorld, CollectionState, Item

# Object classes from Manual -- extending AP core -- representing items and locations that are used in generation
from ..Items import ManualItem
from ..Locations import ManualLocation

# Raw JSON data from the Manual apworld, respectively:
#          data/game.json, data/items.json, data/locations.json, data/regions.json
#
from ..Data import game_table, item_table, location_table, region_table

# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value, format_state_prog_items_key, ProgItemsCat

# calling logging.info("message") anywhere below in this file will output the message to both console and log file
import logging

########################################################################################
## Order of method calls when the world generates:
##    1. create_regions - Creates regions and locations
##    2. create_items - Creates the item pool
##    3. set_rules - Creates rules for accessing regions and locations
##    4. generate_basic - Runs any post item pool options, like place item/category
##    5. pre_fill - Creates the victory location
##
## The create_item method is used by plando and start_inventory settings to create an item from an item name.
## The fill_slot_data method will be used to send data to the Manual client for later use, like deathlink.
########################################################################################



# Use this function to change the valid filler items to be created to replace item links or starting items.
# Default value is the `filler_item_name` from game.json
def hook_get_filler_item_name(world: World, multiworld: MultiWorld, player: int) -> str | bool:
    return False

# Called before regions and locations are created. Not clear why you'd want this, but it's here. Victory location is included, but Victory event is not placed yet.
def before_create_regions(world: World, multiworld: MultiWorld, player: int):

    remove_low = get_option_value(multiworld, player, "remove_low_percentage")
    game_version = get_option_value(multiworld, player, "game_version")

    #Change below 5% encounters to only locations that dont have said 5%
    if remove_low:
        for loc in world.location_table:
            categories = loc.get("category", [])

            # Nickit Force Route 2 Access
            if "LowPerc:Nickit" in categories:
                loc["requires"] = "|Route 2 Access|"

            # Yamper Force Route 4 Access
            elif "LowPerc:Yamper" in categories:
                loc["requires"] = "|Route 4 Access|"
                
            # Zigzagoon Only Route 3 or Route 2 with bike
            elif "LowPerc:Zigzagoon" in categories:
                loc["requires"] = "|Route 3 Access| OR (|Route 2 Access| AND |Progressive bike:2|)"
                
            # Chewtle Force Route 2 Access
            elif "LowPerc:Chewtle" in categories:
                loc["requires"] = "|Route 2 Access|"
                
            # Hoothoot Force Slumbering Weald Access
            elif "LowPerc:Hoothoot" in categories:
                loc["requires"] = "|Slumbering Weald Access|"
                
            # Stunfisk Force Galar Mine 2 Access
            elif "LowPerc:Stunfisk" in categories:
                loc["requires"] = "|Galar Mine 2 Access|"
                
            # Impidimp Force Glimwood Tangle Access
            elif "LowPerc:Impidimp" in categories:
                loc["requires"] = "|Glimwood Tangle Access|"
            elif "LowPerc:Roggenrola" in categories:
                if game_version == 3 or game_version == 1:
                    loc["requires"] = "|Motostoke Outskirts Access|"

    ##Researcher Goal, Add Type Unlock requires to location and victory
    current_goal_name = ""
    if hasattr(world, "options") and hasattr(world.options, "goal"):
        current_goal_name = world.options.goal.current_key

    if str(current_goal_name).lower() != "type researcher":
        return

    active_types = set()
    pokemon_types = ["Normal", "Fire", "Water", "Grass", "Electric", "Ice", "Fighting", 
                     "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", 
                     "Dragon", "Dark", "Steel", "Fairy"]
    
    for loc in world.location_table:
        if "Pokemon" in loc.get("category", []):
            for p_type in pokemon_types:
                if p_type in loc.get("category", []):
                    active_types.add(p_type)


    for loc in world.location_table:
        if "Pokemon" in loc.get("category", []):
            loc_types = [p_type for p_type in pokemon_types if p_type in loc.get("category", []) and p_type in active_types]
            
            if loc_types:
                type_lock_requirements = [f"|Type Unlock - {p_type} Type:1|" for p_type in loc_types]
                unlock_logic_str = f"({' AND '.join(type_lock_requirements)})"
                
                existing_req = loc.get("requires", "").strip()
                if existing_req:
                    loc["requires"] = f"({existing_req}) AND {unlock_logic_str}"
                else:
                    loc["requires"] = unlock_logic_str

    type_or_chains = {}

    for loc in world.location_table:
        if "Type Collection" in loc.get("category", []):
            for p_type in active_types:
                if loc["name"] == f"Type Researched - {p_type} Type":
                    
                    pokemon_requires_list = []
                    for pokemon in world.location_table:
                        if "Pokemon" in pokemon.get("category", []) and p_type in pokemon.get("category", []):
                            req_string = pokemon["requires"].strip()
                            pokemon_requires_list.append(f"({req_string})")

                    overworld_or_chain = f"({' OR '.join(pokemon_requires_list)})"
                    type_or_chains[p_type] = overworld_or_chain

                    loc["requires"] = f"{overworld_or_chain} AND |Type Unlock - {p_type} Type:1|"
                    break

    victory_requirements = []
    for p_type in active_types:
        victory_requirements.append(f"({type_or_chains[p_type]} AND |Type Unlock - {p_type} Type:1|)")
    
    victory_string = " AND ".join(victory_requirements)
    
    for loc in world.location_table:
        if "Type Researcher" == loc["name"]:
            loc["requires"] = victory_string
            break



# Called after regions and locations are created, in case you want to see or modify that information. Victory location is included.
def after_create_regions(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to remove locations from the world
    locationNamesToRemove: list[str] = [] # List of location names

    #game version filters And Remove locations that are below 5%
    game_version = get_option_value(multiworld, player, "game_version")
    remove_low = get_option_value(multiworld, player, "remove_low_percentage")
    if game_version == 1:
        locationNamesToRemove += world.location_name_groups["GameShield"]
        locationNamesToRemove += world.location_name_groups["GameSword"]
        if remove_low:
            locationNamesToRemove += ["Heatmor", "Durant", "Karrablast", "Shelmet", "Jellicent", "Toxapex","Timburr"]
    if game_version == 2: #Shield
        locationNamesToRemove += world.location_name_groups["GameSword"]
        if remove_low:
            locationNamesToRemove += ["Durant", "Karrablast", "Toxapex", "Timburr"]
    if game_version == 3: #Sword
        locationNamesToRemove += world.location_name_groups["GameShield"]
        if remove_low:
            locationNamesToRemove += ["Heatmor", "Shelmet", "Jellicent"]

    current_goal_name = ""
    if hasattr(world, "options") and hasattr(world.options, "goal"):
        current_goal_name = world.options.goal.current_key

    pokemon_types = ["Normal", "Fire", "Water", "Grass", "Electric", "Ice", "Fighting", 
                     "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", 
                     "Dragon", "Dark", "Steel", "Fairy"]

    # If Type Researcher is NOT the goal, wipe everything related to it
    if str(current_goal_name).lower() != "type researcher":
        for p_type in pokemon_types:
            locationNamesToRemove.append(f"Type Researched - {p_type} Type")

    # If Type Researcher is active, find the missing types and remove their tracker locations
    else:
        active_types = set()
        for loc in world.location_table:
            if "Pokemon" in loc.get("category", []):
                for p_type in pokemon_types:
                    if p_type in loc.get("category", []):
                        active_types.add(p_type)

        # Gather any inactive checking locations for complete deletion
        for p_type in pokemon_types:
            if p_type not in active_types:
                locationNamesToRemove.append(f"Type Researched - {p_type} Type")
        
    for region in multiworld.regions:
        if region.player == player:
            for location in list(region.locations):
                if location.name in locationNamesToRemove:
                    region.locations.remove(location)


# This hook allows you to access the item names & counts before the items are created. Use this to increase/decrease the amount of a specific item in the pool
# Valid item_config key/values:
# {"Item Name": 5} <- This will create qty 5 items using all the default settings
# {"Item Name": {"useful": 7}} <- This will create qty 7 items and force them to be classified as useful
# {"Item Name": {"progression": 2, "useful": 1}} <- This will create 3 items, with 2 classified as progression and 1 as useful
# {"Item Name": {0b0110: 5}} <- If you know the special flag for the item classes, you can also define non-standard options. This setup
#       will create 5 items that are the "useful trap" class
# {"Item Name": {ItemClassification.useful: 5}} <- You can also use the classification directly
def before_create_items_all(item_config: dict[str, int|dict], world: World, multiworld: MultiWorld, player: int) -> dict[str, int|dict]:
    location_count = len(world.get_locations())
    current_goal_name = ""
    other_items_count = 0

    # Check if Mend The Broken Shield/Sword goal is active
    current_goal_name = world.options.goal.current_key
    
    if current_goal_name != "mend the broken shield/sword":
        # Set shards to 0 when not the correct goal
        shards_total = 0
        world.options.broken_shards_total.value = 0
    else:
        shards_total = world.options.broken_shards_total.value

        for name, data in item_config.items():
            if name != "Broken shards":
                if isinstance(data, dict):
                    other_items_count += sum(data.values())
                else:
                    other_items_count += data
                                        
        # To crash less with minimal settings 
        buffer = 3 
        free_space = location_count - other_items_count - buffer

        if shards_total > free_space:
            # Check if shards total is higher than free space if yes turn down shards
            shards_total = max(0, free_space) 
            world.options.broken_shards_total.value = shards_total
    
    item_config["Broken shards"] = shards_total
    
    return item_config

# The item pool before starting items are processed, in case you want to see the raw item pool at that stage
def before_create_items_starting(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    start_logic = get_option_value(multiworld, player, "region_start")
    
    start_inventory_names = []

    locations = [
        "Rolling Fields", "Bridge Field", "Dappled Grove", "Dusty Bowl", 
        "Giant's Mirror", "East Lake Axewell", "Giant's Cap", "Giant's Seat", 
        "Hammerlocke Hills", "Motostoke Riverbank", "North Lake Miloch", 
        "South Lake Miloch", "Stony Wilderness", "Watchtower Ruins", "West Lake Axewell"
    ]
    weather = [
        "Normal weather", "Overcast", "Raining", "Thunderstorm", 
        "Snowing", "Snowstorm", "Intense Sun", "Sandstorm", "Fog"
    ]

    if start_logic == 1: # Fixed
        start_inventory_names = ["Rolling Fields", "Normal weather", "Type Unlock - Bug Type", "Route 1 Access"]

    elif start_logic == 2: # Region (Random region, Fixed weather)
        multiworld.random.shuffle(locations)
        start_inventory_names = [locations[0], "Normal weather"]

    elif start_logic == 3: # Weather (Fixed region, Random weather)
        multiworld.random.shuffle(weather)
        start_inventory_names = ["Rolling Fields", weather[0]]

    elif start_logic == 4: # Both (Both random)
        multiworld.random.shuffle(locations)
        multiworld.random.shuffle(weather)
        start_inventory_names = [locations[0], weather[0]]

    for item_name in start_inventory_names:
        found_item = next((item for item in item_pool if item.name == item_name), None)
        
        if found_item:
            multiworld.push_precollected(found_item)
            item_pool.remove(found_item)

    return item_pool

# The item pool after starting items are processed but before filler is added, in case you want to see the raw item pool at that stage
def before_create_items_filler(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    # Use this hook to remove items from the item pool
    itemNamesToRemove: list[str] = [] # List of item names

    current_goal_name = ""
    if hasattr(world, "options") and hasattr(world.options, "goal"):
        current_goal_name = world.options.goal.current_key

    pokemon_types = ["Normal", "Fire", "Water", "Grass", "Electric", "Ice", "Fighting", 
                     "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", 
                     "Dragon", "Dark", "Steel", "Fairy"]

    # Remove if goal is not Type Researcher
    if str(current_goal_name).lower() != "type researcher":
        for p_type in pokemon_types:
            itemNamesToRemove.append(f"Type Unlock - {p_type} Type")
    # Remove unlocks that dont have a matching location type
    else:
        active_types = set()
        for loc in world.location_table:
            if "Pokemon" in loc.get("category", []):
                for p_type in pokemon_types:
                    if p_type in loc.get("category", []):
                        active_types.add(p_type)

        for p_type in pokemon_types:
            if p_type not in active_types:
                itemNamesToRemove.append(f"Type Unlock - {p_type} Type")

    for itemName in itemNamesToRemove:
        item = next((i for i in item_pool if i.name == itemName), None)
        if item:
            item_pool.remove(item)

    return item_pool

    # Some other useful hook options:

    ## Place an item at a specific location
    # location = next(l for l in multiworld.get_unfilled_locations(player=player) if l.name == "Location Name")
    # item_to_place = next(i for i in item_pool if i.name == "Item Name")
    # location.place_locked_item(item_to_place)
    # item_pool.remove(item_to_place)

# The complete item pool prior to being set for generation is provided here, in case you want to make changes to it
def after_create_items(item_pool: list, world: World, multiworld: MultiWorld, player: int) -> list:
    return item_pool

# Called before rules for accessing regions and locations are created. Not clear why you'd want this, but it's here.
def before_set_rules(world: World, multiworld: MultiWorld, player: int):
    pass

# Called after rules for accessing regions and locations are created, in case you want to see or modify that information.
def after_set_rules(world: World, multiworld: MultiWorld, player: int):
    # Use this hook to modify the access rules for a given location

    #Set BrokenShards to the victory location 
    total = world.options.broken_shards_total.value
    required = world.options.broken_shards_required.value
    
    # Failsafe incase of wrong way around
    final_required = min(total, required)
    location_names = [loc.name for loc in multiworld.get_locations(player)]
    
    if "Mend The Broken Shield/Sword" in location_names:
        # Set Broken Shard required
        eternatus_loc = multiworld.get_location("Mend The Broken Shield/Sword", player)
        eternatus_loc.access_rule = lambda state: state.has("Broken shards", player, final_required)

    def Example_Rule(state: CollectionState) -> bool:
        # Calculated rules take a CollectionState object and return a boolean
        # True if the player can access the location
        # CollectionState is defined in BaseClasses
        return True

    ## Common functions:
    # location = world.get_location(location_name, player)
    # location.access_rule = Example_Rule

    ## Combine rules:
    # old_rule = location.access_rule
    # location.access_rule = lambda state: old_rule(state) and Example_Rule(state)
    # OR
    # location.access_rule = lambda state: old_rule(state) or Example_Rule(state)

# The item name to create is provided before the item is created, in case you want to make changes to it
def before_create_item(item_name: str, world: World, multiworld: MultiWorld, player: int) -> str:
    return item_name

# The item that was created is provided after creation, in case you want to modify the item
def after_create_item(item: ManualItem, world: World, multiworld: MultiWorld, player: int) -> ManualItem:
    return item

# This method is run towards the end of pre-generation, before the place_item options have been handled and before AP generation occurs
def before_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This method is run at the very end of pre-generation, once the place_item options have been handled and before AP generation occurs
def after_generate_basic(world: World, multiworld: MultiWorld, player: int):
    pass

# This method is run every time an item is added to the state, can be used to modify the value of an item.
# IMPORTANT! Any changes made in this hook must be cancelled/undone in after_remove_item
def after_collect_item(world: World, state: CollectionState, Changed: bool, item: Item):
    # the following let you add to the Potato Item Value count
    # if item.name == "Cooked Potato":
    #     state.prog_items[item.player][format_state_prog_items_key(ProgItemsCat.VALUE, "Potato")] += 1
    pass

# This method is run every time an item is removed from the state, can be used to modify the value of an item.
# IMPORTANT! Any changes made in this hook must be first done in after_collect_item
def after_remove_item(world: World, state: CollectionState, Changed: bool, item: Item):
    # the following let you undo the addition to the Potato Item Value count
    # if item.name == "Cooked Potato":
    #     state.prog_items[item.player][format_state_prog_items_key(ProgItemsCat.VALUE, "Potato")] -= 1
    pass


# This is called before slot data is set and provides an empty dict ({}), in case you want to modify it before Manual does
def before_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called after slot data is set and provides the slot data at the time, in case you want to check and modify it after Manual is done with it
def after_fill_slot_data(slot_data: dict, world: World, multiworld: MultiWorld, player: int) -> dict:
    return slot_data

# This is called right at the end, in case you want to write stuff to the spoiler log
def before_write_spoiler(world: World, multiworld: MultiWorld, spoiler_handle) -> None:
    pass

# This is called when you want to add information to the hint text
def before_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:

    ### Example way to use this hook:
    # if player not in hint_data:
    #     hint_data.update({player: {}})
    # for location in multiworld.get_locations(player):
    #     if not location.address:
    #         continue
    #
    #     use this section to calculate the hint string
    #
    #     hint_data[player][location.address] = hint_string

    pass

def after_extend_hint_information(hint_data: dict[int, dict[int, str]], world: World, multiworld: MultiWorld, player: int) -> None:
    pass
