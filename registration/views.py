from django.contrib import messages, auth
from django.urls import reverse
from django.shortcuts import redirect, render

# Create your views here.
from django.views.decorators.debug import sensitive_post_parameters
from registration.forms import CandidatoAuthenticationForm


@sensitive_post_parameters("password", "password_confirm")
def login(request):
    if request.user.is_authenticated:
        messages.info(request, "Você já está com login ativo.")
        return redirect("processoseletivo")

    form = CandidatoAuthenticationForm(request, request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = auth.authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                messages.success(request, "Acesso realizado com sucesso.")
                next = request.GET.get("next")
                return redirect(next or "processoseletivo")
            else:
                messages.warning(request, "Usuário e/ou senha incorretos.")

    return render(request, "registration/login.html", {"form": form})


def logout(request):
    auth.logout(request)
    messages.success(request, "Saída realizada com sucesso!")
    next = request.GET.get("next", None) or reverse("processoseletivo")
    return redirect(next)
