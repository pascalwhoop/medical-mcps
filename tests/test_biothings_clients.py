"""
Unit tests for BioThings API clients (MyGene, MyDisease, MyChem)
These test the clients directly without going through the HTTP server layer.
"""

import pytest
from medical_mcps.api_clients.mygene_client import MyGeneClient
from medical_mcps.api_clients.mydisease_client import MyDiseaseClient
from medical_mcps.api_clients.mychem_client import MyChemClient


@pytest.mark.asyncio
async def test_mygene_get_gene_by_symbol_with_context_manager():
    """Test MyGene client using async context manager (like caching tests)"""
    client = MyGeneClient()
    
    async with client:
        result = await client.get_gene("TP53")
        assert isinstance(result, dict)
        assert "symbol" in result or "TP53" in str(result)


@pytest.mark.asyncio
async def test_mygene_get_gene_by_symbol_without_context_manager():
    """Test MyGene client WITHOUT async context manager (like servers do)"""
    client = MyGeneClient()
    
    # This is how servers use clients - directly without context manager
    result = await client.get_gene("TP53")
    assert isinstance(result, dict)
    assert "symbol" in result or "TP53" in str(result)
    
    # Cleanup manually
    if client._client:
        await client._client.aclose()


@pytest.mark.asyncio
async def test_mygene_get_gene_by_id():
    """Test MyGene client with Entrez ID"""
    client = MyGeneClient()
    
    async with client:
        result = await client.get_gene("7157")  # TP53 Entrez ID
        assert isinstance(result, dict)
        assert result.get("_id") == "7157" or result.get("entrezgene") == 7157


@pytest.mark.asyncio
async def test_mydisease_get_disease():
    """Test MyDisease client"""
    client = MyDiseaseClient()
    
    async with client:
        result = await client.get_disease("melanoma")
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_mychem_get_drug():
    """Test MyChem client"""
    client = MyChemClient()
    
    async with client:
        result = await client.get_drug("imatinib")
        assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_mygene_server_handler_pattern():
    """Test MyGene client using the exact pattern servers use (module-level singleton)"""
    # This simulates how servers use clients - as module-level singletons
    from medical_mcps.servers.biothings_server import mygene_client
    
    # Call directly like the server handler does
    result = await mygene_client.get_gene("TP53")
    assert isinstance(result, dict)
    assert "symbol" in result or "TP53" in str(result)
    
    # Test that it works multiple times (like multiple requests)
    result2 = await mygene_client.get_gene("7157")
    assert isinstance(result2, dict)

