import { updateNewsletter, getNewsletterCardById } from './newsletters.js';

export class NewsletterUI {
    editNewsletter(id) {
        const card = getNewsletterCardById(id);
        if (!card) return;
        
        const title = card.querySelector('h3').textContent;
        const content = card.querySelector('p').textContent;
        
        // Save the original content
        card.dataset.originalTitle = title;
        card.dataset.originalContent = content;
        
        // Replace content with form
        card.innerHTML = `
            <form onsubmit="window.newsletterUI.handleEditSubmit(event, ${id})" class="space-y-4">
                <div>
                    <input type="text" value="${title}" 
                        class="w-full p-2 border rounded" 
                        name="title" required>
                </div>
                <div>
                    <textarea name="content" 
                        class="w-full p-2 border rounded" 
                        rows="4" required>${content}</textarea>
                </div>
                <div class="flex justify-end space-x-2">
                    <button type="button" 
                        onclick="window.newsletterUI.cancelEdit(${id})" 
                        class="px-4 py-2 text-gray-600 hover:text-gray-800">
                        Cancel
                    </button>
                    <button type="submit" 
                        class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                        Save
                    </button>
                </div>
            </form>
        `;
    }

    async handleEditSubmit(event, id) {
        event.preventDefault();
        const form = event.target;
        const title = form.title.value;
        const content = form.content.value;
        
        try {
            const updatedNewsletter = await updateNewsletter(id, title, content);
            const card = getNewsletterCardById(id);
            
            // Update card with new content
            card.innerHTML = `
                <div class="flex justify-between items-start mb-4">
                    <h3 class="text-xl font-bold mb-2">${updatedNewsletter.title}</h3>
                    <button onclick="window.newsletterUI.editNewsletter(${id})" class="text-blue-600 hover:text-blue-800">Edit</button>
                </div>
                <p class="text-gray-700">${updatedNewsletter.content}</p>
                <div class="text-sm text-gray-500 mt-4">
                    ${new Date(updatedNewsletter.created_at).toLocaleString()}
                </div>
            `;
        } catch (error) {
            alert('Failed to update newsletter');
        }
    }

    cancelEdit(id) {
        const card = getNewsletterCardById(id);
        if (!card) return;
        
        const title = card.dataset.originalTitle;
        const content = card.dataset.originalContent;
        
        card.innerHTML = `
            <div class="flex justify-between items-start mb-4">
                <h3 class="text-xl font-bold mb-2">${title}</h3>
                <button onclick="window.newsletterUI.editNewsletter(${id})" class="text-blue-600 hover:text-blue-800">Edit</button>
            </div>
            <p class="text-gray-700">${content}</p>
            <div class="text-sm text-gray-500 mt-4">
                ${new Date().toLocaleString()}
            </div>
        `;
    }
}
