import logging
import argparse
from medialocate.batch.controler import ActionControler
from medialocate.finder.file import FileFinder


# -------------------------------------------------------------------------------
# usage & help
# -------------------------------------------------------------------------------
USAGE = "%s [-p] [-c] [-f] [-h] [-v] memory_directory action"
HELP = """
Walk the directory tree from the current directory and process files with processing_command.
memory_directory is used to capture the file processing status and optimize its future
re-processing. File processing status is recorded with a file stored in memory_directory.
File processing status name is the combination of the file name hash and its processing status
as filename extension. Status file records the time of the last file processing with its timestamp
and contains the name of the original file.
Extension are
    .tmp for file with ongoing process
    .ignore for file already processed that must be ignored by subsequents processing
    .done for file already processed
Action:
    . Is triggered for files with no existing status file or with status file older than the file
      itself, unless force option is set True
    . Recieves two parameters, the file name and the current status file name
    . Performs action associated with the file
    . Eventually updates the status file extention according to its own logic
    . Default processing_command is : echo

OPTIONS:
  -h: display this help, ignore any other options and parameters
  -p: purge mode, removes any status files in memory_directory which has no corresponding file
      no action is made on files
  -c: clear all status files from memory_directory
      no action is made on files
  -f: perform action even when file is older than its corresponding status file
  -v: verbose mode, trace progress on standard error
EXAMPLE:
  typical use is in association with the find command which retrieves the list of files to process
  find . -path ./.mymemory -prune -o -type f -print | processMemory ./.mymemory ls
"""


# -------------------------------------------------------------------------------
def main(
    memory_store_location: str,
    purge_mode: bool,
    clear_mode: bool,
    force_option: bool,
    verbose_level: int,
    log: logging.Logger,
) -> int:
    """
    Main entry point for the processMemory script.

    This function parses the command line arguments and starts the processing of the files.

    The function processes the files in the following way:

    1. If the -p option is given, all status files in memory_directory are removed which have
       no corresponding file and no further file processing is made.
    2. If the -c option is given, all status files in memory_directory are cleared before
       processing.
    3. If the -f option is given, the file processing is done even when the status file is newer
       than the file.
    4. If the -v option is given, the progress of the processing is traced on the standard error.
    5. For each file in the standard input, the following steps are performed:
       a. The file is processed with the given action command if the file does not have a status
          file with the same hash.
       b. If the file has a status file with the same hash, the file is skipped unless the -f
          option is given.
       c. If the -v option is given with a value greater than 2, the file processing is traced on
          the standard error.
    6. Finally, the total number of files processed is printed on the standard error.

    param args: the command line arguments as parsed by argparse
    return: 0 if the command line arguments are valid and the processing is successful, 1 otherwise
    """

    try:
        with ActionControler(
            memory_store_location,
            force_option=force_option,
        ) as controler:
            if clear_mode:
                controler.drop()
                log.info(f"all status cleared in {memory_store_location}")
            elif purge_mode:
                controler.clean()
                log.info(
                    f"{controler.get_counters()}".replace("'", "")
                    .replace("{", "")
                    .replace("}", "")
                )
            else:
                finder = FileFinder(".", prune=[memory_store_location])
                for file in finder.find():
                    controler.process(file)

                log.info(
                    f"finder: {finder.get_counters()}".replace("'", "")
                    .replace("{", "")
                    .replace("}", "")
                )
                log.info(
                    f"controler: {controler.get_counters()}".replace("'", "")
                    .replace("{", "")
                    .replace("}", "")
                )

        return 0

    except Exception as e:
        log.error(f"{e}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Optimize batch processing of files using a memory directory."
    )
    parser.add_argument(
        "-p",
        action="store_true",
        help=(
            "purge mode, removes any status files which has no corresponding file "
            "and no further file processing is made"
        ),
    )
    parser.add_argument(
        "-c", action="store_true", help="clear all status files from memory_directory"
    )
    parser.add_argument(
        "-f",
        action="store_true",
        help="forces file processing even when status file is newer than its corresponding file",
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        help="verbose mode, trace progress on standard error",
    )
    parser.add_argument(
        "memory_directory",
        type=str,
        help="directory where to store file processing status",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.NOTSET)
    log = logging.getLogger("ProcessMemory")
    log.debug(", ".join(f"{arg}={getattr(args, arg)}" for arg in vars(args)))

    main(
        args.memory_directory,
        args.p,
        args.c,
        args.f,
        args.v,
        log,
    )
