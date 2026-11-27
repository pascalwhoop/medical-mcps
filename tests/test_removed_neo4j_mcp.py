from starlette.testclient import TestClient

from medical_mcps.http_server import app


def test_everycure_kg_is_not_exposed():
    headers = {"Accept": "application/json, text/event-stream"}
    list_tools = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        response = client.post("/tools/everycure-kg/mcp", json=list_tools, headers=headers)
        assert response.status_code == 404

        response = client.post("/tools/unified/mcp", json=list_tools, headers=headers)
        assert response.status_code == 200
        assert '"tools"' in response.text
        assert "pubmed_" in response.text
        assert "everycure_kg_" not in response.text
