from django import forms
import requests

class ProductForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label='Título del producto',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el título del producto'
        })
    )
    
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        label='Precio',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el precio',
            'step': '0.01'
        })
    )
    
    description = forms.CharField(
        label='Descripción',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese la descripción del producto',
            'rows': 4
        })
    )
    
    category_id = forms.IntegerField(
        min_value=1,
        label='Categoría',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    image_url = forms.URLField(
        required=False,
        label='URL de imagen (opcional)',
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://ejemplo.com/imagen.jpg'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category_id'].widget.choices = self.get_category_choices()
    
    def get_category_choices(self):
        """Obtiene las categorías de la API de Platzi"""
        try:
            response = requests.get("https://api.escuelajs.co/api/v1/categories/")
            if response.status_code == 200:
                categories = response.json()
                choices = [(category.get('id'), category.get('name')) for category in categories]
                return choices
        except Exception as e:
            print(f"Error al obtener categorías: {e}")
        
        # Categorías por defecto si falla la API
        return [
            (1, 'Clothes'),
            (2, 'Electronics'),
            (3, 'Furniture'),
            (4, 'Shoes'),
            (5, 'Others')
        ]
    
    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('El precio debe ser mayor a 0')
        return price
    
    def clean_title(self):
        title = self.cleaned_data['title'].strip()
        if len(title) < 3:
            raise forms.ValidationError('El título debe tener al menos 3 caracteres')
        return title