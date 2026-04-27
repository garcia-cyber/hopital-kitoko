from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import datetime
from django.core.exceptions import ValidationError
from decimal import Decimal
from django.db.models import Sum, F

# 1. CONFIGURATION ET BASE =============================================

class ConfigurationHopital(models.Model):
    taux_usd_en_cdf = models.DecimalField(max_digits=10, decimal_places=2, default=2500.00)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Configuration du Taux"
    def __str__(self):
        return f"1 USD = {self.taux_usd_en_cdf} CDF"

class Fonction(models.Model):
    fonction = models.CharField(max_length=30) 
    def __str__(self):
        return self.fonction

class Service(models.Model):
    nomService = models.CharField(max_length=40) 
    def __str__(self):
        return self.nomService  

class Profil(models.Model):
    nomComplet = models.CharField(max_length=50, null=True) 
    CHOIX_SEXE = [('masculin','Masculin'), ('feminin', 'Feminin')]
    sexe = models.CharField(max_length=15, choices=CHOIX_SEXE)
    phone = models.CharField(max_length=15)
    adresse = models.CharField(max_length=50)
    fonction = models.ForeignKey(Fonction, on_delete=models.SET_NULL, null=True) 
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True) 
    date_register = models.DateField(auto_now_add=True)
    userProfil = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return str(self.nomComplet)

# 2. PATIENTS ET CLINIQUE ================================================

class Patient(models.Model):
    noms = models.CharField(max_length=50)
    CHOIX_SEXE = [('masculin','Masculin'), ('feminin', 'Feminin')]
    sexeP = models.CharField(max_length=15, choices=CHOIX_SEXE) 
    ageP = models.IntegerField()
    phone_responsable = models.CharField(max_length=15)
    adresseP = models.CharField(max_length=60) 
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True)
    date_registerP = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.noms 

    def a_une_fiche_valide(self):
        un_an_en_arriere = timezone.now().date() - timedelta(days=365)
        return Facture.objects.filter(
            patient=self, 
            prestation__categorie='ADM', 
            date_emission__date__gte=un_an_en_arriere
        ).exists()

class SignesVitaux(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='signes_vitaux')
    infirmier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_prelevement = models.DateTimeField(auto_now_add=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1)
    tension_arterielle = models.CharField(max_length=20)
    poids = models.DecimalField(max_digits=5, decimal_places=2)
    frequence_cardiaque = models.IntegerField()
    frequence_respiratoire = models.IntegerField(null=True, blank=True)
    saturation_oxygene = models.IntegerField(null=True, blank=True)
    class Meta:
        ordering = ['-date_prelevement']

class Consultation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    signes_vitaux = models.OneToOneField(SignesVitaux, on_delete=models.CASCADE, related_name='consultation')
    medecin = models.ForeignKey(User, on_delete=models.CASCADE)
    motif = models.TextField()
    diagnostic = models.TextField(null=True, blank=True)
    date_consultation = models.DateTimeField(auto_now_add=True)

# 3. PHARMACIE ET STOCK ==================================================

class Medicament(models.Model):
    designation = models.CharField(max_length=200)
    forme = models.CharField(max_length=100, null=True, blank=True)
    dosage = models.CharField(max_length=100, null=True, blank=True)
    quantite_stock_pieces = models.PositiveIntegerField(default=0)
    pieces_par_carton = models.PositiveIntegerField(default=1)
    seuil_alerte = models.PositiveIntegerField(default=5)
    prix_achat_unitaire_moyen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prix_vente_detail = models.DecimalField(max_digits=12, decimal_places=2)
    prix_vente_gros = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.designation

    @property
    def stock_en_cartons(self):
        if not self.pieces_par_carton or self.pieces_par_carton <= 0: return 0
        return self.quantite_stock_pieces // self.pieces_par_carton

    @property
    def reste_en_pieces(self):
        if not self.pieces_par_carton or self.pieces_par_carton <= 0: return self.quantite_stock_pieces
        return self.quantite_stock_pieces % self.pieces_par_carton

class BonEntree(models.Model):
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    fournisseur = models.CharField(max_length=200, blank=True)
    nb_cartons_recus = models.PositiveIntegerField()
    prix_achat_carton = models.DecimalField(max_digits=12, decimal_places=2)
    date_reception = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.medicament.pieces_par_carton > 0:
                self.medicament.prix_achat_unitaire_moyen = self.prix_achat_carton / self.medicament.pieces_par_carton
            if not self.pk:
                self.medicament.quantite_stock_pieces += (self.nb_cartons_recus * self.medicament.pieces_par_carton)
            self.medicament.save()
            super().save(*args, **kwargs)

class Ordonnance(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='ordonnances')
    medecin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordonnances_prescrites')
    contenu_prescription = models.TextField()
    instructions_posologie = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    est_paye = models.BooleanField(default=False)
    est_delivré = models.BooleanField(default=False)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    class Meta:
        ordering = ['-date_creation']

class LigneOrdonnance(models.Model):
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE, related_name='lignes')
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='lignes_prescrites')
    quantite_prescrite = models.PositiveIntegerField()
    quantite_payee = models.PositiveIntegerField(default=0)
    quantite_delivree = models.PositiveIntegerField(default=0)
    paye = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    @property
    def prix_total(self):
        return self.quantite_prescrite * self.medicament.prix_vente_detail

    @property
    def reste_a_payer(self):
        """Nombre d'unités que le patient n'a pas encore achetées"""
        return self.quantite_prescrite - self.quantite_payee

    @property
    def reste_a_livrer(self):
        """Ce que le pharmacien doit encore donner (Payé mais pas encore délivré)"""
        return self.quantite_payee - self.quantite_delivree

    @property
    def est_totalement_livre(self):
        """Vérifie si le patient a reçu tout ce qu'il a payé"""
        return self.quantite_delivree >= self.quantite_payee

# 4. FACTURATION ET FINANCES =============================================

class Prestation(models.Model):
    CATEGORIES = [
        ('ADM', 'Administratif'), ('CONS', 'Consultation'),
        ('LABO', 'Laboratoire'), ('SOIN', 'Soins'), ('PHARMA', 'Pharmacie'),
    ]
    libelle = models.CharField(max_length=200)
    categorie = models.CharField(max_length=10, choices=CATEGORIES)
    prix_cdf = models.DecimalField(max_digits=15, decimal_places=2)
    def __str__(self):
        return f"{self.libelle} - {self.prix_cdf} CDF"

class FacturePharmacie(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, related_name='factures_pharma')
    nom_client_externe = models.CharField(max_length=200, null=True, blank=True)
    ordonnance = models.OneToOneField(Ordonnance, on_delete=models.SET_NULL, null=True, blank=True, related_name='facture_pharma')
    total_a_payer_cdf = models.DecimalField(max_digits=15, decimal_places=2)
    taux_fixe = models.DecimalField(max_digits=10, decimal_places=2)
    date_facture = models.DateTimeField(auto_now_add=True)
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE)

    @property
    def total_paye(self):
        res = self.paiements.aggregate(total=Sum('montant_comptable_cdf'))['total']
        return res if res else Decimal("0.00")

    @property
    def reste_a_payer(self):
        return self.total_a_payer_cdf - self.total_paye

    @property
    def statut_paiement(self):
        paye = self.total_paye
        if paye <= 0: return 'NON_PAYE'
        if paye < self.total_a_payer_cdf: return 'PARTIEL'
        return 'SOLDE'

class Facture(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    prestation = models.ForeignKey(Prestation, on_delete=models.CASCADE)
    ordonnance = models.OneToOneField(Ordonnance, on_delete=models.CASCADE, null=True, blank=True, related_name='facture')
    date_emission = models.DateTimeField(auto_now_add=True)
    prix_fixe_cdf = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_fixe = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vente_pharmacie = models.OneToOneField('VentePharmacie', on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.id:
            config = ConfigurationHopital.objects.first()
            self.taux_fixe = config.taux_usd_en_cdf if config else 2500
            
            if self.ordonnance:
                total = self.ordonnance.lignes.aggregate(total_ord=Sum(F('quantite_prescrite') * F('medicament__prix_vente_detail')))['total_ord']
                self.prix_fixe_cdf = total if total else self.prestation.prix_cdf
            else:
                self.prix_fixe_cdf = self.prestation.prix_cdf

            if not self.ordonnance and self.prestation.categorie != 'ADM':
                if not self.patient.a_une_fiche_valide():
                    raise ValidationError("Le patient n'a pas de fiche valide.")
        super().save(*args, **kwargs)

    @property
    def total_paye(self):
        res = self.paiements.aggregate(Sum('montant_comptable_cdf'))['montant_comptable_cdf__sum']
        return res if res else 0

    @property
    def reste_a_payer(self):
        return self.prix_fixe_cdf - self.total_paye

class Paiement(models.Model):
    CHOIX_MODE = [('CASH', 'Espèces (Cash)'), ('MPESA', 'M-Pesa')]
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, null=True, blank=True, related_name='paiements')
    facture_pharma = models.ForeignKey(FacturePharmacie, on_delete=models.CASCADE, null=True, blank=True, related_name='paiements')
    montant_physique = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')])
    mode_paiement = models.CharField(max_length=10, choices=CHOIX_MODE, default='CASH')
    reference_transaction = models.CharField(max_length=100, null=True, blank=True)
    date_paiement = models.DateTimeField(auto_now_add=True)
    montant_comptable_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        taux = Decimal("2500") 
        if self.facture: taux = self.facture.taux_fixe
        elif self.facture_pharma: taux = self.facture_pharma.taux_fixe
        self.montant_comptable_cdf = (self.montant_physique * taux) if self.devise == 'USD' else self.montant_physique
        super().save(*args, **kwargs)

class Depense(models.Model):
    motif = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')])
    valeur_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    date_depense = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        config = ConfigurationHopital.objects.first()
        taux = config.taux_usd_en_cdf if config else 2500
        self.valeur_cdf = (self.montant * taux) if self.devise == 'USD' else self.montant
        super().save(*args, **kwargs)

# 5. LABO, CHAMBRES ET MATÉRIEL ==========================================

class ExamenPrescrit(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='examens_prescrits')
    prestation = models.ForeignKey(Prestation, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    paye = models.BooleanField(default=False)
    termine = models.BooleanField(default=False) 
    resultat_labo = models.TextField(null=True, blank=True)
    date_analyse = models.DateTimeField(null=True, blank=True)
    laborantin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    prix_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_prescription = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        self.prix_total = self.prestation.prix_cdf * self.quantite
        super().save(*args, **kwargs)

class Chambre(models.Model):
    TYPES = [('VIP', 'VIP'), ('STANDARD', 'Standard'), ('COMMUNE', 'Salle Commune')]
    numero = models.CharField(max_length=10, unique=True)
    type_chambre = models.CharField(max_length=50, choices=TYPES, default='STANDARD')
    prix_journalier = models.DecimalField(max_digits=12, decimal_places=2)

class Lit(models.Model):
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name="lits")
    nom_lit = models.CharField(max_length=10)
    est_occupe = models.BooleanField(default=False)

class OccupationLit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    lit = models.ForeignKey(Lit, on_delete=models.CASCADE)
    date_admission = models.DateTimeField(default=timezone.now)
    date_sortie = models.DateTimeField(null=True, blank=True)
    est_paye = models.BooleanField(default=False)

class Materiel(models.Model):
    nom = models.CharField(max_length=100)
    marque = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    service_affecte = models.ForeignKey(Service, on_delete=models.CASCADE)
    etat_actuel = models.CharField(max_length=20, default='FONCTIONNEL')

class Maintenance(models.Model):
    materiel = models.ForeignKey(Materiel, on_delete=models.CASCADE, related_name='historique_pannes')
    description_panne = models.TextField()
    est_repare = models.BooleanField(default=False)
    date_reparation = models.DateTimeField(null=True, blank=True)

# 6. RESSOURCES HUMAINES =================================================

class Employe(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fiche_employe')
    matricule = models.CharField(max_length=50, unique=True, blank=True)
    date_embauche = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    type_contrat = models.CharField(max_length=20, default='CDI')
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if not self.matricule:
            annee = datetime.datetime.now().year
            dernier = Employe.objects.filter(matricule__contains=f"-{annee}-").order_by('-id').first()
            nouveau_num = (int(dernier.matricule.split('-')[-1]) + 1) if dernier else 1
            self.matricule = f"HOSP-{annee}-{nouveau_num:03d}"
        super().save(*args, **kwargs)

# 7. VENTES DIRECTES ET LOGS =============================================

class VentePharmacie(models.Model):
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    ordonnance = models.OneToOneField(Ordonnance, on_delete=models.CASCADE, null=True, blank=True, related_name='vente')
    date_vente = models.DateTimeField(auto_now_add=True)
    total_cdf = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, default='VALIDE')

class LigneVente(models.Model):
    vente = models.ForeignKey(VentePharmacie, related_name='lignes', on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_unitaire_applique = models.DecimalField(max_digits=12, decimal_places=2)

class LogPharmacie(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    details = models.TextField()
    date_action = models.DateTimeField(auto_now_add=True)


# Dans models.py
class LigneFacturePharma(models.Model):
    facture = models.ForeignKey(FacturePharmacie, related_name='lignes', on_delete=models.CASCADE)
    medicament = models.ForeignKey('Medicament', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    prix_unitaire_applique = models.DecimalField(max_digits=12, decimal_places=2)
    
    @property
    def sous_total(self):
        return self.quantite * self.prix_unitaire_applique

    def __str__(self):
        return f"{self.medicament.designation} x {self.quantite}"