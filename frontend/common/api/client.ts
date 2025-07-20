import * as z from 'zod';
import type * as zm from 'zod/mini';

import { APIConnectionError, JSONAPIError } from '../errors/api';

type GetRecordValues<T extends Record<string, unknown>> = T[keyof T];

type HTTPMethod = GetRecordValues<typeof HTTP_METHODS>;

type AnyZodType = z.ZodType | zm.ZodMiniType;

type ZodInfer<T extends AnyZodType> = T extends z.ZodType ? z.infer<T> : zm.infer<T>;

export const DefaultResponseSchema = z.object({ detail: z.string() });

const HTTP_METHODS = { GET: 'GET' } as const;

class BaseWebAPIClient {
  private readonly basePath: string;

  constructor(basePath: string) {
    this.basePath = `/v1/web-api${basePath}`;
  }

  get = async <ResponseSchema extends AnyZodType = typeof DefaultResponseSchema>({
    path,
    responseValidator,
  }: {
    path: string;
    responseValidator?: ResponseSchema;
  }): Promise<ZodInfer<ResponseSchema>> => {
    return this.fetch({ path, responseValidator, method: HTTP_METHODS.GET });
  };

  private fetch = async <ResponseSchema extends AnyZodType = typeof DefaultResponseSchema>({
    path,
    payload,
    responseValidator,
    method,
  }: {
    payload?: FormData | Record<string, unknown>;
    path: string;
    responseValidator?: ResponseSchema;
    method: HTTPMethod;
  }): Promise<ZodInfer<ResponseSchema>> => {
    let response: Response;
    try {
      response = await fetch(`${this.basePath}${path}`, {
        method,
        body: this.makePayload(payload),
        credentials: 'include',
        mode: 'same-origin',
      });
    } catch (err) {
      throw new APIConnectionError({ cause: err });
    }

    const jsonResponse = await response.json();
    if (!response.ok) {
      throw new JSONAPIError({
        response: jsonResponse,
        statusCode: response.status,
      });
    }

    const result = await (responseValidator ?? DefaultResponseSchema).parseAsync(jsonResponse);

    return result as ZodInfer<ResponseSchema>;
  };

  private makePayload = (payload: FormData | Record<string, unknown> | undefined) => {
    if (payload == null) return null;
    if (payload instanceof FormData) return payload;
    return JSON.stringify(payload);
  };
}

export default BaseWebAPIClient;
