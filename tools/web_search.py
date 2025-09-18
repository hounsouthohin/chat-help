from smolagents.tools import Tool

class DuckDuckGoSearchTool(Tool):
    name = "web_search"
    description = (
        "Performs a DuckDuckGo web search based on a query "
        "and returns the top search results (title, link, snippet)."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query to perform."
        }
    }
    output_type = "string"

    def __init__(self, max_results: int = 10, **kwargs):
        super().__init__()
        self.max_results = max_results
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise ImportError(
                "You must install `duckduckgo-search`: pip install duckduckgo-search"
            ) from e
        self.ddgs = DDGS(**kwargs)

    def forward(self, query: str) -> str:
        try:
            results = self.ddgs.text(query, max_results=self.max_results)
        except Exception as e:
            return f"❌ Error during DuckDuckGo search: {str(e)}"

        if not results:
            return "⚠️ No results found. Try a different query."

        postprocessed_results = [
            f"[{result['title']}]({result['href']})\n{result['body']}"
            for result in results
        ]
        return "## 🔎 Search Results\n\n" + "\n\n".join(postprocessed_results)
