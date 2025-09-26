import React, { useState } from 'react';
import { User, Bot, AlertCircle, Info, Copy, Check } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

interface Message {
  id: string;
  message: string;
  message_type: 'user' | 'bot' | 'system' | 'error';
  timestamp: string;
  sql_query?: string;
  data?: any[];
  clarification_needed?: boolean;
}

interface ChatMessageProps {
  message: Message;
  onRunAnyway?: (message: Message) => void;
  onRefine?: (message: Message) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onRunAnyway, onRefine }) => {
  const [copiedSql, setCopiedSql] = useState(false);
  const { toast } = useToast();

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedSql(true);
      toast({ title: "Copied!", description: "SQL query copied to clipboard" });
      setTimeout(() => setCopiedSql(false), 2000);
    } catch {
      toast({ title: "Copy failed", description: "Unable to copy", variant: "destructive" });
    }
  };

  const formatMessage = (text: string) => {
    const parts = text.split(/(\*\*.*?\*\*|`.*?`|```[\s\S]*?```)/);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) return <strong key={i}>{part.slice(2, -2)}</strong>;
      if (part.startsWith('```') && part.endsWith('```')) {
        const code = part.slice(3, -3);
        return (
          <div key={i} className="code-block my-2 relative group">
            <pre className="whitespace-pre-wrap text-sm">{code}</pre>
            {message.sql_query && <Button size="sm" variant="ghost" className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => copyToClipboard(message.sql_query)}>
              {copiedSql ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </Button>}
          </div>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) return <code key={i} className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{part.slice(1, -1)}</code>;
      return part.split('\n').map((line, li) => <React.Fragment key={`${i}-${li}`}>{li>0 && <br />}{line}</React.Fragment>);
    });
  };

  const getIcon = () => {
    switch (message.message_type) {
      case 'user': return <User className="h-4 w-4" />;
      case 'bot': return <Bot className="h-4 w-4" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      case 'system': return <Info className="h-4 w-4" />;
      default: return <Bot className="h-4 w-4" />;
    }
  };

  const getMessageClass = () => {
    switch (message.message_type) {
      case 'user': return 'chat-message-user text-white ml-auto';
      case 'bot': return 'chat-message-bot';
      case 'error': return 'bg-destructive/10 text-destructive border-destructive/20';
      case 'system': return 'chat-message-system';
      default: return 'chat-message-bot';
    }
  };

  return (
    <div className={message.message_type === 'user' ? 'flex justify-end' : 'flex justify-start'}>
      <Card className={`max-w-[85%] p-4 smooth-transition hover:shadow-md ${getMessageClass()}`}>
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 mt-0.5">{getIcon()}</div>
          <div className="flex-1 min-w-0">
            <div className="prose prose-sm max-w-none">{formatMessage(message.message)}</div>

            {message.clarification_needed && (
              <div className="flex gap-2 mt-2">
                <Button size="sm" onClick={() => onRunAnyway?.(message)}>Run Anyway</Button>
                <Button size="sm" variant="outline" onClick={() => onRefine?.(message)}>Refine Query</Button>
              </div>
            )}

            <div className="text-xs opacity-70 mt-2">{new Date(parseInt(message.timestamp)).toLocaleTimeString()}</div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChatMessage;
