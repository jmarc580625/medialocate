"""Media file location and GPS data extraction.

This module provides functionality to locate media files in directories and extract
their GPS location data, supporting batch processing and browser-based visualization.
"""

import os
import logging
import argparse
import glob
from pathlib import Path
from medialocate.batch.controler import ActionControler
from medialocate.finder.file import FileFinder
from medialocate.media.locator import MediaLocateAction
from medialocate.media.parameters import MEDIALOCATION_DIR, MEDIALOCATION_STORE_PATH

# -------------------------------------------------------------------------------
# get script location
# -------------------------------------------------------------------------------
EXEC_HOME = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.realpath(os.path.join(EXEC_HOME, "../lib"))


def get_directories(names: list[str]) -> set[str]:
    """Get a set of directory paths from a list of names.

    If no names are provided, uses the current working directory.
    Supports glob patterns for directory selection.

    Args:
        names: List of directory names or glob patterns

    Returns:
        Set of resolved directory paths
    """
    directories = set()
    for name in names:
        directories.update(glob.glob(name))
    if len(directories) == 0:
        directories.add(os.getcwd())
    return directories


def locate_media(
    log: logging.Logger,
    directory: str,
    output_file_name: str,
    force_option: bool = False,
    launch_option: bool = False,
    regenerate_option: bool = False,
    current_directory_only_option: bool = False,
) -> int:
    """Process media files in a directory to extract GPS location data.

    Args:
        log: Logger instance for output
        directory: Directory to process
        output_file_name: Path to save extracted location data
        force_option: Force processing even if output exists
        launch_option: Launch browser after processing
        regenerate_option: Regenerate all location data
        current_directory_only_option: Only process current directory

    Returns:
        0 on success, 1 on error
    """
    try:
        new_dir = os.path.normpath(directory.strip())
        os.chdir(new_dir)
        log.info(f"working now in directory {os.getcwd()}")
    except Exception as e:
        log.error(f"{e} while trying to change curent working directory to {new_dir}")
        return 1

    working_dir = MEDIALOCATION_DIR

    try:
        if regenerate_option:
            result = MediaLocateAction(
                working_dir, output_file_name
            ).create_location_page()
            return 0 if result is not None else 1
        else:
            if not os.path.exists(working_dir):
                os.makedirs(working_dir)

            age_limit: float = 0.0
            if not force_option:
                try:
                    age_limit = os.path.getmtime(MEDIALOCATION_STORE_PATH)
                except OSError:
                    pass

            finder = FileFinder(
                ".",
                extensions=MediaLocateAction.get_expected_extensions(),
                prune=[working_dir],
                min_age=age_limit,
                max_depth=0 if current_directory_only_option else -1,
            )
            with MediaLocateAction(working_dir, output_file_name) as media_action:
                with ActionControler(
                    working_dir,
                    action=media_action,
                    force_option=force_option,
                ) as controler:
                    for file in finder.find():
                        controler.process(file)

                    page = media_action.create_location_page()
                    if page is not None:
                        log.info(f"medialocate page created: {page}")
                        if launch_option:
                            launch_browser(page)
                    else:
                        log.info("medialocate page not created or updated")

                log.info(
                    f"{finder.get_counters()}".replace("'", "")
                    .replace("{", "")
                    .replace("}", "")
                )
                log.info(
                    f"{controler.get_counters()}".replace("'", "")
                    .replace("{", "")
                    .replace("}", "")
                )

    except Exception as e:
        log.fatal(f"UNCAUGHT EXCEPTION:{e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


def launch_browser(page: str) -> None:
    """Launch the system's default web browser to view results.

    Args:
        page: URL or file path to open in browser
    """
    try:
        import webbrowser

        webbrowser.open(str(Path(page).resolve().as_uri()))
    except Exception as e:
        logging.error(f"Failed to launch browser: {str(e)}")


def main():
    """Run the media location extraction tool.

    Processes command line arguments and executes the media location extraction
    based on provided parameters and directory paths.
    """
    help = """
    extract GSP location for all media files in the target directory and its subdirectories to
    generates an html application page showing media and places where they have been captured
    """
    parser = argparse.ArgumentParser(
        description=help, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-l", action="store_true", help="launch display of the created page"
    )
    parser.add_argument(
        "-d",
        action="store_true",
        help="restricts file processing in the current directory",
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help="forces file processing even when already being processed",
    )
    parser.add_argument(
        "-o",
        type=str,
        default="medialocate.html",
        help="redirect output to the specified outfile"
        + "\ndefault output is 'medialocate.html"
        + "\nuses '-' to direct output to standard directory",
    )
    parser.add_argument(
        "-r",
        action="store_true",
        help="unconditionnaly regenerate the output, ignore -d and -f options",
    )
    parser.add_argument(
        "dirs",
        nargs="*",
        help="target directories fr\ndefault target is the local directory",
    )
    args = parser.parse_args()

    # logging.basicConfig(level = logging.NOTSET)
    logging.basicConfig(
        format="%(asctime)s : %(levelname)-8s : %(name)s : %(message)s",
        level=logging.NOTSET,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger("MediaLocateCommand")
    log.debug(", ".join(f"{arg}={getattr(args, arg)}" for arg in vars(args)))

    directories = get_directories(args.dirs)
    if len(directories) == 0:
        log.info("no directory found")
        return 0

    log.debug(f"directories={directories}")

    cwd = os.getcwd()
    for directory in directories:
        locate_media(log, directory, args.o, args.f, args.l, args.r, args.d)
        os.chdir(cwd)

    return 0


if __name__ == "__main__":
    main()
