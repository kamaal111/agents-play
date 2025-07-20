import React from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { asserts } from '@kamaalio/kamaal';

import LLMClient, { type SendMessagePayload } from './client';
import { APIError } from '../../common/errors/api';
import type { LLMMessage } from '../schemas';

type BaseHookResult = { isPending: boolean; isError: boolean };

const client = new LLMClient();

function withErrorHandling<Params extends Array<unknown>, Result>(
  action: (...params: Params) => Promise<Result>,
  ...params: Params
): () => Promise<Result> {
  return async () => {
    try {
      return await action(...params);
    } catch (error) {
      asserts.invariant(error instanceof Error, 'error should have been a error');

      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('Something went wrong');
      }

      throw error;
    }
  };
}

export function useGetMessages(): BaseHookResult & { messages: Array<LLMMessage>; refetchMessages: () => void } {
  const { data, isPending, isError, refetch } = useQuery({
    queryKey: ['messages'],
    queryFn: withErrorHandling(client.getMessages),
  });

  return { messages: data?.data ?? [], isPending, isError, refetchMessages: refetch };
}

export function useSendMessage(): BaseHookResult & {
  response: LLMMessage | undefined;
  sendMessage: (payload: SendMessagePayload) => Promise<LLMMessage>;
} {
  const { mutateAsync, data, isPending, isError } = useMutation({ mutationFn: client.sendMessage });

  const sendMessage = React.useCallback(
    (payload: SendMessagePayload) => withErrorHandling(mutateAsync, payload)(),
    [mutateAsync],
  );

  return { sendMessage, response: data, isPending, isError };
}
