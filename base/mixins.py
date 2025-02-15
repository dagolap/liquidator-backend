from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ParseError, PermissionDenied


class SingleObjectQueryOrDataMixin:
    """Allows pk for a object to be sent as a query or POST parameter, instead of through the URL."""
    lookup_query_field = None
    lookup_data_field = None
    lookup_arg_field = None

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        if self.request.method == 'GET':
            field = self.lookup_query_field or self.lookup_arg_field or self.lookup_field
            data = self.request.query_params
        else:
            field = self.lookup_data_field or self.lookup_arg_field or self.lookup_field
            data = self.request.data

        if field not in data:
            raise ParseError(f'Missing argument "{field}"')
        value = data[field]

        obj = get_object_or_404(queryset, **{self.lookup_field: value})
        self.check_object_permissions(self.request, obj)
        return obj


class ErrorHandlingMixin:
    """Does basic error handling for views, to avoid 500 responses"""
    def get_queryset(self):
        try:
            return super().get_queryset()
        except ValidationError as e:
            raise ParseError(e.messages[0])


class CompanyFilterMixin(ErrorHandlingMixin):
    """
    Handles retrieving objects for the current company.

    When using the API the sender must include the ID of then
    company to manage. `CompanyAccessView` checks if the user
    is allowed to do the action for that company.

    This mixin uses that same company ID to filter the objects
    that can be retrieved.
    """
    company_field = 'company'

    def get_queryset(self):
        queryset = super().get_queryset()
        company_id = self.get_company_id()
        return queryset.filter(**{self.company_field: company_id})
