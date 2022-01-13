from .tcp.Server import Server 
from .repo import FileManager

fp = FileManager()

s = Server(fp)
s.runServer()