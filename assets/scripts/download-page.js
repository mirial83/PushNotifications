        // Download page JavaScript
        document.addEventListener('DOMContentLoaded', function() {
            // Redirect to login after 3 seconds
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 3000);
        });
        
        async function checkServerStatus() {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            
            try {
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'getServerStatus' })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    statusDot.className = 'status-dot';
                    statusText.textContent = 'Server Online - Ready for download';
                } else {
                    statusDot.className = 'status-dot offline';
                    statusText.textContent = 'Server issues detected';
                }
            } catch (error) {
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Unable to connect to server';
            }
        }
        
        async function loadVersionInfo() {
            try {
                const response = await fetch('/api/index', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: 'getClientVersion' })
                });
                
                const result = await response.json();
                
                if (result.success && result.version) {
                    const versionBadge = document.getElementById('versionBadge');
                    const versionText = document.getElementById('versionText');
                    const downloadButton = document.getElementById('downloadButton');
                    
                    versionBadge.textContent = `Current Version: ${result.version}`;
                    versionText.textContent = `v${result.version}`;
                    
                    // Set up download link
                    downloadButton.href = '/api/index?action=downloadClient';
                    downloadButton.style.display = 'inline-block';
                } else {
                    document.getElementById('versionBadge').textContent = 'Version: 2.0.0';
                    document.getElementById('versionText').textContent = 'v2.0.0';
                    document.getElementById('downloadButton').style.display = 'inline-block';
                    document.getElementById('downloadButton').href = '/api/index?action=downloadClient';
                }
            } catch (error) {
                console.error('Error loading version info:', error);
                document.getElementById('versionBadge').textContent = 'Version: 2.0.0';
                document.getElementById('versionText').textContent = 'v2.0.0';
                document.getElementById('downloadButton').style.display = 'inline-block';
                document.getElementById('downloadButton').href = '/api/index?action=downloadClient';
            }
        }
        
        // Refresh status every 30 seconds
        setInterval(checkServerStatus, 30000);