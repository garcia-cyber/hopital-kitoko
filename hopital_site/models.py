from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError

# Create your models here.

# 1
# =============================================
#   TYPE DE FONCTION 
class Fonction(models.Model):
    fonction = models.CharField(max_length = 30) 

    def __str__(self):
        return self.fonction

# 2
# =============================================
# SERVICE
#
class Service(models.Model):
    nomService = models.CharField(max_length = 40) 

    def __str__(self):
        return self.nomService  
# 3
# =============================================
# PROFIL 
# 
class Profil(models.Model):
    nomComplet = models.CharField(max_length = 50 , null = True) 
    CHOIX_SEXE = [
        ('masculin','Masculin') ,
        ('feminin', 'Feminin')
    ]
    sexe = models.CharField(max_length = 15 , choices = CHOIX_SEXE)
    phone = models.CharField(max_length = 15)
    adresse = models.CharField(max_length = 50)
    fonction = models.ForeignKey(Fonction, on_delete = models.SET_NULL, null = True) 
    service  = models.ForeignKey(Service , on_delete = models.SET_NULL , null = True) 
    date_register = models.DateField(auto_now_add = True)
    userProfil = models.ForeignKey(User , on_delete = models.SET_NULL, null = True)

    def __str__(self):

        return self.nomComplet

# 4
# ================================================
# PATIENT 
#
class Patient(models.Model):
    noms = models.CharField(max_length = 50)
    CHOIX_SEXE = [
        ('masculin','Masculin') ,
        ('feminin', 'Feminin')
    ]
    sexeP = models.CharField(max_length = 15 , choices = CHOIX_SEXE) 
    ageP = models.IntegerField()
    phone_responsable = models.CharField(max_length =15)
    adresseP = models.CharField(max_length = 60) 
    service  = models.ForeignKey(Service , on_delete = models.SET_NULL , null =True)
    date_registerP = models.DateField(auto_now_add = True)


    def __str__(self):
        return self.noms 

    # --- LOGIQUE DE LA FICHE ANNUELLE ---
    
    def a_une_fiche_valide(self):
        """ Vérifie si le patient a payé une fiche il y a moins de 365 jours """
        un_an_en_arriere = timezone.now().date() - timedelta(days=365)
        # On cherche une facture de catégorie 'ADM' (Administratif/Fiche) 
        # créée pour ce patient depuis moins d'un an.
        return Facture.objects.filter(
            patient=self, 
            prestation__categorie='ADM', 
            date_emission__date__gte=un_an_en_arriere
        ).exists()

    def doit_solder_fiche(self):
        """ Vérifie s'il existe une facture de fiche non payée (Reste > 0) """
        factures_fiche = Facture.objects.filter(patient=self, prestation__categorie='ADM')
        for f in factures_fiche:
            if f.reste_a_payer > 0:
                return True # Il a une dette sur sa fiche
        return False


# 5
# ==================================================
# Gestion de taux 
#
class ConfigurationHopital(models.Model):
    taux_usd_en_cdf = models.DecimalField(max_digits=10, decimal_places=2, default=2500.00)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration du Taux"

    def __str__(self):
        return f"1 USD = {self.taux_usd_en_cdf} CDF"

# 6 
# ===================================================
# Prestation 
#
class Prestation(models.Model):
    CATEGORIES = [
        ('ADM', 'Administratif (Fiche, etc.)'),
        ('CONS', 'Consultation'),
        ('LABO', 'Laboratoire'),
        ('SOIN', 'Soins / Nursing'),
    ]
    libelle = models.CharField(max_length=200)
    categorie = models.CharField(max_length=10, choices=CATEGORIES)
    prix_cdf = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.libelle} - {self.prix_cdf} CDF"


# 7 
# ======================================================
# Facture 
#
class Facture(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    prestation = models.ForeignKey('Prestation', on_delete=models.CASCADE)
    date_emission = models.DateTimeField(auto_now_add=True)
    
    # Historique figé pour la comptabilité
    prix_fixe_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    taux_fixe = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # 1. LOGIQUE DE SÉCURITÉ LORS DE LA CRÉATION
        if not self.id:
            # Si on essaie de facturer autre chose qu'une FICHE (catégorie 'ADM')
            if self.prestation.categorie != 'ADM':
                
                # Vérification A : La fiche existe-t-elle (moins de 365 jours) ?
                if not self.patient.a_une_fiche_valide():
                    raise ValidationError(
                        f"Action refusée : {self.patient.noms} n'a pas de fiche annuelle valide."
                    )

                # Vérification B : La fiche existante est-elle totalement payée ?
                if self.patient.doit_solder_fiche():
                    raise ValidationError(
                        f"Action refusée : {self.patient.noms} doit d'abord solder sa fiche annuelle."
                    )

            # 2. ENREGISTREMENT DES VALEURS FIXES
            config = ConfigurationHopital.objects.first()
            if not config:
                raise ValidationError("Erreur : Aucun taux de change n'est configuré dans le système.")
            
            self.taux_fixe = config.taux_usd_en_cdf
            self.prix_fixe_cdf = self.prestation.prix_cdf
            
        super().save(*args, **kwargs)

    @property
    def total_paye(self):
        # Utilise aggregate pour plus de performance sur de gros volumes
        from django.db.models import Sum
        return self.paiements.aggregate(Sum('montant_comptable_cdf'))['montant_comptable_cdf__sum'] or 0

    @property
    def reste_a_payer(self):
        return self.prix_fixe_cdf - self.total_paye

    def __str__(self):
        return f"Facture {self.id} - {self.patient.noms} ({self.prestation.libelle})"

# 8 
# ====================================================
# Paiement 
#
class Paiement(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant_physique = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')])
    date_paiement = models.DateTimeField(auto_now_add=True)
    
    # Montant final qui entre en caisse après calcul
    montant_comptable_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if self.devise == 'USD':
            # On utilise le taux qui a été figé sur la facture
            self.montant_comptable_cdf = self.montant_physique * self.facture.taux_fixe
        else:
            self.montant_comptable_cdf = self.montant_physique
        super().save(*args, **kwargs)

# 9 
# =======================================================
# depense
#
class Depense(models.Model):
    motif = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')])
    valeur_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    date_depense = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.devise == 'USD':
            config = ConfigurationHopital.objects.first()
            self.valeur_cdf = self.montant * config.taux_usd_en_cdf
        else:
            self.valeur_cdf = self.montant
        super().save(*args, **kwargs)
    

    

