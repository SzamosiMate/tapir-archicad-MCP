# Element queries

`elements_query` is a handwritten command discovered with `archicad_list_commands`,
described with `archicad_get_command_schema`, and executed through
`archicad_call_tool`. It uses multiconn's executable query model and evaluation.
It requires Tapir 2.0.0 or newer.

Discover property IDs and metadata using `properties_search_properties`, and
classification systems/items using the existing classification commands. The
query command's schema describes the supported predicates, test kinds, operators,
and operand types. Property quantities use SI units, except angles use degrees.
Multiconn refreshes and validates referenced metadata during execution.

For example, find walls and doors:

```json
{
  "name": "elements_query",
  "arguments": {
    "port": 19723,
    "params": {
      "query": {
        "schema_version": "1.0",
        "where": {
          "kind": "element_type",
          "test": {"kind": "element_type", "types": ["Wall", "Door"]}
        }
      }
    }
  }
}
```

Queries can nest `all` and `any` groups containing `items`. Use the schema for
property and classification predicate details. Executable queries require an
explicit `schema_version`; editor draft rows are a different format.

Omitting `params.elements` (or supplying null) searches the floor plan through
`find_elements()`. Supplying an array filters those IDs through
`filter_elements_by_query_result()` and returns its successful matches. An empty
array returns no matches while still validating the query. Supplied order and
duplicate matches are preserved. Neither path changes selection.

The response contains `elements`, with each ID in the usual
`{"elementId": {"guid": "..."}}` shape. Per-element evaluation errors are omitted
from matches. Invalid queries and query-wide failures fail the command. Pagination
and background jobs follow the existing dispatch workflow; continuation pages
read retained results without rerunning the query.

## Development pilot

The published multiconn 0.9.8 dependency does not contain the query engine. During
the pilot, install the sibling source checkout into the MCP environment:

```powershell
uv pip install --python .venv/Scripts/python.exe --no-deps --editable ../multiconn_archicad
.venv/Scripts/python.exe -m pytest tests
```

Use the corresponding `.venv/bin/python` path on macOS/Linux. `uv sync` restores
the published dependency, so reapply the editable install afterward. The release
dependency pin and lockfile must be updated to a multiconn release containing the
query engine before shipping this feature.

The handwritten implementation lives in `tools/custom/element_queries.py` and is
imported by `tools/custom/__init__.py`. It registers through
`register_tool_for_dispatch`, like generated wrappers. Regeneration leaves it
intact. Query capability gaps are addressed in multiconn; existing discovery
commands remain available during the pilot.
