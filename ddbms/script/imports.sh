mongoimport --db db --collection user --host 127.0.0.1:26000 --file ../dbfiles/user.json --legacy
mongoimport --db db --collection article --host 127.0.0.1:26000 --file ../dbfiles/article.json --legacy
mongoimport --db db --collection articlesci --host 127.0.0.1:26000 --file ../dbfiles/articlesci.json --legacy
mongoimport --db db --collection read --host 127.0.0.1:26000 --file ../dbfiles/readregion.json --legacy
mongoimport --db db --collection beread --host 127.0.0.1:26000 --file ../dbfiles/beread.json --legacy
mongoimport --db db --collection bereadsci --host 127.0.0.1:26000 --file ../dbfiles/bereadsci.json --legacy
mongoimport --db db --collection poprank --host 127.0.0.1:26000 --file ../dbfiles/poprank.json --legacy

for dir in '../dbfiles/article/*'; do
    echo $dir
    mongofiles --port 26000 --db db put $dir/*
    
done

redis-server ../../redis_config/redis.conf
