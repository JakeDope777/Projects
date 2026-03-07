import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Trash2, Bot, UserCircle } from 'lucide-react';
import { chatService } from '../services/api';
import type { ChatMessage } from '../types';
import ReactMarkdown from 'react-markdown';

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await chatService.sendMessage({
        message: text,
        conversation_id: conversationId,
      });
      setConversationId(response.conversation_id);

      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toISOString(),
        module_used: response.module_used,
        tokens_used: response.tokens_used,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please check that the backend is running and try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    if (conversationId) {
      chatService.clearConversation(conversationId).catch(() => {});
    }
    setMessages([]);
    setConversationId(undefined);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">AI Marketing Assistant</h2>
          <p className="text-sm text-gray-500">
            Ask about market research, campaigns, analytics, creative content, and more.
          </p>
        </div>
        {messages.length > 0 && (
          <button onClick={clearChat} className="btn-secondary flex items-center gap-2 text-sm">
            <Trash2 className="w-4 h-4" /> Clear
          </button>
        )}
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400">
            <Bot className="w-16 h-16 mb-4 text-primary-300" />
            <p className="text-lg font-medium text-gray-600">How can I help with your marketing today?</p>
            <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
              {[
                'Do a SWOT analysis for our SaaS product',
                'Write a LinkedIn post about AI trends',
                'Show me dashboard metrics',
                'Create a welcome email campaign',
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="text-left px-4 py-3 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 hover:border-primary-300 hover:bg-primary-50 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message-enter flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                <Bot className="w-4 h-4 text-primary-600" />
              </div>
            )}
            <div
              className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-md'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-md'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              ) : (
                msg.content
              )}
              {msg.module_used && (
                <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-400">
                  Module: {msg.module_used}
                  {msg.tokens_used ? ` · ${msg.tokens_used} tokens` : ''}
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0">
                <UserCircle className="w-4 h-4 text-gray-600" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 chat-message-enter">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-primary-600" />
            </div>
            <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-bl-md">
              <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 pt-4">
        <div className="flex gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            className="input-field resize-none"
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="btn-primary flex items-center gap-2 px-5"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
