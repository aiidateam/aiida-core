#!/bin/bash 

echo "********************************************"
echo "USE WITH A LOT OF CARE!! MAY DESTROY FILES!!"
echo "********************************************"
echo Enter to continue, Ctrl+C to abort
read

echo 'Replacing "aida" with "aiida" case-insensitively'
echo Enter to continue, Ctrl+C to abort
read

OLD='[aA][iI][dD][aA]'
OLDREPL='\([aA]\)[iI]\([dD]\)\([aA]\)'
NEWREPL='\1ii\2\3'
grep -e "$OLD" --color --include '*.py' -r .

echo Enter to substitute everywhere, Ctrl+C to abort
read

grep --files-with-matches --null --include '*.py' -r "$OLD" . | xargs -0 -I {} sed -i~ 's/'"$OLDREPL"'/'"$NEWREPL"'/g' "{}"
#grep --files-with-matches --null -r "$OLD" . | xargs -0 -I {} sed -i~ 's/'"$OLDREPL"'/'"$NEWREPL"'/g' "{}"


