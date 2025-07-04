from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size_query_param = 'page_size'  # Параметр запроса для изменения размера страницы
    max_page_size = 100  # Максимально допустимый размер страницы

