import { logger } from './logger';

export interface InputProperty {
  type: string;
  description: string;
}

export class InputPropertyImpl implements InputProperty {
  type: string;
  description: string;

  constructor(type: string, description: string) {
    this.type = type;
    this.description = description;
  }

  static fromDict(data: Record<string, any> | null): InputProperty {
    if (!data || Object.keys(data).length === 0) {
      return new InputPropertyImpl('', '');
    }
    return new InputPropertyImpl(data.type, data.description);
  }
}

export interface InputSchema {
  type: string;
  properties: Record<string, InputProperty>;
}

export class InputSchemaImpl implements InputSchema {
  type: string;
  properties: Record<string, InputProperty>;

  constructor(type: string, properties: Record<string, InputProperty>) {
    this.type = type;
    this.properties = properties;
  }

  static fromDict(data: Record<string, any> | null): InputSchema {
    if (!data || Object.keys(data).length === 0) {
      return new InputSchemaImpl('', {});
    }
    const properties: Record<string, InputProperty> = {};
    for (const [key, value] of Object.entries(data.properties)) {
      properties[key] = InputPropertyImpl.fromDict(value as Record<string, any>);
    }
    return new InputSchemaImpl(data.type, properties);
  }
}

export interface Tool {
  name: string;
  description: string;
  inputSchema: InputSchema;
}

export class ToolImpl implements Tool {
  name: string;
  description: string;
  inputSchema: InputSchema;

  constructor(name: string, description: string, inputSchema: InputSchema) {
    this.name = name;
    this.description = description;
    this.inputSchema = inputSchema;
  }

  static fromDict(data: Record<string, any>): Tool {
    return new ToolImpl(
      data.name,
      data.description,
      InputSchemaImpl.fromDict(data.inputSchema)
    );
  }
}

export interface ToolMeta {
  invokeContext: Record<string, any>;
  enabled: boolean;
  templates: Record<string, string>;
}

export class ToolMetaImpl implements ToolMeta {
  invokeContext: Record<string, any>;
  enabled: boolean;
  templates: Record<string, string>;

  constructor(invokeContext: Record<string, any>, enabled: boolean, templates: Record<string, string>) {
    this.invokeContext = invokeContext;
    this.enabled = enabled;
    this.templates = templates;
  }

  static fromDict(data: Record<string, any>): ToolMeta {
    return new ToolMetaImpl(
      data.invokeContext || {},
      data.enabled ?? true,
      data.templates || {}
    );
  }
}

export interface ToolSpec {
  tools: Tool[];
  toolsMeta: Record<string, ToolMeta>;
}

export class ToolSpecImpl implements ToolSpec {
  tools: Tool[];
  toolsMeta: Record<string, ToolMeta>;

  constructor(tools: Tool[], toolsMeta: Record<string, ToolMeta>) {
    this.tools = tools;
    this.toolsMeta = toolsMeta;
  }

  static fromDict(data: Record<string, any>): ToolSpec {
    return new ToolSpecImpl(
      (data.tools || []).map((t: any) => ToolImpl.fromDict(t)),
      Object.fromEntries(
        Object.entries(data.toolsMeta || {}).map(([k, v]) => [k, ToolMetaImpl.fromDict(v as Record<string, any>)])
      )
    );
  }
}

export interface ServiceRef {
  namespaceId: string;
  groupName: string;
  serviceName: string;
}

export class ServiceRefImpl implements ServiceRef {
  namespaceId: string;
  groupName: string;
  serviceName: string;

  constructor(namespaceId: string, groupName: string, serviceName: string) {
    this.namespaceId = namespaceId;
    this.groupName = groupName;
    this.serviceName = serviceName;
  }

  static fromDict(data: Record<string, any> | null): ServiceRef {
    if (!data || Object.keys(data).length === 0) {
      return new ServiceRefImpl('', '', '');
    }
    return new ServiceRefImpl(
      data.namespaceId,
      data.groupName,
      data.serviceName
    );
  }
}

export interface RemoteServerConfig {
  serviceRef: ServiceRef;
  exportPath: string;
  credentials: Record<string, any>;
}

export class RemoteServerConfigImpl implements RemoteServerConfig {
  serviceRef: ServiceRef;
  exportPath: string;
  credentials: Record<string, any>;

  constructor(serviceRef: ServiceRef, exportPath: string, credentials: Record<string, any>) {
    this.serviceRef = serviceRef;
    this.exportPath = exportPath;
    this.credentials = credentials;
  }

  static fromDict(data: Record<string, any> | null): RemoteServerConfig {
    if (!data || Object.keys(data).length === 0) {
      return new RemoteServerConfigImpl(ServiceRefImpl.fromDict({}), '', {});
    }
    return new RemoteServerConfigImpl(
      ServiceRefImpl.fromDict(data.serviceRef),
      data.exportPath,
      data.credentials || {}
    );
  }
}

export interface BackendEndpoint {
  address: string;
  port: number;
}

export class BackendEndpointImpl implements BackendEndpoint {
  address: string;
  port: number;

  constructor(address: string, port: number) {
    this.address = address;
    this.port = port;
  }

  static fromDict(data: Record<string, any> | null): BackendEndpoint {
    if (!data || Object.keys(data).length === 0) {
      return new BackendEndpointImpl('', -1);
    }
    return new BackendEndpointImpl(data.address, data.port);
  }
}

export interface NacosMcpServerConfig {
  name: string;
  protocol: string;
  description: string | null;
  version: string;
  remoteServerConfig: RemoteServerConfig;
  localServerConfig: Record<string, any>;
  enabled: boolean;
  capabilities: string[];
  backendEndpoints: BackendEndpoint[];
  toolSpec: ToolSpec;
  getToolDescription(): string;
}

export class NacosMcpServerConfigImpl implements NacosMcpServerConfig {
  name: string;
  protocol: string;
  description: string | null;
  version: string;
  remoteServerConfig: RemoteServerConfig;
  localServerConfig: Record<string, any>;
  enabled: boolean;
  capabilities: string[];
  backendEndpoints: BackendEndpoint[];
  toolSpec: ToolSpec;

  constructor(
    name: string,
    protocol: string,
    description: string | null,
    version: string,
    remoteServerConfig: RemoteServerConfig,
    localServerConfig: Record<string, any>,
    enabled: boolean,
    capabilities: string[],
    backendEndpoints: BackendEndpoint[],
    toolSpec: ToolSpec
  ) {
    this.name = name;
    this.protocol = protocol;
    this.description = description;
    this.version = version;
    this.remoteServerConfig = remoteServerConfig;
    this.localServerConfig = localServerConfig;
    this.enabled = enabled;
    this.capabilities = capabilities;
    this.backendEndpoints = backendEndpoints;
    this.toolSpec = toolSpec;
  }

  static fromDict(data: Record<string, any>): NacosMcpServerConfig {
    const toolSpecData = data.toolSpec;
    const backendEndpointsData = data.backendEndpoints;

    try {
      return new NacosMcpServerConfigImpl(
        data.name,
        data.protocol,
        data.description,
        data.version,
        RemoteServerConfigImpl.fromDict(data.remoteServerConfig),
        data.localServerConfig || {},
        data.enabled ?? true,
        data.capabilities || [],
        backendEndpointsData ? backendEndpointsData.map((e: any) => BackendEndpointImpl.fromDict(e)) : [],
        toolSpecData ? ToolSpecImpl.fromDict(toolSpecData) : new ToolSpecImpl([], {})
      );
    } catch (error) {
      logger.warn(`failed to parse NacosMcpServerConfig from data: ${JSON.stringify(data)}`, error);
      throw new Error('failed to parse NacosMcpServerConfig from data');
    }
  }

  static fromString(string: string): NacosMcpServerConfig {
    return NacosMcpServerConfigImpl.fromDict(JSON.parse(string));
  }

  getToolDescription(): string {
    let des = this.description || '';
    for (const tool of this.toolSpec.tools) {
      if (tool.description) {
        des += '\n' + tool.description;
      }
    }
    return des;
  }
}
