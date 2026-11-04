# Schema exclusions to revisit when affected

The generator config holds the active exclusions and their short reasons. Verify these details against the target release before retiring an exclusion.

## GetClassificationOfAttributesInSystem

- In MultiConn 0.9.7 for Tapir 1.8.0, the published result expects each successful `attributeClassifications` item to contain `classificationSystemId` and optional `classificationItemId` directly. Tapir wraps those fields under `classificationId`, so the published model rejects the actual success shape. [Published result schema](https://github.com/SzamosiMate/multiconn_archicad/blob/v0.9.7/code_generation/tapir/schema/tapir_master_schema.json#L19235) · [Tapir response writer](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.8.0/archicad-addon/Sources/ClassificationCommands.cpp#L650)
- `GetClassificationsOfAttributes` returns the classifications for every system. Filter its `classificationIds` by system and treat an absent assignment as unclassified. Revisit the exclusion if a later release aligns the schema with the writer and offers a result the broader command cannot supply. [Broader command writer](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.8.0/archicad-addon/Sources/ClassificationCommands.cpp#L375)
