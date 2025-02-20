import { useState, useRef, useEffect } from "react";
import { Mic, Send, Loader2, Bot, User, Sparkles } from "lucide-react";

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

  const handleSend = async () => {
    if (!message.trim()) return;

    const userMessage = { role: "user", content: message };
    setMessages(prev => [...prev, userMessage]);
    setMessage("");
    setIsLoading(true);
    inputRef.current?.focus();

    try {
      const response = await fetch("http://127.0.0.1:8000/router/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          "query": message
        }),
      });

      const data = await response.json();
      const parsedData = JSON.parse(data);
      const aiMessage = { role: "ai", content: parsedData.Message };
      setMessages(prev => [...prev, aiMessage]);
      await fetch(`http://127.0.0.1:8000/text-to-speech/?text=${parsedData.Message}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      await fetch("http://127.0.0.1:8000/excute/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ command: parsedData.Routing.Details }),
      });
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMic = async () => {
    setIsRecording(!isRecording);
    try{
      const stt = await fetch("http://127.0.0.1:8000/speech-to-text/")
      try {
        const response = await fetch("http://127.0.0.1:8000/router/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            "query": stt
          }),
        });
  
        const data = await response.json();
        const parsedData = JSON.parse(data);
        const aiMessage = { role: "ai", content: parsedData.Message };
        setMessages(prev => [...prev, aiMessage]);
        await fetch(`http://127.0.0.1:8000/text-to-speech/?text=${parsedData.Message}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });
  
        await fetch("http://127.0.0.1:8000/excute/", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ command: parsedData.Routing.Details }),
        });
      } catch (error) {
        console.error("Error:", error);
      } finally {
        setIsLoading(false);
      }
    }
     catch (error){
      console.log(error)
    } finally {
      setIsRecording(!isRecording)
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
              />
              {message.length > 0 && (
                <Sparkles className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-cyan-500 animate-pulse" />
              )}
            </div>
            <button
              onClick={handleSend}
              disabled={isLoading || !message.trim()}
              className="bg-gradient-to-r from-cyan-600 to-cyan-500 text-white p-3 rounded-xl hover:from-cyan-700 hover:to-cyan-600 transition-all duration-300 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed transform hover:scale-105 disabled:hover:scale-100 group"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5 transition-transform group-hover:translate-x-1" />
              )}
            </button>
          </div>
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