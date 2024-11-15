import os
import sys
import glob
import argparse


def main():

    # Analyse de la ligne de commande
    parser = argparse.ArgumentParser(
        description="controls that directories in the list are valid ones"
    )
    parser.add_argument("-l", type=int, default=1, required=False, help="dummy verbose level")
    parser.add_argument("dirs", nargs="*", help="directories to list")
    args = parser.parse_args(sys.argv[1:])

    dummy = args.l
    names = args.dirs

    directories = set()

    for name in names:
        directories.update(glob.glob(name))

    for dir in directories:
        print(f"{dir} {'' if os.path.exists(dir) else 'do not'} exist")


if __name__ == "__main__":
    main()
