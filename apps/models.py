from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime
from django.utils import timezone 
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.conf import settings
# Create your models here.

 

# 1. CONFIGURATION ET BASE =============================================

class ConfigurationHopital(models.Model):
    taux_usd_en_cdf = models.DecimalField(max_digits=10, decimal_places=2, default=2500.00)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Configuration du Taux"
    def __str__(self):
        return f"1 USD = {self.taux_usd_en_cdf} CDF"

# 2  role =======================================================
class Role(models.Model):
    roleName = models.CharField(max_length = 30)

 
    def __str__(self):
        return self.roleName

# 3 fonction ======================================================
class Fonction(models.Model):
    fonctionKey = models.ForeignKey(Role , on_delete = models.SET_NULL , null = True)
    userKey     = models.ForeignKey(User , on_delete = models.SET_NULL , null = True)
    autorisation = models.CharField(max_length = 30 , default = 'oui')


    def __str__(self):
        return self.autorisation 

# 4 prestations

class Prestation(models.Model):
    CATEGORIES = [
        ('ADM', 'Administratif'), 
        # ('CONS', 'Consultation'),
        ('LABO', 'Laboratoire'), 
        # Si la catégorie de la prestation est "Labo", on pourra ajouter la valeur
        ('SOIN', 'Soins'), 
        ('ECHO', 'Échographie'), 
        ('RADIO', 'Radiologie'), 
    ]
    
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    categorie = models.CharField(
        max_length=10, 
        choices=CATEGORIES, 
        verbose_name="Catégorie"
    )
    
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Prix (USD)"
    )

    # Nouveau champ spécifique au Laboratoire
    valeur_normale = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Valeur Normale / Référence (Labo uniquement)",
        help_text="Ex: 70-110 mg/dl, Négatif, etc. Utilisé uniquement pour le Laboratoire."
    )

    def __str__(self):
        return f"{self.libelle} - {self.prix} USD"

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"

    # Optionnel : Validation de sécurité au niveau du modèle
    def clean(self):
        # Si on tente d'entrer une valeur alors que ce n'est pas du LABO
        if self.categorie != 'LABO' and self.valeur_normale:
            self.valeur_normale = None # On force à vide pour les autres catégories

# 5
# service 

class Service(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

# 6
# patient 

class Patient(models.Model):
    code_patient = models.CharField(max_length=20, unique=True, editable=False)
    noms = models.CharField(max_length=100)
    
    # Nouveau champ : Service d'accueil ou d'orientation
    service = models.ForeignKey(
        Service, 
        on_delete=models.PROTECT, # On empêche de supprimer un service s'il a des patients
        related_name='patients',
        null=True # Utile si tu as déjà des patients en base sans service
    )
    
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    age = models.CharField(max_length=30)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    fiche_payee = models.BooleanField(default=False)
    
    # Traçabilité
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='patients_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Ta logique de génération de code_patient reste la même...
        if not self.code_patient:
            import datetime
            annee = datetime.datetime.now().year
            prefixe = f"MLY-{annee}-"
            last_patient = Patient.objects.filter(code_patient__startswith=prefixe).order_by('id').last()
            
            if last_patient:
                last_id = int(last_patient.code_patient.split('-')[-1])
                new_id = last_id + 1
            else:
                new_id = 1
            self.code_patient = f"{prefixe}{new_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.noms} ({self.code_patient})"

# =================================================================================================
class Paiement(models.Model):
    """ Journal de caisse : chaque entrée d'argent physique """
    CURRENCY = [('USD', 'USD'), ('CDF', 'CDF')]
    
    SERVICES = [
        ('FICHE', 'Fiche'), 
        ('LABO', 'Labo'), 
        ('ECHOGRAPHIE', 'Échographie'),
        ('RADIO', 'Radiographie'),  # Ajout de la radiographie
        # ('PHARMA', 'Pharmacie'),  # Masqué pour le moment
    ]

    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    
    # Lien crucial pour retrouver et débloquer les examens de la consultation payée
    consultation = models.ForeignKey(
        'Consultation', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='paiements'
    )
    
    service = models.CharField(max_length=20, choices=SERVICES)
    montant_verse = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=CURRENCY, default='USD')
    date_paiement = models.DateTimeField(default=timezone.now)
    caissier = models.ForeignKey('auth.User', on_delete=models.PROTECT)
    reste_a_payer = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Dette / Reste à payer")

    def save(self, *args, **kwargs):
        # On sauvegarde d'abord le paiement
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Si c'est un nouveau paiement, on crée la facture liée immédiatement
        if is_new:
            Facture.objects.create(
                paiement=self,
                numero_facture=f"FAC-{timezone.now().strftime('%y%m%d')}-{self.id}"
            )

    def __str__(self):
        return f"Paiement {self.id} - {self.montant_verse} {self.devise} ({self.get_service_display()})"


# =================================================================================================


class Facture(models.Model):
    """ Document lié à chaque paiement pour la traçabilité """
    paiement = models.OneToOneField(Paiement, on_delete=models.CASCADE, related_name='facture_liee')
    numero_facture = models.CharField(max_length=50, unique=True)
    date_emission = models.DateTimeField(default=timezone.now)

    def __str__(self):
        # get_service_display() permet d'afficher "Radiographie" au lieu de "RADIO"
        return f"Facture {self.numero_facture} ({self.paiement.get_service_display()})"


# ===================================================================================================
class SigneVital(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    temperature = models.DecimalField(max_digits=4, decimal_places=1) 
    poids = models.DecimalField(max_digits=5, decimal_places=2) 
    
    # Correction ici : on utilise max_length au lieu de max_digits
    tension_arterielle = models.CharField(max_length=10) 
    
    frequence_cardiaque = models.IntegerField()
    frequence_respiratoire = models.IntegerField(null=True, blank=True)
    saturation_oxygene = models.IntegerField(null=True, blank=True) 
    date_prelevement = models.DateTimeField(default=timezone.now)
    infirmier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    est_consulte = models.BooleanField(default=False)

    def __str__(self):
        return f"Signes vitaux de {self.patient.noms} le {self.date_prelevement}"

# ==================================================================================================
class Consultation(models.Model):
    triage = models.OneToOneField('SigneVital', db_index=True, on_delete=models.CASCADE)
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    motif_consultation = models.TextField(verbose_name="Motif")
    histoire_maladie = models.TextField(verbose_name="Histoire de la maladie")
    examen_physique = models.TextField(verbose_name="Examen physique")
    complement_d_anamnese = models.CharField(max_length=200, null=True)
    hypothese_diagnostique = models.TextField(verbose_name="Hypothèse diagnostique")
    
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Consultation de {self.triage.patient.noms} le {self.date_creation.strftime('%d/%m/%Y')}"

    @property
    def total_examens_a_payer(self):
        # CORRECTION ICI : On utilise le related_name 'examens' défini dans DemandeExamen
        examens_lies = self.examens.all()
        # Sécurité : on vérifie que l'examen possède bien une prestation et un prix
        return sum((ex.prestation.prix * ex.quantite) for ex in examens_lies if ex.prestation and ex.prestation.prix)


# ==================================================================================================
class DemandeExamen(models.Model):
    STATUT = [
        ('EN_ATTENTE', 'En attente'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]
    
    consultation = models.ForeignKey(Consultation, related_name='examens', on_delete=models.CASCADE)
    prestation = models.ForeignKey('Prestation', on_delete=models.PROTECT)
    indication = models.TextField(blank=True, help_text="Note du médecin pour le technicien")
    
    # Résultat rempli par le laborantin/radiologue/échographiste
    resultat = models.TextField(blank=True, null=True)
    image_resultat = models.ImageField(upload_to='resultats_examens/', blank=True, null=True)
    technicien = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='examens_realises', 
                                  on_delete=models.SET_NULL, null=True, blank=True)
    
    statut = models.CharField(max_length=20, choices=STATUT, default='EN_ATTENTE')
    date_demande = models.DateTimeField(default=timezone.now)
    date_realisation = models.DateTimeField(null=True, blank=True)
    quantite = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.prestation.libelle} pour {self.consultation.triage.patient.noms}"

# ===================================================================================================
class Ordonnance(models.Model):
    TYPE_CHOICES = [
        ('URGENCE', 'Ordonnance d’Urgence'),
        ('DEFINITIVE', 'Ordonnance Définitive'),
    ]
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    date_prescrite = models.DateTimeField(default=timezone.now)
    # AJOUT DU TYPE ICI
    type_ordonnance = models.CharField(max_length=20, choices=TYPE_CHOICES, default='URGENCE')
    observation = models.TextField(blank=True, help_text="Note générale sur l'ordonnance")

    def __str__(self):
        return f"Ordonnance {self.get_type_ordonnance_display()} du {self.date_prescrite.strftime('%d/%m/%Y')}"
# ===================================================================================================
class LigneMedicament(models.Model):
    STATUT_MEDOC = [
        ('EN_COURS', 'En cours'),
        ('STOPPE', 'Stoppé / Changé'),
    ]
    
    ordonnance = models.ForeignKey(Ordonnance, related_name='medicaments', on_delete=models.CASCADE)
    nom_medicament = models.CharField(max_length=200)
    posologie = models.CharField(max_length=200, help_text="ex: 1 tab 3 fois par jour")
    duree = models.CharField(max_length=100, help_text="ex: 5 jours")
    
    # Gestion de l'évolution du traitement
    statut = models.CharField(max_length=20, choices=STATUT_MEDOC, default='EN_COURS')
    motif_arret = models.TextField(blank=True, null=True, help_text="Pourquoi le médecin a changé ce médicament")
    date_modification = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nom_medicament} - {self.statut}"


# ===================================================================================================


class Depense(models.Model):
    """ Journal des dépenses avec vérification automatique du solde de caisse """
    
    CURRENCY = [('USD', 'USD'), ('CDF', 'CDF')]
    CATEGORIES = [
        ('LABO_REACTIF', 'Réactifs & Matériel Labo'),
        ('PHARMA_STOCK', 'Achat Stock Pharmacie'),
        ('CARBURANT', 'Carburant Générateur'),
        ('MAINTENANCE', 'Maintenance & Réparations'),
        ('ADMIN', 'Frais Administratifs & Bureau'),
        ('SALAIRE', 'Avances & Salaires Personnel'),
        ('AUTRE', 'Autre dépense'),
    ]

    motif = models.CharField(max_length=50, choices=CATEGORIES, verbose_name="Motif")
    description = models.TextField(blank=True, null=True)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=CURRENCY, default='USD')
    date_depense = models.DateTimeField(default=timezone.now)
    auteur = models.ForeignKey('auth.User', on_delete=models.PROTECT, verbose_name="Enregistré par")
    beneficiaire = models.CharField(max_length=150, blank=True, null=True, verbose_name="Bénéficiaire")

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"

    def clean(self):
        """ 
        Validation de sécurité : Empêche de dépenser de l'argent qui n'est pas en caisse.
        """
        # 1. Importer le modèle Paiement localement pour éviter les imports circulaires
        from .models import Paiement  

        # 2. Calculer le total des entrées pour cette devise
        total_entrees = Paiement.objects.filter(devise=self.devise).aggregate(
            total=Sum('montant_verse')
        )['total'] or 0.0

        # 3. Calculer le total des dépenses déjà effectuées pour cette devise
        # Si on est en train de modifier une dépense existante, on l'exclut du calcul
        toutes_les_depenses = Depense.objects.filter(devise=self.devise)
        if self.pk:
            toutes_les_depenses = toutes_les_depenses.exclude(pk=self.pk)
            
        total_sorties = toutes_les_depenses.aggregate(total=Sum('montant'))['total'] or 0.0

        # 4. Calculer le solde actuellement disponible en caisse
        solde_disponible = total_entrees - total_sorties

        # 5. Vérifier si le montant demandé est supérieur au solde disponible
        if self.montant > solde_disponible:
            raise ValidationError(
                f"Opération refusée. Solde de caisse insuffisant en {self.devise}. "
                f"Disponible : {solde_disponible:.2f} {self.devise}. "
                f"Montant demandé : {self.montant:.2f} {self.devise}."
            )

    def save(self, *args, **kwargs):
        # On force l'exécution de la méthode clean() avant d'enregistrer en BDD
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dépense {self.id} - {self.montant} {self.devise} ({self.get_motif_display()})"