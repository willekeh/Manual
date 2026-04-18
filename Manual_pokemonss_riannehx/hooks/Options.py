# Object classes from AP that represent different types of options that you can create
from Options import Option, FreeText, NumericOption, Toggle, DefaultOnToggle, Choice, TextChoice, Range, NamedRange, OptionGroup, PerGameCommonOptions
# These helper methods allow you to determine if an option has been set, or what its value is, for any player in the multiworld
from ..Helpers import is_option_enabled, get_option_value
from typing import Type, Any


####################################################################
# NOTE: At the time that options are created, Manual has no concept of the multiworld or its own world.
#       Options are defined before the world is even created.
#
# Example of creating your own option:
#
#   class MakeThePlayerOP(Toggle):
#       """Should the player be overpowered? Probably not, but you can choose for this to do... something!"""
#       display_name = "Make me OP"
#
#   options["make_op"] = MakeThePlayerOP
#
#
# Then, to see if the option is set, you can call is_option_enabled or get_option_value.
#####################################################################

class GameVersion(Choice):
    """Choose which game you are playing. 
    This matters for the different version exclusives. Default removes all exclusives"""
    display_name = "Game Version"
    option_RemoveAll = 1
    option_Shield = 2
    option_Sword = 3
    default = 1

class BrokenShardsTotal(Range):
    """Choose the number of Goal items (macguffin hunt goal item) in the pool.
    This gets reduced automatically if there are too few locations.
    This is only for the special encounter goal"""
    display_name = "Number of broken shards in the pool"
    range_start = 1
    range_end = 40
    default = 40

class BrokenShardsRequired(Range):
    """Choose the number of Spiritomb wisps required to win.
    If this is set higher than wisps_total, it is reduced to match."""
    display_name = "Number of wisps required to win"
    range_start = 1
    range_end = 40
    default = 10

# This is called before any manual options are defined, in case you want to define your own with a clean slate or let Manual define over them
def before_options_defined(options: dict[str, Type[Option[Any]]]) -> dict[str, Type[Option[Any]]]:
    options["game_version"] = GameVersion
    options["broken_shards_total"] = BrokenShardsTotal
    options["broken_shards_required"] = BrokenShardsRequired
    return options

# This is called after any manual options are defined, in case you want to see what options are defined or want to modify the defined options
def after_options_defined(options: Type[PerGameCommonOptions]):
    # To access a modifiable version of options check the dict in options.type_hints
    # For example if you want to change DLC_enabled's display name you would do:
    # options.type_hints["DLC_enabled"].display_name = "New Display Name"

    #  Here's an example on how to add your aliases to the generated goal
    # options.type_hints['goal'].aliases.update({"example": 0, "second_alias": 1})
    # options.type_hints['goal'].options.update({"example": 0, "second_alias": 1})  #for an alias to be valid it must also be in options

    pass

# Use this Hook if you want to add your Option to an Option group (existing or not)
def before_option_groups_created(groups: dict[str, list[Type[Option[Any]]]]) -> dict[str, list[Type[Option[Any]]]]:
    # Uses the format groups['GroupName'] = [TotalCharactersToWinWith]
    return groups

def after_option_groups_created(groups: list[OptionGroup]) -> list[OptionGroup]:
    return groups
