from pathlib import Path

from .api import execute_yt_dlp_command, get_proxy_strings, run_yt_dlp, update_proxies


class YtDLPProxy:

    @staticmethod
    def execute_raw(proxy_str: str, args: list[str]) -> None:
        execute_yt_dlp_command(proxy_str=proxy_str, args=args)

    @staticmethod
    def load_proxy_strings() -> list[str]:
        return get_proxy_strings()

    @staticmethod
    def execute(args: list[str], yt_dlp_path: Path | None = None) -> bool:
        """If proxy.json is not found it will be created"""
        return run_yt_dlp(
            args=args, yt_dlp_path=yt_dlp_path
        )  # not sure how this works yet

    @staticmethod
    def update() -> None:
        update_proxies()


__all__ = ["YtDLPProxy"]
