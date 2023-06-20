from django.contrib import admin
from django.urls import path, include
from dbms.views import table_list_view, table_detail_view, update_table, order_table

urlpatterns = [
    path("admin/", admin.site.urls),
    path("tables/", table_list_view, name="table_list"),
    path("tables/<str:table_name>/", table_detail_view, name="table_detail"),
    path("update_table/", update_table, name="update_table"),
    path("<str:table_name>/order/<str:column_name>/", order_table, name="order_table"),
]
