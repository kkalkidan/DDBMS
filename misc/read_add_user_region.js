conn = new Mongo("localhost:26000");
db = conn.getDB("db");

db.getCollection("read").aggregate( [ { $lookup: { from: "user", localField: "uid", foreignField: "uid", as: "user_region" } }, { $unwind: { path: "$user_region" } }, { $project: { id: 1, timestamp: 1, uid: 1, aid: 1, readTimeLength: 1, readSequence: 1, readOrNot: 1, aggreeOrNot: 1, commentOrNot: 1, commentDetail: 1, shareOrNot: 1, user_region:'$user_region.region', } }, { $out: "readregion" }, ], { allowDiskUse: true } );