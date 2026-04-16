from django.urls import path
from .views import *
from . import views

urlpatterns = [
    # =================================
    # PAGE D'ACCUEIL front et back 
    #
    path('', home, name='home'),
    path('panel/', panel, name='panel'),

    # ===================================
    # login et logout
    #
    path('login/', login, name='login'),  
    path('deconnexion/', deconnexion, name='deconnexion'), 

    #=======================================
    # employe add, profil add, read, update 
    #
    path('employeAdd/', employeAdd, name='employeAdd'), 
    path('employeRead/', employeRead, name='employeRead'), 
    path('profilAdd/<int:user_id>/', profilAdd, name='profilAdd'),
    path('profilRead/', profilRead, name='profilRead'), 
    path('profil/supprimer/<int:profil_id>/', views.supprimer_profil, name='supprimer_profil'),
    path('profil/modifier/<int:profil_id>/', views.modifier_profil, name='modifier_profil'),
    path('gestion/password-reset/<int:user_id>/', views.admin_force_password, name='admin_force_password'),
    path('mon-profil/securite/', views.modifier_mon_mdp, name='modifier_mon_mdp'),
    

    # ============================================
    # patient add read 
    #
    path('patientAdd/', patientAdd, name='patientAdd'),
    path('patientRead/', patientRead, name='patientRead'), 
    path('liste_patients_soldes/', liste_patients_soldes, name='liste_soldes'),
    path('patient/<int:patient_id>/archives/', views.dossier_archive_patient, name='dossier_archive_patient'),
    path('caisse/payer-ordonnance/<int:patient_id>/', views.payer_ordonnance, name='payer_ordonnance'),


    # ===============================================
    # paiement fiche historique
    #
    path('encaisser-fiche/<int:patient_id>/', views.encaisser_fiche, name='encaisser_fiche'),
    path('historique_patient/<int:patient_id>/', historique_patient, name='historique_patient'),

    # ================================================
    # infirmier / Impressions
    #
    path('imprimer-recu/<int:paiement_id>/', views.imprimer_recu, name='imprimerRecu'),
    path('imprimer-facture-globale/<int:facture_id>/', views.imprimer_facture_globale, name='imprimerFactureGlobale'),
    path('prendre-signes/<int:patient_id>/', views.prendre_signes, name='prendre_signes'),
    path('historique-signes/', views.historique_signes_vitaux, name='historique_signes'),
    
    # ================================================
    # infirmier - Traitement & Ordonnances
    #
    path('infirmier/ordonnances/', views.liste_ordonnances_infirmier, name='liste_ordonnances_infirmier'),
    path('infirmier/ordonnance/<int:ordonnance_id>/', views.detail_ordonnance_traitement, name='detail_ordonnance_traitement'),

    # =================================================
    # medecin (CORRIGÉ)
    #
    path('medecin/liste-attente/', views.liste_attente_medecin, name='liste_attente_medecin'),
    path('medecin/consulter/<int:sv_id>/', views.effectuer_consultation, name='effectuer_consultation'),
    path('medecin/patients-consultes/', views.liste_patients_consultes, name='liste_patients_consultes'),
    path('medecin/resultats-labo/', views.examens_termines_medecin, name='resultats_labo_medecin'),
    
    # On garde uniquement cette ligne pour éviter le conflit 'examen_id'
    path('medecin/prescrire/<int:consultation_id>/', views.rediger_ordonnance, name='rediger_ordonnance'),
    path('ordonnances/liste/', views.liste_ordonnances, name='liste_ordonnances_generale'),
    path('ordonnance/details/<int:ordonnance_id>/', views.ordonnance_details, name='ordonnance_details'),
    
    # 4. Action de délivrance (Pour l'infirmier/pharmacien)
    path('ordonnance/delivrer/<int:ordonnance_id>/', views.delivrer_ordonnance, name='delivrer_ordonnance'),


    # ===============================================
    # reception / finance
    # 
    path('patient/<int:patient_id>/payer_examen/', views.payer_examen, name='payer_examen'),
    path('compta/journal/', views.historique_paiements, name='historique_paiements'),
    path('finance/dashboard/', views.tableau_bord_finance, name='tableau_bord_finance'),
    path('finance/depenses/', views.gestion_depenses, name='gestion_depenses'),
    
    # =================================================
    # Hospitalisation
    #

    path('chambre/ajouter/', views.ajouter_chambre, name='ajouter_chambre'),
    path('lit/ajouter/', views.ajouter_lit, name='ajouter_lit'),
    path('gestion-chambres/', views.gestion_chambres, name='gestion_chambres'),
    path('chambres/liste/', views.liste_chambres, name='liste_chambres'),
    path('lits/liste/', views.liste_lits, name='liste_lits'),

    # ===============================================
    # laboratoire
    # 
    path('labo/liste/', views.liste_examens_labo, name='liste_examens_labo'),
    path('labo/saisir-resultat/<int:examen_id>/', views.saisir_resultat_labo, name='saisir_resultat_labo'),

    # ==============================================
    # pharmacien 
    #
    path('stock/ajouter/', views.ajouter_stock, name='ajouter_stock'),
    path('medicament/nouveau/', views.ajouter_medicament, name='ajouter_medicament'),
    path('stock/liste/', views.liste_stock, name='liste_stock'),
    path('pharmacie/inventaire/', views.inventaire_global, name='page_inventaire'),
    path('pharmacie/medicament/<int:pk>/details/', views.medicament_details, name='medicament_details'),
    path('pharmacie/medicament/<int:pk>/historique/', views.medicament_historique, name='medicament_historique'),
    path('dashboard/', views.dashboard_pharmacie, name='dashboard_pharmacie'),
    path('vente/nouvelle/', views.effectuer_vente, name='effectuer_vente'),
    path('vente/historique/', views.historique_ventes, name='historique_ventes'),
    path('vente/<int:vente_id>/facture/', views.generer_facture_pdf, name='generer_facture_pdf'),
    path('vente/<int:vente_id>/annuler/', views.annuler_vente, name='annuler_vente'),

    # =================================================
    # logistique
    #
    path('logistique/materiel/', views.liste_materiel, name='liste_materiel'),
    path('logistique/materiel/ajouter/', views.ajouter_materiel, name='ajouter_materiel'),
    path('logistique/materiel/panne/<int:materiel_id>/', views.signaler_panne_materiel, name='signaler_panne'),
    path('logistique/materiel/en-panne/', views.materiel_en_panne, name='materiel_en_panne'),
]