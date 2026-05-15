from django.contrib import admin
from django.utils import timezone
from .models import *

# ==========================================
# 1. CONFIGURATION & FINANCE
# ==========================================
@admin.register(ConfigurationHopital)
class ConfigurationHopitalAdmin(admin.ModelAdmin):
    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')
    
    def has_add_permission(self, request):
        # Empêche de créer plusieurs configurations de taux
        return not ConfigurationHopital.objects.exists()

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'service', 'montant_verse', 'devise', 'date_paiement', 'caissier')
    list_filter = ('service', 'devise', 'date_paiement')
    search_fields = ('patient__noms', 'id')
    date_hierarchy = 'date_paiement'

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'get_patient', 'get_service', 'date_emission')
    search_fields = ('numero_facture', 'paiement__patient__noms')

    def get_patient(self, obj):
        return obj.paiement.patient.noms
    get_patient.short_description = "Patient"

    def get_service(self, obj):
        return obj.paiement.get_service_display()
    get_service.short_description = "Service"

# ==========================================
# 2. UTILISATEURS & RÔLES
# ==========================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['roleName']

@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
    list_display = ['fonctionKey', 'userKey', 'autorisation']

# ==========================================
# 3. PATIENTS & SERVICES
# ==========================================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_creation')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('code_patient', 'noms', 'sexe', 'age', 'service', 'fiche_payee', 'date_creation')
    search_fields = ('noms', 'code_patient', 'telephone')
    list_filter = ('service', 'sexe', 'fiche_payee')
    readonly_fields = ('code_patient', 'date_creation')

# ==========================================
# 4. CLINIQUE (CONSULTATIONS & EXAMENS)
# ==========================================
class DemandeExamenInline(admin.TabularInline):
    model = DemandeExamen
    extra = 0
    fields = ('prestation', 'quantite', 'indication', 'statut')

class OrdonnanceInline(admin.StackedInline):
    model = Ordonnance
    extra = 0
    show_change_link = True

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('get_patient', 'medecin', 'get_total_usd', 'date_creation')
    list_filter = ('date_creation', 'medecin')
    search_fields = ('triage__patient__noms', 'hypothese_diagnostique')
    inlines = [DemandeExamenInline, OrdonnanceInline]

    def get_patient(self, obj):
        return obj.triage.patient.noms
    get_patient.short_description = "Patient"

    def get_total_usd(self, obj):
        # Utilisation du related_name='examens' défini dans ton models.py
        examens = obj.examens.all()
        total = sum((ex.prestation.prix * ex.quantite) for ex in examens if ex.prestation)
        return f"{total:.2f} USD"
    get_total_usd.short_description = "Total Prescrit"

@admin.register(SigneVital)
class SigneVitalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'temperature', 'tension_arterielle', 'date_prelevement', 'est_consulte')
    list_filter = ('est_consulte', 'date_prelevement')
    search_fields = ('patient__noms',)

# ==========================================
# 5. PRESTATIONS & PHARMACIE
# ==========================================
@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'prix')
    list_editable = ('prix',)
    list_filter = ('categorie',)
    search_fields = ('libelle',)

@admin.register(DemandeExamen)
class DemandeExamenAdmin(admin.ModelAdmin):
    list_display = ('prestation', 'quantite', 'get_patient', 'statut', 'date_demande')
    list_filter = ('statut', 'prestation__categorie', 'date_demande')
    
    def get_patient(self, obj):
        return obj.consultation.triage.patient.noms
    get_patient.short_description = "Patient"

@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'type_ordonnance', 'date_prescrite')
    list_filter = ('type_ordonnance', 'date_prescrite')

@admin.register(LigneMedicament)
class LigneMedicamentAdmin(admin.ModelAdmin):
    list_display = ('nom_medicament', 'posologie', 'statut', 'ordonnance')
    list_filter = ('statut',)