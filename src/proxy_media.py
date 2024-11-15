import os
import json
import glob
import logging
import argparse

from media.group_proxy import MediaProxiesControler

def get_directories(names : list[str]) -> set[str]:
    directories = set()
    if len(names) == 0:
        directories.add(os.getcwd())
    else:
        for name in names:
            directories.update(glob.glob(name))
    return directories
 
def main():
    parser = argparse.ArgumentParser(description="groups media files by gps location proximity")
    parser.add_argument("-d", type=float, default=1, required=False, help="distance threshold (in kilometer) below which media files are grouped")
    parser.add_argument('-f', action = 'store_true', help = 'forces pxoying even no changes have been made in media location group data')
    parser.add_argument("-t",  required=False, default=".", help="target where to store the processed data")
    parser.add_argument("dirs", nargs="+", help="list of directories where to search for media group data")
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s : %(levelname)-8s : %(name)s : %(message)s',
        level=logging.NOTSET,
        datefmt='%Y-%m-%d %H:%M:%S')
    logger_name = "ProxyMediaCommand"
    log = logging.getLogger(logger_name)
    log.debug(', '.join(f'{arg}={getattr(args, arg)}' for arg in vars(args)))

    proxy_threshold = float(args.d)
    target_directory_name = args.t

    source_directories = get_directories(args.dirs)
    if len(source_directories) == 0:
        log.info(f"no directory found") 
        return 0
    log.debug(f"directories={source_directories}")

    try:
        with MediaProxiesControler(target_directory_name, logger_name) as proxies:
            for directory in source_directories:
                proxies.find_proxies(directory, proxy_threshold)
    except Exception as e:
        log.error(f"{e}")

if __name__ == '__main__':
    main()
