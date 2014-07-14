from scrapy.http import Request

class CollectionMiddleware(object):

    def __init__(self):
        self.items = []

    def process_spider_output(self, response, result, spider):
        if type(result) == Request:
            yield result
        else:
            if len(self.items) < 2:
                self.items.append(result)
            else:
                for i in self.items:
                    yield self.items[i]
                self.items = []