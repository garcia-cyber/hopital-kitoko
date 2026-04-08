from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.utils.safestring import mark_safe

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

# 8
@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('patient', 'prestation', 'prix_fixe_cdf', 'taux_fixe', 'reste_a_payer', 'date_emission')
    readonly_fields = ('prix_fixe_cdf', 'taux_fixe')
    inlines = [PaiementInline]
    list_filter = ('date_emission',)

# 9. PAIEMENTS (Vue séparée pour la comptabilité)
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('facture', 'montant_physique', 'devise', 'montant_comptable_cdf', 'date_paiement')
    readonly_fields = ('montant_comptable_cdf',)
    list_filter = ('devise', 'date_paiement')

# 10. DÉPENSES
@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('motif', 'montant', 'devise', 'valeur_cdf', 'date_depense')
    readonly_fields = ('valeur_cdf',)
    list_filter = ('date_depense', 'devise')

# 11
@admin.register(SignesVitaux)
class SignesVitauxAdmin(admin.ModelAdmin):
    list_display = (
        'date_prelevement', 
        'patient', 
        'temperature', 
        'tension_arterielle', 
        'poids', 
        'frequence_cardiaque', 
        'infirmier'
    )
    list_filter = ('date_prelevement', 'infirmier', 'temperature')
    search_fields = ('patient__noms', 'infirmier__username', 'tension_arterielle')

    fieldsets = (
        ('Informations Générales', {
            'fields': ('patient', 'infirmier')
        }),
        ('Constantes Vitales', {
            'fields': (
                ('temperature', 'tension_arterielle'),
                ('poids', 'frequence_cardiaque'),
                ('frequence_respiratoire', 'saturation_oxygene')
            )
        }),
    )
    readonly_fields = ('date_prelevement',)

    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.infirmier:
            obj.infirmier = request.user
        super().save_model(request, obj, form, change)

# 12 et 13 
class ExamenPrescritInline(admin.TabularInline):
    model = ExamenPrescrit
    readonly_fields = ['prix_total']
    extra = 0
    fields = ['prestation', 'quantite', 'prix_total', 'paye', 'termine']

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'medecin', 'date_consultation', 'get_total_facture')
    list_filter = ('date_consultation', 'medecin')
    search_fields = ('patient__noms', 'medecin__username')
    inlines = [ExamenPrescritInline]

    def get_total_facture(self, obj):
        from django.db.models import Sum
        total = obj.examens_prescrits.aggregate(total=Sum('prix_total'))['total']
        return f"{total or 0} CDF"
    get_total_facture.short_description = 'Total à Payer'

@admin.register(ExamenPrescrit)
class ExamenPrescritAdmin(admin.ModelAdmin):
    list_display = ('prestation', 'consultation', 'prix_total', 'paye', 'termine')
    list_filter = ('paye', 'termine', 'date_prescription')
    readonly_fields = ['prix_total']

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ('numero', 'type_chambre', 'get_prix_cdf')
    list_filter = ('type_chambre',)
    search_fields = ('numero',)

    def get_prix_cdf(self, obj):
        return f"{obj.prix_journalier:,.2f} CDF"
    get_prix_cdf.short_description = "Prix Journalier"

@admin.register(Lit)
class LitAdmin(admin.ModelAdmin):
    list_display = ('nom_lit', 'chambre', 'est_occupe')
    list_filter = ('est_occupe', 'chambre__type_chambre')
    search_fields = ('nom_lit', 'chambre__numero')
    list_editable = ('est_occupe',)

@admin.register(OccupationLit)
class OccupationLitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'lit', 'date_admission', 'date_sortie', 'get_jours', 'get_total_cdf', 'est_paye')
    list_filter = ('est_paye', 'date_admission', 'lit__chambre')
    search_fields = ('patient__nom', 'lit__nom_lit', 'lit__chambre__numero')
    date_hierarchy = 'date_admission'
    
    def get_jours(self, obj):
        return f"{obj.nombre_jours} j"
    get_jours.short_description = "Durée"

    def get_total_cdf(self, obj):
        return f"{obj.total_facture_cdf:,.2f} CDF"
    get_total_cdf.short_description = "Total à payer"

    readonly_fields = ('date_admission',)

@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_patient', 'medecin', 'date_creation', 'est_delivré')
    list_filter = ('est_delivré', 'date_creation', 'medecin')
    search_fields = ('consultation__patient__noms', 'medecin__username', 'id')
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('consultation', 'medecin')
        }),
        ('Détails Médicaux', {
            'fields': ('contenu_prescription', 'instructions_posologie')
        }),
        ('Statut Pharmacie', {
            'fields': ('est_delivré',),
        }),
    )
    readonly_fields = ('date_creation',)

    def get_patient(self, obj):
        return obj.consultation.patient.noms
    get_patient.short_description = 'Patient'

# --- 2. GESTION DES MÉDICAMENTS (STOCK) ---
@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = (
        'designation', 
        'forme', 
        'dosage', 
        'get_stock_format', 
        'prix_vente_detail', 
        'prix_vente_gros', 
        'statut_alerte'
    )
    list_filter = ('forme',) 
    search_fields = ('designation', 'forme')
    readonly_fields = ('quantite_stock_pieces', 'prix_achat_unitaire_moyen')

    def get_stock_format(self, obj):
        return f"{obj.stock_en_cartons} Ctn / {obj.reste_en_pieces} Pcs"
    get_stock_format.short_description = "Stock Actuel"

    # CORRECTION ICI POUR L'ERREUR "args or kwargs must be provided"
    def statut_alerte(self, obj):
        if obj.est_en_alerte:
            # On utilise format_html avec des arguments séparés pour éviter l'erreur Django
            return format_html('<span style="color: {}; font-weight: bold;">{}</span>', "red", "⚠️ RÉAPPROVISIONNER")
        return format_html('<span style="color: {};">{}</span>', "green", "✅ OK")
    statut_alerte.short_description = "État"

# --- 3. RÉCEPTION DE MARCHANDISE ---
@admin.register(BonEntree)
class BonEntreeAdmin(admin.ModelAdmin):
    list_display = ('date_reception', 'medicament', 'nb_cartons_recus', 'prix_achat_carton', 'fournisseur')
    list_filter = ('date_reception', 'fournisseur')
    search_fields = ('medicament__designation',)

# --- 4. LES VENTES (AVEC LIGNES INTÉGRÉES) ---
class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 0
    readonly_fields = ('medicament', 'quantite', 'type_vente', 'prix_unitaire_applique')

@admin.register(VentePharmacie)
class VentePharmacieAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_vente', 'vendeur', 'total_cdf', 'get_total_usd', 'statut')
    list_filter = ('statut', 'date_vente', 'vendeur')
    inlines = [LigneVenteInline]
    actions = ['marquer_comme_annulee']

    def get_total_usd(self, obj):
        return f"{obj.total_en_usd()} $"
    get_total_usd.short_description = "Total (USD)"

    def marquer_comme_annulee(self, request, queryset):
        for vente in queryset:
            if vente.statut != 'ANNULE':
                vente._user_annulation = request.user 
                vente.statut = 'ANNULE'
                vente.save()
        self.message_user(request, "Les ventes sélectionnées ont été annulées et le stock remis en place.")
    marquer_comme_annulee.short_description = "Annuler les ventes sélectionnées"

# --- 5. AUDIT / LOGS (LECTURE SEULE) ---
@admin.register(LogPharmacie)
class LogPharmacieAdmin(admin.ModelAdmin):
    list_display = ('date_action', 'utilisateur', 'action', 'details')
    list_filter = ('action', 'date_action', 'utilisateur')
    search_fields = ('details',)
    
    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False