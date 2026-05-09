from django.db import models
from django.contrib.auth.models import User
import uuid
from datetime import datetime

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
    
    # Prix par défaut en Dollars (USD)
    prix = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Prix (USD)"
    )

    def __str__(self):
        return f"{self.libelle} - {self.prix} USD"

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"

# 5
# service 

class Service(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)

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