from xml.sax.handler import ContentHandler
from xml.sax import parse


class TestHandler(ContentHandler):
    def startElement(self, name, attrs):
        print(name, attrs.keys())


class HeadlineHandler(ContentHandler):
    in_headline = False

    def __init__(self, headlines):
        super().__init__()
        self.headlines = headlines
        self.data = []

    def startElement(self, name, attrs):
        if name == 'h1':
            self.in_headline = True

    def endElement(self, name):
        if name == 'h1':
            text = ''.join(self.data)
            self.data = []
            self.headlines.append(text)
            self.in_headline = False

    def characters(self, content):
        if self.in_headline:
            self.data.append(content)


headlines = []
parse('./file/file.xml', HeadlineHandler(headlines))

print('The following <h1> elements were found：')
for h in headlines:
    print(h)