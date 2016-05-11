from bluesky.plans import Count


print('Waiting for pb6 to report connected')
pb6.wait_for_connection()


c = Count([])
c.flyers = [pb6.enc1]
RE(c, LiveTable([]))
