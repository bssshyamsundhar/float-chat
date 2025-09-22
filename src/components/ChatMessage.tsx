import React from 'react';
import { User, Bot, AlertCircle, Info, Copy, Check } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { useState } from 'react';

interface Message {
  id: string;
  message: string;
  message_type: 'user' | 'bot' | 'system' | 'error';
  timestamp: string;
  sql_query?: string;
  data?: any[];
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copiedSql, setCopiedSql] = useState(false);
  const { toast } = useToast();

  const formatMessage = (text: string) => {
    // Convert markdown-style formatting to JSX
    const parts = text.split(/(\*\*.*?\*\*|`.*?`|```[\s\S]*?```)/);
    
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className="font-semibold">{part.slice(2, -2)}</strong>;
      } else if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3);
        const language = code.split('\n')[0];
        const codeContent = language ? code.substring(language.length + 1) : code;
        
        return (
          <div key={index} className="code-block my-2 relative group">
            {language && (
              <div className="text-xs text-muted-foreground mb-2 uppercase tracking-wide">
                {language}
              </div>
            )}
            <pre className="whitespace-pre-wrap text-sm">{codeContent.trim()}</pre>
            {message.sql_query && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={() => copyToClipboard(message.sql_query!)}
              >
                {copiedSql ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
              </Button>
            )}
          </div>
        );
      } else if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={index} className="bg-muted px-1 py-0.5 rounded text-sm font-mono">
            {part.slice(1, -1)}
          </code>
        );
      }
      
      // Handle line breaks
      return part.split('\n').map((line, lineIndex) => (
        <React.Fragment key={`${index}-${lineIndex}`}>
          {lineIndex > 0 && <br />}
          {line}
        </React.Fragment>
      ));
    });
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedSql(true);
      toast({
        title: "Copied!",
        description: "SQL query copied to clipboard",
      });
      setTimeout(() => setCopiedSql(false), 2000);
    } catch (err) {
      toast({
        title: "Copy failed",
        description: "Unable to copy to clipboard",
        variant: "destructive",
      });
    }
  };

  const getMessageIcon = () => {
    switch (message.message_type) {
      case 'user':
        return <User className="h-4 w-4" />;
      case 'bot':
        return <Bot className="h-4 w-4" />;
      case 'error':
        return <AlertCircle className="h-4 w-4" />;
      case 'system':
        return <Info className="h-4 w-4" />;
      default:
        return <Bot className="h-4 w-4" />;
    }
  };

  const getMessageClass = () => {
    switch (message.message_type) {
      case 'user':
        return 'chat-message-user text-white ml-auto';
      case 'bot':
        return 'chat-message-bot';
      case 'error':
        return 'bg-destructive/10 text-destructive border-destructive/20';
      case 'system':
        return 'chat-message-system';
      default:
        return 'chat-message-bot';
    }
  };

  const getContainerClass = () => {
    return message.message_type === 'user' ? 'flex justify-end' : 'flex justify-start';
  };

  return (
    <div className={getContainerClass()}>
      <Card className={`max-w-[85%] p-4 smooth-transition hover:shadow-md ${getMessageClass()}`}>
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">
            {getMessageIcon()}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="prose prose-sm max-w-none">
              {formatMessage(message.message)}
            </div>
            
            {/* Timestamp */}
            <div className="text-xs opacity-70 mt-2">
              {new Date(parseInt(message.timestamp)).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChatMessage;