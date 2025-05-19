import django_filters
from .models import Assignment


class AssignmentFilter(django_filters.FilterSet):
    is_open = django_filters.BooleanFilter(
        method="filter_is_open", label="Is Open for Submission"
    )

    class Meta:
        model = Assignment
        fields = ["course", "due_date", "is_open"]

    def filter_is_open(self, queryset, name, value):
        if value:
            return queryset.filter(due_date__gte=self.request.now)
        return queryset
