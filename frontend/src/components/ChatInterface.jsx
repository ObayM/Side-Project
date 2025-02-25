import { useState, useRef, useEffect } from "react";
import { Mic, Send, Loader2, Bot, User, Sparkles } from "lucide-react";
import Groq from 'groq-sdk';

const groq = new Groq({
  apiKey: "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",
  dangerouslyAllowBrowser: true
});

const loadingPhrases = [
  "Analyzing your request...",
  "Processing thoughts...",
  "Connecting neural pathways...",
  "Generating response...",
  "Computing possibilities...",
  "Synthesizing information...",
  "Calibrating response...",
  "Understanding context...",
];

const BASE_URL = "https://8000-idx-side-project-1740065276139.cluster-rz2e7e5f5ff7owzufqhsecxujc.cloudworkstations.dev/"

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([
    { role: "ai", content: "Hello! How can I help you today?" },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [loadingPhrase, setLoadingPhrase] = useState(loadingPhrases[0]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    let interval;
    if (isLoading) {
      let index = 0;
      interval = setInterval(() => {
        index = (index + 1) % loadingPhrases.length;
        setLoadingPhrase(loadingPhrases[index]);
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isLoading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Audio recording permission request
  const requestMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      return stream;
    } catch (error) {
      console.error("Microphone permission denied:", error);
      alert("Please allow microphone access to use voice input");
      return null;
    }
  };

  // Transcribe recorded audio using Groq API
  const transcribeAudio = async (audioBlob) => {
    try {
      // Add user's audio message to the chat
      const userMessage = { role: "user", content: "🎤 Voice message..." };
      setMessages(prev => [...prev, userMessage]);
      setIsLoading(true);
      
      // Use the Groq transcription service
      const file = new File([audioBlob], 'audiofile.wav', { type: audioBlob.type });
      
      const transcription = await groq.audio.transcriptions.create({
        file: file,
        model: 'whisper-large-v3-turbo',
        language: 'ar',
      });
      
      const transcribedText = transcription.text;
      
      // Update the user message with transcribed text
      setMessages(prev => prev.map((msg, idx) => 
        idx === prev.length - 1 ? { ...msg, content: transcribedText } : msg
      ));
      
      // Now process the transcribed text with the router
      await processMessage(transcribedText);
      
    } catch (error) {
      console.error("Error transcribing audio:", error);
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: "Sorry, I couldn't process your voice message. Please try again or type your message instead." 
      }]);
      setIsLoading(false);
    }
  };

  // Start recording audio
  const startRecording = async () => {
    audioChunksRef.current = [];
    const stream = await requestMicrophonePermission();
    
    if (!stream) return;
    
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.current = mediaRecorder;
    
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };
    
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      await transcribeAudio(audioBlob);
      
      // Stop all tracks in the stream to release the microphone
      stream.getTracks().forEach(track => track.stop());
    };
    
    mediaRecorder.start();
    setIsRecording(true);
  };

  // Stop recording audio
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Process message (for both text and transcribed audio)
  const processMessage = async (text) => {
    try {
      const response = await fetch(`${BASE_URL}router/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          "query": text
        }),
      });

      const data = await response.json();
      const parsedData = JSON.parse(data);
      const aiMessage = { role: "ai", content: parsedData.Message };
      setMessages(prev => [...prev, aiMessage]);

      const executeResponse = await fetch(`${BASE_URL}execute/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(
          { command: parsedData.Routing.Action,
            details: parsedData.Routing.Details, 
          }

        ),
        });
        if (parsedData.Routing.Action === "Filesharing") {
          const executeData = await executeResponse.json();
          const aiMessage = { role: "ai", content: executeData };
          setMessages(prev => [...prev, aiMessage]);
        
        }
    } catch (error) {
      console.error("Error processing message:", error);
      setMessages(prev => [...prev, { 
        role: "ai", 
        content: "Sorry, I encountered an error processing your request. Please try again." 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage = { role: "user", content: message };
    setMessages(prev => [...prev, userMessage]);
    setMessage("");
    setIsLoading(true);
    inputRef.current?.focus();

    await processMessage(message);
  };

  const handleMic = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <div className="w-full bg-gray-800/30 backdrop-blur-xl border-b border-gray-700/50 p-4 fixed top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <Bot className="w-6 h-6 text-cyan-500" />
          <h1 className="text-xl font-semibold text-white tracking-wide">AI Assistant</h1>
          <div className="ml-auto flex items-center gap-2">
            <span className="animate-pulse">
              <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
            </span>
            <span className="text-sm text-gray-400">Online</span>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto pb-32 pt-20 scroll-smooth">
        <div className="max-w-3xl mx-auto px-4 space-y-6">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex gap-4 transform transition-all duration-500 ease-out ${
                msg.role === "ai" ? "fade-in-left" : "fade-in-right"
              }`}
              style={{
                animationDelay: `${index * 0.1}s`
              }}
            >
              <div
                className={`group flex gap-4 w-full ${
                  msg.role === "ai" ? "justify-start" : "justify-end"
                }`}
              >
                {msg.role === "ai" && (
                  <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-cyan-500" />
                  </div>
                )}
                <div
                  className={`px-6 py-3 rounded-2xl max-w-[80%] transition-all duration-300 shadow-lg ${
                    msg.role === "ai"
                      ? "bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 text-gray-100 hover:bg-gray-800"
                      : "bg-gradient-to-r from-cyan-600 to-cyan-500 text-white hover:from-cyan-700 hover:to-cyan-600"
                  }`}
                >
                  <p className="leading-relaxed">{msg.content}</p>
                </div>
                {msg.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-4 animate-fade-in">
              <div className="w-8 h-8 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center">
                <Bot className="w-5 h-5 text-cyan-500" />
              </div>
              <div className="px-6 py-3 rounded-2xl bg-gray-800/80 backdrop-blur-sm border border-gray-700/50 text-gray-100">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-5 h-5 animate-spin text-cyan-500" />
                  <span className="text-gray-300 transition-all duration-500">{loadingPhrase}</span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="fixed bottom-0 w-full bg-gray-800/30 backdrop-blur-xl border-t border-gray-700/50 p-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-3 items-center">
            <button
              onClick={handleMic}
              className={`p-3 rounded-xl transition-all duration-300 transform hover:scale-105 ${
                isRecording
                  ? "bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700"
                  : "bg-gray-700 hover:bg-gray-600"
              }`}
              aria-label={isRecording ? "Stop recording" : "Start recording"}
            >
              <Mic className={`w-5 h-5 ${
                isRecording ? "animate-pulse text-white" : "text-gray-300"
              }`} />
            </button>
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                type="text"
                value={message}
                onChange={e => setMessage(e.target.value)}
                onKeyPress={e => e.key === "Enter" && handleSend()}
                placeholder="Type your message..."
                className="w-full rounded-xl border border-gray-700/50 bg-gray-900/50 backdrop-blur-sm px-6 py-3 text-gray-100 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent placeholder-gray-400 transition-all duration-300"
                disabled={isRecording}
              />
              {message.length > 0 && (
                <Sparkles className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-cyan-500 animate-pulse" />
              )}
            </div>
            <button
              onClick={handleSend}
              disabled={isLoading || !message.trim() || isRecording}
              className="bg-gradient-to-r from-cyan-600 to-cyan-500 text-white p-3 rounded-xl hover:from-cyan-700 hover:to-cyan-600 transition-all duration-300 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed transform hover:scale-105 disabled:hover:scale-100 group"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5 transition-transform group-hover:translate-x-1" />
              )}
            </button>
          </div>
          {isRecording && (
            <div className="mt-2 flex items-center justify-center">
              <div className="text-cyan-500 text-sm flex items-center gap-2">
                <span className="inline-block w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
                Recording... Click the microphone icon again to stop
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx global>{`
        @keyframes fade-in-left {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        @keyframes fade-in-right {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        .fade-in-left {
          animation: fade-in-left 0.5s ease-out forwards;
        }
        
        .fade-in-right {
          animation: fade-in-right 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
}