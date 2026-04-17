document.addEventListener('DOMContentLoaded', () => {
    // Experience level toggles (Interview page)
    const expBtns = document.querySelectorAll('.experience-toggles .btn');
    if (expBtns.length > 0) {
        expBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                expBtns.forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    // Sidebar active state visual feedback
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function(e) {
            if (this.getAttribute('href') === '#') {
                e.preventDefault();
                navItems.forEach(nav => nav.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });

    // Learning Path Phase toggles
    const phaseItems = document.querySelectorAll('.phase-item');
    const phaseContents = document.querySelectorAll('.phase-content-data');
    if (phaseItems.length > 0) {
        phaseItems.forEach(item => {
            item.addEventListener('click', function() {
                // Remove active from all
                phaseItems.forEach(p => p.classList.remove('active'));
                // Set active to clicked
                this.classList.add('active');
                
                // Switch content
                const targetPhase = this.getAttribute('data-phase');
                if (phaseContents.length > 0) {
                    phaseContents.forEach(content => {
                        content.style.display = 'none';
                        if (content.id === `content-${targetPhase}`) {
                            content.style.display = 'block';
                        }
                    });
                }
            });
        });
    }

    // Insights Tabs toggles
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content-data');
    if (tabBtns.length > 0) {
        tabBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Remove active from all tabs
                tabBtns.forEach(t => t.classList.remove('active'));
                this.classList.add('active');

                // Switch content
                const targetTab = this.getAttribute('data-tab');
                if (tabContents.length > 0) {
                    tabContents.forEach(content => {
                        content.style.display = 'none';
                        if (content.id === `tab-${targetTab}`) {
                            content.style.display = 'flex'; // flex for result lists
                        }
                    });
                }
            });
        });
    }
});
