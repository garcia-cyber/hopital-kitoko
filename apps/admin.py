from django.contrib import admin
from django.utils import timezone
from .models import *

# 1. CONFIGURATION ET ADMINISTRATION ====================================
@admin.register(ConfigurationHopital)
class ConfigurationHopitalAdmin(admin.ModelAdmin):
    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('roleName',)

@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
    list_display = ('userKey', 'fonctionKey', 'autorisation')

# 2. GESTION DES PATIENTS ET SERVICES ==================================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('code_patient', 'noms', 'sexe', 'type_patient', 'est_en_regle')
    list_filter = ('type_patient', 'sexe', 'service')
    search_fields = ('noms', 'code_patient')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_creation')

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'contact_responsable')

# 3. CONSULTATIONS ET SOINS ============================================
@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'medecin', 'consultation_payee')
    list_filter = ('consultation_payee', 'date_creation')

@admin.register(SigneVital)
class SigneVitalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'temperature', 'tension_arterielle', 'date_prelevement')

@admin.register(DemandeExamen)
class DemandeExamenAdmin(admin.ModelAdmin):
    list_display = ('prestation', 'consultation', 'statut', 'date_demande')
    list_filter = ('statut', 'prestation__categorie')

@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'type_ordonnance', 'date_prescrite')

admin.site.register(Medicament)
admin.site.register(LigneMedicament)

# 4. FINANCES ET FACTURATION ===========================================
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'service', 'montant_verse', 'devise', 'caissier', 'date_paiement')
    list_filter = ('service', 'devise', 'date_paiement')
    search_fields = ('patient__noms',)

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'paiement', 'date_emission')

@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('motif', 'montant', 'devise', 'auteur', 'date_depense')
    list_filter = ('motif', 'devise')

# 5. HOSPITALISATION ET MATERNITÉ ======================================
@admin.register(Hospitalisation)
class HospitalisationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'lit', 'statut', 'cout_total')
    list_filter = ('statut',)

@admin.register(SuiviQuotidien)
class SuiviQuotidienAdmin(admin.ModelAdmin):
    list_display = ('hospitalisation', 'date_suivi', 'infirmier')

admin.site.register([TypeChambre, Chambre, Lit])
admin.site.register(Maternite)
admin.site.register(ConsultationMaternite)

# 6. PHARMACIE ET AUTRES ===============================================
@admin.register(ProduitPharmacie)
class ProduitPharmacieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'dosage', 'prix_vente', 'stock_total')

@admin.register(SortiePharmacie)
class SortiePharmacieAdmin(admin.ModelAdmin):
    list_display = ('produit', 'quantite_vendue', 'date_sortie', 'get_montant_paiement')

    def get_montant_paiement(self, obj):
        return f"{obj.paiement.montant_verse} {obj.paiement.devise}"
    get_montant_paiement.short_description = 'Montant Total'

admin.site.register(LotPharmacie)
admin.site.register(Prestation)
admin.site.register(Deces)
admin.site.register(Orientation)
admin.site.register(SoinOccasionnel)