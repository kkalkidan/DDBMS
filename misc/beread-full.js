conn = new Mongo("localhost:27017");
db = conn.getDB("ddbs");

// create beread
db.getCollection("read").aggregate( [ { $group: { _id: "$aid", readNum: { $sum: {$toInt: "$readOrNot" } }, readUidList: { $addToSet: { $cond: { if: { $eq: ["$readOrNot","1"] }, then: "$uid", else: "$$REMOVE"} } }, commentNum: { $sum: {$toInt: "$commentOrNot" } }, commentUidList: { $addToSet: { $cond: { if: { $eq: ["$commentOrNot","1"] }, then: "$uid", else: "$$REMOVE"} } }, agreeNum: { $sum: {$toInt: "$agreeOrNot" } }, agreeUidList: { $addToSet: { $cond: { if: { $eq: ["$agreeOrNot","1"] }, then: "$uid", else: "$$REMOVE"} } }, shareNum: { $sum: {$toInt: "$shareOrNot" } }, shareUidList: { $addToSet: { $cond: { if: { $eq: ["$shareOrNot","1"] }, then: "$uid", else: "$$REMOVE"} } }, } }, { $addFields: { "aid": {$concat: [ "a", "$_id" ]}, } }, { $lookup: { from: "article", localField: "aid", foreignField: "id", as: "article_cat" } }, { $unwind: { path: "$article_cat" } }, { $project: { _id: 1, readNum: 1, readUidList: 1, commentNum: 1, commentUidList: 1, agreeNum: 1, agreeUidList: 1, shareNum: 1, shareUidList: 1, aid: 1, article_cat:'$article_cat.category', } }, { $out: "beread" }, ], { allowDiskUse: true } );

// create bereadsci
db.getCollection("beread").aggregate( [ { $match: { article_cat : "science" } }, { $out: "bereadsci" }, ] );