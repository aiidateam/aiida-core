#!/usr/bin/env python
"""
Some sample tests of how to use the slumber client (when the server is simply
run with
./manage runserver
and can be reached at http://localhost:8000/)

Note that to work, this example requires that the server is running, and that
there is some data in the database.

Note also that, unless in api.py the apply_filters is overridden, using the
.distinct() method, there may be duplicates in the results for very complicated
queries.
"""
import sys
import slumber

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))

        ### Use get(key[, default]) instead of a try/catch
        #try:
        #    cr = (env['LINES'], env['COLUMNS'])
        #except:
        #    cr = (25, 80)
    return int(cr[1]), int(cr[0])

(width, height) = getTerminalSize()
#print "Your terminal size is: %d x %s" % (width, height)

print "Connecting..."

# localhost testing, no auth for the moment
api = slumber.API("http://localhost:8000/api/v1")

print "Connected. Press Enter to start seeing results."
raw_input()

offset=0

def clear_screen():
    print chr(27) + "[2J"

class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


char_getter = _GetchUnix()


def get_keystroke():
    keys_pressed = []

    while True:
        ch = char_getter()
        ordch = ord(ch)
        
        # A '27' prepares to further commands
        # I append if it is a 27, or if the list is not empy
        if ordch == 27 or keys_pressed:
            keys_pressed.append(ord(ch))
            
        if len(keys_pressed) == 3:
            if keys_pressed == [27, 91, 65]:
                return "up"
            elif keys_pressed == [27, 91, 66]:
                return "down"
            elif keys_pressed == [27, 91, 67]:
                return "right"
            elif keys_pressed == [27, 91, 68]:
                return "left"
            else:
                return "unknown"
            keys_pressed = []
        elif keys_pressed:
            # Do nothing if I am building the list
            pass
        else:
            return ord(ch)

def get_offset(url):
    import urlparse
    
    if url is None:
        return None

    # a list of tuples for the query elements of the URL
    the_tuples = urlparse.parse_qsl(urlparse.urlparse(url).query)
    return int(dict(the_tuples)['offset'])
    

exit = False
refresh = False

while True:
    (width, height) = getTerminalSize()
    numspaces = width-4-4
    if numspaces < 0:
        numspaces = 0

    withscheduler = api.dbnode.get(type__startswith="calculation.",
                                   dbattributes__key="state",
                                   dbattributes__tval="WITHSCHEDULER",
                                   offset=offset,
                                   limit = height - 4
                                   )

    clear_screen()

    header_str = "## Total: {}, offset={}, limit={}".format(withscheduler['meta']['total_count'], withscheduler['meta']['offset'], withscheduler['meta']['limit'])
    print header_str[:width]
    
    for i, calc in enumerate(withscheduler['objects'],start=1):
        retstring = "-> {}: calc # {}: '{}'".format(withscheduler['meta']['offset'] + i, calc['id'], calc['label'])
        print retstring[:width]
        #print calc['resource_uri']

    prevpage = withscheduler['meta']['previous']
    nextpage = withscheduler['meta']['next'] 

    prevoffset = get_offset(prevpage)
    nextoffset = get_offset(nextpage)

    help_str = "? to see SchedStat"
    if numspaces >= len(help_str) + 2:
        central_str = "[{}]".format(help_str).center(numspaces)
    elif numspaces >= 2:
        central_str = "[{}]".format(help_str[:numspaces-2])
    else:
        central_str = ""
    
    menu_str = (" {}".format('<--' if not (prevpage is None and offset == 0) else '   ') +
                central_str +
                "{}".format('-->' if nextpage is not None else '   '))
    print(menu_str)

    while True:
        k = get_keystroke()

        if refresh:
            refresh = False
            break
        
        # 3 == CTRL+C
        # 26 == CTRL+Z
        if k == ord('q') or k==3 or k==26:
            exit = True
            break
        if k == 'left':
            if offset == 0:
                continue
            if prevoffset is None:
                offset = 0
            else:
                offset = prevoffset        
            break
        if k == 'right':
            if nextoffset is None:
                continue
            offset = nextoffset
            break
        if k == ord("?"):
            schedstat = api.dbattribute.get(dbnode__in=[calc['id'] for calc in withscheduler['objects']],
                                                key="scheduler_state", limit=len(withscheduler['objects']))            

            schedstatdict = {attr['dbnode']: attr['tval'] for attr in schedstat['objects']}

            clear_screen()
            print "## DETAILED INFO:"[:width]
            
            for i, calc in enumerate(withscheduler['objects'],start=1):
                list_id = withscheduler['meta']['offset'] + i
                try:
                    ret_str = "-> {}: calc # {}: {}".format(
                        list_id, calc['id'], schedstatdict[calc['resource_uri']])
                except KeyError:
                    ret_str = "-> {}: calc # {}: ???".format(list_id, calc['id'])
                print ret_str[:width]

            print "[Press any key to go back]"[:width]
            # So that next keypress will refresh
            refresh = True
                
    if exit:
        break
        
