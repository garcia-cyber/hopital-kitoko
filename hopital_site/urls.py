from django.urls import path
from .views import *
from . import views


urlpatterns = [
    # =================================
    # PAGE D'ACCUEIL front et back 
    #
    path('', home , name = 'home') ,
    path('panel/', panel , name ='panel'),
    # ===================================
    # login et logout
    #
    path('login/' , login , name = 'login'),  
    path('deconnexion/', deconnexion , name='deconnexion') , 
    #=======================================
    # employe add , profil add ,read , update 
    #
    path('employeAdd/', employeAdd , name ='employeAdd') , 
    path('employeRead/',employeRead , name = 'employeRead') , 
    path('profilAdd/<int:user_id>/', profilAdd , name = 'profilAdd'),
    path('profilRead/', profilRead , name = 'profilRead') , 

    # ============================================
    # patient add read 
    #
    path('patientAdd/', patientAdd , name = 'patientAdd') ,
    path('patientRead/' , patientRead , name = 'patientRead') , 

    # ===============================================
    # paiement fiche historique
    #
    path('encaisser-fiche/<int:patient_id>/', views.encaisser_fiche, name='encaisser_fiche'),
    path('historique_patient/<int:patient_id>' , historique_patient , name ='historique_patient') ,
    # path('solder-facture/<int:f_id>/', views.solder_facture_view, name='solderFacture'),

    # ================================================
    # imprimer
    #
    path('imprimer-recu/<int:paiement_id>/', views.imprimer_recu, name='imprimerRecu'),
    path('imprimer-facture-globale/<int:facture_id>/', views.imprimer_facture_globale, name='imprimerFactureGlobale'),



]

