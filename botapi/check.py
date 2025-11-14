import re
from product.models import Product 

# Expresion para detectar caracteres problemáticos
pattern = re.compile(r"[\r\n\t\xa0*~_`]+")

def check_products():
    print(" Buscando productos con caracteres o campos problemáticos...\n")
    found = False

    for p in Product.objects.all():
        issues = []

        # Revisa título
        if not p.title or pattern.search(p.title):
            issues.append(f"⚠️ Título inválido: {repr(p.title)}")

        # Revisa precio (si existe)
        try:
            price_text = str(p.price)
            if pattern.search(price_text):
                issues.append(f"💰 Precio contiene caracteres inválidos: {repr(price_text)}")
        except Exception:
            issues.append("💰 Precio no legible")

        # Revisa imagen 
        try:
            image_url = str(p.image.url)
            if not image_url:
                issues.append(" Imagen vacía")
            elif "http://" in image_url:
                issues.append(" Imagen con HTTP (no HTTPS)")
        except Exception:
            issues.append(" Sin imagen asociada")

        # Mostrar resultados si hay algo raro
        if issues:
            found = True
            print(f"🔸 Producto ID {p.id} — {p.title}")
            for i in issues:
                print("   ", i)
            print()

    if not found:
        print(" Todos los productos están limpios y seguros.")

check_products()
