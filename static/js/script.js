document.addEventListener('DOMContentLoaded', () => {
    const ingredientInput = document.getElementById('ingredient-input');
    const tagsWrapper = document.getElementById('tags-wrapper');
    const submitBtn = document.getElementById('submit-btn');
    
    let ingredients = [];

    // --- Tag Input Logic ---
    function renderTags() {
        tagsWrapper.innerHTML = '';
        ingredients.forEach((ing, index) => {
            const tag = document.createElement('div');
            tag.className = 'tag';
            tag.innerHTML = `${ing} <span onclick="removeTag(${index})">&times;</span>`;
            tagsWrapper.appendChild(tag);
        });
    }

    window.removeTag = (index) => {
        ingredients.splice(index, 1);
        renderTags();
    };

    ingredientInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const val = ingredientInput.value.trim();
            if (val && !ingredients.includes(val)) {
                ingredients.push(val);
                ingredientInput.value = '';
                renderTags();
            }
        }
    });

    // --- API Submission Logic ---
    submitBtn.addEventListener('click', async () => {
        if (ingredients.length === 0) {
            alert("Please add at least one ingredient!");
            return;
        }

        // Gather data
        const maxTime = document.getElementById('time-select').value;
        const preference = document.getElementById('pref-select').value;
        const cuisine = document.getElementById('cuisine-input').value;

        // UI States
        document.getElementById('result-card').classList.add('hidden');
        document.getElementById('error-card').classList.add('hidden');
        document.getElementById('loading-indicator').classList.remove('hidden');
        submitBtn.disabled = true;

        // Simulate agent progress updates
        const loadingText = document.getElementById('loading-text');
        const states = ["Agent analyzing ingredients...", "Planning recipe...", "Validating constraints...", "Finalizing instructions..."];
        let stateIdx = 0;
        const stateInterval = setInterval(() => {
            if(stateIdx < states.length) { loadingText.innerText = states[stateIdx++]; }
        }, 1500);

        try {
            const response = await fetch('/api/recipe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ingredients, max_time: maxTime, preference, cuisine })
            });
            
            const data = await response.json();
            clearInterval(stateInterval);

            if (data.status === 'success') {
                populateRecipeCard(data);
            } else {
                showError(data.reasoning_summary || "Agent failed to find a valid recipe.");
            }
        } catch (err) {
            clearInterval(stateInterval);
            showError("Network error. Is the Flask server running?");
        } finally {
            document.getElementById('loading-indicator').classList.add('hidden');
            submitBtn.disabled = false;
            loadingText.innerText = "Agent analyzing ingredients...";
        }
    });

    function populateRecipeCard(data) {
        document.getElementById('r-title').innerText = data.dish_name;
        document.getElementById('r-time').innerText = `⏱️ ${data.estimated_minutes} min`;
        document.getElementById('r-diff').innerText = `📊 ${data.difficulty}`;
        document.getElementById('r-serve').innerText = `🍽️ ${data.servings} Servings`;
        document.getElementById('r-summary').innerText = data.reasoning_summary;

        const populateList = (id, items) => {
            const ul = document.getElementById(id);
            ul.innerHTML = '';
            if(!items || items.length === 0) {
                ul.innerHTML = '<li>None</li>';
                return;
            }
            items.forEach(item => {
                const li = document.createElement('li');
                li.innerText = item;
                ul.appendChild(li);
            });
        };

        populateList('r-available', data.available_ingredients);
        populateList('r-staples', data.optional_pantry_staples);
        populateList('r-missing', data.missing_essential_ingredients);
        populateList('r-instructions', data.instructions);

        const valText = document.getElementById('r-validation');
        if (data.validation) {
            valText.innerText = `Agent Validation: ${data.validation.passed ? 'Passed ✅' : 'Failed ❌'} (Attempts: ${data.validation.attempts})`;
        }

        document.getElementById('result-card').classList.remove('hidden');
    }

    function showError(msg) {
        document.getElementById('error-message').innerText = msg;
        document.getElementById('error-card').classList.remove('hidden');
    }
});