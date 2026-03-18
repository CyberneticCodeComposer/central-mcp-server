# central-mcp-server

Note: Ensure the env.local file is populated with Central Base URL, Client ID & Client Secret

1. Create Virtual Environment
```bash
python3 -m venv env
```
2. Activate Virtual Environment
```bash
source env/bin/activate
```
3. Install Requirements
```bash
pip install -r requirements.txt
```
4. Start MCP Server
```bash
python3 main.py
```
5. Once the Server is running, you should be able to view & enable the `central-mcp` Tool in the CoPilot Tools 
[img CoPilot Screenshot](/CoPilot_Setup.png)