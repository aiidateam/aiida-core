# Make sure you source this script rather than executing it
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]
then
    echo "You need to source this script, stopping." >&2
    exit 1
fi

# run as
# source load-singlesshagent.sh -v
# for verbose output

load_singlesshagent() {
    local VERBOSE
    local SSH_ENV
    local SSH_ADD_OUTPUT
    local SSHADD_RETVAL
    local NUMKEYS

    VERBOSE=false
    if [ "$1" == "-v" ]
    then
        VERBOSE=true
    fi

    [ "$VERBOSE" == "true" ] && echo "Single SSH agent script [verbose mode]" >&2
    SSH_ENV="$HOME/.ssh/agent-environment"
    # Source SSH settings, if applicable
    if [ -r "${SSH_ENV}" ]; then
        source "${SSH_ENV}" > /dev/null
        [ "$VERBOSE" == "true" ] && echo "- sourcing existing environment" >&2
    else
        [ "$VERBOSE" == "true" ] && echo "- no existing environment to source" >&2
    fi

    SSH_ADD_OUTPUT=`ssh-add -l`
    # Needed, the later 'test' calls will replace this
    SSHADD_RETVAL="$?"
    # Error code: 0: there are keys; 1: there are no keys; 2: cannot contact agent
    if [ "$SSHADD_RETVAL" == "2" ]
    then
        [ "$VERBOSE" == "true" ] && echo "  - unable to contact agent, creating a new one" >&2
        (umask 066; ssh-agent > ${SSH_ENV})
        source "${SSH_ENV}" > /dev/null
    elif [ "$SSHADD_RETVAL" == "1" ]
    then
        [ "$VERBOSE" == "true" ] && echo "  - ssh-agent found (${SSH_AGENT_PID}), no keys (I might want to add keys here)" >&2
        # Maybe the user wants to do it by himself?
        #ssh-add
    elif [ "$SSHADD_RETVAL" == "0" ]
    then
        NUMKEYS=`echo "$SSH_ADD_OUTPUT" | wc -l`
        [ "$VERBOSE" == "true" ] && echo "  - ssh-agent found (${SSH_AGENT_PID}) with $NUMKEYS keys" >&2
    else
        [ "$VERBOSE" == "true" ] && echo "  - ssh-add replied with return code $SSHADD_RETVAL - I don't know what to do..." >&2
    fi

    [ "$VERBOSE" == "true" ] && echo "- Debugging, listing all ssh-agents for user $USER:"
    [ "$VERBOSE" == "true" ] && ps -U "$USER" | grep --color=no '[s]sh-agent'
}

# Run with the requested verbosity
if [ "$1" == "-v" ]
then
    load_singlesshagent -v
else
    load_singlesshagent
fi
