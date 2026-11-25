"""Reviewed command contracts for the pinned multiconn release.

A missing positional contract means correspondence is absent or unestablished.
Signatures cover the release description and transitive parameter/result models.
See the command-metadata skill for targeted updates.
"""

from tapir_archicad_mcp.metadata_types import CommandMetadata, MatrixAdapter, OutcomeList, Positional, Presentation

SIZE_BASED = Presentation.SIZE_BASED
HANDLE_PREFERRED = Presentation.HANDLE_PREFERRED

COMMAND_METADATA: dict[tuple[str, str], CommandMetadata] = {
    ("custom", "QueryElements"): CommandMetadata(
        HANDLE_PREFERRED, count_field="elements", reason="Returns matching IDs."
    ),
    ("custom", "ReadPropertyGrid"): CommandMetadata(
        SIZE_BASED,
        adapter=MatrixAdapter.READ,
        reason="Ordered element and property axes; incomplete positional references cannot supply an axis.",
    ),
    ("custom", "WritePropertyGrid"): CommandMetadata(
        HANDLE_PREFERRED,
        adapter=MatrixAdapter.WRITE,
        reason="A stored read grid keeps its axes; writes project only successful cells.",
    ),
    ("tapir", "ActivateDesignOptionsInCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="318a17017739f7b93ae5",
    ),
    ("tapir", "ActivateLayerCombination"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="d8ddde7a2f0183d49a43"
    ),
    ("tapir", "AddCommentToIssue"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="9b5f0660ca6d150574c4"
    ),
    ("tapir", "AddFilesToEmbeddedLibrary"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="29d8eb8ab38d5ac09bce",
    ),
    ("tapir", "AddLibraries"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="30fb6f4b1e1f34325937"
    ),
    ("tapir", "AddLoadCasesToLoadCombination"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="414bdce2fefd4f70822b",
    ),
    ("tapir", "AddMEPPreferenceTableRows"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="6f56e0daca9a2a68bdd4",
    ),
    ("tapir", "AddPropertyToAttributes"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="f60a576be92916bd8835"
    ),
    ("tapir", "AlignElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="4f3f533ecf650b54edb3",
    ),
    ("tapir", "ApplyFavoriteToToolDefault"): CommandMetadata(SIZE_BASED, reviewed="4cf3e2a1c979c5bbcd4a"),
    ("tapir", "ApplyFavoritesToElementDefaults"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="04f2b815c92a7f244633",
    ),
    ("tapir", "ApplyFavoritesToElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="d8b8aadbb28bd1a9a500",
    ),
    ("tapir", "AttachElementsToIssue"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="d0932431ad64de769c91"
    ),
    ("tapir", "BreakHotlinkNodes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="2775387a683c33fd0334",
    ),
    ("tapir", "CalculateSunPosition"): CommandMetadata(SIZE_BASED, reviewed="405d87bdc93f00e92d80"),
    ("tapir", "CanMoveElementsToDesignOptions"): CommandMetadata(SIZE_BASED, reviewed="df8e4ae0069e77cd605f"),
    ("tapir", "CaptureElementState"): CommandMetadata(SIZE_BASED, reviewed="e86c1583d8a450c76cbc"),
    ("tapir", "Change3DStyles"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="012e051b590cfffe999f",
    ),
    ("tapir", "ChangeAddOnViewpoints"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="d28c55681aa5b13ce093",
    ),
    ("tapir", "ChangeDrawingLink"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="18a72edc224228693a36",
    ),
    ("tapir", "ChangeFavorite"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="17da1b12aa37278bf466"
    ),
    ("tapir", "ChangeHotlinkInstances"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3d631cd72b945b128db2",
    ),
    ("tapir", "ChangeHotlinkNodes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="6112a6367dc86b0e771d",
    ),
    ("tapir", "ChangeLibraryPartOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c4ddf385e9cf5c65dd78",
    ),
    ("tapir", "ChangeSelectionOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(
            OutcomeList("executionResultsOfAddToSelection", ("FailedExecutionResult",)),
            OutcomeList("executionResultsOfRemoveFromSelection", ("FailedExecutionResult",)),
        ),
        reason="Separate additions and removals yield independent outcome lists.",
        reviewed="da1e132622969924e95e",
    ),
    ("tapir", "ChangeTextContent"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="aebde609206be887abf1",
    ),
    ("tapir", "ChangeWindow"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="3b9078f24268fe2af963"
    ),
    ("tapir", "CheckLibraries"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="0f9011fc61274eeb1e2f"
    ),
    ("tapir", "CheckMEPPortConnectability"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("results", ("ErrorItem",)),), reviewed="0cc0f556724cbfb1ea5d"
    ),
    ("tapir", "CheckPropertyValues"): CommandMetadata(
        SIZE_BASED, reason="Validation records can carry their own result details.", reviewed="b959dc1e0e980a49d3ab"
    ),
    ("tapir", "CloseWindows"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("windows", "executionResults", ("FailedExecutionResult",)),
        reviewed="025c863f49c0f493b86d",
    ),
    ("tapir", "CompareLibraryPartUnIds"): CommandMetadata(SIZE_BASED, reviewed="251b5fe275f675de6df8"),
    ("tapir", "ConnectMEPElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("connectionResults", ("ErrorItem",)),), reviewed="bd1eb4b5454a1050aa24"
    ),
    ("tapir", "ConnectToElectricalCircuits"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="7b7551051f5d7aaa4dde",
    ),
    ("tapir", "ConsolidateFills"): CommandMetadata(SIZE_BASED, reviewed="33af88038acea6c2fac9"),
    ("tapir", "ConsolidateLines"): CommandMetadata(SIZE_BASED, reviewed="3caff66a564d72b01d75"),
    ("tapir", "ConvertAnalyticalLinksToNonShortest"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("links", ("ErrorItem",)),), reviewed="a63440754f5050c72967"
    ),
    ("tapir", "ConvertImages"): CommandMetadata(
        SIZE_BASED, positional=Positional("images", "images", ("ErrorItem",)), reviewed="802f0211907a80b99f5f"
    ),
    ("tapir", "ConvertRevealOffsets"): CommandMetadata(
        SIZE_BASED, positional=Positional("openings", "revealOffsets", ("ErrorItem",)), reviewed="6a9150f72c7cfd954a54"
    ),
    ("tapir", "ConvertUnitValues"): CommandMetadata(
        SIZE_BASED, positional=Positional("values", "convertedValues", ("ErrorItem",)), reviewed="e3c72b7fdba47e3aa3aa"
    ),
    ("tapir", "CopyElements"): CommandMetadata(SIZE_BASED, reviewed="605d444b629ccfe3dde1"),
    ("tapir", "CopyElementsToDatabase"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="bd068dab5f020c2cb776",
    ),
    ("tapir", "CopyFilesIntoEmbeddedLibrary"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="958dbde8d2431d2a76c6"
    ),
    ("tapir", "CopyLibraryParts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="a69932818f33bdd2aa4f"
    ),
    ("tapir", "Create3DStyles"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="cc3465b24a0ab9c2bf68",
    ),
    ("tapir", "CreateAddOnViewpoints"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="viewpoints",
        outcome_lists=(OutcomeList("viewpoints", ("ErrorItem",)),),
        reviewed="e8423f1afb48bde2d820",
    ),
    ("tapir", "CreateAnalyticalLinks"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="8b07ee0c108df6f2ab9c",
    ),
    ("tapir", "CreateAnalyticalLoadCases"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="loadCaseIds",
        outcome_lists=(OutcomeList("loadCaseIds", ("ErrorItem",)),),
        reviewed="6b323e2bb2201d7d1ea3",
    ),
    ("tapir", "CreateAnalyticalLoadCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="loadCombinationIds",
        outcome_lists=(OutcomeList("loadCombinationIds", ("ErrorItem",)),),
        reviewed="257fb4b9c132c00e1eb4",
    ),
    ("tapir", "CreateAnalyticalLoadGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="loadGroupIds",
        outcome_lists=(OutcomeList("loadGroupIds", ("ErrorItem",)),),
        reviewed="7966899ce640b8a194a3",
    ),
    ("tapir", "CreateAnalyticalLoads"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="4c82937212e391a92d7b",
    ),
    ("tapir", "CreateAnalyticalSupports"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="4c9393e52386c46ef382",
    ),
    ("tapir", "CreateArcs"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="3e94b80788a20e0f77c6",
    ),
    ("tapir", "CreateAssociativeDimensions"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="021ccbfa25deb51d4aed",
    ),
    ("tapir", "CreateAssociativeDimensionsOnSection"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="b03f69a84066d93825bb",
    ),
    ("tapir", "CreateAttributeFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="ea51a42116f7c97473c3",
    ),
    ("tapir", "CreateBeams"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="52c169728ea8f2ed4924",
    ),
    ("tapir", "CreateBuildingMaterials"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="054b4d633e360fd81c9f",
    ),
    ("tapir", "CreateCircles"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="da0de4ecba8d7d257d28",
    ),
    ("tapir", "CreateClassificationItems"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(
            OutcomeList("classificationItemIds", ("ErrorItem",)),
            OutcomeList("executionResults", ("FailedExecutionResult",)),
        ),
        reviewed="c8074dba83d1a8a9cbdc",
    ),
    ("tapir", "CreateClassificationSystems"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(
            OutcomeList("classificationSystemIds", ("ErrorItem",)),
            OutcomeList("executionResults", ("FailedExecutionResult",)),
        ),
        reviewed="7e79c9a08e66423c0fca",
    ),
    ("tapir", "CreateColumns"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="2bda804ab493b8c51673",
    ),
    ("tapir", "CreateComposites"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="2a15c98dfc8d8d8c42c9",
    ),
    ("tapir", "CreateCurtainWalls"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="76e7d395850af32a320b",
    ),
    ("tapir", "CreateDesignOptionCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="designOptionCombinationIdsOrErrors",
        outcome_lists=(OutcomeList("designOptionCombinationIdsOrErrors", ("ErrorItem",)),),
        reviewed="a314f42d2b2ad642fe3f",
    ),
    ("tapir", "CreateDesignOptionSets"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f6daf46088c13f42486d",
    ),
    ("tapir", "CreateDesignOptions"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="designOptionIdsOrErrors",
        outcome_lists=(OutcomeList("designOptionIdsOrErrors", ("ErrorItem",)),),
        reviewed="360cad2d718a59dd822b",
    ),
    ("tapir", "CreateDetailMarkers"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="c634b2637000ee6dc22b",
    ),
    ("tapir", "CreateDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("databases", ("ErrorItem",)),), reviewed="1745ca61f6e34ba3567c"
    ),
    ("tapir", "CreateDoors"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="966f66efbf9be6c03430",
    ),
    ("tapir", "CreateDrawings"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="d4bf59c856fddce743ce",
    ),
    ("tapir", "CreateElectricalCircuits"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="dd6d347b765ec6774469",
    ),
    ("tapir", "CreateElectricalDevices"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="3760615109cb7a6f003c",
    ),
    ("tapir", "CreateElectricalPanels"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="fe0ce50d7256bc6ea00f",
    ),
    ("tapir", "CreateElementSets"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elementSets",
        outcome_lists=(OutcomeList("elementSets", ("ErrorItem",)),),
        reviewed="4a07cf14f2af990b891e",
    ),
    ("tapir", "CreateElementsFromAnalyticalMembers"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elements", ("ErrorItem",)),), reviewed="703fa5da2b59fb261ca2"
    ),
    ("tapir", "CreateElevations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="6291833dd4c56a979e48",
    ),
    ("tapir", "CreateFavorite"): CommandMetadata(SIZE_BASED, reviewed="d671ff1d3dd4e3bb7d9c"),
    ("tapir", "CreateFavoriteFolder"): CommandMetadata(SIZE_BASED, reviewed="e66ae4e2d0cbb3460cf1"),
    ("tapir", "CreateFavoritesFromElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a2d330658149de740346",
    ),
    ("tapir", "CreateFills"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="98b72a15bc4737952d5f",
    ),
    ("tapir", "CreateFolderInEmbeddedLibrary"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="f39f05e3be2975bbcf8b"
    ),
    ("tapir", "CreateGraphicOverrideCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="graphicOverrideCombinationIds",
        outcome_lists=(OutcomeList("graphicOverrideCombinationIds", ("ErrorItem",)),),
        reviewed="4ee8769f4348fae16f3d",
    ),
    ("tapir", "CreateGraphicOverrideRuleGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="161ab0ff3bb970dcc977",
    ),
    ("tapir", "CreateGraphicOverrideRules"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="graphicOverrideRuleIds",
        outcome_lists=(OutcomeList("graphicOverrideRuleIds", ("ErrorItem",)),),
        reviewed="09c126edadf50cd8051a",
    ),
    ("tapir", "CreateGridElements"): CommandMetadata(
        SIZE_BASED,
        summary_fields=("warnings",),
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="905e333b53653e43bd68",
    ),
    ("tapir", "CreateGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="groupGuids",
        outcome_lists=(OutcomeList("groupGuids", ("ErrorItem",)),),
        reviewed="cb1d02f00b4590d1dfff",
    ),
    ("tapir", "CreateHatches"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="223169c5042892139bf2",
    ),
    ("tapir", "CreateHotlinkInstances"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="2264b14ab060c0bd1e15",
    ),
    ("tapir", "CreateHotlinkNodes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("hotlinkNodes", ("ErrorItem",)),), reviewed="824c374e4e208ab47dd3"
    ),
    ("tapir", "CreateHotspots"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="85c6a531c1bcd84c21b3",
    ),
    ("tapir", "CreateInteriorElevations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="43d1da036ec85c6158ef",
    ),
    ("tapir", "CreateIssue"): CommandMetadata(SIZE_BASED, reviewed="b76fb78a11fae9e23c64"),
    ("tapir", "CreateKeynoteFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="keynoteFolderIdsOrErrors",
        outcome_lists=(OutcomeList("keynoteFolderIdsOrErrors", ("ErrorItem",)),),
        reviewed="f4e483cffb4d42b615f7",
    ),
    ("tapir", "CreateKeynoteItems"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="keynoteItemIdsOrErrors",
        outcome_lists=(OutcomeList("keynoteItemIdsOrErrors", ("ErrorItem",)),),
        reviewed="475d857425b01edb1734",
    ),
    ("tapir", "CreateKeynoteLabels"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="52c9d3cb40dc12c6e404",
    ),
    ("tapir", "CreateLabels"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="ddb186d39b3698902104",
    ),
    ("tapir", "CreateLamps"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="b3f36f49c4de79ec4954",
    ),
    ("tapir", "CreateLayerCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="7bb08f11fb821d118992",
    ),
    ("tapir", "CreateLayers"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="47ee3b0d568537a3b779",
    ),
    ("tapir", "CreateLayout"): CommandMetadata(
        SIZE_BASED, reason="A created layout can also contain a view placement error.", reviewed="b207ba2523510af2872e"
    ),
    ("tapir", "CreateLevelDimensions"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="4431bdd594985740eeee",
    ),
    ("tapir", "CreateLibraryPart"): CommandMetadata(SIZE_BASED, reviewed="13519663ac1f84842a85"),
    ("tapir", "CreateLibraryPartFromElements"): CommandMetadata(SIZE_BASED, reviewed="c153f5099d623db57f6d"),
    ("tapir", "CreateLibraryParts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="ad36ba9a0aa31b91c5b6"
    ),
    ("tapir", "CreateLineElements"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="d8bb98f364e6ea92f55a",
    ),
    ("tapir", "CreateLines"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="92a50dde84739ee4aeaa",
    ),
    ("tapir", "CreateMEPElements"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="146fb2052d717c1175c6",
    ),
    ("tapir", "CreateMEPFlexibleSegments"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="515bdb6addf040910b77",
    ),
    ("tapir", "CreateMEPPhysicalSystems"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="physicalSystems",
        outcome_lists=(OutcomeList("physicalSystems", ("ErrorItem",)),),
        reviewed="6b9eb2a6dca90048bc52",
    ),
    ("tapir", "CreateMEPPreferenceTables"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c8e80cdf6968fed4c248",
    ),
    ("tapir", "CreateMEPRoutingElements"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="94023663260ef566e5fd",
    ),
    ("tapir", "CreateMEPSystemGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="systemGroups",
        outcome_lists=(OutcomeList("systemGroups", ("ErrorItem",)),),
        reviewed="fd4f8da8a6f5dedb3d87",
    ),
    ("tapir", "CreateMEPSystems"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="cda9fe7381b5d44cbcdf",
    ),
    ("tapir", "CreateMEPTakeOffs"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="93cb4dd1dcfd4b69e93d",
    ),
    ("tapir", "CreateMeshes"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="6b09e50b181626cd0ef6",
    ),
    ("tapir", "CreateMorphs"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="54a37bd10aaa02b3dd0b",
    ),
    ("tapir", "CreateObjects"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="9ed740d355ac2ae82de2",
    ),
    ("tapir", "CreateOpenings"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="98d7b52ad1230f48f283",
    ),
    ("tapir", "CreatePenTables"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="c377285a4ec560b4d1cc",
    ),
    ("tapir", "CreatePolylines"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="9ecaac2e7dd8d9bf7167",
    ),
    ("tapir", "CreateProfiles"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="67516d2e0bc55647e9b8",
    ),
    ("tapir", "CreateProjectInfoFields"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("fields", ("ErrorItem",)),), reviewed="38f7703a40c6b7a5a593"
    ),
    ("tapir", "CreateProjectInfoGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="projectInfoGroupIdsOrErrors",
        outcome_lists=(OutcomeList("projectInfoGroupIdsOrErrors", ("ErrorItem",)),),
        reviewed="cbc4f28560a9458e4c6a",
    ),
    ("tapir", "CreatePropertyDefinitions"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="propertyIds",
        outcome_lists=(OutcomeList("propertyIds", ("ErrorItem",)),),
        reviewed="a2533f8c75ed05b66c94",
    ),
    ("tapir", "CreatePropertyGroups"): CommandMetadata(
        HANDLE_PREFERRED, count_field="propertyGroupIds", reviewed="1c2e3abd1cb677756d12"
    ),
    ("tapir", "CreateRailings"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="f23930b3aee4780ef3c0",
    ),
    ("tapir", "CreateRailingsFromPolyline"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="686c047ed063a6709b53",
    ),
    ("tapir", "CreateRoofs"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="0ed7faef2d1f279844ba",
    ),
    ("tapir", "CreateSections"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="bcf46235bbda8d1153e8",
    ),
    ("tapir", "CreateShells"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="b45ca7a0b47ee9e28871",
    ),
    ("tapir", "CreateSkylights"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="1df3344d17724dd2b940",
    ),
    ("tapir", "CreateSlabs"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="f69914b108bd94683be2",
    ),
    ("tapir", "CreateSolidElementLinks"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="403c9304b77df9915e26",
    ),
    ("tapir", "CreateSolidOperations"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("results", ("ErrorItem",)),), reviewed="76b9e52ccc7c85fb2b60"
    ),
    ("tapir", "CreateSplines"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="00bdbb5d08583bdce4d9",
    ),
    ("tapir", "CreateStairs"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="86d4d092e51c7248851d",
    ),
    ("tapir", "CreateSurfaces"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="f89f7fd269234200f525",
    ),
    ("tapir", "CreateTexts"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="5f3148e7a85ed0842701",
    ),
    ("tapir", "CreateViewsInViewMap"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="navigatorItems",
        outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),),
        reviewed="5ac3b0d00406265b35fe",
    ),
    ("tapir", "CreateWallThicknessDimensions"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="7a23646ab90151ba5a3a",
    ),
    ("tapir", "CreateWalls"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="61b85250e1f8e0c9aeed",
    ),
    ("tapir", "CreateWindows"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="1f20474bdd09d8cabecd",
    ),
    ("tapir", "CreateWorksheetMarkers"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="261996458b8ba555dc52",
    ),
    ("tapir", "CreateWorksheets"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("databases", ("ErrorItem",)),), reviewed="290e900f57e8b3725f67"
    ),
    ("tapir", "CreateZoneCategories"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="attributeIds",
        outcome_lists=(OutcomeList("attributeIds", ("ErrorItem",)),),
        reviewed="a91fa3e4faf555d97fda",
    ),
    ("tapir", "CreateZones"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="8871850a916b7dcfeffc",
    ),
    ("tapir", "DeactivateDesignOptionsInCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="402fed3bd273fa175380",
    ),
    ("tapir", "DeleteAnalyticalLoadCases"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="83b67d3eac46ccddda09",
    ),
    ("tapir", "DeleteAnalyticalLoadCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="6a723fb7b5b06b47a21e",
    ),
    ("tapir", "DeleteAnalyticalLoadGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f61641ee474f14b9c519",
    ),
    ("tapir", "DeleteAndReplaceAttributes"): CommandMetadata(
        SIZE_BASED,
        summary_fields=("dryRun",),
        outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),),
        reviewed="257e1e960e133ecf57c9",
    ),
    ("tapir", "DeleteAttributeFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="5a203a76f80cf5f70c85",
    ),
    ("tapir", "DeleteAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("attributesToDelete", "executionResults", ("FailedExecutionResult",)),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="744d69b4bb9b19a460f2",
    ),
    ("tapir", "DeleteClassificationItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="5f33d5a117bb2a80f0f6",
    ),
    ("tapir", "DeleteClassificationSystems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="738609b1022df7d613b7",
    ),
    ("tapir", "DeleteDesignOptionCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0d14b86d708a29f3bd6e",
    ),
    ("tapir", "DeleteDesignOptionSets"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="b6500801060e417c338e",
    ),
    ("tapir", "DeleteDesignOptions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="4bbffbd49b5a79836e25",
    ),
    ("tapir", "DeleteElectricalCircuits"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="95c99d132826629b27c0",
    ),
    ("tapir", "DeleteElementSets"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="362e9bbdccf128724bec",
    ),
    ("tapir", "DeleteElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reason="Deletion runs zones first. Item outcomes are exposed, with no reliance on execution order.",
        reviewed="da61d6eaea4e4fd016c8",
    ),
    ("tapir", "DeleteEmbeddedLibraryItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="9b5fec27444bec2fe792",
    ),
    ("tapir", "DeleteFavoriteFolder"): CommandMetadata(SIZE_BASED, reviewed="9bc61c6d3428032cf36d"),
    ("tapir", "DeleteFavorites"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="20ce8ed8d55559328c3e",
    ),
    ("tapir", "DeleteFavoritesWithManager"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0bc6a1781c6c831cd937",
    ),
    ("tapir", "DeleteGhostRecords"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f151284b28210bda4a09",
    ),
    ("tapir", "DeleteGraphicOverrideCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="25ad48bcb36eb70d9003",
    ),
    ("tapir", "DeleteGraphicOverrideRuleGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="4ecbfc2854cc490d0500",
    ),
    ("tapir", "DeleteGraphicOverrideRules"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="4eb53ec3190e93045f14",
    ),
    ("tapir", "DeleteHotlinkNodes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="df94c45816d7488643b1",
    ),
    ("tapir", "DeleteIssue"): CommandMetadata(SIZE_BASED, summary_fields=("dryRun",), reviewed="5e21ca1e813f2f6664fc"),
    ("tapir", "DeleteKeynoteFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="7b7c5d9ab82d011f494f",
    ),
    ("tapir", "DeleteKeynoteItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="9341cff7e4986586118b",
    ),
    ("tapir", "DeleteMEPPhysicalSystems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a0463a36b45d02e885d6",
    ),
    ("tapir", "DeleteMEPPreferenceTableRows"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="7eb11c4573292cf31f09",
    ),
    ("tapir", "DeleteModulData"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="6c3c94342ca2dcbdc864",
    ),
    ("tapir", "DeleteNavigatorItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="47a958d5f1a6b82ef3d9",
    ),
    ("tapir", "DeleteProjectData"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f157d402b072363e4de9",
    ),
    ("tapir", "DeleteProjectInfoFields"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="299348b578c71e486d63",
    ),
    ("tapir", "DeleteProjectInfoGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="58426712142dba4a5585",
    ),
    ("tapir", "DeletePropertyDefinitions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="db9b7cb7b0c2693b9c96",
    ),
    ("tapir", "DeletePropertyGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="4a9f4afa4f3e9f845543",
    ),
    ("tapir", "DeleteSelectedElements"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        summary_fields=("dryRun", "success", "error", "wouldDelete"),
        inline_if_true="dryRun",
        reviewed="11f2d1a44612515161d3",
    ),
    ("tapir", "DeleteUserDataOfAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="e313a59bc05197861c68",
    ),
    ("tapir", "DeleteUserDataOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("elements", "executionResults", ("FailedExecutionResult",)),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="efbe4f10c1a3bd94c75a",
    ),
    ("tapir", "DeselectAll"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="65a0766daf4bf48a2291"
    ),
    ("tapir", "DetachElementsFromIssue"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="235b48be234a01e4067a"
    ),
    ("tapir", "DistributeElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="db904f4f7cf73d239812",
    ),
    ("tapir", "DuplicateDesignOptionCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="designOptionCombinationIdsOrErrors",
        outcome_lists=(OutcomeList("designOptionCombinationIdsOrErrors", ("ErrorItem",)),),
        reviewed="26ee3e139ade370fa18b",
    ),
    ("tapir", "EditHierarchicalElement"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="b3b098329c35ef0a7cc8"
    ),
    ("tapir", "ElevateElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="71603d4154b2f4015dd0",
    ),
    ("tapir", "ExportFavorites"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="e4ff16b1122338da61c2"
    ),
    ("tapir", "ExportIssuesToBCF"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="fc6cfe4a1054fcdfa757"
    ),
    ("tapir", "FilterElements"): CommandMetadata(
        HANDLE_PREFERRED, count_field="elements", reason="Returns a matching subset.", reviewed="865c1f6d16baf27f585a"
    ),
    ("tapir", "FindDimensionStandard"): CommandMetadata(SIZE_BASED, reviewed="6e246370d4759add5fc8"),
    ("tapir", "FindLibraryParts"): CommandMetadata(SIZE_BASED, reviewed="5599a144ee3a622fc9a7"),
    ("tapir", "FindModelViewOption"): CommandMetadata(SIZE_BASED, reviewed="988fa62ddc5aba946d78"),
    ("tapir", "FinishHierarchicalEditing"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="98daf153739b43a60eca"
    ),
    ("tapir", "FitInWindow"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="818ef59149d0a568b194"
    ),
    ("tapir", "Get2DBoundingBoxes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("boundingBoxes2D", ("ErrorItem",)),), reviewed="bb6a091efa7810ec2d16"
    ),
    ("tapir", "Get3DBoundingBoxes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("boundingBoxes3D", ("ErrorItem",)),), reviewed="8abe976287429189bb4a"
    ),
    ("tapir", "Get3DCutPlanes"): CommandMetadata(SIZE_BASED, reviewed="730cc59d1d8f7a4b8a7b"),
    ("tapir", "Get3DCutawayStatus"): CommandMetadata(SIZE_BASED, reviewed="8fa8b88ded671fffa582"),
    ("tapir", "Get3DDocumentSettings"): CommandMetadata(SIZE_BASED, reviewed="c8771ce4a41be24f7c84"),
    ("tapir", "Get3DFilterAndCutSettings"): CommandMetadata(SIZE_BASED, reviewed="7bfb517299ae9e7cbd20"),
    ("tapir", "Get3DGeometryOfElements"): CommandMetadata(
        SIZE_BASED, positional=Positional("elements", "geometries3D", ("ErrorItem",)), reviewed="fa4fe1bb42773fb35033"
    ),
    ("tapir", "Get3DModelCounts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("counts", ("ErrorItem",)),), reviewed="e1879be2606f7d9e8711"
    ),
    ("tapir", "Get3DProjectionSettings"): CommandMetadata(SIZE_BASED, reviewed="96f8d8ddf9cdcacf1239"),
    ("tapir", "Get3DStyleDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("styles", ("ErrorItem",)),), reviewed="94124dc58e79c21ba337"
    ),
    ("tapir", "Get3DStyles"): CommandMetadata(SIZE_BASED, reviewed="7a855817eb68f41d2f20"),
    ("tapir", "Get3DWindowSettings"): CommandMetadata(SIZE_BASED, reviewed="8abb5c2b86b15e1af7f7"),
    ("tapir", "GetActiveGraphicalOverrideCombination"): CommandMetadata(SIZE_BASED, reviewed="385d28362eab0f2faf90"),
    ("tapir", "GetAddOnVersion"): CommandMetadata(SIZE_BASED, reviewed="d185d4da744ecb4effed"),
    ("tapir", "GetAddOnViewpointChildren"): CommandMetadata(
        HANDLE_PREFERRED, count_field="viewpointIds", reviewed="3540acadf5020d4f87f1"
    ),
    ("tapir", "GetAddOnViewpointRoots"): CommandMetadata(
        HANDLE_PREFERRED, count_field="viewpointIds", reviewed="9e08fe47bfc93d874b5c"
    ),
    ("tapir", "GetAddOnViewpoints"): CommandMetadata(
        SIZE_BASED, positional=Positional("viewpointIds", "viewpoints", ("ErrorItem",)), reviewed="ba5bca5e7ef51a3c8a98"
    ),
    ("tapir", "GetAllAutoTextKeys"): CommandMetadata(SIZE_BASED, reviewed="2675ef341d4f5fd8ddfd"),
    ("tapir", "GetAllElements"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("executionResultForDatabases", ("FailedExecutionResult",), unit="database"),),
        summary_fields=("error",),
        reviewed="30e684acf4f456bc3ba3",
    ),
    ("tapir", "GetAllElementsOfGroups"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementsOfGroups", ("ErrorItem",)),), reviewed="94fdb02043ac9faa4989"
    ),
    ("tapir", "GetAllFavorites"): CommandMetadata(SIZE_BASED, reviewed="f9a68a131866da9a4d98"),
    ("tapir", "GetAllProperties"): CommandMetadata(SIZE_BASED, reviewed="8eb44d5fab6e35a94acb"),
    ("tapir", "GetAnalyticalLinks"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("links", ("ErrorItem",)),), reviewed="10e4324be3587fc21ed5"
    ),
    ("tapir", "GetAnalyticalLoadCases"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("loadCases", ("ErrorItem",)),), reviewed="4fd0f151c9f34ea6cba7"
    ),
    ("tapir", "GetAnalyticalLoadCombinations"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("loadCombinations", ("ErrorItem",)),), reviewed="9baa3a26a3897fe73211"
    ),
    ("tapir", "GetAnalyticalLoadGroups"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("loadGroups", ("ErrorItem",)),), reviewed="1ade6244c14f03c788c4"
    ),
    ("tapir", "GetAnalyticalLoads"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("loads", ("ErrorItem",)),), reviewed="02560f61d8801f09a769"
    ),
    ("tapir", "GetAnalyticalMemberDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("analyticalMembers", ("ErrorItem",)),), reviewed="823e2abc1a5da0bbc523"
    ),
    ("tapir", "GetAnalyticalMemberPartGeometries"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("geometries", ("ErrorItem",)),), reviewed="99052c340d0a46932eb8"
    ),
    ("tapir", "GetAnalyticalMemberTypesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("memberTypesOfElements", ("ErrorItem",)),),
        reviewed="278ace2801d5ebf34f8a",
    ),
    ("tapir", "GetAnalyticalMembers"): CommandMetadata(SIZE_BASED, reviewed="ee9b44f9758946db5e38"),
    ("tapir", "GetAnalyticalModel"): CommandMetadata(SIZE_BASED, reviewed="43daf0b77532fcdae9f7"),
    ("tapir", "GetAnalyticalModelCheckTypeId"): CommandMetadata(SIZE_BASED, reviewed="0d0393ec2924036ce3f5"),
    ("tapir", "GetAnalyticalModelVariation"): CommandMetadata(SIZE_BASED, reviewed="f2f4829385816560f424"),
    ("tapir", "GetAnalyticalReleases"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("releases", ("ErrorItem",)),), reviewed="491c1f41b4e4028e120b"
    ),
    ("tapir", "GetAnalyticalSupports"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("supports", ("ErrorItem",)),), reviewed="903f0d5a59cf6748c292"
    ),
    ("tapir", "GetAnalyticalVisibilitySettings"): CommandMetadata(SIZE_BASED, reviewed="2a6b9da54b93befc11bc"),
    ("tapir", "GetArcFromUser"): CommandMetadata(SIZE_BASED, reviewed="79ad84ecb6b38b64c2fa"),
    ("tapir", "GetArchicadLicenseInfo"): CommandMetadata(SIZE_BASED, reviewed="0710b6f007965eabbd6a"),
    ("tapir", "GetArchicadLocation"): CommandMetadata(SIZE_BASED, reviewed="08281faa68b278ae36ce"),
    ("tapir", "GetArchicadReleaseInfo"): CommandMetadata(SIZE_BASED, reviewed="74e215c4234dc12839c6"),
    ("tapir", "GetArchicadVisibility"): CommandMetadata(SIZE_BASED, reviewed="4a2ffdd85ae771d8236a"),
    ("tapir", "GetAttributeIndexes"): CommandMetadata(SIZE_BASED, reviewed="ca7b4d152809f1f2f6d5"),
    ("tapir", "GetAttributesByType"): CommandMetadata(SIZE_BASED, reviewed="f590fd34abdc611bd729"),
    ("tapir", "GetAttributesFromProject"): CommandMetadata(SIZE_BASED, reviewed="83782fb1aca058384afb"),
    ("tapir", "GetAutoGroupMode"): CommandMetadata(SIZE_BASED, reviewed="1a32d2ceeb2ef3e75230"),
    ("tapir", "GetAutoIntersect"): CommandMetadata(SIZE_BASED, reviewed="68dc1c029a7f8f20cc40"),
    ("tapir", "GetAutoTextKeys"): CommandMetadata(SIZE_BASED, reviewed="6c7e240fee822d9f36f2"),
    ("tapir", "GetAutoTextName"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("autoTextNames", ("ErrorItem",)),), reviewed="a65d5af922a197096e43"
    ),
    ("tapir", "GetAvailableLibraryParts"): CommandMetadata(SIZE_BASED, reviewed="e794d8eb09cfbf60f529"),
    ("tapir", "GetBodyMaterialsOfElements"): CommandMetadata(
        SIZE_BASED, positional=Positional("elements", "bodyMaterials", ("ErrorItem",)), reviewed="2f5fe3e12929b3c77e9f"
    ),
    ("tapir", "GetBuildingMaterialPhysicalProperties"): CommandMetadata(SIZE_BASED, reviewed="2abdab4eb205c73243c2"),
    ("tapir", "GetBuildingMaterials"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("buildingMaterials", ("ErrorItem",)),), reviewed="9a7ea308f57e6beb53a3"
    ),
    ("tapir", "GetCalculatedParametersOfCurtainWallSubElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("calculatedParametersOfElements", ("ErrorItem",)),),
        reviewed="c1e402e08af148fac06b",
    ),
    ("tapir", "GetCalculationUnits"): CommandMetadata(SIZE_BASED, reviewed="479949bf332e7c54e0b8"),
    ("tapir", "GetCameras"): CommandMetadata(SIZE_BASED, reviewed="e95b0947f44a1f08bebd"),
    ("tapir", "GetCategoryValuesOfDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("categoryValuesOfDefaults", ("ErrorItem",)),),
        reviewed="3d83a9ee7afa0c59d49e",
    ),
    ("tapir", "GetCategoryValuesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("categoryValuesOfElements", ("ErrorItem",)),),
        reviewed="f204acd81d12bae76013",
    ),
    ("tapir", "GetClassificationItemParents"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("classificationItemIds", "classificationItemParents", ("ErrorItem",)),
        reviewed="4d95a6b0575b93319290",
    ),
    ("tapir", "GetClassificationItemVisibility"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("classificationItemVisibilities", ("ErrorItem",)),),
        reviewed="8ca44cd2422fb6420723",
    ),
    ("tapir", "GetClassificationsOfAttributes"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("attributeClassifications", ("ErrorItem",)),),
        reviewed="10110f098ef78432f70d",
    ),
    ("tapir", "GetClassificationsOfElementDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementDefaultClassifications", ("ErrorItem",)),),
        reviewed="0f1aeb50a89a2548af49",
    ),
    ("tapir", "GetClassificationsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "elementClassifications", ("ErrorItem",)),
        reason="Classification systems form an independent column axis.",
        reviewed="c1e0edf05373c772effe",
    ),
    ("tapir", "GetClassificationsOfToolDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("classificationsOfToolDefaults", ("ErrorItem",)),),
        reviewed="73d6ca6c27048b9e9420",
    ),
    ("tapir", "GetCollisions"): CommandMetadata(SIZE_BASED, reviewed="ad01f2ebee4cac803d99"),
    ("tapir", "GetCommentsFromIssue"): CommandMetadata(SIZE_BASED, reviewed="3ff670c4960635a32b2d"),
    ("tapir", "GetConnectedElements"): CommandMetadata(SIZE_BASED, reviewed="9f0ac193a2d29bf350ef"),
    ("tapir", "GetContainingDatabases"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("databases", ("ErrorItem",)),), reviewed="c809c4aeb76d0db60268"
    ),
    ("tapir", "GetCoordinateOrigins"): CommandMetadata(SIZE_BASED, reviewed="a305941d483f885351be"),
    ("tapir", "GetCurrentAnalyticalModel"): CommandMetadata(SIZE_BASED, reviewed="a528cbe074e1c0e2cb20"),
    ("tapir", "GetCurrentLayerCombination"): CommandMetadata(SIZE_BASED, reviewed="d84b80d8bb343be85df2"),
    ("tapir", "GetCurrentPenTable"): CommandMetadata(SIZE_BASED, reviewed="99a69ef09af564d48212"),
    ("tapir", "GetCurrentRevisionChangesOfLayouts"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("currentRevisionChangesOfLayouts", ("ErrorItem",)),),
        reviewed="903b435542a2a1e17b73",
    ),
    ("tapir", "GetCurrentTool"): CommandMetadata(SIZE_BASED, reviewed="493cd857ff93daa81a10"),
    ("tapir", "GetCurrentViewImage"): CommandMetadata(SIZE_BASED, reviewed="398acebdacdc4cce9aad"),
    ("tapir", "GetCurrentWindowDrawingScale"): CommandMetadata(SIZE_BASED, reviewed="f3b57a1e2c4d002e3415"),
    ("tapir", "GetCurrentWindowType"): CommandMetadata(SIZE_BASED, reviewed="bc35b5f49561ddb8ba85"),
    ("tapir", "GetCurtainWallAbsoluteBottoms"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "absoluteBottoms", ("ErrorItem",)),
        reviewed="f149acf08c27ac4c98f8",
    ),
    ("tapir", "GetCustomCurveMemberStretch"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("stretches", ("ErrorItem",)),), reviewed="826292034b175e316cdd"
    ),
    ("tapir", "GetCutPolygonsOfElements"): CommandMetadata(
        SIZE_BASED, positional=Positional("elements", "cutPolygons", ("ErrorItem",)), reviewed="77a1dfe36c0462a28c59"
    ),
    ("tapir", "GetDatabaseIdFromNavigatorItemId"): CommandMetadata(
        HANDLE_PREFERRED, count_field="databases", reviewed="4687ca8960ab57a21d0b"
    ),
    ("tapir", "GetDatabases"): CommandMetadata(SIZE_BASED, reviewed="6edf2bf0e9cffbbbfd73"),
    ("tapir", "GetDescriptorsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "descriptorsOfElements", ("ErrorItem",)),
        reviewed="380c324daeaf13404916",
    ),
    ("tapir", "GetDesignOptionCombinationOfViews"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("designOptionCombinationOfViews", ("ErrorItem",)),),
        reviewed="9ed1968ffa905358545f",
    ),
    ("tapir", "GetDesignOptionCombinations"): CommandMetadata(SIZE_BASED, reviewed="65dc22ff5a0c907e6388"),
    ("tapir", "GetDesignOptionForElements"): CommandMetadata(SIZE_BASED, reviewed="4baf40b10283226e540a"),
    ("tapir", "GetDesignOptionSets"): CommandMetadata(SIZE_BASED, reviewed="d7140c3f4421f9536522"),
    ("tapir", "GetDesignOptions"): CommandMetadata(SIZE_BASED, reviewed="ffe3dde0dc22dd4200b9"),
    ("tapir", "GetDetailsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional(
            "elements",
            "detailsOfElements",
            ("ErrorItem",),
            output_identity_fields=("elementId",),
            partial_output_types=("DetailsOfElement",),
        ),
        reason="The pinned client documents ordered errors with supplied elements; omitted elements search the project.",
        reviewed="541192eef0cbc4b993fd",
    ),
    ("tapir", "GetDialogAutoClose"): CommandMetadata(SIZE_BASED, reviewed="b0f619c64a805104e6e1"),
    ("tapir", "GetDimensionData"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("dimensionsData", ("ErrorItem",)),), reviewed="fee31ac63c88528a8a3a"
    ),
    ("tapir", "GetDimensionStandards"): CommandMetadata(SIZE_BASED, reviewed="1b1cff71f54a46cec452"),
    ("tapir", "GetDocumentFrom3DDefaults"): CommandMetadata(SIZE_BASED, reviewed="5a860b7fd15caf498a89"),
    ("tapir", "GetDocumentRevisions"): CommandMetadata(SIZE_BASED, reviewed="52f1a44e3ebfad0a96d1"),
    ("tapir", "GetDrawingContentBoxes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("contentBoxes", ("ErrorItem",)),), reviewed="2cc5a8c921592c89c3ad"
    ),
    ("tapir", "GetDrawingNumberingGridLines"): CommandMetadata(SIZE_BASED, reviewed="cb0931a40aecc6d5c1de"),
    ("tapir", "GetDrawingPrimitivesOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "drawingPrimitivesOfElements", ("ErrorItem",)),
        reviewed="954b53a5fd717d8d31d8",
    ),
    ("tapir", "GetEditModeState"): CommandMetadata(SIZE_BASED, reviewed="83a4836a1c6f677d458c"),
    ("tapir", "GetElectricalCircuits"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("electricalCircuits", ("ErrorItem",)),), reviewed="14f714dc71bbb1e752c9"
    ),
    ("tapir", "GetElectricalDevices"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("electricalDevices", ("ErrorItem",)),), reviewed="53c1a6814f050134812b"
    ),
    ("tapir", "GetElectricalPanels"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("electricalPanels", ("ErrorItem",)),), reviewed="c67ad70e3284dcd54d81"
    ),
    ("tapir", "GetElectricalProjectSettings"): CommandMetadata(SIZE_BASED, reviewed="d645dc1bae598a886378"),
    ("tapir", "GetElementAtCoordinate"): CommandMetadata(SIZE_BASED, reviewed="7038c5d93d808d9b3332"),
    ("tapir", "GetElementCategories"): CommandMetadata(SIZE_BASED, reviewed="940a4952aa649690635b"),
    ("tapir", "GetElementChangesSince"): CommandMetadata(SIZE_BASED, reviewed="f39163acfc1924a98cb1"),
    ("tapir", "GetElementConnections"): CommandMetadata(
        SIZE_BASED,
        positional=Positional(
            "elements", "executionResults", ("FailedExecutionResult",), empty_outputs=("connections",)
        ),
        reason="Execution results align to elements; connections are an independent set of element pairs.",
        reviewed="6bf96fb0c403dee7a4bd",
    ),
    ("tapir", "GetElementFromUser"): CommandMetadata(SIZE_BASED, reviewed="8b62587ef5286d12da06"),
    ("tapir", "GetElementPreviewImage"): CommandMetadata(SIZE_BASED, reviewed="88a079f65264ee90e7f8"),
    ("tapir", "GetElementSetData"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementSets", ("ErrorItem",)),), reviewed="55006f5146792e505777"
    ),
    ("tapir", "GetElementSetsOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementSetsOfElements", ("ErrorItem",)),),
        reviewed="7b7d90af7b0861a5838c",
    ),
    ("tapir", "GetElementTrims"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementTrims", ("ErrorItem",)),), reviewed="3cccb5d24145a0cebe4d"
    ),
    ("tapir", "GetElementTypeNames"): CommandMetadata(
        SIZE_BASED, positional=Positional("elementTypes", "names", ("ErrorItem",)), reviewed="8b631cd66b464e64fb80"
    ),
    ("tapir", "GetElementUserData"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementUserData", ("ErrorItem",)),), reviewed="067694d815d3647a34ce"
    ),
    ("tapir", "GetElementsAttachedToIssue"): CommandMetadata(
        HANDLE_PREFERRED, count_field="elements", reviewed="063948abea90db196c42"
    ),
    ("tapir", "GetElementsByCriteria"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        summary_fields=("count",),
        handle_if_list="elements",
        reason="The count-only response is informative inline.",
        reviewed="37e239ce6a0dff60bb5e",
    ),
    ("tapir", "GetElementsByIFCIds"): CommandMetadata(
        SIZE_BASED,
        count_field="elementsByIFCIds",
        reason="An IFC identifier can map to a collection of elements.",
        reviewed="c4b5646faebad59997f8",
    ),
    ("tapir", "GetElementsInCreationOrder"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("executionResultForDatabases", ("FailedExecutionResult",), unit="database"),),
        summary_fields=("error",),
        reason="Archicad determines the returned order.",
        reviewed="4c560b1d9ff45193f9fe",
    ),
    ("tapir", "GetElementsInDrawOrder"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("executionResultForDatabases", ("FailedExecutionResult",), unit="database"),),
        summary_fields=("error",),
        reason="Archicad determines the returned order.",
        reviewed="11658316cefb00fa447e",
    ),
    ("tapir", "GetElementsOfDesignOptions"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementsOfDesignOptions", ("ErrorItem",)),),
        reviewed="c4f1004c219c80722240",
    ),
    ("tapir", "GetElementsOfGroups"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementsOfGroups", ("ErrorItem",)),), reviewed="3577d7d9fe5bff0cdc41"
    ),
    ("tapir", "GetExportTolerance"): CommandMetadata(SIZE_BASED, reviewed="bc83884034244106fc86"),
    ("tapir", "GetFavoriteContents"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("favorites", ("ErrorItem",)),), reviewed="c671bbfc9b0daf28c7ac"
    ),
    ("tapir", "GetFavoriteDefaults"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("favoriteDefaults", ("ErrorItem",)),), reviewed="bab783cb4e2232b07b83"
    ),
    ("tapir", "GetFavoriteDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("favoriteDetails", ("ErrorItem",)),), reviewed="70db0eee080ef1d9e12b"
    ),
    ("tapir", "GetFavoriteFolders"): CommandMetadata(SIZE_BASED, reviewed="3b2b95d974f0cda19c05"),
    ("tapir", "GetFavoritePreviewImage"): CommandMetadata(SIZE_BASED, reviewed="ef082fd2603a820f4d8b"),
    ("tapir", "GetFavoriteSettings"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("favoriteSettings", ("ErrorItem",)),), reviewed="df1cc06c1a9c7e7a2bbd"
    ),
    ("tapir", "GetFavoritesByType"): CommandMetadata(SIZE_BASED, reviewed="c7da8d8d59151cd0bc15"),
    ("tapir", "GetFills"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("fills", ("ErrorItem",)),), reviewed="63037c47797a338c0fb0"
    ),
    ("tapir", "GetFontsByName"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("fonts", ("ErrorItem",)),), reviewed="84be7c592c135cc0ad34"
    ),
    ("tapir", "GetGDLDate"): CommandMetadata(SIZE_BASED, reviewed="258f65c5b34bfcaf2ec7"),
    ("tapir", "GetGDLParametersOfElements"): CommandMetadata(SIZE_BASED, reviewed="f5e3b39e7a2e6fdc3611"),
    ("tapir", "GetGDLParametersOfLibraryParts"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("gdlParametersOfLibraryParts", ("ErrorItem",)),),
        reviewed="228e4be62e221f0bef74",
    ),
    ("tapir", "GetGDLUserGlobals"): CommandMetadata(SIZE_BASED, reviewed="431903ec5b93a091f303"),
    ("tapir", "GetGeoLocation"): CommandMetadata(SIZE_BASED, reviewed="251e44d722d70009980a"),
    ("tapir", "GetGhostStorySettings"): CommandMetadata(SIZE_BASED, reviewed="b2ef26d0620505c3efd1"),
    ("tapir", "GetGraphicOverrideCombinations"): CommandMetadata(SIZE_BASED, reviewed="d18b073875c08e2c963e"),
    ("tapir", "GetGraphicOverrideRuleGroups"): CommandMetadata(SIZE_BASED, reviewed="726780f6766483975b50"),
    ("tapir", "GetGraphicOverrideRules"): CommandMetadata(SIZE_BASED, reviewed="8aa066fd75c99913dd00"),
    ("tapir", "GetGraphicOverrideRulesByName"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("graphicOverrideRules", ("ErrorItem",)),),
        reviewed="af3ede53a96e1c750276",
    ),
    ("tapir", "GetGraphicalOverrideStyleOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("styles", ("ErrorItem",)),), reviewed="12902d16e39f71d3a652"
    ),
    ("tapir", "GetGridElementDefaults"): CommandMetadata(SIZE_BASED, reviewed="9a5f99170154165af11f"),
    ("tapir", "GetGridElements"): CommandMetadata(SIZE_BASED, reviewed="2bde027e030b88f1c8db"),
    ("tapir", "GetGridSettings"): CommandMetadata(SIZE_BASED, reviewed="3b5284dec94ab832437a"),
    ("tapir", "GetGroupsOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="groupGuids",
        outcome_lists=(OutcomeList("groupGuids", ("ErrorItem",)),),
        reviewed="f7c93351a92c1fdb308f",
    ),
    ("tapir", "GetHierarchicalElementOwners"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("owners", ("ErrorItem",)),), reviewed="8b2ad72aab3224147eaf"
    ),
    ("tapir", "GetHotlinkDesignOptionTableDetails"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("hotlinkDesignOptionTables", ("ErrorItem",)),),
        reviewed="7ffa4de7676b1745585b",
    ),
    ("tapir", "GetHotlinkDesignOptionTables"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("hotlinkDesignOptionTables", ("ErrorItem",)),),
        reviewed="089869e6ef275b19af55",
    ),
    ("tapir", "GetHotlinkOwnersOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("hotlinkOwners", ("ErrorItem",)),), reviewed="be9dfc5a241e697ffc45"
    ),
    ("tapir", "GetHotlinkProxyElementTable"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("proxyElementTables", ("ErrorItem",)),), reviewed="0cc14f8ecc0c17b108ad"
    ),
    ("tapir", "GetHotlinkSourceStatus"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("hotlinkSourceStatuses", ("ErrorItem",)),),
        reviewed="3b08f640b915827d6644",
    ),
    ("tapir", "GetHotlinks"): CommandMetadata(SIZE_BASED, reviewed="2b852b3c296cb8bd13b6"),
    ("tapir", "GetHotspotsOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("hotspotsOfElements", ("ErrorItem",)),), reviewed="9ea8ea3505fd8cde2d56"
    ),
    ("tapir", "GetIFCAssignments"): CommandMetadata(SIZE_BASED, reviewed="4fdccb52a00357eda707"),
    ("tapir", "GetIFCAttributesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementIFCAttributes", ("ErrorItem",)),),
        reviewed="49cd5584292b25d16dda",
    ),
    ("tapir", "GetIFCClassificationReferencesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementIFCClassificationReferences", ("ErrorItem",)),),
        reviewed="413c89bf9c799f19f622",
    ),
    ("tapir", "GetIFCExportTranslators"): CommandMetadata(SIZE_BASED, reviewed="756fd3f76a2ec463a44a"),
    ("tapir", "GetIFCIdsOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementIFCIds", ("ErrorItem",)),), reviewed="4b3403c5d0a4e55fc5ec"
    ),
    ("tapir", "GetIFCPropertiesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementIFCProperties", ("ErrorItem",)),),
        reviewed="f6db0c4cadb6bcd9f16d",
    ),
    ("tapir", "GetIFCSpatialStructure"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elements", ("ErrorItem",)),), reviewed="dc4ed847bf8884b3256c"
    ),
    ("tapir", "GetIFCTypeOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementIFCTypes", ("ErrorItem",)),), reviewed="783f3195d49143d91b14"
    ),
    ("tapir", "GetIssues"): CommandMetadata(SIZE_BASED, reviewed="5ebe35957344bbc91300"),
    ("tapir", "GetKeynoteAutoTexts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("autoTexts", ("ErrorItem",)),), reviewed="ea3f2998131d86ef39ce"
    ),
    ("tapir", "GetKeynoteTree"): CommandMetadata(SIZE_BASED, reviewed="bae048623730768ae542"),
    ("tapir", "GetLCSOfAnalyticalMembers"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("localCoordinateSystems", ("ErrorItem",)),),
        reviewed="a9724b63e397363ab9f1",
    ),
    ("tapir", "GetLast3DDefaultLevels"): CommandMetadata(SIZE_BASED, reviewed="fdc1994a6638c38fd088"),
    ("tapir", "GetLastValidEmbeddedLibraryPartName"): CommandMetadata(SIZE_BASED, reviewed="cb5a392f549faafb9d31"),
    ("tapir", "GetLayerCombinations"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("layerCombinations", ("ErrorItem",)),), reviewed="d5792c096350af0e8081"
    ),
    ("tapir", "GetLayerOfElementDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("layersOfElementDefaults", ("ErrorItem",)),),
        reviewed="8d4f11cc731b92182260",
    ),
    ("tapir", "GetLayoutCustomScheme"): CommandMetadata(SIZE_BASED, reviewed="00880705fd9096d069ba"),
    ("tapir", "GetLayoutSettings"): CommandMetadata(SIZE_BASED, reviewed="d61093a047841c81b259"),
    ("tapir", "GetLayoutSubsetSettings"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("subsetSettings", ("ErrorItem",)),), reviewed="cd054c135ea5d553b0e2"
    ),
    ("tapir", "GetLibPartTransformations"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "transformations", ("ErrorItem",)),
        reviewed="f76a5af89fbbd5cc7df3",
    ),
    ("tapir", "GetLibraries"): CommandMetadata(SIZE_BASED, reviewed="78e78a7d9a734306d999"),
    ("tapir", "GetLibrariesOfLibParts"): CommandMetadata(SIZE_BASED, reviewed="a187705328d2f666113e"),
    ("tapir", "GetLibraryPart2DPrimitives"): CommandMetadata(SIZE_BASED, reviewed="41cae8ff1039881754a6"),
    ("tapir", "GetLibraryPartCustomSection"): CommandMetadata(SIZE_BASED, reviewed="498866c732d34511c8e5"),
    ("tapir", "GetLibraryPartDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="c1dd783e87d0204f1aab"
    ),
    ("tapir", "GetLibraryPartFileInfo"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("files", ("ErrorItem",)),), reviewed="1a1fa96fbc3222611312"
    ),
    ("tapir", "GetLibraryPartIdentities"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("identities", ("ErrorItem",)),), reviewed="bce12ac068f602cdb790"
    ),
    ("tapir", "GetLibraryPartMetadata"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="9299bcb5f9e06afea970"
    ),
    ("tapir", "GetLibraryPartOriginalLocations"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("locations", ("ErrorItem",)),), reviewed="30d66ff4365c49141e31"
    ),
    ("tapir", "GetLibraryPartParameterValues"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="929c8a80669897d9e459"
    ),
    ("tapir", "GetLibraryPartPictures"): CommandMetadata(SIZE_BASED, reviewed="3ecbe70319738e89c573"),
    ("tapir", "GetLibraryPartScripts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="66a85bdfe142bbbdd73d"
    ),
    ("tapir", "GetLibraryPartSection"): CommandMetadata(SIZE_BASED, reviewed="2022e2915a808b791a40"),
    ("tapir", "GetLibraryPartSections"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="2b01be62f34b72104d17"
    ),
    ("tapir", "GetLibraryPartTypeDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libraryParts", ("ErrorItem",)),), reviewed="30f451c30ecb6dde80a1"
    ),
    ("tapir", "GetLineFromUser"): CommandMetadata(SIZE_BASED, reviewed="aa2b88873013bd53e0e1"),
    ("tapir", "GetLinkedPropertyObjectsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "linkedPropertyObjectsOfElements", ("ErrorItem",)),
        reviewed="77111c04b54e296f7bcf",
    ),
    ("tapir", "GetLinksOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("linksOfElements", ("ErrorItem",)),), reviewed="8a94bfa2a04070e27c8d"
    ),
    ("tapir", "GetLockableObjectSetStatus"): CommandMetadata(SIZE_BASED, reviewed="b6fc64a17f4476ad57e1"),
    ("tapir", "GetMEPDistributionSystems"): CommandMetadata(SIZE_BASED, reviewed="a75adaa0fe0966d2165b"),
    ("tapir", "GetMEPElementDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementDetails", ("ErrorItem",)),), reviewed="2989c84f1ae0ecaf4b44"
    ),
    ("tapir", "GetMEPElements"): CommandMetadata(SIZE_BASED, reviewed="d175e417d41547a4159d"),
    ("tapir", "GetMEPPhysicalSystemsOfElements"): CommandMetadata(SIZE_BASED, reviewed="129cde5faf829c71e649"),
    ("tapir", "GetMEPPorts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementPorts", ("ErrorItem",)),), reviewed="d5f1513518d8d579fa91"
    ),
    ("tapir", "GetMEPPreferenceTableContainers"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("containers", ("ErrorItem",)),), reviewed="34124588d813eee5d5ff"
    ),
    ("tapir", "GetMEPPreferenceTableRows"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("rows", ("ErrorItem",)),), reviewed="cec6872897339280359a"
    ),
    ("tapir", "GetMEPPreferenceTables"): CommandMetadata(SIZE_BASED, reviewed="617faabcfa464b458f6f"),
    ("tapir", "GetMEPRoutingElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("routingElements", ("ErrorItem",)),), reviewed="16a9d8f7f00b90da767e"
    ),
    ("tapir", "GetMEPRoutingParameters"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("routingParameters", ("ErrorItem",)),), reviewed="07e0165e601d685f57f4"
    ),
    ("tapir", "GetMEPSystemGroups"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("systemGroups", ("ErrorItem",)),), reviewed="1bd398d5ec48331d7b78"
    ),
    ("tapir", "GetMEPSystems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("mepSystems", ("ErrorItem",)),), reviewed="3574d08256e0f06495e7"
    ),
    ("tapir", "GetMEPToolDefaults"): CommandMetadata(SIZE_BASED, reviewed="4b6b693c128c8acdfadd"),
    ("tapir", "GetMagicWandSettings"): CommandMetadata(SIZE_BASED, reviewed="f35540cfeacdd06b1bfa"),
    ("tapir", "GetMainGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="mainGroups",
        outcome_lists=(OutcomeList("mainGroups", ("ErrorItem",)),),
        reviewed="b3f96c796fb4c012f583",
    ),
    ("tapir", "GetMarkerParametersOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("markerParametersOfElements", ("ErrorItem",)),),
        reviewed="8d63eb9567598a8f93c5",
    ),
    ("tapir", "GetMarquee"): CommandMetadata(SIZE_BASED, reviewed="cfb9175ca4a0c9bd6577"),
    ("tapir", "GetMergedElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("elementMerges", ("ErrorItem",)),), reviewed="186b9356e3f4bc9694cd"
    ),
    ("tapir", "GetMissingAttributes"): CommandMetadata(
        SIZE_BASED, summary_fields=("warnings",), reviewed="357f88413473d385e310"
    ),
    ("tapir", "GetMissingLibPartNames"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("libPartNames", ("ErrorItem",)),), reviewed="dcd0b62dc932f3c9f47d"
    ),
    ("tapir", "GetModelExtent"): CommandMetadata(SIZE_BASED, reviewed="63da3fa904501d9dff20"),
    ("tapir", "GetModelViewOptionDetails"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("modelViewOptionDetails", ("ErrorItem",)),),
        reviewed="eed7afcd30367c20b126",
    ),
    ("tapir", "GetModelViewOptions"): CommandMetadata(SIZE_BASED, reviewed="d4058dc752e400508b4b"),
    ("tapir", "GetModulData"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("modulData", ("ErrorItem",)),), reviewed="ecd544b1e07287f76981"
    ),
    ("tapir", "GetNavigatorItemTree"): CommandMetadata(SIZE_BASED, reviewed="b6e8bac24bb204828690"),
    ("tapir", "GetNavigatorParentItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("parentItems", ("ErrorItem",)),), reviewed="a38b83f541a7535fe6dd"
    ),
    ("tapir", "GetNoteAutoTextKeywords"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("keywords", ("ErrorItem",)),), reviewed="052bba9dc19ecc9911b2"
    ),
    ("tapir", "GetNoteAutotexts"): CommandMetadata(SIZE_BASED, reviewed="99baf70b1b1b30e627f4"),
    ("tapir", "GetOpeningDefault"): CommandMetadata(SIZE_BASED, reviewed="3fe8320c6877dd81571e"),
    ("tapir", "GetOpeningDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("openings", ("ErrorItem",)),), reviewed="7167cff636717d5ea942"
    ),
    ("tapir", "GetOpeningFloorPlanParameters"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("openings", ("ErrorItem",)),), reviewed="02bea7f909e6147b0313"
    ),
    ("tapir", "GetOpeningSymbolParameters"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("openings", ("ErrorItem",)),), reviewed="50d3c9d3d1dd21039b27"
    ),
    ("tapir", "GetOpeningTransformations"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("openingTransformations", ("ErrorItem",)),),
        reviewed="fd1e0bbc6c57e63c014f",
    ),
    ("tapir", "GetPens"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("pens", ("ErrorItem",)),), reviewed="0f63de7c83f04b0263bd"
    ),
    ("tapir", "GetPointFromUser"): CommandMetadata(SIZE_BASED, reviewed="3e4a893adc36644966b4"),
    ("tapir", "GetPolygonFromUser"): CommandMetadata(SIZE_BASED, reviewed="117591a025cd5354026f"),
    ("tapir", "GetPrinterAndPlotterInfo"): CommandMetadata(SIZE_BASED, reviewed="b2bd83969357fce5dfa6"),
    ("tapir", "GetPrinterInfo"): CommandMetadata(SIZE_BASED, reviewed="2e720cc44e74c680e399"),
    ("tapir", "GetProductVersionInfo"): CommandMetadata(SIZE_BASED, reviewed="5f00c9841a2685f0100a"),
    ("tapir", "GetProfiles"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("profiles", ("ErrorItem",)),), reviewed="47951239360aa4e93611"
    ),
    ("tapir", "GetProjectData"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("values", ("ErrorItem",)),), reviewed="24850143c1ea9a6c3d80"
    ),
    ("tapir", "GetProjectDataKeys"): CommandMetadata(SIZE_BASED, reviewed="0cfebc4207744e28d794"),
    ("tapir", "GetProjectInfo"): CommandMetadata(SIZE_BASED, reviewed="270ec68c46324cf021ec"),
    ("tapir", "GetProjectInfoFields"): CommandMetadata(SIZE_BASED, reviewed="32578f83b0dcab43da96"),
    ("tapir", "GetProjectInfoGroups"): CommandMetadata(SIZE_BASED, reviewed="418872c38df0c434ab52"),
    ("tapir", "GetProjectNotes"): CommandMetadata(SIZE_BASED, reviewed="98085061c2d36c29685d"),
    ("tapir", "GetProjectPreferences"): CommandMetadata(SIZE_BASED, reviewed="ad6e9441fe99439339d6"),
    ("tapir", "GetPropertiesOfToolDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertiesOfToolDefaults", ("ErrorItem",)),),
        reviewed="60f894693b2473383ce4",
    ),
    ("tapir", "GetPropertyAvailabilityOfDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyAvailabilities", ("ErrorItem",)),),
        reviewed="e8e8f026cf1251d0b951",
    ),
    ("tapir", "GetPropertyDefinitionsOfAttributes"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyDefinitionsOfAttributes", ("ErrorItem",)),),
        reviewed="a55dd1b357977b67e091",
    ),
    ("tapir", "GetPropertyDefinitionsOfElementComponents"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyDefinitionsOfElementComponents", ("ErrorItem",)),),
        reviewed="bfd5954f1d28ffbadf0b",
    ),
    ("tapir", "GetPropertyEditability"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(
            OutcomeList("editabilityOfElements", ("ErrorItem",)),
            OutcomeList("editabilityOfElementTypeDefaults", ("ErrorItem",)),
            OutcomeList("editabilityOfPropertyDefinitionDefaults", ("ErrorItem",)),
        ),
        reviewed="3e1a21408f32f636cb6a",
    ),
    ("tapir", "GetPropertyExpressionReferences"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("references", ("ErrorItem",)),), reviewed="8d3ca96f8771a7510e17"
    ),
    ("tapir", "GetPropertyObjectsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "propertyObjectsOfElements", ("ErrorItem",)),
        reviewed="76affe52708971e9a4d3",
    ),
    ("tapir", "GetPropertyValuesOfAttributes"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyValuesForAttributes", ("ErrorItem",)),),
        reviewed="64f1bec278b6d519a772",
    ),
    ("tapir", "GetPropertyValuesOfElementComponents"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elementComponents", "propertyValuesForElementComponents", ("ErrorItem",)),
        reason="Components form the returned row axis. Properties form an independent column axis.",
        reviewed="b9fb642d246e3cbe48ad",
    ),
    ("tapir", "GetPropertyValuesOfElementDefaults"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyValues", ("PropertyValueErrorItem",)),),
        reviewed="6cdb7093e7fbf600cfb4",
    ),
    ("tapir", "GetPropertyValuesOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "propertyValuesForElements", ("ErrorItem",)),
        reason="Only the element rows align. Properties form an independent column axis.",
        reviewed="1fc6a9a5bad6a3c48a8c",
    ),
    ("tapir", "GetPublisherSets"): CommandMetadata(SIZE_BASED, reviewed="0ab526852cb716740ae6"),
    ("tapir", "GetQuantitiesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("quantitiesOfElements", ("ErrorItem",)),),
        reviewed="9c5963b0ff50a3e7b38f",
    ),
    ("tapir", "GetRelationsOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("relations", ("ErrorItem",)),), reviewed="01dd6f7e4630351146e5"
    ),
    ("tapir", "GetRenderingScenes"): CommandMetadata(SIZE_BASED, reviewed="7cb7678e20b7b2b2010e"),
    ("tapir", "GetRenovationFilters"): CommandMetadata(SIZE_BASED, reviewed="d4c619717005e65f5950"),
    ("tapir", "GetRenovationStatusNames"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("renovationStatuses", ("ErrorItem",)),), reviewed="930a80a3f2a47515f6fc"
    ),
    ("tapir", "GetReservationStatusOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("reservationStatuses", ("ErrorItem",)),), reviewed="9e2dd359b28ffc285bbf"
    ),
    ("tapir", "GetRevisionChangeCustomScheme"): CommandMetadata(SIZE_BASED, reviewed="7a32ae8c21018100f04c"),
    ("tapir", "GetRevisionChanges"): CommandMetadata(SIZE_BASED, reviewed="301caaa9bab222b6ed49"),
    ("tapir", "GetRevisionChangesOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("revisionChangesOfElements", ("ErrorItem",)),),
        reviewed="504c88b86dadae502d5f",
    ),
    ("tapir", "GetRevisionIssues"): CommandMetadata(SIZE_BASED, reviewed="8dc02cd326a3c228da8e"),
    ("tapir", "GetRoofPlanes"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "roofPlanesOfElements", ("ErrorItem",)),
        reviewed="3e6838ffd0884b66f097",
    ),
    ("tapir", "GetRoomImage"): CommandMetadata(SIZE_BASED, reviewed="ab4e43a7f446dc00978c"),
    ("tapir", "GetSchedules"): CommandMetadata(SIZE_BASED, reviewed="1de008bccb4f7f5f94bf"),
    ("tapir", "GetSectionElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("executionResultForDatabases", ("FailedExecutionResult",)),),
        reviewed="e21eaadc2bb1bc4b488f",
    ),
    ("tapir", "GetSectionsAndElevationsDetails"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("detailsOfElements", ("ErrorItem",)),), reviewed="e8b1b29a477f365ffb74"
    ),
    ("tapir", "GetSelectedElements"): CommandMetadata(
        HANDLE_PREFERRED, count_field="elements", reviewed="8fd1e44733088ffed22c"
    ),
    ("tapir", "GetShapePrimitivesOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "shapePrimitivesOfElements", ("ErrorItem",)),
        reviewed="ba8204fcbc0f56b81e5f",
    ),
    ("tapir", "GetSkylightHolePolygons"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "skylightHolePolygons", ("ErrorItem",)),
        reviewed="18022c5ee284b606a6fb",
    ),
    ("tapir", "GetSnapPointsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "snapPointsOfElements", ("ErrorItem",)),
        reviewed="52e229104109ea0a4724",
    ),
    ("tapir", "GetSolidElementLinks"): CommandMetadata(SIZE_BASED, reviewed="a96757cf0c0cbb074faa"),
    ("tapir", "GetSpecialFolders"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("folderPaths", ("ErrorItem",)),), reviewed="84840290f0da2416af0a"
    ),
    ("tapir", "GetSplineMaxDistances"): CommandMetadata(
        SIZE_BASED, positional=Positional("splines", "results", ("ErrorItem",)), reviewed="5ef6872e44b2d8d9d8c1"
    ),
    ("tapir", "GetStories"): CommandMetadata(SIZE_BASED, reviewed="6e24a4b6c271edea1d06"),
    ("tapir", "GetStoryControlPrimitives"): CommandMetadata(SIZE_BASED, reviewed="79ee4d9d033bd3f26a7f"),
    ("tapir", "GetStructureDisplay"): CommandMetadata(SIZE_BASED, reviewed="054ddff08650c3d48339"),
    ("tapir", "GetSubelementsOfHierarchicalElements"): CommandMetadata(SIZE_BASED, reviewed="1802a9620bd34ecf0536"),
    ("tapir", "GetSunSettings"): CommandMetadata(SIZE_BASED, reviewed="30414fe6e0a6d62fd6cc"),
    ("tapir", "GetSurfaceQuantitiesOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "surfaceQuantitiesOfElements", ("ErrorItem",)),
        reason="Covering elements are shared context, not a parallel input list.",
        reviewed="45365e89968a08a35ba8",
    ),
    ("tapir", "GetSurfaceTypesOfElements"): CommandMetadata(
        SIZE_BASED, positional=Positional("elements", "surfaceTypes", ("ErrorItem",)), reviewed="f93a1a60b24679a96a65"
    ),
    ("tapir", "GetSurfaces"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("surfaces", ("ErrorItem",)),), reviewed="dc35f644c6c70781e5aa"
    ),
    ("tapir", "GetSurveyPointTransformation"): CommandMetadata(SIZE_BASED, reviewed="ecc3d52e95ce8e4c4bd9"),
    ("tapir", "GetSuspendGroupsMode"): CommandMetadata(SIZE_BASED, reviewed="0a4c77f7095fc5ab1ed0"),
    ("tapir", "GetTeamworkAccessRights"): CommandMetadata(SIZE_BASED, reviewed="d89d319aaccd09191cff"),
    ("tapir", "GetTeamworkOwnersOfDatabases"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("owners", ("ErrorItem",)),), reviewed="b1de6406fee02a0a64c2"
    ),
    ("tapir", "GetTeamworkProjectInfo"): CommandMetadata(SIZE_BASED, reviewed="04fdcc7ad170661aa670"),
    ("tapir", "GetTeamworkRightsOfObjects"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("rights", ("ErrorItem",)),), reviewed="2d349cf1730b59c2f8c5"
    ),
    ("tapir", "GetTeamworkStatus"): CommandMetadata(SIZE_BASED, reviewed="2d7c33551581dc5628d3"),
    ("tapir", "GetTextureCoordinates"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "textureCoordinates", ("ErrorItem",)),
        reviewed="fc6111f132e39a200c86",
    ),
    ("tapir", "GetToolboxItems"): CommandMetadata(SIZE_BASED, reviewed="dc2f9e166e9e35689e84"),
    ("tapir", "GetURLReferencesOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("urlReferences", ("ErrorItem",)),), reviewed="d52a25cc2c56388ad7b4"
    ),
    ("tapir", "GetUnusedAttributes"): CommandMetadata(
        SIZE_BASED, summary_fields=("warnings",), reviewed="15ab2eeb4750dc5f2357"
    ),
    ("tapir", "GetUnusedLibraryParts"): CommandMetadata(
        SIZE_BASED, summary_fields=("warnings",), reviewed="8910cd08f075edc6808d"
    ),
    ("tapir", "GetUsedAttributes"): CommandMetadata(SIZE_BASED, reviewed="f2b9c981370d140edfe9"),
    ("tapir", "GetUserDataOfAttributes"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("userDataOfAttributes", ("ErrorItem",)),),
        reviewed="dad0c2549849141b2825",
    ),
    ("tapir", "GetUserDataOfGroups"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("userDataOfGroups", ("ErrorItem",)),), reviewed="7d2e97f2355d7f48dde6"
    ),
    ("tapir", "GetUserGSID"): CommandMetadata(SIZE_BASED, reviewed="0e4be42e18acbe0c2027"),
    ("tapir", "GetView2DTransformations"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("transformations", ("ErrorItem",)),), reviewed="b383f6ec42e2e389e57d"
    ),
    ("tapir", "GetViewOptions"): CommandMetadata(SIZE_BASED, reviewed="993c2fc219b9e36c3a92"),
    ("tapir", "GetViewSettings"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("viewSettings", ("ErrorItem",)),), reviewed="bd84c3e784464b6585c7"
    ),
    ("tapir", "GetVisibleSkinStatus"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "visibleSkinStatuses", ("ErrorItem",)),
        reviewed="87c75ced88dfa4787e44",
    ),
    ("tapir", "GetZoneBoundaries"): CommandMetadata(SIZE_BASED, reviewed="0a51f7c8182a052cc50a"),
    ("tapir", "GetZoneLabelingSettings"): CommandMetadata(SIZE_BASED, reviewed="379a93c75ff73fe4bf78"),
    ("tapir", "GetZoneReductions"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "reductionsOfZones", ("ErrorItem",)),
        reviewed="4aef7a94b3a51e93b13b",
    ),
    ("tapir", "GrantElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="c1438222703100a509da"
    ),
    ("tapir", "GrantProjectData"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="1b8c536fd7385b4c6ad6"
    ),
    ("tapir", "HighlightElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="a0b0d4895da88775b7d3"
    ),
    ("tapir", "IFCFileOperation"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="0ccfee84535763a2acea"
    ),
    ("tapir", "ImportAttributesFromProject"): CommandMetadata(SIZE_BASED, reviewed="f4adb28100c1b3934301"),
    ("tapir", "ImportClassificationsXml"): CommandMetadata(SIZE_BASED, reviewed="be4a26be51d516413df9"),
    ("tapir", "ImportFavorites"): CommandMetadata(SIZE_BASED, reviewed="637be1d6ff44f1322395"),
    ("tapir", "ImportIssuesFromBCF"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="223970844c682f01fac5"
    ),
    ("tapir", "ImportMarkupsFromPDF"): CommandMetadata(
        HANDLE_PREFERRED, count_field="issues", summary_fields=("executionResult",), reviewed="7f9239423acbc71254eb"
    ),
    ("tapir", "ImportPropertiesXml"): CommandMetadata(SIZE_BASED, reviewed="c3de065be236d1821f13"),
    ("tapir", "InterpretAutoTexts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("values", ("ErrorItem",)),), reviewed="a1e5bb0f616a52f93d22"
    ),
    ("tapir", "InterpretGDLScript3D"): CommandMetadata(SIZE_BASED, reviewed="598167f99c8452b35533"),
    ("tapir", "IsLibraryPartSubtypeOf"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("results", ("ErrorItem",)),), reviewed="43d51314eb693d4543a7"
    ),
    ("tapir", "IsUsableGDLString"): CommandMetadata(SIZE_BASED, reviewed="24142b07d4c1e03ad359"),
    ("tapir", "LinkElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f9e13aed002c2989155d",
    ),
    ("tapir", "LockElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="a2b527fd6e00978a9765"
    ),
    ("tapir", "MakePropertyAvailableForElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="48f253728cd97d27d6ef"
    ),
    ("tapir", "MakePropertyUnavailableForElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="2df2e95facab5eb9d05d"
    ),
    ("tapir", "MeasureTexts"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("measurements", ("ErrorItem",)),), reviewed="3d88546681b4c7c55da5"
    ),
    ("tapir", "MergeElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="3ade61442e1886792876"
    ),
    ("tapir", "MirrorElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0fe0882c646af6c1fc20",
    ),
    ("tapir", "ModelToScreen"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("screenPoints", ("ErrorItem",)),), reviewed="e06a0f56069f960197be"
    ),
    ("tapir", "ModifyAssociativeDimensions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="5c9e84f6fd213a851a99",
    ),
    ("tapir", "ModifyBeams"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="732dc2997ed73b8fcd50",
    ),
    ("tapir", "ModifyColumns"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0a6dcfbea67f1e3c64b3",
    ),
    ("tapir", "ModifyCurtainWallFrames"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="1202cfd709634d191736",
    ),
    ("tapir", "ModifyCurtainWalls"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="d86fdecc311decd03818",
    ),
    ("tapir", "ModifyDetailMarkers"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="db7bf9cfab3394c29cee",
    ),
    ("tapir", "ModifyDoors"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c42cd316314e620022a8",
    ),
    ("tapir", "ModifyElectricalCircuits"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="eb1015a3f4fa42f74247",
    ),
    ("tapir", "ModifyElectricalDevices"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="5de7228dc912ad8d8ee1",
    ),
    ("tapir", "ModifyElectricalPanels"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="8c3e85d745b6046c5668",
    ),
    ("tapir", "ModifyElectricalProjectSettings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="aec925b282b78a36752e"
    ),
    ("tapir", "ModifyGraphicOverrideCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3b66fd4994c37d307bde",
    ),
    ("tapir", "ModifyGraphicOverrideRules"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="cb41a7fe43108cf29125",
    ),
    ("tapir", "ModifyKeynoteFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a707b4680a1d5e1f9294",
    ),
    ("tapir", "ModifyKeynoteItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f60a3f1376cf5d0e9e4d",
    ),
    ("tapir", "ModifyLabels"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="d8e543d6b39c47dfdb81",
    ),
    ("tapir", "ModifyLamps"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="4a9709db764e438f10ad",
    ),
    ("tapir", "ModifyLevelDimensions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a3ade66a6c1777835e2f",
    ),
    ("tapir", "ModifyLibraryList"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(
            OutcomeList("addResults", ("FailedExecutionResult",)),
            OutcomeList("removeResults", ("FailedExecutionResult",)),
        ),
        reviewed="7f254d831fb9bbceced6",
    ),
    ("tapir", "ModifyMEPElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elements", "executionResults", ("FailedExecutionResult",), input_identity_fields=("elementId",)
        ),
        reviewed="321ad13f241942aab805",
    ),
    ("tapir", "ModifyMEPPhysicalSystems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c9af5eefef4380b4e786",
    ),
    ("tapir", "ModifyMEPPorts"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="327d772e92acf234e8a3",
    ),
    ("tapir", "ModifyMEPPreferenceTables"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(
            OutcomeList("addedTables", ("FailedExecutionResult",)),
            OutcomeList("tables", ("FailedExecutionResult",)),
            OutcomeList("deletedTables", ("FailedExecutionResult",)),
        ),
        reviewed="74e3b6ccbfea4c80793f",
    ),
    ("tapir", "ModifyMEPRoutingElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3970d92b1b437fd3fdcb",
    ),
    ("tapir", "ModifyMEPSystemGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="9b0a55f83bff483d6acd",
    ),
    ("tapir", "ModifyMeshes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="684def2ec0156f68a63f",
    ),
    ("tapir", "ModifyMorphs"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="24bb083f8ed04b2fe53e",
    ),
    ("tapir", "ModifyObjects"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c5b1bdc302a5b8728a51",
    ),
    ("tapir", "ModifyOpenings"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="06cfbcd637fc1a4aa1a5",
    ),
    ("tapir", "ModifyPens"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="86850287fa04d067bec8",
    ),
    ("tapir", "ModifyPropertyValueOfElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="0bbbcb8c4cf6328495a2"
    ),
    ("tapir", "ModifyRailings"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="03d02a26e4e863372707",
    ),
    ("tapir", "ModifyRevisionIssues"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="cddb2b4ee31494f58baa",
    ),
    ("tapir", "ModifyRoofs"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="1e3a720da74cdd23b265",
    ),
    ("tapir", "ModifySections"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="7fc02dcd96404eb0498b",
    ),
    ("tapir", "ModifyShells"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="ddbb235678bc28dbfe24",
    ),
    ("tapir", "ModifySkylights"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0ae20b521a1bccf9f95a",
    ),
    ("tapir", "ModifySlabs"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="112b6aab604add7bb074",
    ),
    ("tapir", "ModifyStairs"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="28990c5f5a9e65c739da",
    ),
    ("tapir", "ModifyTexts"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="7bc64fab77ab39fbc480",
    ),
    ("tapir", "ModifyWalls"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e1e7105a5a647ccd3366",
    ),
    ("tapir", "ModifyWindows"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="2008957cdeacb90c77b7",
    ),
    ("tapir", "ModifyZones"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="75d3eeb15291e8b6b19d",
    ),
    ("tapir", "MoveAttributesAndFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(
            OutcomeList("attributeExecutionResults", ("FailedExecutionResult",)),
            OutcomeList("folderExecutionResults", ("FailedExecutionResult",)),
        ),
        reason="Independent attribute and folder outcome lists; there is no shared controlling axis.",
        reviewed="bc110be4eac3e8cc80ca",
    ),
    ("tapir", "MoveDesignOptionsToAnotherSet"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0feeea453a30502ac92b",
    ),
    ("tapir", "MoveElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="ff824b749d3c4e8a8358",
    ),
    ("tapir", "MoveElementsToDesignOptions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3f074763d7a3ab6824d1",
    ),
    ("tapir", "MoveFavoriteFolder"): CommandMetadata(SIZE_BASED, reviewed="4f10b7046fd09290314c"),
    ("tapir", "MoveFavorites"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reason="targetPath is one hierarchical path shared by all favorites.",
        reviewed="1b4c8c61d3c62ae439aa",
    ),
    ("tapir", "MoveGraphicOverrideRules"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="640b9206c29cd9b83f32",
    ),
    ("tapir", "MoveProjectInfoFields"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="1e5536c6b17d26b9b485",
    ),
    ("tapir", "MoveProjectInfoGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="1b115f7f3f15e22f491c",
    ),
    ("tapir", "OpenLibraryPartInEditor"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="a22201e58facaca55260"
    ),
    ("tapir", "OpenProject"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="7cb5ef0867c0ef787bc1"
    ),
    ("tapir", "PhotoRender"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="5b5151369e7fd438e36c"
    ),
    ("tapir", "PlaceOpenings"): CommandMetadata(
        HANDLE_PREFERRED,
        count_field="elements",
        outcome_lists=(OutcomeList("elements", ("ErrorItem",)),),
        reviewed="806cef80b7625791ced6",
    ),
    ("tapir", "PrintView"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="5897f104080c6dc74b59"
    ),
    ("tapir", "PublishPublisherSet"): CommandMetadata(SIZE_BASED, reviewed="2770778c5330b86906a8"),
    ("tapir", "ReadFavoritesFile"): CommandMetadata(SIZE_BASED, reviewed="8b597a6f90afc89a8593"),
    ("tapir", "RebuildCurrentDatabase"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="3df119b1adbee7a4a74e"
    ),
    ("tapir", "RebuildView"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="79cc4f436d88244d7270"
    ),
    ("tapir", "RedrawCurrentDatabase"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="1becb8e512fd14e7b224"
    ),
    ("tapir", "RefreshElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("elements", "executionResults", ("FailedExecutionResult",)),
        reviewed="33798aeb525002f2bab4",
    ),
    ("tapir", "RegularizePolygons"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("results", ("ErrorItem",)),), reviewed="845da6ce7c7f0afbe5c2"
    ),
    ("tapir", "RegularizePolylines"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("results", ("ErrorItem",)),), reviewed="6e36e2c6f36b18c0bad5"
    ),
    ("tapir", "ReindexAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="5fd6da63596846cb48ca"
    ),
    ("tapir", "ReindexLayers"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("layers", ("ErrorItem",)),), reviewed="37971dfdf973b0d0f8e8"
    ),
    ("tapir", "ReleaseElementState"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="c47c82828b9d451d89e2"
    ),
    ("tapir", "ReleaseElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="fd9d9b99e93b7bafe2db"
    ),
    ("tapir", "ReleaseHotlinkCacheManagement"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="f62ef4af0ca8946aac54"
    ),
    ("tapir", "ReleaseLockableObjectSet"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="eae84795dacb2ee866f2"
    ),
    ("tapir", "ReleaseProjectData"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="bae1347e60ac1657fc48"
    ),
    ("tapir", "ReloadLibraries"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="91104ccee2af67172e3a"
    ),
    ("tapir", "RemoveElementNotificationClient"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="5790dad4fea7ecbead04"
    ),
    ("tapir", "RemoveElementTrims"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="022e8fd0763f56a1944b",
    ),
    ("tapir", "RemoveIFCClassificationReferencesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="b73716cfd3dc8c7c896e",
    ),
    ("tapir", "RemoveIFCPropertiesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="9191b3689d7d357a07c4",
    ),
    ("tapir", "RemovePropertyFromAttributes"): CommandMetadata(
        SIZE_BASED, summary_fields=("dryRun",), reviewed="7d6dbecf74ea60453054"
    ),
    ("tapir", "RemoveSolidElementLinks"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="6f190b43b9913fa14b6e",
    ),
    ("tapir", "RenameAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="10bcfd881e0450faa8e1",
    ),
    ("tapir", "RenameDesignOptionCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="cecfa7fcef6d8ade82a9",
    ),
    ("tapir", "RenameDesignOptionSets"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="b3e11f2f5a616acf0bc7",
    ),
    ("tapir", "RenameDesignOptions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3e9d1a9225ce4eef52a8",
    ),
    ("tapir", "RenameFavoriteFolder"): CommandMetadata(SIZE_BASED, reviewed="8c71258e97659070fc12"),
    ("tapir", "RenameFavorites"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3a7f9151429decb071bc",
    ),
    ("tapir", "RenameGraphicOverrideRuleGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="d67ecffb5aff8bf0c75b",
    ),
    ("tapir", "RenameNavigatorItem"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="49d8bb3a373d689c6c9c"
    ),
    ("tapir", "RenameProjectInfoFields"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="2aefa614c7d35c8fb9e1",
    ),
    ("tapir", "RenameProjectInfoGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3f84330ba23b8a8da0d6",
    ),
    ("tapir", "ReorderDesignOptionSets"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3dad58b27bc922cb64c9",
    ),
    ("tapir", "ReorderDesignOptionsInSet"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="bf95d6d0dcbeb4a4a76e",
    ),
    ("tapir", "ReorderNavigatorItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c020d047a285e79fddb6",
    ),
    ("tapir", "RequestProjectData"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="857cbdbe908d94626f98"
    ),
    ("tapir", "ReserveElements"): CommandMetadata(SIZE_BASED, reviewed="a50ef6a7504a3c8e77fb"),
    ("tapir", "ReserveHotlinkCacheManagement"): CommandMetadata(SIZE_BASED, reviewed="8df03452f843623f1e6e"),
    ("tapir", "ReserveLockableObjectSet"): CommandMetadata(SIZE_BASED, reviewed="000e319e5805eeae747f"),
    ("tapir", "ReserveProjectData"): CommandMetadata(SIZE_BASED, reviewed="438f646741833d2e3c36"),
    ("tapir", "ResetLibraries"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="b27117c73ece7fa53d6c"
    ),
    ("tapir", "ResetZoom"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="1da08222e87469e0c962"
    ),
    ("tapir", "ResolveNames"): CommandMetadata(SIZE_BASED, reviewed="d3a44f047d9fe276570f"),
    ("tapir", "RotateCopyElements"): CommandMetadata(SIZE_BASED, reviewed="67522aadf8178a2fe918"),
    ("tapir", "RotateElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="34e7167ffc308885df34",
    ),
    ("tapir", "RunActionCenterChecks"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="824665934c7fc4891bc3",
    ),
    ("tapir", "RunParameterScriptOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="479653f42f1e66e56f97",
    ),
    ("tapir", "SaveAsModuleFile"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="c0458530f404b1a8dab2"
    ),
    ("tapir", "SaveCurrentWindowAsImage"): CommandMetadata(SIZE_BASED, reviewed="cc2a3852ca825d519eea"),
    ("tapir", "SaveProject"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="e9e1f46b24821c25c946"
    ),
    ("tapir", "SaveProjectAsArchive"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="4e90ed1b69257487e2ee"
    ),
    ("tapir", "ScaleElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="57e359cab21a4b618835",
    ),
    ("tapir", "ScreenToModel"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("coordinates", ("ErrorItem",)),), reviewed="a74e8293ac034fbfb711"
    ),
    ("tapir", "SearchFavorites"): CommandMetadata(SIZE_BASED, reviewed="1468291714b495187640"),
    ("tapir", "SearchLibraryParts"): CommandMetadata(SIZE_BASED, reviewed="375e3051aa2a597601f3"),
    ("tapir", "SearchProperties"): CommandMetadata(SIZE_BASED, reviewed="ff6921c3747d2f97bdd8"),
    ("tapir", "Set3DCutPlanes"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="b4b6808304ccf74deb76"
    ),
    ("tapir", "Set3DCutawayStatus"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="1fa7c5f36d59dfbe6675"
    ),
    ("tapir", "Set3DDocumentSettings"): CommandMetadata(SIZE_BASED, reviewed="a550b9d69405d3a77272"),
    ("tapir", "Set3DFilterAndCutSettings"): CommandMetadata(SIZE_BASED, reviewed="c282b31a41c03bf0ffd1"),
    ("tapir", "Set3DProjectionSettings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="e5ef78d71063cb880c39"
    ),
    ("tapir", "Set3DWindowSettings"): CommandMetadata(SIZE_BASED, reviewed="731445971ccbce6a6d01"),
    ("tapir", "SetActiveDesignOptionsInCombinations"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e3502e8e77d2fb64585e",
    ),
    ("tapir", "SetActiveGraphicalOverrideCombination"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="9a8f5603ee5143b8d754"
    ),
    ("tapir", "SetActiveRenovationFilter"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="efda4f4091acac01b601"
    ),
    ("tapir", "SetAnalyticalGenerationSettingsToNoRule"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="ae9cd55296e091d2ca93"
    ),
    ("tapir", "SetAnalyticalReleases"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="ffbe7e8d1314b5ea0cce",
    ),
    ("tapir", "SetAnalyticalVisibilitySettings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="dc25550635e031d4c76e"
    ),
    ("tapir", "SetArchicadVisibility"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="5e239129888e4d17f702"
    ),
    ("tapir", "SetAutoIntersect"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="cea3c139a89d9e1e1d43"
    ),
    ("tapir", "SetBuiltInPropertyValuesOfAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("attributes", "executionResults", ("FailedExecutionResult",)),
        reviewed="f2f3c0440c23a3b8c503",
    ),
    ("tapir", "SetCategoryValuesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elementCategoryValues",
            "executionResults",
            ("FailedExecutionResult",),
            input_identity_fields=("elementId",),
        ),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="7f55c65f9a8f601e02d6",
    ),
    ("tapir", "SetClassificationsOfAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="69b997015bd158e478cb",
    ),
    ("tapir", "SetClassificationsOfElementDefaults"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0358b0bb0764ddbd7248",
    ),
    ("tapir", "SetClassificationsOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elementClassifications",
            "executionResults",
            ("FailedExecutionResult",),
            input_identity_fields=("elementId",),
        ),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="626476ba72f3d44f4bc5",
    ),
    ("tapir", "SetCurrentRenderingScene"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="becdc3f00db1dad987e7"
    ),
    ("tapir", "SetCurrentTool"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="afdcc381350f3aab49a1"
    ),
    ("tapir", "SetCurrentWindowDrawingScale"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="495199b1316ccb863408"
    ),
    ("tapir", "SetCustomCurveMemberStretch"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="2964c226b8a58272e4e2",
    ),
    ("tapir", "SetDefaultDesignOption"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="db6781da5be3d27e15f0"
    ),
    ("tapir", "SetDesignOptionCombinationOfViews"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e3f04104dee6476135bf",
    ),
    ("tapir", "SetDetailsOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="29c6faa211275354547c",
    ),
    ("tapir", "SetDialogAutoClose"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="61ab25b0029c20861a16"
    ),
    ("tapir", "SetDocumentFrom3DDefaults"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="acae8940f2ced91a45e7"
    ),
    ("tapir", "SetElementInfoStrings"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elements", "executionResults", ("FailedExecutionResult",), input_identity_fields=("elementId",)
        ),
        reviewed="6b27436007f61c88921c",
    ),
    ("tapir", "SetElementNotificationClient"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="b984c6b3857a276799b6"
    ),
    ("tapir", "SetElementUserData"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elementUserData", "executionResults", ("FailedExecutionResult",), input_identity_fields=("elementId",)
        ),
        reviewed="263e065d77dac21829e1",
    ),
    ("tapir", "SetGDLDate"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="1096eb4fe8d6123995e1"
    ),
    ("tapir", "SetGDLParametersOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="669df2c1ba8f03fcc48b",
    ),
    ("tapir", "SetGeoLocation"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="0e181c3378bed4de06d1"
    ),
    ("tapir", "SetGhostStorySettings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="2162ca459adc6c7774d5"
    ),
    ("tapir", "SetGraphicOverrideRuleGroupOrder"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="da2a7f9b82c5bfd72e9d"
    ),
    ("tapir", "SetGraphicOverrideRuleOrder"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e9dd300b87a7e47b3709",
    ),
    ("tapir", "SetGridSettings"): CommandMetadata(SIZE_BASED, reviewed="4b8658df203f231cc27d"),
    ("tapir", "SetHotlinkDesignOptionTables"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="6265f319c000255002d1",
    ),
    ("tapir", "SetIFCAttributesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="d4162d0e04316822f5e8",
    ),
    ("tapir", "SetIFCClassificationReferencesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a6988dd3f756466e4270",
    ),
    ("tapir", "SetIFCPropertiesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e8752ed9cf5cf7c59822",
    ),
    ("tapir", "SetLast3DDefaultLevels"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="d58b7dfac94210034230"
    ),
    ("tapir", "SetLayerOfElementDefaults"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="71759e105c204d09d41e",
    ),
    ("tapir", "SetLayoutSettings"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="55ee871b08ea7c1b5f90",
    ),
    ("tapir", "SetLibraries"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="c294d10f2629d144f1d5"
    ),
    ("tapir", "SetLibraryPartCustomSection"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="fbecdf52e4fb31ed268b"
    ),
    ("tapir", "SetLibraryPartMetadata"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="fd0dfb2472c0d31fc606",
    ),
    ("tapir", "SetLibraryPartParameters"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="8de65beab697edfe7f1e",
    ),
    ("tapir", "SetLibraryPartPictureImages"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="225d79794cbd386a328d"
    ),
    ("tapir", "SetLibraryPartPictures"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="3edc5009ab361bc48d97"
    ),
    ("tapir", "SetLibraryPartScripts"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f50035ef1947e9e9d964",
    ),
    ("tapir", "SetLinkedPropertyObjectsOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="06589d678de5f52d7646",
    ),
    ("tapir", "SetMEPPreferenceTableRows"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a9d613d0904194771b78",
    ),
    ("tapir", "SetMEPRoutingParameters"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elements", "executionResults", ("FailedExecutionResult",), input_identity_fields=("elementId",)
        ),
        reviewed="61430aab0e427bb756bc",
    ),
    ("tapir", "SetMarkerLibraryPartOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="130377afaebf62812a8a",
    ),
    ("tapir", "SetMarkerParametersOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="50ee7af57a772ad82138",
    ),
    ("tapir", "SetMarquee"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="2a6f6fd30c0b4c673ac1"
    ),
    ("tapir", "SetMasterLayoutContext"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="c511900a7ebb7a8d4622"
    ),
    ("tapir", "SetOpeningDefault"): CommandMetadata(SIZE_BASED, reviewed="5317c0aee40199a13c85"),
    ("tapir", "SetOpeningDetails"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="507804451823a3e5612f",
    ),
    ("tapir", "SetOpeningFloorPlanParameters"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a57fdabe76fe66f93599",
    ),
    ("tapir", "SetOpeningSymbolParameters"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e389860ade795b0832a5",
    ),
    ("tapir", "SetPens"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="0b0ae8860720faabf225",
    ),
    ("tapir", "SetPlaceSettings"): CommandMetadata(SIZE_BASED, reviewed="42357363e7c195df41fa"),
    ("tapir", "SetProjectData"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="fcd44b13ece14008bc25",
    ),
    ("tapir", "SetProjectInfoField"): CommandMetadata(SIZE_BASED, reviewed="97c2b37d9c8613e8a34b"),
    ("tapir", "SetProjectNotes"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="0efae98f0760cd2e380b"
    ),
    ("tapir", "SetProjectPreferences"): CommandMetadata(SIZE_BASED, reviewed="1e62fc3d746c112b573d"),
    ("tapir", "SetPropertyValueOfAttributes"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="7a0f9ee018fce6c0529d"
    ),
    ("tapir", "SetPropertyValuesOfAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="a2dd97e5ed8efb017802",
    ),
    ("tapir", "SetPropertyValuesOfElementDefaults"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="4c84bb33c6548f5226be",
    ),
    ("tapir", "SetPropertyValuesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional(
            "elementPropertyValues",
            "executionResults",
            ("FailedExecutionResult",),
            input_identity_fields=("elementId",),
        ),
        summary_fields=("dryRun",),
        inline_if_true="dryRun",
        reviewed="5fc0e38ca3c0807d0f71",
    ),
    ("tapir", "SetSectionsAndElevationsDetails"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="cd2976661901154a0708",
    ),
    ("tapir", "SetStories"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="d0d72e873f6c4ada8c36"
    ),
    ("tapir", "SetStructureDisplay"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="2ce1d569069c6f01c48a"
    ),
    ("tapir", "SetSuspendGroupsMode"): CommandMetadata(SIZE_BASED, reviewed="05543c049aea900f4da1"),
    ("tapir", "SetURLReferencesOfElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="298545a703b11210ff47",
    ),
    ("tapir", "SetUserDataOfAttributes"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="f7280547cd92f6ab4ca2",
    ),
    ("tapir", "SetUserDataOfGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="c7acc1bf6c3085ed7a12",
    ),
    ("tapir", "SetViewOptions"): CommandMetadata(SIZE_BASED, reviewed="cdc89a057d2d27a7429f"),
    ("tapir", "SetViewRotation"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="ebd6087d54b3b2bae689",
    ),
    ("tapir", "SetViewSettings"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="3464b9d0542d2c26218a",
    ),
    ("tapir", "SetZoneLabelingSettings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="090dee331db93e8131a3"
    ),
    ("tapir", "SetZoom"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="a872debf2f6b0d159232"
    ),
    ("tapir", "ShowAlert"): CommandMetadata(SIZE_BASED, reviewed="37b64d41eb759a78bc65"),
    ("tapir", "ShowElementsIn3D"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="c42390208c5d27851f93"
    ),
    ("tapir", "ShowNotificationBubble"): CommandMetadata(SIZE_BASED, reviewed="3ffaac8847084d80488d"),
    ("tapir", "SolveStairBaseline"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("solutions", ("ErrorItem",)),), reviewed="7b79b71834c722518430"
    ),
    ("tapir", "SplitElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("results", ("ErrorItem",)),), reviewed="2fcb62df3b1914e204c6"
    ),
    ("tapir", "StoreModulData"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="e43ba818800738bccd6e",
    ),
    ("tapir", "StoreViewSettings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="0ad99c07562b4b9103bf"
    ),
    ("tapir", "TeamworkReceive"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="13df1131025e45d828a0"
    ),
    ("tapir", "TeamworkSend"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="ccd57a4b6f4bad68ea27"
    ),
    ("tapir", "TransferMEPSettings"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="8bd8ccb4837b484b20f4",
    ),
    ("tapir", "TriangulatePolygonsOfElements"): CommandMetadata(
        SIZE_BASED, positional=Positional("elements", "triangulations", ("ErrorItem",)), reviewed="ac2cfc353f1321a7010f"
    ),
    ("tapir", "TrimElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="9a04081e6f3278341685"
    ),
    ("tapir", "UngroupElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="934fc1f4b748faf969f0",
    ),
    ("tapir", "UnlinkElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="32e072c592b9560cbc7e",
    ),
    ("tapir", "UnlockElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="308b9bf65a27e45e1919"
    ),
    ("tapir", "UnmergeElements"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("elementPairs", "executionResults", ("FailedExecutionResult",)),
        reviewed="74d54ef8a9d22e8f3ea5",
    ),
    ("tapir", "UpdateAnalyticalModel"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="67b26a19643e90fa556d"
    ),
    ("tapir", "UpdateClassificationItems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="7619ff86b0c35f2e9d12",
    ),
    ("tapir", "UpdateClassificationSystems"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="2ef30eafaec4c80a3f68",
    ),
    ("tapir", "UpdateDrawings"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="e04c50193a84dcaabe21"
    ),
    ("tapir", "UpdateFavoritesFromElements"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="146244277eebb672faa6",
    ),
    ("tapir", "UpdateHotlinks"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="51bad98a93760bd593e0",
    ),
    ("tapir", "UpdateLibraryPartSections"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("sections", "executionResults", ("FailedExecutionResult",)),
        reviewed="17323b70452284a9bd33",
    ),
    ("tapir", "UpdatePropertyDefinitions"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="748a725ac53c77d765ca",
    ),
    ("tapir", "UpdatePropertyGroups"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="07831b37208351ab9610",
    ),
    ("tapir", "UpdateZones"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="cdeabd15a78b65fbc445"
    ),
    ("tapir", "UploadLibrariesToBIMcloud"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="bc18723d6972843bf07d",
    ),
    ("tapir", "ZoomToElements"): CommandMetadata(
        SIZE_BASED, summary_fields=("success", "error"), reviewed="5aa3c4d73ea033aa2256"
    ),
    ("official", "CloneProjectMapItemToViewMap"): CommandMetadata(SIZE_BASED, reviewed="e70bb152ee251d23a112"),
    ("official", "CreateLayout"): CommandMetadata(SIZE_BASED, reviewed="a37c8ee8a19e50d53ef9"),
    ("official", "CreateLayoutSubset"): CommandMetadata(SIZE_BASED, reviewed="389cb71f5828908d575e"),
    ("official", "CreateViewMapFolder"): CommandMetadata(SIZE_BASED, reviewed="bf1a923c543c02db6c30"),
    ("official", "GetActivePenTables"): CommandMetadata(SIZE_BASED, reviewed="a9afea3199586013e661"),
    ("official", "GetAllClassificationSystems"): CommandMetadata(SIZE_BASED, reviewed="bebdf6222df3168d3a40"),
    ("official", "GetAllClassificationsInSystem"): CommandMetadata(SIZE_BASED, reviewed="15679ba11dc203f5a5ba"),
    ("official", "GetAllPropertyGroupIds"): CommandMetadata(
        HANDLE_PREFERRED, count_field="propertyGroupIds", reviewed="78f12fc254e2a7b00071"
    ),
    ("official", "GetAllPropertyIds"): CommandMetadata(
        HANDLE_PREFERRED, count_field="propertyIds", reviewed="471eec16ed4e6c48bdac"
    ),
    ("official", "GetAllPropertyIdsOfElements"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyIdsOfElements", ("ErrorItem",)),),
        reviewed="cc4fef9b2340bb0215d9",
    ),
    ("official", "GetAllPropertyNames"): CommandMetadata(
        SIZE_BASED, count_field="properties", reviewed="2e6f60c1164a11f6c756"
    ),
    ("official", "GetAttributeFolderStructure"): CommandMetadata(SIZE_BASED, reviewed="115c415bd0198959e9ac"),
    ("official", "GetAttributeFolders"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributeFolders", ("ErrorItem",)),), reviewed="9a149f69c8e03120cdb9"
    ),
    ("official", "GetAttributesIndices"): CommandMetadata(
        SIZE_BASED,
        count_field="attributeIndicesAndGuids",
        outcome_lists=(OutcomeList("attributeIndicesAndGuids", ("ErrorItem",)),),
        reason="Index and GUID pairs help translate attribute identifiers.",
        reviewed="fcc92ced6af7075349fa",
    ),
    ("official", "GetBuiltInContainerNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="afcd1bb7518e9e7076ea"
    ),
    ("official", "GetClassificationItemAvailability"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("classificationItemAvailabilityList", ("ErrorItem",)),),
        reviewed="66bdffb8e5662422b1d8",
    ),
    ("official", "GetClassificationSystemIds"): CommandMetadata(
        HANDLE_PREFERRED, count_field="classificationSystemIds", reviewed="60baaf6f3499e7071455"
    ),
    ("official", "GetClassificationSystems"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("classificationSystems", ("ErrorItem",)),),
        reviewed="14cd7ac2c7433c3006ef",
    ),
    ("official", "GetComponentsOfElements"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("elements", "componentsOfElements", ("ErrorItem",)),
        reviewed="06338aec405a4fb5a928",
    ),
    ("official", "GetCompositeAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="d789f8c4daa0c046bfbf"
    ),
    ("official", "GetDetailNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="ada8e3afb25066d850bc"
    ),
    ("official", "GetDetailsOfClassificationItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("classificationItems", ("ErrorItem",)),), reviewed="31dedd030e6cae918bbb"
    ),
    ("official", "GetDetailsOfProperties"): CommandMetadata(
        SIZE_BASED,
        positional=Positional("properties", "propertyDefinitions", ("ErrorItem",)),
        reviewed="155fe4656e560a9e49e4",
    ),
    ("official", "GetDocument3DNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="db7f2ade6070a57ecd07"
    ),
    ("official", "GetElementsRelatedToZones"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("elementsRelatedToZones", ("ErrorItem",)),),
        reviewed="068c96decf2c73f258d8",
    ),
    ("official", "GetElevationNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="8a4348f5dcbaf2367b1b"
    ),
    ("official", "GetFillAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="75ebf9cf94f66b7b7e98"
    ),
    ("official", "GetInteriorElevationNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="0af706b0d81bca5a737a"
    ),
    ("official", "GetLayerAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="c0150152b3a228385be5"
    ),
    ("official", "GetLayoutSettings"): CommandMetadata(SIZE_BASED, reviewed="e18dd61605cfaa9f62f2"),
    ("official", "GetLineAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="d11a549f2fb5ac172de8"
    ),
    ("official", "GetNavigatorItemsType"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("navigatorItemIdAndTypeList", ("ErrorItem",)),),
        reviewed="80c9c1130a5af1770d2e",
    ),
    ("official", "GetPenTableAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="1ade3d6247fd47844a9b"
    ),
    ("official", "GetProductInfo"): CommandMetadata(SIZE_BASED, reviewed="27236b521c9fcd5512f9"),
    ("official", "GetProfileAttributePreview"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("previewImages", ("ErrorItem",)),), reviewed="36ea5d031469adf86b1b"
    ),
    ("official", "GetPropertyDefinitionAvailability"): CommandMetadata(
        SIZE_BASED,
        outcome_lists=(OutcomeList("propertyDefinitionAvailabilityList", ("ErrorItem",)),),
        reviewed="231bd7afa3348fce38dc",
    ),
    ("official", "GetPropertyGroups"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("propertyGroups", ("ErrorItem",)),), reviewed="4034acd25feff679e9f4"
    ),
    ("official", "GetPropertyIds"): CommandMetadata(
        HANDLE_PREFERRED,
        positional=Positional("properties", "properties", ("ErrorItem",)),
        reviewed="9b908a47d07ce1889863",
    ),
    ("official", "GetPublisherSetNames"): CommandMetadata(SIZE_BASED, reviewed="9a0708ae751d2ac9de19"),
    ("official", "GetSectionNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="7fae98426114b1c3198f"
    ),
    ("official", "GetStoryNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="a8aed15639190177b495"
    ),
    ("official", "GetTypesOfElements"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("typesOfElements", ("ErrorItem",)),), reviewed="b365fa52884fcc422824"
    ),
    ("official", "GetWorksheetNavigatorItems"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("navigatorItems", ("ErrorItem",)),), reviewed="072984276a29f5921a88"
    ),
    ("official", "GetZoneCategoryAttributes"): CommandMetadata(
        SIZE_BASED, outcome_lists=(OutcomeList("attributes", ("ErrorItem",)),), reviewed="5b732c08c04e6ea028b8"
    ),
    ("official", "IsAddOnCommandAvailable"): CommandMetadata(SIZE_BASED, reviewed="b89b0a8a0b35e73808b5"),
    ("official", "MoveNavigatorItem"): CommandMetadata(SIZE_BASED, reviewed="e9c50b5ffe6abd72721d"),
    ("official", "RenameAttributeFolders"): CommandMetadata(
        HANDLE_PREFERRED,
        outcome_lists=(OutcomeList("executionResults", ("FailedExecutionResult",)),),
        reviewed="326889388859ca3e0e5c",
    ),
    ("official", "SetLayoutSettings"): CommandMetadata(SIZE_BASED, reviewed="709c3e769a4a191ee8bf"),
}
