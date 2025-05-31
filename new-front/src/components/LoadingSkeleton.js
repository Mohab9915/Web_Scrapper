import React from 'react';

export const MessageSkeleton = () => (
  <div className="mb-4 animate-fadeIn">
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-purple-700/50 animate-pulse"></div>
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-purple-700/50 rounded-lg w-3/4 animate-shimmer"></div>
        <div className="h-4 bg-purple-700/50 rounded-lg w-1/2 animate-shimmer"></div>
      </div>
    </div>
  </div>
);

export const ProjectCardSkeleton = () => (
  <div className="bg-purple-800/50 rounded-lg shadow-lg aspect-square border-2 border-purple-700 animate-fadeIn">
    <div className="p-4 h-full flex flex-col justify-between">
      <div className="space-y-3">
        <div className="h-6 bg-purple-700/50 rounded-lg animate-shimmer"></div>
        <div className="h-4 bg-purple-700/50 rounded-lg w-2/3 animate-shimmer"></div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-purple-700/50 rounded-lg w-1/2 animate-shimmer"></div>
        <div className="flex space-x-2">
          <div className="h-8 bg-purple-700/50 rounded-lg flex-1 animate-shimmer"></div>
          <div className="h-8 bg-purple-700/50 rounded-lg w-8 animate-shimmer"></div>
        </div>
      </div>
    </div>
  </div>
);

export const URLCardSkeleton = () => (
  <div className="bg-purple-800/40 p-4 rounded-lg shadow-md border border-purple-700 animate-fadeIn">
    <div className="flex justify-between items-center">
      <div className="flex-1 space-y-2">
        <div className="h-5 bg-purple-700/50 rounded-lg w-3/4 animate-shimmer"></div>
        <div className="h-4 bg-purple-700/50 rounded-lg w-1/2 animate-shimmer"></div>
        <div className="h-3 bg-purple-700/50 rounded-lg w-1/4 animate-shimmer"></div>
      </div>
      <div className="ml-4 space-y-2">
        <div className="h-8 bg-purple-700/50 rounded-lg w-16 animate-shimmer"></div>
        <div className="h-8 bg-purple-700/50 rounded-lg w-8 animate-shimmer"></div>
      </div>
    </div>
  </div>
);

export const ConversationSkeleton = () => (
  <div className="p-3 border-b border-purple-700 animate-fadeIn">
    <div className="space-y-2">
      <div className="h-4 bg-purple-700/50 rounded-lg w-3/4 animate-shimmer"></div>
      <div className="h-3 bg-purple-700/50 rounded-lg w-1/2 animate-shimmer"></div>
    </div>
  </div>
);

const LoadingSkeleton = ({ type = 'message', count = 1 }) => {
  const skeletonComponents = {
    message: MessageSkeleton,
    project: ProjectCardSkeleton,
    url: URLCardSkeleton,
    conversation: ConversationSkeleton,
  };

  const SkeletonComponent = skeletonComponents[type] || MessageSkeleton;

  return (
    <div className="space-y-4">
      {Array.from({ length: count }, (_, index) => (
        <SkeletonComponent key={index} />
      ))}
    </div>
  );
};

export default LoadingSkeleton;
