import plum

new_event_loop = plum.new_event_loop


def run_until_complete(future, loop):
    plum.run_until_complete(future, loop)
