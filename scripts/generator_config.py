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
    image_fields: dict[str, str] = field(default_factory=dict)
    image_lists: dict[str, str] = field(default_factory=dict)
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
        "Solid Element Operation Commands": "solid_ops",

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
        "Project Data Commands": "project_data",
        "Analytical Commands": "analytical",
        "Navigator Commands": "navigator",
        "Issue Management Commands": "issues",
        "Revision Management Commands": "revisions",
        "Teamwork Commands": "teamwork",
        "Script UI Commands": "dev",
    },
    commands_to_exclude={
        "QuitArchicad",  # Can lose unsaved work; easy to quit manually
        "CloseProject",  # Can lose unsaved work; easy to close manually
        "NewProject",  # Discards unsaved work; use the application UI
        "GenerateDocumentation",  # Internal use only
        "ShowScriptUI",  # Application UI workflow
        "GetScriptUIResult",  # Companion to ShowScriptUI
        "DeleteAttributes",  # Official deletes by GUID without a type argument
        "DeleteAttributeFolders",  # Same deletion; prefer Official
        "RenameAttributeFolders",  # Same rename; prefer Official
        "DeleteNavigatorItems",  # Same contract; prefer Official
        "MoveNavigatorItem",  # Same operation; prefer Official
        "CloneProjectMapItemToViewMap",  # Only adds batching; prefer Official
        "CreateLayoutSubset",  # Only adds batching/defaults; prefer Official
        "CreateViewMapFolder",  # Official also supports sibling placement
        "GetGraphicalOverrideRules",  # Graphic API also returns styles
        "CreateGraphicalOverrideRule",  # Covered by Graphic create/modify commands
        "CreateGraphicalOverrideCombination",  # Covered by Graphic combinations
        "GetComposites",  # Official also returns total thickness; index available elsewhere
        "GetLayers",  # Same layer state; index available elsewhere
        "GetLines",  # Same line details; index available elsewhere
        "GetPenTables",  # Pen data, index and active tables available elsewhere
        "GetZoneCategories",  # Same category details; index available elsewhere
        "GetCurrentRevisionChangesOfLayouts",  # Malformed revision response schema
        "GetRevisionChangesOfElements",  # Bad response schema and element GUID lookup
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
        "GetPropertyValuesOfElements": "propertyValuesForElements",
        "GetIFCPropertiesOfElements": "elementIFCProperties",
        "GetRelationsOfElements": "relations",
        "GetMEPRoutingElements": "routingElements",
        "GetCollisions": "collisions",
        "GetGDLParametersOfElements": "gdlParametersOfElements",
        "Get3DGeometryOfElements": "geometries3D",
        "GetQuantitiesOfElements": "quantitiesOfElements",
        "GetGridElements": "gridElements",
        "GetGraphicOverrideCombinations": "graphicOverrideCombinations",
        "GetGraphicOverrideRuleGroups": "graphicOverrideRuleGroups",
        "GetGraphicOverrideRules": "graphicOverrideRules",
        "GetElectricalCircuits": "electricalCircuits",
        "GetElectricalDevices": "electricalDevices",
        "GetElectricalPanels": "electricalPanels",
        "GetMEPSystemGroups": "systemGroups",
        "GetDetailsOfElements": "detailsOfElements",
        "GetHotlinks": "hotlinks",
        "GetMarkerParametersOfElements": "markerParametersOfElements",
        "GetSubelementsOfHierarchicalElements": "subelements",
        "GetAllFavorites": "favorites",
        "GetCategoryValuesOfElements": "categoryValuesOfElements",
        "GetDatabases": "databases",
        "GetElementSetsOfElements": "elementSetsOfElements",
        "GetElementsInDrawOrder": "elements",
        "GetFavoriteSettings": "favoriteSettings",
        "GetGraphicOverrideRulesByName": "graphicOverrideRules",
        "GetHotlinkProxyElementTable": "proxyElementTables",
        "GetIFCAttributesOfElements": "elementIFCAttributes",
        "GetLinksOfElements": "linksOfElements",
        "GetOpeningDetails": "openings",
        "GetOpeningFloorPlanParameters": "openings",
        "GetProjectData": "values",
        "GetProjectDataKeys": "keys",
        "GetPropertyDefinitionsOfAttributes": "propertyDefinitionsOfAttributes",
        "GetSurfaceQuantitiesOfElements": "surfaceQuantitiesOfElements",
        "GetUserDataOfGroups": "userDataOfGroups",
        "GetZoneReductions": "reductionsOfZones",
        "TriangulatePolygonsOfElements": "triangulations",
    },
    image_fields={
        "GetElementPreviewImage": "previewImage",
        "GetFavoritePreviewImage": "previewImage",
        "GetRoomImage": "roomImage",
        "GetCurrentViewImage": "image",
    },
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
        "GetAttributesByType",  # Tapir adds names, indices and MEP/operation types
        "IsAlive",  # not useful as tool
        "ExecuteAddOnCommand",  # we handle it with namespaces
        "CreateAttributeFolders",  # Tapir accepts MEP/operation folder types
        "MoveAttributesAndFolders",  # Tapir returns per-item move results
        "GetBuildingMaterialAttributes",  # Tapir adds manufacturer, fill and display details
        "GetLayerCombinationAttributes",  # Tapir returns combination-specific layer states
        "GetProfileAttributes",  # Tapir adds skins, edges and outlines
        "GetSurfaceAttributes",  # Tapir adds texture transforms and alpha settings
        "RenameNavigatorItem",  # Tapir also supports customName
        "GetNavigatorItemTree",  # Tapir adds source links and custom-name/ID flags
    },
    paginated_commands={
        "GetElementsByClassification": "elements",
        "GetAllPropertyIds": "propertyIds",
        "GetAllPropertyNames": "properties",
        "GetDetailsOfProperties": "propertyDefinitions",
        "GetPropertyValuesOfElementComponents": "propertyValuesForElementComponents",
    },
    image_lists={
        "GetProfileAttributePreview": "previewImages",
    },
)
