from django.urls import path
from .views import *
from . import views 
#
#
#
urlpatterns =[
     # ===================================
     # page d'accueil login

     path('', home , name = "home") ,
     path('login/', login , name ='login') ,
     path('deco/', deco , name ='deco') ,
     path('dashboard/', dashboard , name="dashboard") ,
     path('reinitialiser-password/<int:user_id>/', views.force_reinitialiser_pass, name='force_pass'),
     path('modifier-utilisateur/<int:user_id>/', views.modifier_utilisateur, name='modifier_user'),
     path('prestations/', views.gestion_prestations, name='gestion_prestations'),
     path('config/taux/', views.modifier_taux, name='modifier_taux'),


     # employe CRUD
     #
     path('employeAdd/', employeAdd , name = 'employeAdd'),
     path('employeRead/', employeRead , name = 'employeRead') ,
     path('ajouter-fonction/<int:user_id>/', views.attribuer_fonction, name='ajouter_fonction'),
     path('employe-poste/', views.liste_employe_poste, name='liste_employe_poste'),
     path('supprimer-poste/<int:fonction_id>/', views.supprimer_poste, name='supprimer_poste'),
     

 ]
