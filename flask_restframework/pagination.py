from collections import namedtuple

PageInfo = namedtuple("PageInfo", ["page", "page_size"])

class DefaultPagination:
    def __init__(self, qs):
        self.qs = qs
        self.total = 0  #total objects count
        self.count_pages = 0    #total count of pages
        self.page = 0       #current page
        self.page_size = 10 #current page size

    def paginate(self, request):
        "Perform qs filtration"

        pageInfo = self._get_page_info(request)

        page = pageInfo.page
        page_size = pageInfo.page_size

        self.total = self.qs.count()
        self.count_pages = int(self.total/page_size)+1
        self.page = page
        self.page_size = page_size

        self.qs = self.qs[page_size*(page-1):page_size*page]


    def update_response(self, data):
        "Updates response: adds information fields like page, page_size etc."

        return {
            "results": data,
            "total": self.total,
            "pages": self.count_pages,
            "page": self.page,
            "page_size": self.page_size
        }

    def _get_page_info(self, request):
        """
        Returns page info

        :param request:
        :rtype: PageInfo
        """
        return PageInfo(
            page=int(request.args.get("page", 1)),
            page_size=int(request.args.get("page_size", 10))
        )

