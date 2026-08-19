document.addEventListener('DOMContentLoaded', () => {
    const recordBtn = document.getElementById('record-btn');
    const statusText = document.getElementById('status');
    const chatBox = document.getElementById('chat-box');
    const audioPlayer = document.getElementById('audio-player');

    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;

    // Helper to add a message bubble to the UI
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        chatBox.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Initialize MediaRecorder
    async function initAudio() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                audioChunks = [];
                await sendAudioToAPI(audioBlob);
            };
        } catch (err) {
            console.error("Microphone access denied:", err);
            statusText.textContent = "Microphone access denied";
            statusText.style.color = "#ef4444";
        }
    }

    async function sendAudioToAPI(audioBlob) {
        statusText.textContent = "Processing... ";
        
        const formData = new FormData();
        formData.append("audio", audioBlob, "recording.wav");

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                addMessage(data.error, "error");
                statusText.textContent = "Ready";
                return;
            }

            // Display user text and assistant text
            addMessage(data.user_text, "user");
            addMessage(data.assistant_text, "assistant");

            // Play the audio
            if (data.audio_url) {
                audioPlayer.src = data.audio_url + "?t=" + new Date().getTime();
                audioPlayer.play();
                statusText.textContent = "Speaking... ";
                
                audioPlayer.onended = () => {
                    statusText.textContent = "Ready";
                };
            } else {
                statusText.textContent = "Ready";
            }
            
        } catch (error) {
            console.error("API Error:", error);
            addMessage("Failed to communicate with the server.", "error");
            statusText.textContent = "Ready";
        }
    }

    // Toggle recording on click
    recordBtn.addEventListener('click', () => {
        if (!mediaRecorder) {
            alert("Please allow microphone access first.");
            return;
        }

        if (!isRecording) {
            // Start recording
            audioChunks = [];
            mediaRecorder.start();
            isRecording = true;
            recordBtn.classList.add('recording');
            statusText.textContent = "Listening... (Click to stop)";
        } else {
            // Stop recording
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.classList.remove('recording');
            statusText.textContent = "Sending audio...";
        }
    });

    // Request permissions on load
    initAudio();

    // PDF Upload Logic
    const pdfUploadInput = document.getElementById('pdf-upload');
    const uploadPdfBtn = document.getElementById('upload-pdf-btn');
    const pdfStatus = document.getElementById('pdf-status');

    uploadPdfBtn.addEventListener('click', async () => {
        const file = pdfUploadInput.files[0];
        if (!file) {
            alert("Please select a PDF file first.");
            return;
        }

        pdfStatus.textContent = "Uploading...";
        pdfStatus.style.color = "#a78bfa";
        uploadPdfBtn.disabled = true;

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch('/api/upload-pdf', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error("Upload failed");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                // Get the last line of the chunk for the most recent status
                const lines = chunk.trim().split('\n');
                if (lines.length > 0 && lines[lines.length - 1]) {
                     pdfStatus.textContent = lines[lines.length - 1];
                }
            }
            pdfStatus.style.color = "#10b981"; // green success
        } catch (error) {
            console.error(error);
            pdfStatus.textContent = "Error uploading PDF.";
            pdfStatus.style.color = "#ef4444";
        } finally {
            uploadPdfBtn.disabled = false;
        }
    });
});
