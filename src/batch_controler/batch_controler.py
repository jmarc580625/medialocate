import os
import logging
import subprocess
from dict_store import DictStore
from batch_status import ProcessingStatus

class ActionControler:

    # counters gathering ActionControler statistics
    RECOVERED = "recovered"              # number of files which status is recovered from store
    RECIEVED = "recieved"                # number of files received for processing
    RECORDED = "recorded"                # number of files whith no status having one being recorded
    REPAIRED = "repaired"                # number of files whith a recorded status "error", action is performed on it
    PROCESSED = "processed"              # number of files processed by the action
    IGNORED = "ignored"                  # number of files witch action reports to further ignore it
    SUCCEEDED = "succeeded"              # number of files witch action reports a success
    FAILED = "failed"                    # number of files witch action reports an error
    DELETED = "deleted"                  # number of files which status has been deleted
    SAVED = "saved"                      # number of files which status has been saved in the store
    _COUNTER_LIST = {RECOVERED, RECIEVED, RECORDED, REPAIRED, PROCESSED, IGNORED, SUCCEEDED, FAILED, DELETED, SAVED}

    LOGGER_NAME = "ProcessMemory"
    STATUS_STORE_NAME = "pmstatus.json"

    # instance attributes
    log : logging.Logger
    force_option : bool
    action : callable
    store : DictStore
    counters : dict

    def __init__(self : 'ActionControler', 
                 working_directory: str, 
                 action, 
                 action_is_shell: bool, 
                 force_option : bool = False, 
                 parent_logger: str = None,
                 ) -> None:

        self.counters = {}
        for counter in ActionControler._COUNTER_LIST:
            self.counters[counter] = 0

        self.store = DictStore(working_directory, ActionControler.STATUS_STORE_NAME)
        self.store.open()
        self.counters[ActionControler.RECOVERED] = self.store.size()      
        
        self.log = logging.getLogger(".".join(filter(None, [parent_logger, ActionControler.LOGGER_NAME])))

        """
        Forces action to be performed even when a file is older than its corresponding status file
        """
        self.force_option = force_option

        """
        self.action is used to process files with the given action.
        The action MUST accept two str parameters: the file to process and its status file.
        The action MUST return a success status code (0) or an error status code (1).
        The action can be either a shell command name or a python function.
        If action is a shell command, action_is_shell must be True.
        """
        if action is None:
            self.action = lambda file_to_process, filename_hash: 0
        else:
            if action_is_shell:
                self.action = lambda file_to_process, filename_hash: subprocess.run([action, file_to_process, filename_hash], shell=action_is_shell, check=True).returncode
            else:
                self.action = action

    def __enter__(self : 'ActionControler'):
        return self

    def __exit__(self : 'ActionControler', *args):
        self.counters[ActionControler.SAVED] = self.store.size()
        self.store.close()

    def get_counters(self : 'ActionControler') -> dict:
        return self.counters

    def clean(self : 'ActionControler') -> None:
        """
        Remove status which value has no corresponding file.
        No further file processing is made.
        """
        for status in ProcessingStatus.getAllFromStore(self.store):
            if not os.path.isfile(status.getFilename()):
                status.delete()

    def drop(self : 'ActionControler') -> None:
        """
        Remove all status.
        No further file processing is made.
        """
        self.store.drop()

    def process(self : 'ActionControler', file_to_process: str) -> None:
        """
        a store is used to capture the file's processing status and optimize its future re-processing.
        the processing status records uses the file name hash as key and contains
            the name of the processed file
            the file's processing status
            the time of the (last) processing action
        status are:
            ONGOING for file with ongoing process
            DONE for file that has been successfully processed
            IGNORE for file that must be ignored, no further action are performed on it 
            ERROR for file processed with an error
        action: 
            is triggered for files with no existing status file or with status file older than the file itself, unless force option is set True
            recieves two parameters, the file name and the current status file name
            performs action associated with the file
            eventually updates the status file extention according to its own logic
        """

        proceed_action = False
        self.counters[ActionControler.RECIEVED] += 1

        key = ProcessingStatus.filename_hash(file_to_process)
        status = ProcessingStatus.getFromStore(self.store, key)

        if status is None:
            status = ProcessingStatus(self.store, key, ProcessingStatus.State.ONGOING, file_to_process)
            proceed_action = True
            self.counters[ActionControler.RECORDED] += 1
        else:
            state = status.getState()
            if state == ProcessingStatus.State.DONE:
                proceed_action = self.force_option or os.path.getmtime(file_to_process) > status.getTime()
            elif state == ProcessingStatus.State.ERROR:
                self.counters[ActionControler.REPAIRED] += 1
                proceed_action = True
            elif state == ProcessingStatus.State.ONGOING:
                proceed_action = True

        if proceed_action:
            self.counters[ActionControler.PROCESSED] += 1
            rc = self.action(file_to_process, status.key)
            if  rc > 9:
                status.setState(ProcessingStatus.State.ERROR)
                self.counters[ActionControler.FAILED] += 1
            elif rc == 0:
                status.setState(ProcessingStatus.State.DONE)
                self.counters[ActionControler.SUCCEEDED] += 1
            else:
                status.setState(ProcessingStatus.State.IGNORE)
                self.counters[ActionControler.IGNORED] += 1

            status.update()
