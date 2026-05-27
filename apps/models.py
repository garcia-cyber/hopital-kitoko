from django.db import models
from django.contrib.auth.models import User
import uuid
from decimal import Decimal  # Ajout crucial pour la sécurité des calculs financiers
from django.utils import timezone 
from django.db.models import Sum
from django.core.exceptions import ValidationError
from django.conf import settings

# 1. CONFIGURATION ET BASE =============================================

class ConfigurationHopital(models.Model):
    # Utilisation d'une chaîne pour le default pour éviter les dérives de float
    taux_usd_en_cdf = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('2500.00'))
    derniere_mise_a_jour = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration du Taux"

    def __str__(self):
        return f"1 USD = {self.taux_usd_en_cdf} CDF"

# 2. ROLE =======================================================
class Role(models.Model):
    roleName = models.CharField(max_length=30)
 
    def __str__(self):
        return self.roleName

# 3. FONCTION ======================================================
class Fonction(models.Model):
    fonctionKey = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    userKey = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='user_fonction')
    autorisation = models.CharField(max_length=30, default='oui')

    def __str__(self):
        if self.userKey and self.fonctionKey:
            return f"{self.userKey.username} - {self.fonctionKey.roleName}"
        return f"Autorisation: {self.autorisation}"

# 4. PRESTATIONS ===================================================
class Prestation(models.Model):
    CATEGORIES = [
        ('ADM', 'Administratif'), 
        ('CONS', 'Consultation'), # <--- Ajouté ici
        ('LABO', 'Laboratoire'), 
        ('SOIN', 'Soins'), 
        ('ECHO', 'Échographie'), 
        ('RADIO', 'Radiologie'), 
    ]
    
    libelle = models.CharField(max_length=200, verbose_name="Libellé")
    categorie = models.CharField(max_length=10, choices=CATEGORIES, verbose_name="Catégorie")
    prix = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), verbose_name="Prix (USD)")
    valeur_normale = models.CharField(
        max_length=150, blank=True, null=True, 
        verbose_name="Valeur Normale / Référence (Labo uniquement)",
        help_text="Ex: 70-110 mg/dl, Négatif, etc. Utilisé uniquement pour le Laboratoire."
    )

    def __str__(self):
        return f"{self.libelle} ({self.get_categorie_display()}) - {self.prix} USD"

    class Meta:
        verbose_name = "Prestation"
        verbose_name_plural = "Prestations"

    def clean(self):
        # On nettoie la valeur normale si la catégorie n'est pas LABO
        if self.categorie != 'LABO':
            self.valeur_normale = None

# 5. SERVICE =======================================================
class Service(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

# 6. PATIENT =======================================================
class Patient(models.Model):
    code_patient = models.CharField(max_length=20, unique=True, editable=False)
    noms = models.CharField(max_length=100)
    service = models.ForeignKey('Service', on_delete=models.PROTECT, related_name='patients', null=True)
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')])
    age = models.CharField(max_length=30)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    
    # Statuts financiers
    fiche_payee = models.BooleanField(default=False) # Pour le 1er passage
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='patients_crees')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.code_patient:
            annee = timezone.now().year
            prefixe = f"MLY-{annee}-"
            # Utilisation de count() ou filter pour générer l'identifiant
            last_patient = Patient.objects.filter(code_patient__startswith=prefixe).order_by('id').last()
            new_id = int(last_patient.code_patient.split('-')[-1]) + 1 if last_patient else 1
            self.code_patient = f"{prefixe}{new_id:04d}"
        super().save(*args, **kwargs)

    # --- NOUVELLES MÉTHODES MÉTIER ---

    def a_deja_ete_consulte(self):
        """Vérifie si le patient a déjà eu au moins une consultation enregistrée."""
        return self.consultation_set.exists()

    def a_une_consultation_en_attente(self):
        """Retourne True si le patient a une consultation non payée."""
        return self.consultation_set.filter(consultation_payee=False).exists()

    def est_en_regle(self):
        """
        Logique métier complète :
        1. Si c'est la 1ère fois, il faut la fiche payée.
        2. Si c'est un retour, la consultation doit être payée.
        """
        if not self.fiche_payee:
            return False
        if self.a_deja_ete_consulte() and self.a_une_consultation_en_attente():
            return False
        return True

    def __str__(self):
        return f"{self.noms} ({self.code_patient})"

class Paiement(models.Model):
    CURRENCY = [('USD', 'USD'), ('CDF', 'CDF')]
    SERVICES = [
        ('FICHE', 'Fiche'), 
        ('CONSULTATION', 'Consultation'), 
        ('LABO', 'Labo'), 
        ('ECHOGRAPHIE', 'Échographie'),
        ('RADIO', 'Radiographie'), 
        ('SOIN', 'Soins'),
    ]

    patient = models.ForeignKey('Patient', on_delete=models.CASCADE)
    consultation = models.ForeignKey('Consultation', on_delete=models.SET_NULL, null=True, blank=True, related_name='paiements')
    service = models.CharField(max_length=20, choices=SERVICES)
    montant_verse = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, choices=CURRENCY, default='USD')
    date_paiement = models.DateTimeField(default=timezone.now)
    caissier = models.ForeignKey(User, on_delete=models.PROTECT)
    reste_a_payer = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Dette / Reste à payer")

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        
        # LOGIQUE D'AUTOMATISATION
        if self.service == 'FICHE':
            self.patient.fiche_payee = True
            self.patient.save()
            
        elif self.service == 'CONSULTATION' and self.consultation:
            self.consultation.consultation_payee = True
            self.consultation.save()

        super().save(*args, **kwargs)
        
        # Création automatique de la facture
        if is_new:
            # Import différé pour éviter les erreurs d'import circulaire
            from .models import Facture
            Facture.objects.create(
                paiement=self,
                numero_facture=f"FAC-{timezone.now().strftime('%y%m%d')}-{self.id}"
            )

    def __str__(self):
        return f"Paiement {self.id} - {self.montant_verse} {self.devise} ({self.get_service_display()})"

# 8. FACTURE =======================================================
class Facture(models.Model):
    paiement = models.OneToOneField(Paiement, on_delete=models.CASCADE, related_name='facture_liee')
    numero_facture = models.CharField(max_length=50, unique=True)
    date_emission = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Facture {self.numero_facture} ({self.paiement.get_service_display()})"

# 9. SIGNES VITAUX ==================================================
class SigneVital(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    temperature = models.DecimalField(max_digits=4, decimal_places=1) 
    poids = models.DecimalField(max_digits=5, decimal_places=2) 
    tension_arterielle = models.CharField(max_length=10) 
    frequence_cardiaque = models.IntegerField()
    frequence_respiratoire = models.IntegerField(null=True, blank=True)
    saturation_oxygene = models.IntegerField(null=True, blank=True) 
    date_prelevement = models.DateTimeField(default=timezone.now)
    infirmier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    est_consulte = models.BooleanField(default=False)

    def __str__(self):
        return f"Signes vitaux de {self.patient.noms} le {self.date_prelevement}"

# 10. CONSULTATION ==================================================
class Consultation(models.Model):
    triage = models.OneToOneField(SigneVital, db_index=True, on_delete=models.CASCADE)
    medecin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    motif_consultation = models.TextField(verbose_name="Motif")
    histoire_maladie = models.TextField(verbose_name="Histoire de la maladie")
    examen_physique = models.TextField(verbose_name="Examen physique")
    complement_d_anamnese = models.CharField(max_length=200, null=True)
    hypothese_diagnostique = models.TextField(verbose_name="Hypothèse diagnostique")
    date_creation = models.DateTimeField(default=timezone.now)
    
    # NOUVEAU : Statut de paiement pour débloquer l'accès aux soins
    consultation_payee = models.BooleanField(default=False, verbose_name="Consultation payée")

    def __str__(self):
        return f"Consultation de {self.triage.patient.noms} le {self.date_creation.strftime('%d/%m/%Y')}"

    @property
    def total_examens_a_payer(self):
        examens_lies = self.examens.all()
        return sum((ex.prestation.prix * ex.quantite) for ex in examens_lies if ex.prestation and ex.prestation.prix)

    # Méthode utilitaire pour vérifier si le patient est éligible aux examens/soins
    @property
    def est_accessible(self):
        # La consultation est accessible si elle est payée
        return self.consultation_payee

# 11. DEMANDE EXAMEN ===============================================
class DemandeExamen(models.Model):
    STATUT = [
        ('EN_ATTENTE', 'En attente'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]
    
    consultation = models.ForeignKey(Consultation, related_name='examens', on_delete=models.CASCADE)
    prestation = models.ForeignKey(Prestation, on_delete=models.PROTECT)
    indication = models.TextField(blank=True, help_text="Note du médecin pour le technicien")
    resultat = models.TextField(blank=True, null=True)
    image_resultat = models.ImageField(upload_to='resultats_examens/', blank=True, null=True)
    technicien = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='examens_realises', 
        on_delete=models.SET_NULL, null=True, blank=True
    )
    statut = models.CharField(max_length=20, choices=STATUT, default='EN_ATTENTE')
    date_demande = models.DateTimeField(default=timezone.now)
    date_realisation = models.DateTimeField(null=True, blank=True)
    quantite = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.prestation.libelle} pour {self.consultation.triage.patient.noms}"

# 12. ORDONNANCE ===================================================
class Ordonnance(models.Model):
    TYPE_CHOICES = [
        ('URGENCE', 'Ordonnance d’Urgence'),
        ('DEFINITIVE', 'Ordonnance Définitive'),
    ]
    
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    date_prescrite = models.DateTimeField(default=timezone.now)
    type_ordonnance = models.CharField(max_length=20, choices=TYPE_CHOICES, default='URGENCE')
    observation = models.TextField(blank=True, help_text="Note générale sur l'ordonnance")

    def __str__(self):
        return f"Ordonnance {self.get_type_ordonnance_display()} du {self.date_prescrite.strftime('%d/%m/%Y')}"

# 13. LIGNE MEDICAMENT =============================================
class LigneMedicament(models.Model):
    STATUT_MEDOC = [
        ('EN_COURS', 'En cours'),
        ('STOPPE', 'Stoppé / Changé'),
    ]
    
    ordonnance = models.ForeignKey(Ordonnance, related_name='medicaments', on_delete=models.CASCADE)
    nom_medicament = models.CharField(max_length=200)
    posologie = models.CharField(max_length=200, help_text="ex: 1 tab 3 fois par jour")
    duree = models.CharField(max_length=100, help_text="ex: 5 jours")
    statut = models.CharField(max_length=20, choices=STATUT_MEDOC, default='EN_COURS')
    motif_arret = models.TextField(blank=True, null=True, help_text="Pourquoi le médecin a changé ce médicament")
    date_modification = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.nom_medicament} - {self.statut}"

# 14. DEPENSE ======================================================
class Depense(models.Model):
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
        # Correction 1 : Retrait de l'import circulaire de Paiement (on l'appelle directement)
        # Correction 2 : Utilisation d'un entier 0 à la place du float 0.0 pour éviter le TypeError avec Decimal
        total_entrees = Paiement.objects.filter(devise=self.devise).aggregate(
            total=Sum('montant_verse')
        )['total'] or 0

        toutes_les_depenses = Depense.objects.filter(devise=self.devise)
        if self.pk:
            toutes_les_depenses = toutes_les_depenses.exclude(pk=self.pk)
            
        total_sorties = toutes_les_depenses.aggregate(total=Sum('montant'))['total'] or 0

        solde_disponible = total_entrees - total_sorties

        if self.montant > solde_disponible:
            raise ValidationError(
                f"Opération refusée. Solde de caisse insuffisant en {self.devise}. "
                f"Disponible : {solde_disponible:.2f} {self.devise}. "
                f"Montant demandé : {self.montant:.2f} {self.devise}."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Dépense {self.id} - {self.montant} {self.devise} ({self.get_motif_display()})"

# 15. HOSPITALISATION ET CHAMBRES ==================================
class TypeChambre(models.Model):
    libelle = models.CharField(max_length=100)
    # Utilisation de DecimalField pour la précision monétaire
    prix_nuitée = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.libelle

class Chambre(models.Model):
    # En ajoutant default="", Django ne vous posera plus la question
    nom = models.CharField(max_length=50, default="Sans nom") 
    type_chambre = models.ForeignKey(TypeChambre, on_delete=models.CASCADE)
    est_active = models.BooleanField(default=True)

    def __str__(self):
        return self.nom

class Lit(models.Model):
    chambre = models.ForeignKey(Chambre, related_name='lits', on_delete=models.CASCADE)
    nom_lit = models.CharField(max_length=50)
    est_occupe = models.BooleanField(default=False)
    est_actif = models.BooleanField(default=True)


    def __str__(self) :
        return self.nom_lit

# =====================================================================
# hospitalisation 


class Hospitalisation(models.Model):
    # Statuts de l'hospitalisation
    STATUT_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('TERMINE', 'Terminé'),
        ('ANNULE', 'Annulé'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sejours')
    lit = models.ForeignKey(Lit, on_delete=models.PROTECT, related_name='occupations')
    date_entree = models.DateTimeField(default=timezone.now)
    date_sortie = models.DateTimeField(null=True, blank=True)
    motif_admission = models.TextField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_COURS')
    observations = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Logique automatique : met à jour l'état du lit lors de l'enregistrement.
        """
        if self.statut == 'EN_COURS':
            self.lit.est_occupe = True
        elif self.statut == 'TERMINE' or self.statut == 'ANNULE':
            self.lit.est_occupe = False
            
        self.lit.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Hosp. {self.patient.noms} - Lit {self.lit.nom_lit}"

    @property
    def prix_par_jour(self):
        # Accède au prix défini dans le TypeChambre en passant par la chambre du lit
        return self.lit.chambre.type_chambre.prix_nuitée

    @property
    def nombre_jours(self):
        """
        Calcule la différence en jours. Utilise .date() pour éviter 
        les erreurs de comparaison entre datetime et date.
        """
        date_fin = self.date_sortie.date() if self.date_sortie else timezone.now().date()
        date_deb = self.date_entree.date()
        delta = date_fin - date_deb
        return max(1, delta.days)

    @property
    def cout_total(self):
        """
        Calcule le coût total basé sur le nombre de jours et le prix de la chambre.
        """
        # Conversion en float pour permettre la multiplication avec le Decimal
        return float(self.nombre_jours) * float(self.prix_par_jour)

    class Meta:
        verbose_name = "Hospitalisation"
        verbose_name_plural = "Hospitalisations"