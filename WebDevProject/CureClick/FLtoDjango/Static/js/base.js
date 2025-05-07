document.addEventListener('DOMContentLoaded', function() {
    const userProfile = document.querySelector('.cc-navbar__user');
    const dropdownContent = document.querySelector('.dropdown-content');
    
    if (userProfile && dropdownContent) {
        userProfile.addEventListener('click', function(e) {
            e.preventDefault();
            dropdownContent.style.display = dropdownContent.style.display === 'block' ? 'none' : 'block';
        });
        
        // Close the dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userProfile.contains(e.target) && !dropdownContent.contains(e.target)) {
                dropdownContent.style.display = 'none';
            }
        });
    }
});

