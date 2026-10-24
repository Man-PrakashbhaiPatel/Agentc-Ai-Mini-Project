from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from agent import get_agent_recipe

# Load environment variables securely
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    """Serves the frontend application."""
    return render_template('index.html')

@app.route('/api/recipe', methods=['POST'])
def generate_recipe():
    """API endpoint to handle frontend requests and trigger the agent workflow."""
    try:
        data = request.get_json()
        
        # Input Validation
        ingredients = data.get('ingredients', [])
        max_time = data.get('max_time', 30)
        preference = data.get('preference', 'any')
        cuisine = data.get('cuisine', '')

        if not ingredients or len(ingredients) < 1:
            return jsonify({"status": "error", "reasoning_summary": "Please provide at least one ingredient."}), 400

        # Trigger Agent
        result = get_agent_recipe(
            ingredients=ingredients, 
            max_time=max_time, 
            preference=preference, 
            cuisine=cuisine
        )
        
        return jsonify(result), 200

    except Exception as e:
        # Safe error handling (don't expose stack traces)
        return jsonify({"status": "error", "reasoning_summary": "Internal server error processing request."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)