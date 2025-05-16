'use client';

import type React from 'react';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { ChatMessage } from '@/types';
import { formatDistanceToNowStrict } from 'date-fns';
import { Bot, User, FileText, Loader2 } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

interface ChatMessageCardProps {
  message: ChatMessage;
}

const ChatMessageCard: React.FC<ChatMessageCardProps> & { Skeleton: typeof MessageSkeleton } = ({ message }) => {
  const isUser = message.role === 'user';
  const timeAgo = formatDistanceToNowStrict(new Date(message.timestamp), { addSuffix: true });

  return (
    <div className={cn('flex items-start gap-3', isUser ? 'justify-end' : '')}>
      {!isUser && (
        <Avatar className="w-8 h-8 border">
          <AvatarImage src="https://picsum.photos/seed/ai-assistant/40" data-ai-hint="robot avatar" />
          <AvatarFallback><Bot size={18} /></AvatarFallback>
        </Avatar>
      )}
      <Card className={cn('max-w-[75%] shadow-md', isUser ? 'bg-primary text-primary-foreground' : 'bg-card')}>
        <CardContent className="p-3">
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </CardContent>
        {(message.cost || (message.sources && message.sources.length > 0)) && !isUser && (
          <CardFooter className="text-xs px-3 py-1 text-muted-foreground flex justify-between items-center border-t">
            <div>
              {message.cost && <span>Cost: ${message.cost.toFixed(4)}</span>}
            </div>
            {message.sources && message.sources.length > 0 && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <span className="flex items-center gap-1 cursor-help">
                      <FileText size={12} /> {message.sources.length} source(s)
                    </span>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" align="end" className="max-w-xs">
                    <p className="font-medium mb-1">Sources:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {message.sources.map((src, idx) => (
                        <li key={idx} className="truncate text-xs">
                          <a
                            href={src}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            {src.length > 40 ? `${src.substring(0, 37)}...` : src}
                          </a>
                        </li>
                      ))}
                    </ul>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </CardFooter>
        )}
      </Card>
      {isUser && (
        <Avatar className="w-8 h-8 border">
           <AvatarImage src="https://picsum.photos/seed/current-user/40" data-ai-hint="user avatar"/>
          <AvatarFallback><User size={18} /></AvatarFallback>
        </Avatar>
      )}
       <p className={cn("text-xs text-muted-foreground self-end", isUser ? "mr-11" : "ml-11", "mt-1")}>{timeAgo}</p>
    </div>
  );
};

interface MessageSkeletonProps {
  role?: 'user' | 'assistant';
  isTyping?: boolean;
}

const MessageSkeleton: React.FC<MessageSkeletonProps> = ({ role = 'user', isTyping = false }) => {
  const isUser = role === 'user';
  return (
    <div className={cn('flex items-start gap-3', isUser ? 'justify-end' : '')}>
      {!isUser && <Skeleton className="w-8 h-8 rounded-full" />}
      <div className={cn('max-w-[60%] p-3 rounded-lg space-y-2', isUser ? 'bg-primary/80' : 'bg-muted')}>
        {isTyping ? (
          <div className="flex items-center space-x-1">
            <Loader2 className="w-4 h-4 animate-spin" />
            <Skeleton className="h-3 w-12" />
          </div>
        ) : (
          <>
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-3 w-32" />
          </>
        )}
      </div>
      {isUser && <Skeleton className="w-8 h-8 rounded-full" />}
    </div>
  );
};

ChatMessageCard.Skeleton = MessageSkeleton;

export default ChatMessageCard;
