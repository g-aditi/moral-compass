const textarea = document.getElementById("user-message");

textarea.addEventListener("input", function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + "px";
});

function sendMessage() {
    const message = document.getElementById("user-message").value;
    const chatBox = document.getElementById("chat-box");

    const userMessageDiv = document.createElement("div");
    userMessageDiv.textContent = message;

    userMessageDiv.style.backgroundColor = "#d3d3d3";
    userMessageDiv.style.padding = "0.8vw";
    userMessageDiv.style.marginBottom = "2vh";
    userMessageDiv.style.borderRadius = "1.2vw";
    userMessageDiv.style.maxWidth = "30vw";
    userMessageDiv.style.wordWrap = "break-word";
    userMessageDiv.style.textAlign = "left";
    userMessageDiv.style.marginLeft = "40vw";

    chatBox.appendChild(userMessageDiv);

    // Send the message to the server (bot response handling)
    fetch("/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.textContent = "Bot: " + data.response;

        botMessageDiv.style.backgroundColor = "#f1f1f1";
        botMessageDiv.style.padding = "10px";
        botMessageDiv.style.marginBottom = "10px";
        botMessageDiv.style.borderRadius = "8px";
        botMessageDiv.style.maxWidth = "50vw";
        botMessageDiv.style.wordWrap = "break-word";
        botMessageDiv.style.textAlign = "left";

        chatBox.appendChild(botMessageDiv);
    });

    const textarea = document.getElementById('user-message');
    textarea.value = ''; 
    textarea.style.height = 'auto'; 
    textarea.style.height = '6.8vh';
}

