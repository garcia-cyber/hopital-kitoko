from django.db import models
from django.contrib.auth.models import User

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
