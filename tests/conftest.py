from types import SimpleNamespace
import pytest
from unittest.mock import Mock

from multiconn_archicad.basic_types import Port
from multiconn_archicad.basic_types import ProductInfo, ArchicadLocation, SoloProjectID
from tapir_archicad_mcp.context import multi_conn_instance


class FakeArchicad:
    """
    In-memory stand-in for a running Archicad instance with the Tapir
    Add-On. Generated tools talk to it through the same
    'core.post_tapir_command' interface as a live connection, so they can
    be tested end-to-end (dispatch, Tapir call, result validation) on
    machines without Archicad.
    """

    def __init__(self, port: int = 19723):
        self.port = port
        self.calls: list[tuple[str, dict | None]] = []
        self._canned_responses: dict[str, dict] = {}
        self.core = SimpleNamespace(post_tapir_command=self._post_tapir_command)
        self.product_info = ProductInfo(version=28, build=6003, lang="USA")
        self.archicad_location = ArchicadLocation(archicadLocation="/Applications/GRAPHISOFT/Archicad 28/ARCHICAD")
        self.archicad_id = SoloProjectID(projectName="FakeProject", projectPath="/path/to/fake_project.pln")


    def on_tapir_command(self, command: str, response: dict) -> None:
        """Registers the canned response returned for a Tapir command."""
        self._canned_responses[command] = response

    def _post_tapir_command(self, command: str, parameters: dict | None = None) -> dict:
        self.calls.append((command, parameters))
        if command not in self._canned_responses:
            raise RuntimeError(
                f"FakeArchicad received unexpected Tapir command '{command}'. "
                f"Register a response with on_tapir_command() first."
            )
        return self._canned_responses[command]


@pytest.fixture
def fake_archicad():
    """
    Provides a FakeArchicad wired into the multi_conn_instance ContextVar
    and ensures all generated tools are registered for dispatch.
    """
    from tapir_archicad_mcp.tools.registration import register_all_tools

    register_all_tools()

    fake = FakeArchicad()
    multi_conn = SimpleNamespace(
        refresh=SimpleNamespace(all_ports=Mock()),
        connect=SimpleNamespace(all=Mock()),
        active={Port(fake.port): fake},
    )

    token = multi_conn_instance.set(multi_conn)
    yield fake
    multi_conn_instance.reset(token)
