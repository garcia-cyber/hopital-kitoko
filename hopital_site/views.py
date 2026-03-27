from django.shortcuts import render , redirect 

# Create your views here.



# ============================================
# ============================================
# home page d'acueil

def home(request):
    return render(request , 'front-end/index.html')