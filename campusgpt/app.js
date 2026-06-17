document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements - Chat & Input
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const emptyState = document.getElementById('empty-state');
    const messageFeed = document.getElementById('message-feed');
    
    // DOM Elements - Sidebar
    const sidebar = document.getElementById('sidebar');
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const sidebarCloseBtn = document.getElementById('sidebar-close-btn');
    const newChatBtn = document.getElementById('new-chat-btn');
    const syncDbBtn = document.getElementById('sync-db-btn');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    const dbChunkCount = document.getElementById('db-chunk-count');
    const ollamaStatus = document.getElementById('ollama-status');
    const ollamaStatusText = document.getElementById('ollama-status-text');
    const modelBadge = document.getElementById('model-badge');
    const modelBadgeText = document.getElementById('model-badge-text');
    
    // DOM Elements - Settings Modal
    const settingsToggleBtn = document.getElementById('settings-toggle-btn');
    const closeSettingsBtn = document.getElementById('close-settings-btn');
    const settingsOverlay = document.getElementById('settings-overlay');
    
    // Settings Controls
    const toggleRag = document.getElementById('toggle-rag');
    const filterCategory = document.getElementById('filter-category');
    const filterType = document.getElementById('filter-type');
    const sliderTopk = document.getElementById('slider-topk');
    const topkVal = document.getElementById('topk-val');
    const toggleHybrid = document.getElementById('toggle-hybrid');
    const toggleRerank = document.getElementById('toggle-rerank');
    const toggleRewrite = document.getElementById('toggle-rewrite');

    // State
    let conversations = [];
    let activeConversationId = null;
    let isOllamaOnline = false;

    // Load initial settings and data
    initApp();

    // Initialize application state
    function initApp() {
        // Load settings from localStorage or defaults
        const storedConversations = localStorage.getItem('campusgpt_conversations');
        if (storedConversations) {
            conversations = JSON.parse(storedConversations);
        }
        
        const storedActiveId = localStorage.getItem('campusgpt_active_id');
        if (storedActiveId && conversations.some(c => c.id === storedActiveId)) {
            activeConversationId = storedActiveId;
        }

        // Event listeners - Sidebar toggles
        sidebarToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
        });
        sidebarCloseBtn.addEventListener('click', () => {
            sidebar.classList.remove('active');
        });
        // On mobile, show sidebar with toggle button
        sidebarToggleBtn.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                sidebar.classList.add('active');
            }
        });

        // Settings Modal controls
        settingsToggleBtn.addEventListener('click', () => {
            settingsOverlay.classList.add('active');
        });
        closeSettingsBtn.addEventListener('click', () => {
            settingsOverlay.classList.remove('active');
        });
        settingsOverlay.addEventListener('click', (e) => {
            if (e.target === settingsOverlay) {
                settingsOverlay.classList.remove('active');
            }
        });

        // Top K slider value update
        sliderTopk.addEventListener('input', () => {
            topkVal.textContent = sliderTopk.value;
        });

        // Textarea auto-resize & input send button active state
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + 'px';
            
            if (chatInput.value.trim() !== '') {
                sendBtn.disabled = false;
                sendBtn.classList.add('active');
            } else {
                sendBtn.disabled = true;
                sendBtn.classList.remove('active');
            }
        });

        // Textarea Enter key submit (Enter submits, Shift+Enter adds new line)
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (chatInput.value.trim() !== '') {
                    chatForm.dispatchEvent(new Event('submit'));
                }
            }
        });

        // Form Submission
        chatForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const query = chatInput.value.trim();
            if (!query) return;

            // Reset input UI
            chatInput.value = '';
            chatInput.style.height = 'auto';
            sendBtn.disabled = true;
            sendBtn.classList.remove('active');

            await handleUserQuery(query);
        });

        // Suggestion prompt card click handler
        document.querySelectorAll('.suggestion-card').forEach(card => {
            card.addEventListener('click', () => {
                const prompt = card.getAttribute('data-prompt');
                if (prompt) {
                    handleUserQuery(prompt);
                }
            });
        });

        // New Chat Button
        newChatBtn.addEventListener('click', () => {
            startNewChat();
        });

        // Clear History Button
        clearHistoryBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to clear all conversations?')) {
                clearAllConversations();
            }
        });

        // Sync Database Button
        syncDbBtn.addEventListener('click', () => {
            syncDatabase();
        });

        // Poll server status
        checkOllamaStatus();
        setInterval(checkOllamaStatus, 10000);

        // Render layout
        renderSidebarHistory();
        renderActiveChat();
    }

    // Start a fresh, empty conversation
    function startNewChat() {
        activeConversationId = null;
        localStorage.removeItem('campusgpt_active_id');
        renderSidebarHistory();
        renderActiveChat();
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('active');
        }
    }

    // Clear all history
    function clearAllConversations() {
        conversations = [];
        activeConversationId = null;
        localStorage.removeItem('campusgpt_conversations');
        localStorage.removeItem('campusgpt_active_id');
        renderSidebarHistory();
        renderActiveChat();
    }

    // Sync local PDF folder with database
    async function syncDatabase() {
        syncDbBtn.disabled = true;
        syncDbBtn.classList.add('spinning');
        const originalText = syncDbBtn.querySelector('span').textContent;
        syncDbBtn.querySelector('span').textContent = 'Syncing...';

        try {
            const res = await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!res.ok) throw new Error('Sync failed');

            const data = await res.json();
            
            if (data.status === 'success') {
                dbChunkCount.textContent = data.total_chunks || 0;
                
                let message = `Sync Complete!\n\n`;
                if (data.updated_files && data.updated_files.length > 0) {
                    message += `Updated/Added files:\n` + data.updated_files.map(f => `- ${f}`).join('\n') + `\n\n`;
                }
                if (data.deleted_files && data.deleted_files.length > 0) {
                    message += `Deleted files:\n` + data.deleted_files.map(f => `- ${f}`).join('\n') + `\n\n`;
                }
                if ((!data.updated_files || data.updated_files.length === 0) && (!data.deleted_files || data.deleted_files.length === 0)) {
                    message += `All files are already up-to-date.\n\n`;
                }
                message += `Total Database Chunks: ${data.total_chunks}`;
                alert(message);
            } else {
                alert(`Sync failed: ${data.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error(error);
            alert(`Failed to sync database: ${error.message}`);
        } finally {
            syncDbBtn.disabled = false;
            syncDbBtn.classList.remove('spinning');
            syncDbBtn.querySelector('span').textContent = originalText;
        }
    }

    // Save conversations state to local storage
    function saveState() {
        localStorage.setItem('campusgpt_conversations', JSON.stringify(conversations));
        if (activeConversationId) {
            localStorage.setItem('campusgpt_active_id', activeConversationId);
        } else {
            localStorage.removeItem('campusgpt_active_id');
        }
    }

    // Check backend status
    async function checkOllamaStatus() {
        try {
            const res = await fetch('/api/status');
            if (!res.ok) throw new Error('Status endpoint down');
            
            const data = await res.json();
            
            isOllamaOnline = data.ollama_connected;
            dbChunkCount.textContent = data.total_chunks_in_db || 0;
            
            if (data.fine_tuned_active) {
                ollamaStatus.className = 'status-indicator online';
                ollamaStatusText.textContent = 'CampusGPT: Local Fine-Tuned';
                modelBadge.style.display = 'flex';
                modelBadgeText.textContent = 'qwen2-finetuned';
            } else if (isOllamaOnline) {
                ollamaStatus.className = 'status-indicator online';
                ollamaStatusText.textContent = `Ollama: Online`;
                modelBadge.style.display = 'flex';
                modelBadgeText.textContent = data.target_model || 'qwen2.5:3b';
            } else {
                ollamaStatus.className = 'status-indicator offline';
                ollamaStatusText.textContent = 'Ollama: Offline';
                modelBadge.style.display = 'none';
            }
        } catch (error) {
            ollamaStatus.className = 'status-indicator offline';
            ollamaStatusText.textContent = 'Ollama: Offline';
            modelBadge.style.display = 'none';
        }
    }

    // Render left sidebar with grouped chats
    function renderSidebarHistory() {
        const todayGroup = document.querySelector('#group-today .group-items');
        const yesterdayGroup = document.querySelector('#group-yesterday .group-items');
        const previousGroup = document.querySelector('#group-previous .group-items');

        todayGroup.innerHTML = '';
        yesterdayGroup.innerHTML = '';
        previousGroup.innerHTML = '';

        const now = Date.now();
        const oneDay = 24 * 60 * 60 * 1000;
        const twoDays = 2 * oneDay;
        const sevenDays = 7 * oneDay;

        let hasToday = false;
        let hasYesterday = false;
        let hasPrevious = false;

        // Sort conversations: newest first
        conversations.sort((a, b) => b.updatedAt - a.updatedAt);

        conversations.forEach(chat => {
            const diff = now - chat.updatedAt;
            
            let targetGroup;
            if (diff < oneDay) {
                targetGroup = todayGroup;
                hasToday = true;
            } else if (diff < twoDays) {
                targetGroup = yesterdayGroup;
                hasYesterday = true;
            } else {
                targetGroup = previousGroup;
                hasPrevious = true;
            }

            const item = document.createElement('div');
            item.className = `history-item ${chat.id === activeConversationId ? 'active' : ''}`;
            
            const titleSpan = document.createElement('span');
            titleSpan.className = 'item-title';
            titleSpan.textContent = chat.title;
            item.appendChild(titleSpan);

            // Options buttons
            const options = document.createElement('div');
            options.className = 'item-options';
            
            const renameBtn = document.createElement('button');
            renameBtn.className = 'option-btn';
            renameBtn.innerHTML = '<i class="fa-solid fa-pen"></i>';
            renameBtn.title = 'Rename chat';
            renameBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                const newTitle = prompt('Rename conversation:', chat.title);
                if (newTitle && newTitle.trim()) {
                    chat.title = newTitle.trim();
                    chat.updatedAt = Date.now();
                    saveState();
                    renderSidebarHistory();
                }
            });

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'option-btn';
            deleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i>';
            deleteBtn.title = 'Delete chat';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm('Delete this conversation?')) {
                    conversations = conversations.filter(c => c.id !== chat.id);
                    if (activeConversationId === chat.id) {
                        activeConversationId = null;
                        localStorage.removeItem('campusgpt_active_id');
                    }
                    saveState();
                    renderSidebarHistory();
                    renderActiveChat();
                }
            });

            options.appendChild(renameBtn);
            options.appendChild(deleteBtn);
            item.appendChild(options);

            // Click item to load chat
            item.addEventListener('click', () => {
                activeConversationId = chat.id;
                saveState();
                renderSidebarHistory();
                renderActiveChat();
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('active');
                }
            });

            targetGroup.appendChild(item);
        });

        // Hide/Show headers based on content
        document.getElementById('group-today').style.display = hasToday ? 'block' : 'none';
        document.getElementById('group-yesterday').style.display = hasYesterday ? 'block' : 'none';
        document.getElementById('group-previous').style.display = hasPrevious ? 'block' : 'none';
    }

    // Render active conversation feed
    function renderActiveChat() {
        if (!activeConversationId) {
            emptyState.style.display = 'flex';
            messageFeed.classList.add('hidden');
            return;
        }

        const chat = conversations.find(c => c.id === activeConversationId);
        if (!chat) {
            startNewChat();
            return;
        }

        emptyState.style.display = 'none';
        messageFeed.classList.remove('hidden');
        messageFeed.innerHTML = '';

        chat.messages.forEach(msg => {
            appendMessageToDOM(msg.role, msg.content, msg.results, msg.rewritten_query, false);
        });

        scrollToBottom();
    }

    // Append a message bubble to the HTML feed
    function appendMessageToDOM(role, content, results = null, rewrittenQuery = null, animate = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role === 'user' ? 'user' : 'assistant'}`;

        // Avatar
        const avatar = document.createElement('div');
        avatar.className = `message-avatar ${role === 'user' ? 'user-avatar' : 'assistant-avatar'}`;
        avatar.innerHTML = role === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-graduation-cap"></i>';
        
        // Bubble
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // Content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        // Add avatar only to left side (assistant), users don't necessarily need side avatars or can have them.
        // Let's use avatars for both for balanced ChatGPT aesthetic
        if (role === 'assistant') {
            messageDiv.appendChild(avatar);
        }

        bubble.appendChild(contentDiv);
        messageDiv.appendChild(bubble);

        if (role === 'user') {
            messageDiv.appendChild(avatar);
        }

        messageFeed.appendChild(messageDiv);

        if (role === 'assistant' && animate) {
            // Typing effect
            let placeholderSpan = document.createElement('span');
            placeholderSpan.className = 'typing-cursor';
            contentDiv.appendChild(placeholderSpan);

            simulateTyping(contentDiv, content, () => {
                placeholderSpan.remove();
                
                // Show optimizer info if present
                if (rewrittenQuery) {
                    showQueryOptimizerInfo(bubble, rewrittenQuery);
                }
                
                // Show references if present
                if (results && results.length > 0) {
                    renderReferences(bubble, results);
                }
                
                // Actions
                renderMessageActions(bubble, content);
                scrollToBottom();
            });
        } else {
            // Instant render
            contentDiv.innerHTML = formatMarkdown(content);
            
            // Show optimizer info if present
            if (role === 'assistant' && rewrittenQuery) {
                showQueryOptimizerInfo(bubble, rewrittenQuery);
            }
            
            // Show references if present
            if (role === 'assistant' && results && results.length > 0) {
                renderReferences(bubble, results);
            }

            // Actions
            if (role === 'assistant') {
                renderMessageActions(bubble, content);
            }
        }

        scrollToBottom();
        return messageDiv;
    }

    // Simulate typing animation
    function simulateTyping(container, text, callback) {
        const words = text.split(' ');
        let currentText = '';
        let i = 0;
        
        const formattedHTML = formatMarkdown(text);
        
        const typeInterval = setInterval(() => {
            if (i < words.length) {
                currentText += (i === 0 ? '' : ' ') + words[i];
                container.innerHTML = formatMarkdown(currentText) + '<span class="typing-cursor"></span>';
                scrollToBottom();
                i++;
            } else {
                clearInterval(typeInterval);
                container.innerHTML = formattedHTML;
                callback();
            }
        }, 30);
    }

    // Render query optimizer details inside AI bubble
    function showQueryOptimizerInfo(parentBubble, rewrittenQuery) {
        const info = document.createElement('div');
        info.className = 'query-optimizer-info';
        
        const icon = document.createElement('i');
        icon.className = 'fa-solid fa-arrows-spin';
        
        const span = document.createElement('span');
        span.textContent = 'Optimized Query: ';
        
        const strong = document.createElement('strong');
        strong.textContent = `"${rewrittenQuery}"`;
        
        span.appendChild(strong);
        info.appendChild(icon);
        info.appendChild(span);
        
        parentBubble.insertBefore(info, parentBubble.firstChild);
    }

    // Render citation / references accordion
    function renderReferences(parentBubble, results) {
        const accordion = document.createElement('div');
        accordion.className = 'sources-accordion';
        
        const header = document.createElement('div');
        header.className = 'sources-header';
        header.innerHTML = `
            <i class="fa-solid fa-chevron-right"></i>
            <span>References retrieved (${results.length})</span>
        `;
        
        const content = document.createElement('div');
        content.className = 'sources-content';
        
        results.forEach((res, index) => {
            const item = document.createElement('div');
            item.className = 'source-item';
            
            const scoreLabel = res.rerank_score !== undefined 
                ? `Rerank Score: ${res.rerank_score.toFixed(2)}`
                : (res.similarity !== undefined ? `Similarity: ${res.similarity}%` : '');
                
            item.innerHTML = `
                <div class="source-title">
                    <span>${index + 1}. ${res.metadata.source || 'Document'}</span>
                    <span class="source-score">${scoreLabel}</span>
                </div>
                <div class="source-text">${res.document}</div>
            `;
            content.appendChild(item);
        });

        accordion.appendChild(header);
        accordion.appendChild(content);

        // Click to toggle
        header.addEventListener('click', () => {
            accordion.classList.toggle('active');
            scrollToBottom();
        });

        parentBubble.appendChild(accordion);
    }

    // Render actions like copy
    function renderMessageActions(parentBubble, contentText) {
        const actions = document.createElement('div');
        actions.className = 'message-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
        copyBtn.addEventListener('click', () => {
            navigator.clipboard.writeText(contentText).then(() => {
                copyBtn.innerHTML = '<i class="fa-solid fa-check" style="color: var(--status-success);"></i> Copied';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                }, 2000);
            });
        });
        
        actions.appendChild(copyBtn);
        parentBubble.appendChild(actions);
    }

    // Handle user prompt query submission
    async function handleUserQuery(query) {
        // Toggle empty state off immediately
        emptyState.style.display = 'none';
        messageFeed.classList.remove('hidden');

        // Check if there is an active conversation, if not, create one
        let currentChat;
        if (!activeConversationId) {
            const title = query.length > 28 ? query.substring(0, 25) + '...' : query;
            activeConversationId = 'chat_' + Date.now();
            currentChat = {
                id: activeConversationId,
                title: title,
                messages: [],
                createdAt: Date.now(),
                updatedAt: Date.now()
            };
            conversations.unshift(currentChat);
            saveState();
            renderSidebarHistory();
            renderActiveChat();
        } else {
            currentChat = conversations.find(c => c.id === activeConversationId);
            currentChat.updatedAt = Date.now();
        }

        // Add user message to state
        const userMsg = {
            role: 'user',
            content: query,
            timestamp: Date.now()
        };
        currentChat.messages.push(userMsg);
        saveState();

        // Render user message to DOM
        appendMessageToDOM('user', query, null, null, false);
        scrollToBottom();

        // Insert placeholder loader bubble
        const loaderDiv = document.createElement('div');
        loaderDiv.className = 'chat-message assistant loader-message';
        loaderDiv.innerHTML = `
            <div class="message-avatar assistant-avatar">
                <i class="fa-solid fa-graduation-cap"></i>
            </div>
            <div class="message-bubble" style="background-color: var(--bg-assistant-bubble); border: 1px solid var(--border-color); border-radius: 18px 18px 18px 0;">
                <div class="message-content" style="color: var(--text-muted); font-style: italic; display: flex; align-items: center; gap: 8px;">
                    <i class="fa-solid fa-circle-notch fa-spin" style="color: var(--accent-secondary);"></i>
                    <span>Running Agentic RAG search...</span>
                </div>
            </div>
        `;
        messageFeed.appendChild(loaderDiv);
        scrollToBottom();

        // Disable input during search
        chatInput.disabled = true;
        chatInput.placeholder = 'CampusGPT is thinking...';
        
        // Grab settings
        const useRAG = toggleRag.checked;
        const category = filterCategory.value || null;
        const docType = filterType.value || null;
        const topK = parseInt(sliderTopk.value);
        const enableHybrid = toggleHybrid.checked;
        const enableRerank = toggleRerank.checked;
        const enableRewrite = toggleRewrite.checked;

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    top_k: topK,
                    rag_mode: useRAG,
                    category: category,
                    document_type: docType,
                    enable_hybrid: enableHybrid,
                    enable_rerank: enableRerank,
                    enable_rewrite: enableRewrite,
                    history: currentChat.messages.slice(0, -1).map(msg => ({
                        role: msg.role,
                        content: msg.content
                    }))
                })
            });

            if (!res.ok) throw new Error('Query execution failed');

            const data = await res.json();
            
            // Remove loader bubble
            loaderDiv.remove();

            const answer = data.answer || "No response generated.";
            const results = data.results || null;
            const rewrittenQuery = data.rewritten_query || null;

            // Add assistant message to state
            const assistantMsg = {
                role: 'assistant',
                content: answer,
                results: results,
                rewritten_query: rewrittenQuery,
                timestamp: Date.now()
            };
            currentChat.messages.push(assistantMsg);
            currentChat.updatedAt = Date.now();
            saveState();
            renderSidebarHistory();

            // Append response to DOM with typing animation
            appendMessageToDOM('assistant', answer, results, rewrittenQuery, true);

        } catch (error) {
            console.error(error);
            loaderDiv.remove();

            const errorMsg = {
                role: 'assistant',
                content: `**Search Failed:** ${error.message}. Please check if the local server is running and try again.`,
                timestamp: Date.now()
            };
            currentChat.messages.push(errorMsg);
            saveState();

            appendMessageToDOM('assistant', errorMsg.content, null, null, false);
        } finally {
            chatInput.disabled = false;
            chatInput.placeholder = 'Message CampusGPT...';
            chatInput.focus();
            scrollToBottom();
        }
    }

    // Scroll chat feed to bottom
    function scrollToBottom() {
        const chatArea = document.querySelector('.chat-area');
        chatArea.scrollTop = chatArea.scrollHeight;
    }

    // Basic Markdown Parser (Enhanced)
    function formatMarkdown(text) {
        if (!text) return '';
        
        let escaped = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
            
        escaped = escaped.replace(/```([\s\S]*?)```/g, (match, code) => {
            return `<pre style="background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; font-family: monospace; font-size: 13px; color: #a5b4fc; overflow-x: auto; margin: 10px 0;"><code>${code.trim()}</code></pre>`;
        });

        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/`([^`\n]+)`/g, '<code>$1</code>');

        let lines = escaped.split('\n');
        let inUl = false;
        let inOl = false;
        let formattedLines = [];

        for (let line of lines) {
            let trimLine = line.trim();
            
            let ulMatch = line.match(/^(\s*)[-*•]\s+(.+)$/);
            if (ulMatch) {
                if (inOl) {
                    formattedLines.push('</ol>');
                    inOl = false;
                }
                if (!inUl) {
                    formattedLines.push('<ul style="margin-left: 20px; margin-top: 6px; margin-bottom: 6px;">');
                    inUl = true;
                }
                formattedLines.push(`<li>${ulMatch[2]}</li>`);
                continue;
            }

            let olMatch = line.match(/^(\s*)\d+\.\s+(.+)$/);
            if (olMatch) {
                if (inUl) {
                    formattedLines.push('</ul>');
                    inUl = false;
                }
                if (!inOl) {
                    formattedLines.push('<ol style="margin-left: 20px; margin-top: 6px; margin-bottom: 6px;">');
                    inOl = true;
                }
                formattedLines.push(`<li>${olMatch[2]}</li>`);
                continue;
            }

            if (trimLine === '' || (!ulMatch && !olMatch)) {
                if (inUl) {
                    formattedLines.push('</ul>');
                    inUl = false;
                }
                if (inOl) {
                    formattedLines.push('</ol>');
                    inOl = false;
                }
            }

            formattedLines.push(line);
        }

        if (inUl) formattedLines.push('</ul>');
        if (inOl) formattedLines.push('</ol>');

        let htmlText = formattedLines.join('\n');

        htmlText = htmlText.split('\n\n').map(p => {
            if (p.trim().startsWith('<pre') || p.trim().startsWith('<ul') || p.trim().startsWith('<ol') || p.trim().startsWith('<li>') || p.trim() === '') {
                return p;
            }
            return `<p style="margin-bottom: 8px;">${p.replace(/\n/g, '<br>')}</p>`;
        }).join('');

        return htmlText;
    }
});
