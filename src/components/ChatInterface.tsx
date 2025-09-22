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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Add welcome message on mount
  useEffect(() => {
    const welcomeMessage: Message = {
      id: 'welcome',
      message: `🌊 **Welcome to the Oceanographic Data Assistant!**

I can help you explore oceanographic data using natural language queries. Here are some examples:

• "Show me temperature profiles from platform 5906468"
• "Find salinity measurements in the Pacific Ocean from 2023"
• "Get recent profiles near latitude 35, longitude -120"
• "Show me data from the Mediterranean Sea"

Just ask your question in plain English, and I'll convert it to SQL and fetch the data for you!`,
      message_type: 'system',
      timestamp: Date.now().toString()
    };
    setMessages([welcomeMessage]);
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      message: input,
      message_type: 'user',
      timestamp: Date.now().toString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: input,
          conversation_id: conversationId || undefined
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Update conversation ID if new
      if (data.conversation_id && !conversationId) {
        setConversationId(data.conversation_id);
      }

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: data.response,
        message_type: data.message_type,
        timestamp: Date.now().toString(),
        sql_query: data.sql_query,
        data: data.data
      };

      setMessages(prev => [...prev, botMessage]);

      // Show toast for successful queries
      if (data.message_type === 'bot' && data.data && data.data.length > 0) {
        toast({
          title: "Query Successful",
          description: `Found ${data.data.length} records`,
        });
      }

    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        message: `❌ **Connection Error:** Unable to connect to the server. Please make sure the backend is running on port 8000.\n\n**Error details:** ${error instanceof Error ? error.message : 'Unknown error'}`,
        message_type: 'error',
        timestamp: Date.now().toString()
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

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationId('');
    // Re-add welcome message
    const welcomeMessage: Message = {
      id: 'welcome-new',
      message: `🌊 **Chat cleared!** 

Feel free to ask me anything about the oceanographic data. I'm here to help you explore temperature, salinity, and pressure measurements from ocean floats worldwide.`,
      message_type: 'system',
      timestamp: Date.now().toString()
    };
    setMessages([welcomeMessage]);
  };

  return (
    <div className={`flex flex-col h-full bg-gradient-to-br from-background to-secondary/30 ${className}`}>
      <ChatHeader onClearChat={clearChat} />
      
      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className="space-y-3">
            <ChatMessage message={message} />
            
            {/* Data Table */}
            {message.data && message.data.length > 0 && (
              <Card className="p-4 border-l-4 border-accent">
                <div className="flex items-center gap-2 mb-3">
                  <Database className="h-4 w-4 text-accent" />
                  <span className="font-medium text-sm">Query Results ({message.data.length} records)</span>
                </div>
                <DataTable data={message.data} />
              </Card>
            )}
          </div>
        ))}
        
        {/* Loading Message */}
        {isLoading && (
          <div className="flex justify-start">
            <Card className="max-w-[80%] p-4 chat-message-bot">
              <div className="flex items-center gap-2">
                <Waves className="h-4 w-4 animate-pulse text-accent" />
                <span>Processing your query</span>
                <div className="typing-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </Card>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t bg-card/50 p-4">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about oceanographic data... (e.g., 'Show me temperature data from the Atlantic Ocean')"
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