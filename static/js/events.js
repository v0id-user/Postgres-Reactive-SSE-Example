import { addNewsletterCard, getNewsletterCardById } from './newsletters.js';

export function setupEventSource() {
    const eventSource = new EventSource('/newsletter/events');
    
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received SSE update:', data);
        
        if (data.action === 'create') {
            addNewsletterCard(data.newsletter, true);
        } else if (data.action === 'update') {
            const card = getNewsletterCardById(data.newsletter.id);
            if (card) {
                card.querySelector('h3').textContent = data.newsletter.title;
                card.querySelector('p').textContent = data.newsletter.content;
            }
        }
    };
    
    eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        eventSource.close();
        // Attempt to reconnect after a delay
        setTimeout(setupEventSource, 5000);
    };

    // Clean up on page unload
    window.addEventListener('beforeunload', () => eventSource.close());
}
