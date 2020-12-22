conn = new Mongo("localhost:26000");
db = conn.getDB("db");

db.getCollection("article").aggregate( [ { $match: { category:{$eq:'science'} } }, { $out: "articlesci" }, ], { allowDiskUse: true } );