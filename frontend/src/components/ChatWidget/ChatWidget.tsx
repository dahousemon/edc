import { useState, useRef, useEffect } from 'react'
import { Send, ThumbsUp, ThumbsDown, X, Minimize2, Maximize2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import clsx from 'clsx'
import { chatApi, ChatMessage, Source } from '../../services/api'

interface ChatWidgetProps {
  embedded?: boolean
  onClose?: () => void
}

export default function ChatWidget({ embedded = false, onClose }: ChatWidgetProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isMinimized, setIsMinimized] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Initial greeting
  useEffect(() => {
    setMessages([
      {
        id: 'greeting',
        role: 'assistant',
        content: `# Welcome to Aurora EDC!

I'm your AI Business Navigator, here to help you explore opportunities in Aurora, Colorado.

I can help you with:
- **Site Selection** - Find the perfect location for your business
- **Incentives** - Learn about tax credits and development programs
- **Permits & Licensing** - Navigate requirements for your business type
- **Workforce & Demographics** - Understand our talent pool
- **Properties** - Search available commercial and industrial spaces

How can I help you today?`,
        timestamp: new Date().toISOString(),
      },
    ])
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await chatApi.sendMessage(input.trim(), conversationId || undefined)

      if (!conversationId) {
        setConversationId(response.conversation_id)
      }

      const assistantMessage: ChatMessage = {
        id: response.message_id,
        role: 'assistant',
        content: response.message,
        timestamp: new Date().toISOString(),
        sources: response.sources,
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: "I apologize, but I'm having trouble connecting right now. Please try again in a moment, or contact Aurora EDC directly at (303) 739-7700.",
          timestamp: new Date().toISOString(),
        },
      ])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleFeedback = async (messageId: string, feedback: 'thumbs_up' | 'thumbs_down') => {
    try {
      await chatApi.submitFeedback(messageId, feedback)
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === messageId ? { ...msg, feedback } : msg
        )
      )
    } catch (error) {
      console.error('Error submitting feedback:', error)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (isMinimized) {
    return (
      <button
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-aurora-600 hover:bg-aurora-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:scale-105"
      >
        <Maximize2 className="w-6 h-6" />
      </button>
    )
  }

  return (
    <div
      className={clsx(
        'flex flex-col bg-white',
        embedded
          ? 'h-full rounded-xl shadow-xl border border-gray-200'
          : 'fixed bottom-6 right-6 w-[420px] h-[600px] rounded-xl shadow-2xl border border-gray-200 z-50'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-aurora-600 text-white rounded-t-xl">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <span className="font-semibold">A</span>
          </div>
          <div>
            <h3 className="font-semibold">Aurora EDC Navigator</h3>
            <p className="text-xs text-aurora-100">AI Business Assistant</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(true)}
            className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
          >
            <Minimize2 className="w-4 h-4" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {messages.map((message) => (
          <div
            key={message.id}
            className={clsx(
              'message-enter',
              message.role === 'user' ? 'flex justify-end' : ''
            )}
          >
            <div
              className={clsx(
                'max-w-[85%] rounded-2xl px-4 py-3',
                message.role === 'user'
                  ? 'bg-aurora-600 text-white rounded-br-md'
                  : 'bg-gray-100 text-gray-900 rounded-bl-md'
              )}
            >
              {message.role === 'assistant' ? (
                <div className="markdown-content">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
              ) : (
                <p>{message.content}</p>
              )}

              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-200">
                  <p className="text-xs text-gray-500 mb-1">Sources:</p>
                  <div className="flex flex-wrap gap-1">
                    {message.sources.map((source, i) => (
                      <span
                        key={i}
                        className="text-xs bg-gray-200 text-gray-600 px-2 py-0.5 rounded"
                      >
                        {source.title}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Feedback buttons */}
              {message.role === 'assistant' && message.id !== 'greeting' && (
                <div className="mt-2 flex items-center gap-2">
                  <button
                    onClick={() => handleFeedback(message.id, 'thumbs_up')}
                    className={clsx(
                      'p-1 rounded transition-colors',
                      message.feedback === 'thumbs_up'
                        ? 'text-green-600 bg-green-50'
                        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-200'
                    )}
                  >
                    <ThumbsUp className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleFeedback(message.id, 'thumbs_down')}
                    className={clsx(
                      'p-1 rounded transition-colors',
                      message.feedback === 'thumbs_down'
                        ? 'text-red-600 bg-red-50'
                        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-200'
                    )}
                  >
                    <ThumbsDown className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isLoading && (
          <div className="flex items-center gap-1 text-gray-400 px-4 py-2">
            <div className="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
            <div className="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
            <div className="typing-dot w-2 h-2 bg-gray-400 rounded-full"></div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Aurora business opportunities..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-aurora-500 focus:border-transparent"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-2.5 bg-aurora-600 text-white rounded-full hover:bg-aurora-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Powered by Aurora Economic Development Council
        </p>
      </div>
    </div>
  )
}
