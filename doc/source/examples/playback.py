import musicpd

# Using a context manager
# (use env var if you need to override default host)
with musicpd.MPDClient() as client:
    client.play()
    client.setvol('80')
