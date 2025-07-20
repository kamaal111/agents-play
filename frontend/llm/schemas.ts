import * as z from 'zod';

import { DefaultResponseSchema } from '../common/api/client';

export type LLMMessage = z.infer<typeof LLMMessageSchema>;

export type GetMessagesResponse = z.infer<typeof GetMessagesResponseSchema>;

export type CreateMessageResponse = z.infer<typeof CreateMessageResponseSchema>;

const LLMMessageSchemaShape = {
  id: z.uuidv4(),
  llm_provider: z.string(),
  llm_key: z.string(),
  date: z.iso.datetime(),
  role: z.literal(['user', 'assistant']),
  content: z.string(),
};

export const LLMMessageSchema = z.object(LLMMessageSchemaShape);

export const GetMessagesResponseSchema = DefaultResponseSchema.extend({ data: z.array(LLMMessageSchema) });

export const CreateMessageResponseSchema = DefaultResponseSchema.extend(LLMMessageSchemaShape).extend({
  room_id: z.uuidv4(),
  title: z.string(),
  updated_at: z.iso.datetime(),
});
