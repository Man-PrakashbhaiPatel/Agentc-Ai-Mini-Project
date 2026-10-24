def normalize_ingredients(ingredients):
    """Standardizes ingredient names and removes duplicates."""
    normalized = set(ing.strip().lower() for ing in ingredients if ing.strip())
    return list(normalized)

def calculate_time_feasibility(recipe_time, max_allowed_time):
    """Checks if the proposed recipe fits within the user's time constraints."""
    try:
        return int(recipe_time) <= int(max_allowed_time)
    except (ValueError, TypeError):
        return False

def check_food_preference(dish_name, ingredients_used, preference):
    """Basic deterministic check to catch obvious preference violations."""
    if preference.lower() == "vegetarian":
        meat_keywords = ['chicken', 'beef', 'pork', 'fish', 'bacon', 'meat', 'lamb']
        for item in ingredients_used + [dish_name]:
            if any(meat in item.lower() for meat in meat_keywords):
                return False, f"Contains meat keyword in vegetarian request."
    return True, "Passed"

def validate_recipe(recipe, user_constraints):
    """
    Validates the generated recipe against user constraints.
    Returns (is_valid: bool, feedback_string: str)
    """
    if not recipe:
        return False, "No recipe provided."

    # 1. Check Time
    if not calculate_time_feasibility(recipe.get("estimated_minutes", 999), user_constraints['time']):
        return False, f"Recipe takes {recipe.get('estimated_minutes')} mins, but user requested max {user_constraints['time']} mins."

    # 2. Check Preferences
    pref_passed, pref_feedback = check_food_preference(
        recipe.get("dish_name", ""), 
        recipe.get("available_ingredients", []), 
        user_constraints['preference']
    )
    if not pref_passed:
        return False, pref_feedback
        
    # 3. Check for essential missing ingredients disguised as available
    # (If the user gave 3 ingredients, and the recipe claims 10 available, it hallucinated)
    claimed_available = recipe.get("available_ingredients", [])
    if len(claimed_available) > len(user_constraints['ingredients']) + 2: # +2 leniency for salt/water assumptions
        return False, "Recipe lists too many available ingredients that the user did not provide."

    return True, "Recipe is valid."