export async function authenticate() {
    try {
        const response = await fetch('/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: 'test',
                password: 'test'
            })
        });
        
        if (!response.ok) {
            throw new Error('Authentication failed');
        }
        
        console.log('Authentication successful');
        return true;
    } catch (error) {
        console.error('Authentication error:', error);
        return false;
    }
}
