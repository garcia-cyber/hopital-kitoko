from django.contrib import admin
from .models import *

# Register your models here.

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['roleName']


# -------------------------------
# fonction
@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
    list_display = ['fonctionKey','userKey','autorisation',] 
