import BaseWebAPIClient from '../../common/api/client';
import { GetMessagesResponseSchema, type GetMessagesResponse } from '../schemas';

class LLMClient extends BaseWebAPIClient {
  constructor() {
    super('/llm');
  }

  getMessages = async (): Promise<GetMessagesResponse> => {
    return this.get({ path: '/chats/messages', responseValidator: GetMessagesResponseSchema });
  };
}

export default LLMClient;
