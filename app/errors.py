"""Custom exceptions so routes can show friendly messages while logs keep the details."""


class ComicCraftError(Exception):
    """Base class. `user_message` is safe to show in the browser."""

    user_message = "Sorry, ComicCraft couldn't generate your comic right now. Please try again."


class ConfigError(ComicCraftError):
    user_message = "ComicCraft is not configured correctly. Please check the server settings."


class OutlineError(ComicCraftError):
    pass


class StoryError(ComicCraftError):
    pass


class ImageError(ComicCraftError):
    pass


class ExportError(ComicCraftError):
    pass
