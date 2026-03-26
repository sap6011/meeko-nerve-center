(function() {
    const container = document.getElementById('solarpunk-interconnect');
    if (!container) return;
    
    fetch('https://meekotharaccoon-cell.github.io/meeko-nerve-center/feed.json')
        .then(response => response.json())
        .then(data => {
            const latest = data.items[0];
            container.innerHTML = `
                <div style="border: 2px solid #238636; border-radius: 8px; padding: 10px; font-family: sans-serif; background: #0d1117; color: #c9d1d9;">
                    <div style="font-size: 0.8em; color: #238636; font-weight: bold; margin-bottom: 5px;">?? SOLARPUNK VERIFIED</div>
                    <div style="font-size: 1.1em; margin-bottom: 5px;">${latest.content_text}</div>
                    <a href="${latest.url}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 0.8em;">View Proof Dashboard</a>
                </div>
            `;
        })
        .catch(err => console.error('Interconnect failed to pulse:', err));
})();
