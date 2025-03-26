from .api import execute_yt_dlp_command, run_yt_dlp, update_proxies


class YtDLPProxy:

    @staticmethod
    def execute(proxy_str: str, args: list[str]) -> None:
        execute_yt_dlp_command(proxy_str=proxy_str, args=args)

    @staticmethod
    def update_and_execute(args: list[str]) -> None:
        run_yt_dlp(args)  # not sure how this works yet

    @staticmethod
    def update() -> None:
        update_proxies()


__all__ = ["YtDLPProxy"]
