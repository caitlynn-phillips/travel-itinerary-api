from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for main list endpoints.
    """

    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class CompactPagination(PageNumberPagination):
    """
    Compact pagination for lightweight components or sidebars.
    """

    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20
