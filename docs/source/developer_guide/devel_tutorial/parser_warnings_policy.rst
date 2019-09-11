Parser warnings policy
++++++++++++++++++++++

As a rule of thumb, always include two keys in the output parameters of a
calculation, ``warnings`` and ``parser_warnings``. These two keys contain
a list of messages (strings) that are
useful for debugging problems in the execution of calculations.
Below are the guidelines for the usage of the keys
``warnings`` and ``parser_warnings`` in the output parameters of a calculation.

Warnings
--------

These should be devoted to
warnings or error messages relative to the **execution of the code**. As a
(non-exhaustive) list of examples, for Quantum-ESPRESSO, run-time messages such as

  * ``Maximum CPU time exceeded.``
  * ``c_bands:  2 eigenvalues not converged``
  * ``Not enough space allocated for radial FFT``
  * ``The scf cycle did not reach convergence.``
  * ``The FFT is incommensurate: some symmetries may be lost.``
  * ``Error in routine [...]``

should be put in the warnings. In the above cases the warning messages are
directly copied from the output of the code, but a warning can also be
elaborated by the parser when it finds out that something strange went on
during the execution of the code. For QE an example is
``QE pw run did not reach the end of the execution.``

Among the code-based warnings, some can be identified as ''critical'', meaning
that when present the calculation should be set in ``FAILED`` state.
There should be an internal list in the parser, e.g. ``critical_messages``, defining
such critical warnings.
Other non-critical warnings instead might be used to signal the presence of some
possible source of troubles, but that nevertheless did not prevent the calculation
to be considered ``FINISHED``.


Parser_warnings
---------------

These should be reserved to warnings occurring **during parsing**, i.e. when
the parser does not find an information it was looking for in the output files.
For Quantum-ESPRESSO (PW), for instance (implemented in the
`aiida-quantumespresso package <https://github.com/aiidateam/aiida-quantumespresso>`_) examples are

  * ``Skipping the parsing of the xml file.``
  * ``Error while parsing for energy terms.``
  * etc.

Therefore, these warnings should be placed just to notify that the output was
not found in the way the developer had expected, and they signal the necessity
of improving the parser code.