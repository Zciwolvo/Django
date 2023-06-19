from django.shortcuts import render, get_object_or_404
from django.db import connection
from django.http import JsonResponse, HttpResponseBadRequest
from django.apps import apps


def table_list_view(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"
        )
        table_names = [row[0] for row in cursor.fetchall()]

    filtered_table_names = [
        name for name in table_names if not name.startswith(("django", "auth", "sys"))
    ]

    return render(request, "table_list.html", {"table_names": filtered_table_names})


def table_detail_view(request, table_name):
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}';"
        )
        columns = [row[0] for row in cursor.fetchall()]

        cursor.execute(f"SELECT * FROM {table_name};")
        data = cursor.fetchall()

    return render(
        request,
        "table_detail.html",
        {"table_name": table_name, "columns": columns, "data": data},
    )


def print_all_models(app_label):
    app_config = apps.get_app_config(app_label)
    for model in app_config.models.values():
        print(model.__name__)


def update_table(request):
    if request.method == "POST" and request.is_ajax():
        table_name = request.POST.get("table_name")
        row_id = request.POST.get("row_id")
        row_data = request.POST.getlist("row_data[]")
        print_all_models("dbms")
        # Retrieve the table model based on the table name
        table_model = apps.get_model(app_label="dbms", model_name=table_name)
        table_fields = table_model._meta.get_fields()
        identifier_field = table_fields[0]  # Assuming the identifier is the first field

        try:
            table_instance = table_model.objects.get(**{identifier_field.name: row_id})
        except table_model.DoesNotExist:
            return JsonResponse({"error": "Table not found"}, status=404)

        # Update the model instance with the new data
        for i, column in enumerate(table_model._meta.fields):
            if column.name != identifier_field.name:
                new_value = row_data[i]
                if new_value:
                    setattr(table_instance, column.name, new_value)

        # Save the updated model instance to the database
        table_instance.save()

        return JsonResponse({"success": "Table updated successfully"})
    else:
        return JsonResponse({"error": "Invalid request"}, status=400)
