#!/bin/bash 

echo "********************************************"
echo "USE WITH A LOT OF CARE!! MAY DESTROY FILES!!"
echo "********************************************"
echo Enter to continue, Ctrl+C to abort
read

echo Replacing "'"$1"'" with "'"$2"'"
echo Enter to continue, Ctrl+C to abort
read

OLD="$1"
NEW="$2"
grep --color --include '*.py' -r "$1" .

echo Enter to substitute everywhere, Ctrl+C to abort
read

grep --files-with-matches --null --include '*.py' -r "$1" . | xargs -0 -I {} sed -i~ 's/'"$1"'/'"$2"'/g' "{}"


