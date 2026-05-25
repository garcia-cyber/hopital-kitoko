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
    
class LigneMedicamentInline(admin.TabularInline): # TabularInline affiche sous forme de tableau
    model = LigneMedicament
    extra = 1  # Nombre de lignes vides pour ajouter rapidement des médicaments
    fields = ('nom_medicament', 'posologie', 'duree', 'statut')

# 2. Configuration de l'admin pour Ordonnance
@admin.register(Ordonnance)
class OrdonnanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'consultation', 'type_ordonnance', 'date_prescrite')
    list_filter = ('type_ordonnance', 'date_prescrite')
    search_fields = ('consultation__triage__patient__noms',) # Permet de chercher par nom de patient
    inlines = [LigneMedicamentInline] # C'est ici que le lien se fait

# 3. Configuration de l'admin pour LigneMedicament
@admin.register(LigneMedicament)
class LigneMedicamentAdmin(admin.ModelAdmin):
    list_display = ('nom_medicament', 'posologie', 'duree', 'statut', 'ordonnance')
    list_filter = ('statut', 'ordonnance__type_ordonnance')
    search_fields = ('nom_medicament',)


# ==================================================================================================
@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    # 1. Configuration des colonnes visibles dans la liste
    list_display = ('id', 'date_depense', 'motif', 'montant_affiche', 'beneficiaire', 'auteur')
    
    # 2. Liens cliquables pour ouvrir une dépense
    list_display_links = ('id', 'motif')
    
    # 3. Filtres rapides latéraux (très pratique pour la comptabilité)
    list_filter = ('devise', 'motif', 'date_depense', 'auteur')
    
    # 4. Barre de recherche intelligente
    search_fields = ('description', 'beneficiaire', 'auteur__username', 'montant')
    
    # 5. Tri par défaut (la dépense la plus récente s'affiche en premier)
    ordering = ('-date_depense',)
    
    # 6. Rendre le champ auteur automatique (met l'utilisateur connecté par défaut)
    readonly_fields = ('date_depense',)

    def montant_affiche(self, obj):
        """ Affiche proprement le montant avec sa devise en couleur dans l'admin """
        if obj.devise == 'USD':
            return f"{obj.montant} USD"
        return f"{obj.montant} CDF"
    montant_affiche.short_description = "Montant"
    montant_affiche.admin_order_field = 'montant'

    def save_model(self, request, obj, form, change):
        """ 
        Intercepte la sauvegarde dans l'admin Django pour attribuer l'auteur 
        et attraper proprement l'erreur de validation du solde insuffisant.
        """
        # Si c'est une nouvelle dépense, l'auteur devient l'utilisateur connecté
        if not change:
            obj.auteur = request.user
            
        try:
            # force la validation du modèle (execute la méthode clean())
            obj.full_clean()
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            # En cas de solde insuffisant, renvoie l'erreur sous forme de message d'alerte rouge
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"Erreur : {error}")


# =================================================================================================================
@admin.register(TypeChambre)
class TypeChambreAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'description')
    search_fields = ('libelle',)


class LitInline(admin.TabularInline):
    """
    Permet d'ajouter, modifier ou voir les lits d'une chambre 
    directement depuis la page de modification de cette chambre.
    """
    model = Lit
    extra = 1 # Nombre de lignes vides affichées par défaut pour ajouter de nouveaux lits
    fields = ('nom_ou_code', 'est_occupe', 'est_actif')


@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = (
        'nom_ou_numero', 
        'type_chambre', 
        'prix_par_jour', 
        'localisation', 
        'est_active',
        'afficher_lits_total',       # Colonne personnalisée basée sur ta property
        'afficher_lits_dispo'        # Colonne personnalisée basée sur ta property
    )
    list_filter = ('type_chambre', 'est_active', 'localisation')
    search_fields = ('nom_ou_numero', 'localisation')
    ordering = ('nom_ou_numero',)
    
    # Intégration des lits directement dans la fiche de la chambre
    inlines = [LitInline]

    # --- Configuration de l'affichage des properties dans la liste ---

    def afficher_lits_total(self, obj):
        return obj.nombre_lits_total
    afficher_lits_total.short_description = "Lits Total" # Titre de la colonne

    def afficher_lits_dispo(self, obj):
        total_dispo = obj.nombre_lits_disponibles
        if total_dispo == 0:
            return "❌ Aucun lit libre"
        return f"🟢 {total_dispo} libre(s)"
    afficher_lits_dispo.short_description = "Disponibles"


@admin.register(Lit)
class LitAdmin(admin.ModelAdmin):
    list_display = ('nom_ou_code', 'chambre', 'get_type_chambre', 'est_occupe', 'est_actif')
    list_filter = ('est_occupe', 'est_actif', 'chambre__type_chambre', 'chambre')
    search_fields = ('nom_ou_code', 'chambre__nom_ou_numero')
    list_editable = ('est_occupe', 'est_actif') # Permet de cocher/décocher directement depuis la liste

    def get_type_chambre(self, obj):
        """ Récupère le type de chambre à travers la relation ForeignKey """
        return obj.chambre.type_chambre.libelle
    get_type_chambre.short_description = "Type de Chambre"