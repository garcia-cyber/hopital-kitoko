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


# =================================
# taux 
@admin.register(ConfigurationHopital)
class ConfigurationHopitalAdmin(admin.ModelAdmin):
    # On empêche l'ajout d'un nouvel enregistrement si un existe déjà
    def has_add_permission(self, request):
        if ConfigurationHopital.objects.exists():
            return False
        return True

    # On empêche la suppression pour ne pas casser le système
    def has_delete_permission(self, request, obj=None):
        return False

    # Configuration de l'affichage dans la liste
    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')
    
    # On rend le champ de date de mise à jour visible mais non modifiable (puisqu'il est auto_now)
    readonly_fields = ('derniere_mise_a_jour',)

    # Petite astuce : rediriger directement vers la modification s'il y a un objet
    def changelist_view(self, request, extra_context=None):
        if ConfigurationHopital.objects.count() == 1:
            obj = ConfigurationHopital.objects.first()
            from django.shortcuts import redirect
            return redirect(f'/admin/{obj._meta.app_label}/{obj._meta.model_name}/{obj.id}/change/')
        return super().changelist_view(request, extra_context=extra_context)

# =======================================
# prestation

@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste
    list_display = ('libelle', 'get_categorie_display', 'prix')
    
    # Filtres sur le côté droit pour trier par type de soin
    list_filter = ('categorie',)
    
    # Barre de recherche pour chercher par nom de prestation
    search_fields = ('libelle',)
    
    # Permet de modifier le prix directement depuis la liste sans ouvrir l'objet
    list_editable = ('prix',)
    
    # Organisation de l'affichage dans le formulaire d'ajout
    fieldsets = (
        ('Informations Générales', {
            'fields': ('libelle', 'categorie')
        }),
        ('Tarification', {
            'fields': ('prix',),
            'description': 'Le prix doit être saisi en Dollars (USD)'
        }),
    )

    # Pour personnaliser l'affichage de la catégorie dans list_display
    def get_categorie_display(self, obj):
        return obj.get_categorie_display()
    get_categorie_display.short_description = 'Catégorie'
