// Message auto-fade functionality
document.addEventListener('DOMContentLoaded', function() {
  // Handle message fade out after 1.5 seconds
  const messages = document.querySelectorAll('.message-fade');
  
  // Function to handle the fade out effect
  function fadeOutMessage(message, index) {
    // Add a small delay for each message to create a cascade effect
    const delay = 1500 + (index * 200);
    
    // Set initial opacity to ensure fade works correctly
    message.style.opacity = '1';
    
    // Set timeout to fade out after delay
    setTimeout(function() {
      // Add slide-up with fade-out effect
      message.style.opacity = '0';
      message.style.transform = 'translateY(-20px)';
      
      // Remove element after fade completes
      setTimeout(function() {
        message.style.display = 'none';
      }, 500); // This matches the transition time in CSS
    }, delay);
  }
  
  // Process each message
  messages.forEach(fadeOutMessage);
}); 