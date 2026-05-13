from django.contrib import admin
from django.shortcuts import redirect
from .models import *

# ==========================================
# 1. CONFIGURATION GÉNÉRALE
# ==========================================
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['roleName']

@admin.register(Fonction)
class FonctionAdmin(admin.ModelAdmin):
    list_display = ['fonctionKey', 'userKey', 'autorisation']

@admin.register(ConfigurationHopital)
class ConfigurationHopitalAdmin(admin.ModelAdmin):
    list_display = ('taux_usd_en_cdf', 'derniere_mise_a_jour')
    def has_add_permission(self, request):
        return not ConfigurationHopital.objects.exists()

# ==========================================
# 2. PATIENTS & SERVICES
# ==========================================
@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('code_patient', 'noms', 'sexe', 'age', 'service', 'date_creation')
    search_fields = ('noms', 'code_patient', 'telephone')
    list_filter = ('service', 'sexe')
    readonly_fields = ('code_patient', 'date_creation')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'date_creation')

# ==========================================
# 3. CLINIQUE (GESTION DE L'ERREUR ATTRIBUTE ERROR)
# ==========================================

class DemandeExamenInline(admin.TabularInline):
    model = DemandeExamen
    extra = 0
    # On affiche bien le nouveau champ 'quantite'
    fields = ('prestation', 'quantite', 'indication', 'statut')

class OrdonnanceInline(admin.StackedInline):
    model = Ordonnance
    extra = 0
    show_change_link = True

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    # On utilise 'get_total_examens' défini plus bas au lieu de la propriété du modèle
    list_display = ('get_patient', 'medecin', 'get_total_examens', 'date_creation')
    list_filter = ('date_creation', 'medecin')
    search_fields = ('triage__patient__noms', 'hypothese_diagnostique')
    
    inlines = [DemandeExamenInline, OrdonnanceInline]

    def get_patient(self, obj):
        return obj.triage.patient.noms
    get_patient.short_description = "Patient"

    def get_total_examens(self, obj):
        """
        Calcul dynamique du total sans modifier models.py.
        Gère l'erreur 'demandeexamen_set' vs 'examens'
        """
        try:
            # On cherche d'abord via le related_name 'examens'
            examens_lies = obj.examens.all()
        except AttributeError:
            # Si absent, on utilise le nom par défaut de Django
            examens_lies = obj.demandeexamen_set.all()
        
        total = sum((ex.prestation.prix * ex.quantite) for ex in examens_lies if ex.prestation and ex.prestation.prix)
        return f"{total} USD"
    
    get_total_examens.short_description = "Total Prescrit"

@admin.register(SigneVital)
class SigneVitalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'temperature', 'tension_arterielle', 'date_prelevement')
    search_fields = ('patient__noms',)

# ==========================================
# 4. EXAMENS & ORDONNANCES
# ==========================================
@admin.register(Prestation)
class PrestationAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'categorie', 'prix')
    list_editable = ('prix',)
    search_fields = ('libelle',)

@admin.register(DemandeExamen)
class DemandeExamenAdmin(admin.ModelAdmin):
    list_display = ('prestation', 'quantite', 'get_patient_name', 'statut')
    list_filter = ('statut', 'prestation__categorie')
    
    def get_patient_name(self, obj):
        return obj.consultation.triage.patient.noms
    get_patient_name.short_description = "Patient"

@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'date_prescrite')

@admin.register(LigneMedicament)
class LigneMedicamentAdmin(admin.ModelAdmin):
    list_display = ('nom_medicament', 'posologie', 'statut')