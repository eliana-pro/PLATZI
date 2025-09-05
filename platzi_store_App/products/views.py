from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
import requests
from .forms import ProductForm

class PlatziStoreAPI:
    def __init__(self):
        self.base_url = "https://api.escuelajs.co/api/v1/"
    
    def get_all_products(self):
        """Obtiene todos los productos de la API"""
        try:
            response = requests.get(f"{self.base_url}products/")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error al obtener productos: {e}")
            return []
    
    def get_product_by_id(self, product_id):
        """Obtiene un producto específico por ID"""
        try:
            response = requests.get(f"{self.base_url}products/{product_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error al obtener producto: {e}")
            return None
    
    def get_all_categories(self):
        """Obtiene todas las categorías de la API"""
        try:
            response = requests.get(f"{self.base_url}categories/")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"Error al obtener categorías: {e}")
            return []
    
    def create_product(self, product_data):
        """Crea un nuevo producto"""
        try:
            response = requests.post(f"{self.base_url}products/", json=product_data)
            if response.status_code == 201:
                return response.json()
            return None
        except Exception as e:
            print(f"Error al crear producto: {e}")
            return None
    
    def update_product(self, product_id, product_data):
        """Actualiza un producto existente"""
        try:
            response = requests.put(f"{self.base_url}products/{product_id}", json=product_data)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error al actualizar producto: {e}")
            return None
    
    def delete_product(self, product_id):
        """Elimina un producto"""
        try:
            response = requests.delete(f"{self.base_url}products/{product_id}")
            return response.status_code == 200
        except Exception as e:
            print(f"Error al eliminar producto: {e}")
            return False

# Inicializar la API
api = PlatziStoreAPI()

def get_categories_choices():
    """Obtiene las categorías de la API y las convierte en choices para el formulario"""
    categories = api.get_all_categories()
    choices = []
    
    for category in categories:
        choices.append((category.get('id'), category.get('name')))
    
    # Si no hay categorías de la API, usar las por defecto
    if not choices:
        choices = [
            (1, 'Clothes'),
            (2, 'Electronics'),
            (3, 'Furniture'),
            (4, 'Shoes'),
            (5, 'Others')
        ]
    
    return choices

def filter_products(products, filters):
    """Filtra la lista de productos según los criterios especificados"""
    filtered_products = products.copy()
    
    # Filtro por búsqueda en título
    if filters.get('search'):
        search_term = filters['search'].lower()
        filtered_products = [
            product for product in filtered_products 
            if search_term in product.get('title', '').lower()
        ]
    
    # Filtro por categoría
    if filters.get('category'):
        category_id = int(filters['category'])
        filtered_products = [
            product for product in filtered_products 
            if product.get('category', {}).get('id') == category_id
        ]
    
    # Filtro por rango de precios
    if filters.get('price_range'):
        price_range = filters['price_range']
        filtered_products = filter_by_price_range(filtered_products, price_range)
    
    return filtered_products

def filter_by_price_range(products, price_range):
    """Filtra productos por rango de precio"""
    filtered = []
    
    for product in products:
        price = float(product.get('price', 0))
        
        if price_range == '0-50' and 0 <= price <= 50:
            filtered.append(product)
        elif price_range == '50-100' and 50 < price <= 100:
            filtered.append(product)
        elif price_range == '100-500' and 100 < price <= 500:
            filtered.append(product)
        elif price_range == '500+' and price > 500:
            filtered.append(product)
    
    return filtered

def sort_products(products, sort_by):
    """Ordena la lista de productos según el criterio especificado"""
    if sort_by == 'price_asc':
        return sorted(products, key=lambda x: float(x.get('price', 0)))
    elif sort_by == 'price_desc':
        return sorted(products, key=lambda x: float(x.get('price', 0)), reverse=True)
    elif sort_by == 'name_asc':
        return sorted(products, key=lambda x: x.get('title', '').lower())
    elif sort_by == 'name_desc':
        return sorted(products, key=lambda x: x.get('title', '').lower(), reverse=True)
    else:
        return products  # orden por defecto

def get_category_count(products):
    """Cuenta el número de categorías únicas"""
    categories = set()
    for product in products:
        if product.get('category') and product['category'].get('id'):
            categories.add(product['category']['id'])
    return len(categories)

def products(request):
    """Vista principal para mostrar todos los productos con filtros"""
    # Obtener todos los productos de la API
    all_products = api.get_all_products()
    
    # Obtener categorías para el filtro
    categories = api.get_all_categories()
    
    # Obtener parámetros de filtrado desde la URL
    filters = {
        'search': request.GET.get('search', '').strip(),
        'category': request.GET.get('category', ''),
        'price_range': request.GET.get('price_range', ''),
    }
    
    # Aplicar filtros
    filtered_products = filter_products(all_products, filters)
    
    # Aplicar ordenamiento
    sort_by = request.GET.get('sort', 'default')
    sorted_products = sort_products(filtered_products, sort_by)
    
    # Paginación
    paginator = Paginator(sorted_products, 12)  # 12 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_products': len(all_products),
        'filtered_count': len(filtered_products) if any(filters.values()) else None,
        'total_categories': get_category_count(all_products),
        'current_filters': filters,
        'categories': categories,  # Agregar categorías al contexto
    }
    
    return render(request, 'products/products_list.html', context)

def product_detail(request, product_id):
    """Vista para mostrar el detalle de un producto específico"""
    product = api.get_product_by_id(product_id)
    
    if not product:
        messages.error(request, 'Producto no encontrado')
        return redirect('products:products')
    
    context = {
        'product': product
    }
    return render(request, 'products/product_detail.html', context)

def add_product(request):
    """Vista para agregar un nuevo producto"""
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            # Preparar datos para la API
            product_data = {
                'title': form.cleaned_data['title'],
                'price': float(form.cleaned_data['price']),
                'description': form.cleaned_data['description'],
                'categoryId': form.cleaned_data['category_id'],
                'images': [form.cleaned_data['image_url']] if form.cleaned_data['image_url'] else ["https://placeimg.com/640/480/any"]
            }
            
            created_product = api.create_product(product_data)
            
            if created_product:
                messages.success(request, f'Producto "{created_product["title"]}" creado exitosamente')
                return redirect('products:products')
            else:
                messages.error(request, 'Error al crear el producto')
    else:
        form = ProductForm()
    
    # Obtener categorías para el formulario
    categories = get_categories_choices()
    form.fields['category_id'].widget.choices = categories
    
    context = {
        'form': form,
        'action': 'Crear'
    }
    return render(request, 'products/product_form.html', context)

def edit_product(request, product_id):
    """Vista para editar un producto existente"""
    product = api.get_product_by_id(product_id)
    
    if not product:
        messages.error(request, 'Producto no encontrado')
        return redirect('products:products')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            # Preparar datos para la API
            product_data = {
                'title': form.cleaned_data['title'],
                'price': float(form.cleaned_data['price']),
                'description': form.cleaned_data['description'],
                'images': [form.cleaned_data['image_url']] if form.cleaned_data['image_url'] else product.get('images', ["https://placeimg.com/640/480/any"])
            }
            
            updated_product = api.update_product(product_id, product_data)
            
            if updated_product:
                messages.success(request, f'Producto "{updated_product["title"]}" actualizado exitosamente')
                return redirect('products:product_detail', product_id=product_id)
            else:
                messages.error(request, 'Error al actualizar el producto')
    else:
        # Pre-llenar el formulario con los datos del producto
        initial_data = {
            'title': product.get('title'),
            'price': product.get('price'),
            'description': product.get('description'),
            'category_id': product.get('category', {}).get('id', 1),
            'image_url': product.get('images', [''])[0] if product.get('images') else ''
        }
        form = ProductForm(initial=initial_data)
    
    # Obtener categorías para el formulario
    categories = get_categories_choices()
    form.fields['category_id'].widget.choices = categories
    
    context = {
        'form': form,
        'product': product,
        'action': 'Editar'
    }
    return render(request, 'products/product_form.html', context)

def delete_product(request, product_id):
    """Vista para eliminar un producto"""
    if request.method == 'POST':
        product = api.get_product_by_id(product_id)
        
        if not product:
            return JsonResponse({'success': False, 'message': 'Producto no encontrado'})
        
        if api.delete_product(product_id):
            messages.success(request, f'Producto "{product["title"]}" eliminado exitosamente')
            return JsonResponse({'success': True, 'message': 'Producto eliminado exitosamente'})
        else:
            return JsonResponse({'success': False, 'message': 'Error al eliminar el producto'})
    
    return JsonResponse({'success': False, 'message': 'Método no permitido'})