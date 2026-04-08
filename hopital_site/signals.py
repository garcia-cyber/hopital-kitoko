from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from .models import VentePharmacie, LogPharmacie, Medicament

@receiver(post_save, sender=VentePharmacie)
def gerer_activite_pharmacie(sender, instance, created, **kwargs):
    """
    Signal unique pour gérer :
    1. La création d'une vente (Log)
    2. L'annulation d'une vente (Remise en stock + Log)
    """
    
    # --- CAS 1 : NOUVELLE VENTE CRÉÉE ---
    if created:
        LogPharmacie.objects.create(
            utilisateur=instance.vendeur,
            action='VENTE',
            details=f"Nouvelle vente #{instance.id} effectuée. Montant : {instance.total_cdf} CDF."
        )
        print(f"Audit : Vente #{instance.id} enregistrée.")

    # --- CAS 2 : ANNULATION D'UNE VENTE EXISTANTE ---
    # On vérifie que le statut est 'ANNULE' et que ce n'est pas une création
    elif instance.statut == 'ANNULE':
        
        # SÉCURITÉ : On vérifie si un log d'annulation existe déjà pour ne pas doubler le stock
        deja_annule = LogPharmacie.objects.filter(
            action='ANNULATION', 
            details__contains=f"Vente #{instance.id}"
        ).exists()

        if not deja_annule:
            with transaction.atomic():
                lignes = instance.lignes.all()
                recap_retour = []

                for ligne in lignes:
                    produit = ligne.medicament
                    # On remet les pièces vendues dans le stock
                    produit.quantite_stock_pieces += ligne.quantite
                    produit.save()
                    
                    recap_retour.append(f"{ligne.quantite}x {produit.designation}")

                # --- LOG DE L'ANNULATION POUR LE DASHBOARD ---
                # On récupère l'utilisateur qui a annulé (attribué dans la vue via _user_annulation)
                user_action = getattr(instance, '_user_annulation', instance.vendeur)
                
                LogPharmacie.objects.create(
                    utilisateur=user_action,
                    action='ANNULATION',
                    details=f"Vente #{instance.id} annulée. Retour en stock de : {', '.join(recap_retour)}."
                )

                print(f"Audit : Vente {instance.id} annulée par {user_action}. Stock corrigé.")