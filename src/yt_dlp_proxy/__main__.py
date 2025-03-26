import sys

from yt_dlp_proxy.api import run_yt_dlp, update_proxies


def main() -> None:
    """Main function to handle script arguments and execute the appropriate command."""
    try:
        if "update" in sys.argv:
            update_proxies()
        elif len(sys.argv) < 2:
            print(
                "usage: main.py update | <yt-dlp args> \nScript for starting yt-dlp with best free proxy\nCommands:\n update   Update best proxy"
            )
        else:
            sys.argv.pop(0)
            run_yt_dlp(sys.argv)
    except KeyboardInterrupt:
        print("Canceled by user")


if __name__ == "__main__":
    main()
