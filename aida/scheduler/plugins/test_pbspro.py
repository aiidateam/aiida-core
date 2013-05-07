from aida.scheduler.plugins.pbspro import *
import unittest
import logging
import uuid
        
text_qstat_f_to_test = """Job Id: 68350.mycluster
    Job_Name = cell-Qnormal
    Job_Owner = usernum1@mycluster.cluster
    job_state = Q
    queue = Q_express
    server = mycluster
    Checkpoint = u
    ctime = Tue Apr  9 15:01:47 2013
    Error_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTOs
	caletest/testjob.err
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = a
    mtime = Mon Apr 22 13:13:53 2013
    Output_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTO
	scaletest/testjob.out
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
	PBS_O_HOME=/home/usernum1,PBS_O_LOGNAME=usernum1,
	PBS_O_WORKDIR=/home/usernum1/scratch/cptest/scaletest/PTOscaletest,
	PBS_O_LANG=en_US.UTF-8,
	PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
	al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
	in:/opt/software/python/3.3.0/bin:/opt/software/bin,
	PBS_O_MAIL=/var/spool/mail/usernum1,PBS_O_QUEUE=P_share_queue,
	PBS_O_HOST=mycluster.cluster
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
	caletest/testjob.err
    Hold_Types = n
    Join_Path = n
    Keep_Files = n
    Mail_Points = a
    mtime = Mon Apr 22 13:13:53 2013
    Output_Path = mycluster.cluster:/home/usernum1/scratch/cptest/scaletest/PTO
	scaletest/testjob.out
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
	PBS_O_HOME=/home/usernum1,PBS_O_LOGNAME=usernum1,
	PBS_O_WORKDIR=/home/usernum1/scratch/cptest/scaletest/PTOscaletest,
	PBS_O_LANG=en_US.UTF-8,
	PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
	al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
	in:/opt/software/python/3.3.0/bin:/opt/software/bin,
	PBS_O_MAIL=/var/spool/mail/usernum1,PBS_O_QUEUE=P_share_queue,
	PBS_O_HOST=mycluster.cluster
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
	beforeok:69302.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7/C
	u-dbp.e69301
    exec_host = b141/0*16+b142/0*16+b143/0*16+b144/0*16
    exec_vnode = (b141:ncpus=16)+(b142:ncpus=16)+(b143:ncpus=16)+(b144:ncpus=16
	)
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = a
    mtime = Sat Apr 20 01:37:01 2013
    Output_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7/
	Cu-dbp.o69301
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
	PERL_BADLANG=0,KDE_IS_PRELINKED=1,PBS_O_HOME=/home/user02,
	module=() {  eval `/usr/bin/modulecmd bash $*`,},
	LESSOPEN=|/usr/bin/lesspipe.sh %s,PBS_O_LOGNAME=user02,
	SSH_CLIENT=128.178.54.94 46714 22,CVS_RSH=ssh,PBS_O_LANG=C,USER=user02,
	HOME=/home/user02,LIBGL_ALWAYS_INDIRECT=yes,
	PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/local/bin
	:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bin:/op
	t/software/python/3.3.0/bin:/opt/software/bin,
	LD_LIBRARY_PATH=/opt/software/python/3.3.0/lib,
	SSH_CONNECTION=128.178.54.94 46714 128.178.209.70 22,LANG=C,
	QTLIB=/usr/lib64/qt-3.3/lib,TERM=xterm,SHELL=/bin/bash,
	QTINC=/usr/lib64/qt-3.3/include,G_BROKEN_FILENAMES=1,HISTSIZE=1000,
	PBS_O_WORKDIR=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,
	PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
	al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
	in:/opt/software/python/3.3.0/bin:/opt/software/bin,
	MANPATH=/opt/xcat/share/man:,XCATROOT=/opt/xcat,
	MODULESHOME=/usr/share/Modules,PBS_O_SYSTEM=Linux,MSM_PRODUCT=MSM,
	HOST=mycluster,MAIL=/var/spool/mail/user02,
	PBS_O_MAIL=/var/spool/mail/user02,_=/opt/pbs/default/bin/qsub,
	MODULEPATH=/etc/modulefiles:/opt/software/modulefiles:/opt/software/cs
	e-software/modulefiles,KDEDIRS=/usr,PBS_O_SHELL=/bin/bash,
	SSH_TTY=/dev/pts/55,OLDPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN6,
	LOADEDMODULES=,HISTCONTROL=ignoredups,SHLVL=1,
	PWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,HOSTNAME=mycluster,
	MSM_HOME=/usr/local/MegaRAID Storage Manager,LOGNAME=user02,
	PBS_O_HOST=mycluster.cluster
    comment = Job run at Sat Apr 20 at 01:36 on (b141:ncpus=16)+(b142:ncpus=16)
	+(b143:ncpus=16)+(b144:ncpus=16)
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
	u-dbp.e69302
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = a
    mtime = Wed Apr 10 17:11:21 2013
    Output_Path = mycluster.cluster:/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8/
	Cu-dbp.o69302
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
	PERL_BADLANG=0,KDE_IS_PRELINKED=1,PBS_O_HOME=/home/user02,
	module=() {  eval `/usr/bin/modulecmd bash $*`,},
	LESSOPEN=|/usr/bin/lesspipe.sh %s,PBS_O_LOGNAME=user02,
	SSH_CLIENT=128.178.54.94 46714 22,CVS_RSH=ssh,PBS_O_LANG=C,USER=user02,
	HOME=/home/user02,LIBGL_ALWAYS_INDIRECT=yes,
	PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/local/bin
	:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bin:/op
	t/software/python/3.3.0/bin:/opt/software/bin,
	LD_LIBRARY_PATH=/opt/software/python/3.3.0/lib,
	SSH_CONNECTION=128.178.54.94 46714 128.178.209.70 22,LANG=C,
	QTLIB=/usr/lib64/qt-3.3/lib,TERM=xterm,SHELL=/bin/bash,
	QTINC=/usr/lib64/qt-3.3/include,G_BROKEN_FILENAMES=1,HISTSIZE=1000,
	PBS_O_WORKDIR=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8,
	PBS_O_PATH=/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loc
	al/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/b
	in:/opt/software/python/3.3.0/bin:/opt/software/bin,
	MANPATH=/opt/xcat/share/man:,XCATROOT=/opt/xcat,
	MODULESHOME=/usr/share/Modules,PBS_O_SYSTEM=Linux,MSM_PRODUCT=MSM,
	HOST=mycluster,MAIL=/var/spool/mail/user02,
	PBS_O_MAIL=/var/spool/mail/user02,_=/opt/pbs/default/bin/qsub,
	MODULEPATH=/etc/modulefiles:/opt/software/modulefiles:/opt/software/cs
	e-software/modulefiles,KDEDIRS=/usr,PBS_O_SHELL=/bin/bash,
	SSH_TTY=/dev/pts/55,OLDPWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN7,
	LOADEDMODULES=,HISTCONTROL=ignoredups,SHLVL=1,
	PWD=/scratch/user02/QMMM-CuPhens/dbp/NOSE/RUN8,HOSTNAME=mycluster,
	MSM_HOME=/usr/local/MegaRAID Storage Manager,LOGNAME=user02,
	PBS_O_HOST=mycluster.cluster
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
	beforeany:74165.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-from
	-left/production/u-100-l-96.job.e74164
    exec_host = b270/0*16+b275/0*16
    exec_vnode = (b270:ncpus=16)+(b275:ncpus=16)
    Hold_Types = n
    Join_Path = oe
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = enrico.user3@epfl.ch
    mtime = Mon Apr 22 07:17:36 2013
    Output_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-fro
	m-left/production/u-100-l-96.job.o74164
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
	PBS_O_HOME=/home/user3,PBS_O_LOGNAME=user3,
	PBS_O_WORKDIR=/scratch/user3/ubiquitin/100gL/starting-from-left/produc
	tion,PBS_O_LANG=en_US.utf8,
	PBS_O_PATH=/opt/pbs/default/sbin/:/home/bovigny/bin:/opt/xcat/bin:/opt
	/xcat/sbin:/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loca
	l/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bi
	n:/opt/software/python/3.3.0/bin:/opt/software/bin:/opt/pbs/default/bin
	:/opt/software/python/3.3.0/bin:/opt/software/bin,
	PBS_O_MAIL=/var/spool/mail/user3,PBS_O_QUEUE=P_share_queue,
	PBS_O_HOST=mycluster.cluster
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
	beforeany:74166.mycluster@mycluster.cluster
    Error_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-from
	-left/production/u-100-l-97.job.e74165
    Hold_Types = s
    Join_Path = oe
    Keep_Files = n
    Mail_Points = abe
    Mail_Users = enrico.user3@epfl.ch
    mtime = Fri Apr 12 15:22:07 2013
    Output_Path = mycluster.cluster:/scratch/user3/ubiquitin/100gL/starting-fro
	m-left/production/u-100-l-97.job.o74165
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
	PBS_O_HOME=/home/user3,PBS_O_LOGNAME=user3,
	PBS_O_WORKDIR=/scratch/user3/ubiquitin/100gL/starting-from-left/produc
	tion,PBS_O_LANG=en_US.utf8,
	PBS_O_PATH=/opt/pbs/default/sbin/:/home/bovigny/bin:/opt/xcat/bin:/opt
	/xcat/sbin:/opt/xcat/bin:/opt/xcat/sbin:/usr/lib64/qt-3.3/bin:/usr/loca
	l/bin:/bin:/usr/bin:/usr/local/sbin:/usr/sbin:/sbin:/opt/pbs/default/bi
	n:/opt/software/python/3.3.0/bin:/opt/software/bin:/opt/pbs/default/bin
	:/opt/software/python/3.3.0/bin:/opt/software/bin,
	PBS_O_MAIL=/var/spool/mail/user3,PBS_O_QUEUE=P_share_queue,
	PBS_O_HOST=mycluster.cluster
    Submit_arguments = -W depend=afterany:74164 u-100-l-97.job
    project = _pbs_project_default

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
        s = PbsproScheduler()
        
        retval = 0
        stdout = text_qstat_f_to_test
        stderr = ''
        
        job_list = s._parse_joblist_output(retval, stdout, stderr)

        # The parameters are hard coded in the text to parse
        job_on_cluster = 6
        job_parsed = len(job_list)
        self.assertEquals(job_parsed, job_on_cluster)

        job_running = 2
        job_running_parsed = len([ j for j in job_list if j.jobState \
                                   and j.jobState == jobStates.RUNNING ])
        self.assertEquals(job_running,job_running_parsed)

        job_held = 2
        job_held_parsed = len([ j for j in job_list if j.jobState \
                                   and j.jobState == jobStates.QUEUED_HELD ])
        self.assertEquals(job_held,job_held_parsed)

        job_queued = 2
        job_queued_parsed = len([ j for j in job_list if j.jobState \
                                   and j.jobState == jobStates.QUEUED ])
        self.assertEquals(job_queued,job_queued_parsed)

        running_users = ['user02','user3']
        parsed_running_users = [ j.jobOwner for j in job_list if j.jobState \
                                 and j.jobState == jobStates.RUNNING ]
        self.assertEquals( set(running_users) , set(parsed_running_users) )

        running_jobs = ['69301.mycluster','74164.mycluster']
        parsed_running_jobs = [ j.jobId for j in job_list if j.jobState \
                                 and j.jobState == jobStates.RUNNING ]
        self.assertEquals( set(running_jobs) , set(parsed_running_jobs) )
        
        for j in job_list:
            if j.allocatedNodes:
                num_nodes = 0
                num_cores = 0
                for n in j.allocatedNodes:
                    num_nodes += 1
                    num_cores += n.numCores
                    
                self.assertTrue( j.numNodes==num_nodes )
                self.assertTrue( j.numCores==num_cores )
        # TODO : parse the env_vars

# TODO: WHEN WE USE THE CORRECT ERROR MANAGEMENT, REIMPLEMENT THIS TEST
#        def test_parse_with_error_retval(self):
#            """
#            The qstat -f command has received a retval != 0
#            """
#            s = PbsproScheduler()            
#            retval = 1
#            stdout = text_qstat_f_to_test
#            stderr = ''
#            # Disable logging to avoid excessive output during test
#            logging.disable(logging.ERROR)
#            with self.assertRaises(SchedulerError):
#                job_list = s._parse_joblist_output(retval, stdout, stderr)
#            # Reset logging level
#            logging.disable(logging.NOTSET)

#        def test_parse_with_error_stderr(self):
#            """
#            The qstat -f command has received a stderr
#            """
#            s = PbsproScheduler()            
#            retval = 0
#            stdout = text_qstat_f_to_test
#            stderr = 'A non empty error message'
#            # TODO : catch the logging error
#            job_list = s._parse_joblist_output(retval, stdout, stderr)
#            #            print s._logger._log, dir(s._logger._log),'!!!!'

class TestSubmitScript(unittest.TestCase):
    def test_submit_script(self):
        """
        """
        from aida.scheduler.datastructures import JobTemplate
        s = PbsproScheduler()

        job_tmpl = JobTemplate()
        job_tmpl.argv = ["mpirun", "-np", "23", "pw.x", "-npool", "1"]
        job_tmpl.stdinName = 'aida.in'
        job_tmpl.numNodes = 1
        job_tmpl.uuid = str(uuid.uuid4())
        job_tmpl.maxWallclockSeconds = 24 * 3600 

        submit_script_text = s.get_submit_script(job_tmpl)

        self.assertTrue( '#PBS -r n' in submit_script_text )
        self.assertTrue( submit_script_text.startswith('#!/bin/bash') )
        self.assertTrue( '#PBS -l walltime=24:00:00' in submit_script_text )
        self.assertTrue( '#PBS -l select=1' in submit_script_text )
        self.assertTrue( "'mpirun' '-np' '23' 'pw.x' '-npool' '1'" + \
                         " < 'aida.in'" in submit_script_text )
if __name__ == '__main__':        
    unittest.main()
