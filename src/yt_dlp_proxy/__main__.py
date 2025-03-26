import argparse
from dataclasses import dataclass

from yt_dlp_proxy import YtDLPProxy


@dataclass
class Args:
    args: list[str]
    update: bool

    def __post_init__(self):
        assert isinstance(self.args, list)
        assert isinstance(self.update, bool)


def _parse_args() -> Args:
    parser = argparse.ArgumentParser(description="yt-dlp with best free proxy")
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update best proxy",
    )
    tmp, unknown_args = parser.parse_known_args()
    return Args(
        args=unknown_args,
        update=tmp.update,
    )


def main() -> None:
    """Main function to handle script arguments and execute the appropriate command."""
    args: Args = _parse_args()
    try:
        if args.update:
            YtDLPProxy.update()
        else:
            YtDLPProxy.execute(args=args.args)
    except KeyboardInterrupt:
        print("Canceled by user")


if __name__ == "__main__":
    main()
