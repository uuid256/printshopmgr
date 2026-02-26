from django.urls import path

from . import views

app_name = "customers"

urlpatterns = [
    path("", views.customer_list, name="list"),
    path("new/", views.customer_create, name="create"),
    path("<int:pk>/", views.customer_detail, name="detail"),
    path("<int:pk>/edit/", views.customer_edit, name="edit"),
    # HTMX endpoint: search autocomplete
    path("search/", views.customer_search, name="search"),
    path("autocomplete/", views.customer_autocomplete, name="autocomplete"),
]
