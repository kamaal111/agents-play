import { useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';

import LLMClient from './client';
import { APIError } from '../../common/errors/api';

const client = new LLMClient();

function handleGetMessagesError(error: Error) {
  if (!(error instanceof APIError)) {
    toast.error('Something went wrong');
    return;
  }

  toast.error(error.message);
}

export function useGetMessages() {
  const result = useMutation({ mutationFn: client.getMessages, onError: handleGetMessagesError });

  return {
    getMessages: result.mutateAsync,
    isPending: result.isPending,
    isSuccess: result.isSuccess,
    isError: result.isError,
    messages: result.data,
    status: result.status,
  };
}
