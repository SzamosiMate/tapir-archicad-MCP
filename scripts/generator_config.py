# scripts/_generator_configs.py

import re
import tomllib
from dataclasses import dataclass, field
from importlib.metadata import version
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def get_multiconn_version(project_file: Path) -> str:
    dependencies = tomllib.loads(project_file.read_text(encoding="utf-8"))["project"]["dependencies"]
    pins = [
        match[1]
        for dependency in dependencies
        if (match := re.fullmatch(r"multiconn[-_]archicad\s*==\s*([^\s;*,]+)", dependency, re.IGNORECASE))
    ]
    if len(pins) != 1:
        raise ValueError("Generation requires one exact multiconn-archicad==VERSION dependency pin.")
    installed = version("multiconn-archicad")
    if installed != pins[0]:
        raise RuntimeError(f"MultiConn {pins[0]} is pinned but {installed} is installed. Run uv sync --locked first.")
    return pins[0]


MULTICONN_VERSION = get_multiconn_version(ROOT_DIR / "pyproject.toml")
MULTICONN_SOURCE_URL = (
    f"https://raw.githubusercontent.com/SzamosiMate/multiconn_archicad/refs/tags/v{MULTICONN_VERSION}/code_generation"
)
ORGANIZED_COMMANDS_URL = f"{MULTICONN_SOURCE_URL}/unified/temp_files/01_organized_commands.json"

@dataclass
class ApiSourceConfig:
    """Configuration settings for a single API source."""
    name: str
    details_url: str
    model_names_url: str
    output_dir: Path
    api_call_method: str
    group_mapping: dict[str, str]
    prefix_to_strip: str = ""
    paginated_commands: dict[str, str] = field(default_factory=dict)
    commands_to_exclude: set[str] = field(default_factory=set)


TAPIR_CONFIG = ApiSourceConfig(
    name="tapir",
    details_url=ORGANIZED_COMMANDS_URL,
    model_names_url=f"{MULTICONN_SOURCE_URL}/tapir/schema/_command_model_names.json",
    output_dir=ROOT_DIR / "src" / "tapir_archicad_mcp" / "tools" / "generated" / "tapir",
    api_call_method="post_tapir_command",
    group_mapping={
        # Elements
        "Element Creation Commands": "elements",
        "Element Modification Commands": "elements",
        "Element Commands": "elements",
        "Element grouping Commands": "grouping",
        "Solid Element Operation Commands": "solid_ops_",

        # Domain specifics
        "MEP Commands": "mep",
        "Keynote Commands": "keynotes",
        "Design Options Commands": "design_options",
        "IFC Commands": "ifc",
        "Classification Commands": "classifications",
        "Property Commands": "properties",
        "Attribute Commands": "attributes",
        "Graphic Override Commands": "attributes",
        "Favorites Commands": "favorites",
        "Library Commands": "library",

        # Project & App structure
        "Application Commands": "app",
        "Project Commands": "project",
        "Navigator Commands": "navigator",
        "Issue Management Commands": "issues",
        "Revision Management Commands": "revisions",
        "Teamwork Commands": "teamwork",
        "Script UI Commands": "dev",
    },
    commands_to_exclude={
        "GetProjectInfo", # discovery_list_active_archicads covers this
        "GetArchicadLocation", # discovery_list_active_archicads covers this
        "QuitArchicad", # AI probably shouldn't quit
        "GenerateDocumentation", # command only for internal use
        "ShowScriptUI", # used in apps
        "GetScriptUIResult", # used in apps
        "DeleteAttributes",  # official has a simpler interface for the same functionality (works for MEP systems)
        "DeleteNavigatorItems",  # same parameters as the Official command
        "MoveNavigatorItem",  # same parameters as the Official command
        "GetGraphicalOverrideRules", # Duplicate command in 1.7.2
        "CreateGraphicalOverrideRule", # Duplicate command in 1.7.2
        "CreateGraphicalOverrideCombination", # Duplicate command in 1.7.2
    },
    paginated_commands={
        "GetAllElements": "elements",
        "GetSelectedElements": "elements",
        "GetElementsByType": "elements",
        "GetAllProperties": "properties",
        "GetAttributesByType": "attributes",
        "GetIssues": "issues",
        "GetElementsByIFCIds": "elementsByIFCIds",
        "GetMEPElements": "elements",
        "GetAvailableLibraryParts": "libraryParts",
        "GetDetailsOfElements": "detailsOfElements",
        "GetGDLParametersOfElements": "gdlParametersOfElements",
        "Get3DGeometryOfElements": "geometries3D",
        "GetQuantitiesOfElements": "quantitiesOfElements",
        "GetGridElements": "gridElements",
        "GetGraphicOverrideCombinations": "graphicOverrideCombinations",
        "GetGraphicOverrideRuleGroups": "graphicOverrideRuleGroups",
        "GetGraphicOverrideRules": "graphicOverrideRules",
        "GetGraphicalOverrideRules": "rules",
        "GetElectricalCircuits": "electricalCircuits",
        "GetElectricalDevices": "electricalDevices",
        "GetElectricalPanels": "electricalPanels",
        "GetMEPSystemGroups": "systemGroups",
    }
)


OFFICIAL_CONFIG = ApiSourceConfig(
    name="official",
    details_url=ORGANIZED_COMMANDS_URL,
    model_names_url=f"{MULTICONN_SOURCE_URL}/official/schema/_command_model_names.json",
    output_dir=ROOT_DIR / "src" / "tapir_archicad_mcp" / "tools" / "generated" / "official",
    api_call_method="post_command",
    prefix_to_strip="API.",
    group_mapping={
        "View Map Commands": "view",
        "Layout Book Commands": "layout",
        "Navigator Tree Commands": "navigator",
        "Attribute Commands": "attributes",
        "Element Geometry Commands": "elements",
        "Element Listing Commands": "elements",
        "Element Relation Commands": "elements",
        "Classification Commands": "classifications",
        "Property Commands": "properties",
        "Component Commands": "components",
        "AddOn Commands": "dev",
        "Basic Commands": "app",
    },
    commands_to_exclude={
        "Get3DBoundingBoxes",  # Tapir command works on subelements
        "GetAllElements",  # Tapir command works on more element types
        "GetElementsByType",  # Tapir command works on more element types
        "GetSelectedElements",  # Tapir command works on more element types
        "GetClassificationsOfElements",  # Tapir command works on subelements
        "SetClassificationsOfElements",  # Tapir command works on subelements
        "SetPropertyValuesOfElements",  # Tapir command works on subelements
        "GetPropertyValuesOfElements",  # Tapir command works on subelements
        "GetAttributesByType",  # Tapir command returns additional index and name
        "IsAlive",  # not useful as tool
        "GetProductInfo",  # discovery_list_active_archicads covers this
        "ExecuteAddOnCommand",  # we handle it with namespaces
        "GetBuildingMaterialAttributes",  # Tapir returns index
        "GetCompositeAttributes",  # Tapir returns index
        "GetFillAttributes",  # Tapir returns index
        "GetLayerAttributes",  # Tapir returns index
        "GetLayerCombinationAttributes",  # Tapir returns index
        "GetLineAttributes",  # Tapir returns index
        "GetPenTableAttributes",  # Tapir returns index
        "GetProfileAttributes",  # Tapir returns index
        "GetSurfaceAttributes",  # Tapir returns index
        "GetZoneCategoryAttributes",  # Tapir returns index
        "RenameNavigatorItem",  # Tapir command takes flat parameters instead of a union
        "GetNavigatorItemTree",  # Tapir returns additional fields
    },
    paginated_commands={
        "GetElementsByClassification": "elements",
        "GetAllPropertyIds": "propertyIds",
        "GetAllPropertyNames": "properties",
    },
)
