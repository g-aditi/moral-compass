const textarea = document.getElementById("user-message");

textarea.addEventListener("input", function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + "px";
});


function sendMessage() {
    const message = document.getElementById("user-message").value;
    const chatBox = document.getElementById("chat-box");
    
    const userMessageDiv = document.createElement("div");
    userMessageDiv.textContent = "You: " + message;
    chatBox.appendChild(userMessageDiv);

    fetch("/chat/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        const botMessageDiv = document.createElement("div");
        botMessageDiv.textContent = "Bot: " + data.response;
        chatBox.appendChild(botMessageDiv);
    });

    document.getElementById("user-message").value = "";

    const textarea = document.getElementById('user-message');
    textarea.value = ''; 
    textarea.style.height = 'auto'; 
    textarea.style.height = '6.8vh';
}