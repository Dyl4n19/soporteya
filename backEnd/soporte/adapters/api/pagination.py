from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination


class ApiPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_page_size(self, request):
        value = request.query_params.get(self.page_size_query_param)
        if value is None:
            return self.page_size
        try:
            size = int(value)
        except (ValueError, TypeError):
            size = 0
        if not 1 <= size <= self.max_page_size:
            raise ValidationError({self.page_size_query_param: ["Debe ser un entero entre 1 y 100"]})
        return size
