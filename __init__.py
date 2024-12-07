""""""


import os
import socket, datetime
import threading

now = lambda: datetime.datetime.now()

class HTTPSender:
    def __init__(self, host, port):
        self.host, self.port = host, port
        self._message = b""
        self._headers = ""
        self.path = ""
        self.arguments = {}

    def start(self, code): 
        time = now().strftime("%a %d %b %Y %H:%M:%S %Z")
        self._headers += f"""
HTTP/1.1 {code}
Date: {time}
Content-Type: text/html\n"""

    def message(self, msg):
        if isinstance(msg, bytes):
            self._message += msg
        else:
            self._message += msg.encode() + b"\n"

    def use_request(self, req, verbose):
        if req == "":
            return None
        reqargs = req.split("\n")[0].split(" ")
        func = reqargs[0]
        self.path = reqargs[1]

        if verbose:
            time = now().strftime("%H:%M:%S")
            print(f"[{time}]: {func} {self.path}")

        try:
            for argument in self.path.split("?")[1].split("&"):
                self.arguments[argument.split("=")[0]] = argument.split("=")[1]
            self.path = self.path.split("?")[0]
        except:
            pass
        
        return func

    def run(self, verbose=False):
        print("RUNNING ON", self.host + ":" + str(self.port))
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.port))
            while True:
                sock.listen()
                conn, addr = sock.accept()
                thr = threading.Thread(target=self.handle, args=(conn, addr, verbose))
                thr.start()

    def finalise(self):
        self._headers += "Content-Length: " + str(len(self._message)-1)

    def handle(self, conn, addr, verbose):
        
        req = conn.recv(2048).decode()
        name = self.use_request(req, verbose)
        if name == None:
            conn.close()
            return

        getattr(self, name)()

        conn.sendall((self._headers.encode() + b"\n\n" + self._message))

        self._message = b""
        self._headers = ""
        self.arguments = {}

        conn.close()

    def change_content_type(self, new):
        if "Content-Type: " in self._headers:
            self._headers = self._headers.replace("Content-Type: text/html", f"Content-Type: {new}")
        else:
            self._headers += f"Content-Type: {new}\n"




class Example(HTTPSender):
    def GET(self):
        self.start(200)
        print(self.path)
        print(self.arguments)
        self.message("<h1>wsup</h1>")
        self.finalise()

class FilesystemHTTP(HTTPSender):
    def __init__(self, host, port, path="./html", errorpath="./errors"):
        super().__init__(host, port)
        self.files = path
        self.errorpath = errorpath

    def GET(self):
        path = self.path

        if path == "/":
            path = "/index.html"

        if os.path.exists(self.files + path):
            self.start(200)
        else:
            self.start(404)
            if os.path.exists(self.errorpath + "/404.html"):
                with open(self.errorpath + "/404.html", "rb") as file:
                    self.message(file.read()+b"\n")
            self.finalise()
            return

        if os.path.isdir(self.files + path):
            path += "/index.html"

        extension = path.split(".")[-1]
        mime_type = "text/html"

        if extension == "css":
            mime_type = "text/css"
        elif extension == "js":
            mime_type = "application/javascript"
        elif extension in ["jpg", "jpeg"]:
            mime_type = "image/jpeg"
        elif extension == "png":
            mime_type = "image/png"
        elif extension == "gif":
            mime_type = "image/gif"
        elif extension == "ico":
            mime_type = "image/ico"

        self.change_content_type(mime_type)

        with open(self.files + path, "rb") as file:
            file_content = file.read() + b"\n"
            self.message(file_content)

        self.finalise()

        

if __name__ == "__main__":
    ex = FilesystemHTTP("0.0.0.0", 8000)
    ex.run()