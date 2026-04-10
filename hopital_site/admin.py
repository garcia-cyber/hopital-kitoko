from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Sum

# ======================================================================
# INLINES (Doivent être définis AVANT les Admin qui les utilisent)
# ======================================================================

class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 1 
    readonly_fields = ('montant_comptable_cdf',)

class ExamenPrescritInline(admin.TabularInline):
    model = ExamenPrescrit
    readonly_fields = ['prix_total']
    extra = 0
    fields = ['prestation', 'quantite', 'prix_total', 'paye', 'termine']

class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0
    readonly_fields = ('medicament', 'quantite', 'type_vente', 'prix_unitaire_applique')

class LigneOrdonnanceInline(admin.TabularInline):
    """Suivi des médicaments dans l'ordonnance (Caisse et Pharmacie)"""
    model = LigneOrdonnance
    extra = 0  
    readonly_fields = ('quantite_payee', 'quantite_delivree', 'date_creation')
    fields = ('medicament', 'quantite_prescrite', 'quantite_payee', 'quantite_delivree')

# ======================================================================
# 1. PARAMÉTRAGES ET ACTEURS
# ======================================================================

@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
    list_display = ['fonction']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['nomService']

@admin.register(Profil) 
class ProfilAdmin(admin.ModelAdmin):
    list_display = ['nomComplet','userProfil','sexe','phone','adresse','fonction','service' ,'date_register']

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['noms','sexeP','ageP','phone_responsable','adresseP','service','date_registerP']

@admin.register(ConfigurationHopital)
class ConfigurationHopitalAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not ConfigurationHopital.objects.exists()
    def has_delete_permission(self, request, obj=None):
        return False
    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')

# ======================================================================
# 2. FINANCES ET COMPTABILITÉ
# ======================================================================

@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'prix_cdf')
    list_filter = ('categorie',)
    search_fields = ('libelle',)

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('patient', 'prestation', 'prix_fixe_cdf', 'taux_fixe', 'reste_a_payer', 'date_emission')
    readonly_fields = ('prix_fixe_cdf', 'taux_fixe')
    inlines = [PaiementInline]
    list_filter = ('date_emission',)

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('facture', 'montant_physique', 'devise', 'montant_comptable_cdf', 'date_paiement')
    readonly_fields = ('montant_comptable_cdf',)
    list_filter = ('devise', 'date_paiement')

@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('motif', 'montant', 'devise', 'valeur_cdf', 'date_depense')
    readonly_fields = ('valeur_cdf',)
    list_filter = ('date_depense', 'devise')

# ======================================================================
# 3. CLINIQUE ET MÉDICAL
# ======================================================================

@admin.register(SignesVitaux)
class SignesVitauxAdmin(admin.ModelAdmin):
    list_display = ('date_prelevement', 'patient', 'temperature', 'tension_arterielle', 'poids', 'infirmier')
    list_filter = ('date_prelevement', 'infirmier')
    search_fields = ('patient__noms', 'infirmier__username')
    readonly_fields = ('date_prelevement',)

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.infirmier:
            obj.infirmier = request.user
        super().save_model(request, obj, form, change)

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'medecin', 'date_consultation', 'get_total_facture')
    list_filter = ('date_consultation', 'medecin')
    search_fields = ('patient__noms', 'medecin__username')
    inlines = [ExamenPrescritInline]

    def get_total_facture(self, obj):
        total = obj.examens_prescrits.aggregate(total=Sum('prix_total'))['total']
        return f"{total or 0} CDF"
    get_total_facture.short_description = 'Total Examens'

@admin.register(ExamenPrescrit)
class ExamenPrescritAdmin(admin.ModelAdmin):
    list_display = ('prestation', 'consultation', 'prix_total', 'paye', 'termine')
    list_filter = ('paye', 'termine')

# ======================================================================
# 4. HOSPITALISATION
# ======================================================================

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ('numero', 'type_chambre', 'prix_journalier')

@admin.register(Lit)
class LitAdmin(admin.ModelAdmin):
    list_display = ('nom_lit', 'chambre', 'est_occupe')
    list_editable = ('est_occupe',)

@admin.register(OccupationLit)
class OccupationLitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'lit', 'date_admission', 'date_sortie', 'total_facture_cdf', 'est_paye')
    readonly_fields = ('date_admission',)

# ======================================================================
# 5. PHARMACIE ET STOCK (CORRIGÉ)
# ======================================================================

@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ('designation', 'forme', 'dosage', 'get_stock_format', 'prix_vente_detail', 'statut_alerte')
    list_filter = ('forme',)
    search_fields = ('designation',)
    readonly_fields = ('quantite_stock_pieces', 'prix_achat_unitaire_moyen')

    # Correction : On sécurise l'appel des properties du modèle
    def get_stock_format(self, obj):
        try:
            return f"{obj.stock_en_cartons} Ctn / {obj.reste_en_pieces} Pcs"
        except:
            return "Erreur calcul"
    get_stock_format.short_description = "Stock"

    # Correction : Sécurisation du badge visuel
    def statut_alerte(self, obj):
        try:
            if obj.est_en_alerte:
                return format_html(
                    '<span style="color: white; background: #d9534f; padding: 4px 8px; border-radius: 4px; font-weight: bold;">⚠️ ALERTE</span>'
                )
            return format_html(
                '<span style="color: white; background: #5cb85c; padding: 4px 8px; border-radius: 4px; font-weight: bold;">✅ OK</span>'
            )
        except:
            return "N/A"
    statut_alerte.short_description = "État"

@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'medecin', 'date_creation', 'est_delivré')
    list_filter = ('est_delivré', 'date_creation', 'medecin')
    search_fields = ('consultation__patient__noms', 'medecin__username', 'id')
    inlines = [LigneOrdonnanceInline]
    readonly_fields = ('date_creation',)

    def get_patient(self, obj):
        return obj.consultation.patient.noms if obj.consultation else "N/A"
    get_patient.short_description = 'Patient'

@admin.register(LigneOrdonnance)
class LigneOrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('medicament', 'ordonnance', 'quantite_prescrite', 'quantite_payee', 'quantite_delivree')
    list_filter = ('medicament',)

@admin.register(VentePharmacie)
class VentePharmacieAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_vente', 'vendeur', 'total_cdf', 'statut')
    inlines = [LigneVenteInline]
    actions = ['marquer_comme_annulee']

    def marquer_comme_annulee(self, request, queryset):
        queryset.update(statut='ANNULE')
        self.message_user(request, "Ventes sélectionnées ont été annulées.")

@admin.register(BonEntree)
class BonEntreeAdmin(admin.ModelAdmin):
    list_display = ('date_reception', 'medicament', 'nb_cartons_recus', 'fournisseur')

@admin.register(LogPharmacie)
class LogPharmacieAdmin(admin.ModelAdmin):
    list_display = ('date_action', 'utilisateur', 'action', 'details')
    def has_add_permission(self, request): return False