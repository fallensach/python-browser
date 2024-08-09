from custom_urllib import URL
import argparse
from custom_urllib import URL
import argparse
import tkinter as tk
import tkinter.font
from tkinter.ttk import Style
import threading

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 15, 20
SCROLL_STEP = 100

class Browser:
    def __init__(self) -> None:
        self.window = tk.Tk()
        self.window.title("Browser")
        self.style = Style()
        self.style.theme_use("default")
        self.content = ""
        self.real_height = HEIGHT
        self.real_width = WIDTH
        self.null_term = False
        self.page_height = 0
        self.tokens = []
        self.resize_timer = None

        self.canvas = tk.Canvas(self.window, width=WIDTH, height=HEIGHT, bg="white")
        self.canvas.pack(fill="both", expand=True, side="bottom")
        self.font_default = tkinter.font.Font(family="Noto Sans CJK", size=12)
        self.display = [] 
        self.scroll = 0
        self.window.bind("<Down>", self._scroll)
        self.window.bind("<Up>", self._scroll)
        self.window.bind("<Button-5>", self._scroll)
        self.window.bind("<Button-4>", self._scroll)
        self.window.bind("<MouseWheel>", self._scroll)
        self.window.bind("<Configure>", self._debounced_resize)
    
        self.search_frame = tk.Frame(self.window, borderwidth=1, relief="raised", height=60)
        self.search_frame.pack(fill="both", side="top")

        # Create search button
        self.search_button = tk.Button(self.search_frame, text="Search", command=self.search)
        self.search_button.pack(pady=5, side="right")
        # Create search bar
        self.search_bar = tk.Entry(self.search_frame)
        self.search_bar.pack(pady=10, padx=5, side="right", fill="both", expand=True)
    
    def _debounced_resize(self, event) -> None:
        if self.resize_timer: 
            self.resize_timer.cancel()
        self.resize_timer = threading.Timer(0.5, self._resize, args=(event,))
        self.resize_timer.start()
    

    def _scroll(self, event) -> None:
        # Up
        if (event.delta > 0 or event.num == 4 or event.keysym == "Up") and self.scroll > 0 :
            self.scroll -= SCROLL_STEP 
        # Down
        elif (event.delta < 0 or event.num == 5 or event.keysym == "Down") and not self.null_term:
            self.scroll += SCROLL_STEP 
        self.draw()
    
    def _resize(self, event) -> None:
        self.real_height = self.window.winfo_height() 
        self.real_width = self.window.winfo_width() 
        self.display = Layout(self.tokens).display
        self.draw()
    
    def draw(self):
        self.canvas.delete("all")
        
        # Draw only the elements that are in view
        for x, y, word, font in self.display:
            if y > self.scroll + HEIGHT or y + font.metrics("linespace") < self.scroll:
                continue
            if word == "\0":
                self.null_term = True
            else:
                self.null_term = False
            self.canvas.create_text(x, y - self.scroll, text=word, font=font, anchor="nw")
 
    def search(self) -> None:
        url_text = self.search_bar.get()
        if url_text:
            self.window.configure(cursor="watch")
            threading.Thread(target=self.fetch_content, args=(url_text,)).start()

    def fetch_content(self, url_text: str) -> None:
        url = URL(url_text, http_version="1.0", user_agent="python", type="page")
        self.content = get_body_content(url)
        self.tokens = lex(self.content)
        self.display = Layout(self.tokens).display
        self.draw()
        self.window.configure(cursor="arrow")

def lex(body):
    in_tag = False
    buffer = ""
    out = []

    for c in body:
        if c == "<":
            in_tag = True
            if buffer:
                out.append(Text(buffer))
            buffer = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(buffer))
            buffer = ""
        else:
            buffer += c

    if not in_tag and buffer:
        out.append(Text(buffer))

    return out 

class Layout:
    def __init__(self, tokens) -> None:
        self.display = []
        self.line = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.weight = "normal"
        self.style = "roman"
        self.size = 12

        for tok in tokens:
            self.token(tok)
        
        self.flush()
    
    def token(self, tok):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.word(word)
             
        elif tok.tag == "i":
            self.style = "italic"
        elif tok.tag == "/i":
            self.style = "roman"
        elif tok.tag == "b":
            self.weight = "bold"
        elif tok.tag == "/b":
            self.weight = "normal"
        elif tok.tag == "small":
            self.size -= 2  
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
            self.cursor_y += VSTEP
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += VSTEP
    
    def word(self, word):
        font = tkinter.font.Font(family="Ubuntu", size=self.size, weight=self.weight, slant=self.style)
        w = font.measure(word)
        if self.cursor_x + w > WIDTH - HSTEP:
            self.flush()
        
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font.measure(" ") 
    
    def flush(self):
        if not self.line: return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics]) 

        baseline = self.cursor_y + 1.25 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display.append((x, y, word, font))
        
        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.25 * max_descent
        self.cursor_x = HSTEP
        self.line = []

class Text:
    def __init__(self, text) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text
    
    def __repr__(self) -> str:
        return self.text

class Tag:
    def __init__(self, tag) -> None:
        self.tag=tag 
    
    def __str__(self) -> str:
        return self.tag

    def __repr__(self) -> str:
        return self.tag

def get_content(body: str) -> str:
    in_tag = False
    text = ""
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text + "\n\0"
            
def get_body_content(url: URL) -> str:
    body = url.request()
    return body + "\n\0"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="browser",
        description="A simple web browser"
    )

    """
    parser.add_argument("url", help="URL to load")
    parser.add_argument("-v", "--version", help="HTTP version", default="1.0")
    parser.add_argument("-a", "--agent", help="User agent", default="python!")
    parser.add_argument("-t", "--type", help="Type of URL", default="page")
    parser.add_argument("-x", "--host", help="Host name", default="localhost")

    args = parser.parse_args()
    
    url = URL(args.url, args.version, args.agent, args.type, args.host)
    
    """
    Browser()
    tk.mainloop()