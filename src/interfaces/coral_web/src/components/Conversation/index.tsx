import React, { useCallback, useEffect, useRef } from 'react';

import { Tool } from '@/cohere-client';
import { Composer } from '@/components/Conversation/Composer';
import { Header } from '@/components/Conversation/Header';
import MessagingContainer from '@/components/Conversation/MessagingContainer';
import { Spinner } from '@/components/Shared';
import { HotKeysProvider } from '@/components/Shared/HotKeys';
import { WelcomeGuideTooltip } from '@/components/WelcomeGuideTooltip';
import { ReservedClasses } from '@/constants';
import { useChatHotKeys } from '@/hooks/actions';
import { useChat } from '@/hooks/chat';
import { useDefaultFileLoaderTool, useFileActions, useFilesInConversation } from '@/hooks/files';
import { WelcomeGuideStep, useWelcomeGuideState } from '@/hooks/ftux';
import { useRouteChange } from '@/hooks/route';
import {
  useCitationsStore,
  useConversationStore,
  useFilesStore,
  useParamsStore,
  useSettingsStore,
} from '@/stores';
import { ConfigurableParams } from '@/stores/slices/paramsSlice';
import { ChatMessage } from '@/types/message';

type Props = {
  startOptionsEnabled?: boolean;
  conversationId?: string;
  history?: ChatMessage[];
};

/**
 * @description Renders the entire conversation pane, which includes the header, messages,
 * composer, and the citation panel.
 */
const Conversation: React.FC<Props> = ({ conversationId, startOptionsEnabled = false }) => {
  const chatHotKeys = useChatHotKeys();

  const { uploadFile } = useFileActions();
  const { welcomeGuideState, finishWelcomeGuide } = useWelcomeGuideState();
  const {
    settings: { isConfigDrawerOpen },
    setSettings,
  } = useSettingsStore();
  const {
    conversation: { messages },
  } = useConversationStore();
  const {
    citations: { selectedCitation },
    selectCitation,
  } = useCitationsStore();
  const { files } = useFilesInConversation();
  const {
    params: { fileIds },
  } = useParamsStore();
  const {
    files: { composerFiles },
  } = useFilesStore();
  const { defaultFileLoaderTool, enableDefaultFileLoaderTool } = useDefaultFileLoaderTool();

  const {
    userMessage,
    isStreaming,
    streamingMessage,
    setUserMessage,
    handleSend: send,
    handleStop,
    handleRetry,
  } = useChat({
    onSend: () => {
      if (isConfigDrawerOpen) setSettings({ isConfigDrawerOpen: false });
      if (welcomeGuideState !== WelcomeGuideStep.DONE) {
        finishWelcomeGuide();
      }
    },
  });

  const chatWindowRef = useRef<HTMLDivElement>(null);

  const handleClickOutside = useCallback(
    (event: MouseEvent) => {
      if (!selectedCitation) return;

      const target = event.target as Node;
      const invalidElements = Array.from(
        document.querySelectorAll(`.${ReservedClasses.MESSAGE}, .${ReservedClasses.CITATION}`)
      );
      const validParentElements = Array.from(
        document.querySelectorAll(
          `.${ReservedClasses.MESSAGES}, .${ReservedClasses.CITATION_PANEL}`
        )
      );

      const isClickInsideInvalidElements = invalidElements.some((node) => node.contains(target));
      const isClickInsideValidParentElements = validParentElements.some((node) =>
        node.contains(target)
      );
      if (!isClickInsideInvalidElements && isClickInsideValidParentElements) {
        selectCitation(null);
      }
    },
    [selectedCitation, selectCitation]
  );

  useEffect(() => {
    window?.addEventListener('click', handleClickOutside);
    return () => {
      window?.removeEventListener('click', handleClickOutside);
    };
  }, [handleClickOutside]);

  const [isRouteChanging] = useRouteChange();

  if (isRouteChanging) {
    return (
      <div className="flex h-full flex-grow items-center justify-center">
        <Spinner />
      </div>
    );
  }

  const handleUploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFileIds = await uploadFile(e.target.files?.[0], conversationId);
    if (!newFileIds) return;
    enableDefaultFileLoaderTool();
  };

  const handleSend = (msg?: string, overrides?: Partial<ConfigurableParams>) => {
    const areFilesSelected = fileIds && fileIds.length > 0;
    const enableFileLoaderTool = areFilesSelected && !!defaultFileLoaderTool;

    if (enableFileLoaderTool) {
      enableDefaultFileLoaderTool();
    }
    send({ suggestedMessage: msg }, overrides);
  };

  return (
    <div className="flex h-full w-full flex-col">
      <HotKeysProvider customHotKeys={chatHotKeys} />
      <Header conversationId={conversationId} isStreaming={isStreaming} />

      <div className="relative flex h-full w-full flex-col" ref={chatWindowRef}>
        <MessagingContainer
          conversationId={conversationId}
          startOptionsEnabled={startOptionsEnabled}
          isStreaming={isStreaming}
          onRetry={handleRetry}
          messages={messages}
          streamingMessage={streamingMessage}
          composer={
            <>
              <WelcomeGuideTooltip step={3} className="absolute bottom-full mb-4" />
              <Composer
                isStreaming={isStreaming}
                value={userMessage}
                isFirstTurn={messages.length === 0}
                streamingMessage={streamingMessage}
                chatWindowRef={chatWindowRef}
                onChange={(message) => setUserMessage(message)}
                onSend={handleSend}
                onStop={handleStop}
                onUploadFile={handleUploadFile}
              />
            </>
          }
        />
      </div>
    </div>
  );
};

export default Conversation;
