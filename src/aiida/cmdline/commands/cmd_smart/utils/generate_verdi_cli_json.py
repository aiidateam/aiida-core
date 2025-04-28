import asyncio
import json
import re
from pathlib import Path

VERDI_CLI_MAP = Path(__file__).resolve().parent / 'verdi_cli.json'
__all__ = ['VERDI_CLI_MAP']


def parse_usage(lines):
    """Extract the usage line from the help text."""
    for line in lines:
        if line.startswith('Usage: '):
            return line[len('Usage: ') :].strip()
    return ''


def parse_description(lines):
    """Extract the description from the help text, stopping at Options or Commands."""
    description = []
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith(('Options:', 'Commands:')):
            break
        if stripped_line and not line.startswith('Usage: '):
            description.append(stripped_line)
    return ' '.join(description)


def parse_options(lines):
    """Parse the options section into a list of flags and descriptions."""
    options = []
    in_options = False
    current_option = None

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('Options:'):
            in_options = True
            continue
        if in_options:
            # Check if we've moved to a new section
            if stripped_line.startswith(('Commands:', 'Arguments:')) or (stripped_line and not line.startswith(' ')):
                break
            # Process option lines
            if stripped_line.startswith('-'):
                parts = re.split(r'\s{2,}', stripped_line, 1)
                flags = parts[0].strip()
                desc = parts[1].strip() if len(parts) > 1 else ''
                current_option = {'flags': flags, 'description': desc}
                options.append(current_option)
            elif current_option and stripped_line:
                current_option['description'] += ' ' + stripped_line
    return options


# def get_help_output(command_path):
#     """Run `verdi` with the given command path and --help, returning the output."""
#     cmd = ['verdi'] + command_path + ['--help']
#     result = subprocess.run(cmd, capture_output=True, text=True, check=False)
#     return result.stdout


def parse_sub_commands(lines):
    """Parse the sub-commands section into a list of command names."""
    sub_commands = []
    in_commands = False

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('Commands:'):
            in_commands = True
            continue
        if in_commands:
            if stripped_line.startswith(('Options:', 'Arguments:')) or (stripped_line and not line.startswith(' ')):
                break
            if stripped_line:
                parts = re.split(r'\s{2,}', stripped_line, 1)
                if parts:
                    sub_commands.append(parts[0].strip())
    return sub_commands


# def process_command(command_path):
#     """Process a command and its sub-commands recursively."""
#     help_text = get_help_output(command_path)
#     lines = help_text.split('\n')
#     usage = parse_usage(lines)
#     description = parse_description(lines)
#     options = parse_options(lines)
#     sub_commands = parse_sub_commands(lines)

#     # Add entries for each option
#     for option in options:
#         flags = [f.strip() for f in option['flags'].split(',')]
#         combined_flags = ' / '.join(flags)
#         full_command = 'verdi ' + ' '.join(command_path + [combined_flags])
#         entry = {
#             'command': full_command,
#             'usage': usage,
#             'description': f"{description} {option['description']}".strip(),
#         }
#         entries.append(entry)

#     if not sub_commands:
#         # Add the command itself without options
#         full_command = 'verdi ' + ' '.join(command_path)
#         entry = {'command': full_command, 'usage': usage, 'description': description.strip()}
#         entries.append(entry)
#     else:
#         # Recursively process sub-commands
#         for sub_cmd in sub_commands:
#             process_command(command_path + [sub_cmd])


# if __name__ == '__main__':
#     if argv[1]:
#         output_file = Path(argv[1])
#     else:
#         output_file = Path(__file__).resolve().parent / 'verdi_cli.json'

#     entries: list[dict] = []
#     process_command([])

#     with open(output_file, 'w') as f:
#         json.dump(entries, f, indent=2)


CONCURRENCY_LIMIT = 10  # Adjust based on your system capabilities


async def get_help_output(command_path):
    """Async version of subprocess execution with timeout handling"""
    cmd = ['verdi'] + command_path + ['--help']
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=30)
        return stdout.decode().strip()
    except Exception as e:
        print(f"Error executing {' '.join(cmd)}: {e!s}")
        return ''


async def process_command(command_path, semaphore, entries):
    """Process a command and its sub-commands recursively with async"""

    print(f"Processing command: {' '.join(command_path)}")

    async with semaphore:
        help_text = await get_help_output(command_path)

    if not help_text:
        return

    lines = help_text.split('\n')
    usage = parse_usage(lines)
    description = parse_description(lines)
    options = parse_options(lines)
    sub_commands = parse_sub_commands(lines)

    # Process options concurrently
    for option in options:
        flags = [f.strip() for f in option['flags'].split(',')]
        combined_flags = ' / '.join(flags)
        full_command = 'verdi ' + ' '.join(command_path + [combined_flags])
        entry = {
            'command': full_command,
            'usage': usage,
            'description': f"{description} {option['description']}".strip(),
        }
        entries.append(entry)

    # Process sub-commands concurrently
    sub_tasks = []
    if sub_commands:
        for sub_cmd in sub_commands:
            sub_tasks.append(process_command(command_path + [sub_cmd], semaphore, entries))
    else:
        full_command = 'verdi ' + ' '.join(command_path)
        entries.append({'command': full_command, 'usage': usage, 'description': description.strip()})

    if sub_tasks:
        await asyncio.gather(*sub_tasks)


async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    entries: list[dict] = []

    await process_command([], semaphore, entries)

    with open(VERDI_CLI_MAP, 'w') as f:
        json.dump(entries, f, indent=2)


if __name__ == '__main__':
    asyncio.run(main())
