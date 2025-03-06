declare module '@smithery/sdk/transport' {
  export function createTransport(url: string): any;
}

declare module '@smithery/sdk/dist/transport.js' {
  export function createTransport(url: string): any;
}

declare module '@modelcontextprotocol/sdk/client' {
  export class Client {
    constructor(options: { name: string; version: string });
    connect(transport: any): Promise<void>;
    listTools(): Promise<any[]>;
    callTool(name: string, params: Record<string, any>): Promise<any>;
  }
}

declare module '@modelcontextprotocol/sdk/dist/esm/client/index.js' {
  export class Client {
    constructor(options: { name: string; version: string });
    connect(transport: any): Promise<void>;
    listTools(): Promise<any[]>;
    callTool(name: string, params: Record<string, any>): Promise<any>;
  }
} 