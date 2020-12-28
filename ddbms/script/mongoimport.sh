# this script takes in five arguments
# $1 = host name
# $2 = port 
# $3 = db name
# $4 = folder path
# $5 = filename

# example
# bash mongoimport.sh localhost 26000 db /home/data "*.json"

if [ -z ${3+x} ] || [ -z ${4+x} ]; then
  echo "Error! This script requires two parameters:"
  echo "1) the database name"
  echo "2) the folder containing the collections to import"
  exit 1
fi

echo "--- start mongoimport ---"
for f in $(find $4 -name $5); do mongoimport --host $1:$2 --db $3 --file $f --legacy&>> mongoimport.log ; done
echo "--- import successful ---"
echo "--- view the status @ mongoimport.log ---"