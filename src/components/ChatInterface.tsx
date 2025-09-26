import React, { useState, useRef, useEffect } from 'react';
import { Send, Database, Waves, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import ChatMessage from './ChatMessage';
import ChatHeader from './ChatHeader';
import DataTable from './DataTable';

interface Message {
  id: string;
  message: string;
  message_type: 'user' | 'bot' | 'system' | 'error';
  timestamp: string;
  sql_query?: string;
  data?: any[];
  clarification_needed?: boolean;
}

interface ChatInterfaceProps {
  className?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '' }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(scrollToBottom, [messages]);

  // Welcome message
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      message: `🌊 **Welcome to the Oceanographic Data Assistant!**\n\nI can help you explore oceanographic data using natural language queries.`,
      message_type: 'system',
      timestamp: Date.now().toString(),
    };
    setMessages([welcomeMessage]);
  }, []);

  // ----------------- API -----------------
  const sendQuery = async (question: string, override = false, sql?: string) => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          conversation_id: conversationId || undefined,
          override,
          sql_query: sql,
        }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();

      if (data.conversation_id && !conversationId) setConversationId(data.conversation_id);

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: data.response,
        message_type: data.message_type,
        timestamp: Date.now().toString(),
        sql_query: data.sql_query,
        data: data.data,
        clarification_needed: data.clarification_needed,
      };

      setMessages(prev => [...prev, botMessage]);

      if (data.message_type === 'bot' && data.data?.length) {
        toast({ title: "Query Successful", description: `Found ${data.data.length} records` });
      }
    } catch (error) {
      console.error(error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: `❌ Connection Error: ${(error as Error).message}`,
        message_type: 'error',
        timestamp: Date.now().toString(),
      };
      setMessages(prev => [...prev, errorMessage]);
      toast({
        title: "Connection Error",
        description: "Unable to connect to the server",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage: Message = {
      id: Date.now().toString(),
      message: input,
      message_type: 'user',
      timestamp: Date.now().toString(),
    };
    setMessages(prev => [...prev, userMessage]);
    const question = input;
    setInput('');
    await sendQuery(question);
  };

  // ✅ Run Anyway should use the last generated SQL
  const handleRunAnyway = async (message: Message) => {
    await sendQuery(
      message.message,       // original natural language question
      true,                  // override flag
      message.sql_query      // use the SQL the model generated
    );
  };

  // ✅ Refine Query should recall the last USER query
  const handleRefine = (message: Message) => {
    const lastUserMessage = [...messages].reverse().find(m => m.message_type === 'user');
    if (lastUserMessage) {
      setInput(lastUserMessage.message);  // prefill user query for editing
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId('');
    const welcomeMessage: Message = {
      id: 'welcome-new',
      message: `🌊 Chat cleared! Feel free to ask me anything about oceanographic data.`,
      message_type: 'system',
      timestamp: Date.now().toString(),
    };
    setMessages([welcomeMessage]);
  };

  return (
    <div className={`flex flex-col h-full bg-gradient-to-br from-background to-secondary/30 ${className}`}>
      <ChatHeader onClearChat={clearChat} />

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className="space-y-3">
            <ChatMessage
              message={msg}
              onRunAnyway={handleRunAnyway}
              onRefine={handleRefine}
            />
            {msg.data?.length > 0 && (
              <Card className="p-4 border-l-4 border-accent">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="h-4 w-4 text-accent" />
                  <span className="font-medium text-sm">
                    Query Results ({msg.data.length} records)
                  </span>
                </div>
                <DataTable data={msg.data} />
              </Card>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <Card className="max-w-[80%] p-4 chat-message-bot">
              <div className="flex items-center gap-2">
                <Waves className="h-4 w-4 animate-pulse text-accent" />
                <span>Processing your query</span>
                <div className="typing-dots"><span></span><span></span><span></span></div>
              </div>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t bg-card/50 p-4">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <Input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about oceanographic data..."
              disabled={isLoading}
              className="pr-20 bg-background/80 backdrop-blur-sm border-border/50 focus:border-accent"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <MessageSquare className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>
          <Button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            size="default"
            className="px-6 smooth-transition hover:shadow-lg"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex justify-center mt-2">
          <p className="text-xs text-muted-foreground">
            Powered by Gemini AI • Connected to Neon PostgreSQL • Vector search via Qdrant
          </p>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
