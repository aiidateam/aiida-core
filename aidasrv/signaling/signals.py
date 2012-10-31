def get_running_signal(calc_id):
    """
    Returns a string with the command to execute on the cluster
    to send a signal back when the code starts running (e.g., a
    curl connection to a suitable API backend server).

    For the moment, signaling is not implemented (i.e., an empty
    string is returned).
    """
    return """
    # Signaling not implemented yet.
    """

def get_finished_signal(calc_id):
    """
    Returns a string with the command to execute on the cluster
    to send a signal back when the code ends running (e.g., a
    curl connection to a suitable API backend server).

    For the moment, signaling is not implemented (i.e., an empty
    string is returned).
    """
    return """
    # Signaling not implemented yet.
    """

