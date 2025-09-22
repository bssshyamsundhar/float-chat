import React from 'react';
import { Waves, RefreshCw, Database, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface ChatHeaderProps {
  onClearChat: () => void;
}

const ChatHeader: React.FC<ChatHeaderProps> = ({ onClearChat }) => {
  return (
    <Card className="border-b bg-gradient-to-r from-primary/5 to-accent/5 rounded-none border-x-0 border-t-0">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-primary to-accent rounded-lg text-white">
            <Waves className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold gradient-text">
              Oceanographic Data Assistant
            </h1>
            <p className="text-sm text-muted-foreground">
              Natural language to SQL • Real-time oceanographic data
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Status indicators */}
          <div className="hidden sm:flex items-center gap-4 mr-4">
            <div className="flex items-center gap-1 text-xs">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <Database className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Neon DB</span>
            </div>
            <div className="flex items-center gap-1 text-xs">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <Activity className="h-3 w-3 text-muted-foreground" />
              <span className="text-muted-foreground">Qdrant</span>
            </div>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={onClearChat}
            className="smooth-transition hover:bg-secondary"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Clear Chat
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default ChatHeader;