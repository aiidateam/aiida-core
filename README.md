This directory contains the files involved in the calculation/workflow
`ArithmeticAddCalculation <4>` run with AiiDA.

Child calculations/workflows (also called `CalcJob`s/`CalcFunction`s and `WorkChain`s/`WorkFunction`s in AiiDA
jargon) run by the parent workflow are contained in the directory tree as sub-folders and are sorted by their
creation time. The directory tree thus mirrors the logical execution of the workflow, which can also be queried
by running `verdi process status 4` on the command line.

By default, input and output files of each calculation can be found in the corresponding "inputs" and "outputs"
directories (the former also contains the hidden ".aiida" folder with machine-readable job execution settings).
Additional input and output files (depending on the type of calculation) are placed in the "node_inputs" and
"node_outputs", respectively.

Lastly, every folder also contains a hidden, human-readable `.aiida_node_metadata.yaml` file with the relevant
AiiDA node data for further inspection.


Output of `verdi process status 4`:

```shell
ArithmeticAddCalculation<4> Finished [0]
```


Output of `verdi process report 4`:

```shell
*** 4: None
*** (empty scheduler output file)
*** (empty scheduler errors file)
*** 0 LOG MESSAGES
```


Output of `verdi process show 4`:

```shell
Property     Value
-----------  ------------------------------------
type         ArithmeticAddCalculation
state        Finished [0]
pk           4
uuid         59bd82f7-5740-40fe-b937-b9ada2d71209
label
description
ctime        2024-11-04 14:49:21.356112+01:00
mtime        2024-11-04 14:49:22.888647+01:00
computer     [1] localhost

Inputs      PK  Type
--------  ----  -------------
code         1  InstalledCode
x            2  Int
y            3  Int

Outputs          PK  Type
-------------  ----  ----------
remote_folder     5  RemoteData
retrieved         6  FolderData
sum               7  Int
```
