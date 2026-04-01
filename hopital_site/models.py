from django.db import models
from django.contrib.auth.models import User

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



    

    

