from django.urls import path
from .views import *
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


     # enregistrement des employes
     #
     path('employeAdd/', employeAdd , name = 'employeAdd'),
     
 ]
