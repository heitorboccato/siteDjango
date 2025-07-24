from django import forms
from .models import Usuario
from django.contrib.auth.forms import AuthenticationForm
from .utils import carregar_unidades_do_excel
from django.conf import settings

CAMINHO_EXCEL = settings.BASE_DIR / 'calculadora' / 'static' / 'calculadora' / 'excel' / 'Controle de Clinicas.xlsx'

class UsuarioCadastroForm(forms.ModelForm):
    senha = forms.CharField(widget=forms.PasswordInput)
    unidade = forms.ChoiceField(
        choices=carregar_unidades_do_excel(CAMINHO_EXCEL),
        label='Franquia'
    )
    
    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'unidade', 'senha']
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@amorsaude.com'):
            raise forms.ValidationError("O e-mail deve ser do domínio AmorSaúde.")
        return email

class UsuarioLoginForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')