"""
Скрипт для добавления более разнообразных и необычных продуктов.
Запустите в Django shell:

python manage.py shell

Затем скопируйте и вставьте этот код.
"""

from nutrition.models import FoodItem
from django.contrib.auth.models import User

# Получаем или создаем системного пользователя
try:
    system_user = User.objects.get(username='system')
except User.DoesNotExist:
    system_user = User.objects.create_user(username='system', is_staff=True)
    print("Created system user")

# Проверяем текущее количество продуктов
existing_count = FoodItem.objects.count()
print(f"Current food count: {existing_count}")

# Расширенный набор блюд мировой кухни, готовых блюд и экзотических продуктов
diverse_foods = [
    # Блюда мировой кухни
    {
        "name": "Sushi Roll",
        "description": "California roll with crab, avocado and cucumber",
        "serving_size": "6 pieces",
        "calories": 255,
        "protein": 9.0,
        "carbs": 38.0,
        "fat": 7.0,
        "fiber": 3.0,
        "sugar": 4.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Chicken Tikka Masala",
        "description": "Indian chicken dish with tomato cream sauce",
        "serving_size": "1 cup (250g)",
        "calories": 320,
        "protein": 28.0,
        "carbs": 13.0,
        "fat": 18.0,
        "fiber": 2.5,
        "sugar": 7.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Pad Thai",
        "description": "Thai stir-fried rice noodles with shrimp and peanuts",
        "serving_size": "1 cup (240g)",
        "calories": 380,
        "protein": 16.0,
        "carbs": 44.0,
        "fat": 16.0,
        "fiber": 2.0,
        "sugar": 10.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Falafel",
        "description": "Middle Eastern deep-fried chickpea balls",
        "serving_size": "4 pieces (100g)",
        "calories": 330,
        "protein": 13.0,
        "carbs": 31.0,
        "fat": 18.0,
        "fiber": 6.0,
        "sugar": 0.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Paella",
        "description": "Spanish rice dish with seafood and saffron",
        "serving_size": "1 cup (250g)",
        "calories": 345,
        "protein": 22.0,
        "carbs": 38.0,
        "fat": 12.0,
        "fiber": 2.0,
        "sugar": 2.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Готовые питательные блюда
    {
        "name": "Tuna Salad",
        "description": "Tuna mixed with mayo and vegetables",
        "serving_size": "1 cup (205g)",
        "calories": 290,
        "protein": 29.0,
        "carbs": 9.0,
        "fat": 16.0,
        "fiber": 1.0,
        "sugar": 3.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Chicken and Rice Bowl",
        "description": "Grilled chicken with steamed rice and vegetables",
        "serving_size": "1 bowl (350g)",
        "calories": 410,
        "protein": 30.0,
        "carbs": 45.0,
        "fat": 12.0,
        "fiber": 5.0,
        "sugar": 2.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Beef Stir Fry",
        "description": "Lean beef with mixed vegetables",
        "serving_size": "1 bowl (300g)",
        "calories": 320,
        "protein": 26.0,
        "carbs": 20.0,
        "fat": 15.0,
        "fiber": 3.0,
        "sugar": 6.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Lentil Soup",
        "description": "Hearty lentil soup with vegetables",
        "serving_size": "1 bowl (240ml)",
        "calories": 190,
        "protein": 10.0,
        "carbs": 33.0,
        "fat": 1.0,
        "fiber": 8.0,
        "sugar": 6.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Turkey Sandwich",
        "description": "Turkey sandwich with whole grain bread",
        "serving_size": "1 sandwich",
        "calories": 320,
        "protein": 22.0,
        "carbs": 38.0,
        "fat": 9.0,
        "fiber": 5.0,
        "sugar": 4.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Завтраки
    {
        "name": "Protein Pancakes",
        "description": "Pancakes with added protein powder",
        "serving_size": "3 pancakes (150g)",
        "calories": 280,
        "protein": 20.0,
        "carbs": 30.0,
        "fat": 8.0,
        "fiber": 2.0,
        "sugar": 5.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Vegetable Omelette",
        "description": "Egg omelette with mixed vegetables",
        "serving_size": "1 omelette (3 eggs)",
        "calories": 280,
        "protein": 21.0,
        "carbs": 6.0,
        "fat": 19.0,
        "fiber": 2.0,
        "sugar": 3.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Breakfast Burrito",
        "description": "Eggs, beans, cheese and salsa in a tortilla",
        "serving_size": "1 burrito (240g)",
        "calories": 380,
        "protein": 19.0,
        "carbs": 40.0,
        "fat": 15.0,
        "fiber": 6.0,
        "sugar": 3.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Необычные и экзотические продукты
    {
        "name": "Quinoa Bowl with Berries",
        "description": "Quinoa with mixed berries and nuts",
        "serving_size": "1 bowl (220g)",
        "calories": 290,
        "protein": 10.0,
        "carbs": 45.0,
        "fat": 9.0,
        "fiber": 7.0,
        "sugar": 12.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Tofu Stir Fry",
        "description": "Tofu with mixed vegetables",
        "serving_size": "1 cup (240g)",
        "calories": 220,
        "protein": 18.0,
        "carbs": 15.0,
        "fat": 10.0,
        "fiber": 4.0,
        "sugar": 6.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Acai Bowl",
        "description": "Acai berries blended with fruits and topped with granola",
        "serving_size": "1 bowl (300g)",
        "calories": 330,
        "protein": 5.0,
        "carbs": 65.0,
        "fat": 8.0,
        "fiber": 12.0,
        "sugar": 30.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Chia Pudding",
        "description": "Chia seeds soaked in almond milk with fruits",
        "serving_size": "1 cup (240g)",
        "calories": 180,
        "protein": 6.0,
        "carbs": 28.0,
        "fat": 8.0,
        "fiber": 10.0,
        "sugar": 10.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Супы и горячие блюда
    {
        "name": "Chicken Noodle Soup",
        "description": "Classic chicken soup with noodles",
        "serving_size": "1 bowl (240ml)",
        "calories": 180,
        "protein": 15.0,
        "carbs": 18.0,
        "fat": 5.0,
        "fiber": 2.0,
        "sugar": 1.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Beef Stew",
        "description": "Slow-cooked beef with vegetables",
        "serving_size": "1 bowl (300g)",
        "calories": 300,
        "protein": 25.0,
        "carbs": 25.0,
        "fat": 10.0,
        "fiber": 3.0,
        "sugar": 5.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Vegetable Lasagna",
        "description": "Layered pasta with vegetables and cheese",
        "serving_size": "1 piece (250g)",
        "calories": 320,
        "protein": 15.0,
        "carbs": 40.0,
        "fat": 12.0,
        "fiber": 4.0,
        "sugar": 8.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Перекусы и снеки
    {
        "name": "Trail Mix",
        "description": "Mixed nuts, seeds and dried fruits",
        "serving_size": "1/4 cup (40g)",
        "calories": 180,
        "protein": 5.0,
        "carbs": 14.0,
        "fat": 13.0,
        "fiber": 3.0,
        "sugar": 8.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Hummus with Carrots",
        "description": "Chickpea dip with raw carrots",
        "serving_size": "1/4 cup hummus with 10 baby carrots",
        "calories": 150,
        "protein": 5.0,
        "carbs": 18.0,
        "fat": 7.0,
        "fiber": 6.0,
        "sugar": 4.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Cottage Cheese with Fruit",
        "description": "Low-fat cottage cheese with mixed berries",
        "serving_size": "1 cup (225g)",
        "calories": 180,
        "protein": 24.0,
        "carbs": 14.0,
        "fat": 3.0,
        "fiber": 3.0,
        "sugar": 9.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Десерты с высоким содержанием белка
    {
        "name": "Protein Muffin",
        "description": "High protein muffin with blueberries",
        "serving_size": "1 muffin (80g)",
        "calories": 190,
        "protein": 15.0,
        "carbs": 20.0,
        "fat": 6.0,
        "fiber": 3.0,
        "sugar": 5.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Protein Ice Cream",
        "description": "Frozen dessert with added protein",
        "serving_size": "1/2 cup (100g)",
        "calories": 150,
        "protein": 20.0,
        "carbs": 10.0,
        "fat": 3.0,
        "fiber": 1.0,
        "sugar": 4.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Напитки
    {
        "name": "Green Smoothie",
        "description": "Spinach, banana, and protein powder smoothie",
        "serving_size": "1 cup (240ml)",
        "calories": 180,
        "protein": 15.0,
        "carbs": 25.0,
        "fat": 2.0,
        "fiber": 4.0,
        "sugar": 15.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Protein Hot Chocolate",
        "description": "Hot chocolate with added protein powder",
        "serving_size": "1 cup (240ml)",
        "calories": 150,
        "protein": 20.0,
        "carbs": 10.0,
        "fat": 2.0,
        "fiber": 1.0,
        "sugar": 7.0,
        "is_user_created": False,
        "created_by": system_user
    },

    # Вегетарианские и веганские блюда
    {
        "name": "Vegan Buddha Bowl",
        "description": "Bowl with quinoa, roasted vegetables and tahini",
        "serving_size": "1 bowl (350g)",
        "calories": 380,
        "protein": 12.0,
        "carbs": 65.0,
        "fat": 10.0,
        "fiber": 12.0,
        "sugar": 9.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Vegetarian Chili",
        "description": "Bean and vegetable chili",
        "serving_size": "1 cup (245g)",
        "calories": 280,
        "protein": 15.0,
        "carbs": 50.0,
        "fat": 3.0,
        "fiber": 15.0,
        "sugar": 10.0,
        "is_user_created": False,
        "created_by": system_user
    },
    {
        "name": "Black Bean Burger",
        "description": "Vegetarian burger patty with black beans",
        "serving_size": "1 patty (120g)",
        "calories": 200,
        "protein": 12.0,
        "carbs": 30.0,
        "fat": 5.0,
        "fiber": 8.0,
        "sugar": 2.0,
        "is_user_created": False,
        "created_by": system_user
    }
]

# Создаем продукты в базе данных
created_count = 0
for food in diverse_foods:
    if not FoodItem.objects.filter(name=food["name"]).exists():
        try:
            FoodItem.objects.create(**food)
            created_count += 1
            print(f"Added: {food['name']}")
        except Exception as e:
            print(f"Error adding {food['name']}: {str(e)}")

print(f"\nAdded {created_count} new diverse food items")
print(f"Total food items now: {FoodItem.objects.count()}")

# Проверяем, что продукты добавились
new_foods = FoodItem.objects.order_by('-id')[:created_count]
print("\nNew food items added:")
for i, food in enumerate(new_foods, 1):
    print(f"{i}. {food.name} - {food.calories} kcal ({food.protein}p/{food.carbs}c/{food.fat}f)")