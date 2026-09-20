setTimeout(() => {
    const messages = document.querySelectorAll(".flash-message");

    messages.forEach(message => {
        message.style.opacity = "0";

        setTimeout(() => {
            message.remove();
        }, 300);
    });
}, 2000);