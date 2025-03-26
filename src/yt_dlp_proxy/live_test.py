from yt_dlp_proxy import YtDLPProxy

CMD_LIST = [
    "https://www.youtube.com/watch?v=Ay41fytSZQM",
    "-f",
    "bestaudio/worst",
    "--no-playlist",
    "--output",
    "temp_audio.%(ext)s",
    "--no-geo-bypass",
    "--cookies",
    "../cookies/youtube/cookies.txt",
]


def test():
    YtDLPProxy.execute(CMD_LIST)


test()
