self.addEventListener("push", function (event) {
    if (!event.data) {
        console.log("Push event but no data");
        return;
    }

    const payload = event.data.json(); // Parse JSON data
    const title = payload.title || "Notification";
    const body = payload.body || "No message";
    const href = payload.href || "/"; // Ensure href is passed as data
    const icon = payload.icon || "https://crm.monarchbuildestate.com/static/assets/img/logo.png";
    const badge = payload.badge || "https://crm.monarchbuildestate.com/static/assets/img/logo.png";

    const options = {
        body: body,
        icon: icon,
        badge: badge,
        vibrate: [200, 100, 200], // Vibration pattern
        data: { href: href } // Store the URL inside data
    };

    event.waitUntil(self.registration.showNotification(title, options));
});

// Handle notification click event
self.addEventListener("notificationclick", function (event) {
    event.notification.close(); // Close the notification
    const href = event.notification.data?.href || "/"; // Retrieve href from data

    event.waitUntil(
        clients.openWindow(href) // Open homepage or a specific URL
    );
});
