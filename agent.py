import os
import json
import logging
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from tools import normalize_ingredients, validate_recipe

logging.basicConfig(level=logging.INFO)

# Define the structured output we demand from Gemini
class RecipeSchema(BaseModel):
    status: str = Field(description="'success' or 'error'")
    dish_name: str
    estimated_minutes: int
    difficulty: str
    servings: int
    available_ingredients: List[str] = Field(description="Ingredients used that user provided")
    optional_pantry_staples: List[str] = Field(description="Common things like salt, oil, spices")
    missing_essential_ingredients: List[str] = Field(description="Things needed but missing")
    instructions: List[str]
    reasoning_summary: str = Field(description="Why this recipe fits the constraints")

def get_agent_recipe(ingredients, max_time, preference, cuisine=""):
    """
    Agentic workflow: Plan -> Generate -> Validate -> Revise (Loop)
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "reasoning_summary": "API Key not configured on the server."}

    client = genai.Client(api_key=api_key)
    # Using gemini-2.5-flash as the standard, fast, multimodal/text model
    model_id = 'gemini-3.5-flash' 
    
    clean_ingredients = normalize_ingredients(ingredients)
    user_constraints = {
        "ingredients": clean_ingredients,
        "time": max_time,
        "preference": preference,
        "cuisine": cuisine
    }

    base_prompt = f"""
    You are an expert chef agent. The user has exactly these ingredients: {', '.join(clean_ingredients)}.
    Maximum cooking time: {max_time} minutes.
    Food preference: {preference}.
    Cuisine (optional): {cuisine}.
    
    Propose a realistic recipe. Do NOT hallucinate that they have ingredients they didn't list, 
    though you can assume basic pantry staples (water, salt, pepper, cooking oil).
    If a recipe is impossible with these constraints, return status="error" and explain why in reasoning_summary.
    """

    max_attempts = 3
    current_prompt = base_prompt

    for attempt in range(1, max_attempts + 1):
        logging.info(f"Agent Attempt {attempt}...")
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RecipeSchema,
                    temperature=0.4
                ),
            )
            
            recipe_data = json.loads(response.text)
            
            # If the LLM itself decided it's impossible, stop here.
            if recipe_data.get("status") == "error":
                recipe_data["validation"] = {"passed": False, "attempts": attempt}
                return recipe_data

            # VALIDATION STAGE
            is_valid, feedback = validate_recipe(recipe_data, user_constraints)
            
            if is_valid:
                recipe_data["validation"] = {"passed": True, "attempts": attempt}
                return recipe_data
            else:
                logging.warning(f"Validation failed: {feedback}")
                # REVISION STAGE - feed the error back to the model
                current_prompt += f"\n\nVALIDATION FAILED on previous attempt: {feedback}. Please revise the recipe to fix this error."
                
        except Exception as e:
            logging.error(f"API or Parsing Error: {str(e)}")
            return {
                "status": "error",
                "reasoning_summary": f"An error occurred while generating the recipe: {str(e)}",
                "validation": {"passed": False, "attempts": attempt}
            }
            
    # If we exhaust retries
    return {
        "status": "error",
        "reasoning_summary": "Agent could not generate a recipe that strictly met all constraints after 3 attempts.",
        "validation": {"passed": False, "attempts": max_attempts}
    }