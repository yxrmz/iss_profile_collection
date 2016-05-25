from bluesky.plans import Count


uid, = RE(Count([fm]), LiveTable([fm]))
db[uid]
