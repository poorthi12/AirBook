setTimeout(() => {
    const messages = document.querySelectorAll(".flash-message");

    messages.forEach(message => {
        message.style.opacity = "0";

        setTimeout(() => {
            message.remove();
        }, 300);
    });
}, 2000);


document.addEventListener("DOMContentLoaded", function () {
    const departureInput = document.getElementById("departureDate");
    const returnInput = document.getElementById("returnDate");

    if (departureInput) {
        const today = new Date();
        const isoToday = today.toISOString().split("T")[0];
        departureInput.min = isoToday;
    }

    if (departureInput && returnInput) {
        departureInput.addEventListener("change", function () {
            returnInput.min = departureInput.value || "";
            if (returnInput.value && returnInput.value < departureInput.value) {
                returnInput.value = "";
            }
        });
    }

    const customSelects = document.querySelectorAll(".custom-select");

    customSelects.forEach(select => {
        const trigger = select.querySelector(".custom-select-trigger");
        const options = select.querySelectorAll(".custom-option");
        const hiddenInput = select.querySelector("input[type='hidden']");
        const valueText = select.querySelector(".custom-select-value");

        trigger.addEventListener("click", function (event) {
            event.stopPropagation();

            customSelects.forEach(other => {
                if (other !== select) {
                    other.classList.remove("open");
                    other.querySelector(".custom-select-trigger").setAttribute("aria-expanded", "false");
                }
            });

            const isOpen = select.classList.contains("open");
            select.classList.toggle("open", !isOpen);
            trigger.setAttribute("aria-expanded", String(!isOpen));
        });

        options.forEach(option => {
            option.addEventListener("click", function () {
                const value = option.dataset.value || "";
                const label = option.textContent.trim();

                hiddenInput.value = value;
                valueText.textContent = label;

                options.forEach(item => {
                    item.classList.toggle("is-selected", item === option);
                });

                trigger.classList.toggle("is-selected", value !== "");
                select.classList.remove("open");
                trigger.setAttribute("aria-expanded", "false");
            });
        });
    });

    document.addEventListener("click", function () {
        customSelects.forEach(select => {
            select.classList.remove("open");
            select.querySelector(".custom-select-trigger").setAttribute("aria-expanded", "false");
        });
    });

    const upcomingFlightsContainer = document.getElementById("upcomingFlights");
    const allUpcomingFlightsContainer = document.getElementById("allUpcomingFlights");
    const toggleAllUpcomingBtn = document.getElementById("toggleAllUpcoming");

    if (!upcomingFlightsContainer && !allUpcomingFlightsContainer) {
        return;
    }

    if (toggleAllUpcomingBtn && allUpcomingFlightsContainer) {
        toggleAllUpcomingBtn.addEventListener("click", function () {
            const isExpanded = allUpcomingFlightsContainer.classList.toggle("collapsed");
            const expanded = !isExpanded;
            toggleAllUpcomingBtn.textContent = expanded ? "Hide all" : "View all";
            toggleAllUpcomingBtn.setAttribute("aria-expanded", String(expanded));
        });
    }

    function createFlightCard(flight) {
        const card = document.createElement("div");
        card.className = "upcoming-flight-card all-upcoming-flight-card";

        const header = document.createElement("div");
        header.className = "upcoming-card-header";
        header.innerHTML = `
            <div class="upcoming-route">
                <strong>${flight.from_code || flight.from}</strong>
                <span>→</span>
                <strong>${flight.to_code || flight.to}</strong>
            </div>
            <span class="flight-badge">${flight.flight_number || "SK"}</span>
        `;

        const body = document.createElement("div");
        body.className = "upcoming-card-body";
        body.innerHTML = `
            <div class="time-pill">${flight.departure} • ${flight.arrival}</div>
            <div class="duration-pill">${flight.duration || "N/A"}</div>
        `;

        const meta = document.createElement("div");
        meta.className = "upcoming-meta";
        meta.innerHTML = `
            <span>${flight.airline || "AirBook Airways"}</span>
            <span>${flight.available_seats || 0} seats left</span>
        `;

        const bottom = document.createElement("div");
        bottom.className = "upcoming-bottom";
        bottom.innerHTML = `
            <span>${flight.flight_date || "Today"}</span>
            <strong>₹${Number(flight.price || 0).toLocaleString("en-IN")}</strong>
        `;

        card.appendChild(header);
        card.appendChild(body);
        card.appendChild(meta);
        card.appendChild(bottom);

        return card;
    }

    async function loadUpcomingFlights() {
        try {
            const response = await fetch("/api/upcoming-flights");

            if (!response.ok) {
                throw new Error("Failed to load flights");
            }

            const data = await response.json();

            const todayFlights = data.today || [];
            const tomorrowFlights = data.tomorrow || [];
            const fullSchedule = data.next_two_months || [];

            if (upcomingFlightsContainer) {
                const renderColumn = (title, flights) => {
                    const column = document.createElement("div");
                    column.className = "upcoming-column";

                    const heading = document.createElement("h3");
                    heading.textContent = title;
                    column.appendChild(heading);

                    if (!flights.length) {
                        const empty = document.createElement("p");
                        empty.className = "upcoming-empty";
                        empty.textContent = "No flights scheduled.";
                        column.appendChild(empty);
                        return column;
                    }

                    flights.forEach(flight => {
                        column.appendChild(createFlightCard(flight));
                    });

                    return column;
                };

                upcomingFlightsContainer.innerHTML = "";
                upcomingFlightsContainer.appendChild(renderColumn("Today", todayFlights));
                upcomingFlightsContainer.appendChild(renderColumn("Tomorrow", tomorrowFlights));
            }

            if (allUpcomingFlightsContainer) {
                allUpcomingFlightsContainer.innerHTML = "";

                if (!fullSchedule.length) {
                    allUpcomingFlightsContainer.innerHTML = '<div class="all-upcoming-empty">No flights are available in the next two months.</div>';
                    return;
                }

                const grouped = {};

                fullSchedule.forEach(flight => {
                    const date = flight.flight_date || "Unknown date";
                    if (!grouped[date]) grouped[date] = [];
                    grouped[date].push(flight);
                });

                Object.keys(grouped).forEach(date => {
                    const dateGroup = document.createElement("div");
                    dateGroup.className = "all-upcoming-date-group";

                    const heading = document.createElement("div");
                    heading.className = "all-upcoming-date-heading";
                    heading.textContent = new Date(`${date}T00:00:00`).toLocaleDateString("en-IN", {
                        weekday: "short",
                        day: "numeric",
                        month: "short",
                        year: "numeric"
                    });

                    const list = document.createElement("div");
                    list.className = "all-upcoming-date-list";

                    grouped[date].forEach(flight => {
                        const row = document.createElement("div");
                        row.className = "all-upcoming-row";

                        const left = document.createElement("div");
                        left.className = "all-upcoming-left";
                        left.innerHTML = `
                            <strong>${flight.from_code || flight.from}</strong>
                            <span>→</span>
                            <strong>${flight.to_code || flight.to}</strong>
                        `;

                        const middle = document.createElement("div");
                        middle.className = "all-upcoming-middle";
                        middle.innerHTML = `
                            <span>${flight.departure} - ${flight.arrival}</span>
                            <small>${flight.airline || "AirBook Airways"}</small>
                        `;

                        const right = document.createElement("div");
                        right.className = "all-upcoming-right";
                        right.innerHTML = `
                            <span>${flight.flight_number || "SK"}</span>
                            <strong>₹${Number(flight.price || 0).toLocaleString("en-IN")}</strong>
                        `;

                        row.appendChild(left);
                        row.appendChild(middle);
                        row.appendChild(right);
                        list.appendChild(row);
                    });

                    dateGroup.appendChild(heading);
                    dateGroup.appendChild(list);
                    allUpcomingFlightsContainer.appendChild(dateGroup);
                });
            }

        } catch (error) {
            console.error("Upcoming flights error:", error);
            if (upcomingFlightsContainer) {
                upcomingFlightsContainer.innerHTML = `
                    <div class="upcoming-column error">
                        <h3>Today</h3>
                        <p>Unable to load live flights right now.</p>
                    </div>
                    <div class="upcoming-column error">
                        <h3>Tomorrow</h3>
                        <p>Please refresh the page.</p>
                    </div>
                `;
            }

            if (allUpcomingFlightsContainer) {
                allUpcomingFlightsContainer.innerHTML = '<div class="all-upcoming-empty">Unable to load the full schedule right now.</div>';
            }
        }
    }

    loadUpcomingFlights();
    setInterval(loadUpcomingFlights, 30000);
});