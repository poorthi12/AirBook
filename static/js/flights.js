// ==========================================
// SKYBOOK FLIGHT NOTIFICATION
// ==========================================

document.addEventListener("DOMContentLoaded", function () {

    const notification =
        document.getElementById("flightNotification");

    if (!notification) {
        return;
    }

    // Show notification after page loads
    setTimeout(function () {

        notification.classList.add("notification-visible");

    }, 100);


    // Automatically hide after 3 seconds
    setTimeout(function () {

        closeFlightNotification();

    }, 3000);

});


// ==========================================
// CLOSE NOTIFICATION
// ==========================================

function closeFlightNotification() {

    const notification =
        document.getElementById("flightNotification");

    if (!notification) {
        return;
    }

    // Slide notification back up
    notification.classList.remove("notification-visible");


    // Remove completely after animation
    setTimeout(function () {

        notification.remove();

    }, 500);

}