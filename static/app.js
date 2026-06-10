const chatForm = document.querySelector("#chat-form");
const messageInput = document.querySelector("#message");
const messagesContainer = document.querySelector("#messages");

let sessionId = window.localStorage.getItem("tenerife-session-id");

const createMessage = (role, content, sources = []) => {
    const article = document.createElement("article");
    article.className = `message message--${role}`;

    const roleLabel = document.createElement("p");
    roleLabel.className = "message__role";
    roleLabel.textContent = role === "user" ? "Tú" : "Asistente";
    article.appendChild(roleLabel);

    const text = document.createElement("p");
    text.textContent = content;
    article.appendChild(text);

    if (sources.length > 0) {
        const sourcesBlock = document.createElement("p");
        sourcesBlock.className = "message__sources";
        sourcesBlock.textContent = `Fuentes: ${sources.map((source) => `${source.source} p.${source.page ?? "?"} ch.${source.chunk_id ?? "?"}`).join(" | ")}`;
        article.appendChild(sourcesBlock);
    }

    messagesContainer.appendChild(article);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
};

const parseResponsePayload = async (response) => {
    const contentType = response.headers.get("content-type") || "";

    if (contentType.includes("application/json")) {
        return response.json();
    }

    const text = await response.text();
    return {
        detail: text || "No se pudo completar la consulta.",
    };
};

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = messageInput.value.trim();
    if (!message) {
        return;
    }

    createMessage("user", message);
    messageInput.value = "";

    const button = chatForm.querySelector("button");
    button.disabled = true;

    try {
        const response = await fetch("/api/v1/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
            }),
        });

        const payload = await parseResponsePayload(response);
        if (!response.ok) {
            throw new Error(payload.detail || "No se pudo completar la consulta.");
        }

        sessionId = payload.session_id;
        window.localStorage.setItem("tenerife-session-id", sessionId);
        createMessage("assistant", payload.answer, payload.sources || []);
    } catch (error) {
        createMessage("assistant", error.message || "Ha ocurrido un error inesperado.");
    } finally {
        button.disabled = false;
    }
});
