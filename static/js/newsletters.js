export async function loadInitialNewsletters() {
    try {
        const response = await fetch('/newsletters');
        if (!response.ok) throw new Error('Failed to fetch newsletters');
        const newsletters = await response.json();
        newsletters.forEach(newsletter => addNewsletterCard(newsletter));
    } catch (error) {
        console.error('Error loading newsletters:', error);
    }
}

export async function createNewsletter(formData) {
    try {
        const response = await fetch('/newsletters', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) throw new Error('Failed to create newsletter');
        return await response.json();
    } catch (error) {
        console.error('Error creating newsletter:', error);
        throw error;
    }
}

export async function updateNewsletter(id, title, content) {
    try {
        const response = await fetch(`/newsletters/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title, content })
        });
        
        if (!response.ok) throw new Error('Failed to update newsletter');
        return await response.json();
    } catch (error) {
        console.error('Error updating newsletter:', error);
        throw error;
    }
}

export function addNewsletterCard(newsletter, isNew = false) {
    const newslettersContainer = document.getElementById('newsletters');
    const card = document.createElement('div');
    card.className = `newsletter-card p-6 mb-4 rounded-lg ${isNew ? 'new-newsletter' : ''}`;
    card.dataset.id = newsletter.id;
    
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <h3 class="text-xl font-bold mb-2">${newsletter.title}</h3>
            <button onclick="window.newsletterUI.editNewsletter(${newsletter.id})" class="text-blue-600 hover:text-blue-800">Edit</button>
        </div>
        <p class="text-gray-700">${newsletter.content}</p>
        <div class="text-sm text-gray-500 mt-4">
            ${new Date(newsletter.created_at).toLocaleString()}
        </div>
    `;
    
    newslettersContainer.insertBefore(card, newslettersContainer.firstChild);
}

export function getNewsletterCardById(id) {
    return document.querySelector(`.newsletter-card[data-id="${id}"]`);
}
