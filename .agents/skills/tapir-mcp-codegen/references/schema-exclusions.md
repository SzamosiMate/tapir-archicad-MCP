# Schema exclusions to revisit when affected

The generator config holds the active exclusions and their short reasons. Verify these details against the target release before retiring an exclusion.

## SetCurrent3DStyle

- In multiconn 0.9.8 / Tapir 2.0.0, this command validates the style name, then unconditionally returns `APIERR_NOTSUPPORTED`. It does not call `ACAPI_View_SetCurrent3DStyle`: the source documents an Archicad assertion in versions 28 and 29 and no known working version. [Pinned implementation](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/2.0.0/archicad-addon/Sources/3DProjectionCommands.cpp#L1009)
- Retire the exclusion when a published target actually switches the current style without that assertion, with matching schemas and documented supported Archicad versions. A declaration or schema alone is insufficient; the refusal must be removed by a working implementation.
