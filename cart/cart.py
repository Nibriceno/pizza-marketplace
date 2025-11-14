from django.conf import settings
from product.models import Product

class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def __iter__(self):
        """
        Itera sobre los productos del carrito y devuelve un diccionario uniforme
        con los datos de producto, cantidad y total.
        """
        product_ids = self.cart.keys()
        products = Product.objects.filter(pk__in=product_ids)

        for product in products:
            item = self.cart[str(product.id)]
            yield {
                "id": product.id,
                "product": product,
                "quantity": item["quantity"],
                "total_price": product.price * item["quantity"],
            }


    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    # ✅ método corregido
    def add(self, product_id, quantity=1, update_quantity=False):
        """
        Agrega un producto al carrito.
        - update_quantity=True → reemplaza cantidad exacta.
        - update_quantity=False → suma cantidad incremental.
        """
        product_id = str(product_id)

        # Si no existe el producto, inicializar en 0 (no en 1)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'id': product_id}

        if update_quantity:
            # Reemplaza cantidad exacta
            self.cart[product_id]['quantity'] = int(quantity)
        else:
            # Suma normalmente
            self.cart[product_id]['quantity'] += int(quantity)

        # Si la cantidad es 0 o menor, eliminar
        if self.cart[product_id]['quantity'] <= 0:
            self.remove(product_id)

        self.save()

    def remove(self, product_id):
    # Siempre convertir a string
        product_id = str(product_id)

        if product_id in self.cart:
            del self.cart[product_id]
            self.save()


    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def get_total_cost(self):
        for p in self.cart.keys():
            self.cart[str(p)]['product'] = Product.objects.get(pk=p)
        return sum(item['quantity'] * item['product'].price for item in self.cart.values())
