from django.shortcuts import render , redirect
from .forms import *
from .models import *
from django.contrib.auth import authenticate , login as auth , logout ,update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

# Create your views here.

# 1
# ======================================================================================
# PAGE D'ACCUEIL
# ======================================================================================
def home(request):
    return render(request , "front-end/index.html")

# 2
# =====================================================================
# CONNEXION DANS LE SYSTEME
# =====================================================================
def login(request):
    msg = None
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username = username , password = password)
            if user :
                auth(request,user)
                return redirect('dashboard')
            else:
                msg = "mot de passe erronne !!!:🤞"
    form = LoginForm()
    return render(request , 'back-end/page-login.html',{'form':form ,'msg':msg})

# 3
# ==========================================================================
# DECONNEXION
# ==========================================================================
def deco(request):
    logout(request)
    return redirect('home')

# 4
# ==========================================================================
# DASHBOARD
# ==========================================================================
@login_required
def dashboard(request):

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # compte les nombres des utilisateurs
    utilisateurs = User.objects.count()



    return render(request , 'back-end/index.html',
                  {
                  'fonctionKey': fonctionKey,
                  'utilisateurs' : utilisateurs
                  }
                  )
# 5
# ===========================================================================
# AJOUTER UTILISATEURS
# ===========================================================================
@login_required()
def employeAdd(request):
    msg = None
    if request.method =='POST':
        form = EmployeForm(request.POST)
        if form.is_valid():
            user = form.save(commit= False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            # auth(request,user)

            form = EmployeForm(request.POST)
            msg = "employe enregistre "


    form = EmployeForm()
    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None


    return render(request,'back-end/employeAdd.html',{'fonctionKey':fonctionKey, 'form':form, 'msg':msg})

# 6
# ============================================================================
# LISTE DES UTILISATEURS ENREGISTRE
# ============================================================================
@login_required
def employeRead(request):

    # verification de la fonction
    role = Fonction.objects.filter(userKey = request.user).first()
    fonctionKey = role.fonctionKey.roleName if role else None

    # listes des utilisateurs
    
    return render(request , 'back-end/employeRead.html')
