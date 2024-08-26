import asyncio
import datetime
import platform
import os

from src.routes.auth import blacklisted_tokens


def cleanup_blacklist():
    blacklisted_tokens.clear()


async def periodic_clean_blacklist(time: int = 60):
    # Запускається кожні 60 хвилин
    while True:
        cleanup_blacklist()
        await asyncio.sleep(60 * time)


def get_downloads_directory():
    """Get the path to the user's Downloads directory."""
    home = os.path.expanduser("~")
    if platform.system() == "Windows":
        return os.path.join(home, "Downloads")
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(home, "Downloads")
    elif platform.system() == "Linux":
        return os.path.join(home, "Downloads")
    else:
        return home  # Default to home if the OS is not recognized