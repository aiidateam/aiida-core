###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida-core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""The implementation of all llm models for the `verdi smart` command line interface."""

# TODO:
# This design is subject to change,
# depending on un-foreseen capability and optimizations and available options of other LLMs.
# since this is in backend and will not break backward compatibility,
# I avoid going crazy for now.

import json

import click
import requests


def groc_command_generator(sentence, api_key):
    """Generate a command using the Groq LLM."""
    # return 'verdi process list'  # Placeholder for the actual command

    model = 'llama3-8b-8192'
    endpoint = 'https://api.groq.com/openai/v1/chat/completions'

    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    data = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant that generates valid verdi commands.'
                "Only respond with the complete command starting with 'verdi'.",
            },
            {'role': 'user', 'content': f'Generate a AiiDA verdi command to: {sentence}.'},
        ],
        'max_tokens': 100,
        'temperature': 0.5,  # Lower temperature for more deterministic output
    }

    response = requests.post(endpoint, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        suggestion = response_json['choices'][0]['message']['content'].strip()
        # Ensure the command starts with verdi
        if not suggestion.startswith('verdi'):
            suggestion = 'verdi ' + suggestion
        return suggestion
    else:
        click.echo(f'Failed to generate command: {response.status_code} - {response.text}')
        return None
