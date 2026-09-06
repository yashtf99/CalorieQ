import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { useAuthStore } from '@/store/authStore'
import axios from 'axios'
import { toast } from 'sonner'
import { Send, Loader2, X, MessageCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export default function FloatingChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const accessToken = useAuthStore((state) => state.accessToken)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  if (!accessToken) {
    return null
  }

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
    }

    setMessages((prev) => [...prev, userMessage])
    const userInput = input
    setInput('')
    setIsLoading(true)

    try {
      const response = await axios.post(
        '/api/v1/chat/message',
        {
          message: userInput,
        },
        {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        },
      )

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.response,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setSessionId(response.data.session_id)
    } catch (error) {
      console.error('Chat error:', error)
      if (axios.isAxiosError(error)) {
        console.error('Response data:', error.response?.data)
        console.error('Status:', error.response?.status)
      }
      toast.error('Failed to send message')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="fixed bottom-8 right-8 z-50">
      {isOpen ? (
        <Card className="w-96 h-[500px] shadow-xl flex flex-col bg-card border border-border rounded-lg overflow-hidden">
          {/* Header */}
          <div
            className="p-4 flex justify-between items-start text-card-foreground"
            style={{ backgroundColor: 'var(--color-primary)', color: 'var(--color-primary-foreground)' }}
          >
            <div className="flex-1">
              <h3 className="font-semibold text-sm">CalorieQ Assistant</h3>
              <p className="text-xs opacity-90 mt-1">Log meals, check your goals, and review your nutrition — just type naturally.</p>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded hover:opacity-80 transition-opacity flex-shrink-0 ml-2"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-background">
            {messages.length === 0 ? (
              <div className="text-center text-muted-foreground text-sm mt-12 px-2">
                <p className="text-xs">Start by asking about your meals, goals, or nutrition.</p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs px-3 py-2 rounded-lg text-sm ${
                      msg.role === 'user'
                        ? 'text-primary-foreground'
                        : 'text-foreground bg-muted'
                    }`}
                    style={
                      msg.role === 'user'
                        ? { backgroundColor: 'var(--color-primary)' }
                        : {}
                    }
                  >
                    {msg.role === 'user' ? (
                      msg.content
                    ) : (
                      <ReactMarkdown
                        components={{
                          p: ({ children }) => <p className="mb-2">{children}</p>,
                          ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                          li: ({ children }) => <li className="ml-2">{children}</li>,
                          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                          em: ({ children }) => <em className="italic">{children}</em>,
                          code: ({ children }) => <code className="bg-opacity-20 px-1 rounded">{children}</code>,
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-muted text-foreground px-3 py-2 rounded-lg">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-border p-3 flex gap-2 bg-muted/30">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask anything..."
              disabled={isLoading}
              className="text-sm"
            />
            <Button
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              variant="default"
              size="icon-sm"
            >
              {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Send className="h-3 w-3" />}
            </Button>
          </div>
        </Card>
      ) : (
        <button
          onClick={() => setIsOpen(true)}
          className="rounded-full p-4 shadow-lg hover:shadow-xl transition-all text-primary-foreground"
          style={{
            backgroundColor: 'var(--color-primary)',
          }}
        >
          <MessageCircle size={24} />
        </button>
      )}
    </div>
  )
}
