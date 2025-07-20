import * as z from 'zod';

import { DefaultResponseSchema } from '../common/api/client';

export type GetMessagesResponse = z.infer<typeof GetMessagesResponseSchema>;

export const MessageResponseSchema = z.object({
  llm_provider: z.string(),
  llm_key: z.string(),
  date: z.date(),
  role: z.literal(['user', 'assistant']),
  content: z.string(),
});

export const GetMessagesResponseSchema = DefaultResponseSchema.extend({ data: z.array(MessageResponseSchema) });
