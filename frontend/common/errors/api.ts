type ObjectWith<Base extends Record<string, unknown>, Rest extends Record<string, unknown>> = Rest & Base;

type WithDetails<Rest extends Record<string, unknown>> = ObjectWith<{ detail: string }, Rest>;

export class APIError extends Error {
  cause?: unknown;
  statusCode: number;

  constructor({ message, cause, statusCode }: { message?: string; cause?: unknown; statusCode: number }) {
    super(message);
    this.cause = cause;
    this.statusCode = statusCode;
  }
}

export class APIConnectionError extends APIError {
  constructor({ cause }: { cause?: unknown }) {
    super({ statusCode: 503, cause });
  }
}

export class JSONAPIError<RestOfJSONResponse extends Record<string, unknown>> extends APIError {
  response: WithDetails<RestOfJSONResponse>;

  constructor({
    message,
    cause,
    response,
    statusCode,
  }: {
    message?: string;
    cause?: unknown;
    response: WithDetails<RestOfJSONResponse>;
    statusCode: number;
  }) {
    super({ message: message ?? response.detail, cause, statusCode });
    this.response = response;
  }
}
