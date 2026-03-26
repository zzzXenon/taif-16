import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

// Generate UUID for session
const generateUUID = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'bot',
      content: 'Halo! Saya AiYukToba, asisten wisata daerah Toba. Apa yang ingin Anda ketahui hari ini?',
      source_documents: [],
      standalone_query: null
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(generateUUID());

  const [ablationMode, setAblationMode] = useState('proposed'); // modes: proposed, pipeline_a_only, pipeline_b_only
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: input
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMsg.content,
          ablation_mode: ablationMode
        })
      });

      if (!response.ok) {
        throw new Error('API Error');
      }

      const data = await response.json();

      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'bot',
        content: data.reply,
        source_documents: data.source_documents,
        standalone_query: data.standalone_query
      }]);

    } catch (error) {
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'bot',
        content: `**Error**: Gagal terhubung ke API backend. Pastikan server FastAPI di \`http://127.0.0.1:8000\` sudah berjalan.\n\nDetail: ${error.message}`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">✨</span>
          <span>AiYukToba</span>
        </div>

        <div className="glass-panel">
          <div className="control-group">
            <h3 className="control-label">Run options</h3>

            <label className={`radio-option ${ablationMode === 'proposed' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ablationMode"
                value="proposed"
                checked={ablationMode === 'proposed'}
                onChange={(e) => setAblationMode(e.target.value)}
              />
              <div className="radio-custom"></div>
              <div className="radio-text">Pipeline A + B</div>
            </label>

            <label className={`radio-option ${ablationMode === 'pipeline_a_only' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ablationMode"
                value="pipeline_a_only"
                checked={ablationMode === 'pipeline_a_only'}
                onChange={(e) => setAblationMode(e.target.value)}
              />
              <div className="radio-custom"></div>
              <div className="radio-text">Pipeline A</div>
            </label>

            <label className={`radio-option ${ablationMode === 'pipeline_b_only' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ablationMode"
                value="pipeline_b_only"
                checked={ablationMode === 'pipeline_b_only'}
                onChange={(e) => setAblationMode(e.target.value)}
              />
              <div className="radio-custom"></div>
              <div className="radio-text">Pipeline B</div>
            </label>

            <label className={`radio-option ${ablationMode === 'baseline' ? 'selected' : ''}`}>
              <input
                type="radio"
                name="ablationMode"
                value="baseline"
                checked={ablationMode === 'baseline'}
                onChange={(e) => setAblationMode(e.target.value)}
              />
              <div className="radio-custom"></div>
              <div className="radio-text">Baseline</div>
            </label>
          </div>
        </div>

        <div style={{ marginTop: 'auto', fontSize: '0.8rem', color: '#64748b' }}>
          <p>Prototype</p>
          <p>Session ID: <br /><span style={{ fontFamily: 'monospace' }}>{sessionId}</span></p>
        </div>
      </aside>

      <main className="main-chat">
        <div className="chat-messages">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.role}`}>
              <div className="message-bubble">
                <div className="markdown-body">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>

                {msg.role === 'bot' && (msg.standalone_query || (msg.source_documents && msg.source_documents.length > 0)) && (
                  <div className="bot-metadata">
                    {msg.standalone_query && (
                      <div className="bot-metadata-title">
                        <span className="badge">CQR Engine</span>
                        <span>"{msg.standalone_query}"</span>
                      </div>
                    )}

                    {msg.source_documents && msg.source_documents.length > 0 && (
                      <div style={{ marginTop: '0.75rem' }}>
                        <div className="bot-metadata-title"><span className="badge">Retrieval</span> Referensi:</div>
                        {msg.source_documents.map((doc, idx) => (
                          <div key={idx} className="source-item">
                            {doc}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message-wrapper bot">
              <div className="message-bubble" style={{ padding: '1rem' }}>
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <form className="input-container" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-input"
              placeholder="Tanya rekomendasi wisata Danau Toba..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isLoading}
            />
            <button type="submit" className="send-button" disabled={!input.trim() || isLoading}>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;
