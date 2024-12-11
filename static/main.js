import { authenticate } from './js/auth.js';
import { loadInitialNewsletters, createNewsletter } from './js/newsletters.js';
import { setupEventSource } from './js/events.js';
import { NewsletterUI } from './js/ui.js';

// Initialize UI handler
window.newsletterUI = new NewsletterUI();

// Initialize the application
async function init() {
    const isAuthenticated = await authenticate();
    if (isAuthenticated) {
        await loadInitialNewsletters();
        setupEventSource();
    }
}

// Set up form submission
document.addEventListener('DOMContentLoaded', () => {
    init();

    document.getElementById('newsletterForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            title: e.target.title.value,
            content: e.target.content.value
        };
        
        try {
            await createNewsletter(formData);
            e.target.reset(); // Clear form
        } catch (error) {
            alert('Failed to create newsletter');
        }
    });
});
