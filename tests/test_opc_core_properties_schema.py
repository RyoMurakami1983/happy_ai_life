from __future__ import annotations

from pathlib import Path

import lxml.etree


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "plugins" / "happy-ai-life" / "skills" / "pptx" / "scripts" / "office" / "schemas" / "ecma" / "fouth-edition" / "opc-coreProperties.xsd"


def test_opc_core_properties_schema_loads_without_network() -> None:
    parser = lxml.etree.XMLParser(no_network=True)
    xsd_doc = lxml.etree.parse(
        str(SCHEMA),
        parser=parser,
        base_url=SCHEMA.resolve().as_uri(),
    )
    schema = lxml.etree.XMLSchema(xsd_doc)

    assert schema is not None
