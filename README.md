## Distributed Database System

This is the final project for Distributed Database Systems（70240063-0）2020.
Entire project is developed using MongoDB, Jupyter Notebook and Studio3T.

![Alt text](/img/mongodb.png?raw=true "MongoDB")

### Setup

Start the servers
```
>python3 ./ddbms/server/server.py
```

### Import structured data
To import structured data in json format, simply run

`mongoimport.sh <host> <port> <database name> <path to data> <file name>`

```
>bash ./ddbms/import/mongoimport.sh localhost 26000 db /home/data "*.json"
```

### Import unstructured data
We use GridFS from MongoDB to store unstructured data such as image, video and text files. To import unstructured data, run

`mongofiles.sh <host> <port> <database name> <path to data> <file name>`

```
>bash ./ddbms/import/mongofiles.sh localhost 26000 db <data path> "*.flv"
```

### Start mongo shell

```
mongo --port 26000
```

![Alt text](/img/architecture.png?raw=true "architecture")

**_note:_** Misc folder contains some of the JavaScript and Python codes that were used to generate additional collections and start listener.