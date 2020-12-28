# this script takes in five arguments
# $1 = host name
# $2 = port 
# $3 = db name
# $4 = path
# $5 = file name

# example
# bash mongofiles.sh localhost 26000 db ../data/articles "*.flv"

echo "--- start mongofiles ---"    
for f in $(find $4 -name $5 ); do mongofiles --host $1 --port $2 --db $3 put $f &>> mongofiles.log ; done
echo "--- import successful ---"
echo "--- view the status @ mongofiles.log ---"