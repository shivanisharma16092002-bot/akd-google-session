import asyncio
import json
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp():
    # Adjust path to the server script
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    server_script = os.path.join(backend_dir, "mcp_server.py")
    
    # Ensure dependencies are available (we already pip installed them)
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy()
    )
    
    print("Connecting to local MCP server...")
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # List tools to verify
                tools = await session.list_tools()
                print(f"Available tools: {[t.name for t in tools.tools]}")

                # 1. Call scrape_github
                print("Step 1: Scraping 'torvalds'...")
                scrape_result = await session.call_tool("scrape_github", {"username": "torvalds"})
                if scrape_result.isError:
                    print(f"Error in scrape_github: {scrape_result.content}")
                    return
                
                # The content is a list of TextContent objects
                github_data = json.loads(scrape_result.content[0].text)
                print("Scrape successful.")
                
                # 2. Pass that result into analyze_profile
                print("Step 2: Analyzing profile...")
                analysis_result = await session.call_tool("analyze_profile", {"github_data": github_data})
                if analysis_result.isError:
                    print(f"Error in analyze_profile: {analysis_result.content}")
                    # If this fails due to API key, we should mention it
                    return
                
                analysis = json.loads(analysis_result.content[0].text)
                print("Analysis successful.")
                
                # 3. Generate an HTML card
                print("Step 3: Generating HTML card...")
                card_result = await session.call_tool("generate_card_html", {
                    "username": "torvalds",
                    "github_data": github_data,
                    "analysis": analysis
                })
                if card_result.isError:
                    print(f"Error in generate_card_html: {card_result.content}")
                    return
                
                print("Card generation successful.")
                
                # 4. Save the card (optional but good to test)
                print("Step 4: Saving card...")
                save_result = await session.call_tool("save_card", {
                    "username": "torvalds",
                    "html": card_result.content[0].text
                })
                print(f"Card saved to: {save_result.content[0].text}")
                
                # Print the final requested info
                print("\n--- RESULTS ---")
                print(f"Card Theme: {analysis.get('card_theme')}")
                print(f"Developer Vibe: {analysis.get('developer_vibe')}")
                
    except Exception as e:
        print(f"CRITICAL FAILURE: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_mcp())
