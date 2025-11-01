from django import forms
from django.contrib.auth import get_user_model
from .models import Product, Category, Tag, ProductImage, ProductVariant, ProductReview
from tinymce.widgets import TinyMCE

User = get_user_model()


class ProductForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier un produit
    """
    description = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
    
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'tags', 'main_image', 'description', 'short_description',
            'price', 'original_price', 'discount_percentage', 'is_on_sale',
            'sale_start_date', 'sale_end_date', 'compare_price',
            'stock', 'min_stock', 'status', 'is_featured', 'is_digital', 'scheduled_publish_at'
        ]
        widgets = {
            'sale_start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'sale_end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'scheduled_publish_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'short_description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # IMPORTANT: Afficher TOUTES les catégories actives (y compris vides)
        # Cela permet aux vendeurs d'ajouter des produits dans n'importe quelle catégorie
        # La catégorie apparaîtra automatiquement sur le site une fois qu'elle a des produits
        self.fields['category'].queryset = Category.objects.filter(
            is_active=True
        ).select_related('parent').order_by('parent__name', 'name')
        
        self.fields['category'].help_text = 'Sélectionnez la catégorie du produit'
        self.fields['category'].label = 'Catégorie'
        
        # Tags avec un widget personnalisé pour une meilleure UX
        self.fields['tags'].queryset = Tag.objects.all().order_by('name')
        self.fields['tags'].widget.attrs = {
            'class': 'form-check-input'
        }
        self.fields['tags'].help_text = 'Sélectionnez les étiquettes du produit'
        self.fields['tags'].required = False
        
        # Styling des champs
        for field_name, field in self.fields.items():
            if field_name in ['is_on_sale', 'is_featured', 'is_digital']:
                field.widget.attrs['class'] = 'form-check-input'
            elif field_name == 'main_image':
                field.widget.attrs['class'] = 'form-control'
                field.widget.attrs['accept'] = 'image/*'
            elif field_name == 'status':
                field.widget.attrs['class'] = 'form-select'
            elif field_name == 'scheduled_publish_at':
                field.widget.attrs['class'] = 'form-control'
            elif field_name == 'tags':
                # Tags déjà configuré avec CheckboxSelectMultiple
                continue
            else:
                field.widget.attrs['class'] = 'form-control'


class ProductImageForm(forms.ModelForm):
    """
    Formulaire pour les images de produits
    """
    class Meta:
        model = ProductImage
        fields = ['image', 'alt_text', 'order', 'is_active']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),
            'alt_text': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductVariantForm(forms.ModelForm):
    """
    Formulaire pour les variantes de produits
    """
    class Meta:
        model = ProductVariant
        fields = ['name', 'price', 'stock', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductSearchForm(forms.Form):
    """
    Formulaire de recherche de produits
    """
    query = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un produit...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    min_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix min',
            'step': '0.01'
        })
    )
    max_price = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prix max',
            'step': '0.01'
        })
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('-created_at', 'Plus récent'),
            ('created_at', 'Plus ancien'),
            ('price', 'Prix croissant'),
            ('-price', 'Prix décroissant'),
            ('name', 'Nom A-Z'),
            ('-name', 'Nom Z-A'),
            ('-rating', 'Mieux noté'),
            ('-sales_count', 'Plus vendu'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ProductReviewForm(forms.ModelForm):
    """
    Formulaire pour les avis sur les produits
    """
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} étoile{"s" if i > 1 else ""}') for i in range(1, 6)],
                attrs={'class': 'form-control'}
            ),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Partagez votre expérience avec ce produit...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].required = True
        self.fields['comment'].required = False


class CategoryForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une catégorie
    """
    class Meta:
        model = Category
        fields = ['name', 'description', 'image', 'parent', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control-file'}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = Category.objects.filter(is_active=True)


class TagForm(forms.ModelForm):
    """
    Formulaire pour créer/modifier une étiquette
    """
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'style': 'width: 60px; height: 38px;'
            }),
        }
