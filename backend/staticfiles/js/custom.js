// Custom JavaScript for Ticketing System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirm before deleting
    const deleteButtons = document.querySelectorAll('[data-confirm-delete]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm-delete') || 'Are you sure you want to delete this item?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Auto-refresh dashboard data every 5 minutes
    const dashboardElement = document.querySelector('[data-dashboard-refresh]');
    if (dashboardElement) {
        setInterval(function() {
            location.reload();
        }, 300000); // 5 minutes
    }

    // Handle form submission with loading state
    const forms = document.querySelectorAll('form[data-loading-text]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                const originalText = submitButton.innerHTML;
                const loadingText = form.getAttribute('data-loading-text') || 'Loading...';

                submitButton.innerHTML = `<span class="spinner-border spinner-border-sm" role="status"></span> ${loadingText}`;
                submitButton.disabled = true;

                // Re-enable button after 10 seconds in case form submission fails
                setTimeout(function() {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 10000);
            }
        });
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('[data-copy-to-clipboard]');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy-to-clipboard');
            navigator.clipboard.writeText(textToCopy).then(function() {
                const originalText = button.innerHTML;
                button.innerHTML = '<i class="bi bi-check"></i> Copied!';
                button.classList.remove('btn-outline-secondary');
                button.classList.add('btn-success');

                setTimeout(function() {
                    button.innerHTML = originalText;
                    button.classList.remove('btn-success');
                    button.classList.add('btn-outline-secondary');
                }, 2000);
            });
        });
    });

    // Toggle password visibility
    const passwordToggles = document.querySelectorAll('[data-toggle-password]');
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const targetId = this.getAttribute('data-toggle-password');
            const passwordInput = document.getElementById(targetId);

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                this.innerHTML = '<i class="bi bi-eye-slash"></i>';
            } else {
                passwordInput.type = 'password';
                this.innerHTML = '<i class="bi bi-eye"></i>';
            }
        });
    });

    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(function(textarea) {
        function resizeTextarea() {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }

        resizeTextarea();
        textarea.addEventListener('input', resizeTextarea);
    });

    // Smooth scroll to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                const targetElement = document.querySelector(targetId);
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });

    // Add active class to current nav item
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Handle dropdown menus on mobile
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    dropdowns.forEach(function(dropdown) {
        if (window.innerWidth <= 768) {
            dropdown.setAttribute('data-bs-toggle', 'dropdown');
        }
    });

    // Search functionality (client-side filtering)
    const searchInputs = document.querySelectorAll('[data-search-target]');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            const targetSelector = this.getAttribute('data-search-target');
            const searchTerm = this.value.toLowerCase();
            const targetElements = document.querySelectorAll(targetSelector);

            targetElements.forEach(function(element) {
                const text = element.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    element.style.display = '';
                } else {
                    element.style.display = 'none';
                }
            });
        });
    });

    // Lazy load images
    const lazyImages = document.querySelectorAll('img[data-src]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.getAttribute('data-src');
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });

        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });
    }

    // Print functionality
    const printButtons = document.querySelectorAll('[data-print]');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Export functionality (basic CSV export for tables)
    const exportButtons = document.querySelectorAll('[data-export-table]');
    exportButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const tableId = this.getAttribute('data-export-table');
            const table = document.getElementById(tableId);

            if (table) {
                exportTableToCSV(table, 'export.csv');
            }
        });
    });
});

// Utility Functions

function exportTableToCSV(table, filename) {
    const rows = table.querySelectorAll('tr');
    const csv = [];

    for (let i = 0; i < rows.length; i++) {
        const row = [], cols = rows[i].querySelectorAll('td, th');

        for (let j = 0; j < cols.length; j++) {
            let text = cols[j].innerText.trim();
            text = text.replace(/"/g, '""'); // Escape double quotes
            if (text.includes(',') || text.includes('"')) {
                text = `"${text}"`; // Quote if contains comma or quote
            }
            row.push(text);
        }
        csv.push(row.join(','));
    }

    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');

    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function showLoadingSpinner(element) {
    element.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Loading...';
    element.disabled = true;
}

function hideLoadingSpinner(element, originalText) {
    element.innerHTML = originalText;
    element.disabled = false;
}

function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function debounce(func, wait, immediate) {
    let timeout;
    return function() {
        const context = this, args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}