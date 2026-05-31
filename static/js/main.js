document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const searchDropdown = document.getElementById("searchDropdown");
    let debounceTimeout = null;

    if (!searchInput || !searchDropdown) return;

    searchInput.addEventListener("input", function () {
        clearTimeout(debounceTimeout);
        const query = this.value.trim();

        if (query.length < 1) {
            searchDropdown.style.display = "none";
            
            return;
        }

        debounceTimeout = setTimeout(() => {
            fetch(`/api/search?q=${encodeURIComponent(query)}`)
                .then(res => res.json())
                .then(data => {
                    searchDropdown.innerHTML = "";
                    if (data.length === 0) {
                        searchDropdown.innerHTML = '<div class="p-3 text-muted text-center">No clubs found.</div>';
                        searchDropdown.style.display = "block";
                        return;
                    }

                    data.forEach(team => {
                        const row = document.createElement("a");
                        row.href = `/stadiums?team_name=${encodeURIComponent(team.name)}`;
                        row.className = "search-result-item d-flex align-items-center";
                        row.innerHTML = `
                            <img src="${team.badge}" class="search-result-badge me-3" style="width:30px; height:30px; object-fit:contain;">
                            <div>
                                <div class="fw-bold text-white">${team.name}</div>
                                <small class="text-muted">${team.stadium || 'Unknown Grounds'}</small>
                            </div>
                        `;
                        searchDropdown.appendChild(row);
                    });
                    searchDropdown.style.display = "block";
                })
                .catch(err => console.error("Error fetching search indices:", err));
        }, 250);
    });

    // Hide dropdown when focus is lost
    document.addEventListener("click", function (e) {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.style.display = "none";
        }
    });
});