"""Test container initialization."""
import psutil, os

def test_file_descriptor_closed(aiida_profile):
    """Checks if the number of open file descriptors change during a reset."""
    def list_open_file_descriptors():
        process = psutil.Process(os.getpid())
        return process.open_files()
    # We have some connections active due to aiida profile during the first
    # reset these are destroyed. We check the second time changes the number of
    # open file descriptors.
    # TODO The fix should keep the existing connections alive and just reuse them
    #      then one does not need to do two resets.
    aiida_profile.reset_storage() 
    open_file_descriptors_before = list_open_file_descriptors()
    aiida_profile.reset_storage() 
    open_file_descriptors_after = list_open_file_descriptors()
    assert len(open_file_descriptors_before) == len(open_file_descriptors_after), f"Before these file descriptor were open:\n{open_file_descriptors_before}\n Now these are open:\n{open_file_descriptors_after}"
