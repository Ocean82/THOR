/**
 * Chat functionality for AI system
 */

// Global variables
let currentConversationId = null;
let messageHistory = [];
let waitingForPermission = false;
let permissionReason = '';

// DOM elements
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const loadingIndicator = document.getElementById('loading-indicator');
    const permissionModal = new bootstrap.Modal(document.getElementById('permission-modal'));
    const permissionReasonElement = document.getElementById('permission-reason');
    const allowButton = document.getElementById('allow-button');
    const denyButton = document.getElementById('deny-button');
    
    // Check if all elements exist (they might not on some pages)
    if (!chatForm || !messageInput || !chatMessages) {
        return; // Exit if we're not on a page with chat functionality
    }

    // Load conversation if one is active
    const activeConversationElement = document.getElementById('active-conversation');
    if (activeConversationElement) {
        currentConversationId = activeConversationElement.dataset.conversationId;
        loadMessages(currentConversationId);
    }

    // Set up event listeners
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage();
    });

    // Permission modal buttons
    if (allowButton) {
        allowButton.addEventListener('click', function() {
            handlePermissionResponse(true);
        });
    }
    
    if (denyButton) {
        denyButton.addEventListener('click', function() {
            handlePermissionResponse(false);
        });
    }

    // Allow pressing Enter to submit
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    /**
     * Send a message to the AI
     */
    function sendMessage() {
        const message = messageInput.value.trim();
        
        if (!message) {
            return; // Don't send empty messages
        }
        
        // Clear input field
        messageInput.value = '';
        
        // Add user message to chat
        addMessageToChat('user', message);
        
        // Show loading indicator
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Send message to server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            // Update conversation ID if new
            if (data.conversation_id && !currentConversationId) {
                currentConversationId = data.conversation_id;
                // Update URL without reloading page
                history.pushState(
                    {conversationId: currentConversationId}, 
                    '', 
                    `/conversation/${currentConversationId}`
                );
            }
            
            // Check if response requires permission
            if (data.requires_permission) {
                waitingForPermission = true;
                permissionReason = data.permission_reason || 'performing this action';
                
                // Show permission modal
                if (permissionReasonElement) {
                    permissionReasonElement.textContent = data.permission_reason || 'this operation';
                }
                permissionModal.show();
                
                // Don't add AI response yet
                return;
            }
            
            // Add AI response to chat
            addMessageToChat('ai', data.response);
        })
        .catch(error => {
            console.error('Error:', error);
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            // Show error message
            addMessageToChat('system', 'Error: Failed to get a response. Please try again.');
        });
    }

    /**
     * Add a message to the chat display
     */
    function addMessageToChat(sender, content) {
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}-message`;
        
        // Create avatar
        const avatarElement = document.createElement('div');
        avatarElement.className = 'message-avatar';
        
        if (sender === 'user') {
            avatarElement.innerHTML = '<i class="fa fa-user"></i>';
        } else if (sender === 'ai') {
            avatarElement.innerHTML = '<i class="fa fa-robot"></i>';
        } else {
            avatarElement.innerHTML = '<i class="fa fa-exclamation-triangle"></i>';
        }
        
        // Create content
        const contentElement = document.createElement('div');
        contentElement.className = 'message-content';
        
        // Convert newlines to <br> tags
        contentElement.innerHTML = content.replace(/\n/g, '<br>');
        
        // Assemble message
        messageElement.appendChild(avatarElement);
        messageElement.appendChild(contentElement);
        
        // Add to chat
        chatMessages.appendChild(messageElement);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add to history
        messageHistory.push({
            sender: sender,
            content: content,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Handle user's response to permission request
     */
    function handlePermissionResponse(granted) {
        if (!waitingForPermission) {
            return;
        }
        
        // Hide modal
        permissionModal.hide();
        
        // Show loading indicator
        if (loadingIndicator) {
            loadingIndicator.classList.remove('d-none');
        }
        
        // Send permission response to server
        fetch('/api/permission', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                permission_granted: granted,
                operation: permissionReason,
                conversation_id: currentConversationId
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            
            // Add AI response to chat
            addMessageToChat('ai', data.response);
            
            // Reset permission state
            waitingForPermission = false;
            permissionReason = '';
        })
        .catch(error => {
            console.error('Error:', error);
            // Hide loading indicator
            if (loadingIndicator) {
                loadingIndicator.classList.add('d-none');
            }
            // Show error message
            addMessageToChat('system', 'Error: Failed to process permission response.');
            
            // Reset permission state
            waitingForPermission = false;
            permissionReason = '';
        });
    }

    /**
     * Load messages for a conversation
     */
    function loadMessages(conversationId) {
        // This function would load existing messages from the server
        // For now, we're just using what's already in the DOM
        const messageElements = document.querySelectorAll('.message-history .message');
        
        messageElements.forEach(element => {
            const sender = element.classList.contains('user-message') ? 'user' : 'ai';
            const content = element.querySelector('.message-content').textContent;
            
            messageHistory.push({
                sender: sender,
                content: content,
                timestamp: new Date().toISOString()
            });
        });
    }
});
