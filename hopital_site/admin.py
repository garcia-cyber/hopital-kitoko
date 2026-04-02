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
	list_display = ['noms','sexeP','ageP','phone_responsable','adresseP','service','date_registerP']

# 5. GESTION DU TAUX UNIQUE (Singleton)
@admin.register(ConfigurationHopital)
class ConfigurationHopitalAdmin(admin.ModelAdmin):
    # Empêche d'ajouter une deuxième ligne si une existe déjà
    def has_add_permission(self, request):
        if ConfigurationHopital.objects.exists():
            return False
        return True

    # Empêche la suppression du taux pour éviter de casser les calculs
    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')

# 6. CATALOGUE DES PRESTATIONS
@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'prix_cdf')
    list_filter = ('categorie',)
    search_fields = ('libelle',)



# 7. FACTURES (Avec vue des paiements à l'intérieur)
class PaiementInline(admin.TabularInline):
    """Permet de voir et d'ajouter des paiements directement dans la facture"""
    model = Paiement
    extra = 1 # Propose une ligne vide pour un nouveau versement
    readonly_fields = ('montant_comptable_cdf',)

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('patient', 'prestation', 'prix_fixe_cdf', 'taux_fixe', 'reste_a_payer', 'date_emission')
    readonly_fields = ('prix_fixe_cdf', 'taux_fixe')
    inlines = [PaiementInline]
    list_filter = ('date_emission',)

# 8. PAIEMENTS (Vue séparée pour la comptabilité)
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('facture', 'montant_physique', 'devise', 'montant_comptable_cdf', 'date_paiement')
    readonly_fields = ('montant_comptable_cdf',)
    list_filter = ('devise', 'date_paiement')

# 9. DÉPENSES
@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('motif', 'montant', 'devise', 'valeur_cdf', 'date_depense')
    readonly_fields = ('valeur_cdf',)
    list_filter = ('date_depense', 'devise')