import importlib
import inspect
import io
import json
import logging
import random
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterator

import requests

# from yt_dlp_proxy.proxy_providers import *
from tqdm import tqdm

SPEEDTEST_URL = "http://212.183.159.230/5MB.zip"
_MAX_WORKERS = 16

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def is_valid_proxy(proxy):
    """Check if the proxy is valid."""
    return (
        proxy.get("host") is not None
        and proxy.get("country") != "Russia"
        and proxy.get("country") != "RU"
    )


def construct_proxy_string(proxy):
    """Construct a proxy string from the proxy dictionary."""
    if proxy.get("username"):
        return (
            f'{proxy["username"]}:{proxy["password"]}@{proxy["host"]}:{proxy["port"]}'
        )
    return f'{proxy["host"]}:{proxy["port"]}'


def test_proxy(proxy):
    """Test the proxy by measuring the download time."""
    proxy_str = construct_proxy_string(proxy)
    start_time = time.perf_counter()
    try:
        response = requests.get(
            SPEEDTEST_URL,
            stream=True,
            proxies={"http": f"http://{proxy_str}"},
            timeout=5,
        )
        response.raise_for_status()  # Ensure we raise an error for bad responses

        total_length = response.headers.get("content-length")
        if total_length is None or int(total_length) != 5242880:
            return None

        with io.BytesIO() as f:
            download_time, _ = download_with_progress(
                response, f, total_length, start_time
            )
            return {"time": download_time, **proxy}  # Include original proxy info
    except requests.RequestException:
        return None


def download_with_progress(response, f, total_length, start_time):
    """Download content from the response with progress tracking."""
    downloaded_bytes = 0
    for chunk in response.iter_content(1024):
        downloaded_bytes += len(chunk)
        f.write(chunk)
        done = int(30 * downloaded_bytes / int(total_length))
        if done == 6:
            break
        if (
            done > 3
            and (downloaded_bytes // (time.perf_counter() - start_time) / 100000) < 1.0
        ):
            return float("inf"), downloaded_bytes
    return round(time.perf_counter() - start_time, 2), downloaded_bytes


def save_proxies_to_file(proxies) -> None:
    """Save the best proxies to a JSON file."""
    with open("proxy.json", "w") as f:
        json.dump(proxies, f, indent=4)


def get_best_proxies(providers):
    """Return the top five proxies based on speed from all providers."""
    all_proxies = []
    proxies = None
    for provider in providers:
        try:
            print(f"Fetching proxies from {provider.__class__.__name__}")
            proxies = provider.fetch_proxies()
            all_proxies.extend([proxy for proxy in proxies if is_valid_proxy(proxy)])
        except Exception as e:
            print(f"Failed to fetch proxies from {provider.__class__.__name__}: {e}")

    best_proxies = []
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in all_proxies}
        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Testing proxies",
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_noinv_fmt}]",
            unit=" proxies",
            unit_scale=True,
            ncols=80,
        ):
            result = future.result()
            if result is not None:
                best_proxies.append(result)
    return sorted(best_proxies, key=lambda x: x["time"])[:5]


def update_proxies():
    """Update the proxies list and save the best ones."""
    providers = []

    module_names = [
        "yt_dlp_proxy.proxy_providers.sandvpn_provider",
        "yt_dlp_proxy.proxy_providers.vnnet_provider",
        "yt_dlp_proxy.proxy_providers.onworks_provider",
    ]

    for module_name in module_names:
        module = importlib.import_module(module_name)
        classes = inspect.getmembers(module, inspect.isclass)
        providers.append(
            [classs[-1]() for classs in classes if classs[0] != "ProxyProvider"][0]
        )

    best_proxies = get_best_proxies(providers)
    save_proxies_to_file(best_proxies)
    print("All done.")


def run_yt_dlp(args: list[str], yt_dlp_path: Path | None = None) -> bool:
    """Run yt-dlp with a randomly selected proxy."""

    print("Checking for proxy list...")

    if not Path("proxy.json").exists():
        print("'proxy.json' not found. Starting proxy list update...")
        update_proxies()

    for proxy_str in iter_random_proxy_str():
        print(f"Using proxy from {proxy_str}")
        if execute_yt_dlp_command(
            proxy_str=proxy_str, args=args, yt_dlp_path=yt_dlp_path
        ):
            return True
        print("Got 'Sign in to confirm' error. Trying again with another proxy...")
    return False


def get_proxy_strings() -> list[str]:
    """Construct a proxy string from the proxy dictionary."""
    all_strings = list(iter_random_proxy_str())
    return all_strings


def iter_random_proxy_str() -> Iterator[str]:
    """Construct a proxy string from the proxy dictionary."""
    proxy_json: Path = Path("proxy.json")
    proxy_txt = proxy_json.read_text()

    json_data = json.loads(proxy_txt)

    while True:
        proxy = random.choice(json_data)
        # print(f"Trying proxy: {proxy}")
        if proxy.get("username"):
            yield (
                f'{proxy["username"]}:{proxy["password"]}@{proxy["host"]}:{proxy["port"]}'
            )
        else:
            yield f'{proxy["host"]}:{proxy["port"]}'


def execute_yt_dlp_command(
    proxy_str: str, args: list[str], yt_dlp_path: Path | None = None
) -> bool:
    """Execute the yt-dlp command with the given proxy."""

    # yt_dlp = shutil.which("yt-dlp") or "yt-dlp"
    # yt_dlp_path = yt_dlp_path or Path(yt_dlp)
    if yt_dlp_path is None:
        maybe_path = shutil.which("yt-dlp")
        if maybe_path is None:
            print("yt-dlp not found in PATH. Please specify the path to yt-dlp")
            return False
        yt_dlp_path = Path(maybe_path)

    # cmd_str = subprocess.list2cmdline(args)

    full_cmd_list: list[str] = [
        yt_dlp_path,
        "--color",
        "always",
        f"--proxy=http://{proxy_str}",
    ] + args

    cmd_str = subprocess.list2cmdline(full_cmd_list)
    logger.info("Executing yt-dlp command: %s", cmd_str)
    proc = subprocess.Popen(
        full_cmd_list, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    with proc:
        stdout = proc.stdout
        assert stdout is not None
        for line in stdout:
            # print(line.decode("utf-8").strip())
            line_str = line.decode("utf-8", errors="ignore")
            print(line_str.strip())
            if "Sign in to" in line_str or "403" in line_str:
                return False
    cmd_str = subprocess.list2cmdline(full_cmd_list)
    logger.error("could not execute yt-dlp command: %s", cmd_str)
    return True
