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
    # 1. Les colonnes affichées dans la liste
    list_display = (
        'date_prelevement', 
        'patient', 
        'temperature', 
        'tension_arterielle', 
        'poids', 
        'frequence_cardiaque', 
        'infirmier'
    )

    # 2. Les filtres sur le côté droit
    # Permet de filtrer par date ou par l'infirmier qui a fait le prélèvement
    list_filter = ('date_prelevement', 'infirmier', 'temperature')

    # 3. La barre de recherche
    # Permet de chercher par le nom du patient ou le nom d'utilisateur de l'infirmier
    search_fields = ('patient__noms', 'infirmier__username', 'tension_arterielle')

    # 4. Organisation du formulaire de modification
    # On regroupe les constantes pour une lecture plus propre
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

    # 5. Rendre la date de prélèvement accessible mais non modifiable (lecture seule)
    readonly_fields = ('date_prelevement',)

    # Optionnel : permettre de modifier l'infirmier seulement si on est superadmin
    def save_model(self, request, obj, form, change):
        # Si c'est une nouvelle création et que l'infirmier n'est pas rempli
        if not obj.pk and not obj.infirmier:
            obj.infirmier = request.user
        super().save_model(request, obj, form, change)

# 12 et 13 

# 1. Permet d'ajouter/voir les examens directement dans la page Consultation
# class ExamenPrescritInline(admin.TabularInline):
#     model = ExamenPrescrit
#     extra = 1  # Nombre de lignes vides affichées par défaut
#     fields = ('prestation', 'quantite', 'prix_total', 'paye', 'termine', 'resultat')
#     readonly_fields = ('prix_total',) # On ne peut pas modifier le prix total à la main (calcul auto

class ExamenPrescritInline(admin.TabularInline):
    model = ExamenPrescrit
    readonly_fields = ['prix_total']
    extra = 0
    fields = ['prestation', 'quantite', 'prix_total', 'paye', 'termine']






@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    # Remplacement de date_creation par date_consultation (nom exact de ton modèle)
    list_display = ('id', 'patient', 'medecin', 'date_consultation', 'get_total_facture')
    
    # Remplacement ici aussi pour le filtre
    list_filter = ('date_consultation', 'medecin')
    
    search_fields = ('patient__noms', 'medecin__username')
    
    # L'inline doit être défini au-dessus de cette classe dans ton fichier
    inlines = [ExamenPrescritInline]

    def get_total_facture(self, obj):
        # Cette fonction calcule le total des examens liés (ex: Sida + Goutte)
        from django.db.models import Sum
        total = obj.examens_prescrits.aggregate(total=Sum('prix_total'))['total']
        return f"{total or 0} CDF"
    
    get_total_facture.short_description = 'Total à Payer'

@admin.register(ExamenPrescrit)
class ExamenPrescritAdmin(admin.ModelAdmin):
    # Correction E116 : 'termine' doit exister dans ton models.py
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
    list_editable = ('est_occupe',) # Permet de libérer un lit rapidement depuis la liste

@admin.register(OccupationLit)
class OccupationLitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'lit', 'date_admission', 'date_sortie', 'get_jours', 'get_total_cdf', 'est_paye')
    list_filter = ('est_paye', 'date_admission', 'lit__chambre')
    search_fields = ('patient__nom', 'lit__nom_lit', 'lit__chambre__numero') # Assure-toi que le modèle Patient a un champ 'nom'
    date_hierarchy = 'date_admission'
    
    # Configuration des champs calculés pour l'affichage
    def get_jours(self, obj):
        return f"{obj.nombre_jours} j"
    get_jours.short_description = "Durée"

    def get_total_cdf(self, obj):
        return f"{obj.total_facture_cdf:,.2f} CDF"
    get_total_cdf.short_description = "Total à payer"

    # Optionnel : Rendre certains champs en lecture seule pour éviter les erreurs de calcul manuel
    readonly_fields = ('date_admission',)


