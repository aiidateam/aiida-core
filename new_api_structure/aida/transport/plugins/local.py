###
### GP: a note on the local transport:
### I believe that we must not use os.chdir to keep track of the folder
### in which we are, since this may have very nasty side effects in other
### parts of code, and make things not thread-safe.
### we should instead keep track internally of the 'current working directory'
### in the exact same way as paramiko does already.
