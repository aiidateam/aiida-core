# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
import unittest
import uuid
from aiida.schedulers.datastructures import JobState
from aiida.schedulers.plugins.torque import *

text_qstat_f_to_test = """Job Id: 68350.mycluster
    Job_Name = cell-Qnormal
    Job_Owner = usernum1@mycluster.cluster
    job_state = Q
    queue = Q_express
    server = mycluster
    Checkpoint = u
    ctime = Tue Apr  9 15:01:47 2013
    Error_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTOs
\tcaletest/testjob.err
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = a
    mtime = Mon Apr 22 13:13:53 2013
    Output_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTO
\tscaletest/testjob.out
    Priority = 0
    qtime = Tue Apr  9 18:26:32 2013
    Rerunable = False
    Resource_List.mpiprocs = 15
    Resource_List.ncpus = 240
    Resource_List.nodect = 15
    Resource_List.place = free
    Resource_List.select = 15:ncpus=16
    Resource_List.walltime = 01:00:00
    substate = 10
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
\tPBS_O_HOME=/home/usernum1,PBS_O_LOGNAME=usernum1,
\tPBS_O_WORKDIR=/home/usernum1/scratch/cptest/scaletest/PTOscaletest,
\tPBS_O_LANG=en_US.UTF-8,
\tPBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
\tal/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
\tin:/opt/software/python/3.3.0/bin:/opt/software/bin,
\tPBS_O_MAIL=/var/spool/mail/usernum1,PBS_O_QUEUE=P_share_queue,
\tPBS_O_HOST=mycluster.cluster
    comment = Not Running: Node is in an ineligible state: offline
    etime = Tue Apr  9 18:26:32 2013
    Submit_arguments = job-PTO64cell-Qnormal.6.15.1.64.4
    project = _pbs_project_default

Job Id: 68351.mycluster
    Job_Name = cell-Qnormal
    Job_Owner = usernum1@mycluster.cluster
    job_state = Q
    queue = Q_express
    server = mycluster
    Checkpoint = u
    ctime = Tue Apr  9 15:01:47 2013
    Error_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTOs
\tcaletest/testjob.err
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = a
    mtime = Mon Apr 22 13:13:53 2013
    Output_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTO
\tscaletest/testjob.out
    Priority = 0
    qtime = Tue Apr  9 18:26:32 2013
    Rerunable = False
    Resource_List.mpiprocs = 15
    Resource_List.ncpus = 240
    Resource_List.nodect = 15
    Resource_List.place = free
    Resource_List.select = 15:ncpus=16
    Resource_List.walltime = 01:00:00
    substate = 10
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
\tPBS_O_HOME=/home/usernum1,PBS_O_LOGNAME=usernum1,
\tPBS_O_WORKDIR=/home/usernum1/scratch/cptest/scaletest/PTOscaletest,
\tPBS_O_LANG=en_US.UTF-8,
\tPBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
\tal/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
\tin:/opt/software/python/3.3.0/bin:/opt/software/bin,
\tPBS_O_MAIL=/var/spool/mail/usernum1,PBS_O_QUEUE=P_share_queue,
\tPBS_O_HOST=mycluster.cluster
    comment = Not Running: Node is in an ineligible state: offline
    etime = Tue Apr  9 18:26:32 2013
    Submit_arguments = job-PTO64cell-Qnormal.6.15.1.64.8
    project = _pbs_project_default

Job Id: 69301.mycluster
    Job_Name = Cu-dbp
    Job_Owner = user02@mycluster.cluster
    resources_used.cpupercent = 6384
    resources_used.cput = 4090:56:03
    resources_used.mem = 13378420kb
    resources_used.ncpus = 64
    resources_used.vmem = 9866188kb
    resources_used.walltime = 64:26:16
    job_state = R
    queue = P_lsu
    server = mycluster
    Account_Name = lsu
    Checkpoint = u
    ctime = Wed Apr 10 17:10:29 2013
    depend = afterok:69299.mycluster@mycluster.cluster,
\tbeforeok:69302.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7/C
\tu-dbp.e69301
    exec_host = b141/0*16+b142/0*16+b143/0*16+b144/0*16
    exec_vnode = (b141:ncpus=16)+(b142:ncpus=16)+(b143:ncpus=16)+(b144:ncpus=16
\t)
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = a
    mtime = Sat Apr 20 01:37:01 2013
    Output_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7/
\tCu-dbp.o69301
    Priority = 0
    qtime = Wed Apr 10 17:10:29 2013
    Rerunable = False
    Resource_List.mpiprocs = 4
    Resource_List.ncpus = 64
    Resource_List.nodect = 4
    Resource_List.place = excl
    Resource_List.select = 4:ncpus=16
    Resource_List.walltime = 72:00:00
    stime = Sat Apr 20 01:36:59 2013
    session_id = 118473
    Shell_Path_List = /bin/tcsh
    jobdir = /home/user02
    substate = 42
    Variable_List = SSH_ASKPASS=/usr/libexec/openssh/gnome-ssh-askpass,
\tPERL_BADLANG=0,KDE_IS_PRELINKED=1,PBS_O_HOME=/home/user02,
\tmodule=() {  eval `/usr/bin/modulecmd bash $*`,},
\tLESSOPEN=|/usr/bin/lesspipe.sh %s,PBS_O_LOGNAME=user02,
\tSSH_CLIENT=128.178.54.94 46714 22,CVS_RSH=ssh,PBS_O_LANG=C,USER=user02,
\tHOME=/home/user02,LIBGL_ALWAYS_INDIRECT=yes,
\tPATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/local/bin
\t:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bin:/op
\tt/software/python/3.3.0/bin:/opt/software/bin,
\tLD_LIBRARY_PATH=/opt/software/python/3.3.0/lib,
\tSSH_CONNECTION=128.178.54.94 46714 128.178.209.70 22,LANG=C,
\tQTLIB=/usr/lib64/qt-3.3/lib,TERM=xterm,SHELL=/bin/bash,
\tQTINC=/usr/lib64/qt-3.3/include,G_BROKEN_FILENAMES=1,HISTSIZE=1000,
\tPBS_O_WORKDIR=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,
\tPBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
\tal/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
\tin:/opt/software/python/3.3.0/bin:/opt/software/bin,
\tMANPATH=/opt/xcat/share/man:,XCATROOT=/opt/xcat,
\tMODULESHOME=/usr/share/Modules,PBS_O_SYSTEM=Linux,MSM_PRODUCT=MSM,
\tHOST=mycluster,MAIL=/var/spool/mail/user02,
\tPBS_O_MAIL=/var/spool/mail/user02,_=/opt/pbs/default/bin/qsub,
\tMODULEPATH=/etc/modulefiles:/opt/software/modulefiles:/opt/software/cs
\te-software/modulefiles,KDEDIRS=/usr,PBS_O_SHELL=/bin/bash,
\tSSH_TTY=/dev/pts/55,OLDPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN6,
\tLOADEDMODULES=,HISTCONTROL=ignoredups,SHLVL=1,
\tPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,HOSTNAME=mycluster,
\tMSM_HOME=/usr/local/MegaRAID Storage Manager,LOGNAME=user02,
\tPBS_O_HOST=mycluster.cluster
    comment = Job run at Sat Apr 20 at 01:36 on (b141:ncpus=16)+(b142:ncpus=16)
\t+(b143:ncpus=16)+(b144:ncpus=16)
    etime = Sat Apr 20 01:36:59 2013
    Submit_arguments = job.sh
    project = _pbs_project_default

Job Id: 69302.mycluster
    Job_Name = Cu-dbp
    Job_Owner = user02@mycluster.cluster
    job_state = H
    queue = P_lsu
    server = mycluster
    Account_Name = lsu
    Checkpoint = u
    ctime = Wed Apr 10 17:11:21 2013
    depend = afterok:69301.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8/C
\tu-dbp.e69302
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = a
    mtime = Wed Apr 10 17:11:21 2013
    Output_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8/
\tCu-dbp.o69302
    Priority = 0
    qtime = Wed Apr 10 17:11:21 2013
    Rerunable = False
    Resource_List.mpiprocs = 4
    Resource_List.ncpus = 64
    Resource_List.nodect = 4
    Resource_List.place = excl
    Resource_List.select = 4:ncpus=16
    Resource_List.walltime = 72:00:00
    Shell_Path_List = /bin/tcsh
    substate = 22
    Variable_List = SSH_ASKPASS=/usr/libexec/openssh/gnome-ssh-askpass,
\tPERL_BADLANG=0,KDE_IS_PRELINKED=1,PBS_O_HOME=/home/user02,
\tmodule=() {  eval `/usr/bin/modulecmd bash $*`,},
\tLESSOPEN=|/usr/bin/lesspipe.sh %s,PBS_O_LOGNAME=user02,
\tSSH_CLIENT=128.178.54.94 46714 22,CVS_RSH=ssh,PBS_O_LANG=C,USER=user02,
\tHOME=/home/user02,LIBGL_ALWAYS_INDIRECT=yes,
\tPATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/local/bin
\t:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bin:/op
\tt/software/python/3.3.0/bin:/opt/software/bin,
\tLD_LIBRARY_PATH=/opt/software/python/3.3.0/lib,
\tSSH_CONNECTION=128.178.54.94 46714 128.178.209.70 22,LANG=C,
\tQTLIB=/usr/lib64/qt-3.3/lib,TERM=xterm,SHELL=/bin/bash,
\tQTINC=/usr/lib64/qt-3.3/include,G_BROKEN_FILENAMES=1,HISTSIZE=1000,
\tPBS_O_WORKDIR=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8,
\tPBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
\tal/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
\tin:/opt/software/python/3.3.0/bin:/opt/software/bin,
\tMANPATH=/opt/xcat/share/man:,XCATROOT=/opt/xcat,
\tMODULESHOME=/usr/share/Modules,PBS_O_SYSTEM=Linux,MSM_PRODUCT=MSM,
\tHOST=mycluster,MAIL=/var/spool/mail/user02,
\tPBS_O_MAIL=/var/spool/mail/user02,_=/opt/pbs/default/bin/qsub,
\tMODULEPATH=/etc/modulefiles:/opt/software/modulefiles:/opt/software/cs
\te-software/modulefiles,KDEDIRS=/usr,PBS_O_SHELL=/bin/bash,
\tSSH_TTY=/dev/pts/55,OLDPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,
\tLOADEDMODULES=,HISTCONTROL=ignoredups,SHLVL=1,
\tPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8,HOSTNAME=mycluster,
\tMSM_HOME=/usr/local/MegaRAID Storage Manager,LOGNAME=user02,
\tPBS_O_HOST=mycluster.cluster
    Submit_arguments = job.sh
    project = _pbs_project_default

Job Id: 74164.mycluster
    Job_Name = u-100-l-96.job
    Job_Owner = user3@mycluster.cluster
    resources_used.cpupercent = 3889
    resources_used.cput = 343:11:42
    resources_used.mem = 1824176kb
    resources_used.ncpus = 32
    resources_used.vmem = 3796376kb
    resources_used.walltime = 10:45:13
    job_state = R
    queue = Q_normal
    server = mycluster
    Checkpoint = u
    ctime = Fri Apr 12 15:21:55 2013
    depend = afterany:74163.mycluster@mycluster.cluster,
\tbeforeany:74165.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-from
\t-left/production/u-100-l-96.job.e74164
    exec_host = b270/0*16+b275/0*16
    exec_vnode = (b270:ncpus=16)+(b275:ncpus=16)
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = enrico.user3@epfl.ch
    mtime = Mon Apr 22 07:17:36 2013
    Output_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-fro
\tm-left/production/u-100-l-96.job.o74164
    Priority = 0
    qtime = Fri Apr 12 15:21:55 2013
    Rerunable = False
    Resource_List.mpiprocs = 32
    Resource_List.ncpus = 32
    Resource_List.nodect = 2
    Resource_List.place = excl
    Resource_List.select = 2:ncpus=16:mpiprocs=16
    Resource_List.walltime = 24:00:00
    stime = Mon Apr 22 07:17:36 2013
    session_id = 14147
    jobdir = /home/user3
    substate = 42
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
\tPBS_O_HOME=/home/user3,PBS_O_LOGNAME=user3,
\tPBS_O_WORKDIR=/scratch/user3/ubiquitin/100gL/starting-from-left/produc
\ttion,PBS_O_LANG=en_US.utf8,
\tPBS_O_PATH=/opt/pbs/default/sbin/:/home/bovigny/bin:/opt/xcat/bin:/opt
\t/xcat/sbin:/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loca
\tl/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bi
\tn:/opt/software/python/3.3.0/bin:/opt/software/bin:/opt/pbs/default/bin
\t:/opt/software/python/3.3.0/bin:/opt/software/bin,
\tPBS_O_MAIL=/var/spool/mail/user3,PBS_O_QUEUE=P_share_queue,
\tPBS_O_HOST=mycluster.cluster
    comment = Job run at Mon Apr 22 at 07:17 on (b270:ncpus=16)+(b275:ncpus=16)

    etime = Mon Apr 22 07:17:34 2013
    Submit_arguments = -W depend=afterany:74163 u-100-l-96.job
    project = _pbs_project_default

Job Id: 74165.mycluster
    Job_Name = u-100-l-97.job
    Job_Owner = user3@mycluster.cluster
    job_state = H
    queue = Q_normal
    server = mycluster
    Checkpoint = u
    ctime = Fri Apr 12 15:22:01 2013
    depend = afterany:74164.mycluster@mycluster.cluster,
\tbeforeany:74166.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-from
\t-left/production/u-100-l-97.job.e74165
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = enrico.user3@epfl.ch
    mtime = Fri Apr 12 15:22:07 2013
    Output_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-fro
\tm-left/production/u-100-l-97.job.o74165
    Priority = 0
    qtime = Fri Apr 12 15:22:01 2013
    Rerunable = False
    Resource_List.mpiprocs = 32
    Resource_List.ncpus = 32
    Resource_List.nodect = 2
    Resource_List.place = excl
    Resource_List.select = 2:ncpus=16:mpiprocs=16
    Resource_List.walltime = 24:00:00
    substate = 22
    Variable_List = PBS_O_SYSTEM=Linux,PBS_O_SHELL=/bin/bash,
\tPBS_O_HOME=/home/user3,PBS_O_LOGNAME=user3,
\tPBS_O_WORKDIR=/scratch/user3/ubiquitin/100gL/starting-from-left/produc
\ttion,PBS_O_LANG=en_US.utf8,
\tPBS_O_PATH=/opt/pbs/default/sbin/:/home/bovigny/bin:/opt/xcat/bin:/opt
\t/xcat/sbin:/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loca
\tl/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bi
\tn:/opt/software/python/3.3.0/bin:/opt/software/bin:/opt/pbs/default/bin
\t:/opt/software/python/3.3.0/bin:/opt/software/bin,
\tPBS_O_MAIL=/var/spool/mail/user3,PBS_O_QUEUE=P_share_queue,
\tPBS_O_HOST=mycluster.cluster
    Submit_arguments = -W depend=afterany:74164 u-100-l-97.job
    project = _pbs_project_default

"""

## This contains in the 10-th job unexpected newlines
## in the sched_hint field. Still, it should parse correctly.
text_qstat_f_to_test_with_unexpected_newlines = """Job Id: 549159
    Job_Name = somejob
    Job_Owner = user_549159
    job_state = H
    queue = ShortQ
    server = service1
    Account_Name = account_549159
    Checkpoint = u
    ctime = Sun Jun 21 07:09:41 2015
    depend = afterok:549158.service1.head.cb3.ichec.ie@service1.cb3.ichec.ie
    Error_Path = host.domain:/some/path/to/sth/ASSP
\t-1R-p/more/down/the/path/ASSP
\t-1R.e549159
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    Mail_Users = usermail@domain1
    mtime = Sun Jun 21 07:09:41 2015
    Output_Path = host.domain:/some/path/to/sth/GL
\tmore/down/the/path/ASS
\tP-1R.o549159
    Priority = 0
    qtime = Sun Jun 21 07:09:41 2015
    Rerunable = False
    Resource_List.nodect = 4
    Resource_List.nodes = 4:ppn=24
    Resource_List.walltime = 09:00:00
    euser = user_549159
    egroup = users
    queue_type = E
    submit_args = -W depend=afterok:549158 somejob.pbs
    fault_tolerant = False
    job_radix = 0
    submit_host = host.domain1

Job Id: 555716
    Job_Name = ini_J2
    Job_Owner = somebody@host.domain
    resources_used.cput = 500:13:39
    resources_used.energy_used = 0
    resources_used.mem = 20716400kb
    resources_used.vmem = 23534576kb
    resources_used.walltime = 41:45:13
    job_state = R
    queue = ProdQ
    server = service1
    Account_Name = dias01
    Checkpoint = u
    ctime = Fri Jun 26 14:04:56 2015
    Error_Path = host:/down/the/path/test
\t_valg.out
    exec_host = r2i4n13/0-23+r1i2n12/0-23+r1i2n11/0-23+r1i1n15/0-23
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    Mail_Users = usermail@mail.domain
    mtime = Sun Jun 28 23:20:51 2015
    Output_Path = host:/down/the/path/tes
\tt_valg.out
    Priority = 0
    qtime = Fri Jun 26 14:04:56 2015
    Rerunable = False
    Resource_List.nodect = 4
    Resource_List.nodes = 4:ppn=24
    Resource_List.walltime = 70:00:00
    session_id = 21190
    euser = somebody
    egroup = users
    queue_type = E
    etime = Fri Jun 26 14:04:56 2015
    submit_args = runmem_CB_E
    start_time = Sun Jun 28 23:20:51 2015
    Walltime.Remaining = 101627
    start_count = 1
    fault_tolerant = False
    job_radix = 0
    submit_host = host.domain

Job Id: 556491
    Job_Name = somejob010
    Job_Owner = user_556491
    resources_used.cput = 1850:10:45
    resources_used.energy_used = 0
    resources_used.mem = 50392860kb
    resources_used.vmem = 77507412kb
    resources_used.walltime = 78:21:43
    job_state = R
    queue = LongQ
    server = service1
    Account_Name = some432472
    Checkpoint = u
    ctime = Sat Jun 27 10:44:32 2015
    Error_Path = host:/down/teh/path/ATc
\tT/somejob010.e556491
    exec_host = r3i1n2/0-23
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = ea
    Mail_Users = user@mail
    mtime = Sat Jun 27 10:45:06 2015
    Output_Path = host;/down/the/path/AT
\tcT/somejob-010.o556491
    Priority = 0
    qtime = Sat Jun 27 10:44:32 2015
    Rerunable = False
    Resource_List.nodect = 1
    Resource_List.nodes = 1:ppn=24
    Resource_List.walltime = 144:00:00
    session_id = 28668
    euser = user_556491
    egroup = users
    queue_type = E
    etime = Sat Jun 27 10:44:32 2015
    submit_args = scriptname.pbs
    start_time = Sat Jun 27 10:45:06 2015
    Walltime.Remaining = 236282
    start_count = 1
    fault_tolerant = False
    job_radix = 0
    submit_host = host.domain

Job Id: 546437
    Job_Name = job_546437
    Job_Owner = user_546437
    resources_used.cput = 146:03:05
    resources_used.energy_used = 0
    resources_used.mem = 4199416kb
    resources_used.vmem = 10804052kb
    resources_used.walltime = 06:12:22
    job_state = C
    queue = ShortQ
    server = server.service.546437
    Account_Name = account_546437
    Checkpoint = u
    ctime = Thu Jun 18 16:10:46 2015
    depend = beforeok:546438@service1
    Error_Path = server.domain:/path/to/error/file
\t-1R-p/more/down/the/path/GLP
\t-1R.e546437
    exec_host = r2i7n16/0-23+r2i6n14/0-23+r2i6n1/0-23+r1i7n8/0-23
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    Mail_Users = usermail_546437@domain.546437
    mtime = Thu Jun 18 22:36:03 2015
    Output_Path = server.domain:/path/to/output/file
\tsomething2/more/down/the/path/GL
\tP-1R.o546437
    Priority = 0
    qtime = Thu Jun 18 16:10:46 2015
    Rerunable = False
    Resource_List.nodect = 4
    Resource_List.nodes = 4:ppn=24
    Resource_List.walltime = 08:00:00
    session_id = 7054
    euser = user_546437
    egroup = group_546437
    queue_type = E
    etime = Thu Jun 18 16:10:46 2015
    exit_status = 271
    submit_args = args_546437.ext
    start_time = Thu Jun 18 16:23:35 2015
    start_count = 1
    fault_tolerant = False
    job_radix = 0
    submit_host = host_546437.domain

Job Id: 547637
    Job_Name = job_546437
    Job_Owner = user_546437
    job_state = Q
    queue = ShortQ
    server = server.service.546437
    Account_Name = account_546437
    Checkpoint = u
    ctime = Fri Jun 19 14:00:43 2015
    Error_Path = server.domain:/path/to/error/file

    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    Mail_Users = usermail_546437@domain.546437
    mtime = Fri Jun 19 14:00:43 2015
    Output_Path = server.domain:/path/to/output/file
\t7
    Priority = 0
    qtime = Fri Jun 19 14:00:43 2015
    Rerunable = False
    Resource_List.nodect = 1
    Resource_List.nodes = 1:ppn=24
    Resource_List.walltime = 24:00:00
    euser = user_546437
    egroup = group_546437
    queue_type = E
    etime = Fri Jun 19 14:00:43 2015
    submit_args = args_546437.ext
    fault_tolerant = False
    job_radix = 0
    submit_host = host_546437.domain

Job Id: 547683
    Job_Name = job_547683
    Job_Owner = user_547683
    job_state = Q
    queue = ShortQ
    server = server.service.547683
    Account_Name = account_547683
    Checkpoint = u
    ctime = Fri Jun 19 14:58:08 2015
    Error_Path = server.domain:/path/to/error/file
\t83
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = ea
    Mail_Users = usermail_547683@domain.547683
    mtime = Fri Jun 19 14:58:08 2015
    Output_Path = server.domain:/path/to/output/file
\t683
    Priority = 0
    qtime = Fri Jun 19 14:58:08 2015
    Rerunable = False
    Resource_List.nodect = 1
    Resource_List.nodes = 1:ppn=24
    Resource_List.walltime = 23:30:00
    euser = user_547683
    egroup = group_547683
    queue_type = E
    etime = Fri Jun 19 14:58:08 2015
    submit_args = args_547683.ext
    fault_tolerant = False
    job_radix = 0
    submit_host = host_547683.domain

Job Id: 549004
    Job_Name = job_549004
    Job_Owner = user_549004
    job_state = Q
    queue = ProdQ
    server = server.service.549004
    Account_Name = account_549004
    Checkpoint = u
    ctime = Sat Jun 20 21:25:20 2015
    Error_Path = server.domain:/path/to/error/file
\t_something1_202.e549004
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    mtime = Sat Jun 20 21:25:20 2015
    Output_Path = server.domain:/path/to/output/file
\tw_something1_202.o549004
    Priority = 0
    qtime = Sat Jun 20 21:25:20 2015
    Rerunable = False
    Resource_List.nodect = 1
    Resource_List.nodes = 1:ppn=24
    Resource_List.walltime = 48:00:00
    euser = user_549004
    egroup = group_549004
    queue_type = E
    etime = Sat Jun 20 21:25:20 2015
    submit_args = args_549004ext
    fault_tolerant = False
    job_radix = 0
    submit_host = host_549004.domain

Job Id: 549005
    Job_Name = job_549004
    Job_Owner = user_549004
    job_state = Q
    queue = ProdQ
    server = server.service.549004
    Account_Name = account_549004
    Checkpoint = u
    ctime = Sat Jun 20 21:25:24 2015
    Error_Path = server.domain:/path/to/error/file
\t_something1_102.e549005
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    mtime = Sat Jun 20 21:25:24 2015
    Output_Path = server.domain:/path/to/output/file
\tw_something1_102.o549005
    Priority = 0
    qtime = Sat Jun 20 21:25:24 2015
    Rerunable = False
    Resource_List.nodect = 1
    Resource_List.nodes = 1:ppn=24
    Resource_List.walltime = 48:00:00
    euser = user_549004
    egroup = group_549004
    queue_type = E
    etime = Sat Jun 20 21:25:24 2015
    submit_args = args_549004.ext
    fault_tolerant = False
    job_radix = 0
    submit_host = host_549004.domain

Job Id: 549008
    Job_Name = job_549008
    Job_Owner = user_549008
    job_state = Q
    queue = ProdQ
    server = server.service.549008
    Account_Name = account_549008
    Checkpoint = u
    ctime = Sat Jun 20 21:25:39 2015
    Error_Path = server.domain:/path/to/error/file
\tsomething1_102.e549008
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = bea
    mtime = Sat Jun 20 21:25:39 2015
    Output_Path = server.domain:/path/to/output/file
\t_something1_102.o549008
    Priority = 0
    qtime = Sat Jun 20 21:25:39 2015
    Rerunable = False
    Resource_List.nodect = 1
    Resource_List.nodes = 1:ppn=24
    Resource_List.walltime = 48:00:00
    euser = user_549008
    egroup = group_549008
    queue_type = E
    etime = Sat Jun 20 21:25:39 2015
    submit_args = args_549008.ext
    fault_tolerant = False
    job_radix = 0
    submit_host = host_549008.domain

Job Id: 543984
    Job_Name = job_543984
    Job_Owner = user_543984
    resources_used.cput = 641:36:16
    resources_used.energy_used = 0
    resources_used.mem = 3815752kb
    resources_used.vmem = 12122136kb
    resources_used.walltime = 35:47:31
    job_state = C
    queue = ProdQ
    server = server.service.543984
    Account_Name = account_543984
    Checkpoint = u
    ctime = Wed Jun 17 09:16:05 2015
    depend = beforeany:545943@service1
    Error_Path = server.domain:/path/to/error/file
\tP_Mp=318.,NVF=1e5,tau=0.10,ddZ,AD,1T,iFlr,xyz.e543984
    exec_host = r2i7n17/0-23+r2i0n11/0-23+r2i6n17/0-23+r2i0n5/0-23+r2i7n1/0-23
\t+r2i5n8/0-23+r2i4n11/0-23+r2i4n8/0-23+r2i2n8/0-23+r2i0n2/0-23+r2i3n16/
\t0-23+r2i3n2/0-23+r2i1n2/0-23+r2i4n3/0-23+r2i1n15/0-23+r2i1n9/0-23+r2i2
\tn2/0-23+r2i3n8/0-23+r2i3n5/0-23+r2i1n11/0-23+r2i0n16/0-23+r2i2n5/0-23
\tr2i1n3/0-23+r2i0n17/0-23+r2i0n8/0-23+r1i3n0/0-23+r1i7n7/0-23+r1i6n1/0-
\t23+r1i7n3/0-23+r1i7n5/0-23+r1i6n17/0-23+r1i7n4/0-23
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = n
    Mail_Users = usermail_543984@domain.543984
    mtime = Thu Jun 18 22:36:12 2015
    Output_Path = server.domain:/path/to/output/file
\tEP_Mp=318.,NVF=1e5,tau=0.10,ddZ,AD,1T,iFlr,xyz.o543984
    Priority = 0
    qtime = Wed Jun 17 09:16:05 2015
    Rerunable = False
    Resource_List.nodect = 32
    Resource_List.nodes = 32:ppn=24
    Resource_List.walltime = 71:59:59
    session_id = 47630
    euser = user_543984
    egroup = group_543984
    queue_type = E
    sched_hint = Post job file processing error; job 543984 on host r2i7n17

U
\tnable to copy file 543984.OU to /some/path/on/the/cluster/MHD
\tsomething_Mp=318.,NVF=1e5,tau=0.10,ddZ,AD,1T,iFlr,xyz.o543984,
\t error 1
*** error from copy
/bin/cp: cannot stat `543984.OU': No suc
\th file or directory
*** end error output

Unable to copy file 543984.E
\tR to /some/path/on/the/cluster/something_Mp=318.,
\tNVF=1e5,tau=0.10,ddZ,AD,1T,iFlr,xyz.e543984,
\t error 1
*** error from copy
/bin/cp: cannot stat `543984.ER': No suc
\th file or directory
*** end error output
    etime = Wed Jun 17 09:16:05 2015
    exit_status = 271
    submit_args = args_XX.ext
\txyz -l nodes=32:ppn=24,walltime=71:59:59 -v RESUME=true,SMP=24,
\tNND=32,
\tNOPFS=false -d /some/path/ /some/other/pa
\tth/NIx/que/runN.sth
    start_time = Wed Jun 17 10:48:24 2015
    start_count = 1
    fault_tolerant = False
    job_radix = 0
    submit_host = host_XX.domain
"""


class TestParserQstat(unittest.TestCase):
    """
    Tests to verify if teh function _parse_joblist_output behave correctly
    The tests is done parsing a string defined above, to be used offline
    """

    def test_parse_common_joblist_output(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        """
        s = TorqueScheduler()

        retval = 0
        stdout = text_qstat_f_to_test
        stderr = ''

        job_list = s._parse_joblist_output(retval, stdout, stderr)

        # The parameters are hard coded in the text to parse
        job_on_cluster = 6
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)

        job_running = 2
        job_running_parsed = len([j for j in job_list if j.job_state \
                                  and j.job_state == JobState.RUNNING])
        self.assertEquals(job_running, job_running_parsed)

        job_held = 2
        job_held_parsed = len([j for j in job_list if j.job_state \
                               and j.job_state == JobState.QUEUED_HELD])
        self.assertEquals(job_held, job_held_parsed)

        job_queued = 2
        job_queued_parsed = len([j for j in job_list if j.job_state \
                                 and j.job_state == JobState.QUEUED])
        self.assertEquals(job_queued, job_queued_parsed)

        running_users = ['user02', 'user3']
        parsed_running_users = [j.job_owner for j in job_list if j.job_state \
                                and j.job_state == JobState.RUNNING]
        self.assertEquals(set(running_users), set(parsed_running_users))

        running_jobs = ['69301.mycluster', '74164.mycluster']
        parsed_running_jobs = [j.job_id for j in job_list if j.job_state \
                               and j.job_state == JobState.RUNNING]
        self.assertEquals(set(running_jobs), set(parsed_running_jobs))

        for j in job_list:
            if j.allocated_machines:
                num_machines = 0
                num_cpus = 0
                for n in j.allocated_machines:
                    num_machines += 1
                    num_cpus += n.num_cpus

                self.assertTrue(j.num_machines == num_machines)
                self.assertTrue(j.num_cpus == num_cpus)
                # TODO : parse the env_vars

    def test_parse_with_unexpected_newlines(self):
        """
        Test whether _parse_joblist can parse the qstat -f output
        also when there are unexpected newlines
        """
        s = TorqueScheduler()

        retval = 0
        stdout = text_qstat_f_to_test_with_unexpected_newlines
        stderr = ''

        job_list = s._parse_joblist_output(retval, stdout, stderr)

        # The parameters are hard coded in the text to parse
        job_on_cluster = 10
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)

        job_running = 2
        job_running_parsed = len([j for j in job_list if j.job_state \
                                  and j.job_state == JobState.RUNNING])
        self.assertEquals(job_running, job_running_parsed)

        job_held = 1
        job_held_parsed = len([j for j in job_list if j.job_state \
                               and j.job_state == JobState.QUEUED_HELD])
        self.assertEquals(job_held, job_held_parsed)

        job_queued = 5
        job_queued_parsed = len([j for j in job_list if j.job_state \
                                 and j.job_state == JobState.QUEUED])
        self.assertEquals(job_queued, job_queued_parsed)

        running_users = ['somebody', 'user_556491']
        parsed_running_users = [j.job_owner for j in job_list if j.job_state \
                                and j.job_state == JobState.RUNNING]
        self.assertEquals(set(running_users), set(parsed_running_users))

        running_jobs = ['555716', '556491']
        parsed_running_jobs = [j.job_id for j in job_list if j.job_state \
                               and j.job_state == JobState.RUNNING]
        self.assertEquals(set(running_jobs), set(parsed_running_jobs))

        for j in job_list:
            if j.allocated_machines:
                num_machines = 0
                num_cpus = 0
                for n in j.allocated_machines:
                    num_machines += 1
                    num_cpus += n.num_cpus

                self.assertTrue(j.num_machines == num_machines)
                self.assertTrue(j.num_cpus == num_cpus)
                # TODO : parse the env_vars


class TestSubmitScript(unittest.TestCase):

    def test_submit_script(self):
        """
        Test to verify if scripts works fine with default options
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        s = TorqueScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = s.create_job_resource(num_machines=1, num_mpiprocs_per_machine=1)
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = s.get_submit_script(job_tmpl)

        self.assertTrue('#PBS -r n' in submit_script_text)
        self.assertTrue(submit_script_text.startswith('#!/bin/bash'))
        self.assertTrue('#PBS -l nodes=1:ppn=1,walltime=24:00:00' in submit_script_text)
        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                        " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_machine(self):
        """
        Test to verify if script works fine if we specify only
        num_cores_per_machine value.
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        s = TorqueScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = s.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24)
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = s.get_submit_script(job_tmpl)

        self.assertTrue('#PBS -r n' in submit_script_text)
        self.assertTrue(submit_script_text.startswith('#!/bin/bash'))
        self.assertTrue('#PBS -l nodes=1:ppn=24,walltime=24:00:00' in submit_script_text)
        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_mpiproc(self):
        """
        Test to verify if scripts works fine if we pass only
        num_cores_per_mpiproc value
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = TorqueScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_mpiproc=24)
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        self.assertTrue('#PBS -r n' in submit_script_text)
        self.assertTrue(submit_script_text.startswith('#!/bin/bash'))
        self.assertTrue('#PBS -l nodes=1:ppn=24,walltime=24:00:00' in submit_script_text)
        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_machine_and_mpiproc1(self):
        """
        Test to verify if scripts works fine if we pass both
        num_cores_per_machine and num_cores_per_mpiproc correct values
        It should pass in check:
        res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine
        """
        from aiida.schedulers.datastructures import JobTemplate
        from aiida.common.datastructures import CodeInfo, CodeRunMode

        scheduler = TorqueScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.shebang = '#!/bin/bash'
        job_tmpl.job_resource = scheduler.create_job_resource(
            num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24, num_cores_per_mpiproc=24)
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.max_wallclock_seconds = 24 * 3600
        code_info = CodeInfo()
        code_info.cmdline_params = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
        code_info.stdin_name = 'aiida.in'
        job_tmpl.codes_info = [code_info]
        job_tmpl.codes_run_mode = CodeRunMode.SERIAL

        submit_script_text = scheduler.get_submit_script(job_tmpl)

        self.assertTrue('#PBS -r n' in submit_script_text)
        self.assertTrue(submit_script_text.startswith('#!/bin/bash'))
        self.assertTrue('#PBS -l nodes=1:ppn=24,walltime=24:00:00' in submit_script_text)
        self.assertTrue("'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + " < 'aiida.in'" in submit_script_text)

    def test_submit_script_with_num_cores_per_machine_and_mpiproc2(self):
        """
        Test to verify if scripts works fine if we pass
        num_cores_per_machine and num_cores_per_mpiproc wrong values
        It should fail in check:
        res.num_cores_per_mpiproc * res.num_mpiprocs_per_machine = res.num_cores_per_machine
        """
        from aiida.schedulers.datastructures import JobTemplate

        scheduler = TorqueScheduler()

        job_tmpl = JobTemplate()
        with self.assertRaises(ValueError):
            job_tmpl.job_resource = scheduler.create_job_resource(
                num_machines=1, num_mpiprocs_per_machine=1, num_cores_per_machine=24, num_cores_per_mpiproc=23)
