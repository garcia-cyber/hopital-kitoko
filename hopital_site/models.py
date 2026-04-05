from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from decimal import Decimal

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
# ====================================================
# Facturation & Paiement (Ton code original préservé)
# ====================================================

class Facture(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    prestation = models.ForeignKey('Prestation', on_delete=models.CASCADE)
    date_emission = models.DateTimeField(auto_now_add=True)
    
    prix_fixe_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    taux_fixe = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            # Sécurité Fiche Annuelle
            if self.prestation.categorie != 'ADM':
                if not self.patient.a_une_fiche_valide():
                    raise ValidationError(f"Action refusée : {self.patient.noms} n'a pas de fiche valide.")
                if self.patient.doit_solder_fiche():
                    raise ValidationError(f"Action refusée : {self.patient.noms} doit solder sa fiche.")

            # Figement des valeurs
            config = ConfigurationHopital.objects.first()
            if not config:
                raise ValidationError("Erreur : Aucun taux de change configuré.")
            
            self.taux_fixe = config.taux_usd_en_cdf
            self.prix_fixe_cdf = self.prestation.prix_cdf
            
        super().save(*args, **kwargs)

    @property
    def total_paye(self):
        from django.db.models import Sum
        # On utilise le montant comptable calculé lors du paiement
        return self.paiements.aggregate(Sum('montant_comptable_cdf'))['montant_comptable_cdf__sum'] or 0

    @property
    def reste_a_payer(self):
        return self.prix_fixe_cdf - self.total_paye

    def __str__(self):
        return f"Facture {self.id} - {self.patient.noms}"

# 8
# ======================================================================
class Paiement(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant_physique = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')])
    date_paiement = models.DateTimeField(auto_now_add=True)
    montant_comptable_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        if self.devise == 'USD':
            # Utilisation du taux figé sur la facture au moment de l'émission
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
# 10 
# =======================================================
# signe vitaux
#
class SignesVitaux(models.Model):
    # 1. LIENS (RELATIONS)
    # Relie les signes à un patient précis. Si le patient est supprimé, ses signes le sont aussi.
    patient = models.ForeignKey(
        'Patient', 
        on_delete=models.CASCADE, 
        related_name='signes_vitaux'
    )
    
    # Relie l'action à l'utilisateur (infirmier) connecté. 
    # Si le compte de l'infirmier est supprimé, on garde les données (null=True).
    infirmier = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Infirmier ayant effectué le prélèvement"
    )

    # 2. HORODATAGE
    # Enregistre la date et l'heure exactes de la prise des constantes.
    date_prelevement = models.DateTimeField(auto_now_add=True)

    # 3. CONSTANTES MÉDICALES
    # Température : ex 37.5 (max 4 chiffres, 1 après la virgule)
    temperature = models.DecimalField(
        max_digits=4, 
        decimal_places=1, 
        verbose_name="Température (°C)",
        help_text="Ex: 37.5"
    )
    
    # Tension : stockée en texte car contient souvent un "/" (ex: 12/8)
    tension_arterielle = models.CharField(
        max_length=20, 
        verbose_name="Tension Artérielle",
        help_text="Ex: 12/8 ou 120/80"
    )
    
    # Poids : ex 75.50 (max 5 chiffres, 2 après la virgule)
    poids = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        verbose_name="Poids (kg)"
    )
    
    # Pouls : Battements par minute (Nombre entier)
    frequence_cardiaque = models.IntegerField(
        verbose_name="Fréquence Cardiaque (BPM)"
    )
    
    # Respiration : Cycles par minute (Optionnel)
    frequence_respiratoire = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Fréquence Respiratoire"
    )
    
    # SPO2 : Saturation en oxygène (Optionnel, en %)
    saturation_oxygene = models.IntegerField(
        null=True, 
        blank=True, 
        verbose_name="Saturation (SpO2 %)",
        help_text="Saturation en oxygène"
    )

    # 4. MÉTA-DONNÉES
    class Meta:
        verbose_name = "Signe Vital"
        verbose_name_plural = "Signes Vitaux"
        ordering = ['-date_prelevement'] # Les plus récents en premier

    # 5. AFFICHAGE DANS L'ADMIN
    def __str__(self):
        infirmier_nom = self.infirmier.username if self.infirmier else "Inconnu"
        return f"Signes de {self.patient.noms} - {self.date_prelevement.strftime('%d/%m/%Y %H:%M')} (Par: {infirmier_nom})"
    

    
# 11  
# =============================================================
# 


# ====================================================
# Consultation & Examens (Flux Médical)
# ====================================================

class Consultation(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    signes_vitaux = models.OneToOneField('SignesVitaux', on_delete=models.CASCADE, related_name='consultation')
    medecin = models.ForeignKey(User, on_delete=models.CASCADE)
    motif = models.TextField(verbose_name="Motif de consultation")
    diagnostic = models.TextField(null=True, blank=True)
    date_consultation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Consultation de {self.patient.noms} le {self.date_consultation}"
# 12
# =====================================================
# examen prescrit
#

class ExamenPrescrit(models.Model):
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='examens_prescrits')
    prestation = models.ForeignKey('Prestation', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    
    # --- LOGIQUE FLUX DE TRAVAIL ---
    paye = models.BooleanField(default=False, verbose_name="Est payé (Caisse)")
    termine = models.BooleanField(default=False, verbose_name="Analyse terminée (Labo)") 

    # --- AJOUTS POUR LE LABORATOIRE (Résultats) ---
    resultat_labo = models.TextField(null=True, blank=True, verbose_name="Résultats / Conclusions")
    date_analyse = models.DateTimeField(null=True, blank=True)
    laborantin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='analyses_faites')
    
    # --- LOGIQUE FINANCIÈRE ---
    prix_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_prescription = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        etat = "TERMINÉ" if self.termine else ("PAYÉ" if self.paye else "EN ATTENTE")
        return f"{self.prestation.libelle} - {self.consultation.patient.noms} ({etat})"

    def save(self, *args, **kwargs):
        if self.prestation:
            self.prix_total = Decimal(str(self.prestation.prix_cdf)) * self.quantite
        super().save(*args, **kwargs)

# 13 
# =========================================================================
#

class Chambre(models.Model):
    TYPES = [
        ('VIP', 'Privée VIP'),
        ('STANDARD', 'Standard'),
        ('COMMUNE', 'Salle Commune'),
        ('REANIMATION', 'Réanimation'),
    ]
    
    numero = models.CharField("N° de Chambre", max_length=10, unique=True)
    type_chambre = models.CharField(max_length=50, choices=TYPES, default='STANDARD')
    prix_journalier = models.DecimalField(max_digits=12, decimal_places=2, help_text="Prix par jour en CDF")

    def __str__(self):
        return f"Chambre {self.numero} ({self.type_chambre})"

class Lit(models.Model):
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name="lits")
    nom_lit = models.CharField("Nom du Lit", max_length=10) # ex: L1, L2
    est_occupe = models.BooleanField("Est occupé ?", default=False)

    def __str__(self):
        status = "Occupé" if self.est_occupe else "Libre"
        return f"{self.chambre.numero} - {self.nom_lit} ({status})"

class OccupationLit(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    lit = models.ForeignKey(Lit, on_delete=models.CASCADE)
    date_admission = models.DateTimeField(default=timezone.now)
    date_sortie = models.DateTimeField(null=True, blank=True)
    est_paye = models.BooleanField(default=False)

    @property
    def nombre_jours(self):
        if not self.date_sortie:
            fin = timezone.now()
        else:
            fin = self.date_sortie
        
        diff = fin - self.date_admission
        # Si le patient reste moins d'un jour, on facture 1 jour par défaut
        jours = diff.days if diff.days > 0 else 1
        return jours

    @property
    def total_facture_cdf(self):
        """Calcul du total en Francs Congolais"""
        return self.nombre_jours * self.lit.chambre.prix_journalier

    def __str__(self):
        return f"Occupation: {self.patient} sur {self.lit}"