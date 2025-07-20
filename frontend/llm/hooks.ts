import React from 'react';

import { useGetMessages, useSendMessage } from './api/hooks';
import type { SendMessagePayload } from './api/client';

function useMessages() {
  const { messages, isPending: getMessagesIsPending, isError: getMessagesErrored, refetchMessages } = useGetMessages();
  const {
    sendMessage: internalSendMessage,
    isPending: sendMessageIsPending,
    isError: sendMessageErrored,
  } = useSendMessage();

  const sendMessage = React.useCallback(
    async (payload: SendMessagePayload) => {
      try {
        await internalSendMessage(payload);
      } catch {
        return;
      }

      refetchMessages();
    },
    [internalSendMessage, refetchMessages],
  );

  return {
    messages,
    isPending: getMessagesIsPending || sendMessageIsPending,
    getMessagesErrored,
    sendMessageErrored,
    sendMessage,
  };
}

export function useChatRoom() {
  const { messages, isPending, getMessagesErrored, sendMessageErrored, sendMessage } = useMessages();

  return { messages, isPending, getMessagesErrored, sendMessageErrored, sendMessage };
}
