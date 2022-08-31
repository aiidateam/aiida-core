.. _how-to:run-containerized_codes:

****************************************
How to setup and run containerized codes
****************************************

This how-to walks you through the steps of setting up a (possibly remote) compute resource, setting up a containerized code on that computer, and submitting a calculation through AiiDA (with more details supplement to :ref:`introductory tutorial <tutorial:basic:calcjob>`).

.. important::

    Since running code in then container require mapping the current directory where the input files locate to the working directory in the container, the current directory is specified in the job script as ``$PWD``.
    The computer setup to run containerized code MUST set ``use_double_quotes`` to ``True`` to escape the command line parameters using double quotes.

There are two type of codes the ``installed`` and ``portable``, which are all supported to be run in the container.

Docker containerized code
=========================

Running installed code within container
---------------------------------------

The typical code setup for for running code installed docker container is shown below.

    .. code-block:: yaml

        ---
        label: add-docker
        description: add docker
        default_calc_job_plugin: core.arithmetic.add
        on_computer: true
        computer: localhost
        filepath_executable: /bin/bash
        image: ubuntu
        engine_command: docker run -v $PWD:/workdir:rw -w /workdir {image} sh -c
        escape_exec_line: true
        prepend_text: ' '
        append_text: ' '

The option ``escape_exec_line`` is mandatory for running commands in docker which need to have executable command in the quotes after ``sh -c`` of engine command.
This opiton will escape the ``cmdline_params`` along with the redirect parameters in the quotes so the whole command is recogonized and run inside the docker container.

Then this code can be used the same way as regular setup code.
There is no need to explicitly imstall or compile the code on the machine, but only require that the executable is in the container shipped with docker image.
For the first time running the docker containerized code, the image will pulled from dockerhub automatically, which will cost sometime if the image is large.

.. important::

    One issue with running code in docker container is the files output is owned by ``root``, which lead to the remote folder can not be cleaned by current user.

Running portable code within container
--------------------------------------

Using container as the environment to run the portable script code without isolating environment and installing libraries.
It is common to have some codes which are scripts for example the python scripts that need to run with libraries dependencies installed prehead.
It is not easy to isolate the environment and install the dependencies everytime before setup the code for AiiDA.
With portable code option, the container can be regard as the environment with dependencies installed.
The user just need to setup the script code as portable code and run it inside the container where has all dependencies fullfilled.
Therefore, the code can be run on whatever computer that has docker istalled, which reduce the burden to sophisticately configure the environment and dependencies in computer.

The code setup config example is:

    .. code-block:: yaml

        ---
        label: "docker-python-add"
        description: "doing python add"
        input_plugin: "core.arithmetic.add"
        image: "python:3.9.12-buster"
        engine_command: "docker run -v $PWD:/workdir:rw -w /workdir {image} sh -c"
        escape_exec_line: true
        filepath_executable: "./eval_sh.py"
        filepath_files: "<Filepath to directory containing code files>"
        prepend_text: " "
        append_text: " "

where the executable ``eval_sh.py`` is a dummy python script that execute ``bash < aiida.in > aiida.out``.
It can be a much complex script with many different libraries imported such as ``numpy``, ``scipy``, only if the container image has this libraries installed.

    .. code-block:: python

        #!/usr/bin/env python
        import os

        if __name__ == '__main__':
            inputfile = 'aiida.in'
            outputfile = 'aiida.out'

            with open(inputfile, 'r') as f:
                bashCommand = '/bin/bash < aiida.in > aiida.out'
                os.system(bashCommand)

To run this containerized portable code, you need to specify the computer where has docker installed in ``CalcJob`` metadata as:

    .. code-block:: python

        from aiida import orm
        from aiida.engine import run_get_node
        from aiida.plugins import CalculationFactory

        ArithmeticAddCalculation = CalculationFactory('core.arithmetic.add')

        inputs = {
            'code': orm.load_code('docker-python-add'),
            'x': orm.Int(4),
            'y': orm.Int(6),
            'metadata': {
                'computer': orm.load_computer('localhost'), # localhost has docker installed
                'options': {
                    'resources': {
                        'num_machines': 1,
                        'num_mpiprocs_per_machine': 1
                    }
                }
            }
        }

        _, node = run_get_node(ArithmeticAddCalculation, **inputs)

Just specify the computer and user are free from worrying about the dependencies on the computer.

Containerized code run by Singularity and Sarus
===============================================

Sarus and Singularity are softwares to run Linux containers on High Performance Computing environments.
Their development have been driven by the specific requirements of HPC system, while leveraging open standards and technologies to encourage vendor and community involement.

The simulation codes are shipping inside the container which can be hardware agnostic.
The images are built by users to fit the deployment of a specific application, and spawing of isolated environments (containers) when running.
Users can install any code to remote cluster by simply pull the image.

The Sarus and Singularity share the same logic of using the the containerized technology.
The only difference is the details of the command to launch the container and call/running the softwares for inside, which can be specified by ``engine_command`` when setup the code.

The typical code setup for for running Sarus containerized code is shown below.

    .. code-block::yaml

        ---
        label: sarus-qe
        description: The QuantumESPRESSO in the Sarus container.
        default_calc_job_plugin: <calc_job_plugin>
        on_computer: true
        computer: <remote computer with Sarus available>
        filepath_executable: <path to executable inside the container>
        image: <image will replace the template of image in engine_command>
        engine_command: sarus run --mount=src=$PWD,dst=/workdir,type=bind --workdir=/rundir {image}
        escape_exec_line: false
        prepend_text: ' '
        append_text: ' '

For the Singularity the ``engine_command`` is ``singularity exec --bind $PWD:$PWD``

Then this code can be used the same way as regular setup code.
There is no need to explicitly imstall or compile the code on the machine, but only require that the executable is in the container shipped with docker image.
For the first time running the docker containerized code, the image will pulled from dockerhub automatically, which will cost sometime if the image is large.

.. important::

    The image need to be exist on the remote computer before you can use them. To install the containerized code just need to pull the image if the it is prepared.
