#class Code(NodeClass):
#    computer = m.ManyToManyField('Computer') #for checking computer compatibility

#class ComputerUsername(m.Model):
#    """Association of aida users with given remote usernames on a computer.
#
#    There is an unique_together constraint to be sure that each aida user
#    has no more than one remote username on a given computer.
#
#    Attributes:
#        computer: the remote computer
#        aidauser: the aida user
#        remoteusername: the username of the aida user on the remote computer
#    NOTE: this table can be eliminated in favor of a text field in each computer containing a dict.
#    """
#    computer = m.ForeignKey('Computer')
#    aidauser = m.ForeignKey(User)
#    remoteusername = m.CharField(max_length=255)
#
#    class Meta:
#        unique_together = (("aidauser", "computer"),)
#
#    def __unicode__(self):
#        return self.aidauser.username + " => " + \
#            self.remoteusername + "@" + self.computer.hostname

#-------------------- Abstract Base Classes ------------------------
#quality_choice = ((1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'))     
#nodetype_choice = (("calculation","calculation"), ("data","data"))
#state_choice = (('prepared', 'prepared'),
#                ('submitted', 'submitted'), 
#                ('queued', 'queued'),
#                ('running', 'runnning'),
#                ('failed', 'failed'),
#               ('finished', 'finished'),
#               ('completed', 'completed'))

## OLDSTUFF OF Node
#    path = m.FilePathField()
#    quality = m.IntegerField(choices=quality_choice, null=True, blank=True) 
#    #if node is data
#    source = m.ForeignKey('self', null=True, related_name='outputs')   #only valid for data nodes to link to source calculations
   # members = m.ManyToManyField('self', symmetrical=False, related_name='containers') 
#edgetype_choice = (("input","input"), ("member","member"), ("workflow","workflow"))
#    state = m.CharField(max_length=255, choices=state_choice, db_index=True)

## OLDSTUFF OF group
#grouptype_choice = (('project', 'project'), ('collection', 'collection'), ('workflow', 'workflow'))
#datagrouptype_choice = (('collection', 'collection'), ('relation', 'relation'))
#   type =  m.CharField(max_length=255, choices=calcgrouptype_choice, db_index=True)    
    


