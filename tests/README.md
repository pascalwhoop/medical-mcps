# MCP Server Test Suite

Comprehensive Tavern-based integration tests for all MCP biological API servers.

## Test Coverage

### ✅ All 6 APIs Tested (28 tools)

| API | Tools Tested | Key Features |
|-----|--------------|--------------|
| **UniProt** | 5 | get_protein, search_proteins, get_protein_sequence, get_disease_associations, map_ids |
| **Reactome** | 4 | get_pathway, query_pathways, get_pathway_participants, get_disease_pathways |
| **KEGG** | 8 | get_pathway, list_pathways, find_pathways, get_gene, find_genes, get_disease, find_diseases, link_pathway_genes |
| **OMIM** | 6 | API key requirement validation for all tools |
| **GWAS Catalog** | 3 | search_associations, search_studies, search_traits |
| **Pathway Commons** | 2 | search, top_pathways |

## Running Tests

### Run all tests:
```bash
uv run pytest tests/ -v
```

### Run specific API tests:
```bash
uv run pytest tests/test_uniprot_tools.tavern.yaml -v
uv run pytest tests/test_reactome_tools.tavern.yaml -v
uv run pytest tests/test_kegg_tools.tavern.yaml -v
uv run pytest tests/test_omim_tools.tavern.yaml -v
uv run pytest tests/test_gwas_tools.tavern.yaml -v
uv run pytest tests/test_pathwaycommons_tools.tavern.yaml -v
```

### Expected Output:
```
tests/test_gwas_tools.tavern.yaml::GWAS Catalog API Tools Test Suite PASSED [ 16%]
tests/test_kegg_tools.tavern.yaml::KEGG API Tools Test Suite PASSED      [ 33%]
tests/test_omim_tools.tavern.yaml::OMIM API Tools Test Suite PASSED      [ 50%]
tests/test_pathwaycommons_tools.tavern.yaml::Pathway Commons API Tools Test Suite PASSED [ 66%]
tests/test_reactome_tools.tavern.yaml::Reactome API Tools Test Suite PASSED [ 83%]
tests/test_uniprot_tools.tavern.yaml::UniProt API Tools Test Suite PASSED [100%]

============================== 6 passed in ~30s ==============================
```

## Test Architecture

### Fixtures (`conftest.py`)

- **`server_url`**: Configurable server URL (default: `http://localhost:8000`)
- **`server_process`**: Automatically starts/stops MCP server for entire test session
- **`mcp_base_url`**: Base URL for MCP API endpoints

The server is started once for all tests and shared across test sessions for efficiency.

### Test Structure

Each test file follows this pattern:

```yaml
---
test_name: API Name Tools Test Suite

marks:
  - usefixtures:
      - server_process  # Start server before tests

stages:
  - name: Test tool with valid input
    request:
      url: "http://localhost:8000/tools/api/mcp"
      method: POST
      headers:
        Content-Type: "application/json"
      json:
        jsonrpc: "2.0"
        id: 1
        method: "tools/call"
        params:
          name: "tool_name"
          arguments:
            param: "value"
    response:
      status_code: 200
      strict:
        - json:off  # Allow MCP framework extra fields
      json:
        jsonrpc: "2.0"
        id: 1
        result:
          content:
            - type: "text"
              text: !re_search "API: ApiName"
```

### Key Testing Patterns

1. **MCP JSON-RPC Format**: All requests use MCP protocol (jsonrpc 2.0, tools/call method)
2. **Strict Mode Off**: `strict: [json:off]` allows MCP framework fields (`isError`, `structuredContent`)
3. **Regex Validation**: Use `!re_search` to validate API response prefixes (e.g., "API: UniProt")
4. **Real API Calls**: Tests make actual calls to external APIs (UniProt, Reactome, KEGG, etc.)
5. **Error Validation**: OMIM tests validate proper error messages for missing API keys

## API-Specific Notes

### APIs Not Requiring Authentication
- **UniProt, Reactome, KEGG, GWAS Catalog, Pathway Commons**
- Tests make real API calls to public endpoints
- No special configuration needed

### APIs Requiring Client-Provided Keys
- **OMIM**
- API key must be provided by MCP client with each request
- Tests validate that missing API keys return proper error messages
- Server does NOT store API keys

## Test Performance

- **Duration**: ~30 seconds for full suite
- **Parallelization**: Tests run sequentially (server is shared)
- **External API Calls**: Tests make real calls to public APIs
  - UniProt, Reactome, KEGG: Fast (~1-2s per test)
  - GWAS, Pathway Commons: May be slower (~5-10s per test)

## Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing processes
kill -9 <PID>
```

### Tests Timeout
- Check network connectivity to external APIs
- Some APIs (GWAS, Pathway Commons) can be slow
- Consider increasing timeout in `conftest.py`

### API Key Tests Failing
- Verify OMIM tools are correctly checking for empty/missing API keys
- Check error message format: "API key is required"

## Development

### Adding New Tests

1. Create `tests/test_newapi_tools.tavern.yaml`
2. Add `usefixtures: [server_process]` mark
3. Use standard MCP JSON-RPC request format
4. Set `strict: [json:off]` in responses
5. Validate API response prefix with `!re_search "API: NewAPI"`

### Testing with Real API Keys

To test OMIM with a real API key:

```bash
# Modify test to include real key
api_key: "your-real-omim-api-key"
```

Note: Be careful not to commit real API keys to version control!

## Continuous Integration

These tests are suitable for CI/CD pipelines:

```bash
# In CI environment
uv sync --extra test
uv run pytest tests/ -v --tb=short
```

**Considerations:**
- Tests make real external API calls
- May be rate-limited by external APIs
- Network connectivity required
- Consider mocking for faster CI runs

## Related Documentation

- [MCP Server README](../tools/README.md) - Server architecture and API documentation
- [Worklog Entry](../agents/worklog/2025-11-09_20-49-17-implemented-client-side-api-key-handling.md) - Implementation details
