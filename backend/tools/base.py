from typing import Any, Dict

class BaseTool:
    """
    Abstract base class for all independent tools.
    Every tool must implement single-responsibility actions and have no knowledge of other tools.
    """
    name: str = ""
    description: str = ""

    async def run(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute the tool action. Must be implemented by subclasses.
        """
        raise NotImplementedError("Each tool must implement its own run method.")
