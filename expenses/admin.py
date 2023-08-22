from django.contrib import admin
from .models import Expense, Category


class ExpenseAdmin(admin.ModelAdmin):
    list_display  = ('amount','description','owner','category','date',)
    search_fields  = ('description','category','date',)

    list_per_page = 3
admin.site.register(Category)
admin.site.register(Expense, ExpenseAdmin)


# Register your models here.
