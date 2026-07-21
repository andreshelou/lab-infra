rs.initiate(
    {
        _id: "rs0",
        members: [
            {
                _id: 0,
                host: "gl01:27017"
            },
            {
                _id: 1,
                host: "gl02:27017"
            },
            {
                _id: 2,
                host: "gl03:27017"
            }
        ]
    })