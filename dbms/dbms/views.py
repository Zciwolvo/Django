from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
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

        # Retrieve the table model based on the table name
        table_model = apps.get_model(app_label="dbms", model_name=table_name)
        identifier_field = None

        # Find the primary key field named "ID"
        for field in table_model._meta.fields:
            if field.primary_key:
                identifier_field = field
                break

        if identifier_field is None:
            return JsonResponse({"error": "Table primary key not found"}, status=404)

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


def order_table(request, table_name, column_name):
    # Retrieve the table model based on the table name
    table_model = apps.get_model(app_label="dbms", model_name=table_name)

    # Convert the column name to lowercase for comparison
    column_name_lower = column_name.lower()

    # Check if the specified column exists in the table
    column_names = [field.name for field in table_model._meta.fields if field.db_column]
    if column_name_lower not in [name.lower() for name in column_names]:
        return JsonResponse({"error": "Invalid column name"}, status=400)

    # Get the primary key field name
    primary_key_field_name = table_model._meta.pk.name

    # Retrieve the current order from the session
    order = request.session.get("order", {})
    current_order_column = order.get("column")
    current_order_direction = order.get("direction")

    # Determine the new order column and direction
    if current_order_column == column_name_lower:
        # If the same column is clicked again, toggle the order direction
        if current_order_direction == "asc":
            new_order_direction = "desc"
        else:
            new_order_direction = "asc"
    else:
        # If a new column is clicked, set the order direction to ascending
        new_order_direction = "asc"

    # Update the session with the new order
    request.session["order"] = {
        "column": column_name_lower,
        "direction": new_order_direction,
    }

    # Check if the column is a BinaryField
    field_type = table_model._meta.get_field(column_name_lower).get_internal_type()
    if field_type == "BinaryField":
        # Return a redirect to the table_detail view without any changes
        return redirect("table_detail", table_name=table_name)

    # Determine the ordering string based on the new order
    ordering = (
        f"{column_name_lower}"
        if new_order_direction == "asc"
        else f"-{column_name_lower}"
    )

    # Retrieve all rows from the table and order them by the specified column
    rows = table_model.objects.all().order_by(ordering)

    # Fetch the column names from the database using raw SQL query
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}';"
        )
        columns = [row[0] for row in cursor.fetchall()]

    # Prepare the data to be passed to the template
    table_data = []
    for row in rows:
        row_data = [getattr(row, primary_key_field_name)]
        for name in columns:
            if name.lower() != primary_key_field_name:
                row_data.append(getattr(row, name.lower()))
        table_data.append(row_data)

    context = {
        "table_name": table_name,
        "columns": columns,
        "data": table_data,
    }

    return render(request, "table_detail.html", context)
