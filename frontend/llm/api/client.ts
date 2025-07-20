import BaseWebAPIClient from '../../common/api/client';
import {
  CreateMessageResponseSchema,
  GetMessagesResponseSchema,
  type CreateMessageResponse,
  type GetMessagesResponse,
} from '../schemas';

export type SendMessagePayload = {
  message: string;
};

class LLMClient extends BaseWebAPIClient {
  constructor() {
    super('/llm');
  }

  getMessages = async (): Promise<GetMessagesResponse> => {
    return this.get({ path: '/chats/messages', responseValidator: GetMessagesResponseSchema });
  };

  sendMessage = async (payload: SendMessagePayload): Promise<CreateMessageResponse> => {
    return this.post({ path: '/chats', responseValidator: CreateMessageResponseSchema, payload });
  };
}

export default LLMClient;
