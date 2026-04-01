from django.contrib import admin
from .models import *

# Register your models here.

# 1
# =======================================
#  fonction 
@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
	list_display = ['fonction']

# 2
# =======================================
# service 
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
	list_display = ['nomService']

# 3
# =======================================
# profil 
@admin.register(Profil) 
class ProfilAdmin(admin.ModelAdmin):
	list_display = ['nomComplet','userProfil','sexe','phone','adresse','fonction','service' ,'date_register']

# 4
# ======================================
# patient 
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
	list_display = fields = ['noms','sexeP','ageP','phone_responsable','adresseP','service','date_registerP']