from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from decimal import Decimal
import datetime
from django.db.models import Sum, F
# 1 =============================================
class Fonction(models.Model):
    fonction = models.CharField(max_length=30) 
    def __str__(self):
        return self.fonction

# 2 =============================================
class Service(models.Model):
    nomService = models.CharField(max_length=40) 
    def __str__(self):
        return self.nomService  

# 3 =============================================
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
        return self.nomComplet

# 4 ================================================
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

    def doit_solder_fiche(self):
        factures_fiche = Facture.objects.filter(patient=self, prestation__categorie='ADM')
        for f in factures_fiche:
            if f.reste_a_payer > 0:
                return True
        return False

# 5 ==================================================
class ConfigurationHopital(models.Model):
    taux_usd_en_cdf = models.DecimalField(max_digits=10, decimal_places=2, default=2250.00)
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = "Configuration du Taux"
    def __str__(self):
        return f"1 USD = {self.taux_usd_en_cdf} CDF"

# 6 ===================================================
class Prestation(models.Model):
    CATEGORIES = [
        ('ADM', 'Administratif (Fiche, etc.)'),
        ('CONS', 'Consultation'),
        ('LABO', 'Laboratoire'),
        ('SOIN', 'Soins / Nursing'),
        ('PHARMA', 'Pharmacie'),
    ]
    libelle = models.CharField(max_length=200)
    categorie = models.CharField(max_length=10, choices=CATEGORIES)
    prix_cdf = models.DecimalField(max_digits=15, decimal_places=2)
    def __str__(self):
        return f"{self.libelle} - {self.prix_cdf} CDF"

# 7 ======================================================
class Facture(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    prestation = models.ForeignKey('Prestation', on_delete=models.CASCADE)
    ordonnance = models.OneToOneField(
        'Ordonnance', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='facture'
    )
    date_emission = models.DateTimeField(auto_now_add=True)
    # On met default=0 pour éviter les erreurs de calcul au départ
    prix_fixe_cdf = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    taux_fixe = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vente_pharmacie = models.OneToOneField('VentePharmacie', on_delete=models.CASCADE, null=True, blank=True)

    def calculer_total_reel(self):
        """ Calcule le montant total basé sur les lignes de l'ordonnance """
        if self.ordonnance:
            # Calcule la somme de (quantité * prix) pour chaque ligne
            total = self.ordonnance.lignes.aggregate(
                total_ord=Sum(F('quantite_prescrite') * F('medicament__prix_vente_detail'))
            )['total_ord']
            return total or 0
        return self.prestation.prix_cdf

    

    def save(self, *args, **kwargs):
        if not self.id:
            # 1. Taux de change
            from .models import ConfigurationHopital 
            config = ConfigurationHopital.objects.first()
            self.taux_fixe = config.taux_usd_en_cdf if config else 2500
            
            # 2. CALCUL DU PRIX (LOGIQUE INVERSÉE POUR ÉVITER LES ERREURS)
            if self.ordonnance:
                # On calcule d'abord le total des médicaments
                total_medics = self.calculer_total_reel()
                if total_medics > 0:
                    self.prix_fixe_cdf = total_medics
                else:
                    # Si l'ordonnance est vide, on prend quand même le prix de la prestation pharma
                    self.prix_fixe_cdf = self.prestation.prix_cdf
            else:
                # Si pas d'ordonnance, c'est une fiche ou autre prestation standard
                self.prix_fixe_cdf = self.prestation.prix_cdf

            # 3. VERIFICATION DE LA FICHE (Uniquement si ce n'est PAS une ordonnance)
            if not self.ordonnance and self.prestation.categorie != 'ADM':
                if not self.patient.a_une_fiche_valide():
                    raise ValidationError("Le patient n'a pas de fiche valide.")

        super().save(*args, **kwargs)



    @property
    def total_paye(self):
        """ Somme de tous les paiements effectués sur cette facture """
        res = self.paiements.aggregate(Sum('montant_comptable_cdf'))['montant_comptable_cdf__sum']
        return res if res else 0

    @property
    def reste_a_payer(self):
        """ Ce qu'il reste à payer (Total - Déjà payé) """
        return self.prix_fixe_cdf - self.total_paye

    def __str__(self):
        return f"Facture {self.id} - {self.patient.noms}"
# 8 ======================================================================
class Paiement(models.Model):
    # Définition des modes de paiement
    CHOIX_MODE = [
        ('CASH', 'Espèces (Cash)'),
        ('MPESA', 'M-Pesa'),
    ]

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='paiements')
    montant_physique = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=[('CDF', 'CDF'), ('USD', 'USD')])
    
    # --- Nouveaux champs pour la traçabilité M-Pesa ---
    mode_paiement = models.CharField(
        max_length=10, 
        choices=CHOIX_MODE, 
        default='CASH',
        verbose_name="Mode de paiement"
    )
    reference_transaction = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        verbose_name="ID Transaction / Référence"
    )
    # ------------------------------------------------

    date_paiement = models.DateTimeField(auto_now_add=True)
    montant_comptable_cdf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Ta logique de conversion originale (ne change pas)
        if self.devise == 'USD':
            # Utilise le taux fixé au moment de la création de la facture
            self.montant_comptable_cdf = self.montant_physique * self.facture.taux_fixe
        else:
            self.montant_comptable_cdf = self.montant_physique
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paiement {self.mode_paiement} - {self.montant_physique} {self.devise} (Facture #{self.facture.id})"

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"


# 9 =======================================================
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

# 10 =======================================================
class SignesVitaux(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='signes_vitaux')
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
    def __str__(self):
        infirmier_nom = self.infirmier.username if self.infirmier else "Inconnu"
        return f"Signes de {self.patient.noms} - {self.date_prelevement.strftime('%d/%m/%Y %H:%M')}"

# 11 ====================================================
class Consultation(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    signes_vitaux = models.OneToOneField('SignesVitaux', on_delete=models.CASCADE, related_name='consultation')
    medecin = models.ForeignKey(User, on_delete=models.CASCADE)
    motif = models.TextField()
    diagnostic = models.TextField(null=True, blank=True)
    date_consultation = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Consultation de {self.patient.noms} le {self.date_consultation}"

# 12 =====================================================
class ExamenPrescrit(models.Model):
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='examens_prescrits')
    prestation = models.ForeignKey('Prestation', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    paye = models.BooleanField(default=False)
    termine = models.BooleanField(default=False) 
    resultat_labo = models.TextField(null=True, blank=True)
    date_analyse = models.DateTimeField(null=True, blank=True)
    laborantin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='analyses_faites')
    prix_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    date_prescription = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if self.prestation:
            self.prix_total = Decimal(str(self.prestation.prix_cdf)) * self.quantite
        super().save(*args, **kwargs)

# 13 =========================================================================
class Chambre(models.Model):
    TYPES = [('VIP', 'Privée VIP'), ('STANDARD', 'Standard'), ('COMMUNE', 'Salle Commune'), ('REANIMATION', 'Réanimation')]
    numero = models.CharField(max_length=10, unique=True)
    type_chambre = models.CharField(max_length=50, choices=TYPES, default='STANDARD')
    prix_journalier = models.DecimalField(max_digits=12, decimal_places=2)
    def __str__(self):
        return f"Chambre {self.numero}"

class Lit(models.Model):
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE, related_name="lits")
    nom_lit = models.CharField(max_length=10)
    est_occupe = models.BooleanField(default=False)
    def __str__(self):
        return f"{self.chambre.numero} - {self.nom_lit}"

class OccupationLit(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    lit = models.ForeignKey(Lit, on_delete=models.CASCADE)
    date_admission = models.DateTimeField(default=timezone.now)
    date_sortie = models.DateTimeField(null=True, blank=True)
    est_paye = models.BooleanField(default=False)
    @property
    def nombre_jours(self):
        fin = self.date_sortie or timezone.now()
        diff = fin - self.date_admission
        return diff.days if diff.days > 0 else 1
    @property
    def total_facture_cdf(self):
        return self.nombre_jours * self.lit.chambre.prix_journalier

# 14 ==============================================================
class Ordonnance(models.Model):
    consultation = models.ForeignKey('Consultation', on_delete=models.CASCADE, related_name='ordonnances')
    medecin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordonnances_prescrites')
    contenu_prescription = models.TextField()
    instructions_posologie = models.TextField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    # CHAMPS DE FLUX LOGIQUE
    est_paye = models.BooleanField(default=False) # Ajout pour la caisse
    est_delivré = models.BooleanField(default=False) # Pour la pharmacie
    
    # Optionnel : prix total si tu veux gérer les montants
    montant_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Ordonnance #{self.id} - {self.consultation.patient.noms}"

# PHARMACIE ==========================================================
class Medicament(models.Model):
    designation = models.CharField(max_length=200)
    forme = models.CharField(max_length=100, null=True, blank=True)
    dosage = models.CharField(max_length=100, null=True, blank=True)
    quantite_stock_pieces = models.PositiveIntegerField(default=0)
    pieces_par_carton = models.PositiveIntegerField(default=1) # Sécurisé par défaut à 1
    seuil_alerte = models.PositiveIntegerField(default=5)
    prix_achat_unitaire_moyen = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    prix_vente_detail = models.DecimalField(max_digits=12, decimal_places=2)
    prix_vente_gros = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.designation

    # --- CORRECTION ICI POUR ÉVITER LE TYPEERROR ADMIN ---
    @property
    def stock_en_cartons(self):
        # Sécurité : Division par zéro impossible
        if not self.pieces_par_carton or self.pieces_par_carton <= 0:
            return 0
        return self.quantite_stock_pieces // self.pieces_par_carton

    @property
    def reste_en_pieces(self):
        if not self.pieces_par_carton or self.pieces_par_carton <= 0:
            return self.quantite_stock_pieces
        return self.quantite_stock_pieces % self.pieces_par_carton

    @property
    def est_en_alerte(self):
        return self.quantite_stock_pieces <= self.seuil_alerte

class BonEntree(models.Model):
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    fournisseur = models.CharField(max_length=200, blank=True)
    nb_cartons_recus = models.PositiveIntegerField()
    prix_achat_carton = models.DecimalField(max_digits=12, decimal_places=2)
    date_reception = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if self.medicament.pieces_par_carton > 0:
                self.medicament.prix_achat_unitaire_moyen = float(self.prix_achat_carton) / self.medicament.pieces_par_carton
            if not self.pk:
                self.medicament.quantite_stock_pieces += (self.nb_cartons_recus * self.medicament.pieces_par_carton)
            self.medicament.save()
            super().save(*args, **kwargs)
# ===========================================================================
# vente pharmacie

class VentePharmacie(models.Model):
    vendeur = models.ForeignKey(User, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.SET_NULL, null=True, blank=True)
    # AJOUTE CETTE LIGNE :
    ordonnance = models.OneToOneField('Ordonnance', on_delete=models.CASCADE, null=True, blank=True, related_name='vente')
    
    date_vente = models.DateTimeField(auto_now_add=True)
    total_cdf = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=10, choices=[('VALIDE', 'Validée'), ('ANNULE', 'Annulée')], default='VALIDE')

class LigneVente(models.Model):
    vente = models.ForeignKey(VentePharmacie, related_name='lignes', on_delete=models.CASCADE)
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField()
    type_vente = models.CharField(max_length=10, choices=[('DETAIL', 'Détail'), ('GROS', 'Gros')], default='DETAIL')
    prix_unitaire_applique = models.DecimalField(max_digits=12, decimal_places=2)

class LogPharmacie(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    details = models.TextField()
    date_action = models.DateTimeField(auto_now_add=True)

# =================================================================
# ligne ordonnance 

class LigneOrdonnance(models.Model):
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE, related_name='lignes')
    medicament = models.ForeignKey(Medicament, on_delete=models.CASCADE, related_name='lignes_prescrites')
    quantite_prescrite = models.PositiveIntegerField()
    quantite_payee = models.PositiveIntegerField(default=0)
    quantite_delivree = models.PositiveIntegerField(default=0)
    date_creation = models.DateTimeField(auto_now_add=True)
    paye = models.BooleanField(default=False)

    @property
    def prix_total(self):
        if self.medicament and self.medicament.prix_vente_detail:
            return self.quantite_prescrite * self.medicament.prix_vente_detail
        return 0

    @property
    def reste_a_payer(self):
        return max(0, self.quantite_prescrite - self.quantite_payee)

    @property
    def reste_a_delivrer(self):
        return max(0, self.quantite_payee - self.quantite_delivree)

# =============================================================================================
# materiel
# =============================================================================================
class Materiel(models.Model):
    CATEGORIES = [
        ('LAPTOP', 'Ordinateur Portable'),
        ('DESKTOP', 'Ordinateur de Bureau'),
        ('TABLET', 'Tablette'),
        ('PRINTER', 'Imprimante'),
        ('MEDICAL', 'Appareil Médical'),
        ('TECH', 'Matériel Technique (Groupe, etc.)'),
    ]

    ETAT_CHOICES = [
        ('FONCTIONNEL', 'En marche'),
        ('PANNE', 'En Panne'),
        ('REPARATION', 'En Réparation'),
        ('DECLASSE', 'Hors service / Déclassé'),
    ]

    nom = models.CharField(max_length=100)
    marque = models.CharField(max_length=100)
    modele = models.CharField(max_length=100)
    numero_serie = models.CharField(max_length=100, unique=True)
    categorie = models.CharField(max_length=50, choices=CATEGORIES)
    
    # Relation avec ton modèle Service
    service_affecte = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='materiels')
    
    date_achat = models.DateField(null=True, blank=True)
    etat_actuel = models.CharField(max_length=20, choices=ETAT_CHOICES, default='FONCTIONNEL')
    description = models.TextField(blank=True, null=True, help_text="Caractéristique technique (RAM, Stockage, etc.)")

    def __str__(self):
        return f"{self.nom} - {self.service_affecte.nomService} ({self.numero_serie})"



#
# maintenance
# ===============================================================================================
class Maintenance(models.Model):
    # Relie la panne au matériel spécifique
    materiel = models.ForeignKey(Materiel, on_delete=models.CASCADE, related_name='historique_pannes')
    
    date_signalement = models.DateTimeField(auto_now_add=True)
    description_panne = models.TextField(help_text="Expliquez le problème constaté")
    
    # Suivi de la réparation
    est_repare = models.BooleanField(default=False)
    date_reparation = models.DateTimeField(null=True, blank=True)
    rapport_technique = models.TextField(blank=True, null=True, help_text="Ce qui a été fait pour réparer")
    cout_reparation = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        status = "Réparé" if self.est_repare else "En attente"
        return f"Panne sur {self.materiel.nom} ({status})"


#
# employe
# ==================================================================================================

class Employe(models.Model):
    # Lien unique vers le compte de connexion
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fiche_employe')
    
    # --- Informations Administratives ---
    # blank=True permet de laisser le champ vide dans le formulaire pour la génération auto
    matricule = models.CharField(max_length=50, unique=True, blank=True, verbose_name="Matricule")
    date_embauche = models.DateField(verbose_name="Date de début / Embauche")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin de contrat")
    
    TYPES_CONTRAT = [
        ('CDI', 'Contrat à Durée Indéterminée (CDI)'),
        ('CDD', 'Contrat à Durée Déterminée (CDD)'),
        ('STAGE_PRO', 'Stagiaire Professionnel'),
        ('STAGE_ACA', 'Stagiaire Académique (Non payé)'),
        ('PRESTAIRE', 'Consultant / Prestataire Extérieur'),
    ]
    type_contrat = models.CharField(max_length=20, choices=TYPES_CONTRAT, default='CDI')
    salaire_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Salaire de base")

    # --- Documents Numérisés ---
    carte_identite = models.FileField(upload_to='rh/identite/', null=True, blank=True, verbose_name="Carte d'identité")
    diplome = models.FileField(upload_to='rh/diplomes/', null=True, blank=True, verbose_name="Diplôme")
    contrat_signe = models.FileField(upload_to='rh/contrats/', null=True, blank=True, verbose_name="Contrat signé")

    # --- Santé ---
    GROUPES_SANGUINS = [
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
    ]
    groupe_sanguin = models.CharField(max_length=3, choices=GROUPES_SANGUINS, null=True, blank=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['-date_embauche']

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} ({self.matricule})"

    # --- LOGIQUE DE GÉNÉRATION ET VALIDATION ---

    def clean(self):
        """Validation des règles métiers"""
        # 1. Règle Stagiaire Académique
        if self.type_contrat == 'STAGE_ACA' and self.salaire_base > 0:
            raise ValidationError("Un stagiaire académique ne peut pas avoir de salaire.")
        
        # 2. Règle Date de fin obligatoire (sauf CDI)
        if self.type_contrat != 'CDI' and not self.date_fin:
            raise ValidationError({
                'date_fin': "La date de fin est obligatoire pour ce type de contrat."
            })
            
        # 3. Cohérence des dates
        if self.date_fin and self.date_fin < self.date_embauche:
            raise ValidationError("La date de fin ne peut pas être avant la date d'embauche.")

    def save(self, *args, **kwargs):
        # 1. Génération automatique du matricule (Format: HOSP-2026-001)
        if not self.matricule:
            annee = datetime.datetime.now().year
            # On cherche le dernier matricule de l'année en cours
            dernier = Employe.objects.filter(matricule__contains=f"-{annee}-").order_by('-id').first()
            
            if dernier:
                try:
                    dernier_num = int(dernier.matricule.split('-')[-1])
                    nouveau_num = dernier_num + 1
                except (ValueError, IndexError):
                    nouveau_num = 1
            else:
                nouveau_num = 1
            
            self.matricule = f"HOSP-{annee}-{nouveau_num:03d}"

        # 2. Forcer le salaire à 0 pour les stagiaires académiques
        if self.type_contrat == 'STAGE_ACA':
            self.salaire_base = 0
            
        self.full_clean()
        super(Employe, self).save(*args, **kwargs)

    # --- PROPRIÉTÉS POUR L'INTERFACE (Templates) ---

    @property
    def jours_restants(self):
        """Nombre de jours avant la fin du contrat"""
        if self.date_fin:
            delta = self.date_fin - timezone.now().date()
            return delta.days
        return None

    @property
    def est_urgent(self):
        """Alerte si le contrat finit dans moins de 15 jours"""
        restant = self.jours_restants
        return restant is not None and 0 <= restant <= 15