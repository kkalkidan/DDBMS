import yaml
import os
from pymongo import MongoClient

NUMBER_OF_CONFIG_REPL = 3
NUMBER_OF_MONGOS_REPL = 1

config_servers = {"next_available_port" : 26001, "repl_sets": {}}
shard_servers = {"next_available_port" : 27011, "repl_sets":{}}
mongos_servers = {"next_available_port" : 26000, "repl_sets": {}}
monitoring_url = []


def get_config_servers():
    repl_set = list(config_servers["repl_sets"].keys())[0]
    ports = config_servers["repl_sets"][repl_set]
    if(len(ports) < 1): 
        raise ValueError("<Mongos> No config servers found. ")
    result = repl_set + "/"
    for port in ports:
        result += "127.0.0.1:"+str(port)+","
    return result[:-1]

def prepare_config_file(server_type, repl_set):
    data = {}
    
    if(server_type == "configsvr"):
        data["sharding"] = {"clusterRole": "configsvr"}
        server = config_servers

    elif(server_type == "shardsvr"):
        data["sharding"] = {"clusterRole": "shardsvr"}
        server = shard_servers
    else:
        data["sharding"] = {"configDB": get_config_servers()}
        server_name = "mongos"
        server = mongos_servers

    if(server["repl_sets"].get(repl_set, None) is None):
        server["repl_sets"][repl_set] = []    

    count = len(server["repl_sets"][repl_set]) + 1

    server_name = repl_set + "-" + str(count)

    data["net"] = {
        "bindIp": "localhost," + server_name,
        "port": server["next_available_port"]
        }

    data["systemLog"] = {
            "destination": "file",
            "path": "db/" + repl_set + "/" + server_name + "/" + server_name + ".log",
            "logAppend": True
        }

    data["processManagement"]= {
            "fork": True
        }

    if(server_type != "mongos"):
        data["storage"]= {
                "dbPath": "db/" + repl_set + "/" + server_name
            }
        data["replication"] = {"replSetName": repl_set}

    port = server["next_available_port"]
    server["next_available_port"] = server["next_available_port"]+1
    
    server["repl_sets"][repl_set].append(port)

    return data, server_name, port


def write_config_file(server_type, repl_set):
    data, server_name,  port = prepare_config_file(server_type, repl_set)
    path = "./db/"+ repl_set + "/" + server_name
    try:
        os.makedirs(path)
    except OSError:
        print("Creation of the directory %s failed" % path)
    else:
        print("Successfully created the directory %s " % path)

    file = open(server_name+".config", "w")
    yaml.dump(data, file)
    file.close()
    return server_name+".config", port

# define the name of the directory to be created

def config_setup(number_replica):
    # config server files for collection the names of the config server files 
    
    config_serv_files = []
    #creating the config files for the configuration servers
    count = len(list(config_servers["repl_sets"].keys())) + 1 
    repl = "csrs-"+str(count)
    for i in range(number_replica):
        file_name, _ = write_config_file("configsvr", repl)
        config_serv_files.append(file_name)

    # creating config server instances 
    for f in config_serv_files:
        os.system("mongod -f " + f)

    ports = config_servers["repl_sets"][repl]
    conn = MongoClient('localhost', ports[0])
    config = {"_id": repl, "members":[]}

    for i in range(len(ports)):
        config["members"].append({"_id": i, "host": "localhost:"+str(ports[i])})
    # intializing the replica set of the config servers
    try: 
        conn.admin.command({'replSetInitiate': config})
    except Exception as e:
        print("Error has occured during reconfig", e)
        # conn.admin.command({'replSetReconfig': config})
     
def mongos_setup(number_replica):
    #creating config file for mongos server 
    mongos_serv_files = []
    count = len(list(mongos_servers["repl_sets"].keys())) + 1
    for i in range(number_replica):
        file_name, _= write_config_file("mongos", "mongos-"+str(count))
        mongos_serv_files.append(file_name)

    for f in mongos_serv_files:
        os.system("mongos -f " + f)

def shard_setup(number_replica, tag_reg):
    # creating config file for the shard servers 
   
    shard_serv_files = []
    count = len(list(shard_servers["repl_sets"].keys())) + 1
    repl = "shard_replica-" + str(count) 
    # port = shard_servers["repl_sets"][repl][0]
    for i in range(number_replica):
        file_name, port = write_config_file("shardsvr", repl)
        shard_serv_files.append(file_name)

    for f in shard_serv_files:
        os.system("mongod -f " + f)

    ports = shard_servers["repl_sets"][repl]
    conn = MongoClient('localhost', ports[0])
    config = { "_id": repl, "members": []}
    usages = ["production", "recovery"]
    for i in range(len(ports)):
        result = { "_id": i, "host": "localhost:"+str(ports[i]), "tags": {"reg": tag_reg, "usage": usages[i%2]}} 
        config["members"].append(result)
    #initialize shard server replica set
    try: 
        conn.admin.command({'replSetInitiate': config})
    except Exception as e:
        print("Error occured when running repl.initiate()", e)

    conn_mongos = get_mongos_instance()
    url = repl + "/"+"localhost:"+str(port)
    conn_mongos.admin.command({"addShard": url}, True)
    db_name = "db"
    conn_mongos.admin.command({"enableSharding": db_name})
    try:
    #enable monitoring
        addr = conn.admin.command("isMaster")['primary']
        conn_primary = MongoClient(addr)
        conn_primary.admin.command({ "setFreeMonitoring": 1, "action": "enable"})
        url = conn_primary.admin.command({ 'getFreeMonitoringStatus': 1 } )['url']
        monitoring_url.append(url)

    except Exception as e:
        print("Error occured while enabling monitoring", e)

def get_mongos_instance():
    mongos_repl = list(mongos_servers["repl_sets"].keys())
    mongos_port = mongos_servers["repl_sets"][mongos_repl[0]][0]
    conn = MongoClient('localhost', mongos_port)
    return conn

def setup():

    config_setup(NUMBER_OF_CONFIG_REPL)

    mongos_setup(NUMBER_OF_MONGOS_REPL)

    conn = get_mongos_instance()

    shard_setup(2, "Beijing")
    shard_setup(2, "Hong Kong")
    shard_setup(3, "backup")

    shard_replicas = list(shard_servers["repl_sets"].keys())
        
    collections = {"db.user": {"region": "hashed"},
                "db.articlesci": {"category": "hashed"}, 
                #collection containing both science and technology articles 
                "db.article": {"category": "hashed"},
                "db.read":{"user_region": "hashed"},
                "db.beread": {"article_cat": "hashed"},
                "db.bereadsci": {"article_cat": "hashed"},
                "db.poprank":{"category": "hashed"},
                "db.fs.chunks": {"_id": 1}
                }
    
    for key, value in list(collections.items())[:-1]:
        conn.admin.command({"shardCollection":key, "key": value})
        # disabling the balancer for each collection
        conn.get_database("config").collections.update_one(
            {"_id": key + ""},
            {"$set": {"noBalance": True}})

    # sharding the chunks based on the shard keys-region
    conn.admin.command({"moveChunk": "db.user","find": {"region": "Beijing"}, "to":shard_replicas[0]})
    conn.admin.command({"moveChunk": "db.user","find": {"region": "Hong Kong"}, "to":shard_replicas[1]})

    #articles sci and tech shard 1 based on category
    conn.admin.command({"moveChunk": "db.article","find": {"category": "science"},"to": shard_replicas[0]})
    conn.admin.command({"moveChunk": "db.article","find": {"category": "technology"},"to": shard_replicas[1]})

    #articlesci -> shard 2
    conn.admin.command({"moveChunk": "db.articlesci","find": {"category": "science"},"to": shard_replicas[1]})

    conn.admin.command({"moveChunk": "db.read","find": {"user_region": "Beijing"}, "to":shard_replicas[0]})
    conn.admin.command({"moveChunk": "db.read","find": {"user_region": "Hong Kong"}, "to":shard_replicas[1]})

    #articles sci and tech shard 1 based on category
    conn.admin.command({"moveChunk": "db.beread","find": {"article_cat": "science"},"to": shard_replicas[0]})
    conn.admin.command({"moveChunk": "db.beread","find": {"article_cat": "technology"},"to": shard_replicas[1]})

    #articlesci -> shard 2
    conn.admin.command({"moveChunk": "db.bereadsci","find": {"article_cat": "science"},"to": shard_replicas[1]})

    #articles sci and tech shard 1 based on category
    conn.admin.command({"moveChunk": "db.poprank","find": {"category": "science"},"to": shard_replicas[0]})
    conn.admin.command({"moveChunk": "db.poprank","find": {"category": "scitech"},"to": shard_replicas[1]})

# stopping server instances
def stop():

    stop_this(config_servers)
    stop_this(mongos_servers)
    stop_this(shard_servers)
    os.system("rm *.config")
    os.system("rm -rf db/")


def stop_this(server_name):

    repl_sets = list(server_name["repl_sets"].keys())

    for repl in repl_sets:
        ports = server_name["repl_sets"][repl]
        command = ""
        for p in ports:
            command = "mongo --port "+ str(p) + " --eval 'db.getSiblingDB(\"admin\").shutdownServer();' "
            os.system(command)
   

def new_dbms_server():
    
    numb_repl = int(input("Enter number of replica DB > "))
    shard_setup(numb_repl, "new")

def monitoring():
    

    mongos_repl = list(mongos_servers["repl_sets"].keys())
    mongos_port = mongos_servers["repl_sets"][mongos_repl[0]][0]
    command = "mongo --port "+ str(mongos_port) + " --eval 'sh.status()' "
    os.system(command)
    print("\n\n\n")
    print("Mongos server running on : \n \t",  mongos_servers) 
    # print("Initialized Mongo shard server : \n \t",  shard_servers)
    print("\n\n\n")
    shard_names = list(shard_servers["repl_sets"].keys())
    for s in shard_names:
        port = shard_servers["repl_sets"][s][0]
        conn = MongoClient('localhost', port)
        addr = conn.admin.command("isMaster")['primary']
        print("Primary server address of " + s + " : " + addr)

    numb_shards = len(list(shard_servers["repl_sets"].keys()))
    for  i in range(numb_shards):
        print("\t Monitoring url for Shard " + str(i+1) + " - "+ monitoring_url[i])
    print("\n\n\n")

def dropping_serv():
    print("******** Current status of the DB **********")
    monitoring()
    shard_numb = int(input("From which shard (Enter shard number)> "))

    shard_names = list(shard_servers["repl_sets"].keys())
    print(shard_names)
    s = shard_names[shard_numb-1]
    shardports = shard_servers["repl_sets"][s]
    port = int(input("Enter port number of the server > "))
    if(port in shardports):
        command = "mongo --port "+ str(port) + " --eval 'db.getSiblingDB(\"admin\").shutdownServer();' "
        shard_servers["repl_sets"][s].remove(port)
    else:
        print("No Server with specified port")
    os.system(command)
    
def migration():
    try:
        shard_num_from = int(input("From (Enter shard number)> " ))
        shard_num_to = int(input("To (Enter shard number>"))
        if(shard_num_from != shard_num_to 
            and shard_num_from > 0 
            and shard_num_to > 0):
            shard_names = list(shard_servers["repl_sets"].keys())
            shardfrom = shard_names[shard_num_from -1]
            shardto = shard_names[shard_num_to -1]
        portfrom = shard_servers["repl_sets"][shardfrom][0]
        portto = shard_servers["repl_sets"][shardto][0]

        connfrom = MongoClient("localhost", portfrom)
        addrfrom = connfrom.admin.command("isMaster")['primary']

        connto = MongoClient("localhost", portto)
        addrto = connto.admin.command("isMaster")['primary']

        command = "mongodump --host=" + addrfrom + " --db db --archive | mongorestore --host=" + addrto + " --db db  --archive"
        os.system(command)

    except Exception as e:
        print(e)
        print("An error has occurred during migration")


def prompt():
    try:
        while(True): 
                message = """
                    1. Initialize a new shard server replica \n
                    2. See all the initialized servers and their status \n
                    3. Dropping a DBMS server \n
                    4. Migrate db from one server to another \n
                    5. Stop all server instances and clean the db directory \n
                    Choose a task > 
                """
                task = int(input(message))
            
                if(task == 1):
                    new_dbms_server()
                elif(task == 2):
                    monitoring()
                elif(task == 3):
                    dropping_serv()
                elif(task == 4): 
                    migration()
                elif(task==5):
                    break
                else:
                    print("Unknown task number, please try again.")
    except:
        print("An error has occurred. ")
    finally:
        question = input("want to stop all the servers : Enter 'y' > ")
        if(question == "y"):
            stop()
            print("bye")     
        else: prompt()

def main():
    try: 
        setup()
        print("\n\n ******* Finished running initial set up of the db servers ******** \n\n")
        prompt()
    except Exception as e:
        print("An error has occured!")
        print(e)
   
       

main()     

            


