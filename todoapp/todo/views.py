from django.shortcuts import render, redirect, get_object_or_404
from .models import TodoItem

def todo_list(request):
    items = TodoItem.objects.all()
    return render(request, 'todo_list.html', {'items': items})

def update_todo(request, todo_id):
    todo_item = get_object_or_404(TodoItem, id=todo_id)
    todo_item.completed = not todo_item.completed
    todo_item.save()
    return redirect('todo_list')

def add_todo(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        created_at = request.POST.get('created_at')
        if title:
            item = TodoItem.objects.create(title=title, description=description, created_at=created_at)
            item.save()
    else:
        item_id = request.POST.get('item_id')
        if item_id:
            item = TodoItem.objects.get(id=item_id)
            item.toggle_completed()
    return redirect('todo_list')