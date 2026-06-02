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
    # Remettez 'type_ordonnance' ici
    list_display = ['consultation', 'date_prescrite', 'type_ordonnance', 'diagnostic']
    list_filter = ['type_ordonnance', 'date_prescrite'] # Et ici
    search_fields = ['consultation__triage__patient__noms']

# 3. Configuration de l'admin pour LigneMedicament
@admin.register(LigneMedicament)
class LigneMedicamentAdmin(admin.ModelAdmin):
    list_display = ('nom_medicament', 'posologie', 'duree', 'statut', 'ordonnance')
    list_filter = ('statut', 'ordonnance__type_ordonnance')
    search_fields = ('nom_medicament',)

@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):
    # Affiche le nom, la posologie, le statut et l'ordonnance associée
    list_display = ['nom', 'posologie', 'duree', 'statut', 'ordonnance_link']
    list_filter = ['statut']
    search_fields = ['nom', 'ordonnance__consultation__triage__patient__noms']
    
    # Petite astuce : ajoute un lien cliquable vers l'ordonnance dans la liste
    def ordonnance_link(self, obj):
        return str(obj.ordonnance)
    ordonnance_link.short_description = 'Ordonnance liée'


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
# 1. Permet de modifier les lits directement dans la fiche Chambre
class LitInline(admin.TabularInline):
    model = Lit
    extra = 1  # Nombre de lignes vides à afficher par défaut
    fields = ('nom_lit', 'est_occupe', 'est_actif')

@admin.register(TypeChambre)
class TypeChambreAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'prix_nuitée')
    search_fields = ('libelle',)
    list_editable = ('prix_nuitée',) # Permet de changer les prix directement depuis la liste

@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_chambre', 'get_prix', 'nb_lits', 'est_active')
    list_filter = ('type_chambre', 'est_active')
    search_fields = ('nom',)
    inlines = [LitInline] # Intégration des lits

    # Méthode pour afficher le prix lié au type dans la liste des chambres
    def get_prix(self, obj):
        return f"{obj.type_chambre.prix_nuitée} €"
    get_prix.short_description = 'Prix / Nuit'

    # Méthode pour voir rapidement le nombre de lits sans ouvrir la fiche
    def nb_lits(self, obj):
        return obj.lits.count()
    nb_lits.short_description = 'Nombre de lits'

@admin.register(Lit)
class LitAdmin(admin.ModelAdmin):
    list_display = ('nom_lit', 'chambre', 'est_occupe', 'est_actif')
    list_filter = ('est_occupe', 'est_actif', 'chambre__nom')
    search_fields = ('nom_lit', 'chambre__nom')
    list_editable = ('est_occupe', 'est_actif')



@admin.register(Hospitalisation)
class HospitalisationAdmin(admin.ModelAdmin):
    # Affichage des colonnes dans la liste
    list_display = (
        'patient', 
        'lit', 
        'date_entree', 
        'statut', 
        'date_sortie'
    )
    
    # Filtres latéraux pour une gestion rapide
    list_filter = ('statut', 'date_entree', 'lit__chambre')
    
    # Recherche par nom de patient ou nom de lit
    search_fields = ('patient__noms', 'lit__nom_lit', 'motif_admission')
    
    # Organisation des champs par blocs pour plus de clarté
    fieldsets = (
        ('Informations d\'Admission', {
            'fields': ('patient', 'lit', 'motif_admission')
        }),
        ('Suivi et État', {
            'fields': ('statut', 'date_entree', 'date_sortie', 'observations')
        }),
    )
    
    # Actions personnalisées (Optionnel : permet de marquer comme terminé depuis la liste)
    actions = ['marquer_comme_termine']

    def marquer_comme_termine(self, request, queryset):
        for obj in queryset:
            obj.statut = 'TERMINE'
            obj.save() # Le save() automatique gérera la libération du lit
        self.message_user(request, "Les hospitalisations sélectionnées ont été marquées comme terminées.")
    
    marquer_comme_termine.short_description = "Marquer comme terminées"




# ===================================================================================================
#
# maternite 
# ======================================================
# Inline pour afficher les consultations dans la page du dossier Maternite
# ======================================================
class ConsultationMaterniteInline(admin.TabularInline):
    model = ConsultationMaternite
    extra = 1  # Nombre de formulaires vides affichés par défaut
    fields = ['poids', 'tension_arterielle', 'hauteur_uterine', 'bruits_cardiaques_foetaux', 'prestation', 'effectue_par']
    readonly_fields = ['date_consultation']
    
    # Restreindre le choix des prestations dans l'interface inline
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "prestation":
            kwargs["queryset"] = Prestation.objects.filter(categorie='CONS_MAT')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

# ======================================================
# Administration du modèle Maternite
# ======================================================
@admin.register(Maternite)
class MaterniteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date_admission', 'terme_prevu', 'groupe_sanguin', 'enregistre_par')
    search_fields = ('patient__noms', 'patient__code_patient')
    list_filter = ('date_admission', 'enregistre_par')
    readonly_fields = ('date_admission',)
    
    # Intégration de l'inline pour voir les consultations dans le dossier maternité
    inlines = [ConsultationMaterniteInline]

    def patient_name(self, obj):
        return obj.patient.noms
    patient_name.short_description = 'Patiente'

# ======================================================
# Administration du modèle ConsultationMaternite
# ======================================================
@admin.register(ConsultationMaternite)
class ConsultationMaterniteAdmin(admin.ModelAdmin):
    list_display = ['dossier_maternite', 'date_consultation', 'poids', 'tension_arterielle', 'prestation', 'effectue_par']
    list_filter = ['date_consultation', 'effectue_par']
    search_fields = ['dossier_maternite__patient__noms']
    
    # Pour filtrer uniquement les prestations de type CONSULTATION MATERNITE dans l'admin
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "prestation":
            kwargs["queryset"] = Prestation.objects.filter(categorie='CONS_MAT')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



# =========================================================
# ACTE DE DECES 
# =========================================================
@admin.register(Deces)
class DecesAdmin(admin.ModelAdmin):
    # Colonnes affichées dans la liste des décès
    list_display = (
        'get_nom_patient', 
        'date_deces', 
        'certifie_par', 
        'etablissement', 
        'date_enregistrement'
    )
    
    # Recherche rapide dans l'interface admin
    search_fields = (
        'patient__noms',  # Assurez-vous que le modèle Patient a bien un champ 'noms'
        'nom_patient_externe', 
        'certifie_par'
    )
    
    # Filtres latéraux pour trier les données
    list_filter = ('date_deces', 'etablissement', 'date_enregistrement')
    
    # Organisation des formulaires en groupes pour plus de clarté
    fieldsets = (
        ('Identité du défunt', {
            'fields': ('patient', 'nom_patient_externe', 'date_naissance', 'lieu_naissance')
        }),
        ('Adresse du domicile', {
            'fields': ('adresse_avenue', 'adresse_numero', 'adresse_quartier', 'adresse_commune'),
            'classes': ('collapse',) # Le bloc est réduit par défaut
        }),
        ('Informations sur le décès', {
            'fields': ('date_deces', 'cause_deces')
        }),
        ('Certification médicale', {
            'fields': ('etablissement', 'certifie_par', 'numero_cnom')
        }),
        ('Informations complémentaires', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    # Lecture seule pour les champs générés automatiquement
    readonly_fields = ('date_enregistrement',)

    # Méthode pour afficher le nom du patient proprement
    def get_nom_patient(self, obj):
        if obj.patient:
            return str(obj.patient) # Retourne la valeur de __str__ du modèle Patient
        return obj.nom_patient_externe
    
    get_nom_patient.short_description = 'Patient / Défunt'
    get_nom_patient.admin_order_field = 'patient'