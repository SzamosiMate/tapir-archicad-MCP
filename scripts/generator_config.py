# scripts/_generator_configs.py

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Set

ROOT_DIR = Path(__file__).parent.parent

@dataclass
class ApiSourceConfig:
    """Configuration settings for a single API source."""
    name: str
    details_url: str
    model_names_url: str
    output_dir: Path
    api_call_method: str
    group_mapping: Dict[str, str]
    prefix_to_strip: str = ""
    paginated_commands: Dict[str, str] = field(default_factory=dict)
    commands_to_exclude: Set[str] = field(default_factory=set)


TAPIR_CONFIG = ApiSourceConfig(
    name="tapir",
    details_url="https://raw.githubusercontent.com/SzamosiMate/multiconn_archicad/main/code_generation/tapir/schema/_command_details.json",
    model_names_url="https://raw.githubusercontent.com/SzamosiMate/multiconn_archicad/main/code_generation/tapir/schema/_command_model_names.json",
    output_dir=ROOT_DIR / "src" / "tapir_archicad_mcp" / "tools" / "generated" / "tapir",
    api_call_method="post_tapir_command",
    group_mapping={
        "Application Commands": "app", "Project Commands": "project", "Element Commands": "elements",
        "Favorites Commands": "favorites", "Property Commands": "properties", "Attribute Commands": "attributes",
        "Library Commands": "library", "Navigator Commands": "navigator", "Issue Management Commands": "issues",
        "Revision Management Commands": "revisions", "Teamwork Commands": "teamwork", "Developer Commands": "dev",
    },
    commands_to_exclude={
        "GetProjectInfo", # discovery_list_active_archicads covers this
        "GetArchicadLocation", # discovery_list_active_archicads covers this
        "QuitArchicad", # AI probably shouldn't quit
        "GenerateDocumentation", # command only for internal use
    },
    paginated_commands={
        "GetAllElements": "elements",
        "GetSelectedElements": "elements",
        "GetElementsByType": "elements",
        "GetAllProperties": "properties",
        "GetAttributesByType": "attributes",
        "GetIssues": "issues",
        "GetElementsByIFCIds": "elementsByIFCIds",
        "GetElementsOfDesignOptions": "elementsOfDesignOptions"
    }
)


OFFICIAL_CONFIG = ApiSourceConfig(
    name="official",
    details_url="https://raw.githubusercontent.com/SzamosiMate/multiconn_archicad/main/code_generation/official/schema/_command_details.json",
    model_names_url="https://raw.githubusercontent.com/SzamosiMate/multiconn_archicad/main/code_generation/official/schema/_command_model_names.json",
    output_dir=ROOT_DIR / "src" / "tapir_archicad_mcp" / "tools" / "generated" / "official",
    api_call_method="post_command",
    prefix_to_strip="API.",
    group_mapping={
        "View Map Commands": "view", "Layout Book Commands": "layout", "Navigator Tree Commands": "navigator",
        "Attribute Commands": "attributes", "Element Geometry Commands": "elements", "Element Listing Commands": "elements",
        "Element Relation Commands": "elements", "Classification Commands": "classifications", "Property Commands": "properties",
        "Component Commands": "components", "AddOn Commands": "dev", "Basic Commands": "app",
    },
    commands_to_exclude={
        "Get3DBoundingBoxes", # Tapir command works on subelements
        "GetAllElements", # Tapir command works on more element types
        "GetElementsByType", # Tapir command works on more element types
        "GetSelectedElements", # Tapir command works on more element types
        "GetClassificationsOfElements", # Tapir command works on subelements
        "SetClassificationsOfElements", # Tapir command works on subelements
        "SetPropertyValuesOfElements", # Tapir command works on subelements
        "GetPropertyValuesOfElements", # Tapir command works on subelements
        "GetAttributesByType",  # Tapir command returns additional index and name
        "IsAlive",  # not useful as tool
        "GetProductInfo",  # discovery_list_active_archicads covers this
        "ExecuteAddOnCommand", # we handle it with namespaces
    },
    paginated_commands = {
        "GetElementsByClassification": "elements",
        "GetAllPropertyIds": "properties",
        "GetAllPropertyNames": "properties",
    }
)