import httpserver as hs

server = hs.FilesystemHTTP("0.0.0.0", 8000)
server.run(verbose=True)