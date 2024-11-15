import os
import json
import glob
import logging
import argparse

from store.dict import DictStore
from media.location_grouping import MediaGroups
from media.parameters import MEDIALOCATION_DIR, MEDIALOCATION_STORE_NAME, MEDIAGROUPS_STORE_NAME


def get_directories(names: list[str]) -> set[str]:
    directories = set()
    if len(names) == 0:
        directories.add(os.getcwd())
    else:
        for name in names:
            directories.update(glob.glob(name))
    return directories


def main():
    parser = argparse.ArgumentParser(description="groups media files by gps location proximity")
    parser.add_argument(
        "-d",
        type=float,
        default=1,
        required=False,
        help="distance threshold (in kilometer) below which media files are grouped",
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help="forces grouping even no changes have been made in media location data",
    )
    parser.add_argument(
        "dirs", nargs="*", help="directories to search for media files location data"
    )
    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s : %(levelname)-8s : %(name)s : %(message)s",
        level=logging.NOTSET,
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    log = logging.getLogger("GroupMediaCommand")
    log.debug(", ".join(f"{arg}={getattr(args, arg)}" for arg in vars(args)))

    grouping_threshold = float(args.d)
    directories = get_directories(args.dirs)
    if len(directories) == 0:
        log.info(f"no directory found")
        return 0

    log.debug(f"directories={directories}")

    input_name = MEDIALOCATION_STORE_NAME
    for directory in directories:
        working_directory = os.path.join(directory, MEDIALOCATION_DIR)
        output_file_name = os.path.join(working_directory, MEDIAGROUPS_STORE_NAME)
        input_file_name = os.path.join(working_directory, input_name)

        if not os.path.exists(working_directory):
            log.info(f"{directory} does not exist, ignored")
            continue
        elif not os.path.isdir(working_directory):
            log.info(f"{directory} is not a directory, ignored")
            continue
        elif not os.path.exists(input_file_name):
            log.info(f"{directory} no location data available, ignored")
            continue

        if (
            not args.f
            and os.path.exists(output_file_name)
            and os.path.getmtime(output_file_name) > os.path.getmtime(input_file_name)
        ):
            # TODO: check treshold is also unchanged
            log.info(f"{directory} is up-to-date, ignored")
            continue

        with DictStore(working_directory, input_name) as input_store:
            locations = input_store.dict()
            media_groups = MediaGroups(grouping_threshold, [])
            media_groups.add_locations(locations)
            with open(output_file_name, "w") as output_file:
                d = media_groups.toDict()
                json.dump(d, output_file, indent=2)
                log.info(
                    f"{directory} : grouping {len(locations)} media in {len(media_groups.groups)} groups"
                )


if __name__ == "__main__":
    main()
