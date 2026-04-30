from django.contrib import admin
from .models import *
from django.utils.html import format_html
from django.db.models import Sum

# ======================================================================
# INLINES (Définis AVANT les Admin)
# ======================================================================

class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
    # On utilise les noms exacts de ton modèle Paiement
    readonly_fields = ['date_paiement', 'montant_comptable_cdf']
    fields = ['montant_physique', 'devise', 'mode_paiement', 'reference_transaction', 'date_paiement', 'montant_comptable_cdf']
    can_delete = False

class ExamenPrescritInline(admin.TabularInline):
    model = ExamenPrescrit
    readonly_fields = ['prix_total']
    extra = 0
    fields = ['prestation', 'quantite', 'prix_total', 'paye', 'termine']

class LigneVenteInline(admin.TabularInline):
    # CORRECTION : model = LigneVente qui est lié à FacturePharmacie (via champ 'vente')
    model = LigneVente
    extra = 0
    fields = ('medicament', 'quantite', 'prix_unitaire_applique')
    readonly_fields = ('prix_unitaire_applique',)

class LigneOrdonnanceInline(admin.TabularInline):
    model = LigneOrdonnance
    extra = 0  
    readonly_fields = ('quantite_payee', 'quantite_delivree')
    fields = ('medicament', 'quantite_prescrite', 'quantite_payee', 'quantite_delivree')

class LigneFacturePharmaInline(admin.TabularInline):
    model = LigneFacturePharma
    extra = 0
    readonly_fields = ['sous_total']
    fields = ['medicament', 'quantite', 'prix_unitaire_applique', 'sous_total']
    can_delete = False

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
    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')

# ======================================================================
# 2. FINANCES ET COMPTABILITÉ
# ======================================================================

@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'prix_cdf')
    list_filter = ('categorie',)

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('patient', 'prestation', 'prix_fixe_cdf', 'taux_fixe', 'reste_a_payer', 'date_emission')
    inlines = [PaiementInline]

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('id', 'facture', 'facture_pharma', 'montant_physique', 'devise', 'montant_comptable_cdf', 'date_paiement')
    readonly_fields = ('montant_comptable_cdf',)

# ======================================================================
# 3. CLINIQUE ET MÉDICAL
# ======================================================================

@admin.register(SignesVitaux)
class SignesVitauxAdmin(admin.ModelAdmin):
    list_display = ('date_prelevement', 'patient', 'temperature', 'tension_arterielle', 'poids', 'infirmier')

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'medecin', 'date_consultation')
    inlines = [ExamenPrescritInline]

@admin.register(ExamenPrescrit)
class ExamenPrescritAdmin(admin.ModelAdmin):
    list_display = ('prestation', 'consultation', 'prix_total', 'paye', 'termine')

# ======================================================================
# 4. PHARMACIE ET STOCK
# ======================================================================

@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    list_display = ('designation', 'forme', 'dosage', 'get_stock_format', 'prix_vente_detail', 'statut_alerte')
    
    def get_stock_format(self, obj):
        return f"{obj.stock_en_cartons} Ctn / {obj.reste_en_pieces} Pcs"
    get_stock_format.short_description = "Stock"

    def statut_alerte(self, obj):
        if obj.quantite_stock_pieces <= obj.seuil_alerte:
            return format_html('<span style="background: #d9534f; color: white; padding: 3px 7px; border-radius: 4px;">⚠️ ALERTE</span>')
        return format_html('<span style="background: #5cb85c; color: white; padding: 3px 7px; border-radius: 4px;">✅ OK</span>')

@admin.register(FacturePharmacie)
class FacturePharmacieAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_client', 'total_a_payer_cdf', 'get_reste', 'get_statut', 'date_facture')
    # On met les Inlines liés à FacturePharmacie
    inlines = [LigneVenteInline, LigneFacturePharmaInline, PaiementInline]

    def get_client(self, obj):
        return obj.patient.noms if obj.patient else obj.nom_client_externe
    get_client.short_description = "Client/Patient"

    def get_reste(self, obj):
        return f"{obj.reste_a_payer} CDF"
    get_reste.short_description = "Reste"

    def get_statut(self, obj):
        s = obj.statut_paiement
        color = "green" if s == 'SOLDE' else "orange" if s == 'PARTIEL' else "red"
        return format_html('<b style="color: {};">{}</b>', color, s)

# SOLUTION DE L'ERREUR E202 :
# On ne peut PAS utiliser LigneVenteInline ici car ton modèle LigneVente 
# n'a pas de ForeignKey vers VentePharmacie (il est lié à FacturePharmacie).
@admin.register(VentePharmacie)
class VentePharmacieAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_vente', 'vendeur', 'total_cdf', 'statut')
    # inlines = [LigneVenteInline]  <-- C'ÉTAIT CETTE LIGNE LE PROBLÈME. ELLE EST RETIRÉE.

@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'medecin', 'date_creation', 'est_delivré')
    inlines = [LigneOrdonnanceInline]

# ======================================================================
# 5. MATÉRIEL ET MAINTENANCE
# ======================================================================

@admin.register(Materiel)
class MaterielAdmin(admin.ModelAdmin):
    list_display = ('numero_serie', 'nom', 'marque', 'service_affecte', 'etat_actuel')
    list_filter = ('service_affecte', 'etat_actuel')
    search_fields = ('nom', 'numero_serie')
    list_editable = ('etat_actuel',)

@admin.register(Maintenance)
class MaintenanceAdmin(admin.ModelAdmin):
    list_display = ('materiel', 'description_panne', 'est_repare', 'date_reparation')
    list_filter = ('est_repare', 'date_reparation')

# ======================================================================
# 6. RESSOURCES HUMAINES
# ======================================================================

@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = ('get_mat', 'user_name', 'type_contrat', 'date_embauche', 'salaire_base')
    readonly_fields = ('matricule',)

    def get_mat(self, obj):
        return format_html('<b>{}</b>', obj.matricule)
    get_mat.short_description = "Matricule"

    def user_name(self, obj):
        return f"{obj.user.last_name} {obj.user.first_name}"

# ======================================================================
# 7. LOGS ET LIGNES
# ======================================================================

@admin.register(LigneFacturePharma)
class LigneFacturePharmaAdmin(admin.ModelAdmin):
    list_display = ('facture', 'medicament', 'quantite', 'sous_total')

@admin.register(LogPharmacie)
class LogPharmacieAdmin(admin.ModelAdmin):
    list_display = ('date_action', 'utilisateur', 'action')