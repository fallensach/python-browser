import socket
import ssl
import re
from html.parser import HTMLParser

class URL:
    def __init__(self, url, http_version="", user_agent="", type="", host="") -> None:
        self.user_agent = user_agent
        self.type = type
        self.host = host
        self.http_version = http_version
        self.url = url 
        self.scheme = ""
        self.title = ""
         
        try:
            self.scheme, self.url = url.split('://', 1)
        except:
            self.scheme = "https"
            url = "https://" + url
            self.scheme, self.url = url.split('://', 1)
            
        

        if type == "page":
            assert self.scheme in ("http", "https")
        elif type == "file":
            assert self.scheme == "file"

        else:
            raise ValueError("Invalid type, supported types are 'page' and 'file'")
            
        if self.scheme == "https":
            self.port = 443
        else:
            self.port = 80

        if "/" not in self.url: 
            self.url += "/"

        if type == "page":
            self.host, self.url = self.url.split("/", 1)
            self.path = "/" + self.url

        elif type == "file":
            self.path = self.url 

        if ":" in self.host and self.type == "page":
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def is_valid_domain(self, domain: str) -> bool:
        # Regular expression to validate domain
        domain_regex = re.compile(
            r'^(?:[a-zA-Z0-9]'  # First character of the domain
            r'(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)'  # Sub domain + hostname
            r'+[a-zA-Z]{2,6}$'  # First level TLD
        )
        return re.match(domain_regex, domain) is not None
     
    def request(self) -> str:
        error = False

        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
        try:
            s.connect((self.host, self.port))
        except socket.gaierror:
            error = True
       
        if error:
            return f"Could not connect to {self.host}\n Invalid URL or host"
        
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        request  = f"GET {self.path} HTTP/{self.http_version}\r\n" 
        request += f"Host: {self.host}\r\n" 
        request += f"User-Agent: {self.user_agent}\r\n"
        request += "\r\n"
        s.send(request.encode("utf-8"))
        response = s.makefile("r", encoding="utf-8", newline="\r\n")
        status_line = response.readline()
        version, status, explanation = status_line.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        body = self.html_body(content)
        s.close()
        return content 
    
    def html_body(self, html: str) -> str:
        class BrowserParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.data = ""
                self.in_tag = False
                self.in_head = False

            def handle_starttag(self, tag, attrs):
                if tag == "head":
                    self.in_head = True
                elif tag == "title":
                    pass
                self.in_tag = True

            def handle_endtag(self, tag):
                if tag == "head":
                    self.in_head = False
                    
                self.in_tag = False

            def handle_data(self, data):
                if not self.in_head:
                    self.data += data

            def get_data(self):
                return self.data

        parser = BrowserParser()
        parser.feed(html)
        return html 
    
    def find_body(self, html: str) -> str:
        in_tag = False
        buffer = ""

        for c in html:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
                if buffer == "body":
                    break
                buffer = ""
            else:
                buffer += c 
        
    
